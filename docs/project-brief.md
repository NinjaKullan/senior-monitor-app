# Project Brief — "Project Kettle" (working title)

**Passive peace-of-mind monitoring for families caring for aging parents across distance.**

*Prepared July 2026. Founder: Hema (Apex, NC). Status: pre-MVP, 30-day family pilot launching, YC Fall 2026 application in progress (deadline July 27, 2026, 8pm PT).*

---

## 1. The problem

An estimated 53 million Americans are unpaid family caregivers for aging relatives (AARP/NAC 2020). For adult children who live far from their parents — and especially for diaspora families separated by oceans and timezones — the dominant daily experience is not caregiving tasks but **chronic low-grade uncertainty**: *is Mom okay today?*

The founder's own experience is the archetype: left India 26 years ago, parents in their 70s in Chennai, a sister in Texas sharing the load. Timezones make calls inconvenient; work and kids crowd them out; check-in frequency decays from daily to every 3–7 days — not from lack of love, but because you start taking your parents' continued presence for granted. Most sons, the founder believes, are exactly like him. Decline or crisis is typically discovered late, at the point of a fall, a hospitalization, or a frightening unanswered phone.

Current options all fail a proud, independent 70-something:

- **Check-in calls** — decay over time, and seniors mask problems during short conversations.
- **Medical-alert pendants (Life Alert etc.)** — stigmatizing, high non-wear rates, reactive-only.
- **In-home sensors/cameras (CarePredict etc.)** — $499 hardware + ~$70/mo, home-bound, and feel like surveillance.
- **Family location apps (Life360, Snug)** — US-centric, no escalation model, location-tracking feels invasive.
- **Voice check-in robots** — a healthy senior experiences a mandatory daily robot check-in as "roll call in jail" (founder's words, and he's right).

## 2. The core insight: negative-space monitoring

**Seniors reject being watched, but accept a tripwire they own.** The proven precedent is Japan: Zojirushi's i-Pot kettle has been emailing families "mom made tea this morning" since 2001, and Japan Post runs watch-over visit services. Japanese elders accepted these because nothing about the *content* of their life is observed — the system only notices when an **expected routine fails to happen** (kettle not used, door not opened), and then a human checks in.

**The senior's smartphone is already the kettle.** No new hardware, no camera, no wearable, no daily robot conversation. The founder's parents, like most Indian seniors, have ironclad daily phone routines: WhatsApp, YouTube, news sites — all morning-clustered, all detectable as simple app-open events, all content-free.

The product never asks "what is she doing?" It only asks "did the normal thing happen?" — and it asks **her first** when it didn't.

## 3. Product concept

### Senior side (the tripwire they own)
- One-time consented setup on the senior's existing phone.
- Passive signals, all binary/coarse: app-open events for 2–3 personally chosen routine apps, phone charging/activity state, first-unlock-of-day (Android). **No content, no location trail, no keystrokes, no audio, no health/body data** (steps ruled out Jul 26 — body data, decline-inference-shaped, and platform-unscalable).
- A personal baseline is learned (distribution of gaps between phone touches). Alerts fire only on statistical outlier gaps *for that person*.
- **Senior-first confirmation:** when a routine breaks, the phone quietly asks the senior — "All good? Tap yes" — with a generous grace period. Nothing leaves the phone unless they stay silent.
- Framing to the senior: *"This stops your kids from pestering you. You'll never get a worried 6am call unless something is actually wrong."* It's a dead-man's switch they configure, not a camera pointed at them.

### Family side (the buyer)
- **Escalation ladder**, configured per family: routine breaks → senior's phone asks them first → grace period → ping primary child → ping sibling/secondary → local on-the-ground responder.
- **Positive daily/weekly digest**, not anxiety alerts: "Mom was active this morning, 2,100 steps." Sells *reassurance daily* rather than *fear occasionally* — much better retention model.
- **Connection prompts**, not connection replacement: the digest gives you reasons to call ("Mom walked to the temple this morning"). The product scaffolds staying close; it must never read as outsourcing love to an app.

### The end-of-ladder human (the hard part and the moat)
Japan's model works because a postman eventually shows up. Software alone cannot close the loop from another continent. Even the founder — motivated, with family — has no one in Chennai to send. **This is not an edge case; it is the hardest onboarding step for every diaspora customer, and probably the business model.** India has an emerging paid eldercare-response industry (Emoha, Samarth, Yodda) selling exactly this terminal rung. Partnership/referral integration with such services — rather than building operations — is the likely path, and over time the network of local responders + labeled alert-resolution data is the defensible asset.

## 4. What this product is NOT (hard constraints from diligence)

Three independent AI diligence reports (Claude, ChatGPT, Gemini — see `research-synthesis.md`) unanimously killed the original concept of passive cognitive/physical **decline detection** from phone signals. Constraints adopted as product law:

1. **No decline/dementia/diagnostic claims, ever.** Consumer apps making cognitive-decline claims cross into FDA SaMD territory and are scientifically unsupported (Biogen/Apple's 23,000-person Intuition study could not validate passive detection; Mindstrong burned $160M on this thesis and died).
2. **No keystroke dynamics, no background keylogging, no message/call content, no continuous location.** Blocked by iOS/Android policy, and it's spyware-adjacent regardless.
3. **No subtle-anomaly ML alerts.** Base-rate math guarantees mostly false positives; false alarms destroy family trust and retention. Coarse functional events only.
4. **Positioning: family coordination and wellness. General-wellness lane. FTC Health Breach Notification Rule still applies — privacy engineering is a day-one requirement, not an afterthought.**
5. **No mandatory daily voice check-ins for healthy seniors** (founder's own veto: "roll call in jail"). Voice check-ins remain an option for the seriously-ill/very-senior segment later.

## 5. Beachhead and expansion

**Beachhead: NRI (Non-Resident Indian) corridor.** US Indian diaspora ~5M, affluent, USD incomes, acute timezone pain, cultural obligation to parents, thin competition (US products don't serve India; Indian services don't serve the US payer). Founder is customer zero with native cultural insight.

Platform note: the broader Indian 70+ market is overwhelmingly **Android**, where the required passive signals (usage stats, screen-on, charging) are properly supported with explicit consent. iOS is more restricted (the founder's own parents have iPhones — pilot runs on iOS via the Shortcuts workaround; see `pilot-protocol.md`). Product build order: Android-first for market, iOS via reduced signal set (productized Shortcuts + charging events; no health data).

**Expansion:** every diaspora has the same ache — Filipino, Chinese, Mexican, Vietnamese corridors — then domestic US long-distance families (the sister-in-Texas configuration), then B2B2C (employer caregiver benefits, per Gemini's suggestion) once evidence exists.

## 6. Business model

- **Payer: the adult child**, never the senior. Family subscription.
- **Price: $20–30/month** initially (all three diligence reports converged on a $25–50 ceiling for software-only; $40+ requires a human-response component).
- **Upsell: local responder integration** (partner services in India) at a premium tier — this is where the $40–70 tier becomes justified.
- Medicare RPM/RTM reimbursement is **not available** for this data class (verified in diligence); do not build the model around it.
- Known churn risks: worry subsides, senior transitions to assisted living, or passes away. The digest-as-daily-reassurance and multi-sibling accounts are the retention counters.

## 7. Competition

| Category | Players | Why we're different |
|---|---|---|
| Family safety apps | Life360, Snug | US-centric, location-centric, no senior-first escalation, no cross-border design |
| Hardware monitoring | CarePredict, envoyatHome, Sensi.AI | $500+ hardware, home-bound, surveillance feel, US-only |
| Medical alerts | Life Alert, Medical Guardian, Lively | Stigma, reactive-only, pendant non-compliance |
| Platform natives | Apple Health Sharing / Walking Steadiness, Google | Real threat on signals; but no escalation ladder, no digest, no local responder, no cross-border product |
| India eldercare ops | Emoha, Samarth, Yodda | Partners, not competitors — they are the terminal rung |
| Phone-only monitoring | GaitIQ | Proof the space is being attacked; they chase gait/cognition (the discredited path) |

**Moat thesis:** the moat is not the algorithm (trivial) — it's (a) the two-sided trust design that seniors actually accept, (b) the cross-border responder network, and (c) the labeled dataset of alerts → causes → resolutions that accumulates from the closed loop.

## 8. Founder fit

- 26 years abroad, 70+ parents in Chennai, sister in Texas — lived the exact problem; customer zero.
- Solo technical founder who ships: RosterPro (getrosterpro.com) — polished iOS + web youth-sports coordination app, built end-to-end solo, live in the App Store. The magic-link onboarding instinct there is exactly what this product's senior onboarding needs.
- Python/AI-strong; the pilot backend is a weekend of work in his stack.
- Two ideal test users: a compliant mother (tests engagement) and a privacy-minded attorney father (tests consent design — if the design passes him, it passes the hardest segment of the market).

## 9. Key risks

1. **Apple/Google bundle the core signals** natively (Apple Health Sharing already exists). Counter: the product is the escalation ladder + cross-border responder + family UX, not the signal.
2. **False-positive fatigue** despite the ladder. Counter: personal-baseline thresholds tuned in pilot; senior-first confirmation absorbs most; measure "unnecessary family escalations/month" as a core metric with a hard gate.
3. **Senior rejection / perceived surveillance.** Counter: negative-space design, senior-owned configuration, dad-test the consent flow. If the founder's father won't keep it installed, redesign until he will.
4. **Responder rung doesn't exist** for many families. Counter: partnership strategy; treat "configure your responder" as a first-class onboarding flow with suggestions (neighbor, watchman, family doctor, paid service).
5. **YC RFS-driven competition** ("AI for the Aging Population," Fall 2026 RFS). Counter: speed, corridor focus that batchmates will ignore, and evidence from a real pilot.
6. **Churn economics of peace-of-mind subscriptions** (see Alexa Together's death). Counter: daily-reassurance digest, multi-sibling billing, responder-tier lock-in.

## 10. Open questions

- Working name and brand. ("Kettle" is an homage candidate; needs a check for trademark and cultural resonance in both markets.)
- Android MVP scope and whether a senior-side app is even needed on Android vs. a thin agent.
- WhatsApp ecosystem: family digest delivered *in* WhatsApp (where NRI families already live) vs. a standalone app. Note: never scrape WhatsApp "last seen" — ToS violation; detect device-level activity instead.
- Responder partnerships: Emoha vs. Samarth vs. Yodda terms; per-incident vs. subscription pricing.
- Solo founder vs. recruit cofounder — decide before YC interview; do not wing this answer.
- Consent-degradation policy: what happens when a senior's capacity to consent declines (flagged by ChatGPT report; needs a written policy even in pilot).

## 11. Immediate next steps

1. Launch 30-day family pilot (see `pilot-protocol.md`) — target start before July 27.
2. Submit YC Fall 2026 application by July 27, 8pm PT (see `yc-application-draft.md`).
3. Land one conversation with an India eldercare-response service (Emoha/Samarth/Yodda) to validate the terminal-rung partnership.
4. After pilot: threshold model + false-positive rate → decide build/no-build on Android MVP.
