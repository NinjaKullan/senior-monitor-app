"""FastAPI ingestion service (spec 002 §3).

One public write route. The device token *is* the identity — there is no `who`
in the URL to guess, and a token resolves to exactly one device belonging to
exactly one person in exactly one family.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from hmac import compare_digest
from urllib.parse import parse_qs

import psycopg
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from starlette.exceptions import HTTPException as StarletteHTTPException

from kettle import db, waitlist
from kettle.config import Settings, settings_from_env
from kettle.heartbeat import HeartbeatState, heartbeat_loop
from kettle.notify import LogOnlyNotifier, Notifier, NtfyNotifier
from kettle.outbound import (
    OutboundState,
    outbound_loop,
    record_parent_reply,
    transport_from_name,
)
from kettle.setup_page import router as setup_router
from kettle.timeutil import now_utc

log = logging.getLogger("kettle")

DEDUPE_WINDOW_S = 60

#: The landing page's bot trap. A real person never fills it: it is hidden, and
#: it is named for something a form-filler expects to see rather than something
#: that announces itself as a trap.
HONEYPOT_FIELD = "company"


def _client_ip(request: Request) -> str | None:
    """Caller IP as seen behind the Fly proxy. Hashed immediately, never stored raw."""
    forwarded = request.headers.get("fly-client-ip") or request.headers.get(
        "x-forwarded-for"
    )
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def create_app(
    settings: Settings | None = None,
    notifier: Notifier | None = None,
    clock: Callable[[], datetime] = now_utc,
) -> FastAPI:
    """Build the application. `settings`/`notifier`/`clock` are injectable for tests.

    `clock` exists because `/outbound/reply` is the one decision in spec 007 that
    reads wall time instead of being handed an instant, which made its test green
    only while the suite happened to run before 18:30 UTC (DECISIONS 142). Every
    other 007 decision takes `now` as an argument; this restores the seam rather
    than leaving one route that cannot be tested at an arbitrary hour.
    """
    cfg = settings or settings_from_env()

    # Fail closed before anything else exists: an unknown OUTBOUND_TRANSPORT —
    # or resend selected without its API key — refuses to build the app at
    # all, loop flag on or off, so a typo in an env var can never fall through
    # to something that sends (DECISIONS 154/159). The instance built here is
    # thrown away; each boot's loop gets its own.
    transport_from_name(cfg.outbound_transport, cfg)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        pool = ConnectionPool(
            cfg.database_url,
            min_size=1,
            max_size=5,
            kwargs={"row_factory": dict_row, "autocommit": True},
            open=True,
        )
        app.state.pool = pool
        app.state.heartbeat = HeartbeatState()
        app.state.outbound = OutboundState()
        app.state.notifier = notifier or (
            NtfyNotifier(cfg.ntfy_topic) if cfg.ntfy_topic else LogOnlyNotifier()
        )
        tasks: list[asyncio.Task[None]] = []
        loop_conns: list[psycopg.Connection] = []
        if cfg.heartbeat_loop:
            # Each loop gets its own connection: they run in worker threads.
            hb_conn = db.connect(cfg.database_url)
            loop_conns.append(hb_conn)
            tasks.append(
                asyncio.create_task(
                    heartbeat_loop(hb_conn, cfg, app.state.notifier, app.state.heartbeat)
                )
            )
        if cfg.outbound_loop:
            # Spec 007 §2.5: Wave A IS this loop running dark — console
            # transport, ledger written, nothing sent. It does not wait for a
            # real transport; the 48-hour ledger review (§6.3) is a review of
            # what this loop writes. The engines that used to run here — the
            # digest's and the ladder's — were retired with specs 003 and 004.
            ob_conn = db.connect(cfg.database_url)
            loop_conns.append(ob_conn)
            tasks.append(
                asyncio.create_task(
                    outbound_loop(
                        ob_conn,
                        transport_from_name(cfg.outbound_transport, cfg),
                        cfg,
                        app.state.notifier,
                        app.state.outbound,
                    )
                )
            )
        try:
            yield
        finally:
            for task in tasks:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            for conn in loop_conns:
                conn.close()
            pool.close()

    app = FastAPI(
        title="Kettle API",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    app.state.settings = cfg

    # CORS exists for exactly one route — the landing page's waitlist POST — and
    # is locked to the origins that page is served from. The ingest route needs
    # none of this: a Shortcut is not a browser and sends no Origin.
    if cfg.waitlist_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(cfg.waitlist_origins),
            allow_methods=["POST"],
            allow_headers=["content-type"],
        )

    @app.exception_handler(StarletteHTTPException)
    async def _plain_errors(
        request: Request, exc: StarletteHTTPException
    ) -> PlainTextResponse:
        """Plain-text errors: Shortcuts cope with them and they leak nothing."""
        return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

    # The parent setup page (spec 005b): /s/{slug} and its live state check.
    app.include_router(setup_router)

    @app.api_route(
        "/p/{device_token}/{signal}",
        methods=["GET", "POST"],
        response_class=PlainTextResponse,
    )
    async def ingest(
        request: Request, device_token: str, signal: str
    ) -> PlainTextResponse:
        """Record one content-free ping. Everything but the path is ignored."""
        signal = signal.strip().lower()
        with request.app.state.pool.connection() as conn:
            device = db.device_by_token(conn, device_token)
            # Unknown, deactivated or revoked token: same silent 403 either way.
            if device is None or not device["active"] or device["revoked_utc"]:
                raise StarletteHTTPException(status_code=403, detail="forbidden")

            if db.active_signal(conn, device["parent_id"], signal) is None:
                raise StarletteHTTPException(status_code=400, detail="unknown signal")

            db.insert_ping(
                conn,
                device["parent_id"],
                signal,
                now_utc(),
                db.hash_ip(_client_ip(request), cfg.ip_hash_salt),
                DEDUPE_WINDOW_S,
            )
        return PlainTextResponse("ok")

    @app.post("/outbound/reply", response_class=PlainTextResponse)
    async def outbound_reply(request: Request) -> PlainTextResponse:
        """The parent answered the ask (spec 007 §2.6). Nothing calls this yet.

        Wave A builds and tests the endpoint; Wave C points a real WhatsApp
        webhook at it. Three properties hold from today, because they are the
        ones that are expensive to add later:

        * **It does not exist until it is configured.** Cancelling a follow-on
          is a safety-relevant act — anyone who could call this and knows a
          number could suppress an escalation — so with no shared secret set,
          the route is a 404 rather than an open door. Wave C swaps the shared
          secret for the provider's own signature — the shape the retired
          `/twilio/inbound` used, which is worth copying even though the route
          it served is gone.
        * **The body is never read.** Only the sender is, and only to find which
          parent replied. What she said is content, and this product does not
          hold content.
        * **It is not an oracle.** An unknown number and a known one with no
          pending ask get the same empty acknowledgement, so the endpoint cannot
          be used to ask "is this number a Kettle parent".
        """
        if not cfg.outbound_reply_token:
            raise StarletteHTTPException(status_code=404, detail="not found")
        supplied = request.headers.get("x-kettle-reply-token") or ""
        if not compare_digest(supplied, cfg.outbound_reply_token):
            raise StarletteHTTPException(status_code=403, detail="forbidden")

        raw = (await request.body()).decode("utf-8", errors="replace")
        params = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
        sender = (params.get("From") or "").strip()
        # From here on the body is gone, unread beyond the sender.
        del params, raw

        if sender:
            with request.app.state.pool.connection() as conn:
                record_parent_reply(conn, sender, clock())
        return PlainTextResponse("", status_code=204)

    @app.post("/waitlist", response_class=PlainTextResponse)
    async def join_waitlist(request: Request) -> PlainTextResponse:
        """The landing page's one write (spec 006 §7).

        Accepts JSON or form-encoded, because the page's form degrades to a
        plain POST with JavaScript off and must still work — the same body comes
        back either way.

        Everything unusual here is about not leaking. A duplicate signup returns
        the same 200 and the same sentence as a first one, so the endpoint cannot
        be asked whether an address is on the list. A honeypot hit returns that
        too, because telling a bot it was caught only teaches it which field to
        leave alone. And nothing about the request is stored beyond the two
        fields that were typed: no IP, no user agent, no referrer. The page
        carries no analytics (law #4) and this is not going to become the
        analytics by the back door.
        """
        content_type = request.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            try:
                payload = await request.json()
            except ValueError:
                raise StarletteHTTPException(
                    status_code=400, detail="malformed request"
                ) from None
            if not isinstance(payload, dict):
                raise StarletteHTTPException(status_code=400, detail="malformed request")
        else:
            # `parse_qs` rather than `request.form()`, exactly as the Twilio
            # handler does: form parsing in Starlette pulls in python-multipart,
            # and a browser form posts url-encoded anyway. No new dependency for
            # a body this app can read in one line.
            raw = (await request.body()).decode("utf-8", errors="replace")
            payload = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}

        def field(name: str) -> str:
            value = payload.get(name, "")
            return value if isinstance(value, str) else ""

        if field(HONEYPOT_FIELD).strip():
            # Accepted, discarded, and indistinguishable from a real signup.
            return PlainTextResponse(waitlist.WAITLIST_SUCCESS)

        email = waitlist.normalise_email(field("email"))
        parent_phone = waitlist.normalise_choice(field("parent_phone"))
        if email is None or parent_phone is None:
            raise StarletteHTTPException(status_code=400, detail="check the form")
        # Optional, capped, never a reason to fail a signup (DECISIONS 129).
        help_with = waitlist.normalise_help_with(field("help_with"))

        with request.app.state.pool.connection() as conn:
            waitlist.record(conn, email, parent_phone, help_with)
        return PlainTextResponse(waitlist.WAITLIST_SUCCESS)

    @app.get("/healthz")
    async def healthz(request: Request) -> JSONResponse:
        """Liveness probe for Fly. No auth, no data."""
        with request.app.state.pool.connection() as conn:
            ok = db.healthy(conn)
        return JSONResponse({"db": ok}, status_code=200 if ok else 503)

    return app
