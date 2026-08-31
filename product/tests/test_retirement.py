"""Specs 003 and 004 are retired, and the retirement is checked rather than assumed.

Spec 007 supersedes both (DECISIONS 141). Three kinds of assertion here:

* The code is gone, and nothing still reaches for it. A dangling import is the
  usual way half a retirement ships.
* The migration's **archive** branch works. Every other test in this suite runs
  against a database whose ladder tables were empty, so only the drop branch is
  ever exercised — and production is the case where rows might exist. This
  builds that case on purpose.
* `digest_sends` survives, because the family app reads it. That is not an
  oversight in the migration; it is the one thing the retirement deliberately
  did not do, and a test is how it stays deliberate.
"""

from __future__ import annotations

from pathlib import Path

import psycopg
import pytest
from psycopg.rows import dict_row

from kettle.migrations import apply_migrations, migration_files

PRODUCT = Path(__file__).resolve().parents[1]

#: What went, and what it took with it.
RETIRED_MODULES = (
    "kettle/digest.py",
    "kettle/ladder.py",
    "kettle/ladder_messages.py",
    "kettle/messages.py",
    "kettle/channels.py",
    "scripts/ladder.py",
)
# `kettle/twilio_signature.py` was on this list from the spec-004 retirement
# until Wave C REBUILT it for /outbound/reply (DECISIONS 163) — a fresh module
# doing the same job for a different route, written new rather than
# resurrected. It leaves the retired set deliberately, not by drift.
RETIRED_TABLES = ("ladder_candidates", "ladder_events", "family_contacts")
# `family_contacts` left this list's FRESH-SCHEMA check with migration 0021
# (spec 012): the name is reborn as the family's own contacts sheet — a new
# table doing a different job, written new rather than resurrected, the same
# way kettle/twilio_signature.py left the retired modules (DECISIONS 163).
# The 0013 archive test below still uses the full tuple, because it exercises
# the OLD table's retirement at the 0012 schema, where only the old one exists.
FRESH_SCHEMA_RETIRED = ("ladder_candidates", "ladder_events")


def test_the_retired_modules_are_gone():
    for relative in RETIRED_MODULES:
        assert not (PRODUCT / relative).exists(), f"{relative} is still here"


def test_nothing_imports_them():
    """A dangling import is how half a retirement ships."""
    offenders = []
    for path in PRODUCT.rglob("*.py"):
        if "__pycache__" in str(path) or path.name == Path(__file__).name:
            continue
        source = path.read_text()
        for module in ("digest", "ladder", "ladder_messages", "messages", "channels"):
            for form in (f"from kettle.{module} import", f"from kettle import {module}"):
                if form in source:
                    offenders.append(f"{path.relative_to(PRODUCT)}: {form}")
    assert offenders == []


def test_the_twilio_webhook_is_gone(client):
    """The route the retired ladder resolved its ask through."""
    assert client.post("/twilio/inbound", data={"From": "+15125550100"}).status_code == 404


def test_the_ladder_tables_are_gone_from_a_fresh_schema(conn: psycopg.Connection):
    for table in FRESH_SCHEMA_RETIRED:
        row = conn.execute(
            "select to_regclass(%s) as found", (f"public.{table}",)
        ).fetchone()
        assert row["found"] is None, f"{table} is still here"




@pytest.fixture
def half_migrated(database_url: str):
    """A database with 0001–0012 applied and nothing after, on its own name."""
    name = "kettle_retirement_test"
    maintenance = database_url.rsplit("/", 1)[0] + "/postgres"
    try:
        with psycopg.connect(maintenance, autocommit=True) as admin:
            admin.execute(f'drop database if exists "{name}"')
            admin.execute(f'create database "{name}"')
    except psycopg.errors.InsufficientPrivilege:  # pragma: no cover - CI has rights
        pytest.skip("test role cannot create databases")

    url = database_url.rsplit("/", 1)[0] + f"/{name}"
    try:
        with psycopg.connect(url, autocommit=True, row_factory=dict_row) as conn:
            for path in migration_files(include_local=True):
                if path.name.startswith("0013"):
                    break
                conn.execute(path.read_text())
        yield url
    finally:
        with psycopg.connect(maintenance, autocommit=True) as admin:
            admin.execute(
                "select pg_terminate_backend(pid) from pg_stat_activity "
                "where datname = %s and pid <> pg_backend_pid()",
                (name,),
            )
            admin.execute(f'drop database if exists "{name}"')


