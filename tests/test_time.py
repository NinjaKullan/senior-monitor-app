"""IST/UTC handling, especially either side of IST midnight (UTC+05:30)."""

from __future__ import annotations

from datetime import UTC, datetime

from app import db
from app.heartbeat import KIND_NOON, run_checks
from app.timeutil import (
    date_local,
    display_tz,
    fmt_utc,
    humanize_gap,
    local_day_bounds_utc,
    local_time_today_utc,
    parse_utc,
)

IST = display_tz("Asia/Kolkata")


def _ping(conn, who: str, signal: str, when: datetime) -> None:
    db.insert_ping(conn, who, signal, fmt_utc(when), None)


class Silent:
    """Notifier that records nothing but satisfies the protocol."""

    def send(self, message: str) -> bool:
        return False


def test_late_evening_ist_ping_belongs_to_the_ist_day():
    """23:50 IST is still 'today' in IST even though UTC says 18:20."""
    late = datetime(2026, 7, 25, 23, 50, tzinfo=IST)
    assert fmt_utc(late) == "2026-07-25T18:20:00Z"
    assert date_local(late, "Asia/Kolkata") == "2026-07-25"


def test_just_after_ist_midnight_rolls_the_ist_day():
    """00:10 IST on the 26th is 18:40 UTC on the 25th — the label day is the 26th."""
    early = datetime(2026, 7, 26, 0, 10, tzinfo=IST)
    assert fmt_utc(early) == "2026-07-25T18:40:00Z"
    assert date_local(early, "Asia/Kolkata") == "2026-07-26"


def test_ist_day_bounds_are_utc_offset_by_five_thirty():
    start, end = local_day_bounds_utc("2026-07-26", "Asia/Kolkata")
    assert start == "2026-07-25T18:30:00Z"
    assert end == "2026-07-26T18:30:00Z"


def test_morning_window_anchors_to_the_ist_day():
    """05:00 IST on the 26th, computed from an instant just after IST midnight."""
    early = datetime(2026, 7, 26, 0, 10, tzinfo=IST)
    assert local_time_today_utc(early, "Asia/Kolkata", 5) == "2026-07-25T23:30:00Z"


def test_utc_round_trip():
    stored = fmt_utc(datetime(2026, 7, 25, 18, 20, tzinfo=UTC))
    assert parse_utc(stored) == datetime(2026, 7, 25, 18, 20, tzinfo=UTC)


def test_ping_counts_use_ist_days_not_utc_days(conn):
    """A 23:50 IST ping counts on its IST day, not the UTC one."""
    _ping(conn, "mom", "whatsapp", datetime(2026, 7, 25, 23, 50, tzinfo=IST))
    start_25, end_25 = local_day_bounds_utc("2026-07-25", "Asia/Kolkata")
    start_26, end_26 = local_day_bounds_utc("2026-07-26", "Asia/Kolkata")
    assert db.count_pings_between(conn, "mom", start_25, end_25) == 1
    assert db.count_pings_between(conn, "mom", start_26, end_26) == 0


def test_late_night_ping_does_not_satisfy_next_mornings_heartbeat(settings, conn):
    """A 23:50 IST ping on the 25th must not silence the noon check on the 26th."""
    _ping(conn, "dad", "whatsapp", datetime(2026, 7, 25, 23, 50, tzinfo=IST))
    _ping(conn, "mom", "whatsapp", datetime(2026, 7, 26, 8, 0, tzinfo=IST))

    fired = run_checks(conn, settings, Silent(), datetime(2026, 7, 26, 12, 0, tzinfo=IST))
    assert fired == [KIND_NOON]
    row = conn.execute("SELECT * FROM alerts").fetchone()
    assert row["who"] == "dad"


def test_early_morning_ping_does_satisfy_the_noon_check(settings, conn):
    """05:30 IST is inside the morning window and stands the check down."""
    for who in ("mom", "dad"):
        _ping(conn, who, "news", datetime(2026, 7, 26, 5, 30, tzinfo=IST))
    assert run_checks(conn, settings, Silent(), datetime(2026, 7, 26, 12, 0, tzinfo=IST)) == []


def test_humanize_gap():
    assert humanize_gap(45) == "45s"
    assert humanize_gap(60 * 45) == "45m"
    assert humanize_gap(3600 * 2 + 60 * 14) == "2h 14m"
    assert humanize_gap(86400 * 3 + 3600 * 4) == "3d 4h"
    assert humanize_gap(-5) == "0s"
