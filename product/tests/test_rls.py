"""Acceptance criterion 1 — the isolation proof.

Two real families, two real Supabase Auth users, one connection acting as the
`authenticated` role. Nothing in the API layer is involved: if these policies
were wrong, no amount of careful app code would save the tenant boundary.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import psycopg
import pytest

from kettle import db
from kettle.provisioning import provision_family
from kettle.timeutil import now_utc
from testsupport import BASE_URL, add_member, as_user

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"
STRANGER = "33333333-3333-3333-3333-333333333333"


@pytest.fixture
def two_families(conn: psycopg.Connection) -> dict:
    """Family A (Chennai) and family B (Chicago), each with a member and a ping."""
    family_a = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    family_b = provision_family(
        conn, "Iyer", "America/Chicago", [("Patti", None)], base_url=BASE_URL
    )
    add_member(conn, family_a.family_id, USER_A)
    add_member(conn, family_b.family_id, USER_B)

    now = now_utc()
    db.insert_ping(conn, family_a.parents[0].parent_id, "whatsapp", now, None)
    db.insert_ping(
        conn, family_b.parents[0].parent_id, "whatsapp", now - timedelta(hours=1), None
    )
    return {"a": family_a, "b": family_b}


def _rows(c: psycopg.Connection, sql: str) -> list[dict]:
    return c.execute(sql).fetchall()


def test_each_family_sees_only_its_own_rows(two_families, authed):
    """AC1: A's JWT reads A's data and nothing of B's, and vice versa."""
    as_user(authed, USER_A)
    assert [r["name"] for r in _rows(authed, "select name from families")] == ["Sharma"]
    assert [r["display_name"] for r in _rows(authed, "select display_name from parents")] == [
        "Amma"
    ]
    assert len(_rows(authed, "select id from pings")) == 1

    as_user(authed, USER_B)
    assert [r["name"] for r in _rows(authed, "select name from families")] == ["Iyer"]
    assert [r["display_name"] for r in _rows(authed, "select display_name from parents")] == [
        "Patti"
    ]
    assert len(_rows(authed, "select id from pings")) == 1


def test_family_a_cannot_read_family_b_pings_even_when_asked_by_id(
    two_families, authed, conn
):
    """Naming B's rows explicitly does not get past the policy."""
    b_parent = two_families["b"].parents[0].parent_id
    b_ping_ids = [
        r["id"]
        for r in conn.execute(
            "select id from pings where parent_id = %s", (b_parent,)
        ).fetchall()
    ]
    assert b_ping_ids  # the rows genuinely exist for the service role

    as_user(authed, USER_A)
    hidden = authed.execute(
        "select id from pings where id = any(%s)", (b_ping_ids,)
    ).fetchall()
    assert hidden == []

    targeted = authed.execute(
        "select count(*) as n from pings where parent_id = %s", (b_parent,)
    ).fetchone()
    assert targeted["n"] == 0


def test_family_a_cannot_read_family_b_devices_or_signals(two_families, authed):
    """Device tokens are credentials: a neighbouring tenant must never see one."""
    b_token = two_families["b"].parents[0].device_token

    as_user(authed, USER_A)
    tokens = [r["device_token"] for r in _rows(authed, "select device_token from devices")]
    assert b_token not in tokens
    assert len(tokens) == 1

    assert (
        authed.execute(
            "select count(*) as n from devices where device_token = %s", (b_token,)
        ).fetchone()["n"]
        == 0
    )
    # parent_signals is scoped through parents the same way.
    assert len({r["parent_id"] for r in _rows(authed, "select parent_id from parent_signals")}) == 1


def test_user_with_no_family_sees_nothing(two_families, authed):
    """A signed-in stranger is not a tenant."""
    as_user(authed, STRANGER)
    for table in ("families", "members", "parents", "devices", "parent_signals", "pings"):
        assert _rows(authed, f"select * from {table}") == []


def test_no_jwt_sees_nothing(two_families, authed):
    """An authenticated role with no claims resolves to no families at all."""
    authed.execute("select set_config('request.jwt.claims', '', false)")
    assert _rows(authed, "select * from pings") == []


def test_ops_alerts_are_service_only(two_families, authed, conn):
    """Ops alerts are the founder's plumbing log — no end user can read them."""
    family_a = two_families["a"]
    db.insert_ops_alert(
        conn, family_a.family_id, family_a.parents[0].parent_id, "noon", "x", now_utc()
    )
    assert conn.execute("select count(*) as n from ops_alerts").fetchone()["n"] == 1

    as_user(authed, USER_A)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute("select * from ops_alerts").fetchall()


def test_authenticated_role_cannot_write(two_families, authed):
    """Spec 002 grants reads only; ingestion runs as the service role."""
    as_user(authed, USER_A)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute(
            "insert into pings (parent_id, signal, ts_utc) "
            "select id, 'whatsapp', now() from parents limit 1"
        )


def test_rls_is_enabled_on_every_table(conn: psycopg.Connection):
    """A new table without RLS would be a silent tenant leak — assert on the catalog."""
    rows = conn.execute(
        """
        select c.relname, c.relrowsecurity
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public' and c.relkind = 'r'
        """
    ).fetchall()
    assert rows
    unprotected = [r["relname"] for r in rows if not r["relrowsecurity"]]
    assert unprotected == []


def test_service_role_still_sees_everything(two_families, conn):
    """The ingestion service must not be locked out by its own policies."""
    assert conn.execute("select count(*) as n from pings").fetchone()["n"] == 2
    assert conn.execute("select count(*) as n from families").fetchone()["n"] == 2


def test_policies_survive_a_second_membership(two_families, authed, conn):
    """A child in two families (their parents and their in-laws) sees both."""
    add_member(conn, two_families["b"].family_id, USER_A, role="child")
    as_user(authed, USER_A)
    names = sorted(r["name"] for r in _rows(authed, "select name from families"))
    assert names == ["Iyer", "Sharma"]
    assert len(_rows(authed, "select id from pings")) == 2


def test_ping_lands_under_the_right_family(two_families, conn, client):
    """AC1, first half: a ping on A's token is A's row, not B's."""
    token = two_families["a"].parents[0].device_token
    a_parent = two_families["a"].parents[0].parent_id

    before = conn.execute(
        "select count(*) as n from pings where parent_id = %s", (a_parent,)
    ).fetchone()["n"]
    assert client.get(f"/p/{token}/youtube").status_code == 200

    row = conn.execute(
        "select p.parent_id, pa.family_id from pings p "
        "join parents pa on pa.id = p.parent_id "
        "where p.signal = 'youtube'"
    ).fetchone()
    assert row["parent_id"] == a_parent
    assert row["family_id"] == two_families["a"].family_id
    assert (
        conn.execute(
            "select count(*) as n from pings where parent_id = %s", (a_parent,)
        ).fetchone()["n"]
        == before + 1
    )


def test_isolation_holds_for_a_freshly_created_family(conn, authed):
    """Provisioning a third family does not widen anyone else's view."""
    third = provision_family(
        conn, "Nair", "Asia/Kolkata", [("Ammachi", None)], base_url=BASE_URL
    )
    add_member(conn, third.family_id, USER_B)
    db.insert_ping(
        conn, third.parents[0].parent_id, "news", datetime.now().astimezone(), None
    )

    as_user(authed, USER_A)
    assert _rows(authed, "select * from pings") == []
