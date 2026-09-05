"""Spec 016 §6 — replies on a note, at the schema.

The trigger is what keeps a thread one level deep and keeps Kettle's own
lines out of conversations; what matters is what it refuses, and that a
reply inherits the note's tag rather than carrying one of its own.
"""

from __future__ import annotations

import psycopg
import pytest

from kettle.provisioning import provision_family
from testsupport import BASE_URL, add_member, as_user

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


@pytest.fixture
def two_families(conn):
    a = provision_family(conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL)
    b = provision_family(conn, "Iyer", "America/Chicago", [("Patti", None)], base_url=BASE_URL)
    add_member(conn, a.family_id, USER_A)
    add_member(conn, b.family_id, USER_B)
    return {"a": a, "b": b}


def _note(authed, family_id, parent_id=None, kind="note", event_date=None) -> int:
    return authed.execute(
        "insert into journal_entries (family_id, parent_id, author_label, body, event_date, kind) "
        "values (%s, %s, 'Hema', 'Dr. Reed, Thursday 2pm', %s, %s) returning id",
        (family_id, parent_id, event_date, kind),
    ).fetchone()["id"]


def _reply(authed, family_id, parent_entry_id, **over) -> int:
    fields = {
        "family_id": family_id,
        "parent_id": None,
        "author_label": "Priya",
        "body": "Took her, all fine",
        "event_date": None,
        "kind": "note",
        "parent_entry_id": parent_entry_id,
    }
    fields.update(over)
    columns = ", ".join(fields)
    marks = ", ".join(["%s"] * len(fields))
    return authed.execute(
        f"insert into journal_entries ({columns}) values ({marks}) returning id",  # noqa: S608
        tuple(fields.values()),
    ).fetchone()["id"]


def _row(conn, entry_id):
    return conn.execute("select * from journal_entries where id = %s", (entry_id,)).fetchone()


def test_a_reply_inherits_the_notes_tag_and_carries_no_date(two_families, authed, conn):
    a = two_families["a"]
    as_user(authed, USER_A)
    note = _note(authed, a.family_id, a.parents[0].parent_id, event_date="2026-09-10")
    reply = _reply(authed, a.family_id, note)
    row = _row(conn, reply)
    assert row["parent_entry_id"] == note
    assert row["parent_id"] == a.parents[0].parent_id  # inherited, not supplied
    assert row["event_date"] is None and row["kind"] == "note"
    # And a family-wide note's reply stays family-wide.
    family_note = _note(authed, a.family_id)
    assert _row(conn, _reply(authed, a.family_id, family_note))["parent_id"] is None


def test_a_reply_to_a_reply_is_refused(two_families, authed):
    a = two_families["a"]
    as_user(authed, USER_A)
    note = _note(authed, a.family_id)
    reply = _reply(authed, a.family_id, note)
    with pytest.raises(psycopg.errors.CheckViolation, match="reply_to_reply"):
        _reply(authed, a.family_id, reply)


def test_a_reply_to_a_kettle_line_is_refused(two_families, authed, conn):
    a = two_families["a"]
    line = conn.execute(
        "insert into journal_entries (family_id, parent_id, author_label, body, kind) "
        "values (%s, %s, 'Kettle', 'Amma is in Chennai now.', 'city_change') returning id",
        (a.family_id, a.parents[0].parent_id),
    ).fetchone()["id"]
    as_user(authed, USER_A)
    with pytest.raises(psycopg.errors.CheckViolation, match="reply_to_kettle_line"):
        _reply(authed, a.family_id, line)


def test_a_reply_with_an_event_date_or_a_kettle_kind_is_refused(two_families, authed):
    a = two_families["a"]
    as_user(authed, USER_A)
    note = _note(authed, a.family_id)
    with pytest.raises(psycopg.errors.CheckViolation, match="reply_with_date"):
        _reply(authed, a.family_id, note, event_date="2026-10-02")
    with pytest.raises(psycopg.errors.CheckViolation, match="reply_must_be_note"):
        _reply(authed, a.family_id, note, kind="started")


def test_a_reply_across_families_is_refused_by_name(two_families, authed):
    a, b = two_families["a"], two_families["b"]
    as_user(authed, USER_B)
    theirs = _note(authed, b.family_id)
    as_user(authed, USER_A)
    # Own family on the row, the neighbour's note as the parent: the trigger
    # sees the parent (SECURITY DEFINER) and says exactly what is wrong.
    with pytest.raises(psycopg.errors.CheckViolation, match="reply_across_families"):
        _reply(authed, a.family_id, theirs)
    # The other way round is 0017's WITH CHECK, unchanged.
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _reply(authed, b.family_id, theirs)


def test_a_reply_to_nothing_is_refused(two_families, authed):
    a = two_families["a"]
    as_user(authed, USER_A)
    with pytest.raises(psycopg.errors.CheckViolation, match="reply_parent_missing"):
        _reply(authed, a.family_id, 999_999)


def test_deleting_a_note_deletes_its_replies(two_families, authed, conn):
    a = two_families["a"]
    as_user(authed, USER_A)
    note = _note(authed, a.family_id)
    _reply(authed, a.family_id, note)
    _reply(authed, a.family_id, note)
    assert conn.execute("select count(*) as n from journal_entries").fetchone()["n"] == 3
    conn.execute("delete from journal_entries where id = %s", (note,))
    assert conn.execute("select count(*) as n from journal_entries").fetchone()["n"] == 0


def test_the_thread_reads_back_with_the_note(two_families, authed):
    """§4's MCP constraint: a thread is the note plus its replies from the
    same bounded read — the reply's family_id is the note's, so the family
    read carries both, and the inherited tag puts both in the parent read."""
    a = two_families["a"]
    as_user(authed, USER_A)
    note = _note(authed, a.family_id, a.parents[0].parent_id)
    _reply(authed, a.family_id, note)
    rows = authed.execute(
        "select id, parent_entry_id, parent_id from journal_entries where parent_id = %s "
        "order by created_utc desc, id desc limit 50",
        (a.parents[0].parent_id,),
    ).fetchall()
    assert [r["parent_entry_id"] for r in rows] == [note, None]