def test_a_table_with_rows_is_archived_rather_than_dropped(half_migrated: str):
    """The branch production might take, built on purpose.

    Shadow-mode ladder rows are the labelled ledger that was meant to tune the
    thresholds. Deleting them silently would be the wrong call to make on
    someone else's behalf, so a table that holds anything is renamed, stripped
    of its policies and revoked — history kept, reach removed.
    """
    with psycopg.connect(half_migrated, autocommit=True, row_factory=dict_row) as conn:
        family = conn.execute(
            "insert into families (name, tz) values ('Sharma', 'Asia/Kolkata') returning id"
        ).fetchone()["id"]
        conn.execute(
            "insert into family_contacts (family_id, name, phone_e164, relation) "
            "values (%s, 'Neighbour', '+919845550100', 'friend')",
            (family,),
        )

        # Apply only 0013, the way a real deploy would reach it.
        retirement = next(p for p in migration_files() if p.name.startswith("0013"))
        conn.execute(retirement.read_text())

        assert conn.execute(
            "select to_regclass('public.family_contacts') as found"
        ).fetchone()["found"] is None
        archived = conn.execute(
            "select to_regclass('public.retired_family_contacts') as found"
        ).fetchone()["found"]
        assert archived is not None, "a table with rows was dropped instead of archived"

        # The rows survived.
        assert conn.execute(
            "select count(*) as n from retired_family_contacts"
        ).fetchone()["n"] == 1
        # And nothing can reach them: no policy, and no privilege either.
        assert conn.execute(
            "select count(*) as n from pg_policies "
            "where schemaname = 'public' and tablename = 'retired_family_contacts'"
        ).fetchone()["n"] == 0
        for role in ("anon", "authenticated"):
            granted = conn.execute(
                "select count(*) as n from information_schema.table_privileges "
                "where table_name = 'retired_family_contacts' and grantee = %s",
                (role,),
            ).fetchone()["n"]
            assert granted == 0, f"{role} still holds a privilege on the archive"

        # The empty ones took the other branch in the same run.
        for table in ("ladder_candidates", "ladder_events"):
            assert conn.execute(
                "select to_regclass(%s) as found", (f"public.{table}",)
            ).fetchone()["found"] is None
            assert conn.execute(
                "select to_regclass(%s) as found", (f"public.retired_{table}",)
            ).fetchone()["found"] is None


def test_digest_sends_survives_the_retirement_migration(half_migrated: str):
    """The one table the retirement deliberately left alone.

    `webapp/src/lib/queries.ts` declares it in the app's READ_SURFACE and the
    Digests screen renders from it. Spec 007's `sent_messages` is RLS deny-all
    by design, so it is not a replacement — moving the screen is a decision, not
    a migration. **If this fails, read DECISIONS 141 before "fixing" it**: the
    likely cause is somebody tidying `digest_sends` into 0013's retire list,
    and the repair is to take it back out, not to drop the screen.

    Deliberately on `half_migrated` rather than the shared `conn`. On the shared
    database this assertion never gets to run — `testsupport.TABLES` truncates
    `digest_sends`, so retiring it blows the fixture up first, and the failure a
    maintainer reads is "relation digest_sends does not exist" pointing at the
    fixture. That reads like an invitation to delete the fixture's reference,
    which is precisely the wrong repair. Here the migration is applied by the
    test itself, so the named assertion below is what fails.
    """
    retirement = next(p for p in migration_files() if p.name.startswith("0013"))
    with psycopg.connect(half_migrated, autocommit=True, row_factory=dict_row) as conn:
        conn.execute(retirement.read_text())
        assert conn.execute(
            "select to_regclass('public.digest_sends') as found"
        ).fetchone()["found"] is not None, (
            "the retirement took digest_sends with it — the family app's Digests "
            "screen reads this table. See DECISIONS 141."
        )
        assert conn.execute(
            "select count(*) as n from pg_policies "
            "where schemaname = 'public' and tablename = 'digest_sends'"
        ).fetchone()["n"] > 0, "digest_sends lost the policy the family app reads through"


def test_the_retirement_migration_is_safe_to_run_twice(half_migrated: str):
    """A migration runner that re-applies must not fail on already-gone tables."""
    retirement = next(p for p in migration_files() if p.name.startswith("0013"))
    with psycopg.connect(half_migrated, autocommit=True, row_factory=dict_row) as conn:
        conn.execute(retirement.read_text())
        conn.execute(retirement.read_text())


def test_every_migration_still_applies_in_order(conn: psycopg.Connection):
    """0022 is the last one, and the numbering has no gap."""
    names = [p.name for p in migration_files()]
    assert names[-1].startswith("0022")
    numbers = [int(name[:4]) for name in names]
    assert numbers == list(range(1, len(numbers) + 1))
    assert apply_migrations is not None
