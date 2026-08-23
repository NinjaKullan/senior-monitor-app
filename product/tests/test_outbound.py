"""Spec 007 §6.1 — the outbound channel's decision core, driven by a fake clock.

Every test here runs whole days by calling `run_outbound` at chosen instants,
because that is the only way to assert the thing that matters: what Kettle
decided to say, and when, and to whom — and, just as often, that it decided to
say nothing.

Two properties get asserted on every path rather than once:

* **The ledger is unique.** Each scenario runs the scheduler twice at the same
  instant and requires the second run to record nothing. A crashed-and-restarted
  scheduler is the case the unique index exists for.
* **Nothing reaches anyone.** Wave A's only transport writes a log line. The
  transport under test counts its own calls, so "sent dark" is asserted against
  the object that would have done the sending.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import psycopg
import pytest

from kettle import db
from kettle.outbound import (
    ASK_THRESHOLD,
    EVENING_DIGEST,
    FOLLOW_ON_GRACE,
    MORNING_DIGEST,
    MORNING_WINDOW_START,
    DeliveryResult,
    LogTransport,
    record_parent_reply,
    run_outbound,
    schedule_for,
)
from kettle.provisioning import provision_family, set_parent_relationship
from testsupport import BASE_URL, add_child_email, set_parent_whatsapp

IST = ZoneInfo("Asia/Kolkata")
CHICAGO = ZoneInfo("America/Chicago")
DAY = (2026, 8, 21)
WHATSAPP = "+919845550001"


def at(hour: int, minute: int = 0, tz: ZoneInfo = IST) -> datetime:
    """An instant on the fixed test day, in a named zone."""
    return datetime(*DAY, hour, minute, tzinfo=tz)


class CountingTransport(LogTransport):
    """The dark transport, with its calls kept for assertions."""

    def send(
        self, to: str, template_id: str, variables: Mapping[str, str]
    ) -> DeliveryResult:
        return super().send(to, template_id, variables)


@pytest.fixture
def family(conn: psycopg.Connection):
    """One family, one parent, a child with an email, a WhatsApp number."""
    provisioned = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    add_child_email(conn, provisioned.family_id)
    set_parent_whatsapp(conn, provisioned.parents[0].parent_id, WHATSAPP)
    return provisioned


def ping(conn: psycopg.Connection, parent_id, signal: str, when: datetime) -> None:
    db.insert_ping(conn, parent_id, signal, when, None)


def ledger(conn: psycopg.Connection) -> list[tuple[str, str]]:
    """What Kettle actually said: SENT rows as (kind, template_id), in order.

    Sent-only since 0015 — skipped and failed decisions also claim ledger rows
    now, and `statuses()` below is how a test looks at those.
    """
    # By id, not by sent_utc: everything one run decides shares an instant, so
    # a timestamp sort would report alphabetical order as if it were sequence.
    rows = conn.execute(
        "select kind, template_id from sent_messages where status = 'sent' order by id"
    ).fetchall()
    return [(r["kind"], r["template_id"]) for r in rows]


def statuses(conn: psycopg.Connection) -> dict[str, str]:
    """Every ledger row's status, keyed by kind (one row per kind per day here)."""
    rows = conn.execute("select kind, status from sent_messages order by id").fetchall()
    return {r["kind"]: r["status"] for r in rows}


def run_twice(conn: psycopg.Connection, transport, now: datetime, **kwargs) -> list:
    """Run the scheduler, then run it again at the same instant.

    The second run must record nothing. Returns what the *first* run decided.
    """
    first = run_outbound(conn, transport, now, **kwargs)
    second = run_outbound(conn, transport, now, **kwargs)
    assert second == [], f"the scheduler double-sent at {now}: {second}"
    return first


# --- the schedule itself ------------------------------------------------------


def test_the_schedule_is_wall_clock_in_the_parents_zone():
    plan = schedule_for(at(9, 0), "Asia/Kolkata")
    assert plan.local_date == "2026-08-21"
    for instant, wall in (
        (plan.window_start, MORNING_WINDOW_START),
        (plan.morning_digest, MORNING_DIGEST),
        (plan.ask_threshold, ASK_THRESHOLD),
        (plan.evening_digest, EVENING_DIGEST),
    ):
        local = instant.astimezone(IST)
        assert (local.hour, local.minute) == (wall.hour, wall.minute)


def test_two_zones_get_two_different_days_from_the_same_instant():
    """The same instant is a different local day and a different schedule.

    Amma is provisioned Asia/Kolkata and physically in Texas (DECISIONS 108);
    the tz on her row is what decides her morning, which is the whole reason
    the arithmetic is per parent rather than per server.
    """
    instant = at(2, 0)  # 02:00 IST on the 21st is still the 20th in Chicago
    assert schedule_for(instant, "Asia/Kolkata").local_date == "2026-08-21"
    assert schedule_for(instant, "America/Chicago").local_date == "2026-08-20"


# --- §6.1 scenario 1: a normal day -------------------------------------------


def test_a_normal_day_sends_two_digests_and_never_asks(conn, family):
    parent_id = family.parents[0].parent_id
    ping(conn, parent_id, "whatsapp", at(7, 0))
    transport = CountingTransport()

    run_twice(conn, transport, at(8, 30))
    assert ledger(conn) == [("digest_morning", "digest_morning_normal")]

    run_twice(conn, transport, at(11, 0))
    assert ledger(conn) == [("digest_morning", "digest_morning_normal")]

    run_twice(conn, transport, at(20, 30))
    assert ledger(conn) == [
        ("digest_morning", "digest_morning_normal"),
        ("digest_evening", "digest_evening_normal"),
    ]
    assert [t for t, _ in transport.sent] == [
        "digest_morning_normal",
        "digest_evening_normal",
    ]


