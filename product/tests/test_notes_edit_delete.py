"""Spec 018 §6 — authorship, edit and delete at the schema.

The trigger records who wrote a row from the JWT and ignores what the client
says; two functions are the only paths to rewrite or remove one, and what
matters is what they refuse: a non-author edit, an admin edit of someone
else's words, a non-author non-admin delete, anything on a Kettle line, and
a legacy row by anyone but an admin.
"""

from __future__ import annotations

import psycopg
import pytest

from kettle.provisioning import provision_family
from testsupport import BASE_URL, add_member, as_user

ADMIN = "11111111-1111-1111-1111-111111111111"
AUTHOR = "22222222-2222-2222-2222-222222222222"
OTHER = "33333333-3333-3333-3333-333333333333"


@pytest.fixture
def circle(conn):
    family = provision_family(conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL)
    add_member(conn, family.family_id, ADMIN, role="admin")
    add_member(conn, family.family_id, AUTHOR, role="member")
    add_member(conn, family.family_id, OTHER, role="member")
    return family


def _member_id(conn, family_id, auth_user_id):
    return conn.execute(
        "select id from members where family_id = %s and auth_user_id = %s",
        (family_id, auth_user_id),
    ).fetchone()["id"]


def _note(authed, family_id, body="Dr. Reed, Thursday 2pm", **cols) -> int:
    fields = {"family_id": family_id, "author_label": "Priya", "body": body, **cols}
    columns = ", ".join(fields)
    marks = ", ".join(["%s"] * len(fields))
    return authed.execute(
        f"insert into journal_entries ({columns}) values ({marks}) returning id",  # noqa: S608
        tuple(fields.values()),
    ).fetchone()["id"]


def _row(conn, entry_id):
    return conn.execute(
        "select body, edited_utc, author_member_id from journal_entries where id = %s",
        (entry_id,),
    ).fetchone()


def _edit(authed, entry_id, body):
    authed.execute("select public.app_edit_entry(%s, %s)", (entry_id, body))


def _delete(authed, entry_id):
    authed.execute("select public.app_delete_entry(%s)", (entry_id,))


# --- the trigger ------------------------------------------------------------------


def test_the_author_is_recorded_from_the_jwt_and_a_client_value_is_ignored(circle, authed, conn):
    as_user(authed, AUTHOR)
    mine = _member_id(conn, circle.family_id, AUTHOR)
    admin = _member_id(conn, circle.family_id, ADMIN)
    plain = _note(authed, circle.family_id)
    forged = _note(
        authed, circle.family_id, author_member_id=admin, edited_utc="2026-01-01T00:00:00Z"
    )
    assert _row(conn, plain)["author_member_id"] == mine
    assert _row(conn, forged)["author_member_id"] == mine
    assert _row(conn, forged)["edited_utc"] is None
    # A reply carries its own author, the note's tag (0026), and no date.
    reply = _note(authed, circle.family_id, body="I can drive", parent_entry_id=plain)
    assert _row(conn, reply)["author_member_id"] == mine


def test_a_service_write_has_no_author(circle, conn):
    line = conn.execute(
        "insert into journal_entries (family_id, author_label, body, kind) "
        "values (%s, 'Kettle', 'Amma is in Chennai now.', 'city_change') returning id",
        (circle.family_id,),
    ).fetchone()["id"]
    assert _row(conn, line)["author_member_id"] is None


# --- edit -------------------------------------------------------------------------


def test_the_author_edits_their_own_text_and_the_row_says_so(circle, authed, conn):
    as_user(authed, AUTHOR)
    note = _note(authed, circle.family_id)
    assert _row(conn, note)["edited_utc"] is None
    _edit(authed, note, "Dr. Reed, Thursday 3pm")
    row = _row(conn, note)
    assert row["body"] == "Dr. Reed, Thursday 3pm"
    assert row["edited_utc"] is not None


def test_nobody_else_edits_not_even_an_admin(circle, authed, conn):
    as_user(authed, AUTHOR)
    note = _note(authed, circle.family_id)
    for who in (OTHER, ADMIN):
        as_user(authed, who)
        with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_author"):
            _edit(authed, note, "rewritten")
    assert _row(conn, note)["body"] == "Dr. Reed, Thursday 2pm"


