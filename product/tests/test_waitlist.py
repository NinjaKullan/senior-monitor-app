"""The landing page's waitlist (spec 006 §7, AC13).

The endpoint's job is small; the discipline around it is not. Everything below
is a test of something that must *not* be observable — that a repeat signup
looks like a first one, that a trapped bot looks like a success, that the client
roles cannot touch the table at all, and that the child app never learns the
table exists. A public write endpoint on a product about not collecting things
deserves that scrutiny.
"""

from __future__ import annotations

import re
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient

from kettle import waitlist
from kettle.main import HONEYPOT_FIELD
from testsupport import as_user

SITE_COPY_TS = Path(__file__).resolve().parent.parent.parent / "site" / "src" / "copy.ts"
USER = "33333333-3333-3333-3333-333333333333"

SIGNUP = {"email": "Child@Example.COM", "parent_phone": "iphone"}


def rows(conn: psycopg.Connection) -> list[dict]:
    return conn.execute("select email, parent_phone from waitlist order by email").fetchall()


# ---------------------------------------------------------------------------
# The endpoint
# ---------------------------------------------------------------------------


def test_a_signup_is_stored_lowercased(client: TestClient, conn: psycopg.Connection):
    response = client.post("/waitlist", json=SIGNUP)

    assert response.status_code == 200
    assert response.text == waitlist.WAITLIST_SUCCESS
    assert rows(conn) == [{"email": "child@example.com", "parent_phone": "iphone"}]


def test_the_form_degrades_to_a_plain_post(client: TestClient, conn: psycopg.Connection):
    """AC9: with JavaScript off the browser posts the form directly here."""
    response = client.post("/waitlist", data=SIGNUP)

    assert response.status_code == 200
    assert response.text == waitlist.WAITLIST_SUCCESS
    assert len(rows(conn)) == 1


def test_the_optional_note_is_stored_and_capped(client: TestClient, conn: psycopg.Connection):
    """DECISIONS 129: one free-text kindness, bounded, never a reason to fail."""
    noted = {**SIGNUP, "help_with": "  Mostly the mornings, when nobody has heard yet.  "}
    assert client.post("/waitlist", json=noted).status_code == 200
    stored = conn.execute("select help_with from waitlist").fetchone()["help_with"]
    assert stored == "Mostly the mornings, when nobody has heard yet."

    # Overlong answers are trimmed to the cap, not rejected: this field is a
    # kindness, not a gate, and a signup must never be lost to a long story.
    conn.execute("delete from waitlist")
    long = {**SIGNUP, "help_with": "a" * 5000}
    assert client.post("/waitlist", json=long).status_code == 200
    stored = conn.execute("select help_with from waitlist").fetchone()["help_with"]
    assert len(stored) == waitlist.MAX_HELP_WITH_LENGTH


def test_an_empty_note_is_stored_as_absence(client: TestClient, conn: psycopg.Connection):
    assert client.post("/waitlist", json={**SIGNUP, "help_with": "   "}).status_code == 200
    assert conn.execute("select help_with from waitlist").fetchone()["help_with"] is None
    # And the field is genuinely optional: the pre-0011 payload still works.
    conn.execute("delete from waitlist")
    assert client.post("/waitlist", json=SIGNUP).status_code == 200
    assert conn.execute("select help_with from waitlist").fetchone()["help_with"] is None


def test_a_silent_resignup_keeps_the_note_and_a_retyped_one_replaces_it(
    client: TestClient, conn: psycopg.Connection
):
    """Silence is not an erasure request; retyping is a correction."""
    client.post("/waitlist", json={**SIGNUP, "help_with": "The mornings."})
    client.post("/waitlist", json={"email": SIGNUP["email"], "parent_phone": "android"})
    assert conn.execute("select help_with from waitlist").fetchone()["help_with"] == (
        "The mornings."
    )

    client.post("/waitlist", json={**SIGNUP, "help_with": "Actually the evenings."})
    assert conn.execute("select help_with from waitlist").fetchone()["help_with"] == (
        "Actually the evenings."
    )


def test_the_note_survives_the_no_javascript_form_post(
    client: TestClient, conn: psycopg.Connection
):
    """AC9 reaches the new field too: url-encoded and JSON must store alike."""
    response = client.post("/waitlist", data={**SIGNUP, "help_with": "Weekends."})
    assert response.status_code == 200
    assert conn.execute("select help_with from waitlist").fetchone()["help_with"] == "Weekends."