# --- §6.1 scenario 2: quiet morning, then a signal before the threshold -------


def test_a_signal_before_the_threshold_means_no_ask(conn, family):
    parent_id = family.parents[0].parent_id
    transport = CountingTransport()

    # 08:30, and nothing yet: the morning note says so without interpreting it.
    run_twice(conn, transport, at(8, 30))
    assert ledger(conn) == [("digest_morning", "digest_morning_quiet")]

    ping(conn, parent_id, "whatsapp", at(10, 40))
    run_twice(conn, transport, at(11, 0))
    assert ledger(conn) == [("digest_morning", "digest_morning_quiet")]


def test_charger_signals_never_make_a_morning_happen(conn, family):
    """Law #6 at the evaluator: household plumbing cannot speak for a person.

    The first run lands at 11:00, past the staleness cutoff, so the morning
    digest is withheld (its slot records 'skipped') — the ask is what goes.
    """
    parent_id = family.parents[0].parent_id
    ping(conn, parent_id, "charge_on", at(6, 30))
    ping(conn, parent_id, "device_alive", at(7, 30))
    transport = CountingTransport()

    run_twice(conn, transport, at(11, 0))
    assert ledger(conn) == [("ask", "ask_parent")]
    assert statuses(conn)["digest_morning"] == "skipped"


# --- §6.1 scenario 3: quiet past the threshold, then she replies --------------


def test_a_quiet_morning_asks_her_first_and_a_reply_cancels_the_follow_on(
    conn, family
):
    transport = CountingTransport()

    run_twice(conn, transport, at(11, 0))
    assert ("ask", "ask_parent") in ledger(conn)
    # Parent-first is the ordering: nothing has gone to the child about her.
    assert ("follow_on", "follow_on_family") not in ledger(conn)

    assert record_parent_reply(conn, WHATSAPP, at(11, 30)) is True

    run_twice(conn, transport, at(13, 0))
    run_twice(conn, transport, at(19, 0))
    assert ("follow_on", "follow_on_family") not in ledger(conn)


def test_a_second_reply_changes_nothing(conn, family):
    """A duplicate webhook delivery must not move the timestamp around."""
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))

    assert record_parent_reply(conn, WHATSAPP, at(11, 30)) is True
    first = conn.execute("select replied_utc from sent_messages where kind = 'ask'").fetchone()
    assert record_parent_reply(conn, WHATSAPP, at(12, 0)) is False
    assert (
        conn.execute("select replied_utc from sent_messages where kind = 'ask'").fetchone()
        == first
    )


def test_an_unknown_number_replies_for_nobody(conn, family):
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))
    assert record_parent_reply(conn, "+15125550999", at(11, 30)) is False
    assert record_parent_reply(conn, "", at(11, 30)) is False


# --- §6.1 scenario 4: quiet, no reply, the deadline arrives -------------------


def test_no_reply_and_still_quiet_reaches_the_child_at_the_deadline(conn, family):
    # A charger ping keeps the phone visibly alive: this is the changed-morning
    # follow-on, not the unreachable one (those have their own tests below).
    ping(conn, family.parents[0].parent_id, "charge_on", at(6, 30))
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))

    # One minute short of the grace window: still nothing about her.
    run_twice(conn, transport, at(11, 0) + FOLLOW_ON_GRACE - timedelta(minutes=1))
    assert ("follow_on", "follow_on_family") not in ledger(conn)

    run_twice(conn, transport, at(11, 0) + FOLLOW_ON_GRACE)
    assert ledger(conn)[-1] == ("follow_on", "follow_on_family")
    # The relationship label, never the display name (DECISIONS 149): the row
    # says "Amma", the message says what the child calls her.
    assert transport.sent[-1][1].startswith("Mom's usual morning hasn't shown up")
    assert "Amma" not in transport.sent[-1][1]


def test_a_signal_after_the_ask_stops_the_follow_on(conn, family):
    """She did not answer the note, but her day started. Nothing to report."""
    parent_id = family.parents[0].parent_id
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))

    # `whatsapp` rather than `routine`: this family was provisioned with the
    # standard seed, and a signal outside a parent's own allowlist is invisible
    # to the evaluator by design — which is the allowlist doing its job, not a
    # quiet failure to notice her.
    ping(conn, parent_id, "whatsapp", at(11, 45))
    run_twice(conn, transport, at(13, 30))
    assert ("follow_on", "follow_on_family") not in ledger(conn)


def test_a_follow_on_cannot_exist_without_the_ask_that_precedes_it(conn, family):
    """Parent-first by construction, asserted by removing the precondition.

    The ask row is the only route to a follow-on. With it gone, the deadline
    passes and the child hears nothing — not because a flag says so, but
    because there is no query that returns a follow-on.
    """
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))
    conn.execute("delete from sent_messages where kind = 'ask'")

    run_twice(conn, transport, at(14, 0))
    assert ("follow_on", "follow_on_family") not in ledger(conn)


# --- the ledger ---------------------------------------------------------------


def test_the_ledger_stores_no_message_body(conn, family):
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))
    columns = {
        row["column_name"]
        for row in conn.execute(
            "select column_name from information_schema.columns "
            "where table_name = 'sent_messages'"
        ).fetchall()
    }
    assert "body" not in columns and "message" not in columns and "text" not in columns
    stored = conn.execute("select * from sent_messages").fetchall()
    for row in stored:
        for value in row.values():
            assert "Everything okay today" not in str(value)


