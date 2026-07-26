# YC Fall 2026 Application — Draft

*Deadline: **Sunday, July 27, 2026, 8:00pm PT** (on-time; decisions by Aug 28; batch Oct–Dec, San Francisco). Late applications considered without guaranteed timeline. Apply at ycombinator.com/apply.*

*These are drafts in the founder's voice — edit for accuracy and personal tone. Facts in [brackets] need the founder to confirm or fill in. Keep answers short; YC reads thousands — clarity beats completeness.*

---

## Company one-liner (~50 chars)

Options, pick one:
1. **"Know your aging parents are OK — without cameras."** (49)
2. "Peace of mind for kids with parents abroad." (43)
3. "A tripwire, not a camera, for aging parents." (44)

## What is your company going to make?

> [Working name] gives adult children peace of mind about aging parents living far away — without surveilling them. Japan solved elder monitoring 25 years ago with a kettle that emails your kids when Mom makes tea: detect the absence of routine, observe nothing else. Your parent's phone is already that kettle. We passively notice that their normal routine happened (WhatsApp opened, steps taken) — no content, no location, no camera, no wearable. When routine breaks, the phone asks *them* first ("all good? tap yes"); family is pinged only on silence, then a local responder. Families get a daily "Mom's day started normally" digest instead of anxiety. First market: diaspora families (starting with the 5M-strong Indian-American corridor), where timezone pain is sharpest, willingness to pay is high, and nobody serves both sides of the ocean.

## Why did you pick this idea to work on? Do you have domain expertise?

> I left India 26 years ago. My parents are in their 70s in Chennai; my sister is in Texas. Between timezones, kids, and work, my check-ins decayed from daily to weekly — not from lack of love, but because you start assuming your parents will always be there. I am the customer. My parents are users zero: my mother will agree to anything I install; my father is a privacy-minded attorney who will fight every permission — if my design survives him, it survives the market's hardest segment. I've also been building consumer mobile products solo: RosterPro (getrosterpro.com), a youth-sports coordination app, live on iOS + web, built end-to-end by me.

## What do you understand about this space that others don't?

