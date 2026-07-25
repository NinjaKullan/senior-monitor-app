"""Shared fixtures: a temp SQLite DB and a client with the heartbeat loop off."""

from __future__ import annotations

from collections.abc import Iterator
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import connect, init_schema
from app.main import create_app

TOKEN = "test-token-not-a-real-secret"


class RecordingNotifier:
    """Stand-in for ntfy that records what the founder would have received."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, message: str) -> bool:
        self.messages.append(message)
        return True


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Isolated settings: temp DB, IST display, heartbeat loop disabled."""
    return Settings(
        ping_token=TOKEN,
        ntfy_topic="",
        db_path=str(tmp_path / "pilot.db"),
        tz_display="Asia/Kolkata",
        ip_hash_salt="test-salt",
        heartbeat_loop=False,
    )


@pytest.fixture
def notifier() -> RecordingNotifier:
    return RecordingNotifier()


@pytest.fixture
def client(settings: Settings, notifier: RecordingNotifier) -> Iterator[TestClient]:
    with TestClient(create_app(settings, notifier)) as c:
        yield c


@pytest.fixture
def conn(settings: Settings):
    """Direct DB handle for assertions (schema created by the app or here)."""
    c = connect(settings.db_path)
    init_schema(c)
    yield c
    c.close()


@pytest.fixture
def logged_labels(client: TestClient):
    """Satisfy the blinding gate so /status renders data."""

    def _log(note: str = "nothing unusual") -> None:
        for who in ("mom", "dad"):
            client.post(
                f"/labels?token={TOKEN}",
                content=urlencode({"who": who, "note": note}).encode(),
                headers={"content-type": "application/x-www-form-urlencoded"},
                follow_redirects=False,
            )

    return _log
