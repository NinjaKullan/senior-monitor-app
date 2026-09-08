# Spec 020 — The family's own devices (a recorded fact, never a judgement)

Status: RATIFIED by Hema, 2026-09-08 (DECISIONS 312); strings verbatim.
Written by PM from DECISIONS 311 (ruled 2026-09-07/08). Builds on the
ping path (002), setup rows (005b), circles (015), the day view (009/010),
the night state (303) and the day clock (299).

## 1. What this is

A family that already has something in the parent's home that can call
a web address (a smart plug, a door sensor, a motion sensor, a voice
routine) can give it a Kettle address. When the thing fires, Kettle
records which address and when. That is all Kettle records, and that is
all Kettle says: "Plug, 8:05 this morning." Nobody asks whether the plug
means the parent is fine; the family reads it the way they read "heard
from". The engine does not see it.

The sibling sentence: "If Amma's kettle is on a smart plug, the app can
show you when it switched on. Kettle doesn't decide anything from it;
you just get to see it."

## 2. Rulings (founder, DECISIONS 311)

- A device is (parent, kind from a list, where it lives from a short
  list of platforms). No person-or-household grade is asked, stored or
  inferred. The pet, the housekeeper and the visiting sister are the
  family's to read.
- Nothing feeds the engine. Not the ask, not the follow-on, not the
  all clear, not "heard from", not the dots, not the arc, not
  unreachable. The engine's inputs are unchanged by this spec, and a
  test says so.
- Surfaces, opt-in by installing: the Today card carries ONE line, the
  most recent device today; the parent's day view lists each device's
  last time today for every member; the setup rows carry per-device
  plumbing for admins, with Remove. Nothing in the emails.
- Labels name the thing, never the room. The list is ours; the family
  never types a label.
- The line follows the day clock: it starts at 06:00 in the parent's
  zone (299) and is not shown while the card is in its night state
  (303).
- The parent is told, in setup copy, LAW-6 style; no ceremony.
- At most three devices per parent.
- Fixed for good: the address format, the label list (grows, never
  frees), the parent's wording.

## 3. Data (migration numbered at build time; 0031 is next free)

- `household_devices`: id, parent_id, kind (check: one of KINDS below),
  platform (text null; one of PLATFORMS or null), token (unique, same
  shape as `devices.device_token`), created_utc, removed_utc null.
  Family members read their own circles' rows through RLS without the
  token column (a view, `household_devices_view`, is the read surface);
  the token is returned only by `app_household_device_address(device_id)`
  (SECURITY DEFINER, admins of that parent's circle). No client insert
  or update; 0004 doctrine.
- `household_pings`: id, device_id → household_devices, ts_utc. No IP,
  hashed or plain; no body; nothing else. Family read through RLS via
  the device's parent's circle. Swept after thirty days; nothing shown
  reaches back further than today, and the setup row's "heard" line
  needs less than that.
- Functions, SECURITY DEFINER, `authenticated`, admin of the parent's
  circle: `app_add_household_device(parent_id, kind, platform)` returns
  the new row's id (refuses a fourth device, 23514 `device_limit`;
  refuses an unknown kind); `app_remove_household_device(device_id)`
  sets removed_utc. A removed device's address stops in the same
  instant; its pings stay for the sweep and are never shown.
- Separate tables on purpose. `pings` is read by the engine, the
  heartbeat and the webapp's verdicts (any ping makes a quiet start;
  the latest per signal feeds unreachable). A household ping in that
  table would move the verdicts, which 311 forbids.

## 4. Ingest

- `GET|POST /d/{token}`. Path only; query, headers and body are
  ignored. The reply is `ok`, 200, for a live token, a removed token, an
  unknown token, and a duplicate inside the window alike: the address
  never says whether it is real (311: dropped silently, never a 404).
  A malformed token (wrong shape) is a 404 like any unknown path.
