"""The demo family's seeded past (DECISIONS 242).

What this file is really guarding is the refusal. Everything else here is
about a demo looking right; the first test is about a script that writes a
month of invented history into a family Kettle is actually watching. That is
not a bug anyone can undo from the app, so it is checked before the first
write rather than per row, and it is checked here first.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from html import unescape
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
import pytest

from kettle import db
from kettle.outbound import MORNING_DIGEST
from kettle.outbound_templates import render, template
from kettle.provisioning import provision_family
from kettle.signals import ALARM_GRADE
from scripts.seed_demo_history import (
    ANSWERED_ASK_DAYS_AGO,
    APPOINTMENT_DAYS_AGO,
    CHANGED_MORNING_DAYS_AGO,
    LATE_START_DAYS_AGO,
    MARKER,
    NOTE_APPOINTMENT,
    NOTE_AUTHOR,
    NOTE_CHANGED_MORNING,
    NOTE_UNREACHABLE,
    UNREACHABLE_DAYS_AGO,
    Refused,
    check_safe,
    seed,
)
from testsupport import BASE_URL


@pytest.fixture
def whitakers(conn: psycopg.Connection):
    """The demo family as DECISIONS 242 rules it: no numbers on either parent."""
    family = provision_family(
        conn,
        name="Whitaker",
        tz="America/New_York",
        parents=[
            ("Linda", "America/Phoenix", "Mom"),
            ("Bill", "America/Phoenix", "Dad"),
        ],
        base_url=BASE_URL,
        owner_name="Sarah",
        # The merged-method install (DECISIONS 107), which is what a family
        # provisioned today actually receives.
        signals=["routine", "charger", "device_alive"],
    )
    return family


def parent_by(conn: psycopg.Connection, family_id, relationship: str):
    return conn.execute(
        "select id, tz from parents where family_id = %s and relationship = %s",
        (family_id, relationship),
    ).fetchone()


def ledger(conn: psycopg.Connection, parent_id, local_date: str) -> dict[str, tuple]:
    rows = conn.execute(
        "select kind, template_id, status from sent_messages "
        "where parent_id = %s and local_date = %s",
        (parent_id, local_date),
    ).fetchall()
    return {r["kind"]: (r["template_id"], r["status"]) for r in rows}


def parent_relationship(conn, parent_row) -> str:
    return conn.execute(
        "select relationship from parents where id = %s", (parent_row["id"],)
    ).fetchone()["relationship"]


def local_day(parent_row, days_ago: int) -> str:
    tz = ZoneInfo(parent_row["tz"])
    return (datetime.now(tz).date() - timedelta(days=days_ago)).isoformat()


# --- the refusal --------------------------------------------------------------


def test_a_family_anyone_can_be_reached_at_is_refused_before_any_write(
    conn, whitakers
):
    """A phone number is what separates a demo from somebody's mother."""
    mom = parent_by(conn, whitakers.family_id, "Mom")
    conn.execute(
        "update parents set whatsapp_e164 = %s where id = %s", ("+16175550143", mom["id"])
    )
    with pytest.raises(Refused, match="phone number"):
        seed(conn, whitakers.family_id, days=3)
    # Refused BEFORE the first write, not partway through it.
    assert conn.execute("select count(*) as n from pings").fetchone()["n"] == 0
    assert conn.execute("select count(*) as n from sent_messages").fetchone()["n"] == 0


def test_an_sms_number_alone_is_enough_to_refuse(conn, whitakers):
    dad = parent_by(conn, whitakers.family_id, "Dad")
    conn.execute(
        "update parents set phone_e164 = %s where id = %s", ("+16175550143", dad["id"])
    )
    with pytest.raises(Refused, match="phone number"):
        check_safe(conn, whitakers.family_id)


@pytest.mark.parametrize("name", ["Suryaprakasam", "rehearsal", "  Rehearsal  "])
def test_a_real_family_name_is_refused_even_with_no_numbers(conn, whitakers, name):
    """Belt to the number check's braces: numbers can be cleared by accident."""
    conn.execute(
        "update families set name = %s where id = %s", (name, whitakers.family_id)
    )
    with pytest.raises(Refused, match="real family"):
        check_safe(conn, whitakers.family_id)


def test_an_unknown_family_id_is_refused_rather_than_silently_doing_nothing(conn):
    with pytest.raises(Refused, match="no family"):
        check_safe(conn, "11111111-1111-1111-1111-111111111111")


# --- idempotence and determinism ----------------------------------------------


