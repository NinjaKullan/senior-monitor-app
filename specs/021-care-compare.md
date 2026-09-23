# Spec 021 — Care Compare, a free tool under the Kettle name

Status: DRAFT by PM, 2026-09-23, for the founder's ratification.
Ruled: DECISIONS 341 (not a Kettle feature; a marketing asset), and
the founder's four answers of 2026-09-23 recorded in DECISIONS 342.
Builds on the MCP door's conventions (019: sentences, names never
ids, read-only tools, one `instructions` line) and on nothing else
in the product. It shares no process, database, secret or table
with kettle-api.

## 1. What this is

A free, public, read-only MCP server at `https://care.heykettle.com/mcp`
that answers, in sentences, from CMS's own Care Compare data: which
nursing homes and home health agencies are near a US ZIP code, how CMS
rates each one, and how two or three of them compare. It ranks nothing,
recommends nothing, and gives no medical advice. Every answer says
where the numbers came from and how old they are, and ends with the
one useful next step: call the provider.

Why it exists: the people who search for a nursing home today are
Kettle's buyers two years earlier. A tool they cite is worth more links
than any post. It carries the HeyKettle name once, in its `instructions`
line and on its page, and nothing else about Kettle.

The sibling sentence: "It's a little free helper that reads Medicare's
own ratings for nursing homes and home care near a ZIP code and tells
you plainly. It doesn't pick for you; it gives you the numbers and the
phone number."

## 2. Rulings (founder, 2026-09-23)

- First release: nursing homes and home health agencies. Hospitals and
  hospice are held (§9).
- Its own small Fly app, `kettle-care`, at `care.heykettle.com`. Not a
  router in kettle-api. No shared code beyond copying the MCP wiring
  pattern; no shared secrets; no database.
- "Near" means a ZIP code and a distance in miles, computed offline
  from the public Census 2020 ZCTA centroid file bundled with the app.
  No geocoding service, no key, no outbound call except to CMS.
- Data is read live from CMS, one whole state at a time, and kept in
  memory for 24 hours. Nothing is stored anywhere else.
- No accounts, no OAuth, no tokens. A per-IP rate limit and nothing
  else stands between the internet and the tool.
- Nothing about a question is logged: not the ZIP, not the names, not
  the IP. Log lines carry a status code and a count.

## 3. Tools (read-only; `readOnlyHint: true` on all three)

1. `find_care(kind, zip, miles?, min_rating?)`
   - `kind`: "nursing home" or "home health" (accept "nursing homes",
     "home health agency", "home care"; anything else gets KIND_UNKNOWN).
   - `zip`: five digits. Not five digits, or not in the centroid file:
     ZIP_UNKNOWN.
   - `miles`: 1 to 100, default 15.
   - `min_rating`: 1 to 5, optional; filters on the overall rating
     (nursing homes) or the quality of patient care rating (home
     health). Unrated providers are excluded when this is set.
   - Answer: up to 8 providers, nearest first, each as one sentence
     (§4). Zero matches: NONE_NEAR, then the nearest one beyond the
     radius if any within 100 miles (NEAREST_BEYOND). More than 8:
     MORE_LINE.
2. `care_details(name, zip)`
   - The one provider whose name matches best within 50 miles of
     `zip` (case-insensitive, punctuation-insensitive, best of
     prefix then substring; ties go to the nearer). None: NO_MATCH
     with the three nearest names as suggestions.
   - Answer: the full sentence set for that provider (§4), including
     the lines `find_care` leaves out.
3. `compare_care(names, zip)`
   - Two to four names, resolved as in `care_details`. Fewer than two
     resolved: COMPARE_NEED_TWO.
   - Answer: one paragraph per provider in the caller's order, each
     the §4 "details" sentence set, then COMPARE_CLOSE. No winner is
     named; no sums, no averages, no "best".

Every answer ends with SOURCE_LINE carrying the dataset's `modified`
date read from CMS at fetch time, and CALL_LINE.

## 4. Answer shape (Kettle as actor; strings in §10)

Nursing home, list sentence (find_care):
  "{name}, {city}, about {miles} miles away. CMS rates it {overall} of
   5 overall. {phone}."
  Unrated overall: "CMS has not rated it overall yet." replaces the
  rating clause.