def test_each_parent_gets_her_own_row(conn):
    """The spec's key was (family, date, kind); this schema adds the parent.

    Migration 0006 exists because family-granular keys silently dropped the
    second parent's row, and both of the founder's parents are live. With a
    family-granular key exactly one of these two asks would have been recorded.
    """
    provisioned = provision_family(
        conn,
        "Sharma",
        "Asia/Kolkata",
        [("Amma", None, "Mom"), ("Appa", None, "Dad")],
        base_url=BASE_URL,
    )
    add_child_email(conn, provisioned.family_id)
    for parent in provisioned.parents:
        set_parent_whatsapp(conn, parent.parent_id, f"+9198455500{parent.parent_id.int % 10}")

    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))
    asks = conn.execute(
        "select parent_id from sent_messages where kind = 'ask'"
    ).fetchall()
    assert len(asks) == 2
    assert {row["parent_id"] for row in asks} == {p.parent_id for p in provisioned.parents}


def test_a_restarted_scheduler_re_decides_and_records_nothing_new(conn, family):
    """The double-run assertion, made explicit rather than only in the helper."""
    transport = CountingTransport()
    run_outbound(conn, transport, at(11, 0))
    before = ledger(conn)
    for _ in range(5):
        assert run_outbound(conn, transport, at(11, 0)) == []
    assert ledger(conn) == before


def test_the_index_is_what_stops_a_double_send_not_the_read_before_it(conn, family):
    """The race the unique index actually guards, exercised directly.

    A double *run* of the scheduler is stopped by the read that precedes the
    write — the second run sees the row and decides nothing — so the scenarios
    above prove the observable property without ever reaching the index. Two
    schedulers running at once would; this is that, without the threads. The
    write must be idempotent on its own.
    """
    plan = schedule_for(at(11, 0), "Asia/Kolkata")
    parent_id = family.parents[0].parent_id
    args = (
        family.family_id,
        parent_id,
        plan.local_date,
        "ask",
        "ask_parent",
        "log",
        at(11, 0),
    )
    assert db.record_sent_message(conn, *args) is True
    assert db.record_sent_message(conn, *args) is False
    assert (
        conn.execute("select count(*) as n from sent_messages").fetchone()["n"] == 1
    )


def test_the_kill_switch_decides_nothing_at_all(conn, family):
    transport = CountingTransport()
    assert run_outbound(conn, transport, at(11, 0), enabled=False) == []
    assert ledger(conn) == []
    assert transport.sent == []


# --- the transport seam -------------------------------------------------------


def test_the_decision_core_still_has_no_network_client():
    """Wave B added a real transport; the decision core still cannot send.

    `kettle/outbound.py` decides; `kettle/outbound_email.py` is the one module
    with an HTTP client, loaded only when the resend transport is selected. A
    network client appearing in the decision core would mean a code path from
    a decision to a message that no registry gate stands in front of.
    """
    import inspect

    import kettle.outbound as outbound

    source = inspect.getsource(outbound)
    assert "httpx" not in source and "requests" not in source
    transports = [
        name
        for name, value in vars(outbound).items()
        if isinstance(value, type) and name.endswith("Transport") and name != "Transport"
    ]
    assert transports == ["LogTransport"]


def test_an_undeliverable_message_records_failed_and_stays_retryable(
    conn, family, notifier
):
    """A real transport says False: the ledger says 'failed', the founder hears
    once, and a later pass that succeeds upgrades the same slot (0015)."""

    class RefusingTransport(LogTransport):
        def send(self, to, template_id, variables):
            return DeliveryResult(delivered=False, transport="refusing", detail="down")

    assert run_twice(conn, RefusingTransport(), at(11, 0), notifier=notifier) == []
    assert ledger(conn) == []
    assert statuses(conn)["ask"] == "failed"
    assert len([m for m in notifier.messages if "failed" in m and "ask" in m]) == 1

    # The transport recovers: the same slot is claimed by the real send.
    run_twice(conn, CountingTransport(), at(11, 5), notifier=notifier)
    assert ("ask", "ask_parent") in ledger(conn)
    assert statuses(conn)["ask"] == "sent"


def test_a_transport_that_raises_is_a_failed_send_not_a_dead_pass(
    conn, family, notifier
):
    """One exploding send records 'failed' and the pass carries on."""

    class ExplodingTransport(LogTransport):
        def send(self, to, template_id, variables):
            raise ConnectionError("socket reset")

    assert run_twice(conn, ExplodingTransport(), at(11, 0), notifier=notifier) == []
    assert statuses(conn)["ask"] == "failed"
    assert any("ConnectionError" in m for m in notifier.messages)


def test_a_parent_without_a_label_waits_rather_than_rendering_a_blank(conn, notifier):
    """Both live parents predate migration 0014 (DECISIONS 149/152).

    A relationship-bearing template must not render with a blank, so it is
    recorded as 'skipped' with one founder ops alert (157/159) — while the
    ask, which names nobody, still goes: a missing label never delays the
    parent being asked first. Setting the label upgrades the skipped slots on
    the next pass; the morning digest alone stays withheld, because by then it
    is past the staleness cutoff and "this morning" would be a lie.
    """
    provisioned = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    add_child_email(conn, provisioned.family_id)
    set_parent_whatsapp(conn, provisioned.parents[0].parent_id, WHATSAPP)
    ping(conn, provisioned.parents[0].parent_id, "charge_on", at(6, 30))
    token = provisioned.parents[0].device_token
    transport = CountingTransport()

    # Quiet morning: the digest and, later, the follow-on both need the label.
    run_twice(conn, transport, at(8, 30), notifier=notifier)
    assert ledger(conn) == []
    assert statuses(conn) == {"digest_morning": "skipped"}
    assert len([m for m in notifier.messages if "no relationship label" in m]) == 1

    run_twice(conn, transport, at(11, 0), notifier=notifier)
    assert ledger(conn) == [("ask", "ask_parent")]

    run_twice(conn, transport, at(11, 0) + FOLLOW_ON_GRACE, notifier=notifier)
    assert ledger(conn) == [("ask", "ask_parent")]
    assert statuses(conn)["follow_on"] == "skipped"

    assert set_parent_relationship(conn, token, "Mom") == "Amma"
    run_twice(conn, transport, at(11, 0) + FOLLOW_ON_GRACE + timedelta(minutes=5))
    assert ("follow_on", "follow_on_family") in ledger(conn)
    assert statuses(conn)["follow_on"] == "sent"
    assert statuses(conn)["digest_morning"] == "skipped"  # stale by now, stays withheld
    assert all("{" not in body and "Amma" not in body for _, body in transport.sent)