def snapshot(conn: psycopg.Connection, family_id) -> tuple:
    """Everything the seeder owns, in a comparable shape."""
    pings = conn.execute(
        "select p.signal, p.ts_utc, p.parent_id from pings p "
        "join parents pa on pa.id = p.parent_id "
        "where pa.family_id = %s order by p.ts_utc, p.signal",
        (family_id,),
    ).fetchall()
    messages = conn.execute(
        # replied_utc is in here so the answered day's reply is covered by the
        # idempotence and determinism checks like every other seeded value.
        "select parent_id, local_date, kind, template_id, status, sent_utc, "
        "replied_utc from sent_messages where family_id = %s "
        "order by local_date, parent_id, kind",
        (family_id,),
    ).fetchall()
    notes = conn.execute(
        "select parent_id, author_label, body, event_date, kind "
        "from journal_entries where family_id = %s order by body",
        (family_id,),
    ).fetchall()
    return (
        [tuple(r.values()) for r in pings],
        [tuple(r.values()) for r in messages],
        [tuple(r.values()) for r in notes],
    )


def test_running_it_twice_leaves_one_copy_of_everything(conn, whitakers):
    """The founder will re-run this. Twice must not mean twice the history."""
    first = seed(conn, whitakers.family_id, days=30, seed_value=42)
    before = snapshot(conn, whitakers.family_id)
    second = seed(conn, whitakers.family_id, days=30, seed_value=42)
    after = snapshot(conn, whitakers.family_id)

    assert (first.pings, first.messages, first.notes) == (
        second.pings,
        second.messages,
        second.notes,
    )
    assert before == after


def test_the_same_seed_writes_the_same_day_down_to_the_second(conn, whitakers):
    """A screenshot taken after a re-run is the same picture as before it."""
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    once = snapshot(conn, whitakers.family_id)
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    assert snapshot(conn, whitakers.family_id) == once


def test_a_different_seed_moves_the_timestamps_but_not_the_story(conn, whitakers):
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    pings_42, messages_42, notes_42 = snapshot(conn, whitakers.family_id)
    seed(conn, whitakers.family_id, days=30, seed_value=7)
    pings_7, messages_7, notes_7 = snapshot(conn, whitakers.family_id)

    assert pings_42 != pings_7, "the jitter is not actually seeded"
    # The ladder is decided by the clock, not by the jitter, so the story days
    # read the same however the pings fall inside them.
    assert messages_42 == messages_7
    assert notes_42 == notes_7


def test_it_writes_nothing_outside_the_family_it_was_given(conn, whitakers):
    """A second family in the same database is untouched, before and after."""
    other = provision_family(
        conn,
        name="Brennan",
        tz="America/New_York",
        parents=[("Joan", "America/New_York", "Mom")],
        base_url=BASE_URL,
        signals=["routine", "charger", "device_alive"],
    )
    seed(conn, other.family_id, days=5, seed_value=1)
    untouched = snapshot(conn, other.family_id)

    seed(conn, whitakers.family_id, days=30, seed_value=42)
    seed(conn, whitakers.family_id, days=30, seed_value=42)  # and the delete pass

    assert snapshot(conn, other.family_id) == untouched


# --- the three story days -----------------------------------------------------


def test_a_normal_day_is_two_digests_and_nothing_else(conn, whitakers):
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    mom = parent_by(conn, whitakers.family_id, "Mom")
    # A day that is none of the three stories.
    plain = ledger(conn, mom["id"], local_day(mom, 3))
    assert plain == {
        "digest_morning": ("digest_morning_normal", "sent"),
        "digest_evening": ("digest_evening_normal", "sent"),
    }


def test_the_late_morning_is_never_asked_about(conn, whitakers):
    """Mom's quiet start that turned normal.

    The first habit app lands at 10:40: after the 08:30 digest has already
    called the morning quiet, but before the 11:00 threshold that would arm
    the ask. So the family sees a quiet morning and a recovered evening, and
    nothing was ever sent to her - which is the whole point of the shape.
    """
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    mom = parent_by(conn, whitakers.family_id, "Mom")
    day = local_day(mom, LATE_START_DAYS_AGO)
    assert ledger(conn, mom["id"], day) == {
        "digest_morning": ("digest_morning_quiet", "sent"),
        "digest_evening": ("digest_evening_recovered", "sent"),
    }

    # And the pings actually justify it: nothing alarm-grade before 08:30,
    # something before 11:00.
    tz = ZoneInfo(mom["tz"])
    start = datetime.fromisoformat(day).replace(tzinfo=tz)
    assert db.count_alarm_pings_between(
        conn, mom["id"], start.replace(hour=6), start.replace(hour=8, minute=30)
    ) == 0
    assert db.count_alarm_pings_between(
        conn, mom["id"], start.replace(hour=6), start.replace(hour=11)
    ) > 0


