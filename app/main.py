"""FastAPI application — spec 001, pilot webhook backend.

Every write path here is allowlisted by hand. A request may carry any query
params it likes; only `who` and `signal` are ever read, and only `who`,
`signal`, a server-side UTC timestamp and a salted IP hash are ever stored.
"""

from __future__ import annotations

import asyncio
import csv
import io
import logging
import secrets
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from urllib.parse import parse_qs, quote

from fastapi import FastAPI, Request, Response
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import db, views
from app.config import ALARM_GRADE, PEOPLE, SIGNALS, Settings, settings_from_env
from app.heartbeat import HeartbeatState, heartbeat_loop
from app.notify import LogOnlyNotifier, Notifier, NtfyNotifier
from app.timeutil import (
    date_local,
    fmt_display,
    fmt_display_iso,
    fmt_utc,
    humanize_gap,
    local_day_bounds_utc,
    now_utc,
    parse_utc,
)

log = logging.getLogger("kettle")

RECENT_LIMIT = 50
DEDUPE_WINDOW_S = 60
SAFE_REDIRECTS = ("/status", "/labels")


def _forbidden() -> StarletteHTTPException:
    """403 with a body that says nothing about why."""
    return StarletteHTTPException(status_code=403, detail="forbidden")


def _check_token(settings: Settings, token: str | None) -> None:
    """Constant-time shared-secret check. Raises before any DB work happens."""
    if not token or not secrets.compare_digest(token, settings.ping_token):
        raise _forbidden()


def _client_ip(request: Request) -> str | None:
    """Caller IP as seen behind the Fly proxy. Hashed immediately, never stored raw."""
    forwarded = request.headers.get("fly-client-ip") or request.headers.get(
        "x-forwarded-for"
    )
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


async def _form_values(request: Request) -> dict[str, str]:
    """Parse an urlencoded POST body without pulling in a multipart dependency."""
    raw = (await request.body()).decode("utf-8", errors="replace")
    return {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}


def _param(request: Request, form: dict[str, str], name: str) -> str | None:
    """Read a parameter from the query string, falling back to the form body."""
    value = request.query_params.get(name)
    if value is None:
        value = form.get(name)
    return value


