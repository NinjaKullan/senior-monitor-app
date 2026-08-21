"""Family provisioning (spec 002 §5) — the onboarding path until the wizard exists."""

from __future__ import annotations

import re

import psycopg
import pytest

from kettle.provisioning import (
    DEMO_FAMILY_NAME,
    provision_demo_family,
    provision_family,
    render_summary,
    set_parent_signals,
)
from kettle.signals import STANDARD_SIGNALS
from scripts.provision import _parse_parent
from scripts.provision import main as provision_main
from testsupport import BASE_URL

TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{20,}$")


def test_provisioning_creates_the_whole_family(conn: psycopg.Connection):
    family = provision_family(
        conn,
        "Sharma",
        "Asia/Kolkata",
        [("Amma", None), ("Appa", "America/Chicago")],
        base_url=BASE_URL,
        owner_email="child@example.test",
    )

    assert conn.execute("select count(*) as n from families").fetchone()["n"] == 1
    assert conn.execute("select count(*) as n from parents").fetchone()["n"] == 2
    assert conn.execute("select count(*) as n from devices").fetchone()["n"] == 2

    owner = conn.execute("select * from members").fetchone()
    assert owner["role"] == "owner"
    assert owner["email"] == "child@example.test"
    # The auth user does not exist until that person signs up.
    assert owner["auth_user_id"] is None

    amma, appa = family.parents
    assert amma.tz is None
    assert appa.tz == "America/Chicago"
    stored = conn.execute(
        "select display_name, tz from parents order by display_name"
    ).fetchall()
    assert stored == [
        {"display_name": "Amma", "tz": None},
        {"display_name": "Appa", "tz": "America/Chicago"},
    ]


def test_each_parent_gets_the_seeded_allowlist(conn: psycopg.Connection):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    rows = conn.execute(
        "select signal, alarm_grade, active from parent_signals "
        "where parent_id = %s order by signal",
        (family.parents[0].parent_id,),
    ).fetchall()
    assert {(r["signal"], r["alarm_grade"]) for r in rows} == set(STANDARD_SIGNALS)
    assert all(r["active"] for r in rows)


def test_tokens_are_per_device_long_and_url_safe(conn: psycopg.Connection):
    family = provision_family(
        conn,
        "Sharma",
        "Asia/Kolkata",
        [("Amma", None), ("Appa", None)],
        base_url=BASE_URL,
    )
    tokens = [p.device_token for p in family.parents]
    assert len(set(tokens)) == 2
    for token in tokens:
        assert TOKEN_RE.match(token), token
        assert len(token) >= 20


def test_two_families_never_share_a_token(conn: psycopg.Connection):
    a = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    b = provision_family(
        conn, "Iyer", "Asia/Kolkata", [("Patti", None)], base_url=BASE_URL
    )
    assert a.parents[0].device_token != b.parents[0].device_token


def test_urls_and_shortcut_names_are_ready_to_use(conn: psycopg.Connection):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    parent = family.parents[0]
    by_signal = {s.signal: s for s in parent.signals}

    whatsapp = by_signal["whatsapp"]
    assert whatsapp.url == f"{BASE_URL}/p/{parent.device_token}/whatsapp"
    assert whatsapp.shortcut == "Kettle — WhatsApp"
    assert whatsapp.alarm_grade is True
    assert by_signal["device_alive"].alarm_grade is False
    # No parent name in the shortcut (DECISIONS 96a): the tile truncates it,
    # and everyone reading the string already knows whose phone it is on.
    assert by_signal["device_alive"].shortcut == "Kettle — Daily Check"
    # No `who` in the URL — the token is the identity.
    assert "who=" not in whatsapp.url


def test_provisioned_urls_actually_work(conn: psycopg.Connection, client):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    for sig in family.parents[0].signals:
        path = sig.url.removeprefix(BASE_URL)
        assert client.get(path).status_code == 200, path
    assert conn.execute("select count(*) as n from pings").fetchone()["n"] == len(
        STANDARD_SIGNALS
    )


def test_demo_family(conn: psycopg.Connection):
    family = provision_demo_family(conn, base_url=BASE_URL)
    assert family.name == DEMO_FAMILY_NAME
    assert [p.display_name for p in family.parents] == ["Demo Amma", "Demo Appa"]


def test_render_summary_is_operator_readable(conn: psycopg.Connection):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", "America/Chicago")], base_url=BASE_URL
    )
    text = render_summary(family)
    assert "Family: Sharma" in text
    assert "[tz America/Chicago]" in text
    assert "Kettle — WhatsApp" in text
    assert f"{BASE_URL}/p/{family.parents[0].device_token}/whatsapp" in text
    assert "revoking one phone leaves the rest working" in text


def test_revoking_twice_is_idempotent(conn: psycopg.Connection, database_url: str, capsys):
    """Midnight emergencies get run twice; the second run must not look like a failure."""
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    token = family.parents[0].device_token

    assert provision_main(["--revoke", token, "--database-url", database_url]) == 0
    first = conn.execute("select revoked_utc from devices").fetchone()["revoked_utc"]

    assert provision_main(["--revoke", token, "--database-url", database_url]) == 0
    assert "Already revoked device" in capsys.readouterr().out
    # The original revocation time is preserved.
    assert conn.execute("select revoked_utc from devices").fetchone()["revoked_utc"] == first


