"""Acceptance criterion 7 — the copy law, extended for the ladder.

Everything the digest law forbids, plus urgency vocabulary. These messages reach
a family on an ordinary afternoon when nothing may be wrong at all; the job is to
prompt a phone call, not to frighten someone into one.
"""

from __future__ import annotations

import re

import pytest

from kettle import ladder_messages
from kettle.ladder_messages import (
    NEUTRAL_CLAUSE,
    render_all_clear,
    render_ask,
    render_contact_line,
    render_family_unanswered,
    render_family_unreachable,
)
from kettle.signals import STANDARD_SIGNALS

# Words that turn a prompt into an emergency. None of these may appear.
URGENCY_WORDS = (
    "emergency", "urgent", "urgently", "immediately", "critical", "alarm",
    "alarming", "alert", "danger", "dangerous", "panic", "hurry", "asap",
    "worried", "worry", "worrying", "afraid", "scared", "serious", "severe",
    "crisis", "distress", "fear",
)

# Medical language and speculation about what might be happening.
MEDICAL_WORDS = (
    "fall", "fallen", "ill", "illness", "sick", "hospital", "ambulance",
    "unwell", "injured", "injury", "collapse", "unconscious", "dementia",
    "health", "medical", "condition", "symptom", "diagnosis",
)

# Counts, comparisons and profile-shaped detail.
# Counts, comparisons and profile-shaped detail.
#
# "usual" is deliberately absent: §4's binding copy says "usual routine", which
# names the thing being watched rather than comparing it to a number. The
# comparative *phrases* are what the law is about, and they are banned below.
PROFILE_WORDS = (
    *[s for s, _ in STANDARD_SIGNALS],
    "whatsapp", "youtube", "news", "charger", "app", "apps", "opened",
    "times", "count", "counts", "pings", "ping", "average",
    "streak", "trend", "score", "percent",
)

BANNED_PHRASES = (
    "than usual", "more than", "less than", "compared to", "than yesterday",
    "activity level", "how many",
)

BANNED = URGENCY_WORDS + MEDICAL_WORDS + PROFILE_WORDS

NAMES = ("Amma", "Appa", "Ammachi", "Patti")


def _assert_ladder_copy_law(message: str, allow_digits: bool = False) -> None:
    scanned = message
    for name in NAMES:
        scanned = scanned.replace(name, "«name»")
    lowered = scanned.lower()

    for banned in BANNED:
        assert not re.search(rf"\b{re.escape(banned)}\b", lowered), (
            f"{banned!r} leaked into: {message}"
        )
    for phrase in BANNED_PHRASES:
        assert phrase not in lowered, f"{phrase!r} leaked into: {message}"
    if not allow_digits:
        assert not any(ch.isdigit() for ch in scanned), message
    assert "%" not in scanned


def test_ask_copy():
    """The one message this product ever sends the senior."""
    message = render_ask("Amma")
    assert message == (
        "This is Kettle. Amma, your phone has been quiet today. All good? Reply YES."
    )
    _assert_ladder_copy_law(message)


def test_family_unanswered_copy_is_neutral_by_default():
    """Nothing infers a pronoun from a name — policy adopted at item 24."""
    message = render_family_unanswered("Amma")
    assert message == (
        "Kettle: Amma's usual routine hasn't been seen today, and they haven't "
        "answered a gentle check-in. A call from you may be all this needs."
    )
    _assert_ladder_copy_law(message)
    assert NEUTRAL_CLAUSE in message


def test_family_unanswered_agrees_with_a_recorded_pronoun():
    """Verb agreement survives substitution: 'she hasn't', not 'she haven't'."""
    assert "she hasn't answered" in render_family_unanswered("Amma", pronoun="she")
    assert "he hasn't answered" in render_family_unanswered("Appa", pronoun="he")
    assert "they haven't answered" in render_family_unanswered("Amma", pronoun="they")
    # Unrecognised or absent falls back to neutral, never to a guess.
    assert "they haven't answered" in render_family_unanswered("Amma", pronoun="")
    assert "they haven't answered" in render_family_unanswered("Amma", pronoun="unknown")
    for pronoun in ("she", "he", "they", None):
        _assert_ladder_copy_law(render_family_unanswered("Amma", pronoun=pronoun))


def test_family_unreachable_copy():
    """Says exactly what is known — a phone problem is the likely explanation."""
    message = render_family_unreachable("Appa")
    assert message == (
        "Kettle: Appa's phone has been unreachable today (no signals of any "
        "kind). This is often a phone or network issue. A call from you is the "
        "fastest way to know."
    )
    _assert_ladder_copy_law(message)


def test_all_clear_copy():
    message = render_all_clear("Amma")
    assert message == "Kettle: Amma's routine has resumed. All normal."
    _assert_ladder_copy_law(message)


def test_contact_line_is_the_one_place_digits_are_allowed():
    """A phone number is the point of the suggestion (QUESTIONS.md item 36)."""
    line = render_contact_line("Priya", "neighbour", "+919845557777")
    assert line == " Your named local contact is Priya (neighbour) on +919845557777."

    message = render_family_unreachable("Amma", contact=line)
    # Strip the contact's number, then the rest must obey the no-digits rule.
    _assert_ladder_copy_law(message.replace("+919845557777", ""))

    assert render_contact_line(None) == ""
    assert render_contact_line("Priya") == " Your named local contact is Priya."


def test_no_ladder_template_speculates():
    """Walk the module: every template must survive the law on its own."""
    templates = [
        value
        for name, value in vars(ladder_messages).items()
        if isinstance(value, str) and name.isupper()
    ]
    assert len(templates) >= 5
    for template in templates:
        skeleton = re.sub(r"\{[a-z_]+\}", "", template)
        _assert_ladder_copy_law(skeleton)


def test_ladder_copy_never_claims_to_be_a_digest():
    """Spec 004 §0: the two never blend."""
    ladder = [
        render_ask("Amma"),
        render_family_unanswered("Amma"),
        render_family_unreachable("Amma"),
    ]
    for message in ladder:
        assert "normal, active day" not in message
        assert "day started normally" not in message

    # And the all-clear, which is the closest of the four, still is not a digest.
    assert "active day" not in render_all_clear("Amma")


def test_digest_copy_still_never_mentions_absence():
    """The separation runs both ways — 003's law is unweakened by 004 existing."""
    from kettle import messages

    digest_templates = [
        value
        for name, value in vars(messages).items()
        if isinstance(value, str) and name.isupper()
    ]
    for template in digest_templates:
        lowered = template.lower()
        for worrying in ("quiet", "unreachable", "hasn't", "haven't", "check-in"):
            assert worrying not in lowered


@pytest.mark.parametrize("word", ("urgent", "emergency", "worried", "alarm"))
def test_the_law_would_catch_a_regression(word: str):
    """A guard on the guard: prove the assertion actually rejects these."""
    with pytest.raises(AssertionError):
        _assert_ladder_copy_law(f"Kettle: this is {word}, please act.")
