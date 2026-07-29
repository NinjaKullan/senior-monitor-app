"""Acceptance criteria 2, 3 and 4 — the readable ingestion route.

`/p/{device_token}/{signal}`. The token is the identity: there is no `who` in
the URL to guess, and everything outside the path is ignored.
"""

from __future__ import annotations

import psycopg

from kettle import db
from kettle.provisioning import provision_family
from kettle.timeutil import now_utc
from testsupport import BASE_URL

EXPECTED_PING_COLUMNS = {"id", "parent_id", "signal", "ts_utc", "ip_hash"}


def _family(conn: psycopg.Connection, name: str = "Sharma"):
    return provision_family(
        conn,
        name,
        "Asia/Kolkata",
        [("Amma", None), ("Appa", None)],
        base_url=BASE_URL,
    )


def _count(conn: psycopg.Connection) -> int:
    return conn.execute("select count(*) as n from pings").fetchone()["n"]


def test_readable_route_stores_a_ping(client, conn):
    """AC2: the human-readable path works and stores exactly one row."""
    family = _family(conn)
    token = family.parents[0].device_token

    resp = client.get(f"/p/{token}/whatsapp")
    assert resp.status_code == 200
    assert resp.text == "ok"

    row = conn.execute("select * from pings").fetchone()
    assert row["parent_id"] == family.parents[0].parent_id
    assert row["signal"] == "whatsapp"


def test_post_also_works(client, conn):
    """Shortcuts may be configured for either method."""
    family = _family(conn)
    assert client.post(f"/p/{family.parents[0].device_token}/news").status_code == 200
    assert _count(conn) == 1


def test_junk_params_are_never_stored(client, conn):
    """AC2: the schema is the privacy promise — extras are dropped at the door."""
    family = _family(conn)
    token = family.parents[0].device_token

    resp = client.get(
        f"/p/{token}/whatsapp"
        "?location=12.97,77.59&text=hello%20amma&device=iPhone13&lat=1&lng=2"
    )
    assert resp.status_code == 200

    columns = {
        r["column_name"]
        for r in conn.execute(
            "select column_name from information_schema.columns "
            "where table_name = 'pings'"
        ).fetchall()
    }
    assert columns == EXPECTED_PING_COLUMNS

    row = conn.execute("select * from pings").fetchone()
    blob = " ".join(str(v) for v in row.values())
    for leaked in ("12.97", "77.59", "hello", "iPhone13", "location", "lat", "lng"):
        assert leaked not in blob


def test_unknown_token_is_403_and_writes_nothing(client, conn):
    """AC3: a wrong token is a silent 403 — no data pollution from a bad paste."""
    _family(conn)
    resp = client.get("/p/thisisnotarealdevicetoken00/whatsapp")
    assert resp.status_code == 403
    assert resp.text == "forbidden"
    assert _count(conn) == 0


def test_short_token_is_403(client, conn):
    """Nothing that could not be a token gets a different answer than a wrong one."""
    _family(conn)
    assert client.get("/p/abc/whatsapp").status_code == 403
    assert _count(conn) == 0


def test_revoking_one_device_kills_only_that_device(client, conn):
    """AC3: a lost phone is a one-tap revoke, not a family outage."""
    family = _family(conn)
    amma, appa = family.parents

    assert client.get(f"/p/{amma.device_token}/whatsapp").status_code == 200
    assert client.get(f"/p/{appa.device_token}/whatsapp").status_code == 200
    assert _count(conn) == 2

    db.revoke_device(conn, amma.device_id, now_utc())

    revoked = client.get(f"/p/{amma.device_token}/youtube")
    assert revoked.status_code == 403
    assert revoked.text == "forbidden"

    # The other phone in the same family is untouched.
    assert client.get(f"/p/{appa.device_token}/youtube").status_code == 200
    assert _count(conn) == 3
    assert (
        conn.execute(
            "select count(*) as n from pings where parent_id = %s", (amma.parent_id,)
        ).fetchone()["n"]
        == 1
    )


def test_signal_outside_the_allowlist_is_400(client, conn):
    """AC4: an unknown signal name is rejected, not stored."""
    family = _family(conn)
    resp = client.get(f"/p/{family.parents[0].device_token}/tiktok")
    assert resp.status_code == 400
    assert resp.text == "unknown signal"
    assert _count(conn) == 0


def test_allowlist_is_per_parent(client, conn):
    """AC4: turning a signal off for one person leaves everyone else alone."""
    family = _family(conn)
    amma, appa = family.parents
    conn.execute(
        "update parent_signals set active = false "
        "where parent_id = %s and signal = 'youtube'",
        (amma.parent_id,),
    )

    assert client.get(f"/p/{amma.device_token}/youtube").status_code == 400
    assert client.get(f"/p/{appa.device_token}/youtube").status_code == 200
    assert _count(conn) == 1


def test_duplicate_within_60s_is_collapsed(client, conn):
    """AC4: Shortcuts double-fires must not double-count."""
    family = _family(conn)
    token = family.parents[0].device_token

    client.get(f"/p/{token}/whatsapp")
    client.get(f"/p/{token}/whatsapp")
    assert _count(conn) == 1

    # A different signal in the same second is a separate row.
    client.get(f"/p/{token}/youtube")
    assert _count(conn) == 2


def test_ping_outside_the_dedupe_window_is_stored(conn):
    """Past 60s the same signal is a genuine new ping."""
    from datetime import timedelta

    family = _family(conn)
    parent_id = family.parents[0].parent_id
    now = now_utc()
    assert db.insert_ping(conn, parent_id, "news", now - timedelta(seconds=90), None)
    assert db.insert_ping(conn, parent_id, "news", now, None)
    assert _count(conn) == 2


def test_ip_is_hashed_not_stored(client, conn):
    """ip_hash is one-way and never equals the address it came from."""
    family = _family(conn)
    client.get(
        f"/p/{family.parents[0].device_token}/whatsapp",
        headers={"x-forwarded-for": "203.0.113.9"},
    )
    row = conn.execute("select * from pings").fetchone()
    assert row["ip_hash"] and "203.0.113.9" not in row["ip_hash"]
    assert len(row["ip_hash"]) == 16


def test_signal_case_is_normalised(client, conn):
    """A shortcut built with different capitalisation still works."""
    family = _family(conn)
    assert client.get(f"/p/{family.parents[0].device_token}/WhatsApp").status_code == 200
    assert conn.execute("select signal from pings").fetchone()["signal"] == "whatsapp"


def test_healthz_needs_no_auth(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"db": True}
