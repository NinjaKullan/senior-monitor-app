# Spec 017 — Pause Kettle for one parent

Status: RATIFIED by Hema, 2026-09-04 (DECISIONS 274); strings verbatim. Founder ask, same day
(Asana 1218194014017087). Builds on 0023 (demo skip placement, 245),
015 (admin role).

## 1. What this is

An admin pauses Kettle for one parent: hospital stay, travelling with
a child, a broken phone. While paused, Kettle sends nothing about
that parent and raises nothing, and the app says so plainly so a
paused parent is never quietly forgotten. Resume is one tap.

## 2. Rules

- Admin only (015). Members see the paused state, not the control.
- Per parent, never per circle.
- Two durations: "for a week" and "until I turn it back on". No
  calendar picker in v1.
- While paused: no digests, no ask, no follow-on, no all-clear, no
  ops alerts for that parent. The engine skips the parent ABOVE the
  withhold rules, the same placement as the demo skip (267): nothing
  to record, so no skipped rows either.
- The day it is paused: whatever already went out stands; nothing
  more goes out that day, including the evening note.
- The day it resumes: treated as a fresh first day. No changed-
  morning ask fires from a baseline that predates the pause; the
  morning digest that day reads the normal/quiet state from that
  day's pings only. (0023's comment named both edges.)
- The paused state is LOUD: the Today card for that parent shows
  PAUSED_CARD instead of a day; the morning digest for the family
  carries one line PAUSED_DIGEST for that parent instead of their
  section; the Family screen's setup row shows PAUSED_SETUP.
- A week-long pause ends by itself; the app does not remind anyone
  beforehand in v1.

## 3. Data

Migration numbered at build time (268).

- `parents.paused_until timestamptz null`. Null = not paused; a
  week pause stores the instant; the open-ended pause stores
  'infinity' (Postgres timestamptz supports it), so one column
  carries both. `parents.paused_since timestamptz null` for the
  resume-day rule.
- Functions (SECURITY DEFINER, admin only, same pattern as 015):
  `app_pause_parent(parent_id, until)` where until is a timestamptz
  or 'infinity'; `app_resume_parent(parent_id)` sets both to null.
  No client UPDATE on parents.

## 4. Engine

`parents_with_tz` returns paused_until and paused_since. The loop
skips any parent with `paused_until > now` before any decision.
On the first pass after resume (paused_since not null and paused_
until <= now), the engine clears both fields and applies the fresh-
first-day rule for that local day; tests pin the exact instants.

## 5. Webapp

- Parent card on Today, admins: a small "Pause Kettle" link at the
  bottom; opens two choices, PAUSE_WEEK and PAUSE_OPEN, plus
  PAUSE_CANCEL. Paused card: PAUSED_CARD headline, PAUSED_UNTIL or
  PAUSED_OPEN_ENDED beneath, and for admins a "Turn Kettle back on"
  button.
- Members see the paused card without the controls.
- Family screen setup row: PAUSED_SETUP in place of "Set up and
  reporting".

## 6. Strings (VERBATIM; copy laws)

- PAUSE_LINK = "Pause Kettle"
- PAUSE_WEEK = "For a week"
- PAUSE_OPEN = "Until I turn it back on"
- PAUSE_CANCEL = "Not now"
- PAUSED_CARD = "Kettle is paused for {name}."
- PAUSED_UNTIL = "Back on {date}."  (family-timezone day, "Sep 11")
- PAUSED_OPEN_ENDED = "Until someone turns it back on."
- RESUME_BUTTON = "Turn Kettle back on"
- PAUSED_SETUP = "Paused"
- PAUSED_DIGEST = "Kettle is paused for {name}. Nothing to report."

## 7. Tests

Engine: paused parent produces no rows and no alerts across a full
day of passes while a neighbour runs the ladder; resume day fires no
ask from a stale baseline; a week pause expires on its own. Functions:
member refused; admin allowed; resume clears both fields. Webapp:
control hidden for members; paused card renders with the right
second line for each duration; copy-law walk. Digest: the paused
line replaces the parent's section.

## 8. Out of scope

Calendar picker; reminders before a pause ends; pausing a whole
circle; pausing from the parent's side.
