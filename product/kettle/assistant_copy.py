"""Every string an assistant reads (spec 019 §8), Kettle as actor.

Server-side copy in one module, scanned by the same laws as every body in the
template registry. The strings marked "from copy.ts" are the webapp's own,
copied here verbatim; `product/tests/test_assistant_copy.py` reads copy.ts
and asserts the two files agree, so a reword in one place fails in the other.
"""

from __future__ import annotations

# --- Kettle's answers ---------------------------------------------------------
TODAY_NOTHING_YET = "Kettle has not written about {name} yet today."
DAY_NOTHING = "Kettle did not write about {name} that day."
NO_SUCH_PARENT = "Kettle does not know a parent called {asked}. You can ask about {names}."
MORNING_NOTE = "Morning note"
EVENING_NOTE = "Evening note"
ASK_SENT = "Kettle asked {name}"
FOLLOW_ON_SENT = "Kettle wrote to the family"
ALL_CLEAR_SENT = "All clear"

# --- Tool descriptions (the text the assistant reads) -------------------------
TOOL_TODAY = (
    "How a parent's day is going, in Kettle's words: the latest note Kettle "
    "sent today and when their phone was last heard from. Give a parent's "
    "name, or leave it out for everyone."
)
TOOL_PARENT_DAY = (
    "What Kettle wrote about a parent on one day, up to sixty days back. "
    "Dates are in the parent's time zone."
)
TOOL_MEMORY = (
    "The family's notes and replies, newest first, with anything upcoming at "
    "the top. Dates are in the family's time zone."
)
TOOL_WHO_TO_CALL = (
    "The parent's number and the people the family listed to call if they cannot reach them."
)
TOOL_CIRCLES = (
    "The circles this person belongs to: parents, where they live, and who is in the circle."
)

# --- From copy.ts, verbatim (the contract test holds them equal) ---------------
HEARD_MOMENTS = "Heard from moments ago"
HEARD_MINUTES = "Heard from {n} minutes ago"
HEARD_HOUR = "Heard from 1 hour ago"
HEARD_HOURS = "Heard from {n} hours ago"
HEARD_DAY = "Heard from 1 day ago"
HEARD_DAYS = "Heard from {n} days ago"
META_HEARD_DAYS = "Last heard from {days} days ago."
META_NOTHING_YET = "Nothing has reached Kettle yet."
CITY_NOW = "{city} · {time} there now"
CALL_LABEL = "Call {name} ↗"
UPCOMING_LABEL = "Upcoming"
EDITED_MARK = "edited"
AUTO_NOTE_AUTHOR = "Kettle"
PAUSED_CARD = "Kettle is paused for {name}."
PAUSED_UNTIL = "Back on {date}."
PAUSED_OPEN_ENDED = "Until someone turns it back on."
ASSISTANT_FALLBACK = "An assistant"

#: The copy.ts keys these mirror, for the contract test.
SHARED_WITH_WEBAPP = (
    "HEARD_MOMENTS",
    "HEARD_MINUTES",
    "HEARD_HOUR",
    "HEARD_HOURS",
    "HEARD_DAY",
    "HEARD_DAYS",
    "META_HEARD_DAYS",
    "META_NOTHING_YET",
    "CITY_NOW",
    "CALL_LABEL",
    "UPCOMING_LABEL",
    "EDITED_MARK",
    "AUTO_NOTE_AUTHOR",
    "PAUSED_CARD",
    "PAUSED_UNTIL",
    "PAUSED_OPEN_ENDED",
    "ASSISTANT_FALLBACK",
)

#: Everything above that an assistant can read, for the copy-law scan.
ALL_STRINGS = {
    name: value for name, value in globals().items() if name.isupper() and isinstance(value, str)
}


def render_heard(seconds_ago: float, window_days: int = 14) -> str:
    """copy.ts's renderHeard, verbatim in thresholds (spec 009 §2)."""
    minutes = int(seconds_ago // 60)
    if minutes < 2:
        return HEARD_MOMENTS
    if minutes < 60:
        return HEARD_MINUTES.replace("{n}", str(minutes))
    hours = minutes // 60
    if hours < 2:
        return HEARD_HOUR
    if hours < 24:
        return HEARD_HOURS.replace("{n}", str(hours))
    days = hours // 24
    if days > window_days:
        return META_HEARD_DAYS.replace("{days}", str(days))
    if days < 2:
        return HEARD_DAY
    return HEARD_DAYS.replace("{n}", str(days))