def test_the_column_wall_holds_even_past_the_normaliser(conn: psycopg.Connection):
    """The CHECK is the wall: an unbounded blob is unrepresentable, so a future
    code path that forgets the trim gets a loud integrity error, not storage."""
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "insert into waitlist (email, parent_phone, help_with) values (%s, %s, %s)",
            ("wall@example.com", "iphone", "a" * 1001),
        )


def test_a_duplicate_signup_is_indistinguishable_from_a_first_one(
    client: TestClient, conn: psycopg.Connection
):
    """Otherwise the endpoint answers "is this person on the list"."""
    first = client.post("/waitlist", json=SIGNUP)
    again = {"email": "child@example.com", "parent_phone": "android"}
    second = client.post("/waitlist", json=again)

    assert (second.status_code, second.text) == (first.status_code, first.text)
    # One row, and the later answer won — someone signing up twice has usually
    # corrected something.
    assert rows(conn) == [{"email": "child@example.com", "parent_phone": "android"}]


def test_a_honeypot_submission_looks_exactly_like_a_success(
    client: TestClient, conn: psycopg.Connection
):
    """Telling a bot it was caught teaches it which field to leave alone."""
    real = client.post("/waitlist", json=SIGNUP)
    conn.execute("delete from waitlist")

    trapped = client.post(
        "/waitlist",
        json={"email": "bot@example.com", "parent_phone": "iphone", HONEYPOT_FIELD: "Acme Inc"},
    )

    assert (trapped.status_code, trapped.text) == (real.status_code, real.text)
    assert rows(conn) == []


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-address", "parent_phone": "iphone"},
        {"email": "", "parent_phone": "iphone"},
        {"email": "child@example.com", "parent_phone": "blackberry"},
        {"email": "child@example.com"},
        {"parent_phone": "iphone"},
        {"email": "a@b.co", "parent_phone": ""},
    ],
)
def test_a_malformed_signup_is_rejected_and_stores_nothing(
    client: TestClient, conn: psycopg.Connection, payload: dict
):
    assert client.post("/waitlist", json=payload).status_code == 400
    assert rows(conn) == []


def test_an_over_long_address_is_rejected(client: TestClient, conn: psycopg.Connection):
    """The column is not a storage primitive for someone with a script."""
    huge = "a" * waitlist.MAX_EMAIL_LENGTH + "@example.com"
    response = client.post("/waitlist", json={"email": huge, "parent_phone": "iphone"})
    assert response.status_code == 400
    assert rows(conn) == []


def test_malformed_json_does_not_crash_the_endpoint(client: TestClient):
    response = client.post(
        "/waitlist", content=b"{not json", headers={"content-type": "application/json"}
    )
    assert response.status_code == 400


def test_the_endpoint_stores_only_what_was_typed(client: TestClient, conn: psycopg.Connection):
    """Law #4 at the schema: no IP, no user agent, no referrer, no analytics.

    The page carries no tracking, and the endpoint behind it does not get to
    become the tracking by the back door — so the columns are asserted, not the
    intention. `help_with` joined in 0011 (DECISIONS 129) and honours the same
    rule from the other side: it holds only what the person themselves typed
    into a labelled, optional box, and nothing arrives in it any other way.
    """
    client.post(
        "/waitlist",
        json=SIGNUP,
        headers={"user-agent": "Mozilla/5.0 (test)", "referer": "https://heykettle.com/"},
    )

    columns = {
        r["column_name"]
        for r in conn.execute(
            "select column_name from information_schema.columns "
            "where table_schema = 'public' and table_name = 'waitlist'"
        ).fetchall()
    }
    assert columns == {"id", "email", "parent_phone", "created_at", "help_with"}
    # And the headers the request carried really did vanish at the door.
    row = conn.execute("select help_with from waitlist").fetchone()
    assert row["help_with"] is None


def test_cors_is_locked_to_the_landing_page(client: TestClient):
    """A wildcard would let any page on the internet post on a visitor's behalf."""
    allowed = client.post("/waitlist", json=SIGNUP, headers={"origin": "https://heykettle.com"})
    assert allowed.headers.get("access-control-allow-origin") == "https://heykettle.com"

    elsewhere = client.post(
        "/waitlist",
        json={"email": "b@c.co", "parent_phone": "iphone"},
        headers={"origin": "https://evil.test"},
    )
    assert "access-control-allow-origin" not in elsewhere.headers


