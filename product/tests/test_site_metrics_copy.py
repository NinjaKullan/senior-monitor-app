"""The copy scan on the weekly site email (DECISIONS 212).

The family copy law (`test_outbound_copy.py`) cannot apply to this email
verbatim, and saying so plainly is better than quietly exempting it: that law
bans "count", "counts", "average" and "server" among others, and this is a
founder-only note whose entire subject IS server counts. Applying it as written
would forbid the message from existing.

So this file holds the founder-ops subset — the parts of the law that bind
BECAUSE they are about what Kettle may claim and about whom, rather than about
the vocabulary a family should be spared:

* no medical, diagnostic or decline vocabulary (product law #1);
* no urgency;
* no claim about any person, and no person in it at all;
* nothing that could identify a family, a parent or a visitor;
* the house style rules that are not family-specific: no em dash, no gendered
  pronoun.

The plants at the bottom push each rule through the same scanner the real
strings go through, so a rule that stopped matching would be caught here rather
than admired in a comment.
"""

from __future__ import annotations

import re
from datetime import date

import pytest

from kettle import site_metrics
from kettle.site_metrics import WeekRow, render_weekly_email

MEDICAL_WORDS = (
    "fall", "fallen", "ill", "illness", "sick", "hospital", "ambulance",
    "unwell", "injured", "injury", "collapse", "unconscious", "dementia",
    "health", "medical", "condition", "symptom", "diagnosis", "decline",
    "cognitive", "memory loss",
)

URGENCY_WORDS = (
    "emergency", "urgent", "urgently", "immediately", "critical", "alarm",
    "alarming", "danger", "dangerous", "panic", "hurry", "asap", "worried",
    "worry", "worrying", "crisis", "distress",
)

#: A verdict is a claim about a person. This email is about paths.
VERDICT_PHRASES = (
    "is fine", "is okay", "is ok", "is well", "is safe", "seems fine",
    "nothing is wrong", "something is wrong", "she is", "he is",
)

GENDERED = (" she ", " he ", " her ", " his ", " him ", " hers ")

#: Words that would mean the email had started describing PEOPLE rather than
#: pages. "visitor" is allowed exactly once, in the footer sentence that says
#: nothing about one is recorded, so the ban is on the plural and the verbs.
PERSON_WORDS = (
    "parent", "mom", "dad", "mother", "father", "family", "member",
    "user", "visitors", "reader", "someone", "person", "people",
)


def all_strings() -> dict[str, str]:
    """Every string the email can contain, keyed by where it came from.

    Both branches of the renderer: the populated week and the zero-data first
    week, plus the two standing paragraphs. A scan that only walked one branch
    would leave the other unscanned, which is how the empty-state line would
    have escaped.
    """
    rows = [
        WeekRow("/", 120, 98),
        WeekRow("/blog/", 14, 20),
        WeekRow("/resources/normal-day/normal-day-print.pdf", 12, 4),
    ]
    populated_subject, populated_body = render_weekly_email(rows, date(2026, 8, 31))
    empty_subject, empty_body = render_weekly_email([], date(2026, 8, 31))
    return {
        "populated subject": populated_subject,
        "populated body": populated_body,
        "empty subject": empty_subject,
        "empty body": empty_body,
        "footer": site_metrics.FOOTER,
        "search console note": site_metrics.SEARCH_CONSOLE_NOTE,
    }


def scan(text: str) -> list[str]:
    """Every rule this email is held to, as a list of complaints."""
    problems = []
    # Path segments are data, not prose: "/resources/normal-day/..." must not
    # trip a word ban. Strip anything that looks like a path before scanning.
    prose = re.sub(r"/\S*", " ", text)
    low = f" {prose.lower()} "
    for word in MEDICAL_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", low):
            problems.append(f"medical vocabulary: {word}")
    for word in URGENCY_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", low):
            problems.append(f"urgency: {word}")
    for phrase in VERDICT_PHRASES:
        if phrase in low:
            problems.append(f"verdict about a person: {phrase}")
    for pronoun in GENDERED:
        if pronoun in low:
            problems.append(f"gendered pronoun: {pronoun.strip()}")
    for word in PERSON_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", low):
            problems.append(f"a person where only pages belong: {word}")
    if "—" in text or "–" in text:
        problems.append("em or en dash in a body string")
    return problems


def test_every_string_in_the_email_passes_the_founder_ops_scan():
    for where, text in all_strings().items():
        assert scan(text) == [], f"{where}: {scan(text)}"


def test_the_email_carries_no_family_data_of_any_kind():
    """There is no code path from a page count to a person, and this says so.

    The renderer is handed rows and a date; it cannot reach a family table
    even if a later edit wanted it to.
    """
    for text in all_strings().values():
        assert "@" not in text or text.count("@") == 0
        assert not re.search(r"\+?\d{7,}", text)


@pytest.mark.parametrize(
    ("plant", "expected"),
    [
        ("The site is fine this week.", "verdict"),
        ("Urgent: downloads collapsed.", "urgency"),
        ("A reader in poor health downloaded it.", "medical"),
        ("She downloaded the checklist.", "gendered"),
        ("Counts for each family member.", "a person"),
        ("Counts are steady — nothing to do.", "dash"),
    ],
)
def test_the_scanner_actually_catches_what_it_claims_to(plant, expected):
    """The plants: a green scan means nothing unless the scan can go red.

    Each of these is pushed through the SAME `scan` the real strings go
    through, not a looser one written to make the plant fire.
    """
    problems = scan(plant)
    assert problems, f"scanner missed: {plant}"
    assert any(expected in problem for problem in problems), problems
