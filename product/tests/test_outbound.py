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
    """Every ledger row, as (kind, template_id), in the order Kettle spoke."""
    # By id, not by sent_utc: everything one run decides shares an instant, so
    # a timestamp sort would report alphabetical order as if it were sequence.
    rows = conn.execute(
        "select kind, template_id from sent_messages order by id"
    ).fetchall()
    return [(r["kind"], r["template_id"]) for r in rows]


def run_twice(conn: psycopg.Connection, transport, now: datetime) -> list:
    """Run the scheduler, then run it again at the same instant.

    The second run must record nothing. Returns what the *first* run decided.
    """
    first = run_outbound(conn, transport, now)
    second = run_outbound(conn, transport, now)
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
    """Law #6 at the evaluator: household plumbing cannot speak for a person."""
    parent_id = family.parents[0].parent_id
    ping(conn, parent_id, "charge_on", at(6, 30))
    ping(conn, parent_id, "device_alive", at(7, 30))
    transport = CountingTransport()

    run_twice(conn, transport, at(11, 0))
    assert ledger(conn) == [
        ("digest_morning", "digest_morning_quiet"),
        ("ask", "ask_parent"),
    ]


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


def test_wave_a_ships_one_transport_and_it_has_no_network_client():
    """The engine runs dark because there is nothing here that could not.

    Not a flag checked before sending: no transport in this module holds an
    HTTP client, so there is no code path from a decision to a message.
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


def test_an_undeliverable_message_records_nothing(conn, family):
    """A real transport says False, and the day's slot stays free for it."""

    class RefusingTransport(LogTransport):
        def send(self, to, template_id, variables):
            return DeliveryResult(delivered=False, transport="refusing")

    assert run_outbound(conn, RefusingTransport(), at(11, 0)) == []
    assert ledger(conn) == []


def test_a_parent_without_a_label_waits_rather_than_rendering_a_blank(conn):
    """Both live parents predate migration 0014 (DECISIONS 149/152).

    A relationship-bearing template must not render with a blank, so it is
    skipped without recording — the day's slot stays free — while the ask,
    which names nobody, still goes: a missing label never delays the parent
    being asked first. Setting the label releases everything the slot held.
    """
    provisioned = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    add_child_email(conn, provisioned.family_id)
    set_parent_whatsapp(conn, provisioned.parents[0].parent_id, WHATSAPP)
    token = provisioned.parents[0].device_token
    transport = CountingTransport()

    # Quiet morning: the digest and, later, the follow-on both need the label.
    run_twice(conn, transport, at(8, 30))
    assert ledger(conn) == []

    run_twice(conn, transport, at(11, 0))
    assert ledger(conn) == [("ask", "ask_parent")]

    run_twice(conn, transport, at(11, 0) + FOLLOW_ON_GRACE)
    assert ledger(conn) == [("ask", "ask_parent")]

    assert set_parent_relationship(conn, token, "Mom") == "Amma"
    run_twice(conn, transport, at(11, 0) + FOLLOW_ON_GRACE + timedelta(minutes=5))
    kinds = [kind for kind, _ in ledger(conn)]
    assert "digest_morning" in kinds and "follow_on" in kinds
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
    """This engine writes to its own table and nothing else's."""
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))
    for table in ("pings", "digest_sends", "ops_alerts"):
        count = conn.execute(f"select count(*) as n from {table}").fetchone()["n"]
        assert count == 0, f"the outbound channel wrote to {table}"


@pytest.mark.xfail(
    strict=True,
    reason="DECISIONS 142: a reply after local midnight matches no ask and the "
    "follow-on fires anyway. Needs a PM ruling on the matching rule, so this "
    "pins the behaviour that is wanted rather than the behaviour that ships.",
)
def test_a_reply_just_after_local_midnight_still_cancels_the_follow_on(conn, family):
    """The bug the clock seam uncovered, kept visible until it is ruled on.

    `record_parent_reply` looks up the ask by the parent's **local calendar day**.
    A parent asked at 11:00 who answers at 00:20 the next morning is answering on
    a different local day, so no ask matches, nothing is marked replied, and the
    follow-on to her family goes out at its appointed hour — after she has already
    said she is fine. That is the exact failure spec 007 §2.6 exists to prevent,
    and it is worse than a missed message: it escalates to the family over a
    parent who answered.

    Not fixed here because the repair is a spec-level choice, not a bug fix: match
    the most recent *unanswered* ask instead of the day's, and then decide the
    bound on "recent". Both are the PM's to rule. `strict=True` means the day this
    is fixed, this test fails as XPASS and has to be turned into a normal
    assertion — the marker cannot outlive the bug.
    """
    transport = CountingTransport()
    run_twice(conn, transport, at(11, 0))

    # 00:20 IST the next morning: still the same night, a different local day.
    just_after_midnight = at(11, 0) + timedelta(hours=13, minutes=20)
    assert record_parent_reply(conn, WHATSAPP, just_after_midnight) is True
