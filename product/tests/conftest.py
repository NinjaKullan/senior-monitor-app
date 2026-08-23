"""Test fixtures: a real Postgres, the real migrations, the real RLS policies.

RLS cannot be tested against a fake. Every test here runs on a live Postgres
with `product/migrations/` applied exactly as they would be to a Supabase
project, plus the local shim that supplies the `auth` schema and roles Supabase
would otherwise provide. See product/README.md for the one-command setup.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from kettle import db
from kettle.config import Settings
from kettle.main import create_app
from kettle.migrations import apply_migrations
from testsupport import BASE_URL, TABLES, RecordingNotifier

# Matches the GitHub Actions `postgres` service container defaults, which is why
# this is a throwaway local credential rather than a secret.
DEFAULT_TEST_DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/kettle_test"


@pytest.fixture(scope="session")
def database_url() -> str:
    """Skip the product suite when no test Postgres is reachable."""
    url = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    try:
        with psycopg.connect(url, connect_timeout=3):
            pass
    except psycopg.Error as exc:
        message = (
            "product suite SKIPPED — no Postgres reachable; this is NOT a green "
            f"run of spec 002. Tried {url} ({type(exc).__name__}). "
            "See product/README.md -> Running the tests"
        )
        # CI sets this: there, a missing database is a broken pipeline, not a
        # machine without Postgres installed. It is what retires the "green run
        # that actually skipped everything" failure mode for good.
        if os.environ.get("KETTLE_REQUIRE_POSTGRES", "").strip() not in ("", "0", "false"):
            pytest.fail(message.replace("SKIPPED", "FAILED"), pytrace=False)
        pytest.skip(message)
    return url


@pytest.fixture(scope="session")
def _schema(database_url: str) -> None:
    """Rebuild the schema once per session from the real migration files."""
    with psycopg.connect(database_url, autocommit=True, row_factory=dict_row) as conn:
        conn.execute("drop schema if exists public cascade")
        conn.execute("create schema public")
        apply_migrations(conn, include_local=True)


@pytest.fixture
def conn(database_url: str, _schema: None) -> Iterator[psycopg.Connection]:
    """Service-role connection (bypasses RLS), with a clean database per test."""
    with db.connect(database_url) as c:
        c.execute(f"truncate {', '.join(TABLES)} restart identity cascade")
        yield c


@pytest.fixture
def settings(database_url: str) -> Settings:
    """App settings pointed at the test database, heartbeat loop disabled."""
    return Settings(
        database_url=database_url,
        ntfy_topic="",
        ip_hash_salt="test-salt",
        default_tz="Asia/Kolkata",
        public_base_url=BASE_URL,
        heartbeat_loop=False,
        # On, so the tests exercise the engine; the kill-switch has its own
        # test. Wave A's only transport still sends nothing.
        outbound_enabled=True,
        # Off like heartbeat_loop: tests drive run_outbound with their own
        # clocks; the loop has its own lifecycle tests.
        outbound_loop=False,
        outbound_transport="console",
        outbound_reply_token="test-reply-token",
        # The landing page is the only browser that calls this API (spec 006).
        waitlist_origins=("https://heykettle.com",),
    )


@pytest.fixture
def notifier() -> RecordingNotifier:
    return RecordingNotifier()


@pytest.fixture
def client(
    settings: Settings, notifier: RecordingNotifier, conn: psycopg.Connection
) -> Iterator[TestClient]:
    with TestClient(create_app(settings, notifier)) as c:
        yield c


@pytest.fixture
def authed(database_url: str, _schema: None) -> Iterator[psycopg.Connection]:
    """A connection acting as an end user, exactly as the future PWA will.

    `set role authenticated` drops superuser, so the policies actually apply;
    the JWT is simulated the way Supabase publishes it, via `request.jwt.claims`.
    """
    with psycopg.connect(database_url, autocommit=True, row_factory=dict_row) as c:
        c.execute("set role authenticated")
        yield c
