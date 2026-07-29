"""Apply the SQL migrations to a database.

    python -m scripts.migrate                 # against $DATABASE_URL
    python -m scripts.migrate --local         # plus the local Postgres shim

`--local` is for a bare Postgres (CI, a container, your laptop). Never use it
against a real Supabase project: it already provides the auth schema and roles.
"""

from __future__ import annotations

import argparse
import os
import sys

from kettle import db
from kettle.migrations import apply_migrations


def main(argv: list[str] | None = None) -> int:
    """Apply migrations; returns a process exit code."""
    parser = argparse.ArgumentParser(description="Apply Kettle SQL migrations.")
    parser.add_argument(
        "--local",
        action="store_true",
        help="also apply the local Supabase shim (bare Postgres only)",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="defaults to $DATABASE_URL",
    )
    args = parser.parse_args(argv)

    if not args.database_url:
        parser.error("DATABASE_URL is not set and --database-url was not given")

    with db.connect(args.database_url) as conn:
        for name in apply_migrations(conn, include_local=args.local):
            print(f"applied {name}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
