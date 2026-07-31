"""Operate the escalation ladder (spec 004 §1, §3).

    python -m scripts.ladder --list
    python -m scripts.ladder --set-mode "Sharma" shadow
    python -m scripts.ladder --set-mode "Sharma" live
    python -m scripts.ladder --resolve 42 --note "called Amma, she is fine"

Mode changes are the privilege escalation this whole spec is built around, so
they happen here, deliberately, one family at a time — never as a side effect of
anything else. `live` additionally requires the family to have digests on; that
is a database CHECK, so this command reports the refusal rather than enforcing
it itself.
"""

from __future__ import annotations

import argparse
import os
import sys

import psycopg

from kettle import db
from kettle.ladder import MODE_LIVE, MODE_OFF, MODE_SHADOW, RESOLVED_MANUALLY
from kettle.timeutil import now_utc

MODES = (MODE_OFF, MODE_SHADOW, MODE_LIVE)


def _list_families(conn: psycopg.Connection) -> str:
    rows = conn.execute(
        "select name, ladder_mode, digest_enabled from families order by name"
    ).fetchall()
    if not rows:
        return "No families yet."
    lines = ["Family                          ladder    digests"]
    for row in rows:
        lines.append(
            f"{row['name'][:30]:<31} {row['ladder_mode']:<9} "
            f"{'on' if row['digest_enabled'] else 'off'}"
        )
    return "\n".join(lines)


def _set_mode(conn: psycopg.Connection, family_name: str, mode: str) -> tuple[int, str]:
    family = conn.execute(
        "select id, name, digest_enabled, ladder_mode from families where name = %s",
        (family_name,),
    ).fetchone()
    if family is None:
        return 1, f"No family named {family_name!r}."

    try:
        conn.execute(
            "update families set ladder_mode = %s where id = %s", (mode, family["id"])
        )
    except psycopg.errors.CheckViolation:
        return 1, (
            f"Refused: {family['name']} cannot go live while digests are off. "
            "A family should meet Kettle as reassurance before it meets it as "
            "alarm — enable digests first."
        )

    was = family["ladder_mode"]
    note = {
        MODE_OFF: "Nothing will be evaluated.",
        MODE_SHADOW: (
            "The ladder will run and record in full. No message reaches the "
            "senior or the family; every transition goes to founder ops."
        ),
        MODE_LIVE: (
            "REAL SENDS ARE NOW ON for this family: the senior may receive a "
            "check-in and the family may receive escalations."
        ),
    }[mode]
    return 0, f"{family['name']}: {was} -> {mode}. {note}"


def _resolve(conn: psycopg.Connection, candidate_id: int, note: str) -> tuple[int, str]:
    candidate = conn.execute(
        "select c.*, p.display_name as parent_name, f.name as family_name "
        "from ladder_candidates c "
        "join parents p on p.id = c.parent_id "
        "join families f on f.id = c.family_id "
        "where c.id = %s",
        (candidate_id,),
    ).fetchone()
    if candidate is None:
        return 1, f"No candidate {candidate_id}."
    if candidate["resolved_utc"] is not None:
        return 1, (
            f"Candidate {candidate_id} was already resolved "
            f"({candidate['resolution']})."
        )

    now = now_utc()
    db.resolve_candidate(conn, candidate_id, RESOLVED_MANUALLY, now)
    db.insert_ladder_event(
        conn,
        candidate_id,
        candidate["family_id"],
        candidate["parent_id"],
        "resolved",
        candidate["mode"],
        f"{candidate['parent_name']}: resolved by founder — {note}",
        now,
    )
    return 0, (
        f"Candidate {candidate_id} ({candidate['family_name']} / "
        f"{candidate['parent_name']}) resolved manually."
    )


def main(argv: list[str] | None = None) -> int:
    """Operate the ladder; returns a process exit code."""
    parser = argparse.ArgumentParser(description="Kettle escalation ladder.")
    parser.add_argument("--list", action="store_true", help="show every family's mode")
    parser.add_argument(
        "--set-mode",
        nargs=2,
        metavar=("FAMILY", "MODE"),
        help=f"set a family's ladder mode ({', '.join(MODES)})",
    )
    parser.add_argument("--resolve", type=int, metavar="CANDIDATE_ID")
    parser.add_argument("--note", default="", help="why, for the ledger")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="defaults to $DATABASE_URL",
    )
    args = parser.parse_args(argv)

    if not args.database_url:
        parser.error("DATABASE_URL is not set and --database-url was not given")
    chosen = [bool(args.list), bool(args.set_mode), args.resolve is not None]
    if sum(chosen) != 1:
        parser.error("choose exactly one of --list, --set-mode, --resolve")
    if args.set_mode and args.set_mode[1] not in MODES:
        parser.error(f"mode must be one of {', '.join(MODES)}")
    if args.resolve is not None and not args.note.strip():
        parser.error("--resolve needs a --note: the ledger is the point")

    with db.connect(args.database_url) as conn:
        if args.list:
            print(_list_families(conn))
            return 0
        if args.set_mode:
            code, message = _set_mode(conn, args.set_mode[0], args.set_mode[1])
        else:
            code, message = _resolve(conn, args.resolve, args.note.strip())

    print(message, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