def test_the_log_transport_never_logs_a_whole_number(conn, family, caplog):
    import logging

    transport = LogTransport()
    with caplog.at_level(logging.INFO, logger="kettle.outbound"):
        run_outbound(conn, transport, at(11, 0))
    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert WHATSAPP not in logged
    assert "…0001" in logged


# --- the reply endpoint (§2.6) ------------------------------------------------


@pytest.fixture
def replying_client(settings, notifier, conn):
    """A client whose `/outbound/reply` shares the fake clock the scheduler uses.

    Without this the route read wall time while the ask was written on the fixed
    test day, so the test passed only while the suite ran before 18:30 UTC — after
    that, IST is already tomorrow and the reply matched no ask (DECISIONS 142). It
    was green all morning and red all evening, every day, and it went unnoticed
    because nobody runs a suite at 02:00 IST on purpose.
    """
    from fastapi.testclient import TestClient

    from kettle.main import create_app

    with TestClient(create_app(settings, notifier, clock=lambda: at(11, 30))) as c:
        yield c



def test_the_reply_endpoint_does_not_exist_without_a_secret(conn, settings, notifier):
    """An unauthenticated route that cancels an escalation is not shipped."""
    from dataclasses import replace

    from fastapi.testclient import TestClient

    from kettle.main import create_app

    with TestClient(create_app(replace(settings, outbound_reply_token=""), notifier)) as c:
        assert c.post("/outbound/reply", data={"From": WHATSAPP}).status_code == 404


def test_the_reply_endpoint_refuses_a_wrong_secret(client, conn, family):
    response = client.post(
        "/outbound/reply",
        data={"From": WHATSAPP},
        headers={"X-Kettle-Reply-Token": "not-the-token"},
    )
    assert response.status_code == 403


def test_the_reply_endpoint_cancels_the_follow_on(replying_client, conn, family):
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))

    response = replying_client.post(
        "/outbound/reply",
        data={"From": WHATSAPP, "Body": "yes all fine, had a lie-in"},
        headers={"X-Kettle-Reply-Token": "test-reply-token"},
    )
    assert response.status_code == 204

    # The content is gone: only that she answered, and when.
    stored = conn.execute("select * from sent_messages where kind = 'ask'").fetchone()
    assert stored["replied_utc"] is not None
    assert "lie-in" not in str(stored)

    run_twice(conn, transport, at(14, 0))
    assert ("follow_on", "follow_on_family") not in ledger(conn)


def test_the_reply_endpoint_never_repeats_what_she_said(client, conn, family, caplog):
    """Not stored is half of it; not logged is the other half.

    A log line is a copy. The first version of this test only checked the row,
    and a planted `log.info("reply body: %s", ...)` sailed through it.
    """
    import logging

    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))
    secret = "yes all fine, had a lie-in and forgot my phone"
    with caplog.at_level(logging.DEBUG):
        client.post(
            "/outbound/reply",
            data={"From": WHATSAPP, "Body": secret},
            headers={"X-Kettle-Reply-Token": "test-reply-token"},
        )
    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert "lie-in" not in logged and secret not in logged
    assert WHATSAPP not in logged


def test_the_reply_endpoint_is_not_an_oracle(client, conn, family):
    """A known number with no ask and an unknown number answer identically."""
    known = client.post(
        "/outbound/reply",
        data={"From": WHATSAPP},
        headers={"X-Kettle-Reply-Token": "test-reply-token"},
    )
    unknown = client.post(
        "/outbound/reply",
        data={"From": "+15125550999"},
        headers={"X-Kettle-Reply-Token": "test-reply-token"},
    )
    assert known.status_code == unknown.status_code == 204
    assert known.text == unknown.text == ""


# --- posture ------------------------------------------------------------------


def test_the_ledger_is_service_only(conn, authed, family):
    """RLS deny-all: no policy exists, and no privilege either."""
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))
    assert conn.execute("select count(*) as n from sent_messages").fetchone()["n"] > 0

    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute("select * from sent_messages")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute("insert into sent_messages default values")


def test_the_pilot_paths_are_untouched(conn, family):
    """This engine writes its ledger and the founder's ops log, nothing else.

    `ops_alerts` joined the write set with DECISIONS 157 (law #3: it is the
    founder's plumbing log, the same table the heartbeat writes) — and every
    row this engine puts there carries its own kind prefix, so a family-facing
    table gaining a row here still fails loudly.
    """
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))
    for table in ("pings", "digest_sends"):
        count = conn.execute(f"select count(*) as n from {table}").fetchone()["n"]
        assert count == 0, f"the outbound channel wrote to {table}"
    kinds = {
        r["kind"] for r in conn.execute("select kind from ops_alerts").fetchall()
    }
    assert all(k.startswith("outbound_") for k in kinds)


