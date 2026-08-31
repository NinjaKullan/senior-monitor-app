"""Spec 012 §3/§5 — Kettle's gentle lines in the family journal.

Two properties carry the weight, and both are the product's own shape:

* **Absence speaks.** clean_month writes NOTHING for a month that was not
  clean — no entry, no qualifier. The suppression is planted here on the
  spec's own order, not assumed from a green insert path.
* **Once means once, through restarts.** Idempotency lives in migration
  0020's partial unique indexes, not loop memory: reruns, crashes, and
  racing schedulers all land one row. Every test runs its writer twice.
"""

from __future__ import annotations

from datetime import date, timedelta

import psycopg
from test_outbound import (
    CountingTransport,
    at,
    family,  # noqa: F401 - fixture
    ledger,
    ping,
    run_twice,
)
from test_outbound_copy import assert_outbound_copy_law

from kettle import db, journal
from kettle.outbound import record_parent_reply, run_outbound

WHATSAPP = "+919845550001"


def auto_notes(conn: psycopg.Connection) -> list[tuple[str, str, str]]:
    """Kettle-authored journal rows as (kind, body, event_date), oldest first."""
    rows = conn.execute(
        "select kind, body, event_date from journal_entries "
        "where author_label = 'Kettle' order by id"
    ).fetchall()
    return [(r["kind"], r["body"], str(r["event_date"])) for r in rows]


def sent(conn, family_id, parent_id, local_date: str, kind: str, template: str):
    """One SENT ledger row, planted directly — months of history in a line."""
    db.record_sent_message(
        conn, family_id, parent_id, local_date, kind, template,
        "log", at(9, 0), status="sent",
    )


# --- the strings themselves ---------------------------------------------------


def test_the_bodies_are_the_ruled_strings_and_pass_the_copy_law():
    """DECISIONS 200, character for character — and through the same scanner
    the outbound registry passes, with a real name filled in (the journal is
    in-app, where display_name is the law: DECISIONS 183, not 149)."""
    assert journal.STARTED_NOTE == "Kettle's first morning with {parent}."
    assert journal.FIRST_REPLY_NOTE == "Heard from {parent} with a 👍."
    assert journal.CLEAN_MONTH_NOTE == "A normal {month}, start to finish."
    assert journal.AUTHOR == "Kettle"
    for template in (journal.STARTED_NOTE, journal.FIRST_REPLY_NOTE):
        assert_outbound_copy_law(template.format(parent="Amma"))
    assert_outbound_copy_law(journal.CLEAN_MONTH_NOTE.format(month="August"))


# --- started ------------------------------------------------------------------


def test_the_first_daily_note_earns_one_line_and_only_one(
    conn, family, notifier  # noqa: F811
):
    """§3.2: written when the first daily note goes out — and never again,
    though the hook fires on every sent digest."""
    parent_id = family.parents[0].parent_id
    transport = CountingTransport()
    ping(conn, parent_id, "whatsapp", at(6, 30))

    run_twice(conn, transport, at(8, 30), notifier=notifier)
    assert auto_notes(conn) == [
        ("started", "Kettle's first morning with Amma.", "2026-08-21")
    ]

    # The evening digest, and the whole next day: still one line.
    run_twice(conn, transport, at(20, 30), notifier=notifier)
    ping(conn, parent_id, "whatsapp", at(6, 30) + timedelta(days=1))
    run_twice(conn, transport, at(8, 30) + timedelta(days=1), notifier=notifier)
    assert [n for n in auto_notes(conn) if n[0] == "started"] == [
        ("started", "Kettle's first morning with Amma.", "2026-08-21")
    ]


def test_a_parent_with_history_earns_no_first_morning_line(
    conn, family, notifier  # noqa: F811
):
    """DECISIONS 204, the deploy-day case: this is what the once-ever key
    alone could not see. A parent Kettle has been writing to for months gets
    NO "first morning" line from the first engine pass after deploy — the
    line is a claim about history, so it is checked against history."""
    parent_id = family.parents[0].parent_id
    # Three weeks of notes already sent, before the memory feature existed.
    for day in range(1, 21):
        sent(
            conn, family.family_id, parent_id, f"2026-08-{day:02d}",
            "digest_morning", "digest_morning_normal",
        )
    transport = CountingTransport()
    ping(conn, parent_id, "whatsapp", at(6, 30))

    run_twice(conn, transport, at(8, 30), notifier=notifier)
    # The digest went out as always…
    assert ("digest_morning", "digest_morning_normal") in ledger(conn)
    # …and the memory stayed honest.
    assert [n for n in auto_notes(conn) if n[0] == "started"] == []

    # Still nothing tomorrow, or ever: history does not expire.
    ping(conn, parent_id, "whatsapp", at(6, 30) + timedelta(days=1))
    run_twice(conn, transport, at(8, 30) + timedelta(days=1), notifier=notifier)
    assert [n for n in auto_notes(conn) if n[0] == "started"] == []


