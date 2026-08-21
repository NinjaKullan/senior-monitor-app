> **SUPERSEDED by spec 007** (DECISIONS 141). The ladder module, its copy, its CLI
> and the `/twilio/inbound` webhook are retired and deleted; migration 0013 drops
> its tables where they never held a row and archives them where they did. Spec
> 007's ask and follow-on are the first two rungs, rebuilt.
>
> Read on for the reasoning, which 007 inherits rather than replaces: the senior is
> asked first, household signals decide only whether the phone can be asked and
> never whether a person is fine, and privilege escalates by explicit founder
> action. DECISIONS 141 lists what this engine had that 007 does not yet — the
> unreachable-handset distinction, the all-clear, the max-gap trigger, the
> per-family shadow/live gate — so none of it was discarded quietly.

# Spec 004 — Escalation ladder v1 (senior-first, shadow-by-default)

*PM: Fable. Builds on 002/003. This is the alert path — the highest-stakes feature in the product. Everything here defaults to the safest mode and escalates privilege only by explicit per-family founder action.*

## 0. Product-law note

This spec authorizes, for the first time: (a) messages to the SENIOR (the "all good?" ask), and (b) absence-triggered messages to the family — but ONLY in `live` mode, per family, explicitly enabled. The default for every family is `shadow`: the full ladder runs and records, and its outputs go exclusively to founder ops. Law #6 stands: only person-attributed signals feed the ladder. The digest (003) and the ladder never blend: a digest never mentions absence; a ladder message never pretends to be a digest.

## 1. Modes (per family)

`families.ladder_mode text not null default 'off'` — `off` | `shadow` | `live` (migration 0007).
- `off`: nothing evaluated.
- `shadow`: stages evaluated + recorded + founder ntfy at each stage transition. No senior contact, no family contact. This is the beta default once enabled.
- `live`: real sends. Requires `digest_enabled = true` as a precondition (a family should meet Kettle as reassurance before it can meet it as alarm).
Global env `LADDER_ENABLED` kill-switch over everything (default off in `.env.example`).

## 2. The trigger (candidate alarm)

Per parent, evaluated each pass in the parent's effective tz, daytime only (05:00–21:00 local):
- **Rule v1 (fixed, conservative):** no alarm-grade ping since 05:00 local AND local time ≥ a per-parent `alarm_deadline` (default 12:00), OR current gap since last alarm-grade ping exceeds per-parent `max_gap_minutes` (default 480) within the daytime window.
- Config columns on `parents` (migration 0007): `alarm_deadline time default '12:00'`, `max_gap_minutes int default 480`. Defaults deliberately conservative; the pilot's Phase-1 percentile analysis (separate upcoming spec) will produce fitted per-person values — design the columns so that analysis just updates them.
- One candidate per parent per local day (a resolved candidate does not re-arm the same day in v1).
- `device_alive`/charger discrimination: if timer/charger pings ARE flowing while alarm-grade is silent, the candidate still fires but carries `mechanism_ok=true`; if NOTHING is flowing, `mechanism_ok=false` and in live mode the ladder pauses at the ask stage (you cannot ask a dead phone) and goes straight to founder ops + (live mode) a family message that is honest about what is known: see §4 copy.

## 3. The stages

State machine per candidate, all transitions recorded in `ladder_events` (0007: candidate_id, parent_id, family_id, stage, mode, detail, ts_utc; service-only, RLS select for family members like digest_sends):

