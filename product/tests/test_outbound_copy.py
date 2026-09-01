"""Spec 007 §6.2 — the copy law, extended to the template registry.

The registry exists so this scan is possible: every string Kettle can say lives
in one module, and this walks all of it. The law is the ladder's, plus the two
rules this channel adds — no verdict about a person, and no mechanism — plus
the three DECISIONS 149–151 added: no gendered pronoun (singular they or none),
no em dash in a body, and `{relationship}` rather than any name.

The plants at the bottom are the point: one per thing the law names, each
pushed through the same scanner the real templates go through rather than a
looser one written for the plant.
"""

from __future__ import annotations

import re

import pytest

from kettle import outbound_templates
from kettle.outbound_templates import (
    KINDS,
    OWNER_FALLBACK,
    TEMPLATES,
    owner_first_name,
    render,
)
from kettle.provisioning import RELATIONSHIP_LABELS
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

# Retired vocabulary (DECISIONS 192). Spec 009 replaced "ordinary" with
# "normal" in every webapp string and the email bodies were deferred, which left
# the product saying both words for the same day — "a normal morning" at 9:30
# and "An ordinary day, start to finish" at night, in the same family's inbox on
# the same Thursday. The bodies are swept and the word joins the scan, so the
# deferral cannot quietly resume: this is the one ban here that exists for
# consistency with another surface rather than for the copy law's own reasons,
# and it is enforced exactly as hard.
RETIRED_WORDS = ("ordinary",)

BANNED = (
    URGENCY_WORDS + MEDICAL_WORDS + PROFILE_WORDS + MECHANISM_WORDS + RETIRED_WORDS
)

# DECISIONS 149, closing 24: pronouns are never guessed. Singular they, or the
# sentence is restructured to need none — so no gendered pronoun survives the
# scan, whichever parent it would have guessed about.
GENDERED_PRONOUNS = ("she", "her", "hers", "herself", "he", "him", "his", "himself")

NAMES = ("Amma", "Appa", "Ammachi", "Patti", "Kettle")


def assert_outbound_copy_law(message: str) -> None:
    """The whole law, over one rendered message."""
    scanned = message
    for name in NAMES:
        scanned = scanned.replace(name, "«name»")
    lowered = scanned.lower()

    for banned in BANNED + GENDERED_PRONOUNS:
        assert not re.search(rf"\b{re.escape(banned)}\b", lowered), (
            f"banned word {banned!r} in: {message}"
        )
    for phrase in BANNED_PHRASES + VERDICT_PHRASES:
        assert phrase not in lowered, f"banned phrase {phrase!r} in: {message}"
    assert not re.search(r"\d", lowered), f"a digit in: {message}"
    assert "!" not in message, f"an exclamation mark in: {message}"
    # DECISIONS 151, extending 127 to product copy: no em dashes in any body.
    assert "—" not in message, f"an em dash in: {message}"


def rendered(label: str = "Mom") -> list[tuple[str, str]]:
    """Every template, rendered with a relationship label where one is needed."""
    out = []
    for template_id, template in TEMPLATES.items():
        variables = dict.fromkeys(template.variables, label)
        out.append((template_id, render(template_id, variables)))
    return out


def test_the_registry_is_not_empty_and_covers_every_kind():
    """Not passing on an empty registry, and every kind has something to say."""
    assert len(TEMPLATES) >= 5
    assert {t.kind for t in TEMPLATES.values()} == set(KINDS)


@pytest.mark.parametrize("label", RELATIONSHIP_LABELS)
@pytest.mark.parametrize("template_id", sorted(TEMPLATES))
def test_every_template_obeys_the_copy_law_under_every_label(
    template_id: str, label: str
):
    """The whole standard set, not one lucky label: any label a child can pick
    must render every template clean."""
    template = TEMPLATES[template_id]
    variables = dict.fromkeys(template.variables, label)
    assert_outbound_copy_law(render(template_id, variables))


