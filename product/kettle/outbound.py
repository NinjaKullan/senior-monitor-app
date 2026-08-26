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
from kettle.notify import Notifier
from kettle.outbound_templates import (
    KIND_ALL_CLEAR,
    KIND_ASK,
    KIND_DIGEST_EVENING,
    KIND_DIGEST_MORNING,
    KIND_FOLLOW_ON,
    KINDS,
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
#: How late a morning digest may be decided and still sent (DECISIONS 159's
#: v1 constant: two hours, so nothing "about this morning" goes out after
#: 10:30 local). Past it the slot is skipped with an ops alert — a scheduler
#: catching up after downtime reports to the founder, not to the family.
MORNING_STALE_CUTOFF = timedelta(hours=2)


@dataclass(frozen=True)
class Schedule:
    """One parent's day, in UTC instants.

    All arithmetic lands here: every downstream comparison is between aware UTC
    datetimes, and the only place a wall clock appears is in building this. DST
    is the tz database's problem, which is why the local times above are
    `time` objects combined against a real local date rather than offsets.
    """

    local_date: str
    #: Local midnight — the "whole day" bound the unreachable distinction
    #: reads (DECISIONS 161/163): a 03:00 ping is not a morning, but it IS a
    #: phone that reported today.
    day_start: datetime
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
        day_start=at(time(0, 0)),
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
    """Anything that can deliver one rendered template to one recipient.

    `kinds` declares which message kinds it carries — a kind outside it is
    recorded as skipped, never attempted, which is how asks and follow-ons
    stay visibly undeliverable until Wave C gives them a channel.
    `requires_address` is False only for the dark transport: a real sender
    with no address on file is an unroutable skip, not an attempt.
    """

    name: str
    kinds: tuple[str, ...]
    requires_address: bool

    def send(
        self,
        to: str,
        template_id: str,
        variables: Mapping[str, str],
        relationship: str | None = None,
    ) -> DeliveryResult:
        """Deliver, and say whether it happened.

        `relationship` is whose day the message is about — the email
        transport's subject line and name chip (email-polish pass). It rides
        beside `variables` rather than inside them because the registry's
        render() rejects variables a template does not declare, and the
        evening bodies declare none.
        """
        ...


class LogTransport:
    """Wave A's only transport: the engine runs dark.

    It reports `delivered=True` even with no address on file, and that is the
    point rather than an oversight — a dark run's ledger is a record of the
    *decisions* Kettle made, which is what the founder reviews for two days
    before anything real is wired up. A transport with a network client does
    the opposite (`requires_address`): no address is an unroutable skip
    recorded as such, and the retryable slot waits for the day it can send.

    The address is masked on its way to the log. Logs do not need a family's
    phone number, and this one never gets it.
    """

    name = "log"
    #: The dark run carries everything: its whole point is a ledger of every
    #: decision, and it needs no address to write a log line.
    kinds = KINDS
    requires_address = False

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send(
        self,
        to: str,
        template_id: str,
        variables: Mapping[str, str],
        relationship: str | None = None,
    ) -> DeliveryResult:
        body = render(template_id, variables)
        self.sent.append((template_id, body))
        log.info("outbound (dark): %s -> %s: %s", template_id, _mask(to), body)
        return DeliveryResult(delivered=True, transport=self.name)


def _mask(to: str) -> str:
    if not to:
        return "(no address on file)"
    return f"…{to[-4:]}" if len(to) > 4 else "…"


def _console_transport(settings: Any) -> Transport:
    return LogTransport()


def _resend_transport(settings: Any) -> Transport:
    # Imported here, not at module top: this module is the decision core and
    # holds no network client (a test pins it); the HTTP-capable transports
    # live in their own modules and are loaded only when selected.
    from kettle.outbound_email import ResendTransport

    return ResendTransport(settings.resend_api_key, settings.resend_from)


def _twilio_transport(settings: Any) -> Transport:
    from kettle.outbound_whatsapp import TwilioWhatsAppTransport

    return TwilioWhatsAppTransport(
        settings.twilio_account_sid,
        settings.twilio_auth_token,
        settings.twilio_whatsapp_from,
    )


class TransportRoster:
    """Several transports behind the one seam, first-match by kind.

    Wave C runs two live channels at once — the ask to the parent by WhatsApp,
    everything child-facing by email — and the engine still works against a
    single object: `kinds` is the union, and `for_kind` hands back the first
    listed transport that carries the kind, in the order OUTBOUND_TRANSPORT
    named them. A kind nothing carries stays a recorded skip, exactly as with
    a single transport.
    """

    name = "roster"
    requires_address = False  # per-kind; the engine asks the carrier, not the roster

    def __init__(self, transports: list[Transport]) -> None:
        if not transports:  # pragma: no cover - transport_from_name guards
            raise RuntimeError("a transport roster needs at least one transport")
        self._transports = transports
        self.kinds = tuple(
            kind for kind in KINDS if any(kind in t.kinds for t in transports)
        )

    def for_kind(self, kind: str) -> Transport | None:
        for transport in self._transports:
            if kind in transport.kinds:
                return transport
        return None

    def send(
        self,
        to: str,
        template_id: str,
        variables: Mapping[str, str],
        relationship: str | None = None,
    ) -> DeliveryResult:  # pragma: no cover - the engine sends via the carrier
        carrier = self.for_kind(template(template_id).kind)
        if carrier is None:
            return DeliveryResult(delivered=False, transport=self.name, detail="no carrier")
        return carrier.send(to, template_id, variables, relationship=relationship)


def carrier_for(transport: Transport, kind: str) -> Transport | None:
    """The leaf transport that will carry this kind, or None for a skip."""
    for_kind = getattr(transport, "for_kind", None)
    if for_kind is not None:
        return for_kind(kind)
    return transport if kind in transport.kinds else None


#: Every transport the loop can be configured to use, by the name OUTBOUND_TRANSPORT
#: carries. A new entry here is a spec change, not a deploy-time discovery: the
#: registry is what makes a misconfigured name fail closed instead of falling
#: through to something that can send. "console" is the default and stays the
#: deployed value until the founder flips it after the Wave A ledger review.
TRANSPORTS: dict[str, Callable[[Any], Transport]] = {
    "console": _console_transport,
    "resend": _resend_transport,
    "twilio_whatsapp": _twilio_transport,
}


def transport_from_name(name: str, settings: Any) -> Transport:
    """Build the configured transport(s), or refuse to boot.

    Loud and at startup on purpose (DECISIONS 154): the alternative — defaulting
    an unknown name to *anything* — is a path by which a typo in an env var
    chooses who gets messaged. Known names are the registry's, nothing else —
    and a known name missing its credentials (resend without RESEND_API_KEY,
    twilio_whatsapp without its three) fails the same way, at the same moment.

    A comma-separated value builds a roster, first-match by kind in the order
    named (DECISIONS 163): Wave C's flip is
    `OUTBOUND_TRANSPORT=twilio_whatsapp,resend` — asks by WhatsApp, everything
    child-facing by email. One bad name anywhere in the list refuses the whole
    boot; a list never partially applies.
    """
    names = [part.strip() for part in name.split(",") if part.strip()]
    if not names:
        raise RuntimeError("OUTBOUND_TRANSPORT is empty — name a registered transport")
    built: list[Transport] = []
    for part in names:
        try:
            factory = TRANSPORTS[part]
        except KeyError:
            known = ", ".join(sorted(TRANSPORTS))
            raise RuntimeError(
                f"unknown outbound transport {part!r} — registered transports: {known}"
            ) from None
        built.append(factory(settings))
    if len(built) == 1:
        return built[0]
    return TransportRoster(built)


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


#: Ops alert kinds (`ops_alerts.kind`). Founder-only, law #3: nothing here has
#: a path to a family, and the copy may name mechanisms because its reader
#: operates them.
OPS_SEND_FAILED = "outbound_failed"
OPS_SEND_SKIPPED = "outbound_skipped"


def _record_outcome(
    conn: psycopg.Connection,
    notifier: Notifier | None,
    decision: Decision,
    transport_name: str,
    status: str,
    detail: str,
    now: datetime,
    alert: bool = True,
) -> bool:
    """Ledger row plus founder ops alert, once per transition.

    The ledger write is the dedupe: `record_sent_message` returns True only for
    a fresh row or a status transition, so a standing skip re-decided by the
    minutely loop alerts once, not once a minute. Only non-sent outcomes alert —
    a delivered message is the quiet case.

    `alert=False` is for the one withholding that is the system WORKING rather
    than failing (DECISIONS 164, the followed-up day's evening digest): the
    ledger still says why the slot is empty — no silent absence — but neither
    ntfy nor `ops_alerts` hears about it, only an info log line.
    """
    recorded = db.record_sent_message(
        conn,
        decision.family_id,
        decision.parent_id,
        decision.local_date,
        decision.kind,
        decision.template_id,
        transport_name,
        now,
        status=status,
    )
    if recorded and status != "sent":
        if alert:
            kind = OPS_SEND_FAILED if status == "failed" else OPS_SEND_SKIPPED
            message = f"⚠️ outbound: {detail}"
            db.insert_ops_alert(
                conn, decision.family_id, decision.parent_id, kind, message, now
            )
            if notifier is not None:
                notifier.send(message)
            log.warning("outbound: %s %s: %s", decision.template_id, status, detail)
        else:
            log.info("outbound: %s %s: %s", decision.template_id, status, detail)
    return recorded


def run_outbound(
    conn: psycopg.Connection,
    transport: Transport,
    now: datetime,
    *,
    notifier: Notifier | None = None,
    enabled: bool = True,
) -> list[Decision]:
    """Decide and record everything due for every parent, at instant `now`.

    Idempotent by construction: due-ness is a time comparison and sending goes
    through the ledger, so running twice at the same instant — or restarting
    after a crash — produces the same rows and the same messages. The returned
    list is what *this* run recorded as SENT; skips and failures land in the
    ledger with their status and raise a founder ops alert instead (DECISIONS
    157/159), so nothing this engine declines to say is ever silently absent.

    The withhold rules, in the order they are checked:

    * **Staleness** — a morning digest decided more than `MORNING_STALE_CUTOFF`
      past its slot is never sent late: "the morning looked ordinary" is a lie
      at dinnertime, whatever the ledger says about why the scheduler was down.
    * **Evidence** — the evening-normal body renders only from a day that
      produced at least one alarm-grade signal. A zero-signal day is an ops
      condition, not a family message; the morning quiet-so-far path already
      reports absence honestly and stands.
    * **The label** — a relationship-bearing template with no label renders
      nothing (DECISIONS 152); the skip now claims the slot as 'skipped' and
      the slot upgrades the moment the label is set.
    * **Routing** — a kind the transport does not carry (asks and follow-ons
      until Wave C), or an address-requiring transport with no address on
      file, is a skip, never an attempt.

    A transport that throws is a failed send for that one message; the rest of
    the pass continues.
    """
    if not enabled:
        return []

    decisions: list[Decision] = []
    for parent in db.parents_with_tz(conn):
        tz_name = effective_tz(parent["parent_tz"], parent["family_tz"])
        plan = schedule_for(now, tz_name)
        contacts = db.outbound_contacts(conn, parent["family_id"])
        child_address = (contacts or {}).get("child_email") or ""
        label = f"{parent['family_name']} / {parent['parent_name']}"

        for decision in _due_for_parent(conn, parent, plan, now):
            def skip(
                detail: str, decision: Decision = decision, alert: bool = True
            ) -> None:
                _record_outcome(
                    conn,
                    notifier,
                    decision,
                    transport.name,
                    "skipped",
                    detail,
                    now,
                    alert=alert,
                )

            if (
                decision.kind == KIND_DIGEST_MORNING
                and now >= plan.morning_digest + MORNING_STALE_CUTOFF
            ):
                skip(
                    f"morning digest for {label} decided past the staleness "
                    f"cutoff ({decision.local_date}); withheld, never sent late"
                )
                continue

            if decision.kind == KIND_DIGEST_EVENING and db.sent_message(
                conn,
                decision.family_id,
                decision.parent_id,
                decision.local_date,
                KIND_FOLLOW_ON,
            ) is not None:
                # DECISIONS 164: a followed-up day gets no evening digest — the
                # follow-on and, when earned, the all-clear already told the
                # day's story, and an ordinary-day sentence would be a false
                # one. Withheld, not replaced; recorded, not
                # alerted: this absence is the system working. The twice-a-day
                # notes resume with the next morning digest. SENT follow-ons
                # only — a skipped one told the family nothing, so their
                # evening note still comes. Checked before the evidence gate
                # so a still-quiet followed-up day records this reason,
                # quietly, rather than the gate's, loudly.
                skip(
                    f"evening digest for {label} withheld: a follow-on went "
                    f"out on {decision.local_date} (DECISIONS 164)",
                    alert=False,
                )
                continue

            if decision.template_id == "digest_evening_normal" and is_quiet(
                conn, decision.parent_id, plan.window_start, plan.evening_digest
            ):
                skip(
                    f"evening digest for {label} withheld: zero alarm-grade "
                    f"signals on {decision.local_date} — a reassurance body "
                    "never renders from an empty evidence window"
                )
                continue

            # The template says which variables it takes; the caller does not
            # get to guess. A kind-based guess drifts the moment two templates
            # of one kind differ, which `digest_morning` already does.
            available = {"relationship": parent["relationship"] or ""}
            variables = {
                name: available[name] for name in template(decision.template_id).variables
            }
            if any(not value for value in variables.values()):
                # DECISIONS 152: a message with a blank where the label goes is
                # worse than one that waits. The skip claims the slot; setting
                # the label upgrades it on the next pass.
                skip(
                    f"{decision.template_id} for {label} skipped: no "
                    "relationship label on file (set one with "
                    "scripts.provision --set-relationship)"
                )
                continue

            carrier = carrier_for(transport, decision.kind)
            if carrier is None:
                skip(
                    f"{decision.template_id} for {label} skipped: the "
                    f"{transport.name} transport does not carry {decision.kind}"
                )
                continue

            recipient = (
                db.parent_whatsapp(conn, decision.parent_id) or ""
                if decision.kind == KIND_ASK
                else child_address
            )
            if carrier.requires_address and not recipient:
                skip(
                    f"{decision.template_id} for {label} skipped: unroutable, "
                    f"no address on file for the {carrier.name} transport"
                )
                continue

            try:
                result = carrier.send(
                    recipient,
                    decision.template_id,
                    variables,
                    relationship=decision.relationship,
                )
            except Exception as exc:  # noqa: BLE001 - one send must not kill the pass
                log.exception("outbound: %s transport raised", carrier.name)
                result = DeliveryResult(
                    delivered=False, transport=carrier.name, detail=type(exc).__name__
                )
            if result.delivered:
                if _record_outcome(
                    conn, notifier, decision, result.transport, "sent", "", now
                ):
                    decisions.append(decision)
            else:
                why = f" ({result.detail})" if result.detail else ""
                _record_outcome(
                    conn,
                    notifier,
                    decision,
                    result.transport,
                    "failed",
                    f"{decision.template_id} for {label} failed on the "
                    f"{result.transport} transport{why}; slot stays retryable",
                    now,
                )
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

    # The ask, addressed to the parent, if the morning never showed up. Due
    # until a SENT ask exists: a skipped or failed slot keeps retrying.
    if (
        now >= plan.ask_threshold
        and already(KIND_ASK) is None
        and is_quiet(conn, parent_id, plan.window_start, plan.ask_threshold)
    ):
        due.append(decision(KIND_ASK, "ask_parent"))

    # The follow-on. Reachable only through an ask row that exists for the day
    # — ANY status (DECISIONS 163, amending 159's sent-only reading here): an
    # ask that could not be sent must still escalate on the clock, or a
    # missing phone number silently disables the ladder. The reply matcher is
    # unchanged and matches sent asks only; a skipped ask has replied_utc null
    # by construction, so the grace clock runs from the moment the ask was
    # due, whatever became of it. Fresh this run: an ask decided above has no
    # row yet, so nothing fires in the same pass.
    ask_record = db.message_row(conn, family_id, parent_id, plan.local_date, KIND_ASK)
    if (
        ask_record is not None
        and ask_record["replied_utc"] is None
        and now >= ask_record["sent_utc"] + FOLLOW_ON_GRACE
        and is_quiet(conn, parent_id, plan.window_start, now)
        and not already(KIND_FOLLOW_ON)
    ):
        # Which follow-on is the mechanism_ok distinction (DECISIONS 157/161):
        # zero pings of ANY grade all local day means the report is about the
        # phone; signals arriving with routine absent means the changed-morning
        # body. Never both — one kind, one slot, one template chosen at send.
        unreachable = db.count_pings_between(conn, parent_id, plan.day_start, now) == 0
        due.append(
            decision(
                KIND_FOLLOW_ON,
                "follow_on_unreachable" if unreachable else "follow_on_family",
            )
        )

    # The all-clear (DECISIONS 157/161): only after a follow-on actually
    # reached the family, when the first alarm-grade signal of the day since
    # then arrives. Once per day; the ledger row is the resolution record. No
    # follow-on sent, no all-clear ever.
    follow_row = already(KIND_FOLLOW_ON)
    if (
        follow_row is not None
        and already(KIND_ALL_CLEAR) is None
        and db.count_alarm_pings_between(conn, parent_id, follow_row["sent_utc"], now) > 0
    ):
        due.append(decision(KIND_ALL_CLEAR, "all_clear_family"))

    # The evening digest, last because the day is. Which body is decided here
    # (email-polish pass): a morning that was quiet at the digest slot — the
    # same window that chose digest_morning_quiet and armed the ask — but
    # whose routine resumed by evening is a recovered day, and "start to
    # finish" would be a false sentence for it. Every withhold rule around
    # the slot (164's followed-up skip, the evidence gate) is unchanged.
    if now >= plan.evening_digest and not already(KIND_DIGEST_EVENING):
        morning_quiet = is_quiet(
            conn, parent_id, plan.window_start, plan.morning_digest
        )
        recovered = morning_quiet and not is_quiet(
            conn, parent_id, plan.morning_digest, plan.evening_digest
        )
        due.append(
            decision(
                KIND_DIGEST_EVENING,
                "digest_evening_recovered" if recovered else "digest_evening_normal",
            )
        )

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
    #: True while the loop's passes are failing; the transition into a failing
    #: streak is what alerts the founder, so a stuck loop costs one ntfy, not
    #: one a minute (DECISIONS 157/159).
    failing: bool = False


async def outbound_loop(
    conn: psycopg.Connection,
    transport: Transport,
    settings: Any,
    notifier: Notifier,
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
                run_outbound,
                conn,
                transport,
                now,
                notifier=notifier,
                enabled=settings.outbound_enabled,
            )
            state.last_run_utc = now
            state.failing = False
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - the engine must outlive any failure
            log.exception("outbound pass failed")
            if not state.failing:
                state.failing = True
                notifier.send(
                    "⚠️ outbound: a scheduler pass failed and the loop is "
                    "retrying every minute; see the kettle-api logs"
                )
        await asyncio.sleep(interval_s)