def test_the_unreachable_day_runs_the_whole_ladder_and_withholds_the_evening(
    conn, whitakers
):
    """Dad's day: asked, unanswered, escalated, resolved.

    Every rung is here because the engine would have written it, including the
    one that is an ABSENCE: a day a follow-on went out withholds its evening
    digest (DECISIONS 164), and the engine records that as a skipped row
    rather than as no row at all.
    """
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    dad = parent_by(conn, whitakers.family_id, "Dad")
    day = local_day(dad, UNREACHABLE_DAYS_AGO)
    assert ledger(conn, dad["id"], day) == {
        "digest_morning": ("digest_morning_quiet", "sent"),
        "ask": ("ask_parent", "sent"),
        # Nothing of ANY grade had arrived by the grace mark, so the report is
        # about the phone rather than about the morning.
        "follow_on": ("follow_on_unreachable", "sent"),
        "all_clear": ("all_clear_family", "sent"),
        "digest_evening": ("digest_evening_recovered", "skipped"),
    }

    # The ask went unanswered: that is what let the follow-on fire at all.
    assert conn.execute(
        "select replied_utc from sent_messages where parent_id = %s "
        "and local_date = %s and kind = 'ask'",
        (dad["id"], day),
    ).fetchone()["replied_utc"] is None

    # And the phone really was silent: zero pings of any grade before the
    # follow-on, which is what makes it the unreachable body.
    tz = ZoneInfo(dad["tz"])
    midnight = datetime.fromisoformat(day).replace(tzinfo=tz)
    assert db.count_pings_between(
        conn, dad["id"], midnight, midnight.replace(hour=13)
    ) == 0
    assert db.count_alarm_pings_between(
        conn, dad["id"], midnight.replace(hour=13), midnight + timedelta(days=1)
    ) > 0


def test_the_family_note_sits_on_the_day_it_explains(conn, whitakers):
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    dad = parent_by(conn, whitakers.family_id, "Dad")
    note = conn.execute(
        "select parent_id, author_label, body, event_date, kind from journal_entries "
        "where family_id = %s and body = %s",
        (whitakers.family_id, NOTE_UNREACHABLE),
    ).fetchone()
    assert note is not None
    assert note["author_label"] == NOTE_AUTHOR == "Sarah"
    assert note["parent_id"] == dad["id"]
    assert note["kind"] == "note"          # a family note, not a Kettle line
    assert note["event_date"] is None      # it explains a day, it is not an event


def test_the_appointment_note_is_still_ahead_of_the_demo(conn, whitakers):
    """An 'upcoming' entry the app files in the past is just an old note.

    The body was written nineteen days ago; the date it points at has to stay
    in the future or the Memory tab's upcoming strip has nothing to show.
    """
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    mom = parent_by(conn, whitakers.family_id, "Mom")
    note = conn.execute(
        "select parent_id, author_label, body, event_date, created_utc "
        "from journal_entries where family_id = %s and body = %s",
        (whitakers.family_id, NOTE_APPOINTMENT),
    ).fetchone()
    assert note is not None
    assert note["parent_id"] == mom["id"]
    assert note["author_label"] == NOTE_AUTHOR

    today = datetime.now(ZoneInfo(mom["tz"])).date()
    assert note["event_date"] > today, "the appointment has to still be coming"
    assert note["event_date"].weekday() == 3, "the body says Thursday"
    # Written on the story day, which is nineteen days behind the demo.
    assert note["created_utc"].astimezone(ZoneInfo(mom["tz"])).date() == (
        today - timedelta(days=APPOINTMENT_DAYS_AGO)
    )
    # That day itself was otherwise unremarkable, which is the point of it.
    assert ledger(conn, mom["id"], local_day(mom, APPOINTMENT_DAYS_AGO)) == {
        "digest_morning": ("digest_morning_normal", "sent"),
        "digest_evening": ("digest_evening_normal", "sent"),
    }



