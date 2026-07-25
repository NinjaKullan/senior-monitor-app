"""Heartbeat monitor — founder-only ops alerting.

This catches silently disabled iOS Shortcuts (the pilot's known fragility) and
is deliberately the simplest possible form of the product's core idea: notice
the *absence* of routine, never inspect its content.

No thresholds, no percentiles, no inference — fixed IST wall-clock rules only.
Phase-2 shadow alerting is a separate spec.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app import db
from app.config import ALARM_GRADE, PEOPLE, Settings
from app.notify import Notifier
from app.timeutil import (
    date_local,
    display_tz,
    fmt_utc,
    humanize_gap,
    local_day_bounds_utc,
    local_time_today_utc,
    now_utc,
    parse_utc,
)

log = logging.getLogger("kettle.heartbeat")

# Wall-clock rules, all IST.
DAY_START_HOUR = 5  # "this morning" begins at 05:00 IST
NOON_HOUR = 12
EVENING_HOUR = 20
INFRA_SILENCE = timedelta(hours=24)

KIND_NOON = "noon"
KIND_EVENING = "evening"
KIND_INFRA = "infra"

# Infra alerts are about the pipeline, not a person.
NO_PERSON = ""


@dataclass
class HeartbeatState:
    """In-process record of the last check, shown on /status."""

    last_check_utc: str | None = None
    fired: list[str] = field(default_factory=list)


def _last_seen_phrase(conn: sqlite3.Connection, who: str, now: datetime) -> str:
    """'2h 14m ago' since the person's last alarm-grade ping, or 'never'."""
    row = db.last_ping_in(conn, who, ALARM_GRADE)
    if row is None:
        return "never"
    gap = (now - parse_utc(row["ts_utc"])).total_seconds()
    return f"{humanize_gap(gap)} ago"


def _fire(
    conn: sqlite3.Connection,
    notifier: Notifier,
    kind: str,
    who: str,
    detail: str,
    now: datetime,
) -> None:
    """Record the alert, then attempt delivery to the founder."""
    db.insert_alert(conn, kind, who, detail, fmt_utc(now))
    notifier.send(detail)
    log.info("heartbeat alert kind=%s who=%s", kind, who or "-")


def run_checks(
    conn: sqlite3.Connection,
    settings: Settings,
    notifier: Notifier,
    now: datetime,
) -> list[str]:
    """Run every heartbeat rule that applies at `now`. Returns the kinds fired.

    Idempotent within an IST day: each (kind, who) can fire at most once, so
    calling this every minute is safe.
    """
    tz = settings.tz_display
    today_ist = date_local(now, tz)
    day_start, day_end = local_day_bounds_utc(today_ist, tz)
    morning_start = local_time_today_utc(now, tz, DAY_START_HOUR)
    now_s = fmt_utc(now)
    hour_ist = now.astimezone(display_tz(tz)).hour
    fired: list[str] = []

    def already(kind: str, who: str) -> bool:
        return db.alert_exists_between(conn, kind, who, day_start, day_end)

    # Noon check (12:00 IST): nothing alarm-grade since 05:00 IST.
    if hour_ist == NOON_HOUR:
        for who in PEOPLE:
            if already(KIND_NOON, who):
                continue
            seen = db.count_pings_between(conn, who, morning_start, now_s, ALARM_GRADE)
            if seen == 0:
                detail = (
                    f"⚠️ {who}: no routine pings this morning "
                    f"(last seen {_last_seen_phrase(conn, who, now)}). "
                    "Check Shortcut or check in."
                )
                _fire(conn, notifier, KIND_NOON, who, detail, now)
                fired.append(KIND_NOON)

    # Evening check (20:00 IST): only escalates an already-fired noon concern.
    if hour_ist == EVENING_HOUR:
        for who in PEOPLE:
            if already(KIND_EVENING, who) or not already(KIND_NOON, who):
                continue
            seen = db.count_pings_between(conn, who, morning_start, now_s, ALARM_GRADE)
            if seen == 0:
                detail = (
                    f"⚠️ {who}: still no routine pings today "
                    f"(last seen {_last_seen_phrase(conn, who, now)}). "
                    "Check Shortcut or check in."
                )
                _fire(conn, notifier, KIND_EVENING, who, detail, now)
                fired.append(KIND_EVENING)

    # Infra check (hourly): the whole pipeline is silent.
    if not already(KIND_INFRA, NO_PERSON):
        last = db.last_ping_any(conn)
        silent = last is None or (now - parse_utc(last["ts_utc"])) >= INFRA_SILENCE
        if silent:
            detail = "🔧 Pipeline silent 24h — server up but nothing arriving."
            _fire(conn, notifier, KIND_INFRA, NO_PERSON, detail, now)
            fired.append(KIND_INFRA)

    return fired


async def heartbeat_loop(
    conn: sqlite3.Connection,
    settings: Settings,
    notifier: Notifier,
    state: HeartbeatState,
    interval_s: int = 60,
) -> None:
    """Background task: apply the rules once a minute. Never exits on error."""
    while True:
        try:
            now = now_utc()
            state.fired = await asyncio.to_thread(
                run_checks, conn, settings, notifier, now
            )
            state.last_check_utc = fmt_utc(now)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - the monitor must outlive any single failure
            log.exception("heartbeat check failed")
        await asyncio.sleep(interval_s)
