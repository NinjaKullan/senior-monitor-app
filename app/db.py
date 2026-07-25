"""SQLite storage. Four tables, no ORM, allowlisted columns only.

Nothing here accepts a field that is not in the schema below. The schema *is*
the privacy promise: `who`, `signal`, a server timestamp, and a one-way IP
hash for ops. No content, no location, no device identity.
"""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import timedelta
from pathlib import Path
from typing import Any

from app.timeutil import fmt_utc, parse_utc

SCHEMA = """
CREATE TABLE IF NOT EXISTS pings (
    id      INTEGER PRIMARY KEY,
    who     TEXT NOT NULL,
    signal  TEXT NOT NULL,
    ts_utc  TEXT NOT NULL,
    ip_hash TEXT
);
CREATE INDEX IF NOT EXISTS idx_pings_who_ts ON pings(who, ts_utc);
CREATE INDEX IF NOT EXISTS idx_pings_ts ON pings(ts_utc);

CREATE TABLE IF NOT EXISTS labels (
    id          INTEGER PRIMARY KEY,
    date_ist    TEXT NOT NULL,
    who         TEXT NOT NULL,
    note        TEXT NOT NULL,
    created_utc TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_labels_date ON labels(date_ist);

CREATE TABLE IF NOT EXISTS alerts (
    id     INTEGER PRIMARY KEY,
    kind   TEXT NOT NULL,
    who    TEXT NOT NULL,
    detail TEXT NOT NULL,
    ts_utc TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_alerts_kind_who ON alerts(kind, who, ts_utc);

CREATE TABLE IF NOT EXISTS status_views (
    id       INTEGER PRIMARY KEY,
    date_ist TEXT NOT NULL,
    ts_utc   TEXT NOT NULL
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    """Open (and if needed create) the pilot database in WAL mode."""
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create tables and indexes if they do not exist yet."""
    conn.executescript(SCHEMA)
    conn.commit()


def healthy(conn: sqlite3.Connection) -> bool:
    """Cheap liveness probe for /healthz."""
    try:
        conn.execute("SELECT 1 FROM pings LIMIT 1").fetchall()
        return True
    except sqlite3.Error:
        return False


def hash_ip(ip: str | None, salt: str) -> str | None:
    """Salted, truncated SHA-256 of the caller IP. Ops/debug only, never shown."""
    if not ip:
        return None
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()[:16]


# --- pings -----------------------------------------------------------------


def insert_ping(
    conn: sqlite3.Connection,
    who: str,
    signal: str,
    ts_utc: str,
    ip_hash: str | None,
    dedupe_window_s: int = 60,
) -> bool:
    """Insert a ping unless an identical (who, signal) landed within the window.

    Shortcuts automations sometimes double-fire; returns False when collapsed.
    """
    cutoff = fmt_utc(parse_utc(ts_utc) - timedelta(seconds=dedupe_window_s))
    recent = conn.execute(
        "SELECT id FROM pings WHERE who=? AND signal=? AND ts_utc > ? LIMIT 1",
        (who, signal, cutoff),
    ).fetchone()
    if recent is not None:
        return False
    conn.execute(
        "INSERT INTO pings (who, signal, ts_utc, ip_hash) VALUES (?, ?, ?, ?)",
        (who, signal, ts_utc, ip_hash),
    )
    conn.commit()
    return True


def last_ping(conn: sqlite3.Connection, who: str, signal: str) -> sqlite3.Row | None:
    """Most recent ping of one signal for one person."""
    return conn.execute(
        "SELECT * FROM pings WHERE who=? AND signal=? ORDER BY ts_utc DESC LIMIT 1",
        (who, signal),
    ).fetchone()


def last_ping_in(
    conn: sqlite3.Connection, who: str, signals: tuple[str, ...]
) -> sqlite3.Row | None:
    """Most recent ping for a person across a set of signals."""
    placeholders = ",".join("?" * len(signals))
    return conn.execute(
        f"SELECT * FROM pings WHERE who=? AND signal IN ({placeholders}) "
        "ORDER BY ts_utc DESC LIMIT 1",
        (who, *signals),
    ).fetchone()