def test_a_reply_just_after_local_midnight_still_cancels_the_follow_on(conn, family):
    """The DECISIONS 145 defect, fixed by ruling and asserted plainly.

    `record_parent_reply` used to look the ask up by the parent's local
    calendar day, so an answer at 00:20 the next morning matched nothing and
    the family was escalated to over a parent who had already said she is
    fine. The match is now the parent's *pending* ask — sent, unanswered,
    follow-on not yet gone — within the last 24 hours, and no calendar day
    appears in it (spec 007 §2.6, DECISIONS 153). This was a `strict=True`
    xfail from the day the clock seam uncovered it until the ruling landed;
    the marker did not outlive the bug.
    """
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))

    # 00:20 IST the next morning: still the same night, a different local day.
    just_after_midnight = at(11, 0) + timedelta(hours=13, minutes=20)
    assert record_parent_reply(conn, WHATSAPP, just_after_midnight) is True
    stored = conn.execute(
        "select replied_utc from sent_messages where kind = 'ask'"
    ).fetchone()
    assert stored["replied_utc"] is not None


# --- the pending-ask matching rule (§2.6, DECISIONS 153) ----------------------


def plant_ask(conn, family, when: datetime) -> None:
    """An ask row at an arbitrary instant, the way the scheduler would write it.

    The scheduler only asks at 11:00, so the boundary cases around midnight and
    the 24-hour window are planted straight into the ledger instead of driven
    through a day; `record_sent_message` is the same write the scheduler uses.
    """
    plan = schedule_for(when, "Asia/Kolkata")
    assert db.record_sent_message(
        conn,
        family.family_id,
        family.parents[0].parent_id,
        plan.local_date,
        "ask",
        "ask_parent",
        "log",
        when,
    )


def test_a_late_evening_ask_answered_after_midnight_matches(conn, family):
    """Ask 23:00, reply 00:20: two calendar days, one conversation."""
    plant_ask(conn, family, at(23, 0))
    assert record_parent_reply(conn, WHATSAPP, at(23, 0) + timedelta(minutes=80)) is True
    stored = conn.execute(
        "select replied_utc from sent_messages where kind = 'ask'"
    ).fetchone()
    assert stored["replied_utc"] is not None


def test_a_reply_with_no_pending_ask_is_noted_and_cancels_nothing(
    conn, family, caplog
):
    """No open question of Kettle's: the arrival is a masked log line, timestamp
    only, and nothing is marked answered."""
    import logging

    with caplog.at_level(logging.INFO, logger="kettle.outbound"):
        assert record_parent_reply(conn, WHATSAPP, at(9, 0)) is False
    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert "no pending ask" in logged
    assert WHATSAPP not in logged
    assert conn.execute("select count(*) as n from sent_messages").fetchone()["n"] == 0


def test_a_reply_after_the_follow_on_went_is_noted_only(conn, family):
    """Once the family has been told, a late reply cannot un-tell them.

    The ask stays visibly unanswered in the ledger — marking it answered after
    the escalation would rewrite what the family was told into something that
    never needed saying.
    """
    ping(conn, family.parents[0].parent_id, "charge_on", at(6, 30))
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))
    run_twice(conn, transport, at(11, 0) + FOLLOW_ON_GRACE)
    assert ("follow_on", "follow_on_family") in ledger(conn)

    late = at(11, 0) + FOLLOW_ON_GRACE + timedelta(minutes=30)
    assert record_parent_reply(conn, WHATSAPP, late) is False
    stored = conn.execute(
        "select replied_utc from sent_messages where kind = 'ask'"
    ).fetchone()
    assert stored["replied_utc"] is None


def test_an_ask_older_than_a_day_is_no_longer_answerable(conn, family):
    """The 24-hour bound: a reply two days late answers no open question."""
    plant_ask(conn, family, at(11, 0))
    assert (
        record_parent_reply(conn, WHATSAPP, at(11, 0) + timedelta(hours=24, minutes=1))
        is False
    )
    stored = conn.execute(
        "select replied_utc from sent_messages where kind = 'ask'"
    ).fetchone()
    assert stored["replied_utc"] is None


def test_a_reply_matches_the_most_recent_pending_ask(conn, family):
    """Two pending asks in the window: the newer one is the open question."""
    plant_ask(conn, family, at(23, 0))
    next_morning = at(23, 0) + timedelta(hours=12)  # 11:00 the next local day
    plant_ask(conn, family, next_morning)

    assert record_parent_reply(conn, WHATSAPP, next_morning + timedelta(minutes=30)) is True
    rows = conn.execute(
        "select sent_utc, replied_utc from sent_messages where kind = 'ask' "
        "order by sent_utc"
    ).fetchall()
    assert rows[0]["replied_utc"] is None
    assert rows[1]["replied_utc"] is not None


# --- the loop (§2.5): Wave A running dark, wired in the lifespan --------------


def test_the_lifespan_runs_the_loop_under_the_flag(conn, settings, notifier, family):
    """OUTBOUND_LOOP on: the scheduler runs as a background task from startup.

    The wait is bounded, not believed: a loop that never runs its first pass
    fails here at the deadline rather than hanging (failure family 5). Clean
    context exit is the shutdown half — a task that were not cancelled would
    stop the app from closing.
    """
    import time as wall
    from dataclasses import replace

    from fastapi.testclient import TestClient

    from kettle.main import create_app

    looped = replace(settings, outbound_loop=True)
    with TestClient(create_app(looped, notifier)) as client:
        state = client.app.state.outbound
        deadline = wall.monotonic() + 10
        while state.last_run_utc is None and wall.monotonic() < deadline:
            wall.sleep(0.05)
        assert state.last_run_utc is not None, "the loop never ran a pass"