def test_a_genuinely_new_parent_still_earns_exactly_one(
    conn, family, notifier  # noqa: F811
):
    """The other half: no prior ledger rows means the line is TRUE, and it
    lands once — including when the very slot that earned it is re-decided
    after a failure, which the (local_date, kind) exclusion covers."""
    parent_id = family.parents[0].parent_id
    transport = CountingTransport()
    ping(conn, parent_id, "whatsapp", at(6, 30))

    run_twice(conn, transport, at(8, 30), notifier=notifier)
    assert [n for n in auto_notes(conn) if n[0] == "started"] == [
        ("started", "Kettle's first morning with Amma.", "2026-08-21")
    ]

    # A retry of that same slot still reads as first (it is excluded from its
    # own history check) and the key keeps it to one row.
    assert not journal.note_started(
        conn, family.family_id, parent_id, "Amma", "2026-08-21", "digest_morning"
    )
    assert len([n for n in auto_notes(conn) if n[0] == "started"]) == 1


# --- first_reply --------------------------------------------------------------


def test_the_first_reply_earns_one_line_across_days(
    conn, family, notifier  # noqa: F811
):
    """§3.3 with the gate armed (the Phase 3 posture): once ever, content
    unread — a second reply on another day adds nothing."""
    transport = CountingTransport()

    run_twice(conn, transport, at(11, 0), notifier=notifier)  # the ask
    assert record_parent_reply(conn, WHATSAPP, at(11, 30), note_first_reply=True) is True
    assert [n for n in auto_notes(conn) if n[0] == "first_reply"] == [
        ("first_reply", "Heard from Amma with a 👍.", "2026-08-21")
    ]

    # Tomorrow's quiet morning asks again; the reply matches again; one line.
    run_outbound(conn, transport, at(11, 0) + timedelta(days=1), notifier=notifier)
    assert record_parent_reply(
        conn, WHATSAPP, at(11, 30) + timedelta(days=1), note_first_reply=True
    ) is True
    assert len([n for n in auto_notes(conn) if n[0] == "first_reply"]) == 1


def test_the_gate_holds_a_sandbox_reply_out_of_the_memory(
    conn, family, notifier  # noqa: F811
):
    """DECISIONS 203: the line belongs to the real-number era. With the gate
    at its DEFAULT — off — a matched reply cancels the ladder exactly as
    before and writes NOTHING; arming it later still means the NEXT reply is
    the first countable one, once, via the unchanged schema key."""
    transport = CountingTransport()

    run_twice(conn, transport, at(11, 0), notifier=notifier)
    # The default posture: no keyword, gate off — the ladder still stands
    # down, the memory stays silent.
    assert record_parent_reply(conn, WHATSAPP, at(11, 30)) is True
    assert auto_notes(conn) == []

    # The flip: the gate arms, and the next matched reply earns the line.
    run_outbound(conn, transport, at(11, 0) + timedelta(days=1), notifier=notifier)
    assert record_parent_reply(
        conn, WHATSAPP, at(11, 30) + timedelta(days=1), note_first_reply=True
    ) is True
    assert [n for n in auto_notes(conn) if n[0] == "first_reply"] == [
        ("first_reply", "Heard from Amma with a 👍.", "2026-08-22")
    ]


def test_the_gate_defaults_off_in_config_and_rides_the_reply_route():
    """The wiring, both ends: MEMORY_FIRST_REPLY resolves False when unset,
    True when set — and the webhook actually passes it, since a gate the
    route ignores is decoration."""
    from pathlib import Path

    from kettle.config import settings_from_env

    base = {"DATABASE_URL": "postgresql://x/y"}
    assert settings_from_env(base).memory_first_reply is False
    assert settings_from_env({**base, "MEMORY_FIRST_REPLY": "1"}).memory_first_reply is True
    # Anchored to THIS file, not to the working directory. `Path("kettle/
    # main.py")` resolved only when pytest happened to be invoked from
    # product/, and CI invokes it from the repo root — so the source pin that
    # is the whole point of this assertion was raising FileNotFoundError
    # instead of checking anything.
    source = (Path(__file__).resolve().parent.parent / "kettle" / "main.py").read_text()
    assert "note_first_reply=cfg.memory_first_reply" in source


# --- clean_month --------------------------------------------------------------


