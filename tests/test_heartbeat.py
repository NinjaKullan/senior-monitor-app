"""Acceptance criterion 6: the founder-only heartbeat monitor.

Clock is injected (no freezegun needed) and ntfy is a mocked HTTP transport, so
these tests assert on real POSTs, not on a stubbed sender.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import httpx
import pytest

from app import db
from app.heartbeat import KIND_EVENING, KIND_INFRA, KIND_NOON, run_checks
from app.notify import NtfyNotifier
from app.timeutil import display_tz, fmt_utc

IST = display_tz("Asia/Kolkata")


class FakeNtfy:
    """A real NtfyNotifier wired to a mock transport that counts POSTs."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return httpx.Response(200)

        self.notifier = NtfyNotifier(
            "founder-topic", client=httpx.Client(transport=httpx.MockTransport(handler))
        )

    @property
    def bodies(self) -> list[str]:
        return [r.content.decode() for r in self.requests]


@pytest.fixture
def ntfy() -> FakeNtfy:
    return FakeNtfy()


def _ping(conn, who: str, signal: str, when: datetime) -> None:
    db.insert_ping(conn, who, signal, fmt_utc(when), None)


def _alerts(conn) -> list:
    return conn.execute("SELECT * FROM alerts ORDER BY id").fetchall()


def test_noon_check_fires_once_for_silent_person(settings, conn, ntfy):
    """AC6: 12:01 IST, dad silent since 05:00 → one POST, one row, then nothing."""
    noon = datetime(2026, 7, 25, 12, 1, tzinfo=IST)
    _ping(conn, "mom", "whatsapp", datetime(2026, 7, 25, 9, 0, tzinfo=IST))

    fired = run_checks(conn, settings, ntfy.notifier, noon)
    assert fired == [KIND_NOON]
    assert len(ntfy.requests) == 1
    assert ntfy.requests[0].url.path == "/founder-topic"
    assert "dad: no routine pings this morning" in ntfy.bodies[0]

    rows = _alerts(conn)
    assert len(rows) == 1
    assert (rows[0]["kind"], rows[0]["who"]) == (KIND_NOON, "dad")

    # Dedupe: max one per (kind, who) per IST day.
    assert run_checks(conn, settings, ntfy.notifier, noon + timedelta(minutes=5)) == []
    assert len(ntfy.requests) == 1
    assert len(_alerts(conn)) == 1


def test_noon_check_silent_when_both_pinged(settings, conn, ntfy):
    """A normal morning produces no alert at all."""
    for who in ("mom", "dad"):
        _ping(conn, who, "whatsapp", datetime(2026, 7, 25, 7, 30, tzinfo=IST))
    assert run_checks(conn, settings, ntfy.notifier, datetime(2026, 7, 25, 12, 0, tzinfo=IST)) == []
    assert ntfy.requests == []


def test_charger_pings_are_not_alarm_grade(settings, conn, ntfy):
    """Corroborating signals must not suppress the morning check."""
    _ping(conn, "mom", "whatsapp", datetime(2026, 7, 25, 8, 0, tzinfo=IST))
    _ping(conn, "dad", "charge_on", datetime(2026, 7, 25, 8, 0, tzinfo=IST))
    fired = run_checks(conn, settings, ntfy.notifier, datetime(2026, 7, 25, 12, 0, tzinfo=IST))
    assert fired == [KIND_NOON]
    assert _alerts(conn)[0]["who"] == "dad"


def test_device_alive_is_not_alarm_grade(settings, conn, ntfy):
    """Spec 001a: a day of timer pings alone still fires the noon check.

    device_alive proves the phone is on and the Shortcuts engine is alive. It
    involves no human, so it must never stand in for one.
    """
    for hour in (7, 8, 11):
        _ping(conn, "dad", "device_alive", datetime(2026, 7, 25, hour, 0, tzinfo=IST))
    _ping(conn, "mom", "whatsapp", datetime(2026, 7, 25, 9, 0, tzinfo=IST))

    fired = run_checks(conn, settings, ntfy.notifier, datetime(2026, 7, 25, 12, 0, tzinfo=IST))
    assert fired == [KIND_NOON]
    rows = _alerts(conn)
    assert len(rows) == 1
    assert (rows[0]["kind"], rows[0]["who"]) == (KIND_NOON, "dad")


def test_device_alive_keeps_the_pipeline_alive_for_the_infra_check(settings, conn, ntfy):
    """Spec 001a: timer pings flowing means the pipeline is fine, whatever the apps do.

    Apps silent + device_alive flowing is the diagnostic this signal exists for:
    the person is quiet or their app automations are dead, but the server, the
    network and the Shortcuts engine are all working — so no 🔧 infra alert.
    """
    # Last deliberate app open was three days ago; the daily timer never stopped.
    _ping(conn, "mom", "whatsapp", datetime(2026, 7, 22, 8, 0, tzinfo=IST))
    for day in (23, 24, 25):
        for who in ("mom", "dad"):
            _ping(conn, who, "device_alive", datetime(2026, 7, day, 7, 0, tzinfo=IST))

    assert run_checks(conn, settings, ntfy.notifier, datetime(2026, 7, 25, 9, 0, tzinfo=IST)) == []
    assert ntfy.requests == []

    # The person-level checks still fire; only the pipeline is judged healthy.
    fired = run_checks(conn, settings, ntfy.notifier, datetime(2026, 7, 25, 12, 0, tzinfo=IST))
    assert fired == [KIND_NOON, KIND_NOON]
    assert KIND_INFRA not in fired
    assert all("Pipeline silent" not in body for body in ntfy.bodies)


