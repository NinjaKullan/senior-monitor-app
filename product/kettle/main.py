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

import psycopg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from starlette.exceptions import HTTPException as StarletteHTTPException

from kettle import db
from kettle.channels import build_channels
from kettle.config import Settings, settings_from_env
from kettle.digest import DigestState, digest_loop
from kettle.heartbeat import HeartbeatState, heartbeat_loop
from kettle.notify import LogOnlyNotifier, Notifier, NtfyNotifier
from kettle.timeutil import now_utc

log = logging.getLogger("kettle")

DEDUPE_WINDOW_S = 60


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

    @app.exception_handler(StarletteHTTPException)
    async def _plain_errors(
        request: Request, exc: StarletteHTTPException
    ) -> PlainTextResponse:
        """Plain-text errors: Shortcuts cope with them and they leak nothing."""
        return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

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

    @app.get("/healthz")
    async def healthz(request: Request) -> JSONResponse:
        """Liveness probe for Fly. No auth, no data."""
        with request.app.state.pool.connection() as conn:
            ok = db.healthy(conn)
        return JSONResponse({"db": ok}, status_code=200 if ok else 503)

    return app
