"""Acceptance criterion 1 — the isolation proof.

Two real families, two real Supabase Auth users, one connection acting as the
`authenticated` role. Nothing in the API layer is involved: if these policies
were wrong, no amount of careful app code would save the tenant boundary.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import psycopg
import pytest
from psycopg.rows import dict_row

from kettle import db
from kettle.provisioning import provision_family
from kettle.timeutil import now_utc
from testsupport import (
    BASE_URL,
    FAMILY_TABLES,
    add_member,
    as_user,
    object_privileges,
)

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
    """Ops alerts are the founder's plumbing log — no end user can read them.

    Two independent gates, and this asserts both. Before migration 0004 only the
    second one existed: `authenticated` held SELECT from Supabase's bootstrap and
    was stopped purely by ops_alerts having no policy.
    """
    family_a = two_families["a"]
    db.insert_ops_alert(
        conn, family_a.family_id, family_a.parents[0].parent_id, "noon", "x", now_utc()
    )
    assert conn.execute("select count(*) as n from ops_alerts").fetchone()["n"] == 1

    # Gate 1: no privilege.
    assert object_privileges(conn, ["anon", "authenticated"]).get(
        ("authenticated", "ops_alerts")
    ) is None
    # Gate 2: no policy.
    policies = conn.execute(
        "select policyname from pg_policies "
        "where schemaname = 'public' and tablename = 'ops_alerts'"
    ).fetchall()
    assert policies == []

    as_user(authed, USER_A)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute("select * from ops_alerts").fetchall()


def test_digest_sends_are_isolated_per_family(two_families, authed, conn):
    """AC8: a family can read its own digest history and nobody else's."""
    for key, member_user in (("a", USER_A), ("b", USER_B)):
        family = two_families[key]
        member = conn.execute(
            "select id from members where family_id = %s and auth_user_id = %s",
            (family.family_id, member_user),
        ).fetchone()
        db.record_digest_send(
            conn,
            family.family_id,
            family.parents[0].parent_id,
            "morning",
            date(2026, 8, 3),
            member["id"],
            "sms",
            "sent",
            now_utc(),
        )
    assert conn.execute("select count(*) as n from digest_sends").fetchone()["n"] == 2

    as_user(authed, USER_A)
    mine = _rows(authed, "select family_id from digest_sends")
    assert [r["family_id"] for r in mine] == [two_families["a"].family_id]

    # Naming B's family explicitly does not get past the policy either.
    assert (
        authed.execute(
            "select count(*) as n from digest_sends where family_id = %s",
            (two_families["b"].family_id,),
        ).fetchone()["n"]
        == 0
    )

    as_user(authed, USER_B)
    assert [r["family_id"] for r in _rows(authed, "select family_id from digest_sends")] == [
        two_families["b"].family_id
    ]


def test_digest_sends_are_read_only_for_members(two_families, authed, conn):
    """Recipients can see what was sent; only the service writes it."""
    as_user(authed, USER_A)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute(
            "insert into digest_sends "
            "(family_id, kind, local_date, member_id, channel, status) "
            "select f.id, 'morning', current_date, m.id, 'sms', 'sent' "
            "from families f join members m on m.family_id = f.id limit 1"
        )




def test_anon_holds_no_privileges_on_anything(conn: psycopg.Connection):
    """0004: the pre-login role holds nothing on any public table or sequence.

    Supabase's bootstrap had granted anon the full set — including TRUNCATE,
    which is not a row-level operation and which RLS therefore does not govern at
    all. That was a data-loss primitive sitting on the pre-login role, not a read
    risk RLS was quietly covering.
    """
    held = {
        key: privs
        for key, privs in object_privileges(conn, ["anon"]).items()
        if key[0] == "anon"
    }
    assert held == {}


def test_authenticated_holds_exactly_select_on_the_family_tables(
    conn: psycopg.Connection,
):
    """0004's baseline, plus the two grants later specs added on purpose.

    Reads only — except where a ruling says otherwise: spec 009 §4 gives the
    app select+insert on journal_entries (and usage on its identity
    sequence), and §5 an UPDATE on parents scoped to the city_label COLUMN,
    which lives in pg_attribute rather than relacl and is asserted in
    test_webapp_contract.py. Anything else appearing here is a leak.
    """
    held = object_privileges(conn, ["authenticated"])
    expected = {("authenticated", table): {"SELECT"} for table in FAMILY_TABLES}
    expected[("authenticated", "journal_entries")] = {"SELECT", "INSERT"}
    expected[("authenticated", "journal_entries_id_seq")] = {"USAGE"}
    assert held == expected

    # Spelled out, because these are the ones the bootstrap left behind.
    for table in FAMILY_TABLES:
        privs = held[("authenticated", table)]
        assert "TRUNCATE" not in privs
        assert "REFERENCES" not in privs
        assert "TRIGGER" not in privs


def test_authenticated_role_cannot_write_or_truncate(two_families, authed):
    """Spec 002 grants reads only; ingestion runs as the service role."""
    as_user(authed, USER_A)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute(
            "insert into pings (parent_id, signal, ts_utc) "
            "select id, 'whatsapp', now() from parents limit 1"
        )
    # TRUNCATE is the one RLS would not have caught.
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute("truncate pings")


def test_anon_cannot_execute_the_family_lookup(conn: psycopg.Connection, database_url: str):
    """0003: the pre-login role has no business calling a SECURITY DEFINER helper.

    Supabase's default privileges grant EXECUTE on new public functions directly
    to anon, and `revoke ... from public` does not remove a direct grant — so
    this needs its own revoke, and its own test.
    """
    grants = conn.execute(
        """
        select
            has_function_privilege('anon', oid, 'execute') as anon_exec,
            has_function_privilege('authenticated', oid, 'execute') as authed_exec,
            has_function_privilege('service_role', oid, 'execute') as service_exec
        from pg_proc where proname = 'app_current_family_ids'
        """
    ).fetchone()
    assert grants["anon_exec"] is False
    # The roles that legitimately need it keep it.
    assert grants["authed_exec"] is True
    assert grants["service_exec"] is True

    with psycopg.connect(database_url, autocommit=True, row_factory=dict_row) as anon:
        anon.execute("set role anon")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            anon.execute("select public.app_current_family_ids()").fetchall()


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
