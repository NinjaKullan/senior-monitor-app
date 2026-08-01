# Spec 005c — Glance warmth pass

*PM: Fable, from founder direction Jul 31 ("people won't pay for 'All normal' — make the kid feel warm and know Mom's safe"). Scope: webapp Today screen + copy. The law stands: warmth rises, information stays coarse. No counts, no app names, no history/trends, no manufactured liveness.*

## 1. Warm copy (replaces the flat states; binding, same test regime)

- Day-part aware headlines, per parent, chosen by parent-local time and whether routine has been seen:
  - Seen, morning: `{Name}'s morning started the usual way`
  - Seen, afternoon: `A normal day so far` / evening: `A normal, gentle day`
  - Not seen yet, before ~noon local: `Quiet so far this morning`
  - Not seen yet, after noon: `Quiet so far today` (still the darkest copy in the app)
- Subline, dual timezone: `Last routine seen 8:36 pm her time · 11:06 am yours` (viewer tz from the browser; "her/his" only if a recorded pronoun exists — item 24/34 policy — else "their time" / "{Name}'s time").
- Copy-law test extends: no digits beyond clock times (now up to two), no counts, no signal/app names, no urgency vocabulary, and NO numeric representation of activity anywhere (assert no rendered element encodes a ping count).

## 2. The day arc (activity shape without numbers)

- Per parent card: three segments — Morning / Afternoon / Evening (parent-local: 05–12, 12–17, 17–21).
- A segment glows warm once ≥1 alarm-grade ping occurred in it (binary; derived client-side from the pings the RLS view already returns — no new API surface).
- Segments in the future are neutral/empty (not dark); a past segment with no routine renders soft/dim, never red, never labeled. No tooltips with counts or times. Current day only — no history view, no comparisons.
- Guardrail test: the arc's DOM carries no numbers and no more than three binary states.

## 3. The liveness beacon (honest breathing, not decoration)

- Small glow dot per parent, labeled `phone` (it is phone status, never person status — attribution law).
- States driven by real mechanism recency (device_alive/charge events from the same RLS reads): breathing animation when last mechanism OR alarm-grade signal ≤ ~26h old (covers the daily timer cadence with slack); still + gray when older (stillness, not alarm — no red, no copy change); hidden entirely if the parent has no device_alive/charger signals configured (never fake it).
- The animation must map to data state, not run unconditionally — test: with stale fixtures the beacon class is the still variant.

## 4. Non-goals

History/trends of any kind. Per-signal display. Counts anywhere. Configurable thresholds in UI. Any red state. Changes to Digests/Family screens beyond the dual-tz subline reuse if trivial.

## 5. Acceptance criteria

1. Copy renders per §1 matrix across the four state/day-part combinations (component tests with clock injection), dual-tz subline correct for a Chicago viewer of an IST parent.
2. Day arc: fixtures with morning+afternoon pings glow two segments, future segment neutral; zero numbers in arc DOM.
3. Beacon: fresh mechanism signal → breathing; stale → still gray; unconfigured → absent.
4. Extended copy-law test green (incl. the no-numeric-activity assertion); existing floor test still holds (`Quiet so far…` remains the darkest state, no red in the palette).
5. Webapp suite + build + verify green; backend untouched except test additions if the contract test needs the new copy templates mirrored.