def test_the_answered_ask_never_reaches_the_family(conn, whitakers):
    """Day (d), and the shape the whole product exists for (DECISIONS 243).

    The phone is awake all morning - off the charger, heartbeat firing - and
    the habit apps simply never open. Kettle notices, asks HER at eleven, she
    answers, and nobody else is told anything. No follow-on, no all-clear:
    the ladder stopped at the person it was about.
    """
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    dad = parent_by(conn, whitakers.family_id, "Dad")
    day = local_day(dad, ANSWERED_ASK_DAYS_AGO)

    assert ledger(conn, dad["id"], day) == {
        "digest_morning": ("digest_morning_quiet", "sent"),
        "ask": ("ask_parent", "sent"),
        "digest_evening": ("digest_evening_recovered", "sent"),
    }

    ask = conn.execute(
        "select sent_utc, replied_utc from sent_messages where parent_id = %s "
        "and local_date = %s and kind = 'ask'",
        (dad["id"], day),
    ).fetchone()
    assert ask["replied_utc"] is not None, "the answered day has to be answered"
    assert ask["replied_utc"] > ask["sent_utc"]

    # The phone WAS reporting: this is a changed morning, not a silent phone.
    tz = ZoneInfo(dad["tz"])
    midnight = datetime.fromisoformat(day).replace(tzinfo=tz)
    assert db.count_pings_between(
        conn, dad["id"], midnight, midnight.replace(hour=11)
    ) > 0
    assert db.count_alarm_pings_between(
        conn, dad["id"], midnight.replace(hour=6), midnight.replace(hour=11)
    ) == 0


def test_the_changed_morning_tells_the_family_and_then_resolves(conn, whitakers):
    """Day (e): the same morning, unanswered.

    Because the phone reported all morning, the escalation is the
    changed-morning body rather than the silent-phone one - the distinction
    DECISIONS 157/161 drew, and the one day (b) cannot demonstrate.
    """
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    mom = parent_by(conn, whitakers.family_id, "Mom")
    day = local_day(mom, CHANGED_MORNING_DAYS_AGO)

    assert ledger(conn, mom["id"], day) == {
        "digest_morning": ("digest_morning_quiet", "sent"),
        "ask": ("ask_parent", "sent"),
        "follow_on": ("follow_on_family", "sent"),
        "all_clear": ("all_clear_family", "sent"),
        # A follow-on went out, so the evening note is withheld (DECISIONS 164).
        "digest_evening": ("digest_evening_recovered", "skipped"),
    }
    assert conn.execute(
        "select replied_utc from sent_messages where parent_id = %s "
        "and local_date = %s and kind = 'ask'",
        (mom["id"], day),
    ).fetchone()["replied_utc"] is None

    tz = ZoneInfo(mom["tz"])
    midnight = datetime.fromisoformat(day).replace(tzinfo=tz)
    # Reporting, but not opening anything: the two facts that together choose
    # follow_on_family over follow_on_unreachable.
    assert db.count_pings_between(
        conn, mom["id"], midnight, midnight.replace(hour=13)
    ) > 0
    assert db.count_alarm_pings_between(
        conn, mom["id"], midnight.replace(hour=6), midnight.replace(hour=13)
    ) == 0
    assert db.count_alarm_pings_between(
        conn, mom["id"], midnight.replace(hour=15), midnight + timedelta(days=1)
    ) > 0


def test_the_changed_morning_carries_its_note(conn, whitakers):
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    mom = parent_by(conn, whitakers.family_id, "Mom")
    note = conn.execute(
        "select parent_id, author_label, body, event_date, kind, created_utc "
        "from journal_entries where family_id = %s and body = %s",
        (whitakers.family_id, NOTE_CHANGED_MORNING),
    ).fetchone()
    assert note is not None
    assert note["body"] == "Was at Carol's. Left the phone on the counter."
    assert note["author_label"] == NOTE_AUTHOR
    assert note["parent_id"] == mom["id"]
    assert note["kind"] == "note"
    assert note["event_date"] is None
    # Written that evening, on the day it explains.
    assert note["created_utc"].astimezone(ZoneInfo(mom["tz"])).date() == (
        datetime.now(ZoneInfo(mom["tz"])).date()
        - timedelta(days=CHANGED_MORNING_DAYS_AGO)
    )


def test_every_kind_the_product_can_send_has_an_example(conn, whitakers):
    """The reason there are five story days rather than three.

    A demo that cannot show a rung has no way to answer a question about it.
    """
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    templates = {
        row["template_id"]
        for row in conn.execute(
            "select distinct template_id from sent_messages where family_id = %s",
            (whitakers.family_id,),
        ).fetchall()
    }
    assert templates == {
        "digest_morning_normal",
        "digest_morning_quiet",
        "digest_evening_normal",
        "digest_evening_recovered",
        "ask_parent",
        "follow_on_family",
        "follow_on_unreachable",
        "all_clear_family",
    }

