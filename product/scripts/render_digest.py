#!/usr/bin/env python3
"""Write a seeded day's digest emails to HTML files (DECISIONS 245).

    python -m scripts.render_digest --family-id <uuid> \
        --date 2026-08-15 --parent Linda --out /tmp/digests

The demo family is scenery: the engine skips it (0023), so the digests that
day's ledger records were never actually sent anywhere and there is no inbox
to screenshot. This renders them from the SAME templates the transport would
have used, driven by the SAME ledger rows the seeder wrote, and puts the
result on disk.

Nothing here sends. There is no transport, no API key and no address in this
file; it reads three tables and writes files. That is deliberate - the one
thing a demo must never do is turn into a way to mail somebody by accident.

What it renders is decided by the ledger, not by this script: whichever
template id the row names is the template that renders, so a day whose morning
was quiet produces the quiet body and a day withheld in the evening produces
no evening file at all. If the seeded ledger and the engine ever disagree, the
replay test in test_seed_demo_history catches it long before this does.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import psycopg

from kettle import db
from kettle.config import settings_from_env
from kettle.outbound_html import render_email_html
from kettle.outbound_templates import (
    KIND_DIGEST_EVENING,
    KIND_DIGEST_MORNING,
    render,
    subject_for,
    template,
)

#: Only the two digests. The ask goes to the parent by WhatsApp and the
#: follow-on and all-clear are their own conversation; this script exists for
#: the two messages a child actually opens in an inbox.
RENDERABLE = (KIND_DIGEST_MORNING, KIND_DIGEST_EVENING)


def parent_named(conn: psycopg.Connection, family_id: Any, name: str) -> Any:
    row = conn.execute(
        """
        select id, display_name, relationship
        from parents
        where family_id = %s and lower(display_name) = lower(%s)
        """,
        (family_id, name),
    ).fetchone()
    if row is None:
        known = [
            r["parent_name"] for r in db.parents_for_family(conn, family_id)
        ]
        sys.exit(f"no parent named {name!r} in that family; have {known}")
    return row


def rows_for(
    conn: psycopg.Connection, family_id: Any, parent_id: Any, local_date: str
) -> list[Any]:
    """The day's SENT digest rows, in ladder order.

    Sent only: a withheld evening is recorded as skipped, and rendering it
    would put an email on disk that the family never received - the exact
    kind of quiet fiction this whole demo is built to avoid.
    """
    return conn.execute(
        """
        select kind, template_id, status, sent_utc
        from sent_messages
        where family_id = %s and parent_id = %s and local_date = %s
          and kind = any(%s) and status = 'sent'
        order by sent_utc
        """,
        (family_id, parent_id, local_date, list(RENDERABLE)),
    ).fetchall()


def render_day(
    conn: psycopg.Connection,
    family_id: Any,
    parent_name: str,
    local_date: str,
    out: Path,
) -> list[Path]:
    """Write one file per sent digest. Returns the paths written."""
    parent = parent_named(conn, family_id, parent_name)
    relationship = parent["relationship"]
    out.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for row in rows_for(conn, family_id, parent["id"], local_date):
        found = template(row["template_id"])
        variables = dict.fromkeys(found.variables, relationship or "")
        html = render_email_html(row["template_id"], variables, relationship)
        # The subject is part of what a person sees, so it rides in the file
        # as a comment rather than being lost between the ledger and the eye.
        header = (
            f"<!-- {subject_for(relationship)} | {row['template_id']} | "
            f"{local_date} | {parent['display_name']} -->\n"
        )
        path = out / f"{local_date}-{parent['display_name'].lower()}-{row['kind']}.html"
        path.write_text(header + html, encoding="utf-8")
        written.append(path)
        print(f"{path}  ({row['template_id']})")
        print(f"    {render(row['template_id'], variables)}")
    if not written:
        print(f"no sent digest rows for {parent['display_name']} on {local_date}")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a seeded day's digests.")
    parser.add_argument("--family-id", required=True)
    parser.add_argument("--date", required=True, metavar="YYYY-MM-DD")
    parser.add_argument("--parent", required=True)
    parser.add_argument("--out", default="digests", type=Path)
    args = parser.parse_args()

    settings = settings_from_env()
    with db.connect(settings.database_url) as conn:
        render_day(conn, args.family_id, args.parent, args.date, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
