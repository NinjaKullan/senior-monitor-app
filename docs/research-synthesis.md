# Research Synthesis — Three-Model AI Diligence

*July 2026. This document records the structured go/no-go diligence run on the original product concept, the unanimous verdict, and how it reshaped the product. It doubles as the "what we learned" evidence for the YC application.*

---

## 1. Method

A single neutral evaluation prompt was written to avoid biasing the models: the concept described flatly (not as "my idea"), Y Combinator's Fall 2026 "AI for the Aging Population" RFS included as *context to analyze, not validation*, steelman-both-sides required, verdict required **before** constructive ideation (Part 3) to prevent contamination. The identical prompt was run in fresh conversations on three models:

- **Claude Fable 5** (Anthropic)
- **ChatGPT** (OpenAI)
- **Gemini** (Google)

**Concept evaluated (original):** passive smartphone behavioral monitoring (typing patterns, response latency, screen activity, steps, possibly voice) of adults 70+ to establish personal baselines, detect gradual physical/cognitive decline, and alert family with consent. Optional senior-facing wellness prompts. 1–2 person Python-strong team.

## 2. Verdicts

| | Claude Fable 5 | ChatGPT | Gemini |
|---|---|---|---|
| Verdict | Do not pursue as specified; reposition | Do not pursue as stated; reposition | "Pursue with major changes" (functionally identical pivot) |
| Confidence | Medium-high | High | High |
| Riskiest assumption (all three named the same one) | Passive phone signals cannot support actionable decline alerts at a tolerable false-positive rate | Same | Same (adds: OS platforms will not permit the required collection) |

**Reading:** the label differences are packaging. All three rejected the same core (passive decline inference) for the same reasons and prescribed materially the same pivot.

## 3. Unanimous findings (treat as settled)

1. **The science isn't there for passive decline detection.** The definitive study — Biogen/Apple "Intuition," 23,004 US adults, published Nature Medicine March 2025 (Butler et al., s41591-024-03475-9) — built an MCI classifier from **active** cognitive tests + self-report; the authors explicitly deferred passive detection to future work. PPV ~55%. *Independently verified via Nature Medicine and Alzforum.*
2. **Mindstrong is the cautionary precedent:** $160M raised on the smartphone-behavioral-biomarker thesis, shut down March 2023 without published validation.
3. **Platform walls:** iOS sandboxes keyboard extensions (Full Access warning, no background execution, memory caps, password-field exclusion); Screen Time APIs need special entitlements; Android bans call/SMS log access for non-default handlers; Google Play treats adult-to-adult monitoring as high-risk. Continuous background collection is not commercially shippable.
4. **Base-rate math is brutal:** incident actionable decline is rare in any monitoring window, so even 85/85 sensitivity/specificity yields mostly false alarms (ChatGPT's illustration: ~5% PPV at 1% event rate). False positives → alarm fatigue → muted notifications → dead product. False negatives → false reassurance → liability.
5. **Buyer ≠ user:** the adult child pays; the senior must tolerate. Buyer/user incentives conflict (visibility vs. autonomy/dignity).
6. **Willingness to pay:** real but capped — ~$10–30/mo software-only; $40–70/mo requires hardware, humans, or clinical involvement. ~20% of caregivers will pay nothing. Medicare RPM/RTM reimbursement is structurally unavailable for behavioral phone data.
7. **Regulatory lane:** diagnostic claims ("detects cognitive decline") → FDA SaMD. Stay in general wellness. HIPAA largely doesn't apply DTC, but the **FTC Health Breach Notification Rule does** (ChatGPT's catch).
8. **Prescribed pivot (all three):** active, senior-liked engagement + coarse functional events only (missed routine, sustained immobility, phone dead) + caregiver coordination + a cheap Wizard-of-Oz family pilot **before writing real code**.
9. **Amazon's Alexa Together** (elder-care subscription) was discontinued May 2025, replaced by the cheaper, narrower Emergency Assist — a churn/demand warning for peace-of-mind subscriptions. *Verified.* (Caveat: may reflect Amazon's Alexa-wide cost cutting as much as category demand.)

## 4. Unique contributions worth keeping

**Claude Fable 5:** the NRI/India-corridor beachhead (knew founder context); pair software with an on-the-ground human (the Samarth/Yodda lesson: technology alone fails in India eldercare; the winning model pairs monitoring with a trusted local person); the "explainable trend digest, never diagnosis" long-term option.