def month_of_digests(conn, family, year: int, month: int, days: int = 31):  # noqa: F811
    """A full month of sent morning digests, first day through `days`."""
    import calendar

    last = min(days, calendar.monthrange(year, month)[1])
    for day in range(1, last + 1):
        sent(
            conn, family.family_id, family.parents[0].parent_id,
            f"{year:04d}-{month:02d}-{day:02d}", "digest_morning",
            "digest_morning_normal",
        )


def test_a_clean_month_earns_its_line_once(conn, family):  # noqa: F811
    """§3.4 the affirmative half: July watched start to finish, no
    escalation — one line, on the 1st, idempotent under rerun and restart."""
    parent_id = family.parents[0].parent_id
    month_of_digests(conn, family, 2026, 6)  # listening since June
    month_of_digests(conn, family, 2026, 7)

    assert journal.note_clean_month(conn, family.family_id, parent_id, date(2026, 8, 1))
    # The rerun, and the scheduler that slept through the 1st.
    assert not journal.note_clean_month(conn, family.family_id, parent_id, date(2026, 8, 1))
    assert not journal.note_clean_month(conn, family.family_id, parent_id, date(2026, 8, 3))
    assert auto_notes(conn) == [
        ("clean_month", "A normal July, start to finish.", "2026-07-01")
    ]


def test_a_month_with_an_escalation_writes_nothing_at_all(conn, family):  # noqa: F811
    """THE PLANT THE SPEC ORDERS: a month that wasn't clean gets nothing — no
    entry, no qualifier, not a different body. The suppression is the
    feature."""
    parent_id = family.parents[0].parent_id
    month_of_digests(conn, family, 2026, 6)
    month_of_digests(conn, family, 2026, 7)
    # One silent day reached the family in July.
    sent(conn, family.family_id, parent_id, "2026-07-14", "follow_on", "follow_on_family")

    assert not journal.note_clean_month(conn, family.family_id, parent_id, date(2026, 8, 1))
    assert auto_notes(conn) == []

    # And June — clean, fully watched — still earns ITS line, so the
    # suppression is per-month, not a latch.
    assert journal.note_clean_month(conn, family.family_id, parent_id, date(2026, 7, 1))
    assert auto_notes(conn) == [
        ("clean_month", "A normal June, start to finish.", "2026-06-01")
    ]


def test_a_month_kettle_did_not_watch_whole_writes_nothing(conn, family):  # noqa: F811
    """The two honesty guards (flagged in DECISIONS): "start to finish" is a
    claim about coverage, so a month with no digests, or one where the
    parent's first-ever digest lands mid-month, earns no line."""
    parent_id = family.parents[0].parent_id

    # Nothing sent at all: nothing written.
    assert not journal.note_clean_month(conn, family.family_id, parent_id, date(2026, 8, 1))

    # Kettle's first morning was July 15th: July is not "start to finish".
    for day in range(15, 32):
        sent(conn, family.family_id, parent_id, f"2026-07-{day:02d}",
             "digest_morning", "digest_morning_normal")
    assert not journal.note_clean_month(conn, family.family_id, parent_id, date(2026, 8, 1))
    assert auto_notes(conn) == []

    # August, watched whole: the line resumes.
    month_of_digests(conn, family, 2026, 8)
    assert journal.note_clean_month(conn, family.family_id, parent_id, date(2026, 9, 1))
    assert auto_notes(conn) == [
        ("clean_month", "A normal August, start to finish.", "2026-08-01")
    ]


def test_the_engine_writes_the_month_line_on_its_own_pass(
    conn, family, notifier  # noqa: F811
):
    """The hook: a routine engine pass after the month turns carries the
    line out without anyone calling the writer by hand."""
    parent_id = family.parents[0].parent_id
    month_of_digests(conn, family, 2026, 6)
    month_of_digests(conn, family, 2026, 7)
    transport = CountingTransport()
    ping(conn, parent_id, "whatsapp", at(6, 30))

    run_twice(conn, transport, at(8, 30), notifier=notifier)  # Aug 21 pass
    kinds = [n[0] for n in auto_notes(conn)]
    assert "clean_month" in kinds
    assert ("clean_month", "A normal July, start to finish.", "2026-07-01") in auto_notes(conn)


# --- the posture --------------------------------------------------------------


def test_the_writer_never_updates_or_deletes():
    """Insert-only is the journal's law, and the writer keeps it: the module
    contains no UPDATE and no DELETE against the table."""
    from pathlib import Path

    source = Path(journal.__file__).read_text().lower()
    for verb in ("update journal", "delete from journal"):
        assert verb not in source