def test_revoke_cannot_be_mixed_with_provisioning(database_url: str):
    """Two very different operations; refuse the ambiguous invocation."""
    with pytest.raises(SystemExit):
        provision_main(
            ["--revoke", "sometoken000000000000", "--demo", "--database-url", database_url]
        )


def test_parse_parent_argument():
    assert _parse_parent("Amma") == ("Amma", None)
    assert _parse_parent("Appa:America/Chicago") == ("Appa", "America/Chicago")
    assert _parse_parent(" Amma ") == ("Amma", None)


def test_cli_demo_flag(conn: psycopg.Connection, database_url: str, capsys):
    """AC: the --demo flag provisions a usable family end to end."""
    exit_code = provision_main(
        ["--demo", "--database-url", database_url, "--base-url", BASE_URL]
    )
    assert exit_code == 0

    out = capsys.readouterr().out
    assert DEMO_FAMILY_NAME in out
    assert "Kettle — WhatsApp" in out

    token = conn.execute(
        "select device_token from devices join parents p on p.id = devices.parent_id "
        "where p.display_name = 'Demo Amma'"
    ).fetchone()["device_token"]
    assert f"{BASE_URL}/p/{token}/whatsapp" in out


def test_cli_named_family(conn: psycopg.Connection, database_url: str, capsys):
    exit_code = provision_main(
        [
            "--family", "Nair",
            "--tz", "Asia/Kolkata",
            "--parent", "Ammachi",
            "--parent", "Appachan:America/Chicago",
            "--owner-email", "child@example.test",
            "--database-url", database_url,
            "--base-url", BASE_URL,
        ]
    )
    assert exit_code == 0
    assert "Family: Nair" in capsys.readouterr().out

    rows = conn.execute(
        "select display_name, tz from parents order by display_name"
    ).fetchall()
    assert rows == [
        {"display_name": "Ammachi", "tz": None},
        {"display_name": "Appachan", "tz": "America/Chicago"},
    ]


def test_signals_flag_chooses_the_allowlist_at_provisioning(conn: psycopg.Connection):
    """DECISIONS 94: chosen at creation, not seeded-then-edited."""
    family = provision_family(
        conn, "Chosen", "Asia/Kolkata", [("Appa", None)],
        base_url=BASE_URL, signals=["routine", "charger", "device_alive"],
    )
    rows = conn.execute(
        "select signal, alarm_grade, active from parent_signals where parent_id = %s "
        "order by signal",
        (family.parents[0].parent_id,),
    ).fetchall()
    assert [(r["signal"], r["alarm_grade"], r["active"]) for r in rows] == [
        ("charger", False, True),
        ("device_alive", False, True),
        ("routine", True, True),
    ]


def test_an_unknown_signal_key_fails_before_anything_is_written(conn: psycopg.Connection):
    with pytest.raises(ValueError, match="routnie"):
        provision_family(
            conn, "Typo", "Asia/Kolkata", [("Appa", None)],
            base_url=BASE_URL, signals=["routnie"],
        )
    assert conn.execute("select count(*) as n from families").fetchone()["n"] == 0


def test_set_signals_repoints_a_live_parent_without_sql(conn: psycopg.Connection):
    """DECISIONS 107's migration path: Appa moves from per-app keys to the pair.

    The old rows go inactive rather than away — history keeps its rows, and the
    app's `Not set up yet` never lies about a signal that really did report.
    """
    family = provision_family(
        conn, "Live", "Asia/Kolkata", [("Appa", None)], base_url=BASE_URL
    )
    token = family.parents[0].device_token

    result = set_parent_signals(conn, token, ["routine", "charger"])
    assert result == ("Appa", ["routine", "charger"])

    rows = conn.execute(
        "select signal, alarm_grade, active from parent_signals where parent_id = %s "
        "order by signal",
        (family.parents[0].parent_id,),
    ).fetchall()
    state = {r["signal"]: (r["alarm_grade"], r["active"]) for r in rows}
    assert state["routine"] == (True, True)
    assert state["charger"] == (False, True)
    # Every seeded signal survives, inactive.
    for old in ("whatsapp", "youtube", "news", "charge_on", "charge_off", "device_alive"):
        assert state[old][1] is False, old


def test_set_signals_on_a_revoked_or_unknown_token_changes_nothing(conn: psycopg.Connection):
    family = provision_family(
        conn, "Gone", "Asia/Kolkata", [("Appa", None)], base_url=BASE_URL
    )
    token = family.parents[0].device_token
    conn.execute("update devices set revoked_utc = now() where device_token = %s", (token,))

    assert set_parent_signals(conn, token, ["routine"]) is None
    assert set_parent_signals(conn, "no-such-token-anywhere1234", ["routine"]) is None
    active = conn.execute(
        "select count(*) as n from parent_signals where parent_id = %s and active",
        (family.parents[0].parent_id,),
    ).fetchone()["n"]
    assert active == len(STANDARD_SIGNALS)