def test_the_ask_carries_the_icon_and_is_the_only_thing_a_parent_hears():
    """One string reaches a parent, and it is the ruled one, verbatim.

    It survives the verdict ban because it is a question addressed *to* the
    parent rather than a claim *about* them. The 👍 is DECISIONS 150's
    universal icon — the site's older quote of this string is illustrative,
    not binding, so this asserts against the ruling and never the site.

    Reworded again in DECISIONS 217 for a UTILITY approval: v4 was approved
    but recategorized Marketing, and Meta refuses marketing templates to US
    numbers, so the ask reached nobody in the US (216, error 63049). v5 names
    who asked and what for, which is what Utility means. The assertion stays
    codepoint-exact: on the real number these words come from Meta's approved
    template, on the sandbox from this registry, and a drift between them
    would be two different asks wearing one product's voice.
    """
    parent_facing = [t for t in TEMPLATES.values() if t.audience == "parent"]
    assert [t.id for t in parent_facing] == ["ask_parent"]
    body = parent_facing[0].body
    assert body == (
        "{owner_name} asked Kettle to check in with you when a morning looks "
        "different. Is everything okay? Reply with a 👍 when you're free."
    )
    # Bare U+1F44D (no variation selector) and a straight apostrophe — the
    # details a retyping loses (DECISIONS 206, carried into 217).
    assert "\U0001f44d" in body and "\ufe0f" not in body
    assert "'" in body and "\u2019" not in body
    # Codepoint-exact in BOTH renderings, because both are things a parent can
    # actually receive: a family with a name on file, and one without.
    assert len(render("ask_parent", {"owner_name": "Priya"})) == 124
    assert len(render("ask_parent", {"owner_name": OWNER_FALLBACK})) == 130

    # DECISIONS 217: the fallback was chosen so the sentence reads whole
    # rather than leaving a hole where a person should be.
    assert render("ask_parent", {"owner_name": OWNER_FALLBACK}).startswith(
        "Your family asked Kettle to check in with you"
    )


def test_the_email_subjects_are_registry_copy_and_obey_the_law():
    """The subject lines are family-facing copy: they live in the registry
    module and go through the same scan as every body. Per-parent since the
    email-polish pass; the plain subject stands for anything not about a
    single parent (or a parent whose label is not set yet)."""
    assert_outbound_copy_law(outbound_templates.EMAIL_SUBJECT)
    assert outbound_templates.EMAIL_SUBJECT == "A note from Kettle"
    assert outbound_templates.EMAIL_SUBJECT_PARENT == "A note about {relationship}'s day"
    for label in RELATIONSHIP_LABELS:
        subject = outbound_templates.subject_for(label)
        assert subject == f"A note about {label}'s day"
        assert_outbound_copy_law(subject)
    assert outbound_templates.subject_for(None) == outbound_templates.EMAIL_SUBJECT
    assert outbound_templates.subject_for("") == outbound_templates.EMAIL_SUBJECT


def test_the_evening_body_is_the_ruled_string_verbatim():
    """DECISIONS 192, character for character. This body had no verbatim pin
    until the ruling that changed it — which is why the word could sit here
    disagreeing with every webapp string for a whole spec."""
    assert render("digest_evening_normal", {}) == (
        "A normal day, start to finish. Next note in the morning."
    )


def test_no_outbound_body_says_the_retired_word():
    """The sweep itself, over every body under every label — not just the one
    template the ruling named. `rendered()` walks the whole registry, so a
    template added later carrying "ordinary" fails here on the day it lands."""
    for label in RELATIONSHIP_LABELS:
        for template_id, body in rendered(label):
            assert "ordinary" not in body.lower(), f"{template_id}: {body}"
    # The subjects are family-facing copy from the same module.
    for subject in (
        outbound_templates.EMAIL_SUBJECT,
        outbound_templates.subject_for("Mom"),
    ):
        assert "ordinary" not in subject.lower()


def test_the_recovered_evening_body_is_the_ruled_string_verbatim():
    """The email-polish pass's one new body, exactly as ruled."""
    assert render("digest_evening_recovered", {}) == (
        "A quiet start, then a normal day. Next note in the morning."
    )


def test_the_follow_on_hands_off_rather_than_instructing():
    """The ladder's last sentence: Kettle stops where the family starts."""
    body = render("follow_on_family", {"relationship": "Mom"})
    assert body.endswith("A call from you beats anything Kettle can send.")


