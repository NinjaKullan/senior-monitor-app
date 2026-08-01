# Spec 005d — Tripwire health panel (card detail view)

*PM: Fable, from founder direction Aug 1. Tapping a parent's card opens a detail view showing that parent's configured tripwires and their health. This is a MAINTENANCE surface — equipment status for the repair flow — not an activity feed. That distinction drives every rule below.*

## 1. What it shows

Tap parent card → detail view (route or sheet, implementer's choice):

- Header: parent name + the same warm headline/beacon as the card (consistency, no new states).
- **Tripwires list** — one row per active `parent_signals` entry, from the existing RLS reads:
  - Signal display name (humanized: `WhatsApp`, `YouTube`, `News`, `Charger`, `Daily check`). This is the ONE surface where signal names may render — they're necessary for repair ("her WhatsApp tripwire needs attention"). The copy-law tests get a scoped exemption for this view only.
  - Health chip: `Connected` (heard within its expected cadence) / `Not heard in a while` (beyond cadence; soft amber, not red — equipment tone, not alarm). Expected cadence v1: `device_alive` ≈ daily+slack (26h); everything else uses a generous 7-day window (a news app she rarely opens is not a broken tripwire; QUESTIONS note welcome on tuning).
  - Recency at DAY granularity only: `today` / `yesterday` / `3 days ago` / `never`. **Never clock time.** Rationale (record in code comment): precise timestamps on a per-app list are ammunition ("why were you up at 2am?"); the repair question is answered by day-level recency. The existing card subline keeps its clock time — that's a single coarse "last routine" fact, not a per-app ledger.
- Footer: the repair nudge, only when something is `Not heard in a while`: `A tripwire may need a quick fix on {Name}'s phone. It's a two-minute FaceTime.` (No instructions in-app yet — 005b's wizard owns the guided repair.)

## 2. Guardrails

- No counts, no per-day history, no times finer than day granularity, no charts. The no-numeric-activity assertion extends here (day-words are words, not numbers; `3 days ago` digits exempt like clock times are elsewhere).
- Amber is the darkest color on this surface; it refers only to equipment, and the copy never implies anything about the person (attribution law — a dead tripwire is a Shortcuts problem until proven otherwise).
- This view widens `queries.ts` deliberately (parent_signals + per-signal last ping) — the item-48 read-surface test updates consciously with it. Ladder/ops tables remain absent.

## 3. Acceptance criteria

1. Tap card → detail renders all active signals for that parent, none for others (RLS through the UI as usual).
2. Health logic: device_alive stale beyond 26h reads `Not heard in a while`; an app signal at 3 days reads `Connected` (within 7-day window) with `3 days ago` recency; `never` renders for a signal with no pings.
3. No clock times anywhere in the view (test walks DOM: the only digits allowed are day counts); no counts; amber max.
4. Repair nudge appears only when ≥1 tripwire is stale, with the exact copy above.
5. Copy-law scoped exemption implemented as an explicit allowlist for this view, not a weakening of the global test (the digest/glance surfaces must still fail on signal names).
6. Webapp suite/lint/build/secret-scan green; read-surface test updated deliberately; backend untouched.
