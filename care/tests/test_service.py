"""The service around the tools (spec 021 §6; acceptance §8.9, §8.11, §8.13)."""

from __future__ import annotations

import json
import logging

from fastapi.testclient import TestClient

from care import cms
from care import copy as text
from care.app import HOUR, RateLimiter, create_app
from conftest import call


def rpc(c: TestClient, method: str, params: dict | None = None) -> dict:
    response = c.post(
        "/mcp",
        headers={"accept": "application/json, text/event-stream",
                 "content-type": "application/json"},
        content=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}),
        follow_redirects=False,
    )
    assert response.status_code == 200, response.text
    return response.json()["result"]


# --- §8.13 instructions and descriptions ----------------------------------------------


def test_the_instructions_line_is_section_10s(client):
    result = rpc(
        client,
        "initialize",
        {"protocolVersion": "2025-06-18", "capabilities": {},
         "clientInfo": {"name": "test", "version": "0"}},
    )
    assert result["instructions"] == text.SERVER_INSTRUCTIONS
    assert result["serverInfo"]["name"] == "Care Compare by HeyKettle"


def test_three_tools_read_only_with_section_10_descriptions(client):
    tools = {t["name"]: t for t in rpc(client, "tools/list")["tools"]}
    assert set(tools) == {"find_care", "care_details", "compare_care"}
    assert tools["find_care"]["description"] == text.TOOL_FIND
    assert tools["care_details"]["description"] == text.TOOL_DETAILS
    assert tools["compare_care"]["description"] == text.TOOL_COMPARE
    for tool in tools.values():
        assert tool["annotations"]["readOnlyHint"] is True
        assert tool["annotations"]["openWorldHint"] is False
    assert set(tools["find_care"]["inputSchema"]["required"]) == {"kind", "zip"}
    assert set(tools["care_details"]["inputSchema"]["required"]) == {"name", "zip"}
    assert set(tools["compare_care"]["inputSchema"]["required"]) == {"names", "zip"}


# --- §6 no auth ---------------------------------------------------------------------------


def test_no_oauth_metadata_and_no_token_needed(client):
    for path in (
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-protected-resource/mcp",
        "/.well-known/oauth-authorization-server",
        "/.well-known/openid-configuration",
        "/register",
        "/authorize",
        "/token",
    ):
        assert client.get(path).status_code == 404, path
    assert "www-authenticate" not in {
        k.lower() for k in client.post("/mcp", json={}).headers
    }
    # /mcp answers directly, not with a redirect to /mcp/.
    assert call(client, "find_care", kind="x", zip="27502") == text.KIND_UNKNOWN


def test_root_and_healthz(client, fake):
    assert client.get("/").text == "ok\n"
    assert client.get("/healthz").json() == {"ok": True}
    assert fake.requests == []  # a health check reads nothing


# --- §8.9 the rate limit --------------------------------------------------------------------


def test_the_61st_call_in_an_hour_is_refused_and_another_ip_is_not(fake, clock, centroids):
    now = [0.0]
    limiter = RateLimiter(clock=lambda: now[0])
    app = create_app(cms.make_client(fake), centroids, clock, limiter)
    with TestClient(app) as c:
        for i in range(60):
            now[0] = i * 10.0
            assert call(c, "find_care", ip="198.51.100.1", kind="x", zip="1") == (
                text.KIND_UNKNOWN
            ), i
        assert call(c, "care_details", ip="198.51.100.1", name="a", zip="1") == text.RATE_LIMITED
        assert call(c, "compare_care", ip="198.51.100.1", names=["a"], zip="1") == (
            text.RATE_LIMITED
        )
        assert call(c, "find_care", ip="198.51.100.2", kind="x", zip="1") == text.KIND_UNKNOWN
        # The window slides: an hour after the first call, one more is allowed.
        now[0] = HOUR
        assert call(c, "find_care", ip="198.51.100.1", kind="x", zip="1") == text.KIND_UNKNOWN
        assert call(c, "find_care", ip="198.51.100.1", kind="x", zip="1") == text.RATE_LIMITED


def test_a_refusal_is_not_counted_against_the_hour():
    now = [0.0]
    limiter = RateLimiter(limit=2, clock=lambda: now[0])
    assert limiter.allow("a") and limiter.allow("a")
    for _ in range(5):
        assert not limiter.allow("a")
    now[0] = HOUR
    assert limiter.allow("a") and limiter.allow("a") and not limiter.allow("a")


def test_idle_addresses_are_forgotten():
    now = [0.0]
    limiter = RateLimiter(clock=lambda: now[0])
    limiter.allow("a")
    now[0] = HOUR + 1
    limiter.allow("b")
    assert set(limiter.calls) == {"b"}


# --- §8.11 logging ----------------------------------------------------------------------


def test_a_call_logs_neither_the_zip_nor_the_name(client, caplog):
    caplog.set_level(logging.DEBUG)
    call(client, "find_care", ip="192.0.2.44", kind="nursing home", zip="28273")
    call(client, "care_details", ip="192.0.2.44", name="Queen City Nursing", zip="28273")
    call(client, "compare_care", ip="192.0.2.44", names=["Fort Mill Place", "Zebra"],
         zip="28273")
    logged = "\n".join(
        f"{r.name} {r.getMessage()} {r.args!r}" for r in caplog.records
    ).lower()
    for secret in ("28273", "queen city", "fort mill", "zebra", "192.0.2.44",
                   "conditions", "data.cms.gov", "=sc", "=nc"):
        assert secret not in logged, secret
    ours = [r.getMessage() for r in caplog.records if r.name == "care"]
    assert ours == ["find_care ok 2", "care_details ok 1", "compare_care refused 1"]


def test_status_words(client, caplog, fake):
    caplog.set_level(logging.INFO, logger="care")
    fake.down = True
    call(client, "find_care", kind="home health", zip="28273")
    fake.down = False
    call(client, "find_care", kind="nursing home", zip="27936", miles=1)
    call(client, "care_details", name="Sunny Acres", zip="27502")
    call(client, "find_care", kind="x", zip="27502")
    ours = [r.getMessage() for r in caplog.records if r.name == "care"]
    assert ours == [
        "find_care cms_down 0", "find_care none 0", "care_details none 0", "find_care refused 0"
    ]