def last_ping_any(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """Most recent ping from any device — the pipeline liveness signal."""
    return conn.execute("SELECT * FROM pings ORDER BY ts_utc DESC LIMIT 1").fetchone()


def count_pings_between(
    conn: sqlite3.Connection,
    who: str,
    start_utc: str,
    end_utc: str,
    signals: tuple[str, ...] | None = None,
) -> int:
    """Count a person's pings in [start, end), optionally limited to some signals."""
    sql = "SELECT COUNT(*) AS n FROM pings WHERE who=? AND ts_utc >= ? AND ts_utc < ?"
    params: list[Any] = [who, start_utc, end_utc]
    if signals:
        sql += f" AND signal IN ({','.join('?' * len(signals))})"
        params.extend(signals)
    row = conn.execute(sql, params).fetchone()
    return int(row["n"])


def recent_pings(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    """Newest pings first, for the status page table."""
    return list(
        conn.execute(
            "SELECT * FROM pings ORDER BY ts_utc DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
    )


def pings_for(conn: sqlite3.Connection, who: str) -> list[sqlite3.Row]:
    """Every ping ever recorded for one person — the transparency view."""
    return list(
        conn.execute(
            "SELECT * FROM pings WHERE who=? ORDER BY ts_utc DESC, id DESC", (who,)
        ).fetchall()
    )


def all_pings(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Every ping, oldest first — the analysis export."""
    return list(
        conn.execute("SELECT * FROM pings ORDER BY ts_utc ASC, id ASC").fetchall()
    )


# --- labels ----------------------------------------------------------------


def insert_label(
    conn: sqlite3.Connection, date_ist: str, who: str, note: str, created_utc: str
) -> None:
    """Record a blinded ground-truth label for one person on one IST day."""
    conn.execute(
        "INSERT INTO labels (date_ist, who, note, created_utc) VALUES (?, ?, ?, ?)",
        (date_ist, who, note, created_utc),
    )
    conn.commit()


def labelled_people(conn: sqlite3.Connection, date_ist: str) -> set[str]:
    """Who already has a label on this IST day."""
    rows = conn.execute(
        "SELECT DISTINCT who FROM labels WHERE date_ist=?", (date_ist,)
    ).fetchall()
    return {r["who"] for r in rows}


def labels_on(conn: sqlite3.Connection, date_ist: str) -> list[sqlite3.Row]:
    """Labels recorded for one IST day."""
    return list(
        conn.execute(
            "SELECT * FROM labels WHERE date_ist=? ORDER BY id ASC", (date_ist,)
        ).fetchall()
    )


def all_labels(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Every label, newest day first."""
    return list(
        conn.execute(
            "SELECT * FROM labels ORDER BY date_ist DESC, id DESC"
        ).fetchall()
    )


# --- alerts (founder-only) --------------------------------------------------


def insert_alert(
    conn: sqlite3.Connection, kind: str, who: str, detail: str, ts_utc: str
) -> None:
    """Record a founder alert. Nothing here is ever shown to family or parents."""
    conn.execute(
        "INSERT INTO alerts (kind, who, detail, ts_utc) VALUES (?, ?, ?, ?)",
        (kind, who, detail, ts_utc),
    )
    conn.commit()


def alert_exists_between(
    conn: sqlite3.Connection, kind: str, who: str, start_utc: str, end_utc: str
) -> bool:
    """Has this (kind, who) alert already fired in the given window?"""
    row = conn.execute(
        "SELECT id FROM alerts WHERE kind=? AND who=? AND ts_utc >= ? AND ts_utc < ? LIMIT 1",
        (kind, who, start_utc, end_utc),
    ).fetchone()
    return row is not None


def last_alert(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """Most recent founder alert, for the status page."""
    return conn.execute(
        "SELECT * FROM alerts ORDER BY ts_utc DESC, id DESC LIMIT 1"
    ).fetchone()


def recent_alerts(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    """Newest founder alerts first."""
    return list(
        conn.execute(
            "SELECT * FROM alerts ORDER BY ts_utc DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
    )


# --- status views (blinding audit) -----------------------------------------


def insert_status_view(conn: sqlite3.Connection, date_ist: str, ts_utc: str) -> None:
    """Log that the founder looked at the dashboard — the blinding audit trail."""
    conn.execute(
        "INSERT INTO status_views (date_ist, ts_utc) VALUES (?, ?)",
        (date_ist, ts_utc),
    )
    conn.commit()
