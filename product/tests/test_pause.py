"""Spec 017 §7 — pause Kettle for one parent.

The engine's side: a paused parent produces one morning note and nothing
else across a whole day of passes while the neighbour runs the ladder; the
resume day fires nothing that fell due while paused; a week's pause ends by
itself. The functions' side: member refused, admin allowed, resume ends the
pause now and the engine clears the fields once that day is over.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import psycopg
import pytest

from kettle import db
from kettle.outbound import LogTransport, run_outbound
from kettle.outbound_templates import TEMPLATES, render
from kettle.provisioning import provision_family
from testsupport import BASE_URL, add_child_email, add_member, as_user, set_parent_whatsapp

IST = ZoneInfo("Asia/Kolkata")
ADMIN = "11111111-1111-1111-1111-111111111111"
MEMBER = "22222222-2222-2222-2222-222222222222"
INFINITY = datetime.max.replace(tzinfo=IST)


def at(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 8, day, hour, minute, tzinfo=IST)


@pytest.fixture
def two_parents(conn):
    """Amma and Appa in one family, a listening circle, WhatsApp on both."""
    family = provision_family(
        conn,
        "Sharma",
        "Asia/Kolkata",
        [("Amma", None, "Mom"), ("Appa", None, "Dad")],
        base_url=BASE_URL,
    )
    add_child_email(conn, family.family_id)
    for parent, number in zip(family.parents, ("+919845550001", "+919845550002"), strict=True):
        set_parent_whatsapp(conn, parent.parent_id, number)
    add_member(conn, family.family_id, ADMIN, role="admin")
    add_member(conn, family.family_id, MEMBER, role="member")
    return family


def _pause(conn, parent_id, until, since=None) -> None:
    conn.execute(
        "update parents set paused_until = %s, paused_since = %s where id = %s",
        (until, since or until - timedelta(days=1), parent_id),
    )


def _rows(conn, parent_id) -> list[tuple[str, str, str]]:
    rows = conn.execute(
        "select kind, template_id, status from sent_messages where parent_id = %s order by id",
        (parent_id,),
    ).fetchall()
    return [(r["kind"], r["template_id"], r["status"]) for r in rows]


def _alerts(conn, parent_id) -> list[str]:
    return [
        r["detail"]
        for r in conn.execute(
            "select detail from ops_alerts where parent_id = %s order by id", (parent_id,)
        ).fetchall()
    ]


def _pause_state(conn, parent_id):
    """paused_until read the engine's way (clamped: psycopg cannot load
    'infinity'), plus whether the stored value IS infinity."""
    return conn.execute(
        "select case when paused_until is null then null "
        "else least(paused_until, timestamptz '9999-12-31 00:00:00+00') end as paused_until, "
        "paused_since, paused_until = 'infinity' as open_ended from parents where id = %s",
        (parent_id,),
    ).fetchone()


def _full_day(conn, transport, day: int, notifier=None) -> None:
    for hour, minute in ((8, 30), (11, 0), (13, 0), (13, 30), (20, 30)):
        run_outbound(conn, transport, at(day, hour, minute), notifier=notifier)


# --- the engine -----------------------------------------------------------------


def test_a_paused_parent_gets_one_morning_note_and_nothing_else_all_day(
    conn, two_parents, notifier
):
    amma, appa = (p.parent_id for p in two_parents.parents)
    _pause(conn, amma, INFINITY, since=at(20, 9))
    transport = LogTransport()
    _full_day(conn, transport, 21, notifier)

    # Amma: the loud line at the morning slot, then silence — no ask, no
    # follow-on, no evening, no skipped rows, no alerts about her.
    assert _rows(conn, amma) == [("digest_morning", "digest_morning_paused", "sent")]
    assert _alerts(conn, amma) == []
    assert ("digest_morning_paused", render("digest_morning_paused", {"name": "Amma"})) in (
        transport.sent
    )
    # Appa, quiet all day, runs the whole ladder beside her.
    assert [k for k, _, s in _rows(conn, appa) if s == "sent"] == [
        "digest_morning",
        "ask",
        "follow_on",
    ]
    assert ("digest_evening", "digest_evening_normal", "skipped") in _rows(conn, appa)


def test_the_pause_day_lets_what_went_out_stand_and_sends_nothing_more(conn, two_parents):
    amma = two_parents.parents[0].parent_id
    transport = LogTransport()
    run_outbound(conn, transport, at(21, 8, 30))
    run_outbound(conn, transport, at(21, 11, 0))
    assert [k for k, _, _ in _rows(conn, amma)] == ["digest_morning", "ask"]
    # Paused at noon: the ask stands, the follow-on and the evening do not come.
    _pause(conn, amma, INFINITY, since=at(21, 12))
    run_outbound(conn, transport, at(21, 13, 0))
    run_outbound(conn, transport, at(21, 20, 30))
    assert [k for k, _, _ in _rows(conn, amma)] == ["digest_morning", "ask"]


def test_the_resume_day_fires_nothing_that_fell_due_while_paused(conn, two_parents):
    """Resumed at 14:00: the 08:30 note and the 11:00 ask are not sent late,
    the evening reads that day's pings only."""
    amma = two_parents.parents[0].parent_id
    _pause(conn, amma, at(21, 14, 0), since=at(19, 9))
    transport = LogTransport()
    run_outbound(conn, transport, at(21, 8, 30))
    assert _rows(conn, amma) == [("digest_morning", "digest_morning_paused", "sent")]
    for hour, minute in ((11, 0), (14, 30), (16, 0)):
        run_outbound(conn, transport, at(21, hour, minute))
    assert [k for k, _, _ in _rows(conn, amma)] == ["digest_morning"]  # no ask, no follow-on
    db.insert_ping(conn, amma, "whatsapp", at(21, 15, 0), None)
    run_outbound(conn, transport, at(21, 20, 30))
    # The morning was quiet (Kettle was not watching, and nothing pinged),
    # routine resumed after lunch: the engine's own word for that day.
    assert _rows(conn, amma)[-1] == ("digest_evening", "digest_evening_recovered", "sent")
    # The fields survive the resume day…
    assert _pause_state(conn, amma)["paused_since"] is not None
    # …and the first pass of the next day clears them and runs an ordinary morning.
    db.insert_ping(conn, amma, "whatsapp", at(22, 7, 0), None)
    run_outbound(conn, transport, at(22, 8, 30))
    assert _pause_state(conn, amma) == {
        "paused_until": None,
        "paused_since": None,
        "open_ended": None,
    }
    assert _rows(conn, amma)[-1] == ("digest_morning", "digest_morning_normal", "sent")


