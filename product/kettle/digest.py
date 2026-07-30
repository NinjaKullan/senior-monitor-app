"""Digest engine — the two daily family-facing messages (spec 003).

Spec 003 §0 is the boundary this module lives inside: it may send reassurance
when routine IS observed, and nothing else. There is no code path here that
messages a family about the absence of activity, and none that messages the
senior at all. A parent with a quiet day is omitted from the family message and
surfaced to the founder through `ops_alerts` — the human handles it during beta,
and spec 004 owns whatever replaces that.

Two independent switches gate every send: the global `DIGEST_ENABLED` and each
family's `digest_enabled`, both off by default.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import psycopg

from kettle import db
from kettle.channels import DigestChannel
from kettle.config import Settings
from kettle.messages import render_evening, render_morning
from kettle.notify import Notifier
from kettle.timeutil import (
    effective_tz,
    local_day,
    local_day_bounds_utc,
    now_utc,
    to_local,
)

log = logging.getLogger("kettle.digest")

KIND_MORNING = "morning"
KIND_EVENING = "evening"

OPS_SKIPPED = "digest_skipped"
OPS_FAILED = "digest_delivery_failed"

STATUS_SENT = "sent"
STATUS_FAILED = "failed"


@dataclass(frozen=True)
class DigestSend:
    """One message, to one recipient, as recorded."""

    kind: str
    family_id: Any
    parent_id: Any | None
    member_id: Any
    channel: str
    status: str
    message: str


@dataclass
class DigestState:
    """In-process record of the last pass, for ops visibility only."""

    last_check_utc: datetime | None = None
    sent: list[DigestSend] = field(default_factory=list)


def _deliver(channel: DigestChannel, to_e164: str, message: str) -> bool:
    """Send, with exactly one retry. No retry storms — the next pass is hours away."""
    if channel.send(to_e164, message):
        return True
    log.info("digest send failed on channel %s, retrying once", channel.name)
    return channel.send(to_e164, message)


def _fan_out(
    conn: psycopg.Connection,
    channels: dict[str, DigestChannel],
    notifier: Notifier,
    family: dict[str, Any],
    recipients: list[dict[str, Any]],
    parent_id: Any | None,
    kind: str,
    local_date: date,
    message: str,
    now: datetime,
) -> list[DigestSend]:
    """Deliver one composed message to every recipient who has not had it."""
    results: list[DigestSend] = []
    for member in recipients:
        if db.digest_send_exists(
            conn, family["family_id"], parent_id, kind, local_date, member["member_id"]
        ):
            continue

        channel = channels.get(member["digest_channel"])
        if channel is None:  # 'none' is filtered out upstream; be defensive anyway
            continue

        ok = _deliver(channel, member["phone_e164"], message)
        status = STATUS_SENT if ok else STATUS_FAILED

        # Claim the slot before anything else can: the unique index is what makes
        # a mid-pass restart safe, so a lost race here means somebody else sent it.
        if not db.record_digest_send(
            conn,
            family["family_id"],
            parent_id,
            kind,
            local_date,
            member["member_id"],
            channel.name,
            status,
            now,
        ):
            continue

        if not ok:
            detail = (
                f"📵 {family['family_name']}: {kind} digest could not be delivered to "
                f"{member['member_name']} over {channel.name}."
            )
            db.insert_ops_alert(
                conn, family["family_id"], parent_id, OPS_FAILED, detail, now
            )
            notifier.send(detail)

        results.append(
            DigestSend(
                kind=kind,
                family_id=family["family_id"],
                parent_id=parent_id,
                member_id=member["member_id"],
                channel=channel.name,
                status=status,
                message=message,
            )
        )
    return results


def _morning(
    conn: psycopg.Connection,
    settings: Settings,
    channels: dict[str, DigestChannel],
    notifier: Notifier,
    family: dict[str, Any],
    parent: dict[str, Any],
    recipients: list[dict[str, Any]],
    now: datetime,
) -> list[DigestSend]:
    """'Day started' — only once the first alarm-grade ping of the day exists."""
    tz = effective_tz(parent["parent_tz"], family["family_tz"])
    day_start, _ = local_day_bounds_utc(now, tz)

    first = db.first_alarm_ping_between(conn, parent["parent_id"], day_start, now)
    if first is None:
        return []  # no evidence, no reassurance

    cutoff = settings.digest_morning_cutoff_hour
    # Both the ping and the moment of sending must be before the cutoff. A "good
    # morning" is noise at dinnertime whether the day started late or the server
    # was down until then; the evening summary covers the day either way.
    if to_local(first, tz).hour >= cutoff or to_local(now, tz).hour >= cutoff:
        return []

    message = render_morning(parent["parent_name"], to_local(first, tz))
    return _fan_out(
        conn,
        channels,
        notifier,
        family,
        recipients,
        parent["parent_id"],
        KIND_MORNING,
        date.fromisoformat(local_day(now, tz)),
        message,
        now,
    )


def _evening_due(settings: Settings, now: datetime, tz: str) -> bool:
    """Has this timezone reached the evening send time yet today?"""
    local = to_local(now, tz)
    return (local.hour, local.minute) >= (
        settings.digest_evening_hour,
        settings.digest_evening_minute,
    )


def _evening(
    conn: psycopg.Connection,
    settings: Settings,
    channels: dict[str, DigestChannel],
    notifier: Notifier,
    family: dict[str, Any],
    parents: list[dict[str, Any]],
    recipients: list[dict[str, Any]],
    now: datetime,
) -> list[DigestSend]:
    """Daily summary, one message per timezone group of a family.

    Parents are grouped by effective timezone because the send time is a local
    wall-clock hour: a parent visiting Chicago gets their summary on Chicago's
    evening, not Chennai's.
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    for parent in parents:
        tz = effective_tz(parent["parent_tz"], family["family_tz"])
        groups.setdefault(tz, []).append(parent)

    results: list[DigestSend] = []
    for tz, group in groups.items():
        if not _evening_due(settings, now, tz):
            continue

        local_date = date.fromisoformat(local_day(now, tz))
        day_start, _ = local_day_bounds_utc(now, tz)

        active, quiet = [], []
        for parent in group:
            seen = db.count_alarm_pings_between(conn, parent["parent_id"], day_start, now)
            (active if seen else quiet).append(parent)

        # A quiet parent is never mentioned to the family — the founder is told.
        for parent in quiet:
            _note_skipped(conn, notifier, family, parent, tz, now)

        if not active:
            continue

        # parent_id identifies a single-parent message; aggregated rows carry null,
        # matching the unique index's coalesce.
        parent_key = active[0]["parent_id"] if len(active) == 1 else None
        message = render_evening([p["parent_name"] for p in active])
        results.extend(
            _fan_out(
                conn,
                channels,
                notifier,
                family,
                recipients,
                parent_key,
                KIND_EVENING,
                local_date,
                message,
                now,
            )
        )
    return results