def create_app(settings: Settings | None = None, notifier: Notifier | None = None) -> FastAPI:
    """Build the application. `settings`/`notifier` are injectable for tests."""
    cfg = settings or settings_from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        conn = db.connect(cfg.db_path)
        db.init_schema(conn)
        app.state.conn = conn
        app.state.heartbeat = HeartbeatState()
        app.state.notifier = notifier or (
            NtfyNotifier(cfg.ntfy_topic) if cfg.ntfy_topic else LogOnlyNotifier()
        )
        task: asyncio.Task[None] | None = None
        hb_conn: sqlite3.Connection | None = None
        if cfg.heartbeat_loop:
            # Its own connection: the loop runs in a worker thread.
            hb_conn = db.connect(cfg.db_path)
            task = asyncio.create_task(
                heartbeat_loop(hb_conn, cfg, app.state.notifier, app.state.heartbeat)
            )
        try:
            yield
        finally:
            if task is not None:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            if hb_conn is not None:
                hb_conn.close()
            conn.close()

    app = FastAPI(
        title="Kettle pilot backend",
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
        """Errors are plain text — iOS Shortcuts choke on nothing, and bodies leak nothing."""
        return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

    def conn_of(request: Request) -> sqlite3.Connection:
        return request.app.state.conn

    # --- /ping --------------------------------------------------------------

    @app.api_route("/ping", methods=["GET", "POST"], response_class=PlainTextResponse)
    async def ping(request: Request) -> PlainTextResponse:
        """Record one content-free routine ping. Extra query params are ignored."""
        form = await _form_values(request) if request.method == "POST" else {}
        _check_token(cfg, _param(request, form, "token"))

        who = (_param(request, form, "who") or "").strip().lower()
        signal = (_param(request, form, "signal") or "").strip().lower()
        if who not in PEOPLE or signal not in SIGNALS:
            raise StarletteHTTPException(status_code=400, detail="bad who or signal")

        db.insert_ping(
            conn_of(request),
            who,
            signal,
            fmt_utc(now_utc()),
            db.hash_ip(_client_ip(request), cfg.ip_hash_salt),
            DEDUPE_WINDOW_S,
        )
        return PlainTextResponse("ok")

    # --- /status ------------------------------------------------------------

    @app.get("/status", response_class=HTMLResponse)
    async def status(request: Request, token: str | None = None) -> HTMLResponse:
        """Founder dashboard, gated behind today's blinded labels."""
        _check_token(cfg, token)
        conn = conn_of(request)
        now = now_utc()
        today = date_local(now, cfg.tz_display)

        # Blinding audit: every look is recorded, interstitial or not.
        db.insert_status_view(conn, today, fmt_utc(now))

        labelled = db.labelled_people(conn, today)
        missing = [who for who in PEOPLE if who not in labelled]
        if missing:
            done = [(r["who"], r["note"]) for r in db.labels_on(conn, today)]
            return HTMLResponse(views.interstitial(token or "", today, missing, done))

        return HTMLResponse(_render_status(conn, now, today, token or ""))

    def _render_status(
        conn: sqlite3.Connection, now: datetime, today: str, token: str
    ) -> str:
        tz = cfg.tz_display
        day_start, day_end = local_day_bounds_utc(today, tz)

        people = []
        for who in PEOPLE:
            signals = []
            for signal in SIGNALS:
                row = db.last_ping(conn, who, signal)
                if row is None:
                    signals.append(
                        {"signal": signal, "last_seen": "—", "gap": "never"}
                    )
                    continue
                seen = parse_utc(row["ts_utc"])
                signals.append(
                    {
                        "signal": signal,
                        "last_seen": fmt_display(seen, tz),
                        "gap": f"{humanize_gap((now - seen).total_seconds())} ago",
                    }
                )
            alarm = db.last_ping_in(conn, who, ALARM_GRADE)
            alarm_gap = (
                f"{humanize_gap((now - parse_utc(alarm['ts_utc'])).total_seconds())} ago"
                if alarm
                else "no alarm-grade ping yet"
            )
            people.append(
                {
                    "who": who,
                    "signals": signals,
                    "today_count": db.count_pings_between(conn, who, day_start, day_end),
                    "alarm_gap": alarm_gap,
                }
            )

        state: HeartbeatState = app.state.heartbeat
        last_alert_row = db.last_alert(conn)
        heartbeat = {
            "last_check": (
                f"{fmt_display(parse_utc(state.last_check_utc), tz)} IST"
                if state.last_check_utc
                else "not yet since restart"
            ),
            "last_alert": (
                f"{fmt_display(parse_utc(last_alert_row['ts_utc']), tz)} IST — "
                f"{last_alert_row['detail']}"
                if last_alert_row
                else "none"
            ),
        }

        recent = [
            [fmt_display(parse_utc(r["ts_utc"]), tz), r["who"], r["signal"]]
            for r in db.recent_pings(conn, RECENT_LIMIT)
        ]
        return views.status(
            token, fmt_display(now, tz), today, people, heartbeat, recent
        )

    # --- /labels ------------------------------------------------------------

    @app.api_route("/labels", methods=["GET", "POST"])
    async def labels(request: Request) -> Response:
        """Add or view blinded ground-truth labels."""
        form = await _form_values(request) if request.method == "POST" else {}
        token = _param(request, form, "token")
        _check_token(cfg, token)
        conn = conn_of(request)
        now = now_utc()
        today = date_local(now, cfg.tz_display)

        who = (_param(request, form, "who") or "").strip().lower()
        if who:
            if who not in PEOPLE:
                raise StarletteHTTPException(status_code=400, detail="bad who")
            note = (_param(request, form, "note") or "").strip() or "nothing unusual"
            date_ist = (_param(request, form, "date_ist") or "").strip() or today
            db.insert_label(conn, date_ist, who, note, fmt_utc(now))

            nxt = _param(request, form, "next") or "/status"
            if nxt not in SAFE_REDIRECTS:
                nxt = "/status"
            return RedirectResponse(
                f"{nxt}?token={quote(token or '', safe='')}", status_code=303
            )

        rows = [
            [
                r["date_ist"],
                r["who"],
                r["note"],
                fmt_display(parse_utc(r["created_utc"]), cfg.tz_display),
            ]
            for r in db.all_labels(conn)
        ]
        return HTMLResponse(views.labels_page(token or "", today, rows))

    @app.get("/labels.csv", response_class=PlainTextResponse)
    async def labels_csv(request: Request, token: str | None = None) -> PlainTextResponse:
        """Label log as CSV."""
        _check_token(cfg, token)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["date_ist", "who", "note", "created_utc", "created_ist"])
        for r in db.all_labels(conn_of(request)):
            created = parse_utc(r["created_utc"])
            writer.writerow(
                [
                    r["date_ist"],
                    r["who"],
                    r["note"],
                    r["created_utc"],
                    fmt_display_iso(created, cfg.tz_display),
                ]
            )
        return PlainTextResponse(buf.getvalue(), media_type="text/csv")

    # --- /pings/{who} -------------------------------------------------------

    @app.get("/pings/{who}", response_class=HTMLResponse)
    async def pings_for(
        request: Request, who: str, token: str | None = None
    ) -> HTMLResponse:
        """The transparency view: every ping ever recorded for one person."""
        _check_token(cfg, token)
        who = who.strip().lower()
        if who not in PEOPLE:
            raise StarletteHTTPException(status_code=404, detail="unknown person")
        rows = [
            [fmt_display(parse_utc(r["ts_utc"]), cfg.tz_display), r["signal"]]
            for r in db.pings_for(conn_of(request), who)
        ]
        return HTMLResponse(views.pings_page(token or "", who, rows))

    # --- /export.csv --------------------------------------------------------

    @app.get("/export.csv", response_class=PlainTextResponse)
    async def export_csv(request: Request, token: str | None = None) -> PlainTextResponse:
        """All pings as CSV — the Phase-1 analysis input."""
        _check_token(cfg, token)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["who", "signal", "ts_utc", "ts_ist"])
        for r in db.all_pings(conn_of(request)):
            ts = parse_utc(r["ts_utc"])
            writer.writerow(
                [r["who"], r["signal"], r["ts_utc"], fmt_display_iso(ts, cfg.tz_display)]
            )
        return PlainTextResponse(buf.getvalue(), media_type="text/csv")

    # --- /healthz -----------------------------------------------------------

    @app.get("/healthz")
    async def healthz(request: Request) -> JSONResponse:
        """Liveness probe for Fly. No token, no data."""
        ok = db.healthy(conn_of(request))
        return JSONResponse({"db": ok}, status_code=200 if ok else 503)

    return app