**ChatGPT:** senior-first confirmation UX (ask the senior "are you okay?" before notifying family — now a core product mechanic); functional events, not diagnoses; closed-loop alert→cause→resolution labeling as the eventual data moat; high-risk episode focus (post-discharge 30–90 days) as an alternative B2B wedge; GaitIQ identified as a direct phone-only competitor; FTC HBNR; the most rigorous pilot design (blinded day-labels, predeclared gates); repositioning option: "caregiver concierge that completes work rather than inferring disease."

**Gemini:** sharpest articulation of why structured voice has better signal-to-noise than background typing; the **positive daily digest** ("Mom checked in, good energy, 2,100 steps") replacing scary anomaly alerts — reassurance-daily as the retention engine; medication reminders as day-1 utility; detailed RPM/RTM CPT-code disqualification analysis; employer B2B2C channel; two-arm experiment design (literally A/B the scary keyboard-permission flow vs. a friendly flow to kill the original concept empirically). *Caveat: Gemini's report was the least rigorously sourced — several stats (77% smartphone ownership 70+, 80% pendant non-wear, ABOARD correlations) carry no verifiable citations. Directionally consistent; do not quote its numbers externally without checking.*

## 5. Founder corrections that reshaped the product (post-diligence)

These came from the founder, not the models, and both improved the concept:

1. **Rejection of the daily voice check-in for healthy seniors.** "If my kid made me talk to a robot every day for 30–60 seconds, I'd feel like I'm in jail giving roll call... they'd start despising their kid." The models imagined the senior as a patient; the actual users are proud, independent people. Voice check-ins are re-scoped to the seriously-ill/very-senior segment only.
2. **The Japan reframe.** Founder surfaced Japan's aging-population model: elders accept in-home sensors that don't actively monitor them but detect **pattern failure** (fridge not opened, light not turned on, door not opened), with postal/delivery workers as human check-in. Precedents: Zojirushi i-Pot kettle (emailing families usage since 2001), Japan Post watch-over services. This crystallized the product principle: **negative-space monitoring — detect the absence of normal, observe nothing else.** Applied to the phone: app-open events for personally chosen routine apps (his parents: WhatsApp, YouTube, news), steps, charging state. All binary, all content-free.
3. **Original intent clarified:** the goal was always peace-of-mind for the family, never medical decline detection. The diligence killed a feature the founder didn't actually want — and validated the one he did.

## 6. Design conclusions carried into the product

- Personal-baseline outlier thresholds (fit each senior's own gap distribution; alarm at ~99th percentile of *their* gaps) — turns habits like leaving the phone on the dresser from noise into modeled baseline.
- Escalation ladder: routine breaks → senior's phone asks *them* (grace period) → primary child → sibling → local responder. Family enters only after senior-silence; the local human is the rung you hope never fires.
- Household mode: two seniors under one roof → alarm on "both phones silent" (rarer, more specific).
- Digest as connection scaffolding: give the child reasons to call, don't replace the call.
- Optional hardware assist later: smart plug on TV/kettle (~₹1–2k) as a second independent routine — the literal Japan solution.
- iOS pilot workaround: Shortcuts personal automations ("When [app] opened → GET webhook") + Apple Health Sharing. Pilot-grade only; product is Android-first (India market reality). Never scrape WhatsApp "last seen" (ToS).

## 7. Verified sources (checked during synthesis)

- Intuition study: Nature Medicine, s41591-024-03475-9 (Butler et al., March 2025); Alzforum summary "Mobile Devices Track Brain Health in 23,000 People."
- Alexa Together discontinued May 21, 2025; replaced by Alexa Emergency Assist ($5.99/mo).
- Mindstrong shutdown 2023 (~$160M raised) — widely documented.
- YC Fall 2026 RFS "AI for the Aging Population" (Max Kolysh) — screenshot on file; calls for monitoring for safety/independence and caregiver-coordination software; notes even Alexa/Google Home frustrate seniors; hints voice-interface direction.
- YC Fall 2026 application deadline: July 27, 2026, 8pm PT; decisions by Aug 28; batch Oct–Dec in SF.

## 8. Bottom line

Three independent models, adversarially prompted, converged: **the original passive decline-detector is unbuildable and unwise; the peace-of-mind pattern-failure product is buildable, defensible, and untested only in execution.** The remaining risk is not "is this a real idea" — it's adoption (will seniors keep it installed?), false-positive economics (tunable, measurable), and the responder gap (a business-model question). All three are exactly what the 30-day pilot measures.