- Dedupe: one recorded ping per device per sixty seconds
  (DEDUPE_WINDOW_S); extras are dropped, still `ok`.
- No IP is read, hashed or stored on this route. The waitlist's flood
  counter (308) is not applied: a device fires on its own schedule and
  a per-token window already bounds the writes.
- The engine, the heartbeat and the outbound roster do not read
  `household_pings`. A product-side test asserts that no module under
  `kettle/` except the ingest route and the assistant's `today` names
  the table.

## 5. Webapp

- Family screen, SETUP, per parent, below the phone row (admins only;
  members see the rows without Add or Remove and without the address):
  DEVICES_INTRO, then each device as "{KIND_LABEL} · {heard}" where
  {heard} is HEARD_* computed from the device's last ping (or
  DEVICE_NOTHING_YET), with DEVICE_ADDRESS (copies the full address
  `https://<api host>/d/<token>`, DEVICE_COPIED for a moment) and
  DEVICE_REMOVE (confirm DEVICE_REMOVE_CONFIRM, DEVICE_REMOVE_YES,
  DEVICE_REMOVE_NO). Under three devices: DEVICE_ADD opens a two-pick
  sheet, kind (KIND_LABEL list) and platform (PLATFORM_LABEL list, with
  PLATFORM_OTHER), then DEVICE_ADD_DONE; the new row appears with its
  address and the platform's one-line recipe (RECIPE_*) under it. At
  three: DEVICE_LIMIT instead of the button. The parent-told line,
  DEVICE_TELL, sits under the intro, always.
- Today card: when the parent has at least one device with a ping today
  from 06:00 local on, and the card is not in its night, paused or
  unreachable state, one line under the heard-from block:
  DEVICE_LINE_MORNING / _AFTERNOON / _EVENING by the ping's local hour
  (before 12, 12 to 17:59, 18 on; the app's AFTERNOON_START and
  EVENING_START, corrected from "after 17" at build, DECISIONS 314), with the most recent device's
  KIND_LABEL and its time in the parent's zone. Same type size and
  colour as the dual clock line: a fact, not the verdict. No device or
  no ping today: no line, no placeholder.
