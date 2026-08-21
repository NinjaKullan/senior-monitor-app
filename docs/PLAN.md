# Kettle — working plan

*PM: Fable, updated 2026-08-19 (prior: 08-15). One page. If this file and reality disagree,
fix this file in the same commit that changes reality. DECISIONS.md holds the findings; this
holds the order.*

## Where we are

Both parents live in production: Amma (per-app: whatsapp, youtube, charge_on) and Appa (first
merged-method install: routine + charger), verified by prediction on the live setup page.
Spec 005b shipped end to end (setup links, parent page, WhatsApp file delivery). The landing
site is done and deployed: illustration set (one style, six images), one-voice typography
(five sizes, one family), Rhythm Field in both placements with the stir, floating CTA,
privacy policy live, founder note live, waitlist proven end to end (form → API → DB, dedup +
coalesce verified). Onboarding investment is PAUSED by founder ruling — beta families get
manual handholding. Consent ceremony is dead permanently; consent language lives in ToU at
payment. English-only surfaces; what-never-how on all public copy, enforced by test.

## The gap that now leads everything

**The site promises what the backend does not yet send.** "You hear twice a day" and "asks
her first, quietly" require an outbound channel; today signals are collected and nothing
speaks. No beta family can be onboarded honestly until the ladder's first two rungs are real.

## Now — product (Claude Code), in order

1. **The outbound channel + digests.** WhatsApp sender (Twilio number + display name are the
   founder debts gating this) or interim founder-phone relay; then the twice-daily digest and
   the quiet-morning ask, vocabulary-lawful, per the ladder (parent first, others only on
   silence). This is the beta blocker.
2. **Email deliverability (Q115).** Custom SMTP per docs/auth-smtp-plan.md; the built-in
   mailer's ~2/hr cap breaks magic-link logins the day two beta families sign up in the same
   hour.
3. **Hygiene pass, small:** `--revoke`/`--setup-link` leading-dash parse fix (until then the
   `=` form is the documented invocation); `dist/` cleaned at build start (stale-dist false
   green); Q122 webapp "Send on WhatsApp" exemption; runbook §7 rewrite (Q125).
4. Unchanged queue: Q93, 95, 100, 101.

## Now — founder

1. Domain + hosting cutover (separate agent session); site currently at kettle-site.fly.dev.
2. Twilio number + WhatsApp display name — unblocks product item 1.
3. Beta recruiting (separate marketing session) once the outbound channel exists.
4. First stranger-family install, founder hands off after provisioning (005b AC1) — produces
   the field-note DECISIONS block that tunes the manual-handhold script.

## Next — PM

- Review cadence on every Claude Code pass, live-verify after every deploy (unchanged).
- Day-30 pilot memo when the first stranger family crosses 30 days.
- Mark docs/hero-diptych-brief.md superseded (illustration set replaced the photo diptych).

## Later / backlog (filed, not scheduled)

- Payment path: ToU (carries consent language), counsel review of privacy policy, legal
  entity name, founding price $10/parent/month — all before any charge, none before beta.
- Q108 timezone edit (Amma-in-Texas is the live case); Q109 savviness branch; Q107 native
  parent app as device_alive home; Android wave (waitlist parent_phone data decides priority);
  routine discovery (parked).

## Standing rules that keep biting

- Signed shortcuts never enter the founder's library; test only with Rehearsal tokens.
- Signed files are credentials; delete family folders after verification.
- Automations are Run Immediately, always.
- Field notes go to DECISIONS as numbered items the same day; next free number in CLAUDE.md.
- Web assets committed over the bridge get chmod 644 before any build.
- After every deploy: PM live look before the next thing starts.
