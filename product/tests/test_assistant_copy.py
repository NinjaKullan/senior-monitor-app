"""Spec 019 §8/§9 — every string verbatim, the copy laws over every rendered
answer and every tool description, and the contract that server and webapp
carry the same words."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from testsupport_assistant import assert_assistant_copy_law

from kettle import assistant_copy as copy

COPY_TS = Path(__file__).resolve().parents[2] / "webapp" / "src" / "lib" / "copy.ts"

VERBATIM = {
    "TODAY_NOTHING_YET": "Kettle has not written about {name} yet today.",
    "DAY_NOTHING": "Kettle did not write about {name} that day.",
    "NO_SUCH_PARENT": "Kettle does not know a parent called {asked}. You can ask about {names}.",
    "MORNING_NOTE": "Morning note",
    "EVENING_NOTE": "Evening note",
    "ASK_SENT": "Kettle asked {name}",
    "FOLLOW_ON_SENT": "Kettle wrote to the family",
    "ALL_CLEAR_SENT": "All clear",
    "TOOL_TODAY": (
        "How a parent's day is going, in Kettle's words: the latest note Kettle sent "
        "today and when their phone was last heard from. Give a parent's name, or leave "
        "it out for everyone."
    ),
    "TOOL_PARENT_DAY": (
        "What Kettle wrote about a parent on one day, up to sixty days back. Dates are "
        "in the parent's time zone."
    ),
    "TOOL_MEMORY": (
        "The family's notes and replies, newest first, with anything upcoming at the "
        "top. Dates are in the family's time zone."
    ),
    "TOOL_WHO_TO_CALL": (
        "The parent's number and the people the family listed to call if they cannot reach them."
    ),
    "TOOL_CIRCLES": (
        "The circles this person belongs to: parents, where they live, and who is in the circle."
    ),
}

WEBAPP_VERBATIM = {
    "CONNECT_TITLE": "Connect {client} to Kettle",
    "CONNECT_BODY": "{client} will be able to read what you see in Kettle for {names}.",
    "CONNECT_READ_ONLY": "It cannot change anything. Parents are never involved.",
    "CONNECT_ALLOW": "Allow",
    "CONNECT_CANCEL": "Not now",
    "CONNECT_EXPIRED": "That link has expired. Start again from your assistant.",
    "ASSISTANT_FALLBACK": "An assistant",
    "ASSISTANTS_SECTION": "Assistants",
    "ASSISTANTS_INTRO": (
        "Ask Kettle from Claude or another assistant. Add Kettle as a connector once, "
        "on a computer, with this address. After that you just ask."
    ),
    "ASSISTANTS_COPY": "Copy",
    "ASSISTANTS_COPIED": "Copied",
    "ASSISTANTS_NONE": "Nothing is connected yet.",
    "ASSISTANTS_SINCE": "{client} · since {date}",
    "ASSISTANTS_DISCONNECT": "Disconnect",
    "ASSISTANTS_DISCONNECT_CONFIRM": "Disconnect {client}? It will stop seeing Kettle right away.",
    "ASSISTANTS_DISCONNECT_YES": "Disconnect",
    "ASSISTANTS_DISCONNECT_NO": "Keep it",
}


def webapp_strings() -> dict[str, str]:
    source = COPY_TS.read_text()
    found: dict[str, str] = {}
    for match in re.finditer(
        r'export const ([A-Z_0-9]+) =\s*(?:\(\s*)?"((?:[^"\\]|\\.)*)"', source
    ):
        found[match.group(1)] = match.group(2).replace('\\"', '"')
    # Multi-line concatenations ("a" + "b") are joined for the keys that use them.
    for match in re.finditer(
        r'export const ([A-Z_0-9]+) =\s*\n((?:\s*"(?:[^"\\]|\\.)*"\s*\+?\s*\n?)+);', source
    ):
        parts = re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(2))
        found[match.group(1)] = "".join(parts)
    return found


@pytest.mark.parametrize(("name", "expected"), sorted(VERBATIM.items()))
def test_server_strings_are_verbatim(name, expected):
    assert getattr(copy, name) == expected


def test_webapp_strings_are_verbatim_and_present():
    found = webapp_strings()
    for name, expected in WEBAPP_VERBATIM.items():
        assert found.get(name) == expected, name


def test_server_and_webapp_agree_on_the_shared_strings():
    """The contract: what copy.ts says, assistant_copy.py says."""
    found = webapp_strings()
    for name in copy.SHARED_WITH_WEBAPP:
        assert found.get(name) == getattr(copy, name), name


# --- the copy laws over every string an assistant can read ---------------------------


@pytest.mark.parametrize("name", sorted(copy.ALL_STRINGS))
def test_every_server_string_obeys_the_law(name):
    assert_assistant_copy_law(copy.ALL_STRINGS[name].replace("{n}", "3").replace("{days}", "20"))


def test_heard_thresholds_match_the_webapp():
    assert copy.render_heard(30) == "Heard from moments ago"
    assert copy.render_heard(12 * 60) == "Heard from 12 minutes ago"
    assert copy.render_heard(90 * 60) == "Heard from 1 hour ago"
    assert copy.render_heard(5 * 3600) == "Heard from 5 hours ago"
    assert copy.render_heard(30 * 3600) == "Heard from 1 day ago"
    assert copy.render_heard(3 * 86400) == "Heard from 3 days ago"
    assert copy.render_heard(20 * 86400) == "Last heard from 20 days ago."
