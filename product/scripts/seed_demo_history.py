#!/usr/bin/env python3
"""Seed a demo family's thirty days of history (DECISIONS 242).

    python -m scripts.seed_demo_history --family-id <uuid> [--days 30] [--seed 42]

The Whitakers are a REAL provisioned family in prod with no phone numbers on
either parent, so no ask can ever leave the building for them. What they lack
is a past: a family provisioned this morning shows an empty app, and the demo
needs a product that has been watching for a month. This writes that past.

Three properties, in the order they matter:

* **It refuses anything that might be a real family.** Checked before the
  first write, not per row: a parent carrying a phone number, or a family
  whose name is one of the real ones. A seeder that writes half a month into a
  living family before noticing is worse than one that does not exist.
* **It owns its rows and can find them again.** Everything it writes carries
  `demo-seed` where the row has somewhere to put it, so a re-run deletes
  exactly what the last run made and nothing a person did in the app.
* **It is deterministic.** The same `--seed` produces the same timestamps, so
  a screenshot taken today and one taken after a re-run are the same picture.

What it does NOT do is invent a vocabulary. The pings use each parent's own
`parent_signals` allowlist, and the ledger rows are the ones `run_outbound`
would actually have written on those days — the same templates, chosen by the
same rules — so the demo shows the product's real behaviour rather than a
plausible-looking imitation of it.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import psycopg

from kettle import db
from kettle.config import settings_from_env
from kettle.outbound import (
    ASK_THRESHOLD,
    EVENING_DIGEST,
    FOLLOW_ON_GRACE,
    MORNING_DIGEST,
)
from kettle.signals import ALARM_GRADE

#: The one string that says "this row belongs to the seeder".
#:
#: It goes in a column the product never renders: `pings.ip_hash` is an ops
#: breadcrumb, and `sent_messages.transport` names the carrier, which for a
#: message nobody ever sent is honestly none of the real ones. Both are already
#: opaque operational text, so nothing about a family's screen changes.
#:
#: `journal_entries` has no such column — every field it owns is either shown
#: on screen or constrained — so the seeder owns its notes by CONTENT instead,
#: deleting only rows in this family whose body it is about to write. That
#: asymmetry is deliberate: a marker smuggled into `body` or `author_label`
#: would be a marker printed in the family's own record.
MARKER = "demo-seed"

#: Names that are not demos. Belt to the phone-number check's braces: the
#: pilot family and the dark-stage rehearsal family both exist in prod, and
#: the rehearsal one carries numbers so the first rule already stops it. This
#: stops a family that had its numbers cleared for some other reason.
REAL_FAMILY_NAMES = frozenset({"suryaprakasam", "rehearsal"})

#: A normal day under the merged-method install (DECISIONS 107): one
#: multi-app automation firing `routine`, one charger automation firing
#: `charger`, and the daily `device_alive` heartbeat. Times are local, and
#: each carries the jitter a person actually produces — nobody opens the news
#: at 07:30:00 five days running.
@dataclass(frozen=True)
class Beat:
    role: str
    at: time
    jitter_minutes: int


NORMAL_DAY: tuple[Beat, ...] = (
    Beat("corroborating", time(6, 50), 20),   # phone off the charger
    Beat("heartbeat", time(7, 5), 15),        # the time-of-day automation
    Beat("alarm", time(7, 30), 25),           # the first habit app of the day
    Beat("alarm", time(9, 50), 35),
    Beat("alarm", time(12, 40), 40),
    Beat("alarm", time(16, 10), 45),
    Beat("alarm", time(19, 30), 35),
    Beat("corroborating", time(21, 40), 25),  # back on the charger
)

#: The story days, counted back from today in the parent's own timezone.
LATE_START_DAYS_AGO = 6      # Mom: the morning that arrived late and was fine
UNREACHABLE_DAYS_AGO = 12    # Dad: the phone nobody could reach until the afternoon
APPOINTMENT_DAYS_AGO = 19    # Mom: an ordinary day that carries a note

#: Dad's day, in local time: the first ping of any kind lands after the
#: follow-on has already gone out, which is what makes it the unreachable
#: shape rather than the changed-morning one.
UNREACHABLE_FIRST_PING = time(13, 12)
#: Mom's late start: after the morning digest but BEFORE the ask threshold,
#: so the ladder never asks her anything. A quiet start that turned normal.
LATE_START_FIRST_PING = time(10, 40)

NOTE_UNREACHABLE = "Phone was in the car. All fine."
NOTE_APPOINTMENT = "Dr. Patel, Thursday 2pm"
NOTE_AUTHOR = "Sarah"


class Refused(Exception):
    """A precondition failed. Nothing has been written."""


# --- refusals -----------------------------------------------------------------


def check_safe(conn: psycopg.Connection, family_id: Any) -> str:
    """Refuse anything that could be a living family. Returns the family name.

    Both checks run before a single row is written, and both are about the
    same fear: a seeder that rewrites a month of a real family's history is
    not a bug anybody can undo from the app.
    """
    family = conn.execute(
        "select name from families where id = %s", (family_id,)
    ).fetchone()
    if family is None:
        raise Refused(f"no family with id {family_id}")
    name = family["name"]
    if name.strip().lower() in REAL_FAMILY_NAMES:
        raise Refused(f"{name!r} is a real family; this script seeds demos only")

    parents = conn.execute(
        """
        select display_name, phone_e164, whatsapp_e164
        from parents where family_id = %s order by display_name
        """,
        (family_id,),
    ).fetchall()
    if not parents:
        raise Refused(f"{name!r} has no parents to seed history for")
    reachable = [
        p["display_name"]
        for p in parents
        if (p["phone_e164"] or "").strip() or (p["whatsapp_e164"] or "").strip()
    ]
    if reachable:
        raise Refused(
            f"{name!r} has a phone number on {', '.join(reachable)}; a family "
            "Kettle can actually reach is not a demo family (DECISIONS 242)"
        )
    return name


# --- the shape of a day -------------------------------------------------------


def signal_roles(conn: psycopg.Connection, parent_id: Any) -> dict[str, list[str]]:
    """This parent's own allowlist, split into the roles a day is built from.

    Read from `parent_signals` rather than assumed, so the demo speaks the
    vocabulary the family was actually provisioned with. `device_alive` is
    pulled out of the corroborating set because it is the heartbeat rather
    than a household event, and a day wants exactly one of it.
    """
    active = [row["signal"] for row in db.parent_active_signals(conn, parent_id)]
    alarm = [s for s in active if ALARM_GRADE.get(s, False)]
    heartbeat = [s for s in active if s == "device_alive"]
    corroborating = [
        s for s in active if not ALARM_GRADE.get(s, False) and s != "device_alive"
    ]
    return {"alarm": alarm, "heartbeat": heartbeat, "corroborating": corroborating}


def _rng(seed: int, parent_id: Any, day: date) -> random.Random:
    """One generator per parent-day, so a day's times never depend on order."""
    return random.Random(f"{seed}:{parent_id}:{day.isoformat()}")


