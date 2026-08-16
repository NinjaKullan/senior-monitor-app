"""Setup links (spec 005b §4.2) — unguessable, expiring, revocable, per parent.

The link is the setup page's address and nothing else: it must never carry or
reveal the device token it travels for, and it must die with that token. The
child app reads links through RLS to render "Mom's setup" as a forwardable
card, which is why isolation and the write ban are tested here alongside the
issuance mechanics.
"""

from __future__ import annotations

import re
from datetime import timedelta

import psycopg
import pytest

from kettle.provisioning import (
    SETUP_LINK_TTL_DAYS,
    issue_setup_link_by_token,
    provision_family,
    render_summary,
)
from kettle.timeutil import now_utc
from scripts.provision import main as provision_main
from testsupport import BASE_URL, add_member, as_user

SLUG_RE = re.compile(r"^[A-Za-z0-9_-]{20,}$")

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


def _links(conn: psycopg.Connection) -> list[dict]:
    return conn.execute(
        "select * from setup_links order by created_utc, slug"
    ).fetchall()


def test_provisioning_issues_one_live_link_per_parent(conn: psycopg.Connection):
    family = provision_family(
        conn,
        "Sharma",
        "Asia/Kolkata",
        [("Amma", None), ("Appa", None)],
        base_url=BASE_URL,
    )

    rows = _links(conn)
    assert len(rows) == 2
    assert all(r["revoked_utc"] is None for r in rows)
    assert {r["parent_id"] for r in rows} == {p.parent_id for p in family.parents}

    for parent in family.parents:
        assert parent.setup_url.startswith(f"{BASE_URL}/s/")
        slug = parent.setup_url.rsplit("/", 1)[-1]
        assert SLUG_RE.match(slug), slug
        # The slug is its own secret. A setup URL carrying the device token
        # would hand out a ping identity to everyone the link is forwarded
        # through — the page exists precisely so that never happens.
        assert parent.device_token not in parent.setup_url

    slugs = {p.setup_url.rsplit("/", 1)[-1] for p in family.parents}
    assert len(slugs) == 2, "two parents must never share a setup link"


def test_links_expire_seven_days_out(conn: psycopg.Connection):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    row = _links(conn)[0]
    assert row["expires_utc"] - row["created_utc"] == timedelta(days=SETUP_LINK_TTL_DAYS)
    assert family.parents[0].setup_expires_utc == row["expires_utc"]


def test_summary_prints_the_setup_page_per_parent(conn: psycopg.Connection):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    text = render_summary(family)
    assert family.parents[0].setup_url in text
    assert "setup page:" in text
    assert "never a file and never a token" in text


def test_reissue_rotates_the_previous_link(conn: psycopg.Connection):
    """Issuance is rotation: at most one answering link per device."""
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    token = family.parents[0].device_token
    first_slug = family.parents[0].setup_url.rsplit("/", 1)[-1]

    issued = issue_setup_link_by_token(conn, token, BASE_URL, now_utc())
    assert issued is not None
    assert issued.parent_name == "Amma"
    assert issued.family_name == "Sharma"
    new_slug = issued.url.rsplit("/", 1)[-1]
    assert new_slug != first_slug

    by_slug = {r["slug"]: r for r in _links(conn)}
    assert by_slug[first_slug]["revoked_utc"] is not None
    assert by_slug[new_slug]["revoked_utc"] is None


def test_no_link_for_unknown_or_revoked_devices(conn: psycopg.Connection):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    token = family.parents[0].device_token

    assert issue_setup_link_by_token(conn, "nosuchtoken000000000000", BASE_URL, now_utc()) is None

    conn.execute("update devices set active = false, revoked_utc = now()")
    assert issue_setup_link_by_token(conn, token, BASE_URL, now_utc()) is None


def test_cli_setup_link_prints_url_and_expiry(
    conn: psycopg.Connection, database_url: str, capsys
):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    token = family.parents[0].device_token

    exit_code = provision_main(
        ["--setup-link", token, "--database-url", database_url, "--base-url", BASE_URL]
    )
    assert exit_code == 0
    out = capsys.readouterr().out
    assert f"{BASE_URL}/s/" in out
    assert "expires" in out
    assert "Amma" in out
    # The printout confirms the rotation, so the operator knows stale copies died.
    assert "now dead" in out


def test_cli_setup_link_refuses_unknown_tokens(database_url: str, capsys, conn):
    exit_code = provision_main(
        ["--setup-link", "nosuchtoken000000000000", "--database-url", database_url]
    )
    assert exit_code == 1
    assert "No active device" in capsys.readouterr().err


def test_cli_setup_link_cannot_be_mixed(database_url: str):
    with pytest.raises(SystemExit):
        provision_main(
            ["--setup-link", "token0000000000000000", "--demo", "--database-url", database_url]
        )


# --- RLS: the child app's read, and nobody's write ---------------------------


@pytest.fixture
def two_families(conn: psycopg.Connection) -> dict:
    a = provision_family(conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL)
    b = provision_family(conn, "Iyer", "America/Chicago", [("Patti", None)], base_url=BASE_URL)
    add_member(conn, a.family_id, USER_A)
    add_member(conn, b.family_id, USER_B)
    return {"a": a, "b": b}


def test_family_reads_only_its_own_setup_links(two_families, authed):
    a_slug = two_families["a"].parents[0].setup_url.rsplit("/", 1)[-1]
    b_slug = two_families["b"].parents[0].setup_url.rsplit("/", 1)[-1]

    as_user(authed, USER_A)
    slugs = [r["slug"] for r in authed.execute("select slug from setup_links").fetchall()]
    assert slugs == [a_slug]
    assert (
        authed.execute(
            "select count(*) as n from setup_links where slug = %s", (b_slug,)
        ).fetchone()["n"]
        == 0
    )


def test_clients_cannot_mint_or_extend_links(two_families, authed):
    """A client that could write links could mint indefinite credentials."""
    as_user(authed, USER_A)
    parent_id = two_families["a"].parents[0].parent_id
    device_id = two_families["a"].parents[0].device_id
    for statement, params in (
        (
            "insert into setup_links (device_id, parent_id, slug, expires_utc) "
            "values (%s, %s, 'forgedforgedforgedforged', now() + interval '365 days')",
            (device_id, parent_id),
        ),
        ("update setup_links set expires_utc = now() + interval '365 days'", ()),
        ("delete from setup_links", ()),
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            authed.execute(statement, params)