def test_the_flag_off_means_no_loop(client):
    """Default off in code: the app runs, the outbound engine does not."""
    import time as wall

    wall.sleep(0.3)  # long enough that a wrongly started loop would have run
    assert client.app.state.outbound.last_run_utc is None


def test_an_unknown_transport_refuses_to_boot(settings, notifier):
    """Fail closed at startup: a typo cannot choose who gets messaged.

    Loop flag off does not soften it — the name is validated before the app
    exists at all, so a misconfiguration is a crash-loop the founder sees, not
    a latent branch waiting for the flag.
    """
    from dataclasses import replace

    from kettle.main import create_app

    with pytest.raises(RuntimeError, match="twilio"):
        create_app(replace(settings, outbound_loop=True, outbound_transport="twilio"), notifier)
    with pytest.raises(RuntimeError, match="whatsapp"):
        create_app(
            replace(settings, outbound_loop=False, outbound_transport="whatsapp"), notifier
        )


def test_the_loop_settings_default_off_and_console():
    """Off in code, on only where fly.toml says so — HEARTBEAT_LOOP's pattern."""
    from kettle.config import settings_from_env

    cfg = settings_from_env({"DATABASE_URL": "postgresql://example/example"})
    assert cfg.outbound_loop is False
    assert cfg.outbound_transport == "console"


def test_fly_config_runs_the_dark_loop():
    """The deploy that follows this pass is the one that starts Wave A
    (DECISIONS 155): both switches on in fly.toml, and no transport named —
    the code default is the console registry's only entry."""
    from pathlib import Path

    text = (Path(__file__).resolve().parent.parent / "fly.toml").read_text()
    assert 'OUTBOUND_LOOP = "1"' in text
    assert 'OUTBOUND_ENABLED = "1"' in text
    assert "OUTBOUND_TRANSPORT" not in text


def test_the_registry_holds_exactly_the_three_transports(settings):
    """Console (dark, the default), resend (child-facing email), and
    twilio_whatsapp (the ask). Selection stays explicit config; the Wave C
    flip is the comma roster, after the ledger review (spec 007 §6.3)."""
    from kettle.outbound import TRANSPORTS, transport_from_name

    assert set(TRANSPORTS) == {"console", "resend", "twilio_whatsapp"}
    assert isinstance(transport_from_name("console", settings), LogTransport)


def test_resend_without_its_key_refuses_to_boot(settings, notifier):
    """Fail closed extends to credentials: a selected transport missing its
    secret is a startup crash, not a send-time surprise (DECISIONS 159)."""
    from dataclasses import replace

    from kettle.main import create_app
    from kettle.outbound import transport_from_name

    with pytest.raises(RuntimeError, match="RESEND_API_KEY"):
        transport_from_name("resend", settings)
    with pytest.raises(RuntimeError, match="RESEND_API_KEY"):
        create_app(replace(settings, outbound_transport="resend"), notifier)
    # With the key present it builds — and carries digests only.
    built = transport_from_name("resend", replace(settings, resend_api_key="re_test"))
    assert built.name == "resend"
    # The Wave C channel ruling: everything child-facing travels by email.
    assert set(built.kinds) == {"digest_morning", "digest_evening", "follow_on", "all_clear"}
    assert built.requires_address is True


# --- Wave B hardening (DECISIONS 157/159) -------------------------------------


def test_a_morning_digest_is_never_sent_late(conn, family, notifier):
    """Past the staleness cutoff the slot records 'skipped' and the founder
    hears; "her morning looked ordinary" at dinnertime is the ruled-out lie."""
    transport = CountingTransport()
    run_twice(conn, transport, at(10, 31), notifier=notifier)
    assert ledger(conn) == []
    assert statuses(conn)["digest_morning"] == "skipped"
    assert len([m for m in notifier.messages if "never sent late" in m]) == 1


def test_a_morning_digest_inside_the_cutoff_still_goes(conn, family):
    transport = CountingTransport()
    run_twice(conn, transport, at(10, 29))
    assert ledger(conn) == [("digest_morning", "digest_morning_quiet")]


def test_a_zero_signal_day_sends_no_evening_reassurance(conn, family, notifier):
    """The evidence gate: 'An ordinary day, start to finish' never renders
    from a day that produced nothing alarm-grade. Ops condition, not copy."""
    transport = CountingTransport()
    run_twice(conn, transport, at(20, 30), notifier=notifier)
    assert ("digest_evening", "digest_evening_normal") not in ledger(conn)
    assert statuses(conn)["digest_evening"] == "skipped"
    assert len([m for m in notifier.messages if "empty evidence window" in m]) == 1


def test_one_alarm_grade_signal_is_evidence_enough_for_the_evening(conn, family):
    ping(conn, family.parents[0].parent_id, "whatsapp", at(7, 0))
    transport = CountingTransport()
    run_twice(conn, transport, at(20, 30))
    assert ("digest_evening", "digest_evening_normal") in ledger(conn)


def test_a_digests_only_transport_never_carries_the_ask(conn, family, notifier):
    """Asks and follow-ons have no channel until Wave C: recorded as skipped
    with an ops alert, never silently absent and never attempted."""

    class DigestsOnly(LogTransport):
        name = "digests-only"
        kinds = ("digest_morning", "digest_evening")

    run_twice(conn, DigestsOnly(), at(11, 0), notifier=notifier)
    assert statuses(conn)["ask"] == "skipped"
    assert len([m for m in notifier.messages if "does not carry" in m]) == 1


