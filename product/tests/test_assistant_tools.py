"""Spec 019 §7/§9 — the five tools, against seeded days."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from testsupport_assistant import Assistant, jwks_client

from kettle import db
from kettle.main import create_app
from kettle.provisioning import provision_family
from scripts.seed_demo_history import (
    ANSWERED_ASK_DAYS_AGO,
    CHANGED_MORNING_DAYS_AGO,
    NOTE_APPOINTMENT,
    UNREACHABLE_DAYS_AGO,
    seed,
)
from testsupport import BASE_URL, add_member, set_parent_whatsapp

USER = "11111111-1111-1111-1111-111111111111"
SISTER = "22222222-2222-2222-2222-222222222222"
NOW = datetime(2026, 9, 5, 16, 0, tzinfo=UTC)  # 09:00 Phoenix, 21:30 Chennai


class Clock:
    now = NOW

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
def whitakers(conn, clock):
    """The demo family (243), its story days seeded into a real ledger."""
    family = provision_family(
        conn,
        name="Whitaker",
        tz="America/New_York",
        parents=[("Linda", "America/Phoenix", "Mom"), ("Bill", "America/Phoenix", "Dad")],
        base_url=BASE_URL,
        owner_name="Sarah",
        signals=["routine", "charger", "device_alive"],
    )
    conn.execute("update families set demo = true where id = %s", (family.family_id,))
    seed(conn, family.family_id, days=30, seed_value=42, through_now=True, now=clock.now)
    add_member(conn, family.family_id, USER, role="admin")
    return family


@pytest.fixture
def connected(api, whitakers):
    assistant = Assistant(api)
    assistant.connect(USER)
    return assistant


def _day(days_ago: int) -> str:
    return (
        NOW.astimezone(__import__("zoneinfo").ZoneInfo("America/Phoenix")).date()
        - timedelta(days=days_ago)
    ).isoformat()


# --- today -----------------------------------------------------------------------


def test_today_answers_for_everyone_in_kettles_words(connected, conn, whitakers):
    # The seed writes no ledger row for TODAY (272): the honest answer is that
    # Kettle has not written yet, plus the heard line from the seeded pings.
    answer = connected.text("today")
    paragraphs = answer.split("\n\n")
    assert {p.split(":")[0] for p in paragraphs} == {"Linda", "Bill"}
    assert all("Kettle has not written about" in p and "Heard from" in p for p in paragraphs)
    # Phoenix is not New York: the city line says where they are.
    assert all("there now" in p for p in paragraphs)
    # A note in today's ledger becomes the answer, rendered through the registry.
    linda = whitakers.parents[0].parent_id
    conn.execute(
        "insert into sent_messages (family_id, parent_id, local_date, kind, template_id, "
        "transport, sent_utc, status) values (%s, %s, %s, 'digest_morning', "
        "'digest_morning_normal', 'log', %s, 'sent')",
        (whitakers.family_id, linda, _day(0), NOW - timedelta(minutes=30)),
    )
    assert "Linda: Mom's morning looked like a normal morning. Next note this evening." in (
        connected.text("today", parent="Linda")
    )


def test_today_for_one_parent_by_name_case_insensitively(connected):
    assert connected.text("today", parent="linda").startswith("Linda: ")
    assert "Bill" not in connected.text("today", parent="LINDA")


def test_an_unknown_name_is_a_sentence_listing_who_can_be_asked_about(connected):
    assert connected.text("today", parent="Grandpa") == (
        "Kettle does not know a parent called Grandpa. You can ask about Bill and Linda."
    )


def test_nothing_yet_today_and_the_heard_line_stand_on_their_own(api, conn, clock):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    add_member(conn, family.family_id, USER, role="admin")
    assistant = Assistant(api)
    assistant.connect(USER)
    assert (
        assistant.text("today")
        == "Amma: Kettle has not written about Amma yet today. Nothing has reached Kettle yet."
    )
    db.insert_ping(
        conn, family.parents[0].parent_id, "whatsapp", clock.now - timedelta(minutes=12), None
    )
    assert assistant.text("today").endswith("Heard from 12 minutes ago")


def test_a_paused_parent_gets_the_pause_lines(api, conn, whitakers, clock):
    linda = whitakers.parents[0].parent_id
    conn.execute(
        "update parents set paused_until = %s, paused_since = %s where id = %s",
        (clock.now + timedelta(days=6), clock.now - timedelta(days=1), linda),
    )
    assistant = Assistant(api)
    assistant.connect(USER)
    answer = assistant.text("today", parent="Linda")
    assert "Kettle is paused for Linda. Back on Sep 11." in answer
    assert "normal morning" not in answer
    conn.execute("update parents set paused_until = 'infinity' where id = %s", (linda,))
    assert "Until someone turns it back on." in assistant.text("today", parent="Linda")


# --- parent_day --------------------------------------------------------------------


def test_parent_day_tells_a_story_day_in_ledger_order(connected):
    changed = connected.text("parent_day", parent="Linda", date=_day(CHANGED_MORNING_DAYS_AGO))
    assert changed.startswith("Linda: Morning note: ")
    assert "Kettle asked Linda: " in changed
    assert "Kettle wrote to the family: " in changed
    assert changed.index("Kettle asked Linda") < changed.index("Kettle wrote to the family")
    answered = connected.text("parent_day", parent="Bill", date=_day(ANSWERED_ASK_DAYS_AGO))
    assert "Kettle asked Bill" in answered and "wrote to the family" not in answered
    unreachable = connected.text("parent_day", parent="Bill", date=_day(UNREACHABLE_DAYS_AGO))
    assert "Kettle wrote to the family: " in unreachable and "All clear: " in unreachable


def test_parent_day_defaults_to_today_and_has_a_sixty_day_floor(connected):
    assert connected.text("parent_day", parent="Linda") == (
        "Linda: Kettle did not write about Linda that day."
    )
    assert connected.text("parent_day", parent="Linda", date=_day(61)) == (
        "Linda: Kettle did not write about Linda that day."
    )
    assert "did not write about Linda that day" in connected.text(
        "parent_day", parent="Linda", date="2030-01-01"
    )


# --- memory -----------------------------------------------------------------------


def test_memory_lists_notes_newest_first_with_upcoming_on_top_and_replies_indented(
    connected, conn, whitakers
):
    note = conn.execute(
        "insert into journal_entries (family_id, author_label, body, event_date) "
        "values (%s, 'Sarah', 'Eye doctor', %s) returning id",
        (whitakers.family_id, (NOW + timedelta(days=3)).date()),
    ).fetchone()["id"]
    conn.execute(
        "insert into journal_entries (family_id, author_label, body, parent_entry_id) "
        "values (%s, 'Tom', 'I can drive', %s)",
        (whitakers.family_id, note),
    )
    conn.execute(
        "update journal_entries set edited_utc = now() where family_id = %s and body = %s",
        (whitakers.family_id, NOTE_APPOINTMENT),
    )
    conn.execute(
        "insert into journal_entries (family_id, parent_id, author_label, body, kind, created_utc) "
        "values (%s, %s, 'Kettle', 'Linda is in Phoenix now.', 'city_change', %s)",
        (whitakers.family_id, whitakers.parents[0].parent_id, NOW - timedelta(days=40)),
    )
    answer = connected.text("memory")
    lines = answer.splitlines()
    assert lines[0] == "Upcoming"
    assert lines[1].endswith(" · Sarah: Eye doctor")
    assert lines[2].startswith("  ") and lines[2].endswith(" · Tom: I can drive")
    assert " · edited · Sarah: " in answer, answer
    assert " · Kettle: " in answer, answer  # Kettle's own lines carry its name


def test_memory_filters_by_parent_and_since_and_caps_at_forty(connected, conn, whitakers):
    bill = whitakers.parents[1].parent_id
    for i in range(50):
        conn.execute(
            "insert into journal_entries (family_id, parent_id, author_label, body, created_utc) "
            "values (%s, %s, 'Sarah', %s, %s)",
            (
                whitakers.family_id,
                bill,
                f"note number {i}",
                NOW - timedelta(days=100) + timedelta(hours=i),
            ),
        )
    bill_notes = connected.text("memory", parent="Bill")
    # Forty notes: Bill's seeded story note plus the newest thirty-nine.
    assert len(bill_notes.splitlines()) == 40
    assert "note number 49" in bill_notes and "note number 10" not in bill_notes
    recent = connected.text("memory", since=(NOW - timedelta(days=30)).date().isoformat())
    assert "note number" not in recent


# --- who_to_call -------------------------------------------------------------------


def test_who_to_call_is_the_only_tool_that_returns_a_number(connected, conn, whitakers):
    linda = whitakers.parents[0].parent_id
    set_parent_whatsapp(conn, linda, "+16025550101")
    conn.execute(
        "insert into family_contacts "
        "(family_id, parent_id, label, name, phone_e164, phone_display, note, position) "
        "values (%s, null, 'A neighbor', 'Carol', '+16025550102', '(602) 555-0102', "
        "'Next door', 0)",
        (whitakers.family_id,),
    )
    answer = connected.text("who_to_call", parent="Linda")
    assert "Call Linda ↗ +16025550101" in answer
    assert "Carol · (602) 555-0102 · Next door" in answer
    assert "+16025550101" not in connected.text("today", parent="Linda")
    assert "555" not in connected.text("circles")


# --- circles and membership at call time --------------------------------------------


def test_circles_names_parents_places_and_members_and_no_emails(connected, conn, whitakers):
    answer = connected.text("circles")
    assert answer.splitlines()[0] == "Whitaker"
    assert "  Linda · " in answer and "there now" in answer
    assert "(admin)" in answer
    assert "@" not in answer


def test_membership_is_read_at_call_time(api, conn, whitakers):
    other = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    add_member(conn, other.family_id, USER, role="member")
    assistant = Assistant(api)
    assistant.connect(USER)
    assert "Sharma" in assistant.text("circles") and "Whitaker" in assistant.text("circles")
    conn.execute(
        "delete from members where family_id = %s and auth_user_id = %s", (other.family_id, USER)
    )
    circles = assistant.text("circles")
    assert "Sharma" not in circles and "Whitaker" in circles
    assert "Amma" not in assistant.text("today")


def test_a_name_in_two_circles_answers_for_both_with_the_circle_named(api, conn, whitakers):
    other = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Linda", None, "Mom")], base_url=BASE_URL
    )
    add_member(conn, other.family_id, USER, role="member")
    assistant = Assistant(api)
    assistant.connect(USER)
    answer = assistant.text("today", parent="Linda")
    assert "Whitaker · Linda: " in answer and "Sharma · Linda: " in answer


def test_a_person_outside_every_circle_is_told_so(api, conn):
    assistant = Assistant(api)
    assistant.connect(SISTER)
    assert assistant.text("circles") == "This person is not in any circle yet."
    assert assistant.text("today") == "Kettle does not know a parent called . You can ask about ."


def test_every_rendered_answer_obeys_the_copy_law(connected, conn, whitakers):
    from testsupport_assistant import assert_assistant_copy_law

    linda = whitakers.parents[0].parent_id
    for tool, args in (
        ("today", {}),
        ("today", {"parent": "Grandpa"}),
        ("parent_day", {"parent": "Linda", "date": _day(CHANGED_MORNING_DAYS_AGO)}),
        ("parent_day", {"parent": "Bill", "date": _day(UNREACHABLE_DAYS_AGO)}),
        ("parent_day", {"parent": "Linda", "date": _day(61)}),
        ("circles", {}),
    ):
        assert_assistant_copy_law(connected.text(tool, **args))
    # Note bodies are the family's own words and exempt (the journal rule);
    # the chrome around them — dates, authors, the Upcoming label — is not.
    for line in connected.text("memory").splitlines():
        assert_assistant_copy_law(line.split(": ", 1)[0])
    conn.execute(
        "update parents set paused_until = 'infinity', paused_since = now() where id = %s", (linda,)
    )
    assert_assistant_copy_law(connected.text("today", parent="Linda"))
    assert_assistant_copy_law(connected.text("who_to_call", parent="Linda"), digits_ok=True)


def test_every_tool_says_it_only_reads(connected, api):
    """DECISIONS 286: readOnlyHint on all five, openWorldHint off, so the
    assistant does not ask permission on every question."""
    from testsupport_assistant import mcp_call

    tools = mcp_call(api, connected.access_token, "tools/list").json()["result"]["tools"]
    assert len(tools) == 5
    for tool in tools:
        assert tool["annotations"]["readOnlyHint"] is True, tool["name"]
        assert tool["annotations"]["openWorldHint"] is False, tool["name"]


def test_tool_descriptions_are_the_ruled_words(connected, api):
    from testsupport_assistant import mcp_call

    tools = {
        t["name"]: t["description"]
        for t in mcp_call(api, connected.access_token, "tools/list").json()["result"]["tools"]
    }
    assert tools["today"].startswith("How a parent's day is going, in Kettle's words")
    assert tools["memory"].endswith("Dates are in the family's time zone.")
