"""Apply the numbered SQL migrations.

Migrations are plain SQL files (spec 002 §1) so they can be applied by the
supabase CLI or psql without this code existing. This runner is the third
option: it is what the tests use, and it keeps `psql -f` ordering from being
retyped by hand at deploy time.
"""

from __future__ import annotations

from pathlib import Path

import psycopg

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
LOCAL_DIR = MIGRATIONS_DIR / "local"


def migration_files(include_local: bool = False) -> list[Path]:
    """Numbered .sql files in apply order; local shim first when requested."""
    files = sorted(p for p in MIGRATIONS_DIR.glob("*.sql"))
    if include_local:
        return sorted(LOCAL_DIR.glob("*.sql")) + files
    return files


def apply_migrations(conn: psycopg.Connection, include_local: bool = False) -> list[str]:
    """Run every migration in order. Returns the file names applied.

    `include_local` adds the Supabase compatibility shim, which exists only so a
    bare Postgres can run the real migrations unchanged. Never use it against a
    real Supabase project — it already has those objects.
    """
    applied: list[str] = []
    for path in migration_files(include_local):
        conn.execute(path.read_text())
        applied.append(path.name)
    return applied