def _at(day: date, moment: time, tz: ZoneInfo) -> datetime:
    return datetime.combine(day, moment, tzinfo=tz)


def day_pings(
    day: date,
    tz: ZoneInfo,
    roles: dict[str, list[str]],
    rng: random.Random,
    *,
    first_alarm_at: time | None = None,
    silent_before: time | None = None,
) -> list[tuple[str, datetime]]:
    """(signal, instant) for one parent-day, in local time then made absolute.

    `first_alarm_at` moves the day's opening habit app without touching the
    rest of it - a morning that arrived late and then behaved normally.
    `silent_before` drops everything, every grade, until that hour: a phone
    that reported nothing at all, which is what makes the follow-on the
    unreachable one rather than the changed-morning one.
    """
    out: list[tuple[str, datetime]] = []
    seen_alarm = False
    for beat in NORMAL_DAY:
        pool = roles[beat.role]
        if not pool:
            continue
        moment = beat.at
        if beat.role == "alarm" and not seen_alarm and first_alarm_at is not None:
            moment = first_alarm_at
        seen_alarm = seen_alarm or beat.role == "alarm"
        when = _at(day, moment, tz) + timedelta(
            minutes=rng.randint(-beat.jitter_minutes, beat.jitter_minutes),
            seconds=rng.randint(0, 59),
        )
        if silent_before is not None and when < _at(day, silent_before, tz):
            continue
        out.append((rng.choice(pool) if len(pool) > 1 else pool[0], when))
    return sorted(out, key=lambda pair: pair[1])