Nursing home, details sentence set (care_details, compare_care):
  Line 1: "{name}, {address}, {city}, {state} {zip}, about {miles}
           miles from {asked_zip}. {phone}."
  Line 2: "CMS rates it {overall} of 5 overall: {health} for health
           inspections, {staffing} for staffing, {qm} for quality
           measures." (each of the four may be replaced by "not rated"
           when null; if all four are null the line is NOT_RATED_YET).
  Line 3: "{beds} certified beds. {ownership}."
  Line 4, only when true: ABUSE_LINE. Line 5, only when true:
           SPECIAL_FOCUS_LINE.

Home health, list sentence:
  "{name}, {city}, about {miles} miles away. CMS rates its quality of
   patient care {stars} of 5. {phone}."
  Unrated: "CMS has not rated its quality of patient care yet."

Home health, details sentence set:
  Line 1 as above (agency address).
  Line 2: the rating sentence, or the unrated sentence.
  Line 3: "Offers {services}." from the six service flags, in this
           order and wording: nursing care, physical therapy,
           occupational therapy, speech pathology, medical social
           services, home health aide. None flagged: SERVICES_NONE.
  Line 4: "{ownership}. Medicare certified since {year}."

Rules that hold everywhere:
- Names as CMS gives them, title-cased once (CMS shouts). Never a CCN
  or any id.
- Miles rounded to a whole number; under 1 mile reads "under a mile".
- Phone formatted (919) 555 0100.
- Ratings are CMS's words: "CMS rates it". Kettle never says "good",
  "best", "safe", "avoid", or any verdict. The abuse and special
  focus lines are the only warnings and they quote CMS's own flags.
- Distance is between the asked ZIP's centroid and the provider:
  nursing homes by their CMS latitude and longitude; home health
  agencies (no coordinates from CMS) by their ZIP's centroid, and the
  answer says "about" for both.
- No medical advice, no eligibility, no cost, no Medicaid or insurance
  talk. A question outside the two kinds gets the server's
  `instructions` line back as KIND_UNKNOWN says it.

## 5. Data

- Nursing homes: dataset `4pq5-n9py`, columns `provider_name`,
  `provider_address`, `citytown`, `state`, `zip_code`,
  `telephone_number`, `ownership_type`, `number_of_certified_beds`,
  `overall_rating`, `health_inspection_rating`, `staffing_rating`,
  `qm_rating`, `abuse_icon`, `special_focus_status`, `latitude`,
  `longitude`.
- Home health: dataset `6jpm-sxkc`, columns `provider_name`, `address`,
  `citytown`, `state`, `zip_code`, `telephone_number`,
  `type_of_ownership`, `quality_of_patient_care_star_rating`,
  `certification_date`, and the six `offers_*_services` flags.
- Fetch: `GET https://data.cms.gov/provider-data/api/1/datastore/query/
  {dataset}/0?limit=1000&offset={n}&conditions[0][property]=state&
  conditions[0][value]={ST}`, paged until `results` is short. The
  query cap is 1500 per call (verified 2026-09-23); 1000 is the page.
- "As of": `modified` from
  `.../api/1/metastore/schemas/dataset/items/{dataset}`, fetched with
  the state and cached with it.
- Cache: per (dataset, state), 24 hours, in process memory. A miss
  fetches; a CMS failure with a warm copy serves the warm copy and
  marks it; a CMS failure with no copy answers CMS_DOWN. Timeout 10
  seconds per page. No retries inside a request.
- Which states: the asked ZIP's state plus any state whose centroid
  bounding box lies within the radius (a border ZIP in Charlotte needs
  SC). ZCTA to state comes from the first three digits table bundled
  with the centroids.
- Centroids: Census `2020_Gaz_zcta_national.zip` (GEOID, INTPTLAT,
  INTPTLONG), converted at build time to a compact file checked into
  the repo (`care/data/zcta.csv`, three columns, about 33,000 rows).
  Distance is great-circle, in statute miles.

## 6. Service