def test_no_address_on_an_address_requiring_transport_is_an_unroutable_skip(
    conn, notifier
):
    """The dark transport sends without an address by design; a real one must
    not — no child email means the digest records 'skipped' and alerts."""
    provisioned = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    assert provisioned  # no child email on purpose

    class NeedsAddress(LogTransport):
        name = "needs-address"
        requires_address = True

    run_twice(conn, NeedsAddress(), at(8, 30), notifier=notifier)
    assert ledger(conn) == []
    assert statuses(conn)["digest_morning"] == "skipped"
    assert len([m for m in notifier.messages if "unroutable" in m]) == 1


def test_a_failing_loop_pass_alerts_the_founder_once_per_streak(notifier):
    """A stuck loop costs one ntfy, not one a minute; recovery re-arms it."""
    import asyncio
    from types import SimpleNamespace

    from kettle.outbound import OutboundState, outbound_loop

    class DeadConn:
        def execute(self, *args, **kwargs):
            raise RuntimeError("database gone away")

    state = OutboundState()
    cfg = SimpleNamespace(outbound_enabled=True)

    async def drive() -> None:
        task = asyncio.create_task(
            outbound_loop(DeadConn(), LogTransport(), cfg, notifier, state, interval_s=0)
        )
        await asyncio.sleep(0.1)
        task.cancel()
        from contextlib import suppress

        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(drive())
    assert state.failing is True
    assert len([m for m in notifier.messages if "pass failed" in m]) == 1


def test_a_sent_row_cannot_be_downgraded(conn, family):
    """'sent' is final (0015): a racing pass reporting failure after a
    delivery must not un-send the message in the record."""
    plan = schedule_for(at(11, 0), "Asia/Kolkata")
    args = (
        family.family_id,
        family.parents[0].parent_id,
        plan.local_date,
        "ask",
        "ask_parent",
        "log",
        at(11, 0),
    )
    assert db.record_sent_message(conn, *args, status="sent") is True
    assert db.record_sent_message(conn, *args, status="failed") is False
    assert statuses(conn)["ask"] == "sent"


def test_a_skipped_ask_is_not_answerable(conn, family):
    """Only a sent ask is an open question: a skipped one never reached the
    parent, so a reply cannot match it and mark it answered."""
    plan = schedule_for(at(11, 0), "Asia/Kolkata")
    db.record_sent_message(
        conn,
        family.family_id,
        family.parents[0].parent_id,
        plan.local_date,
        "ask",
        "ask_parent",
        "log",
        at(11, 0),
        status="skipped",
    )
    assert record_parent_reply(conn, WHATSAPP, at(11, 30)) is False
    assert conn.execute(
        "select replied_utc from sent_messages where kind = 'ask'"
    ).fetchone()["replied_utc"] is None


# --- Wave C: the ladder cannot be silently disabled (DECISIONS 157/161/163) ---


class ChildChannels(LogTransport):
    """A resend-shaped transport: everything child-facing, never the ask."""

    name = "child-channels"
    kinds = ("digest_morning", "digest_evening", "follow_on", "all_clear")


def test_a_skipped_ask_still_escalates_on_the_clock(conn, family, notifier):
    """DECISIONS 163's amendment of 159: the follow-on precondition is an ask
    row for the day, ANY status. An ask nobody could deliver must not quietly
    turn the ladder off — the family hears at the deadline regardless."""
    ping(conn, family.parents[0].parent_id, "charge_on", at(6, 30))
    transport = ChildChannels()

    run_twice(conn, transport, at(11, 0), notifier=notifier)
    assert statuses(conn)["ask"] == "skipped"

    run_twice(conn, transport, at(11, 0) + FOLLOW_ON_GRACE, notifier=notifier)
    assert ("follow_on", "follow_on_family") in ledger(conn)
    assert statuses(conn)["ask"] == "skipped"  # still never reached the parent


def test_a_failed_ask_still_escalates_on_the_clock(conn, family):
    """Same amendment, other status: a transport that tried and failed."""
    ping(conn, family.parents[0].parent_id, "charge_on", at(6, 30))
    plan = schedule_for(at(11, 0), "Asia/Kolkata")
    db.record_sent_message(
        conn,
        family.family_id,
        family.parents[0].parent_id,
        plan.local_date,
        "ask",
        "ask_parent",
        "twilio_whatsapp",
        at(11, 0),
        status="failed",
    )
    run_twice(conn, ChildChannels(), at(11, 0) + FOLLOW_ON_GRACE)
    assert ("follow_on", "follow_on_family") in ledger(conn)


def test_a_skipped_ask_is_still_not_answerable_after_the_amendment(conn, family):
    """The amendment reaches the follow-on's clock and nothing else: the reply
    matcher still matches sent asks only (the 159 pin, deliberately kept)."""
    run_twice(conn, ChildChannels(), at(11, 0))
    assert statuses(conn)["ask"] == "skipped"
    assert record_parent_reply(conn, WHATSAPP, at(11, 30)) is False


def test_a_silent_phone_gets_the_unreachable_follow_on_and_never_both(conn, family):
    """DECISIONS 161 body 7: zero pings of ANY grade all day means the report
    is about the phone. One kind, one slot — the two bodies cannot both send."""
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))
    run_twice(conn, transport, at(11, 0) + FOLLOW_ON_GRACE)

    follow_ons = [t for k, t in ledger(conn) if k == "follow_on"]
    assert follow_ons == ["follow_on_unreachable"]
    assert transport.sent[-1][1].startswith("Mom's phone has been silent today")


def test_a_reporting_phone_gets_the_changed_morning_follow_on(conn, family):
    """Signals arriving, routine absent: the standard body, not the phone one.
    A 03:00 ping is not a morning, but it IS a phone that reported today."""
    ping(conn, family.parents[0].parent_id, "charge_on", at(3, 0))
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))
    run_twice(conn, transport, at(11, 0) + FOLLOW_ON_GRACE)

    follow_ons = [t for k, t in ledger(conn) if k == "follow_on"]
    assert follow_ons == ["follow_on_family"]