# --- the ledger the engine would have written ---------------------------------


@dataclass(frozen=True)
class LedgerRow:
    kind: str
    template_id: str
    sent_utc: datetime
    status: str = "sent"


def day_ledger(
    day: date, tz: ZoneInfo, *, late_start: bool, unreachable: bool
) -> list[LedgerRow]:
    """What `run_outbound` decides for one parent-day, replayed rather than guessed.

    Every branch below is the engine's own, in its own order, so the demo's
    ledger is a recording of the product rather than a story about it:

    * the morning digest picks quiet or normal from the 06:00-08:30 window;
    * the ask fires only if the window is STILL quiet at 11:00, which is why a
      morning that arrives at 10:40 is never asked about;
    * the follow-on needs an unanswered ask plus the two-hour grace, and is
      the unreachable body when nothing of any grade has arrived all day;
    * the all-clear exists only after a follow-on, when the first alarm-grade
      signal since it lands;
    * the evening digest is WITHHELD on a day a follow-on went out (DECISIONS
      164) - recorded as skipped, which is the row the engine writes too.
    """
    morning = _at(day, MORNING_DIGEST, tz)
    evening = _at(day, EVENING_DIGEST, tz)
    quiet_morning = late_start or unreachable
    rows = [
        LedgerRow(
            "digest_morning",
            "digest_morning_quiet" if quiet_morning else "digest_morning_normal",
            morning,
        )
    ]

    if unreachable:
        ask_at = _at(day, ASK_THRESHOLD, tz)
        follow_at = ask_at + FOLLOW_ON_GRACE
        resumed = _at(day, UNREACHABLE_FIRST_PING, tz)
        rows += [
            LedgerRow("ask", "ask_parent", ask_at),
            # Nothing of any grade had arrived by the grace mark, so the
            # report is about the phone rather than about the morning.
            LedgerRow("follow_on", "follow_on_unreachable", follow_at),
            LedgerRow("all_clear", "all_clear_family", resumed),
            # The day still reads as recovered; the follow-on is what
            # withholds it, and the skipped row is how the engine says so.
            LedgerRow("digest_evening", "digest_evening_recovered", evening, "skipped"),
        ]
        return rows

    rows.append(
        LedgerRow(
            "digest_evening",
            "digest_evening_recovered" if late_start else "digest_evening_normal",
            evening,
        )
    )
    return rows


# --- writing ------------------------------------------------------------------


def clear_owned(conn: psycopg.Connection, family_id: Any, bodies: list[str]) -> None:
    """Delete exactly what a previous run wrote, and nothing else.

    Pings and ledger rows go by MARKER, so a real ping or a real send in this
    family would survive (there are none, but the delete should not depend on
    that being true). Notes go by body, because the journal has nowhere to
    keep a marker that a person would not read.
    """
    conn.execute(
        """
        delete from pings
        where ip_hash = %s
          and parent_id in (select id from parents where family_id = %s)
        """,
        (MARKER, family_id),
    )
    conn.execute(
        "delete from sent_messages where family_id = %s and transport = %s",
        (family_id, MARKER),
    )
    conn.execute(
        "delete from journal_entries where family_id = %s and body = any(%s)",
        (family_id, bodies),
    )


def next_weekday(after: date, weekday: int) -> date:
    """The next given weekday strictly after `after` (Monday is 0)."""
    ahead = (weekday - after.weekday()) % 7 or 7
    return after + timedelta(days=ahead)


@dataclass(frozen=True)
class Seeded:
    pings: int
    messages: int
    notes: int


