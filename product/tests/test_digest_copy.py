"""Acceptance criterion 4 — the copy law.

Two independent derivations made this binding (PLAN.md, Jul 26): "don't give the
child ammunition" and "counts are a behavior profile". So these tests are not
style checks. A rendered digest may contain a parent's name, reassurance, and one
clock time. Not a count, not an app name, not a comparison, not a second number.
"""

from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from kettle.messages import (
    CLOCK_NEUTRAL,
    format_time,
    render_evening,
    render_morning,
)
from kettle.signals import STANDARD_SIGNALS

IST = ZoneInfo("Asia/Kolkata")
MORNING_PING = datetime(2026, 8, 3, 8, 12, tzinfo=IST)

BANNED_WORDS = (
    # Signal and app names.
    *[s for s, _ in STANDARD_SIGNALS],
    "whatsapp", "youtube", "news", "charger", "app", "apps", "opened",
    # Counts, trends, comparisons — the profile-shaped words.
    "times", "count", "counts", "pings", "ping", "average", "usual",
    "more", "less", "streak", "trend", "score", "percent",
)

BANNED_PHRASES = ("activity level", "than yesterday", "compared to")


def _digits_outside_the_time(message: str) -> str:
    """Every digit left once the one permitted clock time is removed."""
    without_time = re.sub(r"\b\d{1,2}:\d{2}\b", "", message)
    return "".join(ch for ch in without_time if ch.isdigit())


def _assert_copy_law(message: str, names: tuple[str, ...] = ()) -> None:
    """Assert what *we* wrote obeys the law.

    Parent names are the family's own words and pass through verbatim, so they
    are removed before scanning — otherwise "Appa" trips the ban on "app", which
    says nothing about the copy. Matching is on word boundaries for the same
    reason.
    """
    scanned = message
    for name in names:
        scanned = scanned.replace(name, "«name»")
    lowered = scanned.lower()

    for banned in BANNED_WORDS:
        assert not re.search(rf"\b{re.escape(banned)}\b", lowered), (
            f"{banned!r} leaked into: {message}"
        )
    for phrase in BANNED_PHRASES:
        assert phrase not in lowered, f"{phrase!r} leaked into: {message}"
    assert "%" not in scanned, message
    assert _digits_outside_the_time(scanned) == "", message


def test_morning_matches_the_binding_template():
    """AC4: exact copy, neutral clock phrasing, one time and nothing else."""
    message = render_morning("Amma", MORNING_PING)
    assert message == "Good morning — Amma's day started normally (08:12 local time)."
    _assert_copy_law(message, ("Amma",))


def test_morning_uses_a_recorded_pronoun_only():
    """Gendered copy is available but never inferred — see QUESTIONS.md item 24."""
    assert "her time" in render_morning("Amma", MORNING_PING, pronoun="she")
    assert "their time" in render_morning("Amma", MORNING_PING, pronoun="they")
    # Anything not explicitly recorded falls back to neutral, including a name
    # that a human might guess from.
    assert CLOCK_NEUTRAL in render_morning("Amma", MORNING_PING)
    assert CLOCK_NEUTRAL in render_morning("Amma", MORNING_PING, pronoun="")
    assert CLOCK_NEUTRAL in render_morning("Amma", MORNING_PING, pronoun="unknown")


def test_evening_one_two_and_many():
    """AC4: aggregation shapes, all free of numbers."""
    one = render_evening(["Amma"])
    two = render_evening(["Amma", "Appa"])
    three = render_evening(["Amma", "Appa", "Patti"])

    assert one == "Amma had a normal, active day."
    assert two == "Amma and Appa both had normal, active days."
    assert three == "Amma, Appa and Patti all had normal, active days."
    for message in (one, two, three):
        _assert_copy_law(message, ("Amma", "Appa", "Patti"))


def test_evening_refuses_to_render_nothing():
    """There is no 'nobody was active' message. That is spec 004's territory."""
    with pytest.raises(ValueError):
        render_evening([])


def test_no_template_describes_absence():
    """The module must not grow an absence-of-activity message by accident."""
    from kettle import messages

    templates = [
        value
        for name, value in vars(messages).items()
        if isinstance(value, str) and name.isupper()
    ]
    assert templates
    for template in templates:
        lowered = template.lower()
        for worrying in ("quiet", "no ", "not ", "missing", "hasn't", "haven't",
                         "silent", "unusual", "concern", "worry", "alert", "check"):
            assert worrying not in lowered, f"{worrying!r} in template: {template}"


def test_time_format_is_minute_resolution():
    assert format_time(MORNING_PING) == "08:12"
    assert format_time(datetime(2026, 8, 3, 8, 12, 45, tzinfo=IST)) == "08:12"


def test_copy_law_holds_for_awkward_names():
    """A name is passed through verbatim; the law is about what we add to it."""
    message = render_morning("Ammachi", MORNING_PING)
    assert message.startswith("Good morning — Ammachi's day started normally")
    _assert_copy_law(message, ("Ammachi",))
