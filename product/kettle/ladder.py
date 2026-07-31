"""Escalation ladder v1 — senior-first, shadow by default (spec 004).

The highest-stakes path in the product, so the shape of this module is built
around one property: **privilege escalates only by explicit founder action, per
family.** Three gates stand between a running server and a message reaching
anyone — the global `LADDER_ENABLED`, the family's `ladder_mode`, and (for
`live`) a database CHECK requiring `digest_enabled` first.

In `shadow` — the beta default and the mode every family starts in once enabled —
the full ladder runs, every transition is recorded, and the founder is told at
each step. Not one message leaves the building. That is not a flag checked at the
last moment before sending; the send helpers below take the mode and simply have
no path to a channel when it is `shadow`.

Law #6 holds: only person-attributed signals feed the ladder. Household or
plumbing signals decide `mechanism_ok` — whether the phone is alive enough to ask
— and never whether a person is fine.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any

import psycopg

from kettle import db
from kettle.channels import DigestChannel
from kettle.config import Settings
from kettle.ladder_messages import (
    render_all_clear,
    render_ask,
    render_contact_line,
    render_family_unanswered,
    render_family_unreachable,
)
from kettle.notify import Notifier
from kettle.timeutil import effective_tz, local_day, local_day_bounds_utc, now_utc, to_local

log = logging.getLogger("kettle.ladder")

# Daytime window: candidates are only *opened* between these local hours.
DAY_START_HOUR = 5
DAY_END_HOUR = 21

MODE_OFF = "off"
MODE_SHADOW = "shadow"
MODE_LIVE = "live"

STAGE_CANDIDATE = "candidate"
STAGE_ASK = "ask"
STAGE_ASK_SKIPPED = "ask_skipped"
STAGE_FAMILY_1 = "family_1"
STAGE_FAMILY_ALL = "family_all"
STAGE_RESOLVED = "resolved"

TRIGGER_DEADLINE = "deadline"
TRIGGER_MAX_GAP = "max_gap"

RESOLVED_BY_SENIOR = "resolved_by_senior"
RESOLVED_BY_ACTIVITY = "resolved_by_activity"
RESOLVED_MANUALLY = "resolved_manually"


@dataclass(frozen=True)
class Transition:
    """One stage change, as recorded."""

    candidate_id: int
    family_id: Any
    parent_id: Any
    stage: str
    mode: str
    detail: str
    sends: int = 0  # channel invocations this transition caused; always 0 in shadow


@dataclass
class LadderState:
    """In-process record of the last pass, for ops visibility only."""

    last_check_utc: datetime | None = None
    transitions: list[Transition] = field(default_factory=list)


# --- delivery ---------------------------------------------------------------


def _deliver(
    mode: str,
    channels: dict[str, DigestChannel],
    channel_name: str,
    to_e164: str | None,
    message: str,
) -> int:
    """Send, but only in live mode. Returns the number of channel invocations.

    Shadow returns before touching `channels` at all — the mode check is the
    first statement, not a condition wrapped around a send that could be
    refactored out from under it.
    """
    if mode != MODE_LIVE:
        return 0
    if not to_e164:
        return 0
    channel = channels.get(channel_name)
    if channel is None or not channel.available:
        return 0
    channel.send(to_e164, message)
    return 1


def _record(
    conn: psycopg.Connection,
    notifier: Notifier,
    candidate: dict[str, Any],
    family: dict[str, Any],
    stage: str,
    detail: str,
    now: datetime,
    sends: int = 0,
) -> Transition:
    """Write the ledger row and tell the founder. Both modes, every transition."""
    mode = candidate["mode"]
    db.insert_ladder_event(
        conn,
        candidate["id"],
        candidate["family_id"],
        candidate["parent_id"],
        stage,
        mode,
        detail,
        now,
    )
    prefix = "SHADOW" if mode == MODE_SHADOW else "LIVE"
    notifier.send(f"[{prefix} {family['family_name']}] {detail}")
    return Transition(
        candidate_id=candidate["id"],
        family_id=candidate["family_id"],
        parent_id=candidate["parent_id"],
        stage=stage,
        mode=mode,
        detail=detail,
        sends=sends,
    )


# --- rule v1 ----------------------------------------------------------------


def _is_daytime(local: datetime) -> bool:
    return DAY_START_HOUR <= local.hour < DAY_END_HOUR


def evaluate_rule(
    conn: psycopg.Connection, parent: dict[str, Any], tz: str, now: datetime
) -> str | None:
    """Rule v1. Returns the trigger name, or None when nothing has fired.

    Two conservative branches, both on per-parent columns so the pilot's
    percentile analysis can fit real values later without touching this code:

    * `deadline` — nothing alarm-grade since 05:00 local and the parent's
      personal deadline has passed.
    * `max_gap` — the gap since their last deliberate action exceeds their
      personal maximum, inside the daytime window.
    """
    local = to_local(now, tz)
    if not _is_daytime(local):
        return None

    day_start, _ = local_day_bounds_utc(now, tz)
    morning_start = datetime.combine(
        local.date(), time(DAY_START_HOUR, 0), tzinfo=local.tzinfo
    ).astimezone(now.tzinfo)

    seen_today = db.count_alarm_pings_between(conn, parent["parent_id"], morning_start, now)
    deadline: time = parent["alarm_deadline"]
    if seen_today == 0 and local.time() >= deadline:
        return TRIGGER_DEADLINE

    last = db.last_alarm_ping(conn, parent["parent_id"])
    if last is not None:
        gap = (now - last).total_seconds() / 60
        if gap > parent["max_gap_minutes"]:
            return TRIGGER_MAX_GAP
    del day_start
    return None


def _mechanism_ok(
    conn: psycopg.Connection, parent_id: Any, tz: str, now: datetime
) -> bool:
    """Is anything at all still arriving from this phone today?

    Timer and charger pings answer this and nothing else — they never say a
    person is fine (law #6). They decide whether we can ask, and which family
    copy is honest.
    """
    day_start, _ = local_day_bounds_utc(now, tz)
    return db.count_any_pings_between(conn, parent_id, day_start, now) > 0


# --- stage machine ----------------------------------------------------------


def _open_candidate(
    conn: psycopg.Connection,
    notifier: Notifier,
    family: dict[str, Any],
    parent: dict[str, Any],
    tz: str,
    trigger: str,
    local_date: date,
    now: datetime,
) -> tuple[dict[str, Any] | None, list[Transition]]:
    mechanism_ok = _mechanism_ok(conn, parent["parent_id"], tz, now)
    candidate = db.insert_candidate(
        conn,
        family["family_id"],
        parent["parent_id"],
        local_date,
        family["ladder_mode"],
        trigger,
        mechanism_ok,
        STAGE_CANDIDATE,
        now,
    )
    if candidate is None:  # today's candidate already exists
        return None, []
    detail = (
        f"{parent['parent_name']}: candidate opened ({trigger}), "
        f"phone {'responding' if mechanism_ok else 'unreachable'}"
    )
    return candidate, [
        _record(conn, notifier, candidate, family, STAGE_CANDIDATE, detail, now)
    ]


def _family_message(
    conn: psycopg.Connection,
    family: dict[str, Any],
    parent: dict[str, Any],
    candidate: dict[str, Any],
    with_contact: bool,
) -> str:
    contact = ""
    if with_contact:
        row = db.family_contact(conn, family["family_id"])
        if row:
            contact = render_contact_line(row["name"], row["relation"], row["phone_e164"])
    if candidate["mechanism_ok"]:
        return render_family_unanswered(parent["parent_name"], contact=contact)
    return render_family_unreachable(parent["parent_name"], contact=contact)


def _advance(
    conn: psycopg.Connection,
    settings: Settings,
    channels: dict[str, DigestChannel],
    notifier: Notifier,
    family: dict[str, Any],
    parent: dict[str, Any],
    candidate: dict[str, Any],
    now: datetime,
) -> list[Transition]:
    """Walk a candidate as far as the clock currently allows."""
    mode = candidate["mode"]
    transitions: list[Transition] = []
    recipients = db.ladder_recipients(conn, family["family_id"])

    for _ in range(4):  # bounded: candidate → ask → family_1 → family_all
        stage = candidate["stage"]

        if stage == STAGE_CANDIDATE:
            if parent["phone_e164"] and candidate["mechanism_ok"]:
                sends = _deliver(
                    mode,
                    channels,
                    "sms",
                    parent["phone_e164"],
                    render_ask(parent["parent_name"]),
                )
                candidate = db.set_candidate_stage(
                    conn, candidate["id"], STAGE_ASK, "ask_utc", now
                )
                transitions.append(
                    _record(
                        conn,
                        notifier,
                        candidate,
                        family,
                        STAGE_ASK,
                        f"{parent['parent_name']}: check-in sent to their phone, "
                        f"waiting {parent['grace_minutes']} minutes",
                        now,
                        sends,
                    )
                )
                continue

            reason = (
                "no phone number on file"
                if not parent["phone_e164"]
                else "phone unreachable — cannot ask a silent handset"
            )
            candidate = db.set_candidate_stage(
                conn, candidate["id"], STAGE_ASK_SKIPPED, None, now
            )
            transitions.append(
                _record(
                    conn,
                    notifier,
                    candidate,
                    family,
                    STAGE_ASK_SKIPPED,
                    f"{parent['parent_name']}: check-in skipped — {reason}",
                    now,
                )
            )
            continue

        if stage == STAGE_ASK:
            due = candidate["ask_utc"] + timedelta(minutes=parent["grace_minutes"])
            if now < due:
                break
            candidate = _to_family_1(
                conn, channels, notifier, family, parent, candidate, recipients, now,
                transitions,
            )
            continue

        if stage == STAGE_ASK_SKIPPED:
            # Nothing to wait for: there was no ask to answer.
            candidate = _to_family_1(
                conn, channels, notifier, family, parent, candidate, recipients, now,
                transitions,
            )
            continue

        if stage == STAGE_FAMILY_1:
            due = candidate["family_1_utc"] + timedelta(
                minutes=parent["family_gap_minutes"]
            )
            if now < due or len(recipients) <= 1:
                break
            message = _family_message(conn, family, parent, candidate, with_contact=True)
            sends = sum(
                _deliver(mode, channels, m["digest_channel"], m["phone_e164"], message)
                for m in recipients[1:]
            )
            candidate = db.set_candidate_stage(
                conn, candidate["id"], STAGE_FAMILY_ALL, "family_all_utc", now
            )
            transitions.append(
                _record(
                    conn,
                    notifier,
                    candidate,
                    family,
                    STAGE_FAMILY_ALL,
                    f"{parent['parent_name']}: remaining family circle notified",
                    now,
                    sends,
                )
            )
            continue

        break

    return transitions


def _to_family_1(
    conn: psycopg.Connection,
    channels: dict[str, DigestChannel],
    notifier: Notifier,
    family: dict[str, Any],
    parent: dict[str, Any],
    candidate: dict[str, Any],
    recipients: list[dict[str, Any]],
    now: datetime,
    transitions: list[Transition],
) -> dict[str, Any]:
    message = _family_message(conn, family, parent, candidate, with_contact=False)
    sends = 0
    if recipients:
        first = recipients[0]
        sends = _deliver(
            candidate["mode"], channels, first["digest_channel"], first["phone_e164"], message
        )
    candidate = db.set_candidate_stage(
        conn, candidate["id"], STAGE_FAMILY_1, "family_1_utc", now
    )
    transitions.append(
        _record(
            conn,
            notifier,
            candidate,
            family,
            STAGE_FAMILY_1,
            f"{parent['parent_name']}: first family contact notified",
            now,
            sends,
        )
    )
    return candidate


def _try_resolve_by_activity(
    conn: psycopg.Connection,
    channels: dict[str, DigestChannel],
    notifier: Notifier,
    family: dict[str, Any],
    parent: dict[str, Any],
    candidate: dict[str, Any],
    now: datetime,
) -> list[Transition]:
    """Any deliberate action from the parent closes the candidate."""
    since = db.count_alarm_pings_between(
        conn, parent["parent_id"], candidate["opened_utc"], now
    )
    if since == 0:
        return []

    family_was_told = candidate["family_1_utc"] is not None
    resolved = db.resolve_candidate(conn, candidate["id"], RESOLVED_BY_ACTIVITY, now)
    if resolved is None:
        return []

    sends = 0
    if family_was_told:
        message = render_all_clear(parent["parent_name"])
        for member in db.ladder_recipients(conn, family["family_id"]):
            sends += _deliver(
                resolved["mode"], channels, member["digest_channel"],
                member["phone_e164"], message,
            )
    detail = (
        f"{parent['parent_name']}: resolved — routine resumed"
        + (", all-clear sent" if family_was_told else "")
    )
    return [_record(conn, notifier, resolved, family, STAGE_RESOLVED, detail, now, sends)]


# --- entry points -----------------------------------------------------------


def run_ladder(
    conn: psycopg.Connection,
    settings: Settings,
    channels: dict[str, DigestChannel],
    notifier: Notifier,
    now: datetime,
) -> list[Transition]:
    """One pass over every family with the ladder switched on."""
    if not settings.ladder_enabled:
        return []  # global kill-switch

    transitions: list[Transition] = []
    for family in db.families_for_ladder(conn):
        for parent in db.ladder_parents(conn, family["family_id"]):
            tz = effective_tz(parent["parent_tz"], family["family_tz"])
            local_date = date.fromisoformat(local_day(now, tz))
            candidate = db.candidate_for_day(conn, parent["parent_id"], local_date)

            if candidate is None:
                trigger = evaluate_rule(conn, parent, tz, now)
                if trigger is None:
                    continue
                candidate, opened = _open_candidate(
                    conn, notifier, family, parent, tz, trigger, local_date, now
                )
                transitions.extend(opened)
                if candidate is None:
                    continue

            if candidate["resolved_utc"] is not None:
                continue

            resolved = _try_resolve_by_activity(
                conn, channels, notifier, family, parent, candidate, now
            )
            if resolved:
                transitions.extend(resolved)
                continue

            transitions.extend(
                _advance(conn, settings, channels, notifier, family, parent, candidate, now)
            )
    return transitions


def resolve_by_senior_reply(
    conn: psycopg.Connection,
    notifier: Notifier,
    parent: dict[str, Any],
    now: datetime,
) -> bool:
    """A reply from the senior's own number, inside grace, closes the candidate.

    The reply's *content* never reaches this function. The webhook drops the body
    before calling; what resolves a candidate is that the right number answered
    at all.
    """
    candidate = db.open_candidate_for_parent(conn, parent["parent_id"])
    if candidate is None or candidate["stage"] != STAGE_ASK:
        return False
    due = candidate["ask_utc"] + timedelta(minutes=parent["grace_minutes"])
    if now > due:
        return False

    resolved = db.resolve_candidate(conn, candidate["id"], RESOLVED_BY_SENIOR, now)
    if resolved is None:
        return False

    family = {
        "family_id": parent["family_id"],
        "family_name": parent["family_name"],
    }
    # The family is told nothing: for them the silence was never broken.
    _record(
        conn,
        notifier,
        resolved,
        family,
        STAGE_RESOLVED,
        f"{parent['parent_name']}: answered the check-in — resolved, family not contacted",
        now,
    )
    return True


async def ladder_loop(
    conn: psycopg.Connection,
    settings: Settings,
    channels: dict[str, DigestChannel],
    notifier: Notifier,
    state: LadderState,
    interval_s: int = 60,
) -> None:
    """Background task: one pass a minute. Never exits on error."""
    while True:
        try:
            now = now_utc()
            state.transitions = await asyncio.to_thread(
                run_ladder, conn, settings, channels, notifier, now
            )
            state.last_check_utc = now
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - the ladder must outlive any failure
            log.exception("ladder pass failed")
        await asyncio.sleep(interval_s)
