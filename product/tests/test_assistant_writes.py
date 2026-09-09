"""Spec 019 Amendment A — notes and replies through the assistant (§A.7).

Scope: a write grant works, a read grant answers NEED_WRITE, write reads
too. add_note by circle and by parent, with a date, capped, marked. reply
under the latest note, by author, by date, refused where 016 refuses. The
hourly limit on the injected clock. Membership at call time. Annotations
and the server's instructions. Everything else the door could do stays
exactly as it was.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from fastapi.testclient import TestClient
from testsupport_assistant import Assistant, jwks_client, mcp_call

from kettle import assistant_copy as copy
from kettle.main import create_app
from kettle.provisioning import provision_family
from testsupport import BASE_URL, add_member

USER = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"
APP = "https://kettle-app.test"


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 9, 15, 0, tzinfo=UTC)  # 8:30 pm IST

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def api(settings, notifier, conn, clock):
    with TestClient(create_app(settings, notifier, clock, jwks_client=jwks_client())) as c:
        yield c


@pytest.fixture
def sharma(conn):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    conn.execute(
        "update members set display_name = 'Hema' where family_id = %s and auth_user_id = %s",
        (family.family_id, USER),
    )
    add_member(conn, family.family_id, USER, role="admin")
    conn.execute(
        "update members set display_name = 'Hema' where family_id = %s and auth_user_id = %s",
        (family.family_id, USER),
    )
    return family


def writer(api, scope: str = "kettle:write") -> Assistant:
    assistant = Assistant(api)
    assistant.connect(USER, scope=scope)
    return assistant


def rows(conn, family_id) -> list[dict]:
    return [
        dict(r)
        for r in conn.execute(
            "select j.body, j.parent_id, j.event_date, j.author_label, j.author_member_id, "
            "j.via_client, j.parent_entry_id, j.kind from journal_entries j "
            "where j.family_id = %s order by j.id",
            (family_id,),
        ).fetchall()
    ]


def note(conn, family_id, body: str, when: datetime, author: str = "Family", member=None):
    return conn.execute(
        "insert into journal_entries (family_id, author_label, author_member_id, body, "
        "created_utc) values (%s, %s, %s, %s, %s) returning id",
        (family_id, author, member, body, when),
    ).fetchone()["id"]


# --- scope (A.2, A.5) ----------------------------------------------------------


def test_a_write_grant_stores_its_scope_and_the_consent_screen_learns_it(api, conn, sharma):
    from urllib.parse import parse_qs, urlsplit

    from testsupport_assistant import pkce_pair

    assistant = Assistant(api)
    assistant.register("Claude")
    _, challenge = pkce_pair()
    sent = assistant.authorize(challenge, scope="kettle:write")
    request_id = parse_qs(urlsplit(sent.headers["location"]).query)["request"][0]
    assert api.get("/oauth/pending", params={"request": request_id}).json() == {
        "client_name": "Claude",
        "scope": "kettle:write",
    }
    assistant.connect(USER, scope="kettle:read kettle:write")
    grant = conn.execute("select scope from assistant_grants").fetchone()
    assert grant["scope"] == "kettle:write"
    # The write scope reads too; a note lands.
    assert "Amma" in assistant.text("today")
    assert assistant.text("add_note", text="Amma's doctor visit is Thursday") == copy.NOTE_SAVED


def test_a_read_grant_gets_need_write_from_both_tools_and_reads_as_before(api, conn, sharma):
    reader = writer(api, scope="kettle:read")
    assert reader.text("add_note", text="anything") == copy.NEED_WRITE
    assert reader.text("reply", text="anything") == copy.NEED_WRITE
    assert rows(conn, sharma.family_id) == []
    assert "Amma" in reader.text("today")
    assert reader.text("memory") == "Nothing in the family's notes yet."
    # And the token endpoint says what was granted.
    assert conn.execute("select scope from assistant_grants").fetchone()["scope"] == "kettle:read"


def test_an_unknown_scope_is_refused_as_before(api, sharma):
    from testsupport_assistant import pkce_pair

    assistant = Assistant(api)
    assistant.register("Claude")
    _, challenge = pkce_pair()
    refused = assistant.authorize(challenge, scope="kettle:admin")
    assert refused.status_code == 302
    assert "invalid_scope" in refused.headers["location"]


def test_discovery_offers_both_scopes_and_the_instructions_are_verbatim(api, sharma):
    server = api.get("/.well-known/oauth-authorization-server").json()
    assert server["scopes_supported"] == ["kettle:read", "kettle:write"]
    assistant = writer(api)
    init = mcp_call(
        api,
        assistant.access_token,
        "initialize",
        {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "t", "version": "0"},
        },
    ).json()
    assert init["result"]["instructions"] == copy.SERVER_INSTRUCTIONS


# --- add_note (A.3.1) ------------------------------------------------------------


def test_one_circle_no_parent_writes_the_marked_note(api, conn, sharma, clock):
    assistant = writer(api)
    assert assistant.text("add_note", text="  Plumber comes Monday  ") == copy.NOTE_SAVED
    [row] = rows(conn, sharma.family_id)
    member = conn.execute(
        "select id from members where family_id = %s and auth_user_id = %s",
        (sharma.family_id, USER),
    ).fetchone()["id"]
    assert row["body"] == "Plumber comes Monday"
    assert row["parent_id"] is None and row["event_date"] is None
    assert row["author_label"] == "Hema"
    assert row["author_member_id"] == member
    assert row["via_client"] == "Claude"
    assert row["kind"] == "note"
    # The memory tool renders the mark.
    assert "· Hema via Claude: Plumber comes Monday" in assistant.text("memory")


def test_several_circles_no_parent_asks_which_and_writes_nothing(api, conn, sharma):
    iyer = provision_family(
        conn, "Iyer", "Asia/Kolkata", [("Patti", None, "Grandma")], base_url=BASE_URL
    )
    add_member(conn, iyer.family_id, USER, role="member")
    assistant = writer(api)
    assert assistant.text("add_note", text="x") == copy.WHICH_PARENT.replace(
        "{names}", "Amma and Patti"
    )
    assert rows(conn, sharma.family_id) == [] and rows(conn, iyer.family_id) == []
    # A parent picks the circle and tags the note; a date becomes event_date.
    assert assistant.text("add_note", text="Eye doctor", parent="patti", date="2026-09-18") == (
        copy.NOTE_SAVED
    )
    [row] = rows(conn, iyer.family_id)
    assert row["parent_id"] == iyer.parents[0].parent_id
    assert str(row["event_date"]) == "2026-09-18"
    assert rows(conn, sharma.family_id) == []
    assert assistant.text("add_note", text="x", parent="Grandpa").startswith(
        "Kettle does not know a parent called Grandpa"
    )


def test_a_body_over_the_cap_or_a_bad_date_cannot_be_saved(api, conn, sharma):
    assistant = writer(api)
    assert assistant.text("add_note", text="x" * 2001) == copy.CANNOT_SAVE.replace("{app}", APP)
    assert assistant.text("add_note", text="x" * 2000) == copy.NOTE_SAVED
    assert assistant.text("add_note", text="x", date="Thursday") == copy.CANNOT_SAVE.replace(
        "{app}", APP
    )
    assert assistant.text("add_note", text="   ") == copy.CANNOT_SAVE.replace("{app}", APP)
    assert len(rows(conn, sharma.family_id)) == 1


# --- reply (A.3.2) ----------------------------------------------------------------


def test_reply_goes_under_the_latest_note_by_default(api, conn, sharma, clock):
    older = note(conn, sharma.family_id, "Old", clock.now - timedelta(days=2), "Priya")
    newest = note(conn, sharma.family_id, "New", clock.now - timedelta(hours=1), "Priya")
    assistant = writer(api)
    assert assistant.text("reply", text="I'll call her tonight") == copy.REPLY_SAVED.replace(
        "{author}", "Priya"
    ).replace("{date}", "Sep 9")
    [reply] = [r for r in rows(conn, sharma.family_id) if r["parent_entry_id"]]
    assert reply["parent_entry_id"] == newest and reply["via_client"] == "Claude"
    assert reply["author_label"] == "Hema"
    assert older != newest
    lines = assistant.text("memory").splitlines()
    assert lines[1].strip().startswith("Sep 9 · Hema via Claude: I'll call her tonight")


def test_author_narrows_by_member_name_then_label_and_date_narrows(api, conn, sharma, clock):
    priya = conn.execute(
        "insert into members (family_id, auth_user_id, display_name, role, email) values "
        "(%s, %s, 'Priya', 'member', 'p@example.test') returning id",
        (sharma.family_id, OTHER),
    ).fetchone()["id"]
    legacy = note(conn, sharma.family_id, "Legacy", clock.now - timedelta(days=3), "Family")
    by_priya = note(conn, sharma.family_id, "Mine", clock.now - timedelta(days=1), "P", priya)
    latest = note(conn, sharma.family_id, "Latest", clock.now - timedelta(hours=2), "Hema")
    assistant = writer(api)
    assert "Priya's note from Sep 8" in assistant.text("reply", text="a", author="priya")
    assert "Family's note from Sep 6" in assistant.text("reply", text="b", author="Family")
    assert "Hema's note from Sep 9" in assistant.text("reply", text="c", date="2026-09-09")
    assert assistant.text("reply", text="d", author="Nobody") == copy.NO_NOTE_TO_ANSWER
    assert assistant.text("reply", text="e", date="2026-01-01") == copy.NO_NOTE_TO_ANSWER
    assert assistant.text("reply", text="f", date="yesterday") == copy.NO_NOTE_TO_ANSWER
    targets = [r["parent_entry_id"] for r in rows(conn, sharma.family_id) if r["parent_entry_id"]]
    assert targets == [by_priya, legacy, latest]


def test_a_reply_never_lands_on_a_reply_or_on_kettles_line(api, conn, sharma, clock):
    parent = note(conn, sharma.family_id, "Root", clock.now - timedelta(days=1), "Priya")
    conn.execute(
        "insert into journal_entries (family_id, author_label, body, parent_entry_id, "
        "created_utc) values (%s, 'Priya', 'a reply', %s, %s)",
        (sharma.family_id, parent, clock.now - timedelta(hours=3)),
    )
    conn.execute(
        "insert into journal_entries (family_id, parent_id, author_label, body, kind, "
        "created_utc) values (%s, %s, 'Kettle', 'Kettle started', 'started', %s)",
        (sharma.family_id, sharma.parents[0].parent_id, clock.now - timedelta(hours=1)),
    )
    assistant = writer(api)
    # The newest rows are a reply and Kettle's own line; neither is a target.
    assert "Priya's note from Sep 8" in assistant.text("reply", text="x")
    [written] = [r for r in rows(conn, sharma.family_id) if r["via_client"]]
    assert written["parent_entry_id"] == parent
    # And the 016 trigger still guards a reply to a reply from the service role.
    with pytest.raises(psycopg.errors.CheckViolation, match="reply_to_reply"):
        conn.execute(
            "insert into journal_entries (family_id, author_label, body, parent_entry_id) "
            "values (%s, 'x', 'y', (select id from journal_entries where body = 'a reply'))",
            (sharma.family_id,),
        )
    conn.rollback()


def test_no_note_at_all_is_no_note_to_answer(api, conn, sharma):
    assistant = writer(api)
    assert assistant.text("reply", text="x") == copy.NO_NOTE_TO_ANSWER
    assert rows(conn, sharma.family_id) == []


# --- the limit (A.4) ---------------------------------------------------------------


def test_the_twenty_first_write_in_an_hour_is_refused_on_the_injected_clock(
    api, conn, sharma, clock
):
    assistant = writer(api)
    for n in range(20):
        clock.now += timedelta(minutes=1)
        assert assistant.text("add_note", text=f"note {n}") == copy.NOTE_SAVED
    assert assistant.text("add_note", text="one more") == copy.WRITE_LIMIT.replace("{app}", APP)
    assert assistant.text("reply", text="one more") == copy.WRITE_LIMIT.replace("{app}", APP)
    assert len(rows(conn, sharma.family_id)) == 20
    # Typed notes do not count; an hour after the first, the window opens.
    conn.execute(
        "insert into journal_entries (family_id, author_label, body) values (%s, 'Hema', 'typed')",
        (sharma.family_id,),
    )
    assert assistant.text("add_note", text="still too many") == copy.WRITE_LIMIT.replace(
        "{app}", APP
    )
    clock.now += timedelta(minutes=41)
    # The access token issued an hour ago has expired with the window; the
    # refresh token carries the same grant (and its scope) forward.
    refreshed = assistant.token(grant_type="refresh_token", refresh_token=assistant.refresh_token)
    assert refreshed.json()["scope"] == "kettle:write"
    assistant.access_token = refreshed.json()["access_token"]
    assert assistant.text("add_note", text="now fine") == copy.NOTE_SAVED
    assert conn.execute("select count(*) as n from ops_alerts").fetchone()["n"] == 0


# --- membership at call time (A.5) --------------------------------------------------


def test_removed_from_the_circle_a_write_never_lands(api, conn, sharma):
    assistant = writer(api)
    assert assistant.text("add_note", text="before") == copy.NOTE_SAVED
    conn.execute(
        "delete from members where family_id = %s and auth_user_id = %s", (sharma.family_id, USER)
    )
    answer = assistant.text("add_note", text="after")
    assert answer.startswith("Say which parent this is about.")
    assert assistant.text("add_note", text="after", parent="Amma").startswith(
        "Kettle does not know a parent called Amma"
    )
    assert assistant.text("reply", text="after") == copy.NO_NOTE_TO_ANSWER
    assert [r["body"] for r in rows(conn, sharma.family_id)] == ["before"]


def test_a_member_may_write_but_the_seat_is_read_at_call_time(api, conn, sharma):
    iyer = provision_family(
        conn, "Iyer", "Asia/Kolkata", [("Patti", None, "Grandma")], base_url=BASE_URL
    )
    add_member(conn, iyer.family_id, USER, role="member")
    assistant = writer(api)
    assert assistant.text("add_note", text="ok", parent="Patti") == copy.NOTE_SAVED
    conn.execute(
        "delete from members where family_id = %s and auth_user_id = %s", (iyer.family_id, USER)
    )
    assert assistant.text("add_note", text="gone", parent="Patti").startswith(
        "Kettle does not know a parent called Patti"
    )
    assert [r["body"] for r in rows(conn, iyer.family_id)] == ["ok"]


# --- copy (A.6) -------------------------------------------------------------------


def test_the_chrome_obeys_the_copy_laws_and_the_body_is_not_scanned(api, conn, sharma):
    from testsupport_assistant import assert_assistant_copy_law

    for text in (
        copy.NOTE_SAVED,
        copy.REPLY_SAVED.replace("{author}", "Priya").replace("{date}", "Sep 9"),
        copy.NEED_WRITE,
        copy.WHICH_PARENT.replace("{names}", "Amma and Appa"),
        copy.NO_NOTE_TO_ANSWER,
        copy.CANNOT_SAVE.replace("{app}", APP),
        copy.WRITE_LIMIT.replace("{app}", APP),
        copy.SERVER_INSTRUCTIONS,
        copy.TOOL_ADD_NOTE,
        copy.TOOL_REPLY,
        copy.AUTHOR_VIA.replace("{name}", "Hema").replace("{client}", "Claude"),
    ):
        assert_assistant_copy_law(text)
    # The person's own words land as typed, banned words and digits included.
    assistant = writer(api)
    assert assistant.text("add_note", text="Amma fell twice, hospital at 4pm") == copy.NOTE_SAVED
    assert rows(conn, sharma.family_id)[0]["body"] == "Amma fell twice, hospital at 4pm"
