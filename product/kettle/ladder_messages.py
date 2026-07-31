"""Ladder copy (spec 004 §4). Binding, same law as the digest — plus urgency.

Separate module from `messages.py` on purpose. Digest copy may never describe
absence, and a test walks that module to keep it that way; ladder copy exists
precisely to describe absence. Keeping them apart means neither test has to be
weakened to accommodate the other.

The law here: calm, no counts, no speculation, no medical language, no digits,
no signal or app names, and no urgency vocabulary anywhere — not "emergency",
not "urgent", not "worried". A family reading one of these at 2pm on a Tuesday
should feel prompted to make a phone call, not frightened.
"""

from __future__ import annotations

ASK_TEMPLATE = (
    "This is Kettle. {name}, your phone has been quiet today. All good? Reply YES."
)

FAMILY_UNANSWERED = (
    "Kettle: {parent}'s usual routine hasn't been seen today, and {clause} "
    "answered a gentle check-in. A call from you may be all this needs.{contact}"
)

FAMILY_UNREACHABLE = (
    "Kettle: {parent}'s phone has been unreachable today (no signals of any "
    "kind). This is often a phone or network issue. A call from you is the "
    "fastest way to know.{contact}"
)

ALL_CLEAR = "Kettle: {parent}'s routine has resumed. All normal."

CONTACT_LINE = " Your named local contact is {name}{relation}{phone}."

# Subject pronoun plus its verb, so agreement survives the substitution:
# "they haven't answered", not "they hasn't answered". Nothing infers a pronoun
# from a name (QUESTIONS.md item 24, adopted as policy); with no pronoun
# recorded, every message uses the neutral clause.
UNANSWERED_CLAUSE = {
    "she": "she hasn't",
    "he": "he hasn't",
    "they": "they haven't",
}
NEUTRAL_CLAUSE = "they haven't"


def render_ask(senior_name: str) -> str:
    """The senior-facing check-in. The only message this product sends them."""
    return ASK_TEMPLATE.format(name=senior_name)


def render_contact_line(
    name: str | None, relation: str | None = None, phone: str | None = None
) -> str:
    """The named-local-contact suggestion. v1 never contacts them itself."""
    if not name:
        return ""
    return CONTACT_LINE.format(
        name=name,
        relation=f" ({relation})" if relation else "",
        phone=f" on {phone}" if phone else "",
    )


def render_family_unanswered(
    parent_name: str, pronoun: str | None = None, contact: str = ""
) -> str:
    """Routine unseen and the check-in unanswered — but the phone is alive."""
    clause = UNANSWERED_CLAUSE.get((pronoun or "").lower(), NEUTRAL_CLAUSE)
    return FAMILY_UNANSWERED.format(
        parent=parent_name, clause=clause, contact=contact
    )


def render_family_unreachable(parent_name: str, contact: str = "") -> str:
    """Nothing at all is arriving. Says exactly that, and no more."""
    return FAMILY_UNREACHABLE.format(parent=parent_name, contact=contact)


def render_all_clear(parent_name: str) -> str:
    """Sent once, and only to a family that was already told something."""
    return ALL_CLEAR.format(parent=parent_name)