> Every eldercare monitoring product dies on the same rock: seniors reject being watched. The industry keeps building cameras, pendants, and check-in robots — my own father would call a daily 60-second voice check-in "roll call in jail." The insight is negative-space monitoring: seniors accept a tripwire they own and configure, that shares nothing about their life except "the normal thing didn't happen," and that asks *them* before anyone else is told. Japan proved acceptance at scale (Zojirushi's i-Pot kettle, Japan Post watch-over). Second insight: I ran adversarial diligence with three frontier AI models before building — all three independently killed the fashionable version of this idea (passive cognitive-decline detection: Apple+Biogen's 23,000-person study couldn't validate it, Mindstrong burned $160M on it, and base-rate math makes the alerts mostly false). What survives is coarse routine-failure detection with senior-first confirmation — boring, buildable, and what families actually want. Third: the hardest onboarding step is naming the local human at the end of the escalation chain — even I don't have one in Chennai after 26 years. That's not an edge case; it's the business model (partnering with India's eldercare-response services like Emoha/Samarth/Yodda).

## How far along are you?

> [Adjust to reality at submission.] Pilot live: my parents' iPhones are instrumented (consented, content-free app-open signals — three stored fields per event: who, which routine, when) feeding a baseline model — measuring signal completeness, personal-baseline stability, and simulated false-escalation rate against predeclared pass/fail gates. 30 days of data by [late August]. Previously: built and shipped RosterPro solo (live on the App Store).

## Who are your competitors, and what do you understand that they don't?

> Life360/Snug (location-centric, US-only, no escalation design); CarePredict/envoyatHome ($500 hardware, home-bound, surveillance feel); medical alerts (stigma, reactive-only); Apple's native Health Sharing (real threat on signals — but the product isn't the signal, it's the senior-consent design, the escalation ladder ending in a local human, and the cross-border family experience). India's eldercare services (Emoha, Samarth, Yodda) are partners, not competitors — they're our last rung. GaitIQ and post-RFS entrants will chase the decline-detection mirage we've already ruled out with evidence.

## How will you make money?

> The adult child pays: family subscription, $20–30/mo software tier; premium tier ($40–70/mo) adds the on-the-ground responder via partners. Expansion: other diaspora corridors (Filipino, Chinese, Mexican), domestic long-distance families, then employer caregiver benefits. Not dependent on Medicare reimbursement (verified: RPM/RTM codes don't cover this data class).

## Equity / legal
> [Fill in: entity status, cap table, any prior RosterPro entity relationship. Keep RosterPro legally separate or fold cleanly — decide before submitting.]

## Have you applied before?

> Yes — [batch] with RosterPro (team-coordination app for volunteer youth coaches). Not accepted. I shipped it anyway; it's live on iOS + web. I deliberately chose not to scale infrastructure ahead of a revenue model — that lesson (charge the motivated payer from day one) is built into this company: the diaspora adult child has both the pain and the wallet.

## Are you looking for a cofounder? (decide before submitting — do not wing this at interview)

> [Option A — open:] Yes. I can carry product and engineering solo through MVP (I've done it before), and I'm actively looking for a cofounder for [growth/ops/India partnerships]. [Option B — solo:] I'm deliberately solo for now; I've shipped complete consumer products alone and the pilot-stage company needs exactly that. I'd rather add the right person later than the available person now.

---

## One-minute video script (~140 words — talk to the camera, no slides)

> "I'm Hema. I left India 26 years ago. My parents are in their seventies in Chennai, and like most sons, my check-ins slid from every day to... every week. Not because I don't love them — because you start assuming your parents will always be there.
>
> Every product for this either surveils seniors — cameras, pendants, check-in robots my dad would call 'roll call in jail' — or tells you nothing. Japan figured this out decades ago with a kettle that emails your kids when Mom makes tea. Detect the broken routine. Watch nothing else.
>
> Your parent's phone is already the kettle. [Name] notices Mom's WhatsApp routine happened, asks *her* first when it didn't, and only then pings family — and a local responder we arrange. It's running on my parents' phones right now. I'm the customer, and there are millions of us."

---

## Interview prep notes (if invited — late August, pilot data in hand)

- **Lead with the pilot chart:** parents' baseline gap distributions + shadow false-positive rate. Nobody else in the RFS pile will have n=2 real 70-somethings instrumented.
- **The Dad story is the differentiator:** the redlined consent one-pager from a privacy-attorney father is both proof of the hard problem and proof you solved it. Bring it.
- **Expect: "Isn't this a feature Apple ships next year?"** Answer: Apple ships signals (Health Sharing exists today); it will never ship a Chennai responder network, a senior-first escalation ladder, or a cross-border family product. Kettle ≠ care loop.
- **Expect: "Why not decline detection / more AI?"** Answer with the diligence: Intuition study, Mindstrong, base rates. "We know exactly where the science ends; that discipline is why our alerts will be trusted." Turning down fashionable AI is a credibility move in 2026.
- **Expect: "Solo founder?"** Have the decided answer ready (see above).
- **Expect: "Small market?"** NRI corridor is the beachhead, not the market: every diaspora + domestic long-distance families + employer benefits. The wedge is where pain, wallet, and founder insight coincide.
- **Expect: "What about Alexa Together dying?"** It was alerts-and-emergency framing with no senior-side value and no responder; churn killed it. Our retention engine is the daily positive digest + multi-sibling accounts + responder lock-in.

## Submission checklist

- [ ] Pilot webhooks live on both phones (so "how far along" is true)
- [ ] Working name chosen (even placeholder)
- [ ] One-liner picked
- [ ] Video recorded (one take, phone camera, good light — authenticity beats polish)
- [ ] RosterPro/entity legal answer settled
- [ ] Cofounder answer settled
- [ ] Submitted before Sun Jul 27, 8pm PT
