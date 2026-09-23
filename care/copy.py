"""Every sentence Care Compare says (spec 021 §10, verbatim, and the §4 shapes).

One file, the way kettle-api keeps `assistant_copy.py`: the strings are a
ruling, and `tests/test_copy.py` reads spec 021 §10 and asserts each one here
character for character, so an "improved" word fails by diff.

Kettle is the actor in these sentences and CMS is the source. Nothing here
ranks, recommends, or judges; the only warnings are CMS's own two flags.

The PAGE_* strings are the site's (site/public/care/index.html) and are pinned
there by site/src/tests/care.test.ts against the same spec section.
"""

from __future__ import annotations

# --- §10 server strings (verbatim) -------------------------------------------

SERVER_INSTRUCTIONS = (
    "Care Compare by HeyKettle reads Medicare's own Care Compare ratings for nursing homes "
    "and home health agencies near a US ZIP code and answers in plain sentences. It does not "
    "rank, recommend, or give medical advice. Read the ratings back to the person, then "
    "suggest they call the provider. For anything else about care, say this tool only covers "
    "those two kinds."
)
TOOL_FIND = (
    "Nursing homes or home health agencies near a US ZIP code, nearest first, with Medicare's "
    "rating and a phone number for each. Give the kind, the ZIP, and optionally miles "
    "(default 15) and a minimum rating."
)
TOOL_DETAILS = (
    "Everything Medicare publishes in Care Compare about one nursing home or home health "
    "agency, by name, near a ZIP code."
)
TOOL_COMPARE = (
    "Two to four nursing homes or home health agencies side by side, by name, near a ZIP "
    "code. Medicare's figures for each, in the order given, with no winner picked."
)
SOURCE_LINE = (
    "Source: Medicare Care Compare, last updated {date}. Ratings are Medicare's, not ours."
)
CALL_LINE = (
    "The next step is a phone call to the provider. Ask about openings, cost, and a visit."
)
STALE_LINE = (
    "Medicare's site did not answer just now, so these figures are from our copy of {date}."
)
CMS_DOWN = (
    "Medicare's site did not answer just now and we have no copy to read from. Try again in "
    "a few minutes."
)
KIND_UNKNOWN = "This tool covers nursing homes and home health agencies only. Say which one."
ZIP_UNKNOWN = "That does not look like a US ZIP code. Give the five digits."
NONE_NEAR = "No {kind_plural} within {miles} miles of {zip} in Medicare's list."
NEAREST_BEYOND = "The nearest is {name} in {city}, about {miles} miles away."
MORE_LINE = (
    "There are {more} more within {miles} miles. Ask for a smaller distance or a minimum "
    "rating to narrow it."
)
NO_MATCH = (
    "Medicare's list has nothing near {zip} called {asked}. The nearest names are {names}."
)
COMPARE_NEED_TWO = "Give at least two names to compare."
COMPARE_CLOSE = (
    "Those are Medicare's figures for each. Which fits depends on what the family needs; a "
    "visit and a call tell you more than the stars."
)
NOT_RATED_YET = "CMS has not rated it yet."
ABUSE_LINE = "CMS has flagged this home for a recent abuse citation."
SPECIAL_FOCUS_LINE = (
    "CMS lists it as a Special Focus Facility, one it inspects more often because of a "
    "history of problems."
)
SERVICES_NONE = "Medicare lists no services for it."
RATE_LIMITED = (
    "This tool has answered a lot of questions from here in the last hour. Try again a "
    "little later."
)
KIND_NURSING = "nursing home"
KIND_NURSING_PLURAL = "nursing homes"
KIND_HOME_HEALTH = "home health agency"
KIND_HOME_HEALTH_PLURAL = "home health agencies"
UNDER_A_MILE = "under a mile"

#: The server's name as a client lists it; the page's title, PAGE_TITLE.
SERVER_NAME = "Care Compare by HeyKettle"

# --- §4 answer shapes ----------------------------------------------------------
# Written out in §4 rather than §10; kept here so every sentence has one home.
# `{distance}` is "about 3 miles" or UNDER_A_MILE (§4: "under 1 mile reads
# 'under a mile'"); `{phone_sentence}` is " (919) 555 0100." or empty when CMS
# lists no number.

NH_LIST = "{name}, {city}, {distance} away. {rating}{phone_sentence}"
NH_LIST_RATED = "CMS rates it {overall} of 5 overall."
NH_LIST_UNRATED = "CMS has not rated it overall yet."
NH_DETAILS_RATINGS = (
    "CMS rates it {overall} overall: {health} for health inspections, {staffing} for "
    "staffing, {qm} for quality measures."
)
NH_OVERALL = "{overall} of 5"
NOT_RATED = "not rated"
NH_BEDS = "{beds} certified beds."

HH_LIST = "{name}, {city}, {distance} away. {rating}{phone_sentence}"
HH_RATED = "CMS rates its quality of patient care {stars} of 5."
HH_UNRATED = "CMS has not rated its quality of patient care yet."
HH_SERVICES = "Offers {services}."
HH_CERTIFIED = "Medicare certified since {year}."
#: §4's six service flags, in its order and wording.
HH_SERVICE_WORDS = (
    "nursing care",
    "physical therapy",
    "occupational therapy",
    "speech pathology",
    "medical social services",
    "home health aide",
)

DETAILS_LINE_1 = "{name}, {address}, {city}, {state} {zip}, {distance} from {asked_zip}.{phone}"
DISTANCE_ABOUT = "about {miles} miles"
DISTANCE_ABOUT_ONE = "about 1 mile"
