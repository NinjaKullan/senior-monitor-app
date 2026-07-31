"""Acceptance criterion 6 — app_claim_membership (spec 005a §2).

`members.auth_user_id` stays null until the invited person signs up. This RPC is
what closes that loop, and it is SECURITY DEFINER, so the interesting tests are
the ones about what it refuses to do.
"""

from __future__ import annotations

import psycopg
import pytest

from kettle.provisioning import provision_family
from testsupport import BASE_URL, as_user, as_user_with_email, invite_member

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"
EMAIL_A = "child@example.test"
EMAIL_B = "sister@example.test"


def _family(conn, name="Sharma"):
    return provision_family(
        conn, name, "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )


def _claim(authed: psycopg.Connection) -> int:
    return authed.execute("select public.app_claim_membership() as n").fetchone()["n"]


def _auth_user_id(conn, member_id):
    return conn.execute(
        "select auth_user_id from members where id = %s", (member_id,)
    ).fetchone()["auth_user_id"]


def test_matching_email_links_the_membership(conn, authed):
    """The ordinary case: invited by email, signs up, gets their family."""
    family = _family(conn)
    member = invite_member(conn, family.family_id, EMAIL_A)

    as_user_with_email(authed, USER_A, EMAIL_A)
    assert _claim(authed) == 1
    assert str(_auth_user_id(conn, member)) == USER_A

    # And now they can see their family through the ordinary policies.
    assert [r["name"] for r in authed.execute("select name from families").fetchall()] == [
        "Sharma"
    ]


def test_a_different_email_links_nothing(conn, authed):
    """The email comes from the verified JWT, so there is nothing to spoof."""
    family = _family(conn)
    member = invite_member(conn, family.family_id, EMAIL_A)

    as_user_with_email(authed, USER_B, EMAIL_B)
    assert _claim(authed) == 0
    assert _auth_user_id(conn, member) is None
    assert authed.execute("select * from families").fetchall() == []


def test_an_already_claimed_row_is_untouched(conn, authed):
    """Only nulls are filled — a claimed membership cannot be taken over."""
    family = _family(conn)
    member = invite_member(conn, family.family_id, EMAIL_A)
    conn.execute(
        "update members set auth_user_id = %s where id = %s", (USER_A, member)
    )

    # A second person with the same invited email signs up later.
    as_user_with_email(authed, USER_B, EMAIL_A)
    assert _claim(authed) == 0
    assert str(_auth_user_id(conn, member)) == USER_A


def test_one_email_across_two_families_links_both(conn, authed):
    """Item 13's case: own parents and in-laws are two memberships, one person."""
    sharma = _family(conn, "Sharma")
    iyer = _family(conn, "Iyer")
    invite_member(conn, sharma.family_id, EMAIL_A)
    invite_member(conn, iyer.family_id, EMAIL_A, role="child")

    as_user_with_email(authed, USER_A, EMAIL_A)
    assert _claim(authed) == 2
    assert sorted(
        r["name"] for r in authed.execute("select name from families").fetchall()
    ) == ["Iyer", "Sharma"]


def test_matching_is_case_insensitive(conn, authed):
    """Auth normalises case; an invitation typed in capitals still matches."""
    family = _family(conn)
    member = invite_member(conn, family.family_id, "Child@Example.Test")

    as_user_with_email(authed, USER_A, EMAIL_A)
    assert _claim(authed) == 1
    assert str(_auth_user_id(conn, member)) == USER_A


def test_a_session_without_an_email_claims_nothing(conn, authed):
    family = _family(conn)
    member = invite_member(conn, family.family_id, EMAIL_A)

    as_user(authed, USER_A)  # sub only, no email
    assert _claim(authed) == 0
    assert _auth_user_id(conn, member) is None


def test_a_session_with_no_jwt_claims_nothing(conn, authed):
    family = _family(conn)
    invite_member(conn, family.family_id, EMAIL_A)

    authed.execute("select set_config('request.jwt.claims', '', false)")
    assert _claim(authed) == 0


def test_anon_cannot_execute_it(conn, database_url):
    """0004 doctrine: the pre-login role gets nothing, by explicit revoke."""
    from psycopg.rows import dict_row

    grants = conn.execute(
        """
        select has_function_privilege('anon', oid, 'execute') as anon_exec,
               has_function_privilege('authenticated', oid, 'execute') as authed_exec
        from pg_proc where proname = 'app_claim_membership'
        """
    ).fetchone()
    assert grants["anon_exec"] is False
    assert grants["authed_exec"] is True

    with psycopg.connect(database_url, autocommit=True, row_factory=dict_row) as anon:
        anon.execute("set role anon")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            anon.execute("select public.app_claim_membership()").fetchall()


def test_claiming_does_not_grant_a_write_path(conn, authed):
    """The RPC exists precisely so no client write grant has to."""
    family = _family(conn)
    invite_member(conn, family.family_id, EMAIL_A)
    as_user_with_email(authed, USER_A, EMAIL_A)
    _claim(authed)

    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute("update members set display_name = 'x'")