def test_evening_check_only_escalates_an_existing_noon_alert(settings, conn, ntfy):
    """20:00 IST fires only if noon already fired and the day is still silent."""
    _ping(conn, "mom", "whatsapp", datetime(2026, 7, 25, 9, 0, tzinfo=IST))
    run_checks(conn, settings, ntfy.notifier, datetime(2026, 7, 25, 12, 0, tzinfo=IST))

    evening = datetime(2026, 7, 25, 20, 5, tzinfo=IST)
    assert run_checks(conn, settings, ntfy.notifier, evening) == [KIND_EVENING]
    assert len(ntfy.requests) == 2
    assert "dad: still no routine pings today" in ntfy.bodies[1]

    # Dedupe again.
    assert run_checks(conn, settings, ntfy.notifier, evening + timedelta(minutes=10)) == []
    assert len(ntfy.requests) == 2


def test_evening_check_without_noon_alert_does_nothing(settings, conn, ntfy):
    """No noon concern → no evening escalation, even if the day looks quiet."""
    _ping(conn, "mom", "whatsapp", datetime(2026, 7, 25, 19, 0, tzinfo=IST))
    _ping(conn, "dad", "news", datetime(2026, 7, 25, 19, 0, tzinfo=IST))
    assert run_checks(conn, settings, ntfy.notifier, datetime(2026, 7, 25, 20, 0, tzinfo=IST)) == []


def test_evening_check_stands_down_if_person_pinged_after_noon(settings, conn, ntfy):
    """A late-afternoon ping resolves the ops concern without any further alert."""
    _ping(conn, "mom", "whatsapp", datetime(2026, 7, 25, 9, 0, tzinfo=IST))
    run_checks(conn, settings, ntfy.notifier, datetime(2026, 7, 25, 12, 0, tzinfo=IST))
    _ping(conn, "dad", "youtube", datetime(2026, 7, 25, 16, 0, tzinfo=IST))
    assert run_checks(conn, settings, ntfy.notifier, datetime(2026, 7, 25, 20, 0, tzinfo=IST)) == []
    assert len(ntfy.requests) == 1


def test_infra_check_fires_when_pipeline_is_silent(settings, conn, ntfy):
    """Nothing from any device in 24h → one pipeline alert per IST day."""
    _ping(conn, "mom", "whatsapp", datetime(2026, 7, 24, 6, 0, tzinfo=IST))
    now = datetime(2026, 7, 25, 9, 0, tzinfo=IST)

    assert run_checks(conn, settings, ntfy.notifier, now) == [KIND_INFRA]
    assert "Pipeline silent 24h" in ntfy.bodies[0]
    assert _alerts(conn)[0]["who"] == ""

    assert run_checks(conn, settings, ntfy.notifier, now + timedelta(hours=1)) == []
    assert len(ntfy.requests) == 1


def test_infra_check_stays_quiet_until_the_first_ever_ping(settings, conn, ntfy):
    """An empty DB means 'not set up yet', not 'broken' — no infra alert at any hour."""
    for hour in (0, 9, 12, 20, 23):
        fired = run_checks(
            conn, settings, ntfy.notifier, datetime(2026, 7, 25, hour, 0, tzinfo=IST)
        )
        assert KIND_INFRA not in fired

    assert [r["kind"] for r in _alerts(conn)] == [KIND_NOON, KIND_NOON, KIND_EVENING, KIND_EVENING]
    assert all("Pipeline silent" not in body for body in ntfy.bodies)

    # Once a ping has arrived, 24h of silence does fire.
    _ping(conn, "mom", "whatsapp", datetime(2026, 7, 26, 6, 0, tzinfo=IST))
    later = datetime(2026, 7, 27, 9, 0, tzinfo=IST)
    assert run_checks(conn, settings, ntfy.notifier, later) == [KIND_INFRA]
    assert "Pipeline silent 24h" in ntfy.bodies[-1]


def test_infra_check_quiet_when_pings_are_recent(settings, conn, ntfy):
    _ping(conn, "dad", "news", datetime(2026, 7, 25, 7, 0, tzinfo=IST))
    assert run_checks(conn, settings, ntfy.notifier, datetime(2026, 7, 25, 9, 0, tzinfo=IST)) == []


def test_log_only_when_no_topic_configured(settings, conn):
    """NTFY_TOPIC unset → alert is still recorded, nothing is sent."""
    silent = NtfyNotifier("")
    fired = run_checks(conn, settings, silent, datetime(2026, 7, 25, 12, 0, tzinfo=IST))
    assert KIND_NOON in fired
    assert len(_alerts(conn)) >= 1


def test_alert_message_handles_never_seen(settings, conn, ntfy):
    """A person with no history reads as 'never', not a crash."""
    _ping(conn, "mom", "whatsapp", datetime(2026, 7, 25, 9, 0, tzinfo=IST))
    run_checks(conn, settings, ntfy.notifier, datetime(2026, 7, 25, 12, 0, tzinfo=IST))
    assert "last seen never" in ntfy.bodies[0]