def test_an_empty_or_oversized_edit_is_refused(circle, authed):
    as_user(authed, AUTHOR)
    note = _note(authed, circle.family_id)
    with pytest.raises(psycopg.errors.CheckViolation, match="body_empty"):
        _edit(authed, note, "   ")
    with pytest.raises(psycopg.errors.CheckViolation, match="body_too_long"):
        _edit(authed, note, "x" * 2001)


# --- delete -----------------------------------------------------------------------


def test_the_author_deletes_their_own_and_a_note_takes_its_replies(circle, authed, conn):
    as_user(authed, AUTHOR)
    note = _note(authed, circle.family_id)
    as_user(authed, OTHER)
    _note(authed, circle.family_id, body="I can drive", parent_entry_id=note)
    as_user(authed, AUTHOR)
    _delete(authed, note)
    assert conn.execute("select count(*) as n from journal_entries").fetchone()["n"] == 0


def test_a_member_cannot_delete_another_members_entry_but_an_admin_can(circle, authed, conn):
    as_user(authed, AUTHOR)
    note = _note(authed, circle.family_id)
    as_user(authed, OTHER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_allowed"):
        _delete(authed, note)
    as_user(authed, ADMIN)
    _delete(authed, note)
    assert conn.execute("select count(*) as n from journal_entries").fetchone()["n"] == 0


def test_kettle_lines_are_untouchable_by_anyone(circle, authed, conn):
    line = conn.execute(
        "insert into journal_entries (family_id, author_label, body, kind) "
        "values (%s, 'Kettle', 'Amma is in Chennai now.', 'city_change') returning id",
        (circle.family_id,),
    ).fetchone()["id"]
    as_user(authed, ADMIN)
    with pytest.raises(psycopg.errors.CheckViolation, match="kettle_line"):
        _edit(authed, line, "rewritten")
    with pytest.raises(psycopg.errors.CheckViolation, match="kettle_line"):
        _delete(authed, line)


def test_legacy_rows_are_admin_only(circle, authed, conn):
    """A row written before 0028 has no author: only an admin may edit or
    delete it — it is nobody's to rewrite, and someone must be able to."""
    legacy = conn.execute(
        "insert into journal_entries (family_id, author_label, body) "
        "values (%s, 'Priya', 'from before') returning id",
        (circle.family_id,),
    ).fetchone()["id"]
    assert _row(conn, legacy)["author_member_id"] is None
    as_user(authed, AUTHOR)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_author"):
        _edit(authed, legacy, "mine now")
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_allowed"):
        _delete(authed, legacy)
    as_user(authed, ADMIN)
    _edit(authed, legacy, "corrected by an admin")
    assert _row(conn, legacy)["body"] == "corrected by an admin"
    _delete(authed, legacy)
    assert conn.execute("select count(*) as n from journal_entries").fetchone()["n"] == 0


def test_a_stranger_reaches_nothing(circle, authed, conn):
    as_user(authed, AUTHOR)
    note = _note(authed, circle.family_id)
    other = provision_family(conn, "Iyer", "Asia/Kolkata", [("Patti", None)], base_url=BASE_URL)
    add_member(conn, other.family_id, "44444444-4444-4444-4444-444444444444", role="admin")
    as_user(authed, "44444444-4444-4444-4444-444444444444")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _edit(authed, note, "rewritten")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _delete(authed, note)
    assert _row(conn, note)["body"] == "Dr. Reed, Thursday 2pm"


def test_no_client_update_or_delete_and_anon_holds_no_execute(circle, authed, conn):
    as_user(authed, ADMIN)
    for statement in ("update journal_entries set body = 'x'", "delete from journal_entries"):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            authed.execute(statement)
    for fn in ("app_edit_entry", "app_delete_entry"):
        row = conn.execute(
            "select has_function_privilege('anon', p.oid, 'execute') as anon, "
            "has_function_privilege('authenticated', p.oid, 'execute') as authed "
            "from pg_proc p where p.proname = %s",
            (fn,),
        ).fetchone()
        assert (row["anon"], row["authed"]) == (False, True), fn