def test_every_seeded_row_carries_the_marker(conn, whitakers):
    """The marker is what makes a re-run safe; nothing may slip past it."""
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    assert conn.execute(
        "select count(*) as n from pings p join parents pa on pa.id = p.parent_id "
        "where pa.family_id = %s and (p.ip_hash is distinct from %s)",
        (whitakers.family_id, MARKER),
    ).fetchone()["n"] == 0
    assert conn.execute(
        "select count(*) as n from sent_messages "
        "where family_id = %s and transport is distinct from %s",
        (whitakers.family_id, MARKER),
    ).fetchone()["n"] == 0


def test_the_pings_speak_the_parents_own_vocabulary(conn, whitakers):
    """No invented signal names: the demo uses what the family was given."""
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    for relationship in ("Mom", "Dad"):
        parent = parent_by(conn, whitakers.family_id, relationship)
        allowed = {r["signal"] for r in db.parent_active_signals(conn, parent["id"])}
        used = {
            r["signal"]
            for r in conn.execute(
                "select distinct signal from pings where parent_id = %s", (parent["id"],)
            ).fetchall()
        }
        assert used, relationship
        assert used <= allowed, f"{relationship} pinged {used - allowed}"


# --- the replay, checked against the engine itself ----------------------------


def test_the_engine_would_have_written_this_exact_ledger(conn, whitakers, notifier):
    """The strongest claim this file makes, so it is checked and not asserted.

    `day_ledger` is a hand-written replay of `_due_for_parent`, and a replay
    drifts the moment the ladder changes. So: keep the seeded PINGS, throw the
    seeded ledger away, run the real engine across the story day at the
    instants its schedule cares about, and compare what it decided with what
    the seeder claimed it would decide.

    If the ladder is ever reworded or re-timed, this fails and the demo stops
    telling a story the product no longer tells.

    `replied_utc` is deliberately outside the comparison: a reply arrives
    through the webhook, not through the ladder, so no replay can produce one.
    The answered day still reproduces its shape without it, because the
    morning resuming before the grace mark closes the ladder on its own - the
    reply and the resumed habits are two independent reasons the family is
    never told, and the seeded day has both.

    The dark transport carries it, which is the honest comparison: what is
    being checked is which rungs fire and which template each chooses. A real
    sender would find no number on these parents and record the ask
    unroutable, which is exactly the safety DECISIONS 242 asked for - the
    seeded past shows an ask that went out, and the live family can never
    send one.
    """
    from kettle.outbound import LogTransport, run_outbound

    seed(conn, whitakers.family_id, days=30, seed_value=42)
    dad = parent_by(conn, whitakers.family_id, "Dad")
    mom = parent_by(conn, whitakers.family_id, "Mom")
    tz = ZoneInfo(dad["tz"])

    for relationship, days_ago in (
        ("Dad", UNREACHABLE_DAYS_AGO),
        ("Mom", LATE_START_DAYS_AGO),
        ("Dad", ANSWERED_ASK_DAYS_AGO),
        ("Mom", CHANGED_MORNING_DAYS_AGO),
        ("Mom", 3),
    ):
        parent = dad if relationship == "Dad" else mom
        day = local_day(parent, days_ago)
        expected = ledger(conn, parent["id"], day)

        conn.execute(
            "delete from sent_messages where parent_id = %s and local_date = %s",
            (parent["id"], day),
        )
        midnight = datetime.fromisoformat(day).replace(tzinfo=tz)
        # Every instant the schedule turns on, in order, the way a minutely
        # loop would have reached them.
        # 15:30 is there for the changed-morning day, whose all-clear waits
        # for the habits to resume mid-afternoon; the others do not mind it.
        for hour, minute in (
            (8, 30), (11, 0), (13, 0), (13, 30), (15, 30), (20, 30)
        ):
            run_outbound(
                conn,
                LogTransport(),
                midnight.replace(hour=hour, minute=minute),
                notifier=notifier,
                enabled=True,
            )

        decided = ledger(conn, parent["id"], day)
        assert decided == expected, f"{relationship}, {days_ago} days ago"


