"""The ask template's category watch (DECISIONS 262, item 1 of the 263 brief).

Meta can re-review v7 into Marketing without telling anyone, and a
non-Utility template stops US delivery with no error on our side. The watch
asks the Content API once a day and raises one founder-only ops alert per
day when the answer is anything but approved/utility. A fetch that fails is
a log line and a retry later, never an alert and never a crash.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import httpx

from kettle.template_watch import (
    KIND_TEMPLATE_CATEGORY,
    RETRY_AFTER,
    WatchState,
    check_once,
    maybe_check,
)

SID = "HX1ebee977bfd531bf7fdee2bf0d1484ad"
NOW = datetime(2026, 9, 7, 9, 0, tzinfo=UTC)


def _settings(settings):
    return replace(
        settings,
        twilio_account_sid="ACtest",
        twilio_auth_token="token",
        twilio_ask_content_sid=SID,
    )


def _client(handler) -> tuple[httpx.Client, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    return httpx.Client(transport=httpx.MockTransport(record)), seen


def answering(status: str, category: str):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"whatsapp": {"status": status, "category": category}}
        )

    return handler


def _alerts(conn) -> list[dict]:
    return conn.execute(
        "select family_id, parent_id, kind, detail from ops_alerts order by id"
    ).fetchall()


def test_utility_raises_nothing(conn, settings, notifier):
    client, seen = _client(answering("approved", "UTILITY"))
    standing = check_once(conn, _settings(settings), notifier, NOW, client)
    assert standing is not None and standing.is_utility
    assert _alerts(conn) == []
    assert notifier.messages == []
    # One authenticated GET at the approval endpoint for THIS sid.
    [request] = seen
    assert request.method == "GET"
    assert request.url.path == f"/v1/Content/{SID}/ApprovalRequests"
    assert request.headers.get("authorization", "").startswith("Basic ")


def test_marketing_raises_one_alert_and_a_second_pass_adds_none(conn, settings, notifier):
    client, _ = _client(answering("approved", "MARKETING"))
    cfg = _settings(settings)
    check_once(conn, cfg, notifier, NOW, client)
    check_once(conn, cfg, notifier, NOW + timedelta(hours=6), client)

    [alert] = _alerts(conn)
    assert alert["kind"] == KIND_TEMPLATE_CATEGORY
    assert alert["family_id"] is None and alert["parent_id"] is None
    assert SID in alert["detail"]
    assert "approved/MARKETING" in alert["detail"]
    assert len(notifier.messages) == 1

    # The next UTC day is a fresh alert: the founder is reminded daily, not once.
    check_once(conn, cfg, notifier, NOW + timedelta(days=1), client)
    assert len(_alerts(conn)) == 2


def test_a_rejected_template_alerts_too(conn, settings, notifier):
    client, _ = _client(answering("rejected", "UTILITY"))
    check_once(conn, _settings(settings), notifier, NOW, client)
    [alert] = _alerts(conn)
    assert "rejected/UTILITY" in alert["detail"]


def test_a_failed_fetch_logs_and_skips(conn, settings, notifier, caplog):
    def down(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route")

    client, _ = _client(down)
    with caplog.at_level("WARNING", logger="kettle.template_watch"):
        assert check_once(conn, _settings(settings), notifier, NOW, client) is None
    assert _alerts(conn) == []
    assert notifier.messages == []
    assert any("could not fetch" in r.message for r in caplog.records)


def test_a_500_or_a_malformed_body_is_a_skip_not_an_alert(conn, settings, notifier):
    client, _ = _client(lambda _: httpx.Response(500, json={"message": "nope"}))
    assert check_once(conn, _settings(settings), notifier, NOW, client) is None
    client, _ = _client(lambda _: httpx.Response(200, json={"sid": SID}))
    assert check_once(conn, _settings(settings), notifier, NOW, client) is None
    assert _alerts(conn) == []


def test_unconfigured_is_a_no_op(conn, settings, notifier):
    # No SID (the sandbox era) or no credentials: nothing to watch, no call.
    client, seen = _client(answering("approved", "UTILITY"))
    assert check_once(conn, settings, notifier, NOW, client) is None
    assert seen == []


def test_the_loop_gate_fetches_once_a_day_and_retries_a_failure_hourly(
    conn, settings, notifier
):
    cfg = _settings(settings)
    state = WatchState()
    client, seen = _client(answering("approved", "UTILITY"))

    # Sixty passes inside one day: one fetch.
    for minute in range(60):
        maybe_check(conn, cfg, notifier, state, NOW + timedelta(minutes=minute), client)
    assert len(seen) == 1
    assert state.checked_day == NOW.date()

    # The next day fetches again.
    maybe_check(conn, cfg, notifier, state, NOW + timedelta(days=1), client)
    assert len(seen) == 2

    # A failure does not claim the day; it is retried after RETRY_AFTER, not
    # every minute.
    failing, attempts = _client(lambda _: httpx.Response(503))
    fresh = WatchState()
    day3 = NOW + timedelta(days=2)
    maybe_check(conn, cfg, notifier, fresh, day3, failing)
    maybe_check(conn, cfg, notifier, fresh, day3 + timedelta(minutes=1), failing)
    assert len(attempts) == 1
    assert fresh.checked_day is None
    maybe_check(conn, cfg, notifier, fresh, day3 + RETRY_AFTER, failing)
    assert len(attempts) == 2


def test_the_heartbeat_state_carries_the_watch():
    # The loop hands its own state to the watch (heartbeat_loop); a
    # HeartbeatState without it would mean the gate resets every pass.
    from kettle.heartbeat import HeartbeatState

    assert isinstance(HeartbeatState().template_watch, WatchState)
