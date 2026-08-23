"""The outbound channel, Wave A (spec 007 §2): decide, record, send nothing.

The site promises "you hear twice a day" and "asks them first, quietly". This
module is the decision core that makes both true, built so that the whole thing
runs in production before any external dependency exists: it evaluates the day,
writes its ledger, and hands each message to a `Transport` that, in this wave,
only writes a log line. Watching that ledger match reality for two days is the
gate to a real transport (§2.5).

Four properties are structural rather than remembered:

* **Parent-first cannot be skipped.** A follow-on is only reachable through a
  ledger row proving the ask already went, unanswered, more than the grace
  window ago. There is no branch that reaches the child first — law #6's ladder
  made out of a query rather than an ordering convention.
* **Nothing is interpreted.** A quiet morning is the *absence* of an
  alarm-grade ping in a window. This module never scores it, never compares it
  to another day, and never says what it might mean.
* **Charger events cannot speak.** The evaluator counts alarm-grade pings only,
  read from each parent's own allowlist, so household plumbing can corroborate
  on the health surface and never stands in for a person.
* **Sent once.** Every send goes through the ledger's unique index, so a
  scheduler that crashes and restarts mid-day re-decides and re-inserts nothing.

Wave A ships exactly one transport and it has no network client. Waves B–D add
real ones behind the same seam, each gated on a founder errand.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, time, timedelta
from typing import Any, Protocol
from zoneinfo import ZoneInfo

import psycopg

from kettle import db
from kettle.outbound_templates import (
    KIND_ASK,
    KIND_DIGEST_EVENING,
    KIND_DIGEST_MORNING,
    KIND_FOLLOW_ON,
    render,
    template,
)
from kettle.timeutil import effective_tz, now_utc, to_local

log = logging.getLogger("kettle.outbound")

# --- v1 constants (§2.1, §2.2). Per-family config is a later spec. -----------

#: The morning window opens here: nothing before it counts toward "the morning
#: happened", because a 03:00 ping is not a morning.
MORNING_WINDOW_START = time(6, 0)
#: When a quiet morning becomes a question addressed to her.
ASK_THRESHOLD = time(11, 0)
#: How long the ask gets to be answered before the child hears anything.
FOLLOW_ON_GRACE = timedelta(hours=2)
#: The two digests.
MORNING_DIGEST = time(8, 30)
EVENING_DIGEST = time(20, 30)


@dataclass(frozen=True)
class Schedule:
    """One parent's day, in UTC instants.

    All arithmetic lands here: every downstream comparison is between aware UTC
    datetimes, and the only place a wall clock appears is in building this. DST
    is the tz database's problem, which is why the local times above are
    `time` objects combined against a real local date rather than offsets.
    """

    local_date: str
    window_start: datetime
    morning_digest: datetime
    ask_threshold: datetime
    evening_digest: datetime


def schedule_for(now: datetime, tz_name: str) -> Schedule:
    """The schedule for the local day that `now` falls on, in `tz_name`."""
    tz = ZoneInfo(tz_name)
    day = to_local(now, tz_name).date()

    def at(wall: time) -> datetime:
        return datetime.combine(day, wall, tzinfo=tz).astimezone(UTC)

    return Schedule(
        local_date=day.isoformat(),
        window_start=at(MORNING_WINDOW_START),
        morning_digest=at(MORNING_DIGEST),
        ask_threshold=at(ASK_THRESHOLD),
        evening_digest=at(EVENING_DIGEST),
    )


# --- the transport seam (§2.5) -----------------------------------------------


@dataclass(frozen=True)
class DeliveryResult:
    """What a transport reports back. `delivered` gates the ledger write."""

    delivered: bool
    transport: str
    detail: str = ""


class Transport(Protocol):
    """Anything that can deliver one rendered template to one recipient."""

    name: str

    def send(
        self, to: str, template_id: str, variables: Mapping[str, str]
    ) -> DeliveryResult:
        """Deliver, and say whether it happened."""
        ...


class LogTransport:
    """Wave A's only transport: the engine runs dark.

    It reports `delivered=True` even with no address on file, and that is the
    point rather than an oversight — a dark run's ledger is a record of the
    *decisions* Kettle made, which is what the founder reviews for two days
    before anything real is wired up. A transport with a network client must do
    the opposite: no address means `delivered=False`, no ledger row, and the
    day's slot stays free for the day it can actually send.

    The address is masked on its way to the log. Logs do not need a family's
    phone number, and this one never gets it.
    """

    name = "log"

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send(
        self, to: str, template_id: str, variables: Mapping[str, str]
    ) -> DeliveryResult:
        body = render(template_id, variables)
        self.sent.append((template_id, body))
        log.info("outbound (dark): %s -> %s: %s", template_id, _mask(to), body)
        return DeliveryResult(delivered=True, transport=self.name)


def _mask(to: str) -> str:
    if not to:
        return "(no address on file)"
    return f"…{to[-4:]}" if len(to) > 4 else "…"


#: Every transport the loop can be configured to use, by the name OUTBOUND_TRANSPORT
#: carries. One entry until a wave adds another — and a new entry here is a spec
#: change, not a deploy-time discovery: the registry is what makes a misconfigured
#: name fail closed instead of falling through to something that can send.
TRANSPORTS: dict[str, Callable[[], Transport]] = {
    "console": LogTransport,
}


def transport_from_name(name: str) -> Transport:
    """Build the configured transport, or refuse to boot.

    Loud and at startup on purpose (DECISIONS 154): the alternative — defaulting
    an unknown name to *anything* — is a path by which a typo in an env var
    chooses who gets messaged. Known names are the registry's, nothing else.
    """
    try:
        factory = TRANSPORTS[name]
    except KeyError:
        known = ", ".join(sorted(TRANSPORTS))
        raise RuntimeError(
            f"unknown outbound transport {name!r} — registered transports: {known}"
        ) from None
    return factory()


# --- the evaluator (§2.1) ----------------------------------------------------


def is_quiet(
    conn: psycopg.Connection, parent_id: Any, start: datetime, end: datetime
) -> bool:
    """True when no alarm-grade ping arrived in [start, end).

    Absence, stated as absence. The grade comes from this parent's own
    allowlist, so charger and device_alive rows are invisible here by
    construction rather than by a filter someone could widen.
    """
    if end <= start:
        return True
    return db.count_alarm_pings_between(conn, parent_id, start, end) == 0


# --- the scheduler (§2.2) ----------------------------------------------------


@dataclass(frozen=True)
class Decision:
    """One message the run decided to send, after it was recorded."""

    family_id: Any
    parent_id: Any
    #: The label the child picked at setup (DECISIONS 149) — the only thing
    #: `{relationship}` ever renders, and None until the label is set.
    relationship: str | None
    local_date: str
    kind: str
    template_id: str


def run_outbound(
    conn: psycopg.Connection,
    transport: Transport,
    now: datetime,
    *,
    enabled: bool = True,
) -> list[Decision]:
    """Decide and record everything due for every parent, at instant `now`.

    Idempotent by construction: due-ness is a time comparison and sending goes
    through the ledger, so running twice at the same instant — or restarting
    after a crash — produces the same rows and the same messages. The returned
    list is what *this* run recorded, which is why a double run returns an empty
    second list rather than a duplicate of the first.
    """
    if not enabled:
        return []

    decisions: list[Decision] = []
    for parent in db.parents_with_tz(conn):
        tz_name = effective_tz(parent["parent_tz"], parent["family_tz"])
        plan = schedule_for(now, tz_name)
        contacts = db.outbound_contacts(conn, parent["family_id"])
        child_address = (contacts or {}).get("child_email") or ""

        for decision in _due_for_parent(conn, parent, plan, now):
            recipient = (
                db.parent_whatsapp(conn, parent["parent_id"]) or ""
                if decision.kind == KIND_ASK
                else child_address
            )
            # The template says which variables it takes; the caller does not
            # get to guess. A kind-based guess drifts the moment two templates
            # of one kind differ, which `digest_morning` already does.
            available = {"relationship": parent["relationship"] or ""}
            variables = {
                name: available[name] for name in template(decision.template_id).variables
            }
            if any(not value for value in variables.values()):
                # No relationship label on file (both live parents predate
                # migration 0014). A message with a blank where the label goes
                # is worse than one that waits, so skip without recording: the
                # day's slot stays free for the run after the label is set.
                log.warning(
                    "outbound: %s skipped for parent %s: no relationship label on file",
                    decision.template_id,
                    decision.parent_id,
                )
                continue
            result = transport.send(recipient, decision.template_id, variables)
            if not result.delivered:
                continue
            recorded = db.record_sent_message(
                conn,
                decision.family_id,
                decision.parent_id,
                decision.local_date,
                decision.kind,
                decision.template_id,
                result.transport,
                now,
            )
            if recorded:
                decisions.append(decision)
    return decisions


def _due_for_parent(
    conn: psycopg.Connection, parent: Any, plan: Schedule, now: datetime
) -> list[Decision]:
    """Which kinds are due for one parent right now, in ladder order."""
    family_id = parent["family_id"]
    parent_id = parent["parent_id"]

    def already(kind: str) -> Any:
        return db.sent_message(conn, family_id, parent_id, plan.local_date, kind)

    def decision(kind: str, template_id: str) -> Decision:
        return Decision(
            family_id=family_id,
            parent_id=parent_id,
            relationship=parent["relationship"],
            local_date=plan.local_date,
            kind=kind,
            template_id=template_id,
        )

    due: list[Decision] = []

    # The morning digest. Its variant is decided at digest time, not later: a
    # day that goes quiet after 08:30 does not rewrite the note already sent.
    if now >= plan.morning_digest and not already(KIND_DIGEST_MORNING):
        quiet_now = is_quiet(conn, parent_id, plan.window_start, plan.morning_digest)
        due.append(
            decision(
                KIND_DIGEST_MORNING,
                "digest_morning_quiet" if quiet_now else "digest_morning_normal",
            )
        )

    # The ask, addressed to her, if the morning never showed up.
    ask_row = already(KIND_ASK)
    if (
        now >= plan.ask_threshold
        and ask_row is None
        and is_quiet(conn, parent_id, plan.window_start, plan.ask_threshold)
    ):
        # `ask_row` stays None, which is what stops a follow-on firing in the
        # same run: the grace window is measured from a row that exists.
        due.append(decision(KIND_ASK, "ask_parent"))

    # The follow-on. Reachable only through an ask row that exists, went
    # unanswered, and is older than the grace window — parent-first as a query.
    if (
        ask_row is not None
        and ask_row["replied_utc"] is None
        and now >= ask_row["sent_utc"] + FOLLOW_ON_GRACE
        and is_quiet(conn, parent_id, plan.window_start, now)
        and not already(KIND_FOLLOW_ON)
    ):
        due.append(decision(KIND_FOLLOW_ON, "follow_on_family"))

    # The evening digest, last because the day is.
    if now >= plan.evening_digest and not already(KIND_DIGEST_EVENING):
        due.append(decision(KIND_DIGEST_EVENING, "digest_evening_normal"))

    return due


# --- reply intake (§2.6) -----------------------------------------------------


def record_parent_reply(
    conn: psycopg.Connection, number: str, now: datetime
) -> bool:
    """The parent answered. Cancels the pending follow-on; stores no content.

    The reply matches the parent's **pending** ask — the most recent ask that
    was sent, is unanswered, and whose follow-on has not gone yet — bounded to
    asks sent within the last 24 hours (spec 007 §2.6, DECISIONS 153). Calendar
    days do not appear in the match: an ask answered just after local midnight
    is the same conversation, which is the defect DECISIONS 145 pinned.

    Returns True only when a pending ask was actually marked answered. An
    unknown number changes nothing and says nothing back; a known number with
    no pending ask in the window is recorded as an arrival — a masked log
    line, timestamp only, never content — and cancels nothing: whatever that
    reply answers, it is not an open question of Kettle's, and un-answering
    is not a thing a late reply can do. Nothing calls this until Wave C.
    """
    parent = db.parent_by_whatsapp(conn, number) if number else None
    if parent is None:
        return False
    matched = db.record_reply(conn, parent["parent_id"], now)
    if not matched:
        log.info(
            "outbound: reply from %s with no pending ask; noted, nothing cancelled",
            _mask(number),
        )
    return matched


# --- the loop (§2.5): Wave A running dark in production -----------------------


@dataclass
class OutboundState:
    """In-process record of the last pass, for ops visibility.

    Same shape as `HeartbeatState`: the dark run's whole point is that the
    founder can see what the engine decided (the ledger is the durable record;
    this is the cheap live one).
    """

    last_run_utc: datetime | None = None
    decided: list[Decision] = field(default_factory=list)


async def outbound_loop(
    conn: psycopg.Connection,
    transport: Transport,
    settings: Any,
    state: OutboundState,
    interval_s: int = 60,
) -> None:
    """Background task: decide and record once a minute. Never exits on error.

    Wave A IS this loop running dark (spec 007 §2.5): console transport, ledger
    written, nothing sent — the 48-hour ledger review of §6.3 is a review of
    what this loop wrote. `run_outbound` is idempotent through the ledger's
    unique index, so a minutely cadence re-decides and re-records nothing.
    `OUTBOUND_ENABLED` is read every pass, live: it is the kill switch on the
    decisions, distinct from OUTBOUND_LOOP which merely runs the machinery.
    """
    while True:
        try:
            now = now_utc()
            state.decided = await asyncio.to_thread(
                run_outbound, conn, transport, now, enabled=settings.outbound_enabled
            )
            state.last_run_utc = now
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - the engine must outlive any failure
            log.exception("outbound pass failed")
        await asyncio.sleep(interval_s)
