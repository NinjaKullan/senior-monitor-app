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
# Spec 019 Amendment A §A.6: notes and replies through the door.
SERVER_INSTRUCTIONS = (
    "Kettle answers in its own sentences about a parent's day. Here Kettle can read, "
    "add a note and reply to a note. Anything else, like pausing a parent, is done in "
    "the Kettle app."
)
NOTE_SAVED = "Saved. The family will see it in Memory."
REPLY_SAVED = "Saved under {author}'s note from {date}."
NEED_WRITE = (
    "This connection can only read. Add Kettle to your assistant again to allow notes and replies."
)
WHICH_PARENT = "Say which parent this is about. You can name {names}."
NO_NOTE_TO_ANSWER = "Kettle can't find a note to answer."
CANNOT_SAVE = "Kettle couldn't save that. You can add it in the Kettle app: {app}."
WRITE_LIMIT = "That's a lot of notes for one hour. The rest can go in the Kettle app: {app}."
TOOL_ADD_NOTE = (
    "Add a note to the family's memory in the person's own words. Read the note back and "
    "confirm before calling. Name a parent to tag the note; give a date for something "
    "upcoming."
)
TOOL_REPLY = (
    "Reply to a note in the family's memory. Read the reply back and confirm before "
    "calling. With no author, the reply goes under the latest note; name an author, or a "
    "date, to pick another."
)
AUTHOR_VIA = "{name} via {client}"
# Spec 020 §5/§6: the card's one device line, a fact after the heard line.
DEVICE_LINE_MORNING = "{kind}, {time} this morning"
DEVICE_LINE_AFTERNOON = "{kind}, {time} this afternoon"
DEVICE_LINE_EVENING = "{kind}, {time} this evening"
#: Spec 020 §7: kind value → label. Mirrors copy.ts KIND_LABEL; the contract
#: test holds the two equal.
KIND_LABEL = {
    "plug": "Plug",
    "door": "Door",
    "motion": "Motion",
    "voice": "Voice routine",
    "fridge": "Fridge",
    "light": "Light",
}

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
    "DEVICE_LINE_MORNING",
    "DEVICE_LINE_AFTERNOON",
    "DEVICE_LINE_EVENING",
    "AUTHOR_VIA",
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
