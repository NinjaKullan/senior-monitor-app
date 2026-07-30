"""Acceptance criteria 7 and 8 — a fresh database boots, and the pilot is untouched."""

from __future__ import annotations

import re
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import dict_row

from kettle.config import Settings
from kettle.main import create_app
from kettle.migrations import apply_migrations, migration_files
from testsupport import BASE_URL, FAMILY_TABLES, TABLES, object_privileges

FRESH_DB = "kettle_fresh_boot_test"
PRODUCT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PRODUCT_ROOT.parent

# `import app` / `from app import ...` — the pilot package.
PILOT_IMPORT = re.compile(r"^\s*(?:from|import)\s+app(?:\.|\s|$)", re.MULTILINE)


def _maintenance_url(database_url: str) -> str:
    info = conninfo_to_dict(database_url)
    info["dbname"] = "postgres"
    return make_conninfo(**info)


def _fresh_url(database_url: str) -> str:
    info = conninfo_to_dict(database_url)
    info["dbname"] = FRESH_DB
    return make_conninfo(**info)


@pytest.fixture
def fresh_database(database_url: str):
    """A genuinely empty database, created and dropped around the test."""
    maintenance = _maintenance_url(database_url)
    try:
        with psycopg.connect(maintenance, autocommit=True) as admin:
            admin.execute(f'drop database if exists "{FRESH_DB}"')
            admin.execute(f'create database "{FRESH_DB}"')
    except psycopg.errors.InsufficientPrivilege:
        pytest.skip("test role cannot create databases")

    try:
        yield _fresh_url(database_url)
    finally:
        with psycopg.connect(maintenance, autocommit=True) as admin:
            admin.execute(
                "select pg_terminate_backend(pid) from pg_stat_activity "
                "where datname = %s and pid <> pg_backend_pid()",
                (FRESH_DB,),
            )
            admin.execute(f'drop database if exists "{FRESH_DB}"')


def test_empty_database_boots_and_passes_healthz(fresh_database: str, notifier):
    """AC7, code half: migrations on an empty database, then a green health check.

    The Fly/Supabase deploy itself is a founder step; product/README.md carries
    the exact commands. This proves the half that can be proven here: nothing in
    the schema depends on state left behind by a previous deploy.
    """
    with psycopg.connect(fresh_database, autocommit=True, row_factory=dict_row) as conn:
        applied = apply_migrations(conn, include_local=True)
        assert [name for name in applied if not name.startswith("0000")] == [
            path.name for path in migration_files()
        ]

        tables = {
            r["table_name"]
            for r in conn.execute(
                "select table_name from information_schema.tables "
                "where table_schema = 'public'"
            ).fetchall()
        }
        assert tables == set(TABLES)

        policies = conn.execute(
            "select tablename from pg_policies where schemaname = 'public'"
        ).fetchall()
        assert {p["tablename"] for p in policies} == set(TABLES) - {"ops_alerts"}

    settings = Settings(
        database_url=fresh_database,
        ntfy_topic="",
        ip_hash_salt="salt",
        default_tz="Asia/Kolkata",
        public_base_url=BASE_URL,
        heartbeat_loop=False,
        digest_enabled=False,
        digest_morning_cutoff_hour=14,
        digest_evening_hour=20,
        digest_evening_minute=30,
        twilio_account_sid="",
        twilio_auth_token="",
        twilio_from="",
    )
    with TestClient(create_app(settings, notifier)) as fresh_client:
        assert fresh_client.get("/healthz").json() == {"db": True}


def test_anon_grant_exists_before_0003_and_is_gone_after(fresh_database: str):
    """0003 is load-bearing, not decoration — prove the grant it removes is real.

    Supabase's default privileges hand EXECUTE to anon at function-creation time.
    The local shim reproduces that, so this asserts the whole sequence: after
    0002 the grant is there (as it was in production), and 0003 is what takes it
    away. If someone drops either the migration or the shim line, this fails.
    """
    files = migration_files(include_local=True)
    revoke = next(p for p in files if p.name.startswith("0003"))
    before = files[: files.index(revoke)]

    privilege = (
        "select has_function_privilege('anon', oid, 'execute') as anon_exec "
        "from pg_proc where proname = 'app_current_family_ids'"
    )

    with psycopg.connect(fresh_database, autocommit=True, row_factory=dict_row) as conn:
        for path in before:
            conn.execute(path.read_text())
        assert conn.execute(privilege).fetchone()["anon_exec"] is True

        conn.execute(revoke.read_text())
        assert conn.execute(privilege).fetchone()["anon_exec"] is False


