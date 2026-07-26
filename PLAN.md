# PLAN.md — Project Kettle

*Maintained by Fable 5 (PM). Updated: Fri Jul 24, 2026.*

## Working model

Fable 5 (Cowork) = PM/reviewer. Claude Code (Opus 5, cloud container) = implementer. Hema pulls after each big build → Fable reviews the diff here → feedback goes into the spec or `specs/QUESTIONS.md`.

## Critical path to Sunday (YC deadline: Sun Jul 27, 8:00pm PT)

| When | What | Owner |
|---|---|---|
| Fri (today) | Spec 001 handed to Claude Code; first build + tests | Claude Code |
| Fri night / Sat am | `git pull` → code review of build 1 | Fable |
| Sat | ~~Deploy to Fly.io~~ ✅ DONE Jul 25 — live at kettle-pilot.fly.dev, /healthz green, 403 verified | Hema |
| Sat/Sun | Instrument both parents' phones (Shortcuts ×3 each + Health sharing); consent conversations incl. Dad's one-pager redline | Hema (+ sister on FaceTime) |
| Sat | Draft consent one-pager for Dad | Fable (next up) |
| Sun am | Verify pings flowing from Chennai; heartbeat armed → "pilot live" is TRUE | Hema |
| Sun | YC app: fill brackets (name, batch history, entity, cofounder answer), pick one-liner, record video (one take, phone, good light) | Hema, Fable assists |
| Sun by ~5pm PT | Submit (buffer before 8pm) | Hema |

## Next up after Sunday

1. Phase 1 silent baseline runs Days 1–14 (no action needed beyond label discipline + heartbeat watch).
2. Spec 002 — Phase-1 analysis: gap distributions, per-daypart percentiles, threshold selection (~Aug 7).
3. Spec 003 — Phase-2 shadow alerting rules (founder-only), digest generator (~Aug 8).
4. Emoha/Samarth/Yodda outreach — one conversation booked (parallel, any time).
5. Android MVP scoping doc — only after G1–G4 gates read out (~Aug 24).
6. Day-30: re-rank `docs/signal-expansion-ideas.md` §3 against real data (its rankings have no rights until then); run the two question sets it moved outside the pilot window (F2 household facts, F3 framing debrief); bench-test C2 alarm auto-silence any time (zero pilot contact).
7. Day-30 findings memo discipline (accepted from adversarial review): G1/G4 are near-unfalsifiable in this cohort — scope claims as "anxiety relief plus faster discovery; clinical outcome delta unquantified." G3 threshold math + G5 contact delta are the real yield.

## Signal review outcomes (Jul 26)

- `docs/signal-expansion-ideas.md` reviewed against product law: clean, adopted as post-pilot backlog. Its kill list is binding (nothing gets re-derived).
- Product law #6 added to CLAUDE.md (household events never prove a person is fine).
- Steps (A10): killed from all product plans by the review; then fully dropped from the pilot too by founder decision later the same night (see "Steps: fully dropped" above). One-pager now contains no Steps row.

## Decisions log

| Date | Decision |
|---|---|
| Jul 24 | Hosting: Fly.io (persistent volume, boring, survives the pilot). Founder alerts: ntfy.sh. |
| Jul 24 | Server-side UTC timestamps only; IST display. Token-gated writes. |
| Jul 24 | Label blinding enforced in software (interstitial before /status). |
| Jul 24 | Roles: Fable = PM/review, Claude Code = build, cloud container + git pull cadence. |

## Steps: fully dropped (founder decision, Jul 26, supersedes earlier "pilot keeps steps" ruling)

Founder ruled: if the product can't use steps, the pilot doesn't collect them. Removed from pilot protocol §3/§4.2, consent one-pager (now uniformly who/signal/when — its strongest form), and YC draft. Chennai setup simplifies (no Health-app step). Phase-2 quiet-day classification: blinded label log + charger events + normal contact. Digest lines: shippable signals only.

## Founder correction (Jul 26, logged for the platform decision)

The "Indian seniors are overwhelmingly Android" fact is population-wide; the NRI beachhead selects for iPhone parents (hand-me-downs, gifts, FaceTime with grandkids). Implications: (a) iOS tier = productized Shortcuts + charging pings + heartbeat, planned earlier than "someday" — the current pilot is its de-facto prototype; (b) Android-native vs dual-track decision waits for data: add "what phone does your parent use?" to any waitlist/next-pilot signup; (c) platform note in project-brief should not be read as iOS-negligible for the beachhead.

## Open items needing Hema's answer (for the YC app, not the code)

- Working name (even placeholder) — needed for app + video.
- Cofounder answer: Option A (open to one) vs Option B (deliberately solo).
- Prior YC application batch + RosterPro entity/cap-table facts.
