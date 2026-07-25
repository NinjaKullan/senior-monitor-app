"""Acceptance criteria 1-4: the webhook itself."""

from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient

from app import db
from app.timeutil import fmt_display, fmt_utc, now_utc
from tests.conftest import TOKEN

EXPECTED_PING_COLUMNS = {"id", "who", "signal", "ts_utc", "ip_hash"}


def _count(conn) -> int:
    return conn.execute("SELECT COUNT(*) AS n FROM pings").fetchone()["n"]


def test_ping_stores_row_and_shows_on_status(client: TestClient, conn, logged_labels):
    """AC1: a valid ping is 200/ok, lands in the DB, and renders on /status in IST."""
    resp = client.get(f"/ping?token={TOKEN}&who=mom&signal=whatsapp")
    assert resp.status_code == 200
    assert resp.text == "ok"

    row = conn.execute("SELECT * FROM pings").fetchone()
    assert row["who"] == "mom"
    assert row["signal"] == "whatsapp"

    logged_labels()
    page = client.get(f"/status?token={TOKEN}").text
    assert "whatsapp" in page
    # Server-side UTC stored, IST rendered.
    assert fmt_display(now_utc(), "Asia/Kolkata") in page


def test_post_ping_also_works(client: TestClient, conn):
    """Shortcuts may be configured for either method."""
    assert client.post(f"/ping?token={TOKEN}&who=dad&signal=news").status_code == 200
    assert _count(conn) == 1


def test_bad_token_is_403_and_writes_nothing(client: TestClient, conn):
    """AC2: wrong or missing token → 403, zero DB writes, nothing leaked."""
    before = _count(conn)

    wrong = client.get("/ping?token=wrong&who=mom&signal=whatsapp")
    assert wrong.status_code == 403
    assert wrong.text == "forbidden"

    missing = client.get("/ping?who=mom&signal=whatsapp")
    assert missing.status_code == 403

    for path in ("/status", "/labels", "/pings/mom", "/export.csv", "/labels.csv"):
        assert client.get(f"{path}?token=wrong").status_code == 403

    assert _count(conn) == before == 0
    assert conn.execute("SELECT COUNT(*) AS n FROM status_views").fetchone()["n"] == 0


def test_invalid_who_or_signal_is_400_and_not_stored(client: TestClient, conn):
    """Unknown people and unknown signals are rejected outright."""
    assert client.get(f"/ping?token={TOKEN}&who=neighbour&signal=whatsapp").status_code == 400
    assert client.get(f"/ping?token={TOKEN}&who=mom&signal=tiktok").status_code == 400
    assert client.get(f"/ping?token={TOKEN}&who=mom").status_code == 400
    assert _count(conn) == 0


def test_duplicate_within_60s_is_collapsed(client: TestClient, conn):
    """AC3: Shortcuts double-fires must not double-count."""
    client.get(f"/ping?token={TOKEN}&who=mom&signal=whatsapp")
    client.get(f"/ping?token={TOKEN}&who=mom&signal=whatsapp")
    assert _count(conn) == 1

    # A different signal in the same second is a separate row.
    client.get(f"/ping?token={TOKEN}&who=mom&signal=youtube")
    assert _count(conn) == 2


def test_ping_outside_dedupe_window_is_stored(conn):
    """Past the 60s window the same signal is a genuine new ping."""
    now = now_utc()
    assert db.insert_ping(conn, "dad", "news", fmt_utc(now - timedelta(seconds=90)), None)
    assert db.insert_ping(conn, "dad", "news", fmt_utc(now), None)
    assert _count(conn) == 2


def test_extra_query_params_are_never_stored(client: TestClient, conn):
    """AC4: the schema is the privacy promise — extras are dropped at the door."""
    resp = client.get(
        f"/ping?token={TOKEN}&who=mom&signal=whatsapp"
        "&location=12.97,77.59&text=hello%20amma&device=iPhone13&lat=1&lng=2"
    )
    assert resp.status_code == 200

    columns = {
        r["name"] for r in conn.execute("PRAGMA table_info(pings)").fetchall()
    }
    assert columns == EXPECTED_PING_COLUMNS

    raw = conn.execute("SELECT * FROM pings").fetchone()
    blob = " ".join(str(v) for v in tuple(raw))
    for leaked in ("12.97", "77.59", "hello", "iPhone13", "location", "lat", "lng"):
        assert leaked not in blob


def test_ip_is_hashed_not_stored(client: TestClient, conn):
    """ip_hash is one-way and never equals the address it came from."""
    client.get(
        f"/ping?token={TOKEN}&who=dad&signal=youtube",
        headers={"x-forwarded-for": "203.0.113.9"},
    )
    row = conn.execute("SELECT * FROM pings").fetchone()
    assert row["ip_hash"] and "203.0.113.9" not in row["ip_hash"]
    assert len(row["ip_hash"]) == 16
