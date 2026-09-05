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

from kettle import db, journal
from kettle.notify import Notifier
from kettle.outbound_templates import (
    KIND_ALL_CLEAR,
    KIND_ASK,
    KIND_DIGEST_EVENING,
    KIND_DIGEST_MORNING,
    KIND_FOLLOW_ON,
    KINDS,
    owner_first_name,
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
        ask_content_sid=settings.twilio_ask_content_sid,
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
#: Spec 010 §3: a move must never be silent. One row per change, and the row
#: doubles as the restart-proof dedupe and the next move's "old zone".
OPS_TZ_CHANGED = "tz_changed"


def first_new_zone_midnight(changed: datetime, tz_name: str) -> datetime:
    """The first local midnight in the NEW zone after the change instant.

    The changeover-conservatism window (spec 010 §3) ends here: until then a
    shifted clock can fabricate a quiet morning, so the ask ladder holds its
    tongue and the morning-quiet body is not used.
    """
    zone = ZoneInfo(tz_name)
    next_day = changed.astimezone(zone).date() + timedelta(days=1)
    return datetime(next_day.year, next_day.month, next_day.day, tzinfo=zone)


def _previous_zone(last_alert: Any, family_tz: str) -> str:
    """The old zone for the move alert's message.

    A parent starts with tz null and inherits the family zone, so the first
    move's old zone is the family's. Every later move reads the previous
    alert's own message — the engine authored it in a pinned format, so the
    parse is of our own writing, and a test holds the round trip.
    """
    if last_alert is None:
        return family_tz
    detail = last_alert["detail"]
    if " → " in detail and " (city" in detail:
        return detail.split(" → ", 1)[1].split(" (city", 1)[0]
    return family_tz  # pragma: no cover - only our own format exists


def _alert_tz_change_once(
    conn: psycopg.Connection,
    notifier: Notifier | None,
    parent: Any,
    tz_name: str,
    now: datetime,
) -> None:
    """Spec 010 §3's founder alert, exactly once per change.

    Deduped through ops_alerts rather than loop memory, so a scheduler
    restart between the webapp write and the next cycle cannot swallow it.
    """
    changed = parent["tz_changed_utc"]
    if changed is None:
        return
    last = db.latest_ops_alert(conn, parent["parent_id"], OPS_TZ_CHANGED)
    if last is not None and last["ts_utc"] >= changed:
        return
    old = _previous_zone(last, parent["family_tz"])
    city = parent["city_label"] or "unset"
    message = (
        f"{parent['parent_name']}: timezone changed {old} → {tz_name} "
        f"(city {city}) via webapp."
    )
    db.insert_ops_alert(
        conn, parent["family_id"], parent["parent_id"], OPS_TZ_CHANGED, message, now
    )
    if notifier is not None:
        notifier.send(message)
    log.warning("outbound: %s", message)


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
      past its slot is never sent late: "the morning looked normal" is a lie
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
        # Scenery (DECISIONS 245): a demo family is skipped BEFORE anything is
        # decided, so it produces no ledger row, no ops alert and no send. The
        # gap this closes was real and shipping: "no phone number" (242) stops
        # the ask and nothing else, so the seeded Whitakers would have mailed
        # the owner a quiet-morning digest and the founder an alert, daily,
        # about a household that does not exist. Placed at the top of the loop
        # rather than inside the withhold rules on purpose - a withhold is a
        # decision recorded, and there is nothing here to record.
        if parent["family_demo"]:
            continue

        # Read fresh from this cycle's query, never cached (spec 010 §3): the
        # zone is load-bearing for every slot below, and a moved parent's
        # digests fire at the NEW zone's clock from the next cycle onward.
        tz_name = effective_tz(parent["parent_tz"], parent["family_tz"])
        plan = schedule_for(now, tz_name)

        # Spec 017: a paused parent, in the demo skip's place — above every
        # withhold rule, so nothing is decided, recorded or alerted. The one
        # exception is the paused line itself (loud, §2): ONCE per pause, at
        # the first morning slot after the pause began (DECISIONS 277),
        # through the circle like any digest, and then nothing until the
        # pause ends. The card and the Family row carry the state after that.
        paused_until = parent["paused_until"]
        if paused_until is not None and paused_until > now:
            decisions.extend(
                _paused_morning_note(conn, transport, notifier, parent, plan, now)
            )
            continue
        # The resume day (§4): from the instant the pause ended until that
        # local day is over, slots that fell due while paused do not fire late
        # — a morning Kettle was not watching cannot arm an ask, and "the
        # morning looked normal" cannot be said of it. After that day both
        # fields are cleared and the parent is an ordinary parent again.
        resumed_at = None
        if paused_until is not None and parent["paused_since"] is not None:
            if to_local(paused_until, tz_name).date().isoformat() < plan.local_date:
                db.clear_pause(conn, parent["parent_id"])
            else:
                resumed_at = paused_until
        # Spec 015 §7: everyone in the circle with mail on and an email,
        # admins first. Digests, follow-ons and all-clears fan out to all of
        # them; the ask below still goes to the parent alone.
        recipients = db.outbound_contacts(conn, parent["family_id"])
        label = f"{parent['family_name']} / {parent['parent_name']}"

        _alert_tz_change_once(conn, notifier, parent, tz_name, now)
        # Spec 012 §3.4: on the turn of the parent-local month, the previous
        # month earns a line ONLY if it was clean — a month with an
        # escalation writes nothing at all. Keyed to the month rather than
        # the day (a scheduler asleep on the 1st writes it on the 2nd, not
        # never), and every guard lives in the writer.
        journal.note_clean_month(
            conn, parent["family_id"], parent["parent_id"], plan.local_date
        )
        tz_changed = parent["tz_changed_utc"]
        in_changeover = tz_changed is not None and now < first_new_zone_midnight(
            tz_changed, tz_name
        )

        for decision in _due_for_parent(conn, parent, plan, now):
            if resumed_at is not None and _due_at(conn, decision, plan) < resumed_at:
                continue

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

            # Changeover conservatism (spec 010 §3): from the change until the
            # first local midnight in the new zone, a shifted clock can
            # fabricate a quiet morning. The ask ladder is suppressed whole,
            # and the morning-quiet body is never chosen from moved-clock
            # absence — digests still send when they report data actually
            # seen. The skip goes through the standard alerting path on
            # purpose: sent_messages has no detail column, so the ops_alerts
            # row IS the durable detail the spec wants naming the timezone
            # change, and a relocation day carries at most a handful of them.
            if in_changeover and decision.kind in (KIND_ASK, KIND_FOLLOW_ON):
                skip(
                    f"{decision.template_id} for {label} suppressed until the "
                    f"first local midnight in the new zone after the timezone "
                    f"change to {tz_name} (spec 010)"
                )
                continue

            if in_changeover and decision.template_id == "digest_morning_quiet":
                skip(
                    f"morning digest for {label} withheld: a quiet verdict "
                    f"under a clock moved to {tz_name} is not evidence "
                    f"(timezone change, spec 010)"
                )
                continue

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
                # day's story, and a normal-day sentence would be a false
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
            # DECISIONS 217: the ask now names who asked for it. The owner's
            # first name is resolved through `owner_first_name`, which returns
            # the ruled fallback rather than an empty string — so unlike
            # `relationship` below, this variable can never be the reason a
            # message is withheld, and a family with no name on file still
            # gets a sentence that reads whole.
            available = {
                "relationship": parent["relationship"] or "",
                "owner_name": owner_first_name(
                    db.family_owner_name(conn, parent["family_id"])
                ),
                "name": parent["parent_name"],
            }
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

            if decision.kind == KIND_ASK:
                recipient = db.parent_whatsapp(conn, decision.parent_id) or ""
                if carrier.requires_address and not recipient:
                    skip(
                        f"{decision.template_id} for {label} skipped: unroutable, "
                        f"no address on file for the {carrier.name} transport"
                    )
                    continue
                result = _attempt(carrier, recipient, decision, variables)
                if result.delivered:
                    if _record_outcome(
                        conn, notifier, decision, result.transport, "sent", "", now
                    ):
                        decisions.append(decision)
                else:
                    _record_failed(conn, notifier, decision, result, label, now)
                continue

            # The circle (spec 015 §7). An address-requiring transport with
            # nobody listening is the one absence that is not a transport
            # problem: recorded as skipped, alerted once a day as
            # circle_unreachable, never as outbound_skipped.
            if carrier.requires_address and not recipients:
                skip(
                    f"{decision.template_id} for {label} skipped: no one in the "
                    "circle is getting Kettle's mail",
                    alert=False,
                )
                _alert_circle_unreachable(conn, notifier, parent, plan, now)
                continue
            outcome = _send_to_circle(
                conn, carrier, decision, variables, recipients, now
            )
            if outcome.delivered_to_all:
                if _record_outcome(
                    conn, notifier, decision, outcome.transport, "sent", "", now
                ):
                    decisions.append(decision)
                    if (
                        decision.kind in (KIND_DIGEST_MORNING, KIND_DIGEST_EVENING)
                        and decision.template_id != "digest_morning_paused"
                    ):
                        # Spec 012 §3.2: the family's memory notes the first
                        # daily note. Called after every sent digest; the
                        # writer itself checks the LEDGER for prior history in
                        # the same statement (DECISIONS 204), so a parent with
                        # months behind them never earns a first-morning line.
                        journal.note_started(
                            conn,
                            decision.family_id,
                            decision.parent_id,
                            parent["parent_name"],
                            decision.local_date,
                            decision.kind,
                        )
            else:
                _record_failed(conn, notifier, decision, outcome.result, label, now)
    return decisions


def _attempt(
    carrier: Any, recipient: str, decision: Decision, variables: Mapping[str, str]
) -> DeliveryResult:
    """One send. A transport that throws is a failed send, never a dead pass."""
    try:
        return carrier.send(
            recipient,
            decision.template_id,
            variables,
            relationship=decision.relationship,
        )
    except Exception as exc:  # noqa: BLE001 - one send must not kill the pass
        log.exception("outbound: %s transport raised", carrier.name)
        return DeliveryResult(
            delivered=False, transport=carrier.name, detail=type(exc).__name__
        )


def _record_failed(
    conn: psycopg.Connection,
    notifier: Notifier | None,
    decision: Decision,
    result: DeliveryResult,
    label: str,
    now: datetime,
) -> None:
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


@dataclass(frozen=True)
class CircleOutcome:
    """What one slot's fan-out to the circle came to."""

    delivered_to_all: bool
    transport: str
    result: DeliveryResult


def _send_to_circle(
    conn: psycopg.Connection,
    carrier: Any,
    decision: Decision,
    variables: Mapping[str, str],
    recipients: list[Any],
    now: datetime,
) -> CircleOutcome:
    """Send one decision to every listening member, once each (spec 015 §7).

    Per-member idempotency lives in `digest_sends`, keyed (family, parent,
    kind, local day, member): a member with a SENT row is skipped, so a slot
    retried after one failure reaches only the members it missed. The slot's
    own ledger row (`sent_messages`) says 'sent' only when every member has
    been reached — anything less stays 'failed' and retryable, which is what
    makes the next pass finish the job rather than declare it done.

    A transport that needs no address (the dark console) with nobody in the
    circle sends once to nobody, exactly as it always has.
    """
    if not recipients:
        result = _attempt(carrier, "", decision, variables)
        return CircleOutcome(result.delivered, result.transport, result)
    last = DeliveryResult(delivered=True, transport=carrier.name, detail="")
    missed = 0
    for member in recipients:
        member_id = member["member_id"]
        if db.member_send_sent(
            conn, decision.family_id, decision.parent_id, decision.kind,
            decision.local_date, member_id,
        ):
            continue
        result = _attempt(carrier, member["email"] or "", decision, variables)
        db.record_member_send(
            conn,
            decision.family_id,
            decision.parent_id,
            decision.kind,
            decision.local_date,
            member_id,
            result.transport,
            "sent" if result.delivered else "failed",
            now,
        )
        if not result.delivered:
            missed += 1
            last = result
    if missed:
        detail = f"{missed} of {len(recipients)} in the circle not reached"
        if last.detail:
            detail = f"{detail}: {last.detail}"
        last = DeliveryResult(delivered=False, transport=last.transport, detail=detail)
    return CircleOutcome(missed == 0, last.transport, last)


OPS_CIRCLE_UNREACHABLE = "circle_unreachable"


def _alert_circle_unreachable(
    conn: psycopg.Connection,
    notifier: Notifier | None,
    parent: Any,
    plan: Schedule,
    now: datetime,
) -> None:
    """Once per family per local day: nobody in the circle is getting mail."""
    family_id = parent["family_id"]
    # The local date rides in the text, and the text is the dedupe key
    # (`ops_alert_exists_with_detail`, the per-member pattern): one row per
    # family per local day, however many parents and slots go unsent.
    message = (
        f"⚠️ outbound: {parent['family_name']}: no one in the circle is getting "
        f"Kettle's notes on {plan.local_date} (every member has mail off or no "
        "email); nothing sent"
    )
    if db.ops_alert_exists_with_detail(
        conn, OPS_CIRCLE_UNREACHABLE, family_id, None, message,
        now - timedelta(days=2), now + timedelta(minutes=1),
    ):
        return
    db.insert_ops_alert(conn, family_id, None, OPS_CIRCLE_UNREACHABLE, message, now)
    if notifier is not None:
        notifier.send(message)
    log.warning("outbound: %s", message)


def _due_at(conn: psycopg.Connection, decision: Decision, plan: Schedule) -> datetime:
    """The instant a decision became due, for the resume-day rule (spec 017)."""
    if decision.kind == KIND_DIGEST_MORNING:
        return plan.morning_digest
    if decision.kind == KIND_ASK:
        return plan.ask_threshold
    if decision.kind == KIND_DIGEST_EVENING:
        return plan.evening_digest
    if decision.kind == KIND_FOLLOW_ON:
        ask = db.message_row(
            conn, decision.family_id, decision.parent_id, decision.local_date, KIND_ASK
        )
        return ask["sent_utc"] + FOLLOW_ON_GRACE if ask else plan.ask_threshold
    # The all-clear follows a follow-on that fired after the resume: now.
    return datetime.max.replace(tzinfo=UTC)


def _paused_morning_note(
    conn: psycopg.Connection,
    transport: Transport,
    notifier: Notifier | None,
    parent: Any,
    plan: Schedule,
    now: datetime,
) -> list[Decision]:
    """The one thing Kettle says about a paused parent (spec 017 §2): the
    registry's digest_morning_paused line, at the first morning slot after
    the pause began, once per pause (DECISIONS 277). Same slot, same ledger
    row, same circle as the digest it stands in for, so on the day it was
    paused whatever went out stands and nothing more follows; every later
    morning of the pause is silent. Idempotent per (parent, pause start):
    a restart, a re-decide, or a week of passes lands one row."""
    if now < plan.morning_digest or now >= plan.morning_digest + MORNING_STALE_CUTOFF:
        return []
    since = parent["paused_since"] or now
    if db.paused_line_sent_since(conn, parent["parent_id"], since):
        return []
    if db.sent_message(
        conn, parent["family_id"], parent["parent_id"], plan.local_date, KIND_DIGEST_MORNING
    ):
        return []
    decision = Decision(
        family_id=parent["family_id"],
        parent_id=parent["parent_id"],
        relationship=parent["relationship"],
        local_date=plan.local_date,
        kind=KIND_DIGEST_MORNING,
        template_id="digest_morning_paused",
    )
    carrier = carrier_for(transport, decision.kind)
    if carrier is None:
        return []
    recipients = db.outbound_contacts(conn, parent["family_id"])
    if carrier.requires_address and not recipients:
        return []  # paused raises nothing, the circle alert included (§2)
    variables = {"name": parent["parent_name"]}
    outcome = _send_to_circle(conn, carrier, decision, variables, recipients, now)
    if outcome.delivered_to_all and _record_outcome(
        conn, notifier, decision, outcome.transport, "sent", "", now
    ):
        return [decision]
    if not outcome.delivered_to_all:
        label = f"{parent['family_name']} / {parent['parent_name']}"
        _record_failed(conn, notifier, decision, outcome.result, label, now)
    return []


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
    conn: psycopg.Connection,
    number: str,
    now: datetime,
    *,
    note_first_reply: bool = False,
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
    if matched and note_first_reply:
        # Spec 012 §3.3: the first-ever reply earns a line in the family's
        # memory, once — the schema key absorbs every later one. Content
        # stays unread; this notes THAT a reply came, never what it said.
        # Gated by MEMORY_FIRST_REPLY (default off, DECISIONS 203): the line
        # belongs to the real-number era and is armed at the Phase 3 flip,
        # never spent on a sandbox or dark-stage reply.
        journal.note_first_reply(
            conn,
            parent["family_id"],
            parent["parent_id"],
            parent["parent_name"],
            now,
        )
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
