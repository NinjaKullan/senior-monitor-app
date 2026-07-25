"""UTC storage, IST display. All conversion lives here."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

# Stored format: sortable, unambiguous, lexicographically comparable in SQLite.
UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def now_utc() -> datetime:
    """Current server time, UTC, second resolution."""
    return datetime.now(tz=UTC).replace(microsecond=0)


def fmt_utc(dt: datetime) -> str:
    """Serialize an aware datetime to the stored UTC string format."""
    return dt.astimezone(UTC).strftime(UTC_FORMAT)


def parse_utc(value: str) -> datetime:
    """Parse a stored UTC string back into an aware datetime."""
    return datetime.strptime(value, UTC_FORMAT).replace(tzinfo=UTC)


def display_tz(name: str) -> ZoneInfo:
    """Resolve the display timezone (IST for the pilot)."""
    return ZoneInfo(name)


def to_display(dt: datetime, tz_name: str) -> datetime:
    """Convert an aware datetime into the display timezone."""
    return dt.astimezone(display_tz(tz_name))


def fmt_display(dt: datetime, tz_name: str) -> str:
    """Human-readable local time, e.g. '2026-07-25 14:45 IST'."""
    local = to_display(dt, tz_name)
    return local.strftime("%Y-%m-%d %H:%M")


def fmt_display_iso(dt: datetime, tz_name: str) -> str:
    """ISO-8601 local time with offset, for CSV export."""
    return to_display(dt, tz_name).isoformat()


def date_local(dt: datetime, tz_name: str) -> str:
    """The local calendar date (YYYY-MM-DD) an instant falls on."""
    return to_display(dt, tz_name).date().isoformat()


def local_day_bounds_utc(date_str: str, tz_name: str) -> tuple[str, str]:
    """[start, end) of a local calendar day, as stored UTC strings."""
    tz = display_tz(tz_name)
    day = datetime.strptime(date_str, "%Y-%m-%d").date()
    start = datetime.combine(day, time(0, 0), tzinfo=tz)
    end = start + timedelta(days=1)
    return fmt_utc(start), fmt_utc(end)


def local_time_today_utc(dt: datetime, tz_name: str, hour: int, minute: int = 0) -> str:
    """A wall-clock time on the local day containing `dt`, as a stored UTC string."""
    tz = display_tz(tz_name)
    local_day = dt.astimezone(tz).date()
    moment = datetime.combine(local_day, time(hour, minute), tzinfo=tz)
    return fmt_utc(moment)


def humanize_gap(seconds: float) -> str:
    """Compact elapsed-time phrasing: '2h 14m', '3d 4h', '45m', '12s'."""
    total = int(max(seconds, 0))
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m"
    return f"{secs}s"
