"""Heartbeat v2 — ops-only, multi-tenant (spec 002 §4).

The pilot's rules, generalized: every check runs on the clock of the person it
is about, so a family in Chennai and a family in Chicago each get their own
local noon, and a parent visiting Texas gets Texas noon while their family stays
on IST.

No thresholds, no percentiles, no inference of any kind — fixed local wall-clock
rules only (product law #1). Nothing family- or parent-facing fires from here;
the escalation ladder is spec 004 and is unbuilt (product law #3).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import psycopg

from kettle import db, site_metrics, template_watch
from kettle.config import Settings
from kettle.notify import Notifier
from kettle.timeutil import (
    effective_tz,
    humanize_gap,
    local_day_bounds_utc,
    local_hour,
    local_time_on_day_utc,
    now_utc,
)

log = logging.getLogger("kettle.heartbeat")

# Wall-clock rules, evaluated in each person's own local time.
DAY_START_HOUR = 5  # "this morning" begins at 05:00 local
NOON_HOUR = 12
EVENING_HOUR = 20
INFRA_SILENCE = timedelta(hours=24)

KIND_NOON = "noon"
KIND_EVENING = "evening"
KIND_INFRA = "infra"


@dataclass(frozen=True)
class Fired:
    """One alert that fired on this pass."""

    kind: str
    family_id: Any
    parent_id: Any | None
    detail: str


@dataclass
class HeartbeatState:
    """In-process record of the last pass, for ops visibility."""

    last_check_utc: datetime | None = None
    fired: list[Fired] = field(default_factory=list)
    template_watch: template_watch.WatchState = field(
        default_factory=template_watch.WatchState
    )


def _last_seen_phrase(conn: psycopg.Connection, parent_id: Any, now: datetime) -> str:
    """'2h 14m ago' since this person's last alarm-grade ping, or 'never'."""
    last = db.last_alarm_ping(conn, parent_id)
    if last is None:
        return "never"
    return f"{humanize_gap((now - last).total_seconds())} ago"


def _fire(
    conn: psycopg.Connection,
    notifier: Notifier,
    kind: str,
    family_id: Any,
    parent_id: Any | None,
    detail: str,
    now: datetime,
) -> Fired:
    """Record the alert, then attempt delivery to the founder."""
    db.insert_ops_alert(conn, family_id, parent_id, kind, detail, now)
    notifier.send(detail)
    log.info("ops alert kind=%s family=%s parent=%s", kind, family_id, parent_id)
    return Fired(kind=kind, family_id=family_id, parent_id=parent_id, detail=detail)


def _person_checks(
    conn: psycopg.Connection,
    notifier: Notifier,
    parent: dict[str, Any],
    now: datetime,
) -> list[Fired]:
    """Noon and evening checks for one parent, on that parent's own clock."""
    tz = effective_tz(parent["parent_tz"], parent["family_tz"])
    hour = local_hour(now, tz)
    if hour not in (NOON_HOUR, EVENING_HOUR):
        return []

    family_id, parent_id = parent["family_id"], parent["parent_id"]
    day_start, day_end = local_day_bounds_utc(now, tz)
    morning_start = local_time_on_day_utc(now, tz, DAY_START_HOUR)
    label = f"{parent['family_name']} / {parent['parent_name']}"

    def already(kind: str) -> bool:
        return db.ops_alert_exists(conn, kind, family_id, parent_id, day_start, day_end)

    # Noon: nothing alarm-grade since 05:00 local.
    if hour == NOON_HOUR:
        if already(KIND_NOON):
            return []
        if db.count_alarm_pings_between(conn, parent_id, morning_start, now) > 0:
            return []
        detail = (
            f"⚠️ {label}: no routine pings this morning "
            f"(last seen {_last_seen_phrase(conn, parent_id, now)}, tz {tz}). "
            "Check the Shortcut."
        )
        return [_fire(conn, notifier, KIND_NOON, family_id, parent_id, detail, now)]

    # Evening: escalates an already-fired noon concern, nothing else.
    if already(KIND_EVENING) or not already(KIND_NOON):
        return []
    if db.count_alarm_pings_between(conn, parent_id, morning_start, now) > 0:
        return []
    detail = (
        f"⚠️ {label}: still no routine pings today "
        f"(last seen {_last_seen_phrase(conn, parent_id, now)}, tz {tz}). "
        "Check the Shortcut."
    )
    return [_fire(conn, notifier, KIND_EVENING, family_id, parent_id, detail, now)]


def _infra_check(
    conn: psycopg.Connection,
    notifier: Notifier,
    family: dict[str, Any],
    now: datetime,
) -> list[Fired]:
    """Whole-family pipeline silence, on the family clock.

    Suppressed until the family's first-ever ping: an empty family is one whose
    phones are not set up yet, not a broken pipeline, and a daily 🔧 during
    onboarding would only teach the founder to ignore the alert.
    """
    family_id = family["family_id"]
    day_start, day_end = local_day_bounds_utc(now, family["family_tz"])
    if db.ops_alert_exists(conn, KIND_INFRA, family_id, None, day_start, day_end):
        return []

    last = db.family_last_ping(conn, family_id)
    if last is None or (now - last) < INFRA_SILENCE:
        return []

    detail = (
        f"🔧 {family['family_name']}: pipeline silent 24h — "
        "server up but nothing arriving from any device."
    )
    return [_fire(conn, notifier, KIND_INFRA, family_id, None, detail, now)]


def run_checks(
    conn: psycopg.Connection,
    settings: Settings,
    notifier: Notifier,
    now: datetime,
) -> list[Fired]:
    """Run every heartbeat rule that applies at `now`, for every family.

    Idempotent per (kind, parent, local day), so calling this every minute is
    safe. The clock is an argument rather than a global so tests can drive exact
    local instants in several timezones at once.
    """
    fired: list[Fired] = []
    for parent in db.parents_with_tz(conn):
        fired.extend(_person_checks(conn, notifier, parent, now))
    for family in db.families_with_tz(conn):
        fired.extend(_infra_check(conn, notifier, family, now))
    return fired


async def heartbeat_loop(
    conn: psycopg.Connection,
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
            state.last_check_utc = now
            # The weekly site summary rides THIS loop, not the outbound one
            # (DECISIONS 212). Both are "the existing scheduler", but the
            # outbound loop is gated behind OUTBOUND_ENABLED, the kill switch
            # on family sending — a founder-only ops note must not be silenced
            # by the switch that stops messages to families, and must not be
            # revived by the one that starts them. This loop is already the
            # founder-only channel, so the note belongs here.
            await asyncio.to_thread(site_metrics.maybe_send_weekly, conn, settings, now)
            # The ask template's category, once a day (DECISIONS 262). Same
            # reasoning as the weekly summary: founder-only, so it rides the
            # founder-only loop and neither outbound switch can silence it.
            await asyncio.to_thread(
                template_watch.maybe_check,
                conn,
                settings,
                notifier,
                state.template_watch,
                now,
            )
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - the monitor must outlive any failure
            log.exception("heartbeat pass failed")
        await asyncio.sleep(interval_s)