- Folder `care/` at the repo root: `care/app.py` (FastAPI + the `mcp`
  package as kettle-api uses it; `/mcp` streamable HTTP; `/` a one-line
  text health answer; `/healthz`), `care/cms.py` (fetch, page, cache),
  `care/geo.py` (centroids, distance), `care/copy.py` (§10 verbatim),
  `care/tests/`, `care/data/zcta.csv`, `care/Dockerfile`,
  `care/fly.toml` (app `kettle-care`, one shared-cpu machine, region
  iad), `care/README.md`.
- DNS: `care` CNAME on heykettle.com in Cloudflare, proxied, to the Fly
  app; founder's console.
- No auth. The MCP server advertises no OAuth metadata; a client that
  asks for one gets 404. Rate limit: 60 tool calls per hour per
  `Fly-Client-IP`, in memory, refusals answer RATE_LIMITED as a normal
  tool result. No CORS beyond what the MCP transport needs.
- Outbound: `data.cms.gov` only. An allowlist in code; a test asserts
  the HTTP client refuses any other host. (The F1 lesson, applied on
  day one.)
- Logging: one line per tool call with tool name, status word (ok,
  none, refused, cms_down) and result count. Never the arguments.
  uvicorn access log off, as kettle-api.
- Instructions line (server `instructions`, verbatim §10
  SERVER_INSTRUCTIONS).
- Tool annotations: `readOnlyHint: true`, `openWorldHint: false`.

## 7. The page

