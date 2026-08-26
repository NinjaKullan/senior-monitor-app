# Spec 010 — The city is the timezone: moving a parent

Status: approved in direction by Hema 2026-08-26 (the auto journal note in
§4 is marked (ruling) and awaits his yes/no). Builds on spec 009; the
city_label column and the Family screen field already exist. This spec
makes the city field the way a family MOVES a parent: pick the city, and
the clocks, digest times, and quiet-morning windows follow. Nobody ever
sees a timezone name.

Motivating case, recorded: a parent set up in Chennai relocates to Texas
for an extended stay. The child changes "Chennai" to "Dallas" and Kettle
is correct again, automatically.

Touches webapp/ (picker, write path) and product/ (transition honesty,
alert) plus migration 0019. All copy laws apply.

## 1. The picker (webapp)

- The Family screen's "City" field becomes a searchable combobox.
  Placeholder: "Where {display_name} lives". Typing filters a curated
  city list; picking an entry sets BOTH `parents.city_label` (the city's
  display form, e.g. "Dallas") and `parents.tz` (its IANA zone, e.g.
  America/Chicago) in one write, and sets `parents.tz_changed_utc` to
  now() when — and only when — the tz value actually changed.
- The list ships as a curated JSON asset in the webapp: roughly 300-400
  entries of {city, country, iana}, weighted toward Indian and US
  metros plus world capitals and major cities. Each entry's display form
  is "City, Country" ("Dallas, United States"; "Chennai, India").
- Beneath the results, a quiet escape hatch: "Can't find it? Pick the
  nearest big city." No raw timezone list is ever shown.
- Free text cannot be committed: only a picked entry writes. Clearing
  the field clears city_label only and never touches tz.
- The webapp validates the iana value against its own list before
  writing; the product test suite separately asserts every iana string
  in the shipped list is accepted by Postgres (`now() at time zone z`).

## 2. Migration 0019 (written by CC, applied to prod by the PM via MCP
before the webapp deploy)

- `alter table parents add column tz_changed_utc timestamptz;`
- `grant update (tz, tz_changed_utc) on parents to authenticated;`
  (0018's `parents_update_own_family` RLS policy already bounds rows to
  the caller's family; the column-scoped grant model continues —
  `display_name` and every other column stay refused, re-pinned.)

## 3. Transition honesty (product)

The timezone is load-bearing: digest slots, the quiet-morning cutoff,
and the local-midnight day boundary all read it. Rules for the day a
parent moves:

- The engine reads `parents.tz` fresh each cycle (verify; if any cached
  read exists, remove it). Digests fire at the configured local slots in
  the NEW zone from the next cycle onward.
- Changeover conservatism: from `tz_changed_utc` until the first local
  midnight in the new zone, the ask ladder is SUPPRESSED for that
  parent (no ask, no follow-on; a shifted clock can fabricate a quiet
  morning). Digests still send, chosen from data actually seen; the
  morning-quiet template is not used in this window (a "quiet" verdict
  under a moved clock is not evidence). The suppressed state records a
  `skipped` ledger row with detail naming the timezone change, so the
  ledger stays explainable.
- Recent-days classification: the changeover day is never marked "a
  quiet start"; it is a normal day if any routine pings arrived in
  either zone's version of that day, and a couldn't-hear day only if
  none did.
- Founder alert: on any tz change the engine writes an ops_alert and
  ntfy: "{display_name}: timezone changed {old} → {new} (city
  {city_label}) via webapp." A move must never be silent.

## 4. The journal remembers the move — (ruling)

If Hema approves: on a successful city change the webapp inserts a
journal entry tagged to the parent, author_label "Kettle", body
"{display_name}'s city changed to {city_label}." — the family's memory
records relocations without anyone typing. If he declines, nothing is
written and this section is dropped.

## 5. Tests

Webapp: picking writes label+tz+tz_changed_utc together; unchanged tz
does not touch tz_changed_utc; free text cannot commit; clearing
behavior; the escape-hatch string; pinned placeholder copy; the 009
surfaces render the new label/zone with no further change. Product: the
iana-list-accepted-by-Postgres sweep; ask suppression inside the
changeover window and normal resumption after the first new-zone
midnight; digest slot movement; the skipped ledger row's detail; the
ops_alert; column grants (display_name still refused). Chrome copy scan
over all new strings.

## Out of scope

Automatic timezone detection from pings; multi-home/seasonal profiles;
DST handling beyond what IANA zones already provide; editing tz through
any surface other than the city picker.
