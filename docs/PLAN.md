# Kettle — working plan

*PM: Fable, 2026-08-15. One page. If this file and reality disagree, fix this file in the same
commit that changes reality. QUESTIONS.md holds the findings; this holds the order.*

## Where we are

Amma is live in production (whatsapp, youtube, charge_on — per-app method, leave untouched).
Appa is provisioned and signed but not delivered; he will be the first merged-method install.
Experiment §5.2 (one automation, many apps) is confirmed on-device — QUESTIONS 107. Experiment
§5.1 (HTTPS-served signed .shortcut → Add Shortcut sheet) is the last unknown gating 005b.

## Now — founder, tomorrow

1. Live-fire the merged automation on your own phone with a **Rehearsal** shortcut: open each of
   the 3 apps, watch the TestDad/TestMom card. Proves the last unproven link.
2. Pull Claude Code's work; review; then re-forge Appa with the merged set (`routine`,
   `charger`), sign, deliver over WhatsApp.
3. Appa's call: consent → delete old automations → 2 files → 2 unlocked first runs → 2
   automations (**Run Immediately, including the charger one**) → verify by prediction.
   Pre-checks: Shortcuts installed; sister's camera booked from the start.
4. Run the §5.1 test URL when Claude Code ships it. Result goes in QUESTIONS; it closes the
   fork in spec 005b.
5. After Amma + Appa verified 48h: delete `~/Projects/kettle-files/suryaprakasam` entirely.

## Now — Claude Code (handoff message sent 2026-08-15)

1. `routine` + `charger` vocabulary keys (label maps, drift test, consent copy).
2. Forge emits the merged two-shortcut set from parent_signals.
3. §5.1 harness: one signed Rehearsal shortcut served over HTTPS, unguessable path.
Then, unchanged queue: QUESTIONS 93, 95, 100, 101.

## Next — PM

- Spec 005b drafted (`specs/005b-family-onboarding.md`) with the §5.1 fork marked; close the
  fork when the experiment answers, then hand to Claude Code.
- Review Claude Code diffs on the git-pull cadence.

## Founder debts outside this track (unchanged)

Migration 0009 + `WAITLIST_ORIGINS` on kettle-api; Amendment B site redeploy; NC annual
reports (LinkAbit); WhatsApp display name (parked with naming).

## Later / backlog (filed, not scheduled)

- Q108 timezone edit for travelling parents (Amma-in-Texas is the live case)
- Q109 savviness branch (merged default, per-app opt-in)
- Q107 native parent-side app as device_alive home (iOS background caveat recorded)
- Routine discovery (parked); Android wave (Q100 platform-aware set)

## Standing rules that keep biting

- Signed shortcuts never enter the founder's Shortcuts library; test only with Rehearsal tokens.
- Signed files are credentials; delete family folders after verification.
- Charger and App automations must be **Run Immediately** — Run After Confirmation is a dead
  automation on a parent's phone.
- Field notes go to QUESTIONS as numbered items the same day; next free number lives in CLAUDE.md.
