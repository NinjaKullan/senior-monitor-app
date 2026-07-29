"""Postgres access. Plain SQL, no ORM (spec 002 §1).

Every write in this module names its columns explicitly. There is no
pass-through of caller-supplied fields anywhere: the schema is the privacy
promise, and it is enforced here by there being no code that could store
anything else.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any

import psycopg
from psycopg.rows import dict_row

Row = dict[str, Any]


def connect(database_url: str) -> psycopg.Connection:
    """Open a connection that returns dict rows and commits each statement."""
    return psycopg.connect(database_url, row_factory=dict_row, autocommit=True)


def healthy(conn: psycopg.Connection) -> bool:
    """Cheap liveness probe for /healthz."""
    try:
        conn.execute("select 1 from pings limit 1").fetchall()
        return True
    except psycopg.Error:
        return False


def hash_ip(ip: str | None, salt: str) -> str | None:
    """Salted, truncated SHA-256 of the caller IP. Ops/debug only, never shown."""
    if not ip:
        return None
    return sha256(f"{salt}:{ip}".encode()).hexdigest()[:16]


# --- ingestion lookups ------------------------------------------------------


def device_by_token(conn: psycopg.Connection, token: str) -> Row | None:
    """Resolve a device token to its device, parent and family in one hop."""
    return conn.execute(
        """
        select d.id as device_id, d.active, d.revoked_utc,
               p.id as parent_id, p.display_name as parent_name, p.tz as parent_tz,
               f.id as family_id, f.name as family_name, f.tz as family_tz
        from devices d
        join parents p on p.id = d.parent_id
        join families f on f.id = p.family_id
        where d.device_token = %s
        """,
        (token,),
    ).fetchone()


def active_signal(conn: psycopg.Connection, parent_id: Any, signal: str) -> Row | None:
    """Look the signal up in *this* parent's allowlist. None means reject."""
    return conn.execute(
        """
        select signal, alarm_grade
        from parent_signals
        where parent_id = %s and signal = %s and active
        """,
        (parent_id, signal),
    ).fetchone()


def insert_ping(
    conn: psycopg.Connection,
    parent_id: Any,
    signal: str,
    ts_utc: datetime,
    ip_hash: str | None,
    dedupe_window_s: int = 60,
) -> bool:
    """Insert a ping unless an identical (parent, signal) landed within the window.

    Shortcuts automations sometimes double-fire. The guard is inside the INSERT
    so two concurrent fires cannot both pass a separate check first.
    """
    cutoff = ts_utc - timedelta(seconds=dedupe_window_s)
    row = conn.execute(
        """
        insert into pings (parent_id, signal, ts_utc, ip_hash)
        select %(parent_id)s, %(signal)s, %(ts)s, %(ip_hash)s
        where not exists (
            select 1 from pings
            where parent_id = %(parent_id)s
              and signal = %(signal)s
              and ts_utc > %(cutoff)s
        )
        returning id
        """,
        {
            "parent_id": parent_id,
            "signal": signal,
            "ts": ts_utc,
            "ip_hash": ip_hash,
            "cutoff": cutoff,
        },
    ).fetchone()
    return row is not None


def revoke_device(conn: psycopg.Connection, device_id: Any, when: datetime) -> None:
    """Kill one device. Every other device in the family keeps working."""
    conn.execute(
        "update devices set active = false, revoked_utc = %s where id = %s",
        (when, device_id),
    )


# --- heartbeat queries ------------------------------------------------------


def parents_with_tz(conn: psycopg.Connection) -> list[Row]:
    """Every monitored person, with the family context needed to pick a clock."""
    return conn.execute(
        """
        select p.id as parent_id, p.display_name as parent_name, p.tz as parent_tz,
               f.id as family_id, f.name as family_name, f.tz as family_tz
        from parents p
        join families f on f.id = p.family_id
        order by f.name, p.display_name
        """
    ).fetchall()


def families_with_tz(conn: psycopg.Connection) -> list[Row]:
    """Every family, for the per-family infra check."""
    return conn.execute(
        "select id as family_id, name as family_name, tz as family_tz "
        "from families order by name"
    ).fetchall()


def count_alarm_pings_between(
    conn: psycopg.Connection, parent_id: Any, start: datetime, end: datetime
) -> int:
    """Count alarm-grade pings for one parent in [start, end).

    Alarm grade is read from that parent's own allowlist, so a family that turns
    a signal off for one person does not change anyone else's checks.
    """
    row = conn.execute(
        """
        select count(*) as n
        from pings p
        join parent_signals ps
          on ps.parent_id = p.parent_id and ps.signal = p.signal
        where p.parent_id = %s
          and ps.alarm_grade and ps.active
          and p.ts_utc >= %s and p.ts_utc < %s
        """,
        (parent_id, start, end),
    ).fetchone()
    return int(row["n"])


def last_alarm_ping(conn: psycopg.Connection, parent_id: Any) -> datetime | None:
    """When this person last did something deliberate, ever."""
    row = conn.execute(
        """
        select max(p.ts_utc) as ts
        from pings p
        join parent_signals ps
          on ps.parent_id = p.parent_id and ps.signal = p.signal
        where p.parent_id = %s and ps.alarm_grade and ps.active
        """,
        (parent_id,),
    ).fetchone()
    return row["ts"] if row else None


def family_last_ping(conn: psycopg.Connection, family_id: Any) -> datetime | None:
    """Last ping from any device in the family. None means none ever."""
    row = conn.execute(
        """
        select max(p.ts_utc) as ts
        from pings p
        join parents pa on pa.id = p.parent_id
        where pa.family_id = %s
        """,
        (family_id,),
    ).fetchone()
    return row["ts"] if row else None


# --- ops alerts (founder-only) ----------------------------------------------


def insert_ops_alert(
    conn: psycopg.Connection,
    family_id: Any,
    parent_id: Any | None,
    kind: str,
    detail: str,
    ts_utc: datetime,
) -> None:
    """Record an ops alert. Nothing here is ever shown to a family or a parent."""
    conn.execute(
        """
        insert into ops_alerts (family_id, parent_id, kind, detail, ts_utc)
        values (%s, %s, %s, %s, %s)
        """,
        (family_id, parent_id, kind, detail, ts_utc),
    )


def ops_alert_exists(
    conn: psycopg.Connection,
    kind: str,
    family_id: Any,
    parent_id: Any | None,
    start: datetime,
    end: datetime,
) -> bool:
    """Has this (kind, parent-or-family) alert already fired in the window?"""
    row = conn.execute(
        """
        select 1 from ops_alerts
        where kind = %s
          and family_id = %s
          and parent_id is not distinct from %s
          and ts_utc >= %s and ts_utc < %s
        limit 1
        """,
        (kind, family_id, parent_id, start, end),
    ).fetchone()
    return row is not None