# ---------------------------------------------------------------------------
# The table
# ---------------------------------------------------------------------------


def test_no_client_role_can_read_or_write_the_waitlist(authed: psycopg.Connection):
    """AC13: RLS on, zero policies, zero privileges — denied twice over."""
    as_user(authed, USER)

    for statement in (
        "select email from waitlist",
        "insert into waitlist (email, parent_phone) values ('x@y.co', 'iphone')",
        "delete from waitlist",
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            authed.execute(statement)


def test_the_waitlist_has_no_policy_at_all(conn: psycopg.Connection):
    """The absence *is* the access control, so it is asserted rather than assumed."""
    policies = conn.execute(
        "select policyname from pg_policies where schemaname = 'public' and tablename = 'waitlist'"
    ).fetchall()
    assert policies == []
    assert conn.execute(
        "select relrowsecurity from pg_class where relname = 'waitlist'"
    ).fetchone()["relrowsecurity"]


def test_the_phone_answer_is_a_check_constraint_not_a_convention(conn: psycopg.Connection):
    """Standing structure 39: make the wrong state unrepresentable."""
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("insert into waitlist (email, parent_phone) values ('a@b.co', 'blackberry')")


def test_the_schema_refuses_an_uppercased_address(conn: psycopg.Connection):
    """The API lowercases; the column insists, so uniqueness cannot be dodged by case."""
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("insert into waitlist (email, parent_phone) values ('A@b.co', 'iphone')")


def test_the_webapp_read_surface_never_learns_this_table_exists():
    """AC13, and standing structure 48: the child app reads families, not signups."""
    queries = (
        Path(__file__).resolve().parent.parent.parent / "webapp" / "src" / "lib" / "queries.ts"
    )
    assert "waitlist" not in queries.read_text()


# ---------------------------------------------------------------------------
# The one string this endpoint says
# ---------------------------------------------------------------------------


def test_the_success_sentence_matches_the_landing_page():
    """Item 47's guard, applied to the one sentence that lives in two languages.

    The no-JS path renders whatever the API returns; the fetch path renders the
    string from copy.ts. If they drift, one visitor in ten sees different words
    from the rest and nobody finds out.
    """
    source = SITE_COPY_TS.read_text()
    match = re.search(r'export const WAITLIST_SUCCESS = "([^"]+)";', source)
    assert match, "WAITLIST_SUCCESS not found in site/src/copy.ts"
    assert match.group(1) == waitlist.WAITLIST_SUCCESS


def test_the_default_origin_list_is_the_live_domain_and_nothing_else():
    """DECISIONS 142 — what the system settles on when nobody sets the env var.

    Two claims, and the second is the one worth a test. The default names
    heykettle.com; it deliberately does **not** name `kettle-site.fly.dev`, even
    though that origin has to be accepted while the domain transitions. The
    transition grant belongs in `WAITLIST_ORIGINS` on kettle-api, where removing
    it is one command, rather than in a shipped default nobody revisits — a
    temporary allowance written into code is a permanent one.
    """
    from kettle.config import DEFAULT_WAITLIST_ORIGINS

    assert DEFAULT_WAITLIST_ORIGINS == (
        "https://heykettle.com",
        "https://www.heykettle.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
    assert not any("getkettle" in origin for origin in DEFAULT_WAITLIST_ORIGINS)
    assert not any("fly.dev" in origin for origin in DEFAULT_WAITLIST_ORIGINS)
    assert not any("*" in origin for origin in DEFAULT_WAITLIST_ORIGINS)


def test_setting_the_env_var_replaces_the_default_rather_than_adding_to_it():
    """The shape of the founder's command depends on this, so it is pinned.

    `_origins` falls back to the default only when the variable is empty. A list
    that names just the fly.dev origin locks out the real domain — which is why
    product/README.md prints the whole list rather than the one addition.
    """
    from kettle.config import DEFAULT_WAITLIST_ORIGINS, settings_from_env

    only_old = settings_from_env(
        {"DATABASE_URL": "postgresql:///x", "WAITLIST_ORIGINS": "https://kettle-site.fly.dev"}
    )
    assert only_old.waitlist_origins == ("https://kettle-site.fly.dev",)
    assert "https://heykettle.com" not in only_old.waitlist_origins

    empty = settings_from_env({"DATABASE_URL": "postgresql:///x"})
    assert empty.waitlist_origins == DEFAULT_WAITLIST_ORIGINS


# --- flood guards (DECISIONS 307) ---------------------------------------------------


class _Clock:
    def __init__(self) -> None:
        from datetime import UTC, datetime

        self.now = datetime(2026, 9, 7, 15, 0, tzinfo=UTC)

    def __call__(self):
        return self.now

    def advance(self, **delta) -> None:
        from datetime import timedelta

        self.now = self.now + timedelta(**delta)


@pytest.fixture
def flood(settings, notifier, conn):
    """A client on a clock the tests can move, with its app to hand."""
    from kettle.main import create_app

    clock = _Clock()
    with TestClient(create_app(settings, notifier, clock)) as c:
        yield c, clock


def _signup(client: TestClient, n: int, ip: str | None = "203.0.113.7"):
    headers = {"fly-client-ip": ip} if ip else {}
    return client.post(
        "/waitlist",
        json={"email": f"person{n}@example.com", "parent_phone": "iphone"},
        headers=headers,
    )


def test_the_sixth_post_from_one_ip_in_an_hour_is_a_quiet_refusal(flood, conn):
    client, _ = flood
    for n in range(waitlist.RATE_LIMIT):
        assert _signup(client, n).status_code == 200
    assert len(rows(conn)) == waitlist.RATE_LIMIT

    sixth = _signup(client, 99)
    assert (sixth.status_code, sixth.text) == (200, waitlist.WAITLIST_SUCCESS)
    assert len(rows(conn)) == waitlist.RATE_LIMIT
    # Another caller in the same minute is stored.
    assert _signup(client, 100, ip="198.51.100.9").status_code == 200
    assert {r["email"] for r in rows(conn)} >= {"person100@example.com"}
    assert "person99@example.com" not in {r["email"] for r in rows(conn)}


def test_the_limit_is_a_rolling_hour_on_the_injected_clock(flood, conn):
    client, clock = flood
    for n in range(waitlist.RATE_LIMIT):
        _signup(client, n)
    assert "person50@example.com" not in {r["email"] for r in rows(conn)}
    _signup(client, 50)
    assert "person50@example.com" not in {r["email"] for r in rows(conn)}
    clock.advance(minutes=59)
    _signup(client, 51)
    assert "person51@example.com" not in {r["email"] for r in rows(conn)}
    clock.advance(minutes=1, seconds=1)
    _signup(client, 52)
    assert "person52@example.com" in {r["email"] for r in rows(conn)}


def test_fly_client_ip_is_the_key_and_the_socket_stands_in_without_it(flood, conn):
    client, _ = flood
    for n in range(waitlist.RATE_LIMIT):
        _signup(client, n, ip="203.0.113.1")
    assert _signup(client, 10, ip="203.0.113.1").text == waitlist.WAITLIST_SUCCESS
    assert "person10@example.com" not in {r["email"] for r in rows(conn)}
    # A different header value is a different caller.
    _signup(client, 11, ip="203.0.113.2")
    assert "person11@example.com" in {r["email"] for r in rows(conn)}
    # No header at all: the socket address (the test client's) is the key,
    # and it has its own budget.
    for n in range(20, 20 + waitlist.RATE_LIMIT):
        _signup(client, n, ip=None)
    _signup(client, 30, ip=None)
    emails = {r["email"] for r in rows(conn)}
    assert f"person{20 + waitlist.RATE_LIMIT - 1}@example.com" in emails
    assert "person30@example.com" not in emails


def test_the_counter_is_process_local_and_resets_on_restart(settings, notifier, conn):
    """Accepted for a one-machine app (307): the count lives in the process."""
    from kettle.main import create_app

    with TestClient(create_app(settings, notifier)) as first:
        for n in range(waitlist.RATE_LIMIT + 1):
            _signup(first, n)
    assert f"person{waitlist.RATE_LIMIT}@example.com" not in {r["email"] for r in rows(conn)}
    with TestClient(create_app(settings, notifier)) as second:
        _signup(second, 77)
    assert "person77@example.com" in {r["email"] for r in rows(conn)}


def test_memory_stays_bounded_past_ten_thousand_distinct_callers():
    from datetime import UTC, datetime, timedelta

    counter = waitlist.FloodCounter()
    now = datetime(2026, 9, 7, tzinfo=UTC)
    for i in range(waitlist.RATE_MAX_KEYS + 500):
        assert counter.allow(f"10.0.{i // 256}.{i % 256}", now)
    assert len(counter) == waitlist.RATE_MAX_KEYS
    # The oldest keys were the ones dropped: they get a fresh budget, the
    # newest still carry their hit.
    assert counter.allow("10.0.0.0", now)
    # And stale keys are pruned as time passes, not only at the bound.
    counter.allow("fresh", now + timedelta(hours=1, seconds=1))
    assert len(counter) == 1


def test_the_table_cap_refuses_quietly_and_blocks_a_resignup_too(
    client: TestClient, conn: psycopg.Connection, monkeypatch
):
    monkeypatch.setattr(waitlist, "WAITLIST_CAP", 2)
    for email in ("one@example.com", "two@example.com"):
        conn.execute("insert into waitlist (email, parent_phone) values (%s, 'android')", (email,))
    before = rows(conn)

    refused = client.post("/waitlist", json=SIGNUP)
    assert (refused.status_code, refused.text) == (200, waitlist.WAITLIST_SUCCESS)
    assert rows(conn) == before

    # A correction of an existing address past the cap changes nothing either.
    again = client.post("/waitlist", json={"email": "one@example.com", "parent_phone": "iphone"})
    assert again.text == waitlist.WAITLIST_SUCCESS
    assert rows(conn) == before
    assert waitlist.record(conn, "one@example.com", "iphone") is False


def test_a_refusal_on_either_guard_is_byte_identical_to_a_first_signup(flood, conn, monkeypatch):
    """The 116 rule, extended: over the limit and over the cap say exactly
    what a first signup says, and record nothing anywhere."""
    client, _ = flood
    real = _signup(client, 0)
    for n in range(1, waitlist.RATE_LIMIT):
        _signup(client, n)
    over_limit = _signup(client, 9)
    assert (over_limit.status_code, over_limit.text, dict(over_limit.headers)) == (
        real.status_code,
        real.text,
        dict(real.headers),
    )
    monkeypatch.setattr(waitlist, "WAITLIST_CAP", 1)
    over_cap = _signup(client, 8, ip="198.51.100.1")
    assert (over_cap.status_code, over_cap.text, dict(over_cap.headers)) == (
        real.status_code,
        real.text,
        dict(real.headers),
    )
    # Nothing recorded on either path: no row, no alert.
    emails = {r["email"] for r in rows(conn)}
    assert "person9@example.com" not in emails and "person8@example.com" not in emails
    assert conn.execute("select count(*) as n from ops_alerts").fetchone()["n"] == 0


def test_the_guards_still_store_only_what_was_typed(flood, conn, monkeypatch, caplog):
    """Nothing new appears in the table, and no log line names the caller."""
    import logging

    client, _ = flood
    with caplog.at_level(logging.DEBUG):
        for n in range(waitlist.RATE_LIMIT + 3):
            _signup(client, n, ip="192.0.2.44")
        monkeypatch.setattr(waitlist, "WAITLIST_CAP", 1)
        _signup(client, 60, ip="192.0.2.45")
    columns = {
        r["column_name"]
        for r in conn.execute(
            "select column_name from information_schema.columns "
            "where table_schema = 'public' and table_name = 'waitlist'"
        ).fetchall()
    }
    assert columns == {"id", "email", "parent_phone", "created_at", "help_with"}
    assert len(rows(conn)) == waitlist.RATE_LIMIT
    assert "192.0.2.44" not in caplog.text and "192.0.2.45" not in caplog.text


def test_a_spread_of_hits_rolls_off_one_at_a_time(flood, conn):
    """Hits spread across the hour: the first falls out of the window while
    the key itself stays live, and that alone re-admits the caller."""
    client, clock = flood
    for n, minutes in enumerate((0, 20, 40, 50, 55)):
        clock.now = _Clock().now
        clock.advance(minutes=minutes)
        assert _signup(client, n).status_code == 200
    assert len(rows(conn)) == 5
    clock.advance(minutes=4)  # 59 minutes after the first hit: still five inside
    _signup(client, 60)
    assert "person60@example.com" not in {r["email"] for r in rows(conn)}
    clock.advance(minutes=1, seconds=1)  # the first hit has rolled off
    _signup(client, 61)
    assert "person61@example.com" in {r["email"] for r in rows(conn)}