def test_a_reseed_leaves_alone_what_it_did_not_write(conn, whitakers):
    """The marker's actual job, which the family-scoping tests do not cover.

    Someone will tap through the demo and add a note, and a stray real ping
    can reach any parent with a device. Both live INSIDE the demo family, so
    scoping the delete to the family is not enough - only the marker tells the
    seeder which rows are its own to replace.
    """
    seed(conn, whitakers.family_id, days=5, seed_value=42)
    mom = parent_by(conn, whitakers.family_id, "Mom")

    # A ping that did not come from the seeder, and a note a person typed.
    conn.execute(
        "insert into pings (parent_id, signal, ts_utc, ip_hash) "
        "values (%s, 'routine', now(), null)",
        (mom["id"],),
    )
    conn.execute(
        "insert into journal_entries (family_id, parent_id, author_label, body) "
        "values (%s, %s, 'Sarah', 'She sounded good on the phone today.')",
        (whitakers.family_id, mom["id"]),
    )

    seed(conn, whitakers.family_id, days=5, seed_value=42)

    assert conn.execute(
        "select count(*) as n from pings where parent_id = %s and ip_hash is null",
        (mom["id"],),
    ).fetchone()["n"] == 1, "a real ping was deleted by the reseed"
    assert conn.execute(
        "select count(*) as n from journal_entries where family_id = %s and body = %s",
        (whitakers.family_id, "She sounded good on the phone today."),
    ).fetchone()["n"] == 1, "a family's own note was deleted by the reseed"


# --- the engine walks past a demo family (DECISIONS 245) ----------------------


def test_a_demo_family_produces_nothing_while_its_neighbour_behaves(
    conn, whitakers, notifier
):
    """The gap DECISIONS 245 found, closed and pinned.

    "No phone number" (242) stops the ASK. It stops nothing else: the engine
    walks every parent in the database, so a seeded demo family would mail the
    owner a quiet-morning digest and the founder an ops alert, daily, about a
    household that does not exist. A family that exists to be photographed
    does not get to send anybody mail.

    Both families here have a silent parent and are otherwise identical, so
    the only thing separating "nothing at all" from "the full ladder" is the
    one bit.
    """
    from kettle.outbound import LogTransport, run_outbound

    real = provision_family(
        conn,
        name="Brennan",
        tz="America/Phoenix",
        parents=[("Joan", "America/Phoenix", "Mom")],
        base_url=BASE_URL,
        signals=["routine", "charger", "device_alive"],
    )
    conn.execute(
        "update families set demo = true where id = %s", (whitakers.family_id,)
    )
    conn.commit()

    # Nobody has pinged today in either family, so the ladder has every reason
    # to fire for both. Late enough that the digest, the ask and the follow-on
    # are all past due.
    tz = ZoneInfo("America/Phoenix")
    now = datetime.now(tz).replace(hour=14, minute=0, second=0, microsecond=0)
    run_outbound(conn, LogTransport(), now, notifier=notifier, enabled=True)

    demo_rows = conn.execute(
        "select count(*) as n from sent_messages where family_id = %s",
        (whitakers.family_id,),
    ).fetchone()["n"]
    real_rows = conn.execute(
        "select count(*) as n from sent_messages where family_id = %s",
        (real.family_id,),
    ).fetchone()["n"]

    assert demo_rows == 0, "a demo family wrote a ledger row"
    assert real_rows > 0, "the neighbour stopped behaving as it does today"

    # And no ops alert either: a skipped ask normally raises one, and the
    # founder should not be told about scenery. Scoped to the demo family on
    # purpose - the neighbour's own skipped ask SHOULD alert, and asserting
    # zero alerts globally would have passed for the wrong reason the moment
    # the neighbour went quiet.
    assert conn.execute(
        "select count(*) as n from ops_alerts where family_id = %s",
        (whitakers.family_id,),
    ).fetchone()["n"] == 0
    assert conn.execute(
        "select count(*) as n from ops_alerts where family_id = %s",
        (real.family_id,),
    ).fetchone()["n"] > 0


def test_the_flag_is_off_until_somebody_sets_it(conn, whitakers):
    """Every existing family keeps behaving exactly as it does today."""
    assert conn.execute(
        "select demo from families where id = %s", (whitakers.family_id,)
    ).fetchone()["demo"] is False


# --- today, in progress (DECISIONS 245) ---------------------------------------


def today_pings(conn, parent_row) -> list:
    tz = ZoneInfo(parent_row["tz"])
    midnight = datetime.combine(datetime.now(tz).date(), time(0, 0), tzinfo=tz)
    return conn.execute(
        "select signal, ts_utc from pings where parent_id = %s and ts_utc >= %s "
        "order by ts_utc",
        (parent_row["id"], midnight),
    ).fetchall()


