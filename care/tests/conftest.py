"""Recorded CMS answers, served with no network (spec 021 §8.14).

The fixtures in `fixtures/` are hand-built in the exact §5 column shape (plus
a few of the columns the real datastore also sends, the CCN among them, to
prove they are dropped at the door): data.cms.gov was unreachable from the
build box. `FakeCms` answers the two URL shapes `cms.py` asks for and
records every request, so a test can count them.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from care import cms
from care.app import RateLimiter, create_app
from care.geo import Centroids

FIXTURES = Path(__file__).resolve().parent / "fixtures"
START = datetime(2026, 9, 23, 15, 0, tzinfo=UTC)


class Clock:
    def __init__(self, now: datetime = START) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **delta: float) -> None:
        self.now += timedelta(**delta)


class FakeCms(httpx.AsyncBaseTransport):
    """data.cms.gov from fixtures. `down` makes every request a 500;
    `extra` adds synthetic rows for (dataset, state)."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.down = False
        self.extra: dict[tuple[str, str], list[dict[str, Any]]] = {}

    def rows(self, dataset: str, state: str) -> list[dict[str, Any]]:
        if (dataset, state) in self.extra:
            return self.extra[(dataset, state)]
        path = FIXTURES / f"datastore_{dataset}_{state}.json"
        return json.loads(path.read_text())["results"] if path.exists() else []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.down:
            return httpx.Response(500, json={"message": "down"})
        parts = request.url.path.split("/")
        if "metastore" in parts:
            dataset = parts[-1]
            return httpx.Response(
                200, content=(FIXTURES / f"metastore_{dataset}.json").read_bytes()
            )
        dataset = parts[-2]
        q = request.url.params
        state = q["conditions[0][value]"]
        assert q["conditions[0][property]"] == "state"
        limit, offset = int(q["limit"]), int(q["offset"])
        page = self.rows(dataset, state)[offset : offset + limit]
        return httpx.Response(200, json={"results": page, "count": len(page)})

    def data_requests(self) -> list[httpx.Request]:
        return [r for r in self.requests if "datastore" in r.url.path]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """§8.14: the suite runs on fixtures only. Any socket that tries to
    reach anywhere fails the test that opened it."""
    import socket

    def refuse(*args: Any, **kwargs: Any) -> None:
        raise AssertionError(f"the suite tried to reach the network: {args[1:]}")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)


@pytest.fixture
def fake() -> FakeCms:
    return FakeCms()


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def centroids() -> Centroids:
    return Centroids.load(FIXTURES / "zcta.csv")


@pytest.fixture
def client(fake: FakeCms, clock: Clock, centroids: Centroids):
    app = create_app(cms.make_client(fake), centroids, clock, RateLimiter(limit=10_000))
    with TestClient(app) as c:
        yield c


def call(c: TestClient, tool: str, ip: str = "203.0.113.7", **arguments: Any) -> str:
    """One tools/call over the real /mcp transport; the tool's text back."""
    response = c.post(
        "/mcp",
        headers={
            "accept": "application/json, text/event-stream",
            "content-type": "application/json",
            "fly-client-ip": ip,
        },
        content=json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool, "arguments": arguments},
            }
        ),
        follow_redirects=False,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "error" not in body, body
    result = body["result"]
    assert not result.get("isError"), result
    return "".join(part["text"] for part in result["content"] if part["type"] == "text")


@pytest.fixture
def ask(client: TestClient) -> Callable[..., str]:
    def go(tool: str, **arguments: Any) -> str:
        return call(client, tool, **arguments)

    return go