def test_a_week_pause_says_the_paused_line_once_and_ends_by_itself(conn, two_parents):
    """DECISIONS 277: seven days of full-day passes, ONE paused send — the
    first morning — then silence, then an ordinary morning after the pause."""
    amma = two_parents.parents[0].parent_id
    _pause(conn, amma, at(28, 7, 0), since=at(21, 7, 0))
    transport = LogTransport()
    for day in range(21, 28):
        _full_day(conn, transport, day)
    # One paused send: one ledger row, delivered once to each listening member.
    paused_sends = [t for t, _ in transport.sent if t == "digest_morning_paused"]
    assert len(paused_sends) == len(db.outbound_contacts(conn, two_parents.family_id)) == 3
    assert _rows(conn, amma) == [("digest_morning", "digest_morning_paused", "sent")]
    # Day 28: the pause ended at 07:00, before the slot — a normal morning.
    db.insert_ping(conn, amma, "whatsapp", at(28, 7, 30), None)
    run_outbound(conn, transport, at(28, 8, 30))
    assert _rows(conn, amma)[-1] == ("digest_morning", "digest_morning_normal", "sent")


def test_a_paused_line_missed_on_the_pause_day_goes_out_the_next_morning(conn, two_parents):
    """Paused at noon, after the day's digest went out: the first morning of
    the pause is tomorrow, and that is when the line goes, once."""
    amma = two_parents.parents[0].parent_id
    transport = LogTransport()
    db.insert_ping(conn, amma, "whatsapp", at(21, 7, 0), None)
    run_outbound(conn, transport, at(21, 8, 30))
    _pause(conn, amma, INFINITY, since=at(21, 12, 0))
    _full_day(conn, transport, 21)
    _full_day(conn, transport, 22)
    _full_day(conn, transport, 23)
    assert _rows(conn, amma) == [
        ("digest_morning", "digest_morning_normal", "sent"),
        ("digest_morning", "digest_morning_paused", "sent"),
    ]


def test_a_week_pause_ends_by_itself(conn, two_parents):
    amma = two_parents.parents[0].parent_id
    _pause(conn, amma, at(21, 8, 0), since=at(14, 8))
    transport = LogTransport()
    db.insert_ping(conn, amma, "whatsapp", at(21, 7, 30), None)
    run_outbound(conn, transport, at(21, 8, 30))
    # Ended at 08:00, the 08:30 slot is after it: an ordinary morning note.
    assert _rows(conn, amma) == [("digest_morning", "digest_morning_normal", "sent")]