def test_without_through_now_today_is_empty(conn, whitakers):
    """The default stops at yesterday, exactly as it always has."""
    seed(conn, whitakers.family_id, days=30, seed_value=42)
    for relationship in ("Mom", "Dad"):
        assert today_pings(conn, parent_by(conn, whitakers.family_id, relationship)) == []


def test_through_now_makes_the_glance_read_as_live(conn, whitakers):
    """The point of the flag: "Heard from N minutes ago", not "nothing yet"."""
    seed(conn, whitakers.family_id, days=30, seed_value=42, through_now=True)
    for relationship in ("Mom", "Dad"):
        parent = parent_by(conn, whitakers.family_id, relationship)
        tz = ZoneInfo(parent["tz"])
        rows = today_pings(conn, parent)
        assert rows, relationship

        newest = rows[-1]["ts_utc"]
        age = datetime.now(tz) - newest
        assert timedelta() <= age < timedelta(hours=1), f"{relationship}: {age}"
        # Alarm-grade, or the glance has nothing to say it heard from her.
        assert ALARM_GRADE.get(rows[-1]["signal"], False)


def test_through_now_never_seeds_the_future(conn, whitakers):
    """A ping timestamped ahead of the clock is a demo that cannot be trusted."""
    seed(conn, whitakers.family_id, days=30, seed_value=42, through_now=True)
    for relationship in ("Mom", "Dad"):
        parent = parent_by(conn, whitakers.family_id, relationship)
        tz = ZoneInfo(parent["tz"])
        for row in today_pings(conn, parent):
            assert row["ts_utc"] <= datetime.now(tz)


def test_through_now_writes_no_ledger_row_for_today(conn, whitakers):
    """Today's digests have not happened yet, so the demo does not claim them.

    An 08:30 digest invented at 09:00 would be the demo saying Kettle said
    something it did not - and the whole point of the replay test is that this
    seeder only ever records what the engine would.
    """
    seed(conn, whitakers.family_id, days=30, seed_value=42, through_now=True)
    for relationship in ("Mom", "Dad"):
        parent = parent_by(conn, whitakers.family_id, relationship)
        today = datetime.now(ZoneInfo(parent["tz"])).date().isoformat()
        assert ledger(conn, parent["id"], today) == {}


def test_re_running_moves_the_front_edge_and_leaves_the_past_alone(conn, whitakers):
    """Idempotent behind today; live at the front (DECISIONS 245)."""
    def past_only(family_id):
        pings, messages, notes = snapshot(conn, family_id)
        mom = parent_by(conn, family_id, "Mom")
        midnight = datetime.combine(
            datetime.now(ZoneInfo(mom["tz"])).date(), time(0, 0),
            tzinfo=ZoneInfo(mom["tz"]),
        )
        return ([p for p in pings if p[1] < midnight], messages, notes)

    seed(conn, whitakers.family_id, days=30, seed_value=42, through_now=True)
    before = past_only(whitakers.family_id)
    first_edge = today_pings(conn, parent_by(conn, whitakers.family_id, "Mom"))[-1]

    seed(conn, whitakers.family_id, days=30, seed_value=42, through_now=True)
    after = past_only(whitakers.family_id)
    second_edge = today_pings(conn, parent_by(conn, whitakers.family_id, "Mom"))[-1]

    assert before == after, "a re-run rewrote history behind today"
    # The edge tracks the clock, so it moves forward (or holds, within the
    # second the two runs share) but never backwards.
    assert second_edge["ts_utc"] >= first_edge["ts_utc"]
    # And there is still exactly one front edge, not two stacked up.
    assert len(today_pings(conn, parent_by(conn, whitakers.family_id, "Mom"))) == len(
        today_pings(conn, parent_by(conn, whitakers.family_id, "Mom"))
    )


