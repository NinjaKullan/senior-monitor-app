"""Kettle's own lines in the family journal — the gentle whats (spec 012 §3).

The journal is the family's memory, and until this module the family were its
only authors. Kettle now writes a FEW warm lines of its own: whats never hows,
no verdicts, and no escalation or ladder events EVER — memory is a warm
record, not an incident log. Absence speaks, exactly like the product: a month
that was not clean gets NOTHING — no entry, no qualifier.

Strings are DECISIONS 200, character for character, with `{parent}` the
display name (the in-app naming law, DECISIONS 183 — the outbound channel's
{relationship} rule, 149, governs messages, not the journal a family reads
inside the app). The fourth ruled string, city_change, is authored by the
WEBAPP (spec 010 §4, `webapp/src/lib/copy.ts` CITY_CHANGED_NOTE) and is
deliberately not duplicated here.

Idempotency lives in the SCHEMA (migration 0020), not loop memory: partial
unique indexes make started/first_reply once ever per parent and clean_month
once per (parent, month), and every insert is ON CONFLICT DO NOTHING — a
rerun, a restart, or two schedulers racing all land one row.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Any

import psycopg

AUTHOR = "Kettle"


def _as_date(value: date | str) -> date:
    """The engine's `local_date` travels as an ISO string (the Schedule
    dataclass); Postgres stores it as a date. Accept both, always work in
    dates."""
    return value if isinstance(value, date) else date.fromisoformat(value)

#: The product-authored auto-note bodies, verbatim from DECISIONS 200.
STARTED_NOTE = "Kettle's first morning with {parent}."
FIRST_REPLY_NOTE = "Heard from {parent} with a 👍."
CLEAN_MONTH_NOTE = "A normal {month}, start to finish."


def _insert(
    conn: psycopg.Connection,
    family_id: Any,
    parent_id: Any,
    kind: str,
    body: str,
    event_date: date,
) -> bool:
    """One auto note, at most once per idempotency key. True when it wrote.

    The conflict target is inferred from 0020's partial unique indexes; the
    journal stays insert-only — nothing here updates or deletes, ever.
    """
    if kind in ("started", "first_reply"):
        conflict = "(parent_id, kind) where kind in ('started', 'first_reply')"
    else:
        conflict = "(parent_id, kind, event_date) where kind = 'clean_month'"
    row = conn.execute(
        f"""
        insert into journal_entries
            (family_id, parent_id, author_label, body, event_date, kind)
        values (%s, %s, %s, %s, %s, %s)
        on conflict {conflict} do nothing
        returning id
        """,  # noqa: S608 - conflict clause is one of two literals above
        (family_id, parent_id, AUTHOR, body, event_date, kind),
    ).fetchone()
    return row is not None


def note_started(
    conn: psycopg.Connection,
    family_id: Any,
    parent_id: Any,
    parent_name: str,
    local_date: date | str,
) -> bool:
    """Spec 012 §3.2: written when a parent's first daily note goes out.

    Called after every SENT digest rather than after a "first" the caller
    proves — the schema's once-ever key makes every call after the first a
    no-op, which is cheaper and safer than each call site re-deriving
    firstness.
    """
    return _insert(
        conn,
        family_id,
        parent_id,
        "started",
        STARTED_NOTE.format(parent=parent_name),
        _as_date(local_date),
    )


def note_first_reply(
    conn: psycopg.Connection,
    family_id: Any,
    parent_id: Any,
    parent_name: str,
    when: datetime,
) -> bool:
    """Spec 012 §3.3: once, on the parent's first-ever WhatsApp reply."""
    return _insert(
        conn,
        family_id,
        parent_id,
        "first_reply",
        FIRST_REPLY_NOTE.format(parent=parent_name),
        when.date(),
    )


def previous_month(today: date) -> tuple[date, date]:
    """The previous calendar month as [first day, first day of `today`'s month)."""
    first_of_this = today.replace(day=1)
    last_month_end = first_of_this
    first_of_prev = (
        date(first_of_this.year - 1, 12, 1)
        if first_of_this.month == 1
        else date(first_of_this.year, first_of_this.month - 1, 1)
    )
    return first_of_prev, last_month_end


def note_clean_month(
    conn: psycopg.Connection,
    family_id: Any,
    parent_id: Any,
    today: date | str,
) -> bool:
    """Spec 012 §3.4: the previous month, only if it was clean — else NOTHING.

    Clean means no silent-day escalation reached the family: zero SENT
    follow-ons with a local_date inside the month. Two guards keep the line
    honest beyond the spec's letter, both flagged in DECISIONS: Kettle must
    have been listening for the WHOLE month (the parent's first-ever sent
    digest predates the month), or "start to finish" is a claim about days
    nobody watched; and a month with no sent digests at all writes nothing.

    Written on the 1st in the normal case, but keyed to the month rather than
    to the day: a scheduler asleep on the 1st writes it on the 2nd instead of
    never. A month that fails any check writes NOTHING — the suppression the
    spec orders, planted in the tests.
    """
    start, end = previous_month(_as_date(today))
    escalations = conn.execute(
        """
        select count(*) as n from sent_messages
        where parent_id = %s and kind = 'follow_on' and status = 'sent'
          and local_date >= %s and local_date < %s
        """,
        (parent_id, start, end),
    ).fetchone()["n"]
    if escalations:
        return False
    digests = conn.execute(
        """
        select min(local_date) as first_ever,
               count(*) filter (where local_date >= %s and local_date < %s) as in_month
        from sent_messages
        where parent_id = %s and kind in ('digest_morning', 'digest_evening')
          and status = 'sent'
        """,
        (start, end, parent_id),
    ).fetchone()
    # Strictly after the month's first day suppresses; ON it is a month
    # watched from its very first morning, which is exactly the claim.
    if not digests["in_month"] or digests["first_ever"] > start:
        return False
    month_name = calendar.month_name[start.month]
    return _insert(
        conn,
        family_id,
        parent_id,
        "clean_month",
        CLEAN_MONTH_NOTE.format(month=month_name),
        start,
    )
