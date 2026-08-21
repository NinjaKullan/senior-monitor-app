"""Family-facing message copy. These templates are product law, not strings.

Two independent derivations reached the same rule (PLAN.md, Jul 26): the founder's
"don't give the child ammunition" and the adversarial review's "counts are a
behavior profile". So the copy is coarse reassurance and nothing else — no
counts, no app or signal names, no trends, no comparisons to other days, and no
digits anywhere except the one clock time in the morning message.

Everything here is sent only when routine WAS observed. There is no template in
this module for the absence of activity, and there must not be one: absence
messaging to families is spec 004's, and messaging the senior is nobody's yet
(spec 003 §0).
"""

from __future__ import annotations

from datetime import datetime

MORNING_TEMPLATE = "Good morning — {parent}'s day started normally ({time} {clock})."

EVENING_ONE = "{parent} had a normal, active day."
EVENING_TWO = "{first} and {second} both had normal, active days."
EVENING_MANY = "{leading} and {last} all had normal, active days."

# Used only when a parent's pronoun is explicitly recorded. Nothing infers a
# pronoun from a name, so with no pronoun column in the schema this stays
# unreached and every message uses the neutral form (DECISIONS.md item 24).
CLOCK_BY_PRONOUN = {
    "she": "her time",
    "he": "his time",
    "they": "their time",
}
CLOCK_NEUTRAL = "local time"


def format_time(local_dt: datetime) -> str:
    """The one number allowed in a digest: a wall-clock time, to the minute.

    Twelve-hour with lowercase am/pm — these are messages to a family, and both
    target markets read "8:12 am" more warmly than "08:12". Built by hand rather
    than with %-I/%p, which are platform-dependent and upper-case respectively.
    """
    hour = local_dt.hour % 12 or 12
    meridiem = "am" if local_dt.hour < 12 else "pm"
    return f"{hour}:{local_dt.minute:02d} {meridiem}"


def render_morning(
    parent_name: str, first_ping_local: datetime, pronoun: str | None = None
) -> str:
    """The 'day started' message, rendered from an observed first ping.

    `first_ping_local` must be a real ping time — there is deliberately no way to
    render this message without one. A "day started normally" with no evidence
    behind it is manufactured reassurance.
    """
    clock = CLOCK_BY_PRONOUN.get((pronoun or "").lower(), CLOCK_NEUTRAL)
    return MORNING_TEMPLATE.format(
        parent=parent_name, time=format_time(first_ping_local), clock=clock
    )


def render_evening(parent_names: list[str]) -> str:
    """The daily summary, naming only the parents who were actually active."""
    if not parent_names:
        raise ValueError("an evening digest needs at least one active parent")
    if len(parent_names) == 1:
        return EVENING_ONE.format(parent=parent_names[0])
    if len(parent_names) == 2:
        return EVENING_TWO.format(first=parent_names[0], second=parent_names[1])
    return EVENING_MANY.format(
        leading=", ".join(parent_names[:-1]), last=parent_names[-1]
    )