def _note_skipped(
    conn: psycopg.Connection,
    notifier: Notifier,
    family: dict[str, Any],
    parent: dict[str, Any],
    tz: str,
    now: datetime,
) -> None:
    """Tell the founder a parent was omitted. Once per parent per local day."""
    day_start, day_end = local_day_bounds_utc(now, tz)
    if db.ops_alert_exists(
        conn, OPS_SKIPPED, family["family_id"], parent["parent_id"], day_start, day_end
    ):
        return
    detail = (
        f"🔕 {family['family_name']} / {parent['parent_name']}: no alarm-grade pings "
        "today, omitted from the evening digest. Family was not told."
    )
    db.insert_ops_alert(
        conn, family["family_id"], parent["parent_id"], OPS_SKIPPED, detail, now
    )
    notifier.send(detail)


def run_digests(
    conn: psycopg.Connection,
    settings: Settings,
    channels: dict[str, DigestChannel],
    notifier: Notifier,
    now: datetime,
) -> list[DigestSend]:
    """One scheduler pass over every opted-in family.

    Idempotent through `digest_sends`, so passing every minute is safe and a
    process restart mid-pass cannot double-send.
    """
    if not settings.digest_enabled:
        return []  # global kill-switch

    results: list[DigestSend] = []
    for family in db.families_for_digest(conn):
        recipients = db.digest_recipients(conn, family["family_id"])
        if not recipients:
            continue
        parents = db.parents_for_family(conn, family["family_id"])

        for parent in parents:
            results.extend(
                _morning(
                    conn, settings, channels, notifier, family, parent, recipients, now
                )
            )
        results.extend(
            _evening(conn, settings, channels, notifier, family, parents, recipients, now)
        )
    return results


async def digest_loop(
    conn: psycopg.Connection,
    settings: Settings,
    channels: dict[str, DigestChannel],
    notifier: Notifier,
    state: DigestState,
    interval_s: int = 60,
) -> None:
    """Background task: one pass a minute. Never exits on error."""
    while True:
        try:
            now = now_utc()
            state.sent = await asyncio.to_thread(
                run_digests, conn, settings, channels, notifier, now
            )
            state.last_check_utc = now
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - the scheduler must outlive any failure
            log.exception("digest pass failed")
        await asyncio.sleep(interval_s)
