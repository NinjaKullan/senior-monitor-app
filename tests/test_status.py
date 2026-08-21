"""Acceptance criterion 5: the label-blinding interstitial."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi.testclient import TestClient

from app import db
from app.timeutil import date_local, local_time_today_utc, now_utc
from tests.conftest import TOKEN

FORM_HEADERS = {"content-type": "application/x-www-form-urlencoded"}
TZ = "Asia/Kolkata"


def _post_label(client: TestClient, who: str, note: str = "") -> None:
    client.post(
        f"/labels?token={TOKEN}",
        content=urlencode({"who": who, "note": note, "next": "/status"}).encode(),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )


def test_status_gates_on_todays_labels(client: TestClient, conn):
    """AC5: no labels → interstitial; both labelled → data."""
    client.get(f"/ping?token={TOKEN}&who=mom&signal=whatsapp")

    first = client.get(f"/status?token={TOKEN}")
    assert first.status_code == 200
    assert "Log today&#x27;s labels" in first.text or "Log today" in first.text
    assert "Recent pings" not in first.text

    _post_label(client, "mom")
    partial = client.get(f"/status?token={TOKEN}")
    assert "Recent pings" not in partial.text  # dad still unlabelled

    _post_label(client, "dad", "visitors")
    full = client.get(f"/status?token={TOKEN}")
    assert "Recent pings" in full.text
    assert "Heartbeat" in full.text
    assert "whatsapp" in full.text


def test_quick_button_records_nothing_unusual(client: TestClient, conn):
    """The one-tap button still writes a real label row."""
    client.post(
        f"/labels?token={TOKEN}",
        content=urlencode({"who": "mom", "note": "", "quick": "1"}).encode(),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )
    row = conn.execute("SELECT * FROM labels").fetchone()
    assert row["who"] == "mom"
    assert row["note"] == "nothing unusual"
    assert row["date_ist"] == date_local(now_utc(), "Asia/Kolkata")


def test_every_status_view_is_logged(client: TestClient, conn):
    """The blinding audit trail records looks, including blocked ones."""
    client.get(f"/status?token={TOKEN}")
    client.get(f"/status?token={TOKEN}")
    rows = conn.execute("SELECT * FROM status_views").fetchall()
    assert len(rows) == 2
    assert rows[0]["date_ist"] == date_local(now_utc(), "Asia/Kolkata")


def test_status_renders_the_device_alive_row(client: TestClient, logged_labels):
    """Spec 001a: the signal table is driven by SIGNALS, so the new row appears."""
    client.get(f"/ping?token={TOKEN}&who=mom&signal=device_alive")
    logged_labels()
    page = client.get(f"/status?token={TOKEN}").text
    # One row per person, whether or not that phone has ever sent the signal.
    assert page.count("device_alive") >= 2


def test_today_count_headline_is_alarm_grade_only(client: TestClient, conn, logged_labels):
    """DECISIONS item 10: plumbing must not inflate the per-person headline.

    Two whatsapp opens plus one device_alive timer ping reads as 2, not 3 —
    the number says how active the person was, and the timer says nothing
    about a person. The per-signal table below still shows every signal.
    """
    now = now_utc()
    for signal, hour in (("whatsapp", 9), ("whatsapp", 10), ("device_alive", 11)):
        db.insert_ping(conn, "mom", signal, local_time_today_utc(now, TZ, hour), None)

    logged_labels()
    page = client.get(f"/status?token={TOKEN}").text

    assert "Today: 2 routine pings" in page
    assert "Today: 3 routine pings" not in page
    assert page.count("Today: 0 routine pings") == 1  # dad, who sent nothing
    assert "device_alive" in page  # still listed in the per-signal table


def test_status_never_shows_the_ip_hash(client: TestClient, logged_labels):
    """ip_hash is ops-only and must never reach a page."""
    client.get(
        f"/ping?token={TOKEN}&who=dad&signal=news",
        headers={"x-forwarded-for": "203.0.113.9"},
    )
    logged_labels()
    page = client.get(f"/status?token={TOKEN}").text
    assert "ip_hash" not in page
    assert "203.0.113.9" not in page
