"""Spec 015 §12 — the circle: the five functions, the RLS reads, the outbound
fan-out.

The functions are SECURITY DEFINER and the only write path to `members`, so
what matters is what they refuse: a stranger, a member reaching for an admin
action, a ninth seat, a second copy of an email, and — above all — the last
admin walking out of a circle that would then have none.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import psycopg
import pytest

from kettle import db
from kettle.outbound import DeliveryResult, LogTransport, run_outbound
from kettle.provisioning import provision_family
from testsupport import BASE_URL, add_member, as_user, invite_member

ADMIN = "11111111-1111-1111-1111-111111111111"
MEMBER = "22222222-2222-2222-2222-222222222222"
STRANGER = "33333333-3333-3333-3333-333333333333"
IST = ZoneInfo("Asia/Kolkata")


def _family(conn, name="Sharma"):
    return provision_family(conn, name, "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL)


@pytest.fixture
def circle(conn):
    """One circle: an admin and a member, both signed in."""
    family = _family(conn)
    add_member(conn, family.family_id, ADMIN, role="admin")
    add_member(conn, family.family_id, MEMBER, role="member")
    return family


def _members(conn, family_id) -> list[dict]:
    return conn.execute(
        "select display_name, role, email, mail, auth_user_id from members "
        "where family_id = %s order by created_utc, id",
        (family_id,),
    ).fetchall()


def _member_id(conn, family_id, auth_user_id):
    return conn.execute(
        "select id from members where family_id = %s and auth_user_id = %s",
        (family_id, auth_user_id),
    ).fetchone()["id"]


def _call(authed, sql, *params):
    return authed.execute(sql, params).fetchone()


# --- the migration ------------------------------------------------------------


def test_0025_renamed_the_roles_and_added_the_switch(conn):
    """owner → admin, child → member, mail on by default, and the constraint
    admits nothing else."""
    family = _family(conn)
    invite_member(conn, family.family_id, "a@example.test", role="admin")
    invite_member(conn, family.family_id, "b@example.test", role="member")
    rows = _members(conn, family.family_id)
    assert [r["role"] for r in rows] == ["admin", "member"]
    assert all(r["mail"] is True for r in rows)
    with pytest.raises(psycopg.errors.CheckViolation):
        invite_member(conn, family.family_id, "c@example.test", role="owner")


def test_provisioning_creates_an_admin_seat(conn):
    family = provision_family(
        conn,
        "Iyer",
        "Asia/Kolkata",
        [("Patti", None)],
        base_url=BASE_URL,
        owner_email="kid@example.test",
        owner_name="Kid",
    )
    [seat] = _members(conn, family.family_id)
    assert (seat["role"], seat["mail"], seat["auth_user_id"]) == ("admin", True, None)


# --- app_add_seat -------------------------------------------------------------


def test_an_admin_adds_a_seat_that_is_a_member_with_mail_on(circle, conn, authed):
    as_user(authed, ADMIN)
    new_id = _call(
        authed,
        "select public.app_add_seat(%s, %s, %s) as id",
        circle.family_id,
        "  Sister ",
        " Sister@Example.test ",
    )["id"]
    assert new_id is not None
    row = conn.execute("select * from members where id = %s", (new_id,)).fetchone()
    assert (row["role"], row["mail"], row["auth_user_id"]) == ("member", True, None)
    assert (row["display_name"], row["email"]) == ("Sister", "sister@example.test")


def test_a_member_cannot_add_a_seat(circle, authed):
    as_user(authed, MEMBER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_admin"):
        _call(authed, "select public.app_add_seat(%s, 'X', 'x@example.test')", circle.family_id)


def test_a_stranger_cannot_add_a_seat_to_a_circle_they_name(circle, conn, authed):
    """The family id is an argument; belonging to it is not."""
    other = _family(conn, "Iyer")
    add_member(conn, other.family_id, STRANGER, role="admin")
    as_user(authed, STRANGER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_admin"):
        _call(authed, "select public.app_add_seat(%s, 'X', 'x@example.test')", circle.family_id)
    assert len(_members(conn, circle.family_id)) == 2


def test_the_ninth_seat_is_refused(circle, authed):
    as_user(authed, ADMIN)
    for n in range(6):  # 2 existing + 6 = 8
        _call(
            authed,
            "select public.app_add_seat(%s, %s, %s)",
            circle.family_id,
            f"P{n}",
            f"p{n}@example.test",
        )
    with pytest.raises(psycopg.errors.CheckViolation, match="circle_full"):
        _call(
            authed, "select public.app_add_seat(%s, 'Nine', 'nine@example.test')", circle.family_id
        )


def test_a_duplicate_email_in_the_circle_is_refused(circle, authed):
    as_user(authed, ADMIN)
    _call(authed, "select public.app_add_seat(%s, 'A', 'dup@example.test')", circle.family_id)
    with pytest.raises(psycopg.errors.CheckViolation, match="duplicate_email"):
        _call(authed, "select public.app_add_seat(%s, 'B', 'DUP@example.test')", circle.family_id)


# --- roles and removal, and the last-admin guard ------------------------------


def test_an_admin_promotes_and_demotes(circle, conn, authed):
    as_user(authed, ADMIN)
    target = _member_id(conn, circle.family_id, MEMBER)
    _call(authed, "select public.app_set_role(%s, 'admin')", target)
    assert [r["role"] for r in _members(conn, circle.family_id)] == ["admin", "admin"]
    _call(authed, "select public.app_set_role(%s, 'member')", target)
    assert [r["role"] for r in _members(conn, circle.family_id)] == ["admin", "member"]
    with pytest.raises(psycopg.errors.CheckViolation, match="bad_role"):
        _call(authed, "select public.app_set_role(%s, 'owner')", target)


def test_a_member_cannot_change_roles_or_remove(circle, conn, authed):
    as_user(authed, MEMBER)
    admin_row = _member_id(conn, circle.family_id, ADMIN)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_admin"):
        _call(authed, "select public.app_set_role(%s, 'member')", admin_row)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_admin"):
        _call(authed, "select public.app_remove_seat(%s)", admin_row)
    assert len(_members(conn, circle.family_id)) == 2


def test_the_last_admin_is_stuck_until_they_promote_someone(circle, conn, authed):
    """§5: the guard on remove, demote and leave — all three ways out."""
    as_user(authed, ADMIN)
    me = _member_id(conn, circle.family_id, ADMIN)
    other = _member_id(conn, circle.family_id, MEMBER)
    with pytest.raises(psycopg.errors.CheckViolation, match="last_admin"):
        _call(authed, "select public.app_set_role(%s, 'member')", me)
    with pytest.raises(psycopg.errors.CheckViolation, match="last_admin"):
        _call(authed, "select public.app_remove_seat(%s)", me)
    with pytest.raises(psycopg.errors.CheckViolation, match="last_admin"):
        _call(authed, "select public.app_leave_circle(%s)", circle.family_id)
    assert [r["role"] for r in _members(conn, circle.family_id)] == ["admin", "member"]

    # Promote someone, and every door opens.
    _call(authed, "select public.app_set_role(%s, 'admin')", other)
    _call(authed, "select public.app_leave_circle(%s)", circle.family_id)
    rows = _members(conn, circle.family_id)
    assert [(r["role"], str(r["auth_user_id"])) for r in rows] == [("admin", MEMBER)]


def test_a_removed_person_sees_nothing(circle, conn, authed):
    as_user(authed, ADMIN)
    target = _member_id(conn, circle.family_id, MEMBER)
    _call(authed, "select public.app_remove_seat(%s)", target)
    as_user(authed, MEMBER)
    assert authed.execute("select id from families").fetchall() == []
    assert authed.execute("select id from parents").fetchall() == []
    assert authed.execute("select id from members").fetchall() == []


def test_a_member_may_leave(circle, conn, authed):
    as_user(authed, MEMBER)
    _call(authed, "select public.app_leave_circle(%s)", circle.family_id)
    assert [str(r["auth_user_id"]) for r in _members(conn, circle.family_id)] == [ADMIN]
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_member"):
        _call(authed, "select public.app_leave_circle(%s)", circle.family_id)


# --- the mail switch ----------------------------------------------------------


def test_the_mail_switch_is_own_row_only(circle, conn, authed):
    as_user(authed, MEMBER)
    _call(authed, "select public.app_set_mail(%s, false)", circle.family_id)
    rows = {str(r["auth_user_id"]): r["mail"] for r in _members(conn, circle.family_id)}
    assert rows == {ADMIN: True, MEMBER: False}
    # A non-member of the named circle changes nothing and is told so.
    as_user(authed, STRANGER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_member"):
        _call(authed, "select public.app_set_mail(%s, false)", circle.family_id)


def test_members_is_still_not_writable_directly(circle, authed):
    """§6: no direct insert/update/delete policy — the functions are the path."""
    as_user(authed, ADMIN)
    for statement in (
        "update members set role = 'admin'",
        "update members set mail = false",
        "delete from members",
        f"insert into members (family_id, role) values ('{circle.family_id}', 'member')",
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            authed.execute(statement)


def test_anon_cannot_execute_the_circle_functions(conn):
    """0004's doctrine: the bootstrap hands anon EXECUTE at creation; 0025
    takes it back, so the grant set is exactly {authenticated}."""
    for fn in (
        "app_add_seat",
        "app_remove_seat",
        "app_set_role",
        "app_set_mail",
        "app_leave_circle",
    ):
        row = conn.execute(
            "select has_function_privilege('anon', p.oid, 'execute') as anon, "
            "has_function_privilege('authenticated', p.oid, 'execute') as authed "
            "from pg_proc p where p.proname = %s",
            (fn,),
        ).fetchone()
        assert (row["anon"], row["authed"]) == (False, True), fn


# --- RLS over two circles -----------------------------------------------------


def test_a_two_circle_account_reads_both_and_a_one_circle_account_reads_one(conn, authed):
    a, b = _family(conn, "Sharma"), _family(conn, "Iyer")
    add_member(conn, a.family_id, ADMIN, role="admin")
    add_member(conn, b.family_id, ADMIN, role="member")
    add_member(conn, b.family_id, MEMBER, role="admin")
    as_user(authed, ADMIN)
    assert sorted(r["name"] for r in authed.execute("select name from families").fetchall()) == [
        "Iyer",
        "Sharma",
    ]
    assert len(authed.execute("select id from parents").fetchall()) == 2
    as_user(authed, MEMBER)
    assert [r["name"] for r in authed.execute("select name from families").fetchall()] == ["Iyer"]
    assert len(authed.execute("select id from parents").fetchall()) == 1


# --- outbound: the whole circle -----------------------------------------------


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 8, 21, hour, minute, tzinfo=IST)


def _seat(conn, family_id, name, email, role="member", mail=True, created="2026-08-01"):
    conn.execute(
        "insert into members (family_id, display_name, role, email, mail, created_utc) "
        "values (%s, %s, %s, %s, %s, %s)",
        (family_id, name, role, email, mail, created),
    )


class Addressed(LogTransport):
    """A transport that needs an address and remembers who it reached."""

    name = "addressed"
    requires_address = True

    def __init__(self, failing: set[str] | None = None) -> None:
        super().__init__()
        self.to: list[tuple[str, str]] = []
        self.failing = failing or set()

    def send(self, to, template_id, variables, relationship=None):
        self.to.append((template_id, to))
        if to in self.failing:
            return DeliveryResult(delivered=False, transport=self.name, detail="bounced")
        return DeliveryResult(delivered=True, transport=self.name, detail="")


def test_outbound_contacts_is_every_mail_on_member_admins_first(conn):
    family = _family(conn)
    _seat(
        conn, family.family_id, "Late admin", "z@example.test", role="admin", created="2026-08-03"
    )
    _seat(conn, family.family_id, "First member", "a@example.test", created="2026-08-01")
    _seat(conn, family.family_id, "Quiet", "q@example.test", mail=False)
    _seat(conn, family.family_id, "No email", None)
    assert [r["email"] for r in db.outbound_contacts(conn, family.family_id)] == [
        "z@example.test",
        "a@example.test",
    ]


def test_the_digest_goes_to_everyone_listening_once_each(conn, notifier):
    family = _family(conn)
    _seat(conn, family.family_id, "Kid", "kid@example.test", role="admin", created="2026-08-01")
    _seat(conn, family.family_id, "Sis", "sis@example.test", created="2026-08-02")
    _seat(conn, family.family_id, "Quiet", "quiet@example.test", mail=False)
    db.insert_ping(conn, family.parents[0].parent_id, "whatsapp", _at(7, 0), None)
    transport = Addressed()
    run_outbound(conn, transport, _at(8, 30), notifier=notifier)
    run_outbound(conn, transport, _at(8, 31), notifier=notifier)
    assert transport.to == [
        ("digest_morning_normal", "kid@example.test"),
        ("digest_morning_normal", "sis@example.test"),
    ]
    rows = conn.execute(
        "select m.email, d.status from digest_sends d join members m on m.id = d.member_id "
        "order by m.email"
    ).fetchall()
    assert [(r["email"], r["status"]) for r in rows] == [
        ("kid@example.test", "sent"),
        ("sis@example.test", "sent"),
    ]
    assert conn.execute("select status from sent_messages").fetchone()["status"] == "sent"


def test_a_member_missed_on_one_pass_is_reached_on_the_next_and_nobody_twice(conn, notifier):
    """§7 idempotency per member: the slot stays failed until everyone has it,
    and the retry reaches only the one who was missed."""
    family = _family(conn)
    _seat(conn, family.family_id, "Kid", "kid@example.test", role="admin", created="2026-08-01")
    _seat(conn, family.family_id, "Sis", "sis@example.test", created="2026-08-02")
    db.insert_ping(conn, family.parents[0].parent_id, "whatsapp", _at(7, 0), None)

    flaky = Addressed(failing={"sis@example.test"})
    run_outbound(conn, flaky, _at(8, 30), notifier=notifier)
    assert conn.execute("select status from sent_messages").fetchone()["status"] == "failed"
    assert any("1 of 2 in the circle not reached" in m for m in notifier.messages)

    recovered = Addressed()
    run_outbound(conn, recovered, _at(8, 35), notifier=notifier)
    assert recovered.to == [("digest_morning_normal", "sis@example.test")]
    assert conn.execute("select status from sent_messages").fetchone()["status"] == "sent"


def test_nobody_listening_means_no_send_and_one_alert_a_day(conn, notifier):
    family = _family(conn)
    _seat(conn, family.family_id, "Quiet", "quiet@example.test", mail=False)
    db.insert_ping(conn, family.parents[0].parent_id, "whatsapp", _at(7, 0), None)
    transport = Addressed()
    for minute in (30, 31, 32):
        run_outbound(conn, transport, _at(8, minute), notifier=notifier)
    run_outbound(conn, transport, _at(20, 30), notifier=notifier)  # the evening slot too
    assert transport.to == []
    kinds = [r["kind"] for r in conn.execute("select kind from ops_alerts order by id").fetchall()]
    assert kinds == ["circle_unreachable"]
    assert len(notifier.messages) == 1
    assert {r["status"] for r in conn.execute("select status from sent_messages").fetchall()} == {
        "skipped"
    }
    # A new day is a new alert.
    run_outbound(conn, transport, _at(8, 30).replace(day=22), notifier=notifier)
    assert [r["kind"] for r in conn.execute("select kind from ops_alerts").fetchall()] == [
        "circle_unreachable",
        "circle_unreachable",
    ]