def test_today_replays_as_a_normal_day_so_far(conn, whitakers, notifier):
    """The same replay discipline the story days get.

    Run the real engine at this moment over today's seeded pings: a morning
    that has reported normally owes a normal morning digest and no ask, which
    is what a demo opened at lunchtime should be showing.
    """
    from kettle.outbound import LogTransport, run_outbound

    seed(conn, whitakers.family_id, days=30, seed_value=42, through_now=True)
    mom = parent_by(conn, whitakers.family_id, "Mom")
    tz = ZoneInfo(mom["tz"])
    now_local = datetime.now(tz)
    run_outbound(conn, LogTransport(), now_local, notifier=notifier, enabled=True)
    decided = ledger(conn, mom["id"], now_local.date().isoformat())

    # Both branches assert, rather than skipping before the digest slot: a
    # test that proves nothing between midnight and 08:30 Phoenix is a test
    # that proves nothing on most of the runs that matter.
    if now_local.time() < MORNING_DIGEST:
        assert decided == {}, "nothing is due before the morning slot"
    else:
        assert decided.get("digest_morning") == ("digest_morning_normal", "sent")
    # Either way, a morning that reported is never asked about.
    assert "ask" not in decided


# --- rendering a seeded day's digests (DECISIONS 245) -------------------------


def test_the_renderer_writes_the_template_ids_the_ledger_names(conn, whitakers, tmp_path):
    """Each story day renders the bodies its own ledger row named.

    The mapping is the table in the DECISIONS 243 build report, checked
    against the files rather than against the ledger it came from - the point
    of this script is that what lands on disk is what the engine decided, and
    a renderer that quietly picked its own template would still pass a test
    that only read sent_messages.
    """
    from scripts.render_digest import render_day

    seed(conn, whitakers.family_id, days=30, seed_value=42)
    mom = parent_by(conn, whitakers.family_id, "Mom")
    dad = parent_by(conn, whitakers.family_id, "Dad")

    cases = [
        # (parent, days ago, expected template id per kind that SENT)
        ("Linda", mom, 3, {"digest_morning": "digest_morning_normal",
                           "digest_evening": "digest_evening_normal"}),
        ("Linda", mom, LATE_START_DAYS_AGO,
         {"digest_morning": "digest_morning_quiet",
          "digest_evening": "digest_evening_recovered"}),
        ("Bill", dad, ANSWERED_ASK_DAYS_AGO,
         {"digest_morning": "digest_morning_quiet",
          "digest_evening": "digest_evening_recovered"}),
        # The withheld evenings: a skipped row is not an email, so no file.
        ("Bill", dad, UNREACHABLE_DAYS_AGO,
         {"digest_morning": "digest_morning_quiet"}),
        ("Linda", mom, CHANGED_MORNING_DAYS_AGO,
         {"digest_morning": "digest_morning_quiet"}),
    ]

    for name, parent, days_ago, expected in cases:
        day = local_day(parent, days_ago)
        out = tmp_path / f"{name}-{days_ago}"
        written = render_day(conn, whitakers.family_id, name, day, out)

        assert len(written) == len(expected), f"{name} {days_ago}d: {written}"
        for kind, template_id in expected.items():
            path = out / f"{day}-{name.lower()}-{kind}.html"
            assert path in written
            # Unescaped, because the wrapper escapes the apostrophe in
            # "Mom's" and the point is the WORDS, not their encoding.
            page = unescape(path.read_text(encoding="utf-8"))
            assert template_id in page, f"{path.name} did not name {template_id}"
            # The rendered body is the registry's words, not a paraphrase.
            body = render(
                template_id,
                dict.fromkeys(
                    template(template_id).variables,
                    parent_relationship(conn, parent),
                ),
            )
            assert body.split(".")[0] in page


def test_the_renderer_never_writes_a_withheld_evening(conn, whitakers, tmp_path):
    """A file on disk is a message the family received.

    The evening of a follow-on day is recorded as skipped, and rendering it
    would put an email in the founder's screenshot folder that nobody was ever
    sent - the quiet fiction this demo exists to avoid.
    """
    from scripts.render_digest import render_day

    seed(conn, whitakers.family_id, days=30, seed_value=42)
    dad = parent_by(conn, whitakers.family_id, "Dad")
    day = local_day(dad, UNREACHABLE_DAYS_AGO)

    assert ledger(conn, dad["id"], day)["digest_evening"][1] == "skipped"
    written = render_day(conn, whitakers.family_id, "Bill", day, tmp_path)
    assert [p.name for p in written] == [f"{day}-bill-digest_morning.html"]


def test_the_renderer_sends_nothing_and_cannot(conn):
    """No transport, no key, no address: it reads tables and writes files."""
    source = (
        Path(__file__).resolve().parent.parent / "scripts" / "render_digest.py"
    ).read_text()
    for forbidden in ("httpx", "requests", "resend", "twilio", "smtp", "ResendTransport"):
        assert forbidden not in source.lower(), forbidden
