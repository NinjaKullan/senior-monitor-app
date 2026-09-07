"""The landing page's waitlist (spec 006 §7).

Three rules govern this module, and all three are about not leaking:

1. **A duplicate signup is indistinguishable from a first one.** Same status,
   same body, same timing shape. Otherwise `POST /waitlist` answers "is this
   address on the list", which is a question about a stranger's private
   intention to buy elder-monitoring for their parent.
2. **A honeypot hit looks exactly like a success.** Telling a bot it was caught
   only teaches whoever wrote it which field to leave alone next time.
3. **The stored record is as small as the product's own.** An email and one
   fixed-choice answer. No IP, no user agent, no referrer, no timestamps beyond
   the row's own — the page carries no analytics (law #4), and the endpoint
   behind it does not quietly become the analytics.
"""

from __future__ import annotations

import re
from collections import OrderedDict, deque
from datetime import datetime, timedelta
from typing import Any

import psycopg

#: The one sentence this endpoint ever says back. Mirrored in `site/src/copy.ts`
#: so the no-JS plain POST and the fetch path show the identical words;
#: `product/tests/test_waitlist.py` fails if the two drift, the same guard the
#: digest templates have carried since item 47.
WAITLIST_SUCCESS = "You're on the list."

#: The only answers the column accepts — the CHECK constraint says the same
#: thing in the schema (structure 39), and this is the API-side mirror so a bad
#: answer is a 400 rather than an integrity error.
PARENT_PHONE_CHOICES = ("iphone", "android", "unsure")

#: Deliberately loose. Address validity is decided by an email actually arriving,
#: not by a regex, and the elaborate ones reject real addresses. This rejects
#: what is obviously not an address and nothing more.
_EMAIL = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")

#: Long enough for any real address, short enough that the column is not a
#: storage primitive for someone with a script.
MAX_EMAIL_LENGTH = 254

#: The optional "what would you most like Kettle to help with?" answer
#: (DECISIONS 129). A thousand characters is several honest paragraphs; the
#: column's CHECK repeats the number so the cap holds even against code that
#: forgets to call the normaliser.
MAX_HELP_WITH_LENGTH = 1000

#: Flood guards (DECISIONS 307). The landing page posts straight to kettle-api,
#: the machine the family engine runs on, and nothing fronts it; a flood slows
#: the engine and can fill the free-plan database by rotating addresses. The
#: limit is a few signups per caller per rolling hour and a ceiling on the
#: table itself; over either, the route answers WAITLIST_SUCCESS and writes
#: nothing, so a refusal is byte-identical to a signup and nothing leaks.
#: Neither guard records anything about the caller: no row, no alert, no log
#: line — an alert on a flood is itself a flood.
RATE_LIMIT = 5
RATE_WINDOW = timedelta(hours=1)
#: The counter's key bound: past this many distinct callers the oldest are
#: dropped, so memory cannot grow without limit under rotating addresses.
RATE_MAX_KEYS = 10_000
#: The table's ceiling. A flood guard, not a feature: at or past it nothing is
#: written, a re-signup's correction included.
WAITLIST_CAP = 50_000


class FloodCounter:
    """Per-caller hit times, in process memory only.

    Process-local and reset on restart, accepted for a one-machine app (307).
    The key is whatever the route hands in (Fly's client IP header); it lives
    here and nowhere else, and never reaches the database or a log line.
    Insertion order tracks recency (a hit moves its key to the end), so pruning
    walks stale keys from the front and stops at the first live one.
    """

    def __init__(
        self,
        limit: int = RATE_LIMIT,
        window: timedelta = RATE_WINDOW,
        max_keys: int = RATE_MAX_KEYS,
    ) -> None:
        self.limit = limit
        self.window = window
        self.max_keys = max_keys
        self._hits: OrderedDict[str, deque[datetime]] = OrderedDict()

    def allow(self, key: str, now: datetime) -> bool:
        """Count this hit and say whether it is within the limit."""
        self._prune(now)
        hits = self._hits.get(key)
        if hits is None:
            hits = deque()
        else:
            while hits and now - hits[0] >= self.window:
                hits.popleft()
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        self._hits[key] = hits
        self._hits.move_to_end(key)
        while len(self._hits) > self.max_keys:
            self._hits.popitem(last=False)
        return True

    def _prune(self, now: datetime) -> None:
        while self._hits:
            key, hits = next(iter(self._hits.items()))
            if hits and now - hits[-1] < self.window:
                return
            del self._hits[key]

    def __len__(self) -> int:
        return len(self._hits)


def normalise_email(raw: str) -> str | None:
    """Lowercase and strip, or None if it is not an address at all."""
    email = raw.strip().lower()
    if not email or len(email) > MAX_EMAIL_LENGTH or not _EMAIL.match(email):
        return None
    return email


def normalise_choice(raw: str) -> str | None:
    """One of the three fixed answers, or None."""
    choice = raw.strip().lower()
    return choice if choice in PARENT_PHONE_CHOICES else None


def normalise_help_with(raw: str) -> str | None:
    """The optional note: stripped, capped, absent when empty.

    Truncation rather than rejection, on purpose: this field is a kindness,
    not a gate, and a signup must never be lost because someone's answer ran
    long. The cap is the storage bound; the sentence survives to its limit.
    """
    text = raw.strip()
    if not text:
        return None
    return text[:MAX_HELP_WITH_LENGTH].rstrip()


def record(
    conn: psycopg.Connection,
    email: str,
    parent_phone: str,
    help_with: str | None = None,
) -> bool:
    """Insert, or quietly update the answer if this address signed up before.

    Returns False, having written nothing, when the table is at or past
    WAITLIST_CAP (307): the count and the insert share one transaction, and
    the cap holds for a re-signup's correction too. The route answers the same
    sentence either way.

    `on conflict do update` rather than `do nothing`: someone who signs up twice
    has usually corrected something, and the later answer is the one they meant.
    Either way the caller cannot tell which branch ran — that is the point.

    The note upserts through `coalesce`: a later signup that says something new
    replaces the old note, and one that leaves the box empty keeps what was
    already said — silence is not an erasure request, retyping is a correction.
    """
    with conn.transaction():
        if count(conn) >= WAITLIST_CAP:
            return False
        _upsert(conn, email, parent_phone, help_with)
    return True


def _upsert(conn: psycopg.Connection, email: str, parent_phone: str, help_with: str | None) -> None:
    conn.execute(
        """
        insert into waitlist (email, parent_phone, help_with)
        values (%s, %s, %s)
        on conflict (email) do update
            set parent_phone = excluded.parent_phone,
                help_with = coalesce(excluded.help_with, waitlist.help_with)
        """,
        (email, parent_phone, help_with),
    )


def count(conn: psycopg.Connection) -> int:
    """How many signups. For the founder's own psql, not for any endpoint."""
    row: Any = conn.execute("select count(*) as n from waitlist").fetchone()
    return int(row["n"])
