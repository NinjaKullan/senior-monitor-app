"""Spec 007 §6.2 — the copy law, extended to the template registry.

The registry exists so this scan is possible: every string Kettle can say lives
in one module, and this walks all of it. The law is the ladder's, plus the two
rules this channel adds — no verdict about a person, and no mechanism.

The plants at the bottom are the point. Three of them, one per thing §6.2 names
(a verdict, a count, a signal name), each pushed through the same scanner the
real templates go through rather than a looser one written for the plant.
"""

from __future__ import annotations

import re

import pytest

from kettle import outbound_templates
from kettle.outbound_templates import KINDS, TEMPLATES, render
from kettle.signals import SIGNAL_LABELS, STANDARD_SIGNALS

# Words that turn a note into an emergency.
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

# Counts, comparisons and profile-shaped detail. `usual` is deliberately absent:
# "usual morning" names the thing being watched rather than comparing it to a
# number, and the comparative *phrases* are banned separately below.
PROFILE_WORDS = (
    *[s for s, _ in STANDARD_SIGNALS],
    *[label.lower() for label in SIGNAL_LABELS.values()],
    "app", "apps", "opened", "times", "count", "counts", "pings", "ping",
    "average", "streak", "trend", "score", "percent",
)

# The mechanism ban (DECISIONS 132, the site's what-never-how) reaching product
# copy: a family is told what Kettle noticed, never how the phone was made to
# say it.
MECHANISM_WORDS = (
    "shortcut", "shortcuts", "automation", "automations", "webhook", "api",
    "supabase", "twilio", "resend", "fly.io", "server",
)

BANNED_PHRASES = (
    "than usual", "more than", "less than", "compared to", "than yesterday",
    "activity level", "how many",
)

# A verdict is a claim *about* a person's state. Kettle reports what did or did
# not arrive and stops; the family decides what it means.
VERDICT_PHRASES = (
    "is fine", "is okay", "is ok", "is well", "is safe", "seems fine",
    "seems okay", "looks fine", "all normal", "all clear", "she is",
    "he is", "they are", "nothing is wrong", "something is wrong",
)

BANNED = URGENCY_WORDS + MEDICAL_WORDS + PROFILE_WORDS + MECHANISM_WORDS

NAMES = ("Amma", "Appa", "Ammachi", "Patti", "Kettle")


def assert_outbound_copy_law(message: str) -> None:
    """The whole law, over one rendered message."""
    scanned = message
    for name in NAMES:
        scanned = scanned.replace(name, "«name»")
    lowered = scanned.lower()

    for banned in BANNED:
        assert not re.search(rf"\b{re.escape(banned)}\b", lowered), (
            f"banned word {banned!r} in: {message}"
        )
    for phrase in BANNED_PHRASES + VERDICT_PHRASES:
        assert phrase not in lowered, f"banned phrase {phrase!r} in: {message}"
    assert not re.search(r"\d", lowered), f"a digit in: {message}"
    assert "!" not in message, f"an exclamation mark in: {message}"


def rendered() -> list[tuple[str, str]]:
    """Every template, rendered with a name where one is needed."""
    out = []
    for template_id, template in TEMPLATES.items():
        variables = dict.fromkeys(template.variables, "Amma")
        out.append((template_id, render(template_id, variables)))
    return out


def test_the_registry_is_not_empty_and_covers_every_kind():
    """Not passing on an empty registry, and every kind has something to say."""
    assert len(TEMPLATES) >= 5
    assert {t.kind for t in TEMPLATES.values()} == set(KINDS)


@pytest.mark.parametrize("template_id", sorted(TEMPLATES))
def test_every_template_obeys_the_copy_law(template_id: str):
    template = TEMPLATES[template_id]
    variables = dict.fromkeys(template.variables, "Amma")
    assert_outbound_copy_law(render(template_id, variables))


def test_the_ask_is_the_sites_own_string_and_the_only_thing_a_parent_hears():
    """One string reaches a parent, and it is the one the site already shows.

    It survives the verdict ban because it is a question addressed *to* her
    rather than a claim *about* her — which is the same reason the site pins it.
    """
    parent_facing = [t for t in TEMPLATES.values() if t.audience == "parent"]
    assert [t.id for t in parent_facing] == ["ask_parent"]
    assert parent_facing[0].body == "Everything okay today? Reply whenever suits."


def test_the_follow_on_hands_off_rather_than_instructing():
    """The ladder's last sentence: Kettle stops where the family starts."""
    body = render("follow_on_family", {"parent_name": "Amma"})
    assert body.endswith("a call from you beats anything Kettle can send.")


def test_no_template_stores_or_names_a_signal():
    """Signal names are the phone's vocabulary, never a family's."""
    for _, body in rendered():
        for signal, _grade in STANDARD_SIGNALS:
            assert signal not in body.lower()
        for label in SIGNAL_LABELS.values():
            assert label.lower() not in body.lower()


def test_a_template_cannot_render_with_a_variable_missing():
    """A message with `{parent_name}` still in it is worse than no message."""
    with pytest.raises(ValueError):
        render("digest_morning_normal", {})
    with pytest.raises(ValueError):
        render("digest_morning_normal", {"parent_name": ""})
    with pytest.raises(ValueError):
        render("digest_evening_normal", {"parent_name": "Amma"})


# --- the plants (§6.2) --------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "body"),
    [
        # A verdict about a person, which is the line this product does not
        # cross: reporting an absence is not the same as concluding a state.
        ("a verdict", "Amma is fine today. Next note this evening."),
        ("a softer verdict", "Everything looks fine at Amma's this morning."),
        # A count, which is the profile-shaped detail the three-fields law
        # exists to make unrepresentable.
        ("a count", "Amma opened three apps this morning."),
        ("a comparison", "Amma's morning was quieter than usual."),
        # A signal name, which is the phone's vocabulary leaking into a family's.
        ("a signal name", "Amma's WhatsApp tripwire has not fired today."),
        ("a raw signal key", "No charge_on since yesterday evening."),
        # The mechanism ban, reaching product copy.
        ("a mechanism", "Her Shortcuts automation did not run this morning."),
        # And the shapes the ladder law already banned.
        ("urgency", "Please check on Amma immediately."),
        ("a digit", "Amma has not been seen for 5 hours."),
    ],
)
def test_the_scan_would_catch(label: str, body: str):
    with pytest.raises(AssertionError):
        assert_outbound_copy_law(body)


def test_the_scan_passes_the_real_bodies_unchanged():
    """The other half of the plant: the shipped copy is not merely surviving a
    scanner that fires at everything."""
    for _, body in rendered():
        assert_outbound_copy_law(body)


def test_the_module_holds_every_string_the_channel_can_say():
    """No message text anywhere but the registry.

    A body assembled at a call site is a body this scan never sees, which is
    how a copy law stops meaning anything.
    """
    import inspect

    from kettle import outbound

    source = inspect.getsource(outbound)
    for _, body in rendered():
        assert body[:20] not in source
    # And the registry module itself declares nothing beyond the four kinds.
    assert set(KINDS) == {t.kind for t in outbound_templates.TEMPLATES.values()}