`https://heykettle.com/care`, a static page in `site/` under the site's
laws (what, never how; one image set; copy law). It carries: the
sibling sentence, the connector address with Copy, one paragraph on
where the numbers come from (Medicare's Care Compare, named because
it is the source, not a tool), the three questions it answers as
examples, and one line back to Kettle ("Kettle is the other thing we
make: ..." using the site's own tagline). Strings in §10 PAGE_*. The
page is the link target for everything the SEO backlog does with
this asset; the MCP address is never the link target.

## 8. Acceptance (CC, tests in `care/tests/`)

1. `find_care("nursing home", "27502")` against a recorded CMS fixture
   for NC returns at most 8, nearest first, every sentence matching
   §4 character for character, SOURCE_LINE carrying the fixture's
   modified date.
2. Home health distance uses the agency ZIP centroid; nursing home
   distance uses CMS coordinates; a nursing home with null
   coordinates falls back to its ZIP centroid.
3. Border case: a ZIP within `miles` of a state line pulls the second
   state; a fixture provider across the line appears.
4. `min_rating` excludes unrated providers; without it they appear
   with the unrated sentence.
5. `care_details` name matching: exact, prefix, substring, punctuation
   and case ignored, nearer wins a tie; no match lists three nearest.
6. `compare_care` with one resolvable name answers COMPARE_NEED_TWO;
   with three answers three paragraphs in the caller's order and
   never a comparative word (a test greps the answer for "best",
   "better", "worse", "top", "recommend").
7. Cache: second call within 24 hours makes no CMS request; a CMS 500
   with a warm copy answers from the copy and appends STALE_LINE; with
   no copy answers CMS_DOWN.
8. Pagination: a fixture state with 2,300 rows is fetched in three
   pages of 1000.
9. Rate limit: the 61st call in an hour from one IP answers
   RATE_LIMITED; another IP is unaffected.
10. Outbound allowlist: a request to any host but data.cms.gov raises
    before the socket opens.
11. Logging: a tool call with a ZIP and a name logs neither.
12. Every string in §10 is pinned by a test, verbatim.
13. The `instructions` line and the three tool descriptions are the
    §10 strings.
14. `ruff` clean; `KETTLE_REQUIRE_POSTGRES` is irrelevant here (no
    database); the suite runs with no network (fixtures only).

## 9. Held

- Hospitals (`xubh-q36u`) and hospice: same shape, later release.
- A listing in the MCP registry and the ChatGPT connector directory:
  after the page exists and the first week of logs is read.
- A "closest with a rating of 4 or more" shortcut; a "what should I ask
  when I call" tool. Both are copy, not code, and wait for a real
  question from a real family.
- Any inclusion in the Kettle app or the family MCP (019). Ruled out
  in 341; not held, out.

## 10. Strings (verbatim; copy laws; no em dashes)

Server:
- SERVER_INSTRUCTIONS = "Care Compare by HeyKettle reads Medicare's own Care Compare ratings for nursing homes and home health agencies near a US ZIP code and answers in plain sentences. It does not rank, recommend, or give medical advice. Read the ratings back to the person, then suggest they call the provider. For anything else about care, say this tool only covers those two kinds."
- TOOL_FIND = "Nursing homes or home health agencies near a US ZIP code, nearest first, with Medicare's rating and a phone number for each. Give the kind, the ZIP, and optionally miles (default 15) and a minimum rating."
- TOOL_DETAILS = "Everything Medicare publishes in Care Compare about one nursing home or home health agency, by name, near a ZIP code."
- TOOL_COMPARE = "Two to four nursing homes or home health agencies side by side, by name, near a ZIP code. Medicare's figures for each, in the order given, with no winner picked."
- SOURCE_LINE = "Source: Medicare Care Compare, last updated {date}. Ratings are Medicare's, not ours."
- CALL_LINE = "The next step is a phone call to the provider. Ask about openings, cost, and a visit."
- STALE_LINE = "Medicare's site did not answer just now, so these figures are from our copy of {date}."
- CMS_DOWN = "Medicare's site did not answer just now and we have no copy to read from. Try again in a few minutes."
- KIND_UNKNOWN = "This tool covers nursing homes and home health agencies only. Say which one."
- ZIP_UNKNOWN = "That does not look like a US ZIP code. Give the five digits."
- NONE_NEAR = "No {kind_plural} within {miles} miles of {zip} in Medicare's list."
- NEAREST_BEYOND = "The nearest is {name} in {city}, about {miles} miles away."
- MORE_LINE = "There are {more} more within {miles} miles. Ask for a smaller distance or a minimum rating to narrow it."
- NO_MATCH = "Medicare's list has nothing near {zip} called {asked}. The nearest names are {names}."
- COMPARE_NEED_TWO = "Give at least two names to compare."
- COMPARE_CLOSE = "Those are Medicare's figures for each. Which fits depends on what the family needs; a visit and a call tell you more than the stars."
- NOT_RATED_YET = "CMS has not rated it yet."
- ABUSE_LINE = "CMS has flagged this home for a recent abuse citation."
- SPECIAL_FOCUS_LINE = "CMS lists it as a Special Focus Facility, one it inspects more often because of a history of problems."
- SERVICES_NONE = "Medicare lists no services for it."
- RATE_LIMITED = "This tool has answered a lot of questions from here in the last hour. Try again a little later."
- KIND_NURSING = "nursing home"; KIND_NURSING_PLURAL = "nursing homes"
- KIND_HOME_HEALTH = "home health agency"; KIND_HOME_HEALTH_PLURAL = "home health agencies"
- UNDER_A_MILE = "under a mile"

Page (`site/`, heykettle.com/care):
- PAGE_TITLE = "Care Compare by HeyKettle"
- PAGE_LEDE = "A free helper that reads Medicare's own ratings for nursing homes and home health agencies near a ZIP code and tells you plainly. It does not pick for you. It gives you the numbers and the phone number."
- PAGE_HOW = "Add it to Claude, ChatGPT, or another assistant as a connector, once, with this address. Then ask in your own words."
- PAGE_ADDRESS = "https://care.heykettle.com/mcp"
- PAGE_COPY = "Copy"
- PAGE_COPIED = "Copied"
- PAGE_EXAMPLES_HEAD = "Things people ask it"
- PAGE_EXAMPLE_1 = "Nursing homes within 15 miles of 43215 with a rating of 4 or more."
- PAGE_EXAMPLE_2 = "Everything Medicare says about Autumn Care of Biscoe."
- PAGE_EXAMPLE_3 = "Compare the three home health agencies nearest to 27502."
- PAGE_SOURCE = "Every number comes from Medicare's Care Compare, the same figures on medicare.gov, and every answer says how old they are. We add nothing and we keep nothing: no account, no history, no record of what you asked."
- PAGE_KETTLE = "Kettle is the other thing we make. {tagline}"
- PAGE_KETTLE_LINK = "See Kettle"
