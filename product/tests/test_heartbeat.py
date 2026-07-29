"""Acceptance criteria 5 and 6 — every check on its own subject's clock.

The clock is injected, so a single call can be simultaneously local noon in
Chennai and half past one in the morning in Chicago. That is the whole point:
one family's schedule must never be evaluated on another family's day.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import psycopg
import pytest

from kettle import db
from kettle.heartbeat import KIND_EVENING, KIND_INFRA, KIND_NOON, run_checks
from kettle.notify import NtfyNotifier
from kettle.provisioning import provision_family
from testsupport import BASE_URL

IST = ZoneInfo("Asia/Kolkata")
CHICAGO = ZoneInfo("America/Chicago")

# One August day. IST is UTC+5:30; Chicago is on CDT (UTC-5).
NOON_IST = datetime(2026, 8, 3, 12, 0, tzinfo=IST)  # 06:30 UTC
NOON_CHICAGO = datetime(2026, 8, 3, 12, 0, tzinfo=CHICAGO)  # 17:00 UTC
EVENING_IST = datetime(2026, 8, 3, 20, 0, tzinfo=IST)  # 14:30 UTC


def _fired(result) -> list[tuple[str, object]]:
    return [(f.kind, f.parent_id) for f in result]


def _ping(conn, parent_id, signal: str, when: datetime) -> None:
    db.insert_ping(conn, parent_id, signal, when, None)


def test_each_family_gets_its_own_local_noon(conn, settings, notifier):
    """AC5: two families, two timezones, two different moments of truth."""
    chennai = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    chicago = provision_family(
        conn, "Iyer", "America/Chicago", [("Patti", None)], base_url=BASE_URL
    )
    amma = chennai.parents[0].parent_id
    patti = chicago.parents[0].parent_id

    # 06:30 UTC: noon in Chennai, 01:30 in Chicago.
    assert _fired(run_checks(conn, settings, notifier, NOON_IST)) == [(KIND_NOON, amma)]

    # 17:00 UTC: noon in Chicago, half past ten at night in Chennai.
    assert _fired(run_checks(conn, settings, notifier, NOON_CHICAGO)) == [
        (KIND_NOON, patti)
    ]

    assert len(notifier.messages) == 2
    assert "Sharma / Amma" in notifier.messages[0]
    assert "Iyer / Patti" in notifier.messages[1]


def test_parent_tz_override_beats_the_family_tz(conn, settings, notifier):
    """AC6: Mom in Texas gets Chicago-noon while her family stays on IST."""
    family = provision_family(
        conn,
        "Sharma",
        "Asia/Kolkata",
        [("Amma", "America/Chicago"), ("Appa", None)],
        base_url=BASE_URL,
    )
    amma = family.parents[0].parent_id
    appa = family.parents[1].parent_id

    assert _fired(run_checks(conn, settings, notifier, NOON_IST)) == [(KIND_NOON, appa)]
    assert _fired(run_checks(conn, settings, notifier, NOON_CHICAGO)) == [
        (KIND_NOON, amma)
    ]


def test_morning_ping_stands_the_noon_check_down(conn, settings, notifier):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None), ("Appa", None)],
        base_url=BASE_URL,
    )
    amma, appa = family.parents
    _ping(conn, amma.parent_id, "whatsapp", datetime(2026, 8, 3, 7, 30, tzinfo=IST))

    assert _fired(run_checks(conn, settings, notifier, NOON_IST)) == [
        (KIND_NOON, appa.parent_id)
    ]


def test_only_alarm_grade_signals_count(conn, settings, notifier):
    """device_alive and charger events are plumbing; they cannot vouch for a person."""
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    amma = family.parents[0].parent_id
    _ping(conn, amma, "device_alive", datetime(2026, 8, 3, 7, 0, tzinfo=IST))
    _ping(conn, amma, "charge_on", datetime(2026, 8, 3, 8, 0, tzinfo=IST))

    assert _fired(run_checks(conn, settings, notifier, NOON_IST)) == [(KIND_NOON, amma)]


def test_late_night_ping_does_not_satisfy_the_next_morning(conn, settings, notifier):
    """The window opens at 05:00 local, so 23:50 the night before does not count."""
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    amma = family.parents[0].parent_id
    _ping(conn, amma, "whatsapp", datetime(2026, 8, 2, 23, 50, tzinfo=IST))

    assert _fired(run_checks(conn, settings, notifier, NOON_IST)) == [(KIND_NOON, amma)]

    _ping(conn, amma, "whatsapp", datetime(2026, 8, 4, 5, 30, tzinfo=IST))
    next_noon = NOON_IST + timedelta(days=1)
    assert _fired(run_checks(conn, settings, notifier, next_noon)) == []


def test_checks_are_idempotent_per_local_day(conn, settings, notifier):
    """Running every minute must not produce an alert every minute."""
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    assert len(run_checks(conn, settings, notifier, NOON_IST)) == 1
    assert run_checks(conn, settings, notifier, NOON_IST + timedelta(minutes=5)) == []
    assert run_checks(conn, settings, notifier, NOON_IST + timedelta(minutes=50)) == []
    assert conn.execute("select count(*) as n from ops_alerts").fetchone()["n"] == 1
    assert len(notifier.messages) == 1
    assert family.parents[0].display_name in notifier.messages[0]


def test_evening_escalates_only_an_existing_noon_alert(conn, settings, notifier):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    amma = family.parents[0].parent_id

    run_checks(conn, settings, notifier, NOON_IST)
    assert _fired(run_checks(conn, settings, notifier, EVENING_IST)) == [
        (KIND_EVENING, amma)
    ]
    assert "still no routine pings today" in notifier.messages[-1]

    # Dedupe applies to the escalation too.
    assert run_checks(conn, settings, notifier, EVENING_IST + timedelta(minutes=9)) == []


def test_evening_without_a_noon_alert_does_nothing(conn, settings, notifier):
    provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    # Nobody ran the noon check today, so there is no ops concern to escalate.
    assert run_checks(conn, settings, notifier, EVENING_IST) == []


def test_afternoon_ping_stands_the_evening_check_down(conn, settings, notifier):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    run_checks(conn, settings, notifier, NOON_IST)
    _ping(
        conn,
        family.parents[0].parent_id,
        "youtube",
        datetime(2026, 8, 3, 16, 0, tzinfo=IST),
    )
    assert run_checks(conn, settings, notifier, EVENING_IST) == []


def test_infra_check_stays_quiet_until_the_families_first_ping(conn, settings, notifier):
    """A family with no pings is one whose phones are not set up yet."""
    provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    for hour in (0, 9, 15, 23):
        fired = run_checks(
            conn, settings, notifier, datetime(2026, 8, 3, hour, 0, tzinfo=IST)
        )
        assert KIND_INFRA not in [f.kind for f in fired]
    assert all("Pipeline" not in m and "pipeline" not in m for m in notifier.messages)


def test_infra_check_fires_per_family_after_24h_of_silence(conn, settings, notifier):
    """AC5, pipeline half: one family goes dark, the other does not."""
    quiet = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    busy = provision_family(
        conn, "Nair", "Asia/Kolkata", [("Ammachi", None)], base_url=BASE_URL
    )
    _ping(conn, quiet.parents[0].parent_id, "whatsapp", datetime(2026, 8, 1, 6, 0, tzinfo=IST))
    _ping(conn, busy.parents[0].parent_id, "whatsapp", datetime(2026, 8, 3, 7, 0, tzinfo=IST))

    now = datetime(2026, 8, 3, 9, 0, tzinfo=IST)  # not noon: only the infra rule runs
    fired = run_checks(conn, settings, notifier, now)
    assert [f.kind for f in fired] == [KIND_INFRA]
    assert fired[0].family_id == quiet.family_id
    assert fired[0].parent_id is None
    assert "Sharma" in fired[0].detail

    # Once per family per local day.
    assert run_checks(conn, settings, notifier, now + timedelta(hours=2)) == []


def test_alert_message_handles_never_seen(conn, settings, notifier):
    provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    run_checks(conn, settings, notifier, NOON_IST)
    assert "last seen never" in notifier.messages[0]
    assert "tz Asia/Kolkata" in notifier.messages[0]


def test_alerts_reach_ntfy_over_real_http(conn, settings):
    """The ops topic is the only destination — asserted against actual HTTP."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200)

    notifier = NtfyNotifier(
        "ops-topic", client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )

    run_checks(conn, settings, notifier, NOON_IST)
    assert len(requests) == 1
    assert requests[0].url.path == "/ops-topic"
    assert "no routine pings this morning" in requests[0].content.decode()


def test_ops_alerts_are_the_only_thing_written(conn, settings, notifier):
    """Product law #3: the heartbeat writes ops rows and nothing family-facing."""
    provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    run_checks(conn, settings, notifier, NOON_IST)
    row = conn.execute("select * from ops_alerts").fetchone()
    assert row["kind"] == KIND_NOON
    assert conn.execute("select count(*) as n from pings").fetchone()["n"] == 0


@pytest.mark.parametrize(
    ("tz_name", "moment"),
    [("Asia/Kolkata", NOON_IST), ("America/Chicago", NOON_CHICAGO)],
)
def test_noon_hour_is_local_everywhere(
    conn: psycopg.Connection, settings, notifier, tz_name, moment
):
    """The same instant is noon in exactly one of these two families."""
    family = provision_family(
        conn, f"F-{tz_name}", tz_name, [("Elder", None)], base_url=BASE_URL
    )
    fired = run_checks(conn, settings, notifier, moment)
    assert [(f.kind, f.parent_id) for f in fired] == [
        (KIND_NOON, family.parents[0].parent_id)
    ]