def test_residual_privileges_exist_before_0004_and_are_gone_after(fresh_database: str):
    """0004 is load-bearing — reproduce what production actually had, then fix it.

    The PM's audit found anon holding the full privilege set (TRUNCATE included)
    on all seven tables, and authenticated holding TRUNCATE/REFERENCES/TRIGGER
    plus SELECT on ops_alerts. The shim reproduces the bootstrap that caused it,
    so this asserts the same before-state and that 0004 is what clears it.
    """
    files = migration_files(include_local=True)
    revoke = next(p for p in files if p.name.startswith("0004"))
    before = files[: files.index(revoke)]

    with psycopg.connect(fresh_database, autocommit=True, row_factory=dict_row) as conn:
        for path in before:
            conn.execute(path.read_text())

        # Tables that exist at this point in the sequence — later migrations add
        # more, and those inherit the cleaned defaults rather than the bootstrap.
        existing = {
            r["table_name"]
            for r in conn.execute(
                "select table_name from information_schema.tables "
                "where table_schema = 'public'"
            ).fetchall()
        }
        assert existing <= set(TABLES)

        held = object_privileges(conn, ["anon", "authenticated"])
        # anon had everything, on every table.
        for table in existing:
            assert held[("anon", table)] >= {
                "SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER",
            }
            assert held[("authenticated", table)] >= {"TRUNCATE", "REFERENCES", "TRIGGER"}
        assert "SELECT" in held[("authenticated", "ops_alerts")]
        # Identity-column sequences were caught by the same bootstrap.
        assert any(key[1].endswith("_id_seq") for key in held)

        conn.execute(revoke.read_text())

        after = object_privileges(conn, ["anon", "authenticated"])
        assert after == {
            ("authenticated", table): {"SELECT"}
            for table in FAMILY_TABLES
            if table in existing
        }

        # Future objects must not re-acquire any of it.
        #
        # Scoped to defaults owned by the migrating role on purpose. ALTER
        # DEFAULT PRIVILEGES only ever touches one role's defaults, and in
        # production pg_default_acl also holds rows owned by `supabase_admin`
        # that still name anon/authenticated. Those govern objects created by
        # the platform's own machinery, not by our migrations, and cannot be
        # altered from the postgres role — so an unscoped version of this
        # assertion would fail against production and read as "0004 didn't
        # work" when the app-owned defaults are in fact clean.
        defaults = conn.execute(
            "select defaclobjtype, defaclacl::text as acl from pg_default_acl d "
            "join pg_namespace n on n.oid = d.defaclnamespace "
            "where n.nspname = 'public' "
            "  and pg_get_userbyid(d.defaclrole) = current_user"
        ).fetchall()
        assert defaults  # service_role keeps its defaults; an empty set means bad scoping
        for row in defaults:
            assert "anon=" not in row["acl"]
            assert "authenticated=" not in row["acl"]


def test_migrations_are_numbered_and_ordered():
    """Applied in filename order, so the numbering is the contract."""
    names = [path.name for path in migration_files()]
    assert names == sorted(names)
    assert names[0].startswith("0001")
    for name in names:
        assert re.match(r"^\d{4}_[a-z0-9_]+\.sql$", name), name


def test_local_shim_is_not_part_of_the_real_migrations():
    """The shim must never reach a Supabase project — it lives outside the sequence."""
    assert all("local" not in str(path.parent.name) for path in migration_files())
    shim = PRODUCT_ROOT / "migrations" / "local" / "0000_supabase_shim.sql"
    assert shim.exists()
    assert "LOCAL / CI ONLY" in shim.read_text()


def test_product_shares_no_runtime_with_the_pilot():
    """AC8: `product/` must not import the pilot package, now or by accident later."""
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in PRODUCT_ROOT.rglob("*.py")
        if PILOT_IMPORT.search(path.read_text())
    ]
    assert offenders == []


def test_pilot_directory_is_not_referenced_by_product_config():
    """The two deployments share a repo and nothing else."""
    for name in ("Dockerfile", "fly.toml"):
        text = (PRODUCT_ROOT / name).read_text()
        assert "app/" not in text
        assert "pilot.db" not in text