def test_nobody_listening_raises_nothing_for_a_paused_parent(conn, notifier):
    family = provision_family(
        conn, "Iyer", "Asia/Kolkata", [("Patti", None, "Mom")], base_url=BASE_URL
    )
    _pause(conn, family.parents[0].parent_id, INFINITY)

    class NeedsAddress(LogTransport):
        name = "needs-address"
        requires_address = True

    run_outbound(conn, NeedsAddress(), at(21, 8, 30), notifier=notifier)
    assert conn.execute("select count(*) as n from ops_alerts").fetchone()["n"] == 0
    assert conn.execute("select count(*) as n from sent_messages").fetchone()["n"] == 0


def test_the_paused_line_is_a_registered_template_with_the_ruled_words():
    assert TEMPLATES["digest_morning_paused"].kind == "digest_morning"
    assert render("digest_morning_paused", {"name": "Amma"}) == (
        "Kettle is paused for Amma. Nothing to report."
    )


# --- the functions ---------------------------------------------------------------


def test_a_member_cannot_pause_or_resume(two_parents, authed, conn):
    amma = two_parents.parents[0].parent_id
    as_user(authed, MEMBER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_admin"):
        authed.execute("select public.app_pause_parent(%s, now() + interval '7 days')", (amma,))
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_admin"):
        authed.execute("select public.app_resume_parent(%s)", (amma,))
    assert _pause_state(conn, amma)["paused_until"] is None


def test_an_admin_pauses_for_a_week_or_open_ended_and_resumes(two_parents, authed, conn):
    amma = two_parents.parents[0].parent_id
    as_user(authed, ADMIN)
    authed.execute("select public.app_pause_parent(%s, now() + interval '7 days')", (amma,))
    state = _pause_state(conn, amma)
    assert state["paused_since"] is not None
    assert (
        timedelta(days=6, hours=23)
        < state["paused_until"] - state["paused_since"]
        <= timedelta(days=7)
    )
    since = state["paused_since"]

    # Extending while paused keeps the original start.
    authed.execute("select public.app_pause_parent(%s, 'infinity')", (amma,))
    state = _pause_state(conn, amma)
    assert state["open_ended"] is True
    assert state["paused_since"] == since

    # Resume ends the pause NOW: paused_until in the past, since kept for the
    # resume-day rule; the engine clears both after that day (tested above).
    authed.execute("select public.app_resume_parent(%s)", (amma,))
    state = _pause_state(conn, amma)
    assert state["paused_until"] <= datetime.now(tz=state["paused_until"].tzinfo)
    assert state["paused_since"] == since
    # Resuming a running parent changes nothing.
    authed.execute("select public.app_resume_parent(%s)", (amma,))
    assert _pause_state(conn, amma) == state


def test_a_pause_in_the_past_is_refused(two_parents, authed):
    amma = two_parents.parents[0].parent_id
    as_user(authed, ADMIN)
    with pytest.raises(psycopg.errors.CheckViolation, match="pause_in_the_past"):
        authed.execute("select public.app_pause_parent(%s, now() - interval '1 hour')", (amma,))


def test_a_stranger_cannot_pause_someone_elses_parent(two_parents, authed, conn):
    other = provision_family(conn, "Iyer", "Asia/Kolkata", [("Patti", None)], base_url=BASE_URL)
    add_member(conn, other.family_id, "33333333-3333-3333-3333-333333333333", role="admin")
    as_user(authed, "33333333-3333-3333-3333-333333333333")
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_admin"):
        authed.execute(
            "select public.app_pause_parent(%s, 'infinity')", (two_parents.parents[0].parent_id,)
        )


def test_the_pause_columns_are_not_client_writable(two_parents, authed):
    as_user(authed, ADMIN)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute("update parents set paused_until = 'infinity'")


def test_anon_cannot_execute_the_pause_functions(conn):
    for fn in ("app_pause_parent", "app_resume_parent"):
        row = conn.execute(
            "select has_function_privilege('anon', p.oid, 'execute') as anon, "
            "has_function_privilege('authenticated', p.oid, 'execute') as authed "
            "from pg_proc p where p.proname = %s",
            (fn,),
        ).fetchone()
        assert (row["anon"], row["authed"]) == (False, True), fn
