"""FastAPI ingestion service (spec 002 §3).

One public write route. The device token *is* the identity — there is no `who`
in the URL to guess, and a token resolves to exactly one device belonging to
exactly one person in exactly one family.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from urllib.parse import parse_qs

import psycopg
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from starlette.exceptions import HTTPException as StarletteHTTPException

from kettle import db, waitlist
from kettle.channels import build_channels
from kettle.config import Settings, settings_from_env
from kettle.digest import DigestState, digest_loop
from kettle.heartbeat import HeartbeatState, heartbeat_loop
from kettle.ladder import LadderState, ladder_loop, resolve_by_senior_reply
from kettle.notify import LogOnlyNotifier, Notifier, NtfyNotifier
from kettle.setup_page import router as setup_router
from kettle.timeutil import now_utc
from kettle.twilio_signature import is_valid

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
    settings: Settings | None = None, notifier: Notifier | None = None
) -> FastAPI:
    """Build the application. `settings`/`notifier` are injectable for tests."""
    cfg = settings or settings_from_env()

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
        app.state.notifier = notifier or (
            NtfyNotifier(cfg.ntfy_topic) if cfg.ntfy_topic else LogOnlyNotifier()
        )
        app.state.digest = DigestState()
        app.state.ladder = LadderState()
        app.state.channels = build_channels(cfg)
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
            # Sibling loop rather than more work inside the heartbeat: ops
            # alerting and family-facing sending should not share a failure mode.
            dg_conn = db.connect(cfg.database_url)
            loop_conns.append(dg_conn)
            tasks.append(
                asyncio.create_task(
                    digest_loop(
                        dg_conn,
                        cfg,
                        app.state.channels,
                        app.state.notifier,
                        app.state.digest,
                    )
                )
            )
            # The ladder is its own loop for the same reason: the alert path
            # must not share a failure mode with reassurance or with ops.
            ld_conn = db.connect(cfg.database_url)
            loop_conns.append(ld_conn)
            tasks.append(
                asyncio.create_task(
                    ladder_loop(
                        ld_conn,
                        cfg,
                        app.state.channels,
                        app.state.notifier,
                        app.state.ladder,
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

    @app.post("/twilio/inbound", response_class=PlainTextResponse)
    async def twilio_inbound(request: Request) -> PlainTextResponse:
        """A senior's reply to the ASK stage (spec 004 §3).

        Two things matter here and nothing else does. First, the request is
        genuinely Twilio's — an unsigned or mismatched call is a bare 403 that
        records nothing. Second, **the message body is dropped**. It is read only
        to compute the signature Twilio itself computed, and never stored,
        logged, or passed on. What resolves a candidate is that the right number
        answered at all; what they said is content, and this product does not
        hold content.
        """
        raw = (await request.body()).decode("utf-8", errors="replace")
        params = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}

        url = str(request.url)
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto == "https" and url.startswith("http://"):
            # Fly terminates TLS; Twilio signed the https URL it called.
            url = "https://" + url[len("http://") :]

        if not is_valid(
            cfg.twilio_auth_token,
            url,
            params,
            request.headers.get("x-twilio-signature"),
        ):
            raise StarletteHTTPException(status_code=403, detail="forbidden")

        sender = (params.get("From") or "").strip()
        # From here on, `params` is not consulted again — the body is gone.
        del params, raw

        with request.app.state.pool.connection() as conn:
            parent = db.parent_by_phone(conn, sender) if sender else None
            if parent is not None:
                resolve_by_senior_reply(
                    conn, request.app.state.notifier, parent, now_utc()
                )
        # Empty TwiML: acknowledged, and the senior gets no automated reply.
        return PlainTextResponse(
            '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml",
        )

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