- Day view (View {name}'s day): a block DEVICES_TODAY under the arc,
  listing each device with a ping today from 06:00 local on as
  "{KIND_LABEL} · {time}", most recent first, at most three rows;
  no device: the block is absent; devices but nothing today:
  DEVICES_NONE_TODAY. Today only; a past day shows nothing.
- Rollup, emails, dots, arc, glyph, unreachable, paused, night: unchanged.

## 6. Assistant (019)

`today` appends the card's device line as its own sentence, the same
string, after the heard line and before CITY_NOW. `parent_day`, `memory`,
`who_to_call`, `circles`: unchanged. Nothing new is written.

## 7. Strings (VERBATIM; copy laws)

Kinds (`kind` value → KIND_LABEL):
- plug → "Plug"
- door → "Door"
- motion → "Motion"
- voice → "Voice routine"
- fridge → "Fridge"
- light → "Light"

Platforms (`platform` value → PLATFORM_LABEL):
- home_assistant → "Home Assistant"
- ifttt → "IFTTT"
- smartthings → "SmartThings"
- alexa → "Alexa routine"
- google_home → "Google Home routine"
- other → "Something else"

Webapp (`copy.ts`):
- DEVICES_INTRO = "Something in {name}'s home can tell Kettle when it switches on or opens. Kettle only notes the time. It never changes what Kettle says about {name}'s day."
- DEVICE_TELL = "Tell {name} what you've set up in the house."
- DEVICE_ADD = "Add a device"
- DEVICE_ADD_KIND = "What is it?"
- DEVICE_ADD_PLATFORM = "Where will you set it up?"
- DEVICE_ADD_DONE = "Add"
- DEVICE_ADD_CANCEL = "Not now"
- DEVICE_LIMIT = "Up to three devices for {name}."
- DEVICE_ADDRESS = "Copy address"
- DEVICE_COPIED = "Copied"
- DEVICE_NOTHING_YET = "Nothing heard yet"
- DEVICE_REMOVE = "Remove"
- DEVICE_REMOVE_CONFIRM = "Remove the {kind}? Its address stops working right away."
- DEVICE_REMOVE_YES = "Remove"
- DEVICE_REMOVE_NO = "Keep it"
- DEVICE_LINE_MORNING = "{kind}, {time} this morning"
- DEVICE_LINE_AFTERNOON = "{kind}, {time} this afternoon"
- DEVICE_LINE_EVENING = "{kind}, {time} this evening"
- DEVICES_TODAY = "In the house today"
- DEVICES_NONE_TODAY = "Nothing from the house yet today."
- DEVICE_ROW = "{kind} · {time}"

Recipes (setup page only; mechanism vocabulary is allowed there, LAW-7):
- RECIPE_HOME_ASSISTANT = "In Home Assistant, add a rest_command that does a GET to this address, then call it from the automation for this device."
- RECIPE_IFTTT = "In IFTTT, make an applet: your device as the trigger, Webhooks 'Make a web request' as the action, this address, method GET."
- RECIPE_SMARTTHINGS = "In SmartThings, use a routine with a webhook action (through IFTTT or a SmartApp that can call a URL) pointing at this address."
- RECIPE_ALEXA = "Alexa routines cannot call an address on their own. Put the routine's action through IFTTT or Home Assistant, and point that at this address."
- RECIPE_GOOGLE_HOME = "Google Home routines cannot call an address on their own. Put the routine's action through IFTTT or Home Assistant, and point that at this address."
- RECIPE_OTHER = "Anything that can open this address, once, when the thing happens, will do."

Server (`assistant_copy.py`): DEVICE_LINE_* and KIND_LABEL mirrored; the
contract test asserts the two files agree.

Times render as the app already renders a clock ("8:05 am"); the copy
scan runs on every rendered line here, including the recipes.

## 8. Tests (CC)

- Ingest: live token records one row; a second inside sixty seconds
  records nothing; removed and unknown tokens answer `ok` 200 and record
  nothing; a wrong-shaped token is 404; no IP column exists to write.
- Engine isolation: the named test that no engine, heartbeat or roster
  module reads `household_pings`; the replay suite's verdicts are
  byte-identical with a household ping planted five minutes before a
  quiet-morning ask.
- Functions: admin adds; member refused (42501); fourth device refused
  (23514 `device_limit`); unknown kind refused; remove sets removed_utc
  and the address answers `ok` while recording nothing; the address
  function refuses members.
- RLS: members of the circle read the view and the pings; the token
  never appears on the view; another circle reads nothing.
- Webapp: the card line only with a ping today from 06:00 on; the
  05:50 ping shows nothing; morning/afternoon/evening by the parent's
  local hour; night, paused, unreachable suppress the line; most recent
  device wins; the day view lists at most three, today only; setup rows
  by role (Add, address and Remove admins only); the copy-law scan over
  every rendered line including the recipes.
- Assistant: `today` carries the line as its own sentence, closed with a
  full stop, before CITY_NOW; absent when the card would show none.
- Strings verbatim in both files; contract test.

## 9. Deploy

PM applies 0031 → `cd product && fly deploy` → `cd webapp && npm run ci
&& fly deploy`. First use, the founder: a smart plug on Amma's kettle or
a voice routine, whichever is already in the house, added from the
Family screen, the address pasted per the recipe, and the next morning's
card read against the ledger. One DECISIONS entry.

## 10. Out of scope

Corroboration (a household ping delaying or shaping an ask); the voice
routine counting for the engine as person-grade (the one signal that
plainly is; revisit with pings behind it); more than one line on the
card; history, dots or arc segments from devices; anything in the
emails; a per-device ops alert when a device goes quiet; free-text
labels; room names; a fourth device; Kettle configuring anyone's
platform for them.