def test_the_all_clear_goes_once_after_routine_resumes(conn, family):
    """DECISIONS 161 body 6: only after a sent follow-on, on the first
    alarm-grade signal since, once — the ledger row is the resolution record."""
    parent_id = family.parents[0].parent_id
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))
    run_twice(conn, transport, at(11, 0) + FOLLOW_ON_GRACE)
    assert ("follow_on", "follow_on_unreachable") in ledger(conn)

    # Nothing yet: the day is still silent.
    run_twice(conn, transport, at(14, 0))
    assert ("all_clear", "all_clear_family") not in ledger(conn)

    ping(conn, parent_id, "whatsapp", at(14, 30))
    run_twice(conn, transport, at(14, 35))
    assert ("all_clear", "all_clear_family") in ledger(conn)
    assert transport.sent[-1][1].startswith("The shape of Mom's usual day is back.")

    # Once means once — asserted against the transport, not just the ledger:
    # the unique index would hide a re-SEND by refusing only the re-record.
    ping(conn, parent_id, "whatsapp", at(16, 0))
    run_twice(conn, transport, at(16, 5))
    assert [k for k, _ in ledger(conn)].count("all_clear") == 1
    assert [t for t, _ in transport.sent].count("all_clear_family") == 1


def test_no_follow_on_means_no_all_clear_ever(conn, family):
    """A day that resolved before the family heard anything stays quiet: the
    all-clear un-worries, and there is nothing to un-worry."""
    parent_id = family.parents[0].parent_id
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))  # ask goes; no follow-on yet

    assert record_parent_reply(conn, WHATSAPP, at(11, 30)) is True
    ping(conn, parent_id, "whatsapp", at(12, 0))
    run_twice(conn, transport, at(14, 0))
    assert ("follow_on", "follow_on_family") not in ledger(conn)
    assert ("all_clear", "all_clear_family") not in ledger(conn)


def test_a_skipped_follow_on_earns_no_all_clear(conn, family):
    """Sent means sent: a follow-on the family never received cannot be
    un-worried about. The transport here CAN carry the all-clear — only the
    follow-on is undeliverable — so a wrongly-earned all-clear would send and
    show, rather than being masked by its own skip."""

    class NoFollowOn(LogTransport):
        name = "no-follow-on"
        kinds = ("digest_morning", "digest_evening", "ask", "all_clear")

    parent_id = family.parents[0].parent_id
    transport = NoFollowOn()
    run_twice(conn, transport, at(11, 0))
    run_twice(conn, transport, at(11, 0) + FOLLOW_ON_GRACE)
    assert statuses(conn)["follow_on"] == "skipped"

    ping(conn, parent_id, "whatsapp", at(14, 0))
    run_twice(conn, transport, at(14, 5))
    assert ("all_clear", "all_clear_family") not in ledger(conn)
    assert "all_clear_family" not in [t for t, _ in transport.sent]


# --- Wave C: the roster (DECISIONS 163) ---------------------------------------


class AskChannel(LogTransport):
    """A twilio-shaped transport: the ask and nothing else."""

    name = "ask-channel"
    kinds = ("ask",)
    requires_address = True


def test_the_roster_routes_each_kind_to_its_channel(conn, family, notifier):
    """Wave C's shape: ask to the parent by one channel, everything
    child-facing by another, behind the single seam the engine already has."""
    from kettle.outbound import TransportRoster

    ping(conn, family.parents[0].parent_id, "charge_on", at(6, 30))
    roster = TransportRoster([AskChannel(), ChildChannels()])
    run_twice(conn, roster, at(11, 0), notifier=notifier)
    run_twice(conn, roster, at(11, 0) + FOLLOW_ON_GRACE, notifier=notifier)

    rows = {
        r["kind"]: r["transport"]
        for r in conn.execute("select kind, transport from sent_messages").fetchall()
    }
    assert rows["ask"] == "ask-channel"
    assert rows["follow_on"] == "child-channels"
    # A pre-routing skip (this one is the staleness cutoff) records the
    # configured stack's name: no carrier was ever chosen for it.
    assert rows["digest_morning"] == "roster"


def test_the_comma_config_builds_the_roster_and_fails_closed(settings, notifier):
    """OUTBOUND_TRANSPORT='twilio_whatsapp,resend' is the Wave C flip. One bad
    name or missing credential anywhere refuses the whole boot."""
    from dataclasses import replace

    from kettle.main import create_app
    from kettle.outbound import TransportRoster, transport_from_name

    live = replace(
        settings,
        resend_api_key="re_test",
        twilio_account_sid="AC_test",
        twilio_auth_token="tok_test",
        twilio_whatsapp_from="whatsapp:+14155238886",
    )
    roster = transport_from_name("twilio_whatsapp,resend", live)
    assert isinstance(roster, TransportRoster)
    assert roster.for_kind("ask").name == "twilio_whatsapp"
    assert roster.for_kind("follow_on").name == "resend"
    assert roster.for_kind("all_clear").name == "resend"

    with pytest.raises(RuntimeError, match="TWILIO"):
        transport_from_name("twilio_whatsapp,resend", replace(live, twilio_auth_token=""))
    with pytest.raises(RuntimeError, match="telegraph"):
        transport_from_name("twilio_whatsapp,telegraph", live)
    with pytest.raises(RuntimeError, match="TWILIO"):
        create_app(replace(live, outbound_transport="twilio_whatsapp,resend",
                           twilio_whatsapp_from=""), notifier)
