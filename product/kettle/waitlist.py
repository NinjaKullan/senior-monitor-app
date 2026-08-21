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
) -> None:
    """Insert, or quietly update the answer if this address signed up before.

    `on conflict do update` rather than `do nothing`: someone who signs up twice
    has usually corrected something, and the later answer is the one they meant.
    Either way the caller cannot tell which branch ran — that is the point.

    The note upserts through `coalesce`: a later signup that says something new
    replaces the old note, and one that leaves the box empty keeps what was
    already said — silence is not an erasure request, retyping is a correction.
    """
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