def test_the_161_bodies_are_verbatim():
    """DECISIONS 161's two bodies, character for character — the last approved
    set that lived only in a chat transcript was lost (141/145), so the pin is
    against the ruling's text, not against taste."""
    assert render("all_clear_family", {"relationship": "Mom"}) == (
        "The shape of Mom's usual day is back. Kettle returns to its "
        "twice-a-day notes."
    )
    assert render("follow_on_unreachable", {"relationship": "Mom"}) == (
        "Mom's phone has been silent today, which is different from a quiet "
        "morning. A phone that is off or out of battery looks exactly like "
        "this. A call from you settles it either way."
    )
    # Both follow-ons share a kind; which renders is the engine's distinction,
    # and they never both send for the same day (a test in test_outbound.py
    # holds that from the engine's side).
    assert TEMPLATES["follow_on_unreachable"].kind == TEMPLATES["follow_on_family"].kind
    assert TEMPLATES["all_clear_family"].audience == "child"


def test_no_template_names_the_parent_it_is_about():
    """DECISIONS 149, and the one exception 217 opened.

    149 banned names because Kettle must never GUESS what a parent is called:
    the family picks `{relationship}` and the product says that, or says
    nothing. That reasoning is untouched here — no template names, or takes a
    variable for, the person it is about.

    What 217 added is a different act. `{owner_name}` is the first name of the
    family member who SET KETTLE UP, addressed to the parent, and it is not
    guessed: it is that member's own display name, or the ruled fallback. It
    exists because Meta's Utility category needs the message to say who asked
    for it, and without it the ask is Marketing and undeliverable to every US
    number (216). So the allowlist is two names wide and each is justified,
    rather than open.
    """
    ALLOWED = {"relationship", "owner_name"}
    for template in TEMPLATES.values():
        assert set(template.variables) <= ALLOWED, (
            f"{template.id} takes {template.variables} — only {ALLOWED} are ruled"
        )
        # The parent-naming ban itself, unchanged: no pet name in any body.
        for name in NAMES:
            if name == "Kettle":
                continue
            assert name not in template.body, f"a name in {template.id}: {name}"

    # And `owner_name` is spent on exactly one template — the ask — so the
    # exception cannot spread to a body that is ABOUT a parent.
    takes_owner = [t.id for t in TEMPLATES.values() if "owner_name" in t.variables]
    assert takes_owner == ["ask_parent"]


def test_the_owner_name_fallback_is_the_ruled_string_and_is_hard_to_reach_past():
    """DECISIONS 217's fallback, pinned, and the shapes that must trigger it.

    This string is the first thing a parent reads when a family has no usable
    name on file, so it is ruled copy and not a default someone can drift.
    """
    assert OWNER_FALLBACK == "Your family"
    assert_outbound_copy_law(OWNER_FALLBACK)

    # A real first name survives, including from a full display name.
    assert owner_first_name("Priya") == "Priya"
    assert owner_first_name("Hema Kumar") == "Hema"
    assert owner_first_name("  Hema  Kumar ") == "Hema"

    # Everything the ruling names as not-a-name falls back.
    for not_a_name in (
        None,
        "",
        "   ",
        "hema@example.com",   # an address in the name field
        "H",                  # an initial is not a name
        "H2",                 # a digit would also break the copy law
        "2Chainz",
    ):
        assert owner_first_name(not_a_name) == OWNER_FALLBACK, not_a_name


def test_no_template_stores_or_names_a_signal():
    """Signal names are the phone's vocabulary, never a family's."""
    for _, body in rendered():
        for signal, _grade in STANDARD_SIGNALS:
            assert signal not in body.lower()
        for label in SIGNAL_LABELS.values():
            assert label.lower() not in body.lower()


def test_a_template_cannot_render_with_a_variable_missing():
    """A message with `{relationship}` still in it is worse than no message."""
    with pytest.raises(ValueError):
        render("digest_morning_normal", {})
    with pytest.raises(ValueError):
        render("digest_morning_normal", {"relationship": ""})
    with pytest.raises(ValueError):
        render("digest_evening_normal", {"relationship": "Mom"})


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
        # DECISIONS 149's pronoun ban: the exact regressions 151 replaced, so a
        # revert of either body fails by name rather than sailing through.
        ("a guessed pronoun", "Mom's morning looked like her morning."),
        ("a guessed pronoun in a handoff", "She hasn't answered Kettle's note yet."),
        # DECISIONS 151's em dash ban, planted with the follow-on's old dash.
        ("an em dash", "You know their day best — a call beats anything."),
        # DECISIONS 192, planted with the exact body it replaced: the evening
        # digest as it really sent on Thursday night.
        ("the retired word", "An ordinary day, start to finish. Next note in the morning."),
        ("the retired word in a new sentence", "It looks like an ordinary morning."),
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
