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
        headers={"user-agent": "Mozilla/5.0 (test)", "referer": "https://getkettle.com/"},
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
    allowed = client.post(
        "/waitlist", json=SIGNUP, headers={"origin": "https://getkettle.com"}
    )
    assert allowed.headers.get("access-control-allow-origin") == "https://getkettle.com"

    elsewhere = client.post(
        "/waitlist", json={"email": "b@c.co", "parent_phone": "iphone"},
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
        conn.execute(
            "insert into waitlist (email, parent_phone) values ('a@b.co', 'blackberry')"
        )


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