def seed(
    conn: psycopg.Connection, family_id: Any, days: int = 30, seed_value: int = 42
) -> Seeded:
    """Write the history. Refuses first, deletes its own, then rewrites.

    One transaction: a half-seeded family is a demo that shows the wrong thing
    without anybody knowing it is wrong.
    """
    check_safe(conn, family_id)
    parents = db.parents_for_family(conn, family_id)

    # The appointment note is the one row whose date has to stay ahead of the
    # demo rather than behind it: an "upcoming" entry the app files in the
    # past is just an old note. Thursday, because that is what it says.
    today_family = datetime.now(
        ZoneInfo(conn.execute(
            "select tz from families where id = %s", (family_id,)
        ).fetchone()["tz"])
    ).date()
    appointment_on = next_weekday(today_family, 3)

    clear_owned(conn, family_id, [NOTE_UNREACHABLE, NOTE_APPOINTMENT])

    ping_rows: list[tuple[Any, str, datetime, str]] = []
    message_rows: list[tuple[Any, Any, str, str, str, str, datetime, str]] = []
    note_rows: list[tuple[Any, Any, str, str, date | None, datetime, str]] = []

    # The two story parents are picked by RELATIONSHIP rather than by display
    # name, so renaming a demo parent never silently moves whose day is whose.
    relationships = {
        row["id"]: (row["relationship"] or "").strip().lower()
        for row in conn.execute(
            "select id, relationship from parents where family_id = %s", (family_id,)
        ).fetchall()
    }

    for parent in parents:
        parent_id = parent["parent_id"]
        tz = ZoneInfo(parent["parent_tz"] or "UTC")
        roles = signal_roles(conn, parent_id)
        if not roles["alarm"]:
            raise Refused(
                f"{parent['parent_name']} has no alarm-grade signal active; "
                "there is no morning for the demo to show"
            )
        relationship = relationships[parent_id]
        today_local = datetime.now(tz).date()

        for back in range(days, 0, -1):
            day = today_local - timedelta(days=back)
            late_start = relationship == "mom" and back == LATE_START_DAYS_AGO
            unreachable = relationship == "dad" and back == UNREACHABLE_DAYS_AGO
            rng = _rng(seed_value, parent_id, day)

            for signal, when in day_pings(
                day,
                tz,
                roles,
                rng,
                first_alarm_at=LATE_START_FIRST_PING if late_start else None,
                silent_before=UNREACHABLE_FIRST_PING if unreachable else None,
            ):
                ping_rows.append((parent_id, signal, when, MARKER))

            for row in day_ledger(
                day, tz, late_start=late_start, unreachable=unreachable
            ):
                message_rows.append(
                    (
                        family_id,
                        parent_id,
                        day.isoformat(),
                        row.kind,
                        row.template_id,
                        MARKER,
                        row.sent_utc,
                        row.status,
                    )
                )

            if unreachable:
                note_rows.append(
                    (
                        family_id,
                        parent_id,
                        NOTE_AUTHOR,
                        NOTE_UNREACHABLE,
                        None,
                        _at(day, time(18, 5), tz),
                        "note",
                    )
                )
            if relationship == "mom" and back == APPOINTMENT_DAYS_AGO:
                note_rows.append(
                    (
                        family_id,
                        parent_id,
                        NOTE_AUTHOR,
                        NOTE_APPOINTMENT,
                        appointment_on,
                        _at(day, time(11, 20), tz),
                        "note",
                    )
                )

    with conn.cursor() as cur:
        cur.executemany(
            "insert into pings (parent_id, signal, ts_utc, ip_hash) "
            "values (%s, %s, %s, %s)",
            ping_rows,
        )
        cur.executemany(
            "insert into sent_messages (family_id, parent_id, local_date, kind, "
            "template_id, transport, sent_utc, status) "
            "values (%s, %s, %s, %s, %s, %s, %s, %s)",
            message_rows,
        )
        cur.executemany(
            "insert into journal_entries (family_id, parent_id, author_label, body, "
            "event_date, created_utc, kind) values (%s, %s, %s, %s, %s, %s, %s)",
            note_rows,
        )
    conn.commit()
    return Seeded(len(ping_rows), len(message_rows), len(note_rows))


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed a demo family's history.")
    parser.add_argument("--family-id", required=True)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    settings = settings_from_env()
    with db.connect(settings.database_url) as conn:
        try:
            name = check_safe(conn, args.family_id)
        except Refused as refusal:
            print(f"refused: {refusal}", file=sys.stderr)
            return 2
        counts = seed(conn, args.family_id, days=args.days, seed_value=args.seed)

    print(f"{name}: {args.days} days seeded (seed {args.seed}, marker {MARKER!r})")
    print(f"  pings          {counts.pings:,}")
    print(f"  sent_messages  {counts.messages:,}")
    print(f"  journal notes  {counts.notes:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
