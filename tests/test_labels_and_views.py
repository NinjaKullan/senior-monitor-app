"""Label log, the Dad-transparency ping view, and /healthz."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.conftest import TOKEN

FORM_HEADERS = {"content-type": "application/x-www-form-urlencoded"}


def test_labels_add_and_view(client: TestClient, conn):
    """POST adds a label and redirects; GET lists them."""
    resp = client.post(
        f"/labels?token={TOKEN}",
        content=urlencode({"who": "dad", "note": "temple festival"}).encode(),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"].startswith("/status?token=")

    assert conn.execute("SELECT COUNT(*) AS n FROM labels").fetchone()["n"] == 1
    assert "temple festival" in client.get(f"/labels?token={TOKEN}").text


def test_labels_via_get_params(client: TestClient, conn):
    """A label can also be filed with a plain GET (Shortcuts-friendly)."""
    client.get(f"/labels?token={TOKEN}&who=mom&note=travel", follow_redirects=False)
    row = conn.execute("SELECT * FROM labels").fetchone()
    assert (row["who"], row["note"]) == ("mom", "travel")


def test_labels_reject_unknown_person(client: TestClient):
    assert client.get(f"/labels?token={TOKEN}&who=sister&note=x").status_code == 400


def test_labels_csv(client: TestClient):
    client.get(f"/labels?token={TOKEN}&who=mom&note=quiet%20day", follow_redirects=False)
    resp = client.get(f"/labels.csv?token={TOKEN}")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    lines = resp.text.strip().splitlines()
    assert lines[0] == "date_ist,who,note,created_utc,created_ist"
    assert "quiet day" in lines[1]


def test_pings_view_shows_only_time_and_signal(client: TestClient):
    """The transparency view: 'you can see every ping it has ever sent'."""
    client.get(f"/ping?token={TOKEN}&who=dad&signal=whatsapp")
    resp = client.get(f"/pings/dad?token={TOKEN}")
    assert resp.status_code == 200
    assert "whatsapp" in resp.text
    assert "Signal" in resp.text and "Time (IST)" in resp.text
    assert "ip_hash" not in resp.text


def test_pings_view_unknown_person_404(client: TestClient):
    assert client.get(f"/pings/nobody?token={TOKEN}").status_code == 404


def test_healthz_needs_no_token(client: TestClient):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"db": True}


def test_fresh_empty_volume_boots_and_creates_schema(tmp_path, notifier):
    """AC8 (local proxy for the Fly deploy): empty volume → schema → healthz green."""
    db_path = tmp_path / "empty-volume" / "pilot.db"
    assert not db_path.exists()
    cfg = Settings(
        ping_token=TOKEN,
        ntfy_topic="",
        db_path=str(db_path),
        tz_display="Asia/Kolkata",
        ip_hash_salt="salt",
        heartbeat_loop=False,
    )
    with TestClient(create_app(cfg, notifier)) as fresh:
        assert fresh.get("/healthz").json() == {"db": True}
        assert fresh.get(f"/ping?token={TOKEN}&who=mom&signal=news").status_code == 200
    assert db_path.exists()