1. **ASK** — message to the SENIOR's phone (SMS now, WhatsApp when live; reuse 003's channel abstraction; senior phone = new column `parents.phone_e164`, nullable — no phone, skip to stage 3 with `ask_skipped`): copy §4. Grace period `grace_minutes` default 90 (column).
2. **REPLY handling** — inbound Twilio webhook (`POST /twilio/inbound`, signature-validated). ANY reply from the senior's number within grace resolves the candidate (`resolved_by_senior`). In live mode, family gets NO message (silence was never broken for them); founder ops row records it. Store only: from-number match, timestamp, and the fact of a reply — NEVER the message body (product law: no content; log body length zero, discard).
3. **FAMILY-1** — grace expired: message the family circle in escalation order (member order v1 = owner first, then members by created order; explicit ordering UI is 005). Copy §4.
4. **FAMILY-ALL** — +`family_gap_minutes` (default 60): remaining members.
5. **RESPONDER-INFO** — v1 does NOT auto-contact any third party. If the family has a named local contact (new table `family_contacts`: name, phone, relation, family_id — populated later by 005; nullable now), the FAMILY-ALL message includes their name/number as a suggestion. No call, no SMS to the contact themselves in v1.
6. **RESOLVE** — any alarm-grade ping from the parent at any stage resolves the candidate (`resolved_by_activity`); in live mode, if family was already notified, they get ONE closing message (§4 all-clear). Founder can resolve manually via CLI (`scripts/ladder.py --resolve <candidate>` with note).

## 4. Copy (binding, same law as 003 — calm, no counts, no speculation, no medical language)

- ASK (to senior): `This is Kettle. {Name}, your phone has been quiet today. All good? Reply YES.` (WhatsApp button variant when live.)
- FAMILY (mechanism_ok=true): `Kettle: {Parent}'s usual routine hasn't been seen today, and they haven't answered a gentle check-in. A call from you may be all this needs. {contact-line if any}` *(neutral clause is the default per items 24/34 — she/he variants only via an explicitly recorded pronoun field; the template takes a whole clause for verb agreement)*
- FAMILY (mechanism_ok=false): `Kettle: {Parent}'s phone has been unreachable today (no signals of any kind). This is often a phone or network issue. A call from you is the fastest way to know. {contact-line}`
- ALL-CLEAR: `Kettle: {Parent}'s routine has resumed. All normal.`
- Copy-law test: extend 003's — no digits (no times needed here), no signal names, no "emergency/urgent/worried/alarm" vocabulary anywhere in ladder copy.

## 5. Shadow-mode mechanics (the beta workhorse)

In `shadow`, every stage transition sends founder ntfy: `[SHADOW {family}] {parent}: stage {X} would have fired — {detail}`. The founder manually decides whether to act (call the family himself during beta). Every shadow candidate + its eventual resolution is the labeled data that tunes thresholds — this is the pilot's Phase-2 ledger, productized.

## 6. Non-goals

Percentile-fitted thresholds (upcoming pilot-analysis spec feeds the columns). Responder auto-contact / paid partners. Family-configurable ordering and grace (005 UI; columns exist, CLI can set). Voice calls. Household/multi-parent corroboration logic (law #6 keeps household signals out of the ladder entirely). Re-arming after resolve same-day. iOS/Android senior app ask (channel abstraction covers it later).

## 7. Acceptance criteria

1. Candidate fires per rule v1 (both branches: deadline and max-gap) with injectable clock; none outside daytime window; one per parent per day.
2. Senior reply within grace resolves; family never contacted; no message body stored anywhere (assert the webhook handler drops it; test posts a body and proves no table/log contains it).
3. Grace expiry walks FAMILY-1 → FAMILY-ALL in order with correct gaps; activity at any stage resolves + (live) sends one all-clear; no further sends after resolve.
4. Mode gates: `off` evaluates nothing; `shadow` sends founder-only ntfy at each transition and NEVER touches Twilio family/senior sends (assert zero channel calls); `live` requires `digest_enabled` (constraint or check at flip time via CLI `scripts/ladder.py --set-mode`).
5. mechanism_ok discrimination: device_alive flowing + apps silent → ask proceeds; nothing flowing → ask skipped, family copy is the unreachable variant (live), founder alerted (shadow).
6. Twilio inbound webhook validates signature; unsigned/mismatched → 403, nothing recorded.
7. Copy law test extended per §4. 8. RLS on new tables mirrors digest_sends; advisor-clean after 0007. 9. All suites green, ruff clean, pilot untouched, no secrets.
