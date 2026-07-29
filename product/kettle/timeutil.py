"""UTC storage, per-parent local display.

The pilot had one timezone. The product has one per family, overridable per
parent, so every wall-clock decision has to name whose clock it is using.
Postgres holds `timestamptz`, so values arrive here already aware and the only
job left is choosing the right zone.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo


def now_utc() -> datetime:
    """Current server time, UTC, second resolution."""
    return datetime.now(tz=UTC).replace(microsecond=0)


def effective_tz(parent_tz: str | None, family_tz: str) -> str:
    """A parent's own timezone when set, otherwise the family's.

    This is what makes "Mom is visiting Texas" a data change rather than a code
    change: her checks move to Chicago while the rest of the family stays put.
    """
    return parent_tz or family_tz


def zone(tz_name: str) -> ZoneInfo:
    """Resolve a timezone name."""
    return ZoneInfo(tz_name)


def to_local(dt: datetime, tz_name: str) -> datetime:
    """Convert an aware datetime into a local zone."""
    return dt.astimezone(zone(tz_name))


def local_day(dt: datetime, tz_name: str) -> str:
    """The local calendar date (YYYY-MM-DD) an instant falls on."""
    return to_local(dt, tz_name).date().isoformat()


def local_hour(dt: datetime, tz_name: str) -> int:
    """Local wall-clock hour of an instant."""
    return to_local(dt, tz_name).hour


def local_day_bounds_utc(dt: datetime, tz_name: str) -> tuple[datetime, datetime]:
    """[start, end) of the local day containing `dt`, as aware UTC datetimes."""
    tz = zone(tz_name)
    day = dt.astimezone(tz).date()
    start = datetime.combine(day, time(0, 0), tzinfo=tz)
    return start.astimezone(UTC), (start + timedelta(days=1)).astimezone(UTC)


def local_time_on_day_utc(dt: datetime, tz_name: str, hour: int) -> datetime:
    """A wall-clock hour on the local day containing `dt`, as aware UTC."""
    tz = zone(tz_name)
    day = dt.astimezone(tz).date()
    return datetime.combine(day, time(hour, 0), tzinfo=tz).astimezone(UTC)


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
