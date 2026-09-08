"""FastAPI ingestion service (spec 002 §3).

One public write route. The device token *is* the identity — there is no `who`
in the URL to guess, and a token resolves to exactly one device belonging to
exactly one person in exactly one family.
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager, suppress
from datetime import date, datetime, timedelta
from hmac import compare_digest
from urllib.parse import parse_qs

import httpx
import psycopg
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from mcp.server.transport_security import TransportSecuritySettings
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.routing import Route

from kettle import assistant_auth, assistant_tools, db, site_metrics, waitlist
from kettle.config import Settings, settings_from_env
from kettle.heartbeat import HeartbeatState, heartbeat_loop
from kettle.notify import LogOnlyNotifier, Notifier, NtfyNotifier
from kettle.outbound import (
    OutboundState,
    outbound_loop,
    record_inbound,
    transport_from_name,
)
from kettle.setup_page import router as setup_router
from kettle.timeutil import now_utc
from kettle.twilio_signature import verify_signature

log = logging.getLogger("kettle")

DEDUPE_WINDOW_S = 60
#: Spec 020 §4: the household address's token shape (the devices.device_token
#: shape); anything else on /d/ is a 404 like any unknown path.
HOUSEHOLD_TOKEN = re.compile(r"^[A-Za-z0-9_-]{20,}$")
#: Spec 020 §3: household pings are swept after thirty days. Nothing shown
#: reaches back further than today, and the setup row's heard line needs less.
HOUSEHOLD_SWEEP_DAYS = 30

#: The landing page's bot trap. A real person never fills it: it is hidden, and
#: it is named for something a form-filler expects to see rather than something
#: that announces itself as a trap.
HONEYPOT_FIELD = "company"


def _client_ip(request: Request) -> str | None:
    """Caller IP as seen behind the Fly proxy. Hashed immediately for the ping
    path, held only in process memory for the waitlist's flood counter (307);
    never stored raw."""
    forwarded = request.headers.get("fly-client-ip") or request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def create_app(
    settings: Settings | None = None,
    notifier: Notifier | None = None,
    clock: Callable[[], datetime] = now_utc,
    jwks_client: httpx.Client | None = None,
    cimd_client: httpx.Client | None = None,
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

    # Spec 019: the MCP server (the official SDK, stateless over Streamable
    # HTTP) and the authorization server in front of it. Built once here;
    # the session manager's own lifespan runs inside ours below.
    mcp_server = assistant_tools.build_server(lambda: app.state.pool.connection(), clock)
    mcp_asgi = mcp_server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        # Host checks belong to Fly's edge and the public URL, not to this
        # in-process app; the SDK's loopback-only default would refuse the
        # real host.
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        host="0.0.0.0",  # noqa: S104 - the SDK's flag for "not loopback-only"
    )
    oauth = assistant_auth.OAuthRoutes(
        cfg.public_base_url,
        cfg.app_origin,
        assistant_auth.JwksVerifier(cfg.supabase_jwks_url, jwks_client),
        clock,
        assistant_auth.ClientDocuments(cimd_client),
    )

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
            async with mcp_server.session_manager.run():
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
    # DECISIONS 307: the waitlist's per-caller counter, in process memory,
    # on the injected clock. Built here like the loop states; reset on restart.
    app.state.waitlist_flood = waitlist.FloodCounter()

    # CORS exists for exactly one route — the landing page's waitlist POST — and
    # is locked to the origins that page is served from. The ingest route needs
    # none of this: a Shortcut is not a browser and sends no Origin.
    # Spec 019 adds the family app's origin for /oauth/approve (and the
    # consent screen's lookup), with the Authorization header it carries.
    # One middleware, one explicit list, no wildcard.
    browser_origins = [*cfg.waitlist_origins, cfg.app_origin]
    if browser_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=browser_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["content-type", "authorization"],
        )

    @app.exception_handler(StarletteHTTPException)
    async def _plain_errors(request: Request, exc: StarletteHTTPException) -> PlainTextResponse:
        """Plain-text errors: Shortcuts cope with them and they leak nothing."""
        return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

    # The parent setup page (spec 005b): /s/{slug} and its live state check.
    app.include_router(setup_router)

    @app.api_route(
        "/p/{device_token}/{signal}",
        methods=["GET", "POST"],
        response_class=PlainTextResponse,
    )
    async def ingest(request: Request, device_token: str, signal: str) -> PlainTextResponse:
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

    @app.api_route("/d/{token}", methods=["GET", "POST"], response_class=PlainTextResponse)
    async def household_ping(request: Request, token: str) -> PlainTextResponse:
        """Spec 020 §4: the family's own device fired. Path only; query,
        headers and body are ignored, and no IP is read, hashed or stored.

        The reply is `ok` for a live, a removed, an unknown and a duplicate
        token alike, so the address never says whether it is real (311:
        dropped silently, never a 404). Only a wrong-shaped path is a 404.
        One recorded ping per device per DEDUPE_WINDOW_S, the guard inside
        the INSERT like the phone's. The thirty-day sweep rides this route
        (the only writer) the way the authorization sweep rides authorize:
        no engine or heartbeat module may name the table (§4).
        """
        if not HOUSEHOLD_TOKEN.match(token):
            raise StarletteHTTPException(status_code=404, detail="not found")
        now = clock()
        with request.app.state.pool.connection() as conn:
            conn.execute(
                "delete from household_pings where ts_utc < %s",
                (now - timedelta(days=HOUSEHOLD_SWEEP_DAYS),),
            )
            conn.execute(
                """
                insert into household_pings (device_id, ts_utc)
                select d.id, %(now)s from household_devices d
                where d.token = %(token)s and d.removed_utc is null
                  and not exists (
                      select 1 from household_pings h
                      where h.device_id = d.id and h.ts_utc > %(cutoff)s
                  )
                """,
                {"now": now, "token": token, "cutoff": now - timedelta(seconds=DEDUPE_WINDOW_S)},
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
        # Two ways in, both fail-closed (spec 007 §2.6, DECISIONS 163): the
        # shared secret (tests, break-glass), or Twilio's own request
        # signature when the auth token is configured — verified against the
        # public URL Twilio actually signed, not the proxied one Fly hands us.
        # With neither credential configured, the route does not exist.
        if not cfg.outbound_reply_token and not cfg.twilio_auth_token:
            raise StarletteHTTPException(status_code=404, detail="not found")

        raw = (await request.body()).decode("utf-8", errors="replace")
        params = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}

        supplied = request.headers.get("x-kettle-reply-token") or ""
        token_ok = bool(cfg.outbound_reply_token) and compare_digest(
            supplied, cfg.outbound_reply_token
        )
        signature = request.headers.get("x-twilio-signature") or ""
        public_url = cfg.public_base_url + request.url.path
        twilio_ok = verify_signature(cfg.twilio_auth_token, public_url, params, signature)
        if not (token_ok or twilio_ok):
            raise StarletteHTTPException(status_code=403, detail="forbidden")

        sender = (params.get("From") or "").strip()
        # Amendment A.5: Twilio's Advanced Opt-Out names the keyword it
        # handled; the body itself is still never read.
        opt_out_type = (params.get("OptOutType") or "").strip()
        # From here on the body is gone: it was read for signature verification,
        # the sender and the keyword flag, nothing else, per §2.6.
        del params, raw

        if sender:
            with request.app.state.pool.connection() as conn:
                record_inbound(
                    conn,
                    sender,
                    opt_out_type,
                    clock(),
                    notifier=request.app.state.notifier,
                    note_first_reply=cfg.memory_first_reply,
                )
        return PlainTextResponse("", status_code=204)

    @app.post("/site-metrics/daily", response_class=PlainTextResponse)
    async def site_metrics_daily(request: Request) -> PlainTextResponse:
        """The site container ships a day's counts (DECISIONS 201/211/212).

        The only writer is site/counter/kettle_counter.py, running beside nginx
        in the site image. What arrives is `{"day": "2026-08-31", "counts":
        {"/": 12, "other": 3}}` and nothing else — no request lines, no
        addresses, no user agents, because the log format the counter reads
        never contained any.

        Fail-closed like every other authenticated route here: with no token
        configured the endpoint does not exist, and a wrong token is a 401
        rather than a hint. `compare_digest` because a token check that leaks
        its answer in timing is not a token check.
        """
        if not cfg.site_metrics_token:
            raise StarletteHTTPException(status_code=404, detail="not found")
        supplied = request.headers.get("x-kettle-metrics-token") or ""
        if not compare_digest(supplied, cfg.site_metrics_token):
            raise StarletteHTTPException(status_code=401, detail="unauthorized")

        try:
            payload = await request.json()
        except ValueError:
            raise StarletteHTTPException(status_code=400, detail="malformed request") from None
        if not isinstance(payload, dict):
            raise StarletteHTTPException(status_code=400, detail="malformed request")

        raw_day = payload.get("day")
        counts = payload.get("counts")
        if not isinstance(raw_day, str) or not isinstance(counts, dict):
            raise StarletteHTTPException(status_code=400, detail="malformed request")
        try:
            day = date.fromisoformat(raw_day)
        except ValueError:
            raise StarletteHTTPException(status_code=400, detail="malformed day") from None
        if len(counts) > site_metrics.MAX_PATHS_PER_POST:
            raise StarletteHTTPException(status_code=400, detail="too many paths")

        with request.app.state.pool.connection() as conn:
            written = site_metrics.record_daily(conn, day, counts)
        # The count of rows written, not the counts themselves: this route is
        # a write, and an endpoint that echoes the numbers back is a read the
        # token was not issued for.
        return PlainTextResponse(str(written))

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

        Two flood guards sit in front (DECISIONS 307), and both answer with
        the success sentence: a few POSTs per caller per rolling hour, checked
        before the body is read, and a ceiling on the table. Nothing is
        recorded on either path — no row, no alert, no log line.
        """
        if not request.app.state.waitlist_flood.allow(_client_ip(request) or "", clock()):
            return PlainTextResponse(waitlist.WAITLIST_SUCCESS)
        content_type = request.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            try:
                payload = await request.json()
            except ValueError:
                raise StarletteHTTPException(status_code=400, detail="malformed request") from None
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

    # --- spec 019: the assistant door ------------------------------------------

    @app.get("/.well-known/oauth-protected-resource")
    async def protected_resource() -> JSONResponse:
        return JSONResponse(assistant_auth.protected_resource_metadata(cfg.public_base_url))

    @app.get("/.well-known/oauth-authorization-server")
    async def authorization_server() -> JSONResponse:
        return JSONResponse(assistant_auth.authorization_server_metadata(cfg.public_base_url))

    app.add_api_route("/oauth/register", oauth.register, methods=["POST"])
    app.add_api_route("/oauth/authorize", oauth.authorize, methods=["GET"])
    app.add_api_route("/oauth/token", oauth.token, methods=["POST"])
    app.add_api_route("/oauth/approve", oauth.approve, methods=["POST"])
    app.add_api_route("/oauth/pending", oauth.pending, methods=["GET"])

    class GuardedMcp:
        """The bearer check in front of the SDK app (§4): a missing or dead
        token is a 401 with the resource_metadata header, never a tool error.
        A live one resolves to exactly one person for the length of the
        request, through CURRENT_USER.

        An exact Route rather than a Mount (DECISIONS 286): a Mount answers
        /mcp with a 307 to /mcp/ BEFORE anything here runs, so an assistant
        following the redirect never saw the header it discovers the
        authorization server from. A class, because Starlette treats a plain
        function endpoint as a request handler and an object as an ASGI app.
        """

        async def __call__(self, scope, receive, send):  # type: ignore[no-untyped-def]
            headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
            auth = headers.get("authorization", "")
            user = None
            if auth.lower().startswith("bearer "):
                with app.state.pool.connection() as conn:
                    user = assistant_auth.resolve_bearer(conn, auth[7:].strip(), clock())
            if user is None:
                response = PlainTextResponse(
                    "unauthorized",
                    status_code=401,
                    headers={
                        "WWW-Authenticate": assistant_auth.www_authenticate(cfg.public_base_url)
                    },
                )
                await response(scope, receive, send)
                return
            token = assistant_tools.CURRENT_USER.set(user)
            try:
                await mcp_asgi(scope, receive, send)
            finally:
                assistant_tools.CURRENT_USER.reset(token)

    app.router.routes.append(
        Route("/mcp", endpoint=GuardedMcp(), methods=["GET", "POST", "DELETE"])
    )

    @app.get("/healthz")
    async def healthz(request: Request) -> JSONResponse:
        """Liveness probe for Fly. No auth, no data."""
        with request.app.state.pool.connection() as conn:
            ok = db.healthy(conn)
        return JSONResponse({"db": ok}, status_code=200 if ok else 503)

    return app
