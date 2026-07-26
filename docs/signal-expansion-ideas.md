# Signal Expansion Ideas — POST-PILOT BACKLOG

> **Status: post-pilot backlog. Nothing in this document is committed scope. Nothing here modifies the running 30-day pilot, its signals, its protocol, or gates G1–G5.** Rankings are provisional priors to be re-ranked against Day-30 data.
>
> *July 26, 2026. Method: deep ideation session (Fable 5, PM) → full draft attacked by a hostile reviewer (Opus 5 subagent, fed conclusions only, charter: "you win by killing ideas") → verdicts adjudicated below. Legend: ✅ survived · 🔧 survived-with-modification · ❌ died. Every survivor carries the attacker's strongest surviving objection verbatim.*

**Admission rule (unchanged product law):** a signal must reduce to stored fields `(who|household, signal_name, server_timestamp)` with everything else dropped at the door — otherwise rejected regardless of value. No decline/diagnostic inference in any disguise. No content. No location trails. Nothing the senior must learn, wear, charge, answer, or remember.

---

## 1. Scoreboard

| Item | Proposal | Verdict |
|---|---|---|
| S1 | App-open ping (incumbent, minimal-set analysis) | 🔧 survived-with-modification |
| S2 | Charger event promoted to co-primary | 🔧 survived — **demotion permanent**, corroborating only |
| S3 | Fridge-door sensor | 🔧 survived — severely modified (local Zigbee, no vendor cloud), demoted to corroborating |
| S4 | Anchor-appliance smart plug (mixie/TV/pump) | ❌ died |
| S5 | First-unlock-of-day (Android) | 🔧 survived-with-modification |
| C1 | Smart-TV vendor API on/off | ❌ died |
| C2 | Alarm-dismissed | 🔧 survived — corroborator only, bench-test gate first |
| F1 | Child-as-sensor (WhatsApp group / call log, zero senior knowledge) | ❌ died as drafted |
| F2 | Household-is-the-kettle | 🔧 survived — attribution rule promoted; coverage-floor and hardware-first claims deleted |
| F3 | Calm-not-detection + pilot-can't-see-the-customer | 🔧 survived-with-modification |
| A10 | Steps via Health Sharing (was grandfathered) | ❌ killed from all product plans — reviewer caught what the draft spared |

## 2. Standing findings from the adversarial pass (apply to everything)

1. **No ranking rights before data.** The pilot had produced zero pings when this was drafted. By this document's own rule ("every added signal must buy precision"), every reliability/false-positive score below is a prior, not a finding. Re-rank at Day 30.
2. **The register rule.** The signed consent one-pager makes an *architectural* promise: "The mechanism can't see these even in principle" and "a private server only I control." Any vendor-cloud signal (Tuya, SmartThings, ThinQ) silently swaps that for a *policy* promise — the mechanism sees everything and we discard it. **The two registers are not interchangeable. Expansion signals must match the architectural register or not ship.** ("Never stored" describes our database, not the mechanism.)
3. **`household` is a new data principal, not a formatting convention.** The pilot schema knows `mom` and `dad`; per-person transparency pages and heartbeats are built on that. A household signal has no honest home on either person's transparency page, and it timestamps unconsented people (the maid — a data subject inside a power asymmetry, with no DPDP exception).
4. **Two scoring axes the draft omitted, now mandatory for any signal decision:** *Attribution* — whose routine does this actually prove? *Failure direction* — does it fail dark (manufacturing false absence: costs a phone call) or fail firing (manufacturing false reassurance: the error this product cannot afford)?
5. **Proposed addition to product law** (F2's surviving core): **a household event must never be presented as evidence that a specific person is fine.** Household signals corroborate; only person-attributed signals may anchor reassurance or alarm.
6. **The boundary-crossing principle** (repairing an inconsistency the attacker found): signals encoding arrival/departure/movement (Wi-Fi join, main-door events, car Bluetooth) are location-in-one-bit and stay dead **on principle, not optics**. Stationary in-home routine completions (fridge opened, phone charged) are the only admissible household class.

## 3. Ranked shortlist (all 🔧; provisional priors, re-rank at Day 30)

Ordering logic: person-attributed above household; among corroborators, safe failure direction (fails dark) above dangerous (can fail firing).

### S1 — App-open ping on personally chosen daily apps 🔧
Incumbent (both platforms; iOS Shortcuts today, UsageStats or equivalent on Android). The senior's strongest voluntary routine, zero hardware, already gate-instrumented.
**Modification required:** the draft's "shrink to the single highest-coverage app" was backwards. Multiple automations are *mechanism-failure insurance* (iOS updates silently kill Shortcuts — the protocol's own §4.3 fragility), not signal redundancy. Analyze by **lone-coverage days** (days a signal alone carried), and never run fewer than two automations per person.
> Attacker: "You are proposing to delete your only defense against the exact failure your own protocol flags as the pilot's known fragility, on the strength of a statistic that cannot distinguish redundancy from robustness."

**Cheapest gate-safe test:** after Day 30, from `export.csv`: per-app lone-coverage-day analysis. Cost 0, analysis-only.

### S2 — Charger-event ping 🔧 (corroborating, permanently)
Already in the schema (`charge_on`). **Demotion is permanent:** Indian seniors charge overnight — a 22:30 event is a report about yesterday; a co-primary morning tripwire it can never be. Spouse-handled charging breaks attribution ("unplug that, it's full" proves a phone was handled, not that its owner was). Its real, reframed value: a **mechanism-health channel** — `charge_on` still flowing while app-opens are silent distinguishes "the Shortcut died" from "the person is quiet." Fails dark (safe direction). 48-hour window only.
> Attacker: "A signal that fires at bedtime and may not fire again for 48 hours is not a co-primary tripwire for a morning-reassurance product; it is a heartbeat for your plumbing, and promoting it is scope inflation wearing the costume of prudence."

**Cheapest gate-safe test (costs restated honestly):** if charge automations were installed at setup, compute per-person inter-charge gap distribution from existing rows. If they weren't, the data does not exist and "cost 0" was false — install at the Day-30 teardown touchpoint (a second FaceTime setup session is the real cost) and the answer arrives mid-September.

### S3 — Fridge-door sensor 🔧 (severely modified; corroborating only)
The draft's version — ₹500–900 Tuya Wi-Fi, peel-and-stick — died three ways: pairing requires a phone on the Chennai 2.4 GHz network (the founder is in Apex; the workaround puts a Chinese IoT app on Amma's phone, contradicting "there is no app of mine installed on your phone"); household events transiting a foreign consumer cloud break the one-pager's architectural promise and create a DPDP processor-contract problem no free consumer cloud can satisfy; and monsoon/load-shedding make it dark exactly when anxiety peaks.
**Surviving form:** local-only **Zigbee sensor + hub on Ethernet**, pre-paired hub-to-sensor in Apex, shipped as a unit — zero in-Chennai Wi-Fi setup, zero vendor cloud, zero app on any senior device, reporting only to the pilot-style private server. First-event-per-window only; no counts (frequency is a behavior profile). Sensor-offline renders "unknown," never "absent." Child-side travel mode. Honest BOM: **₹3,000–3,500 with hub — the <₹2,500 target fails.** Corroborating-grade under the attribution law (proves *someone*, never *Amma*).
> Attacker: "The pairing step alone relocates the product's hardest adoption problem from the phone to the fridge and puts a Chinese IoT app on your mother's handset — and the moment a household event transits a vendor cloud, the sentence 'a private server only I control' is no longer true in the document your father signed."

**Cheapest gate-safe test (claims corrected):** US-side rehearsal on the founder's own fridge validates *plumbing only* — event rates, first-event distribution, hub semantics. It cannot test the actual risks (Chennai power cuts, ISP resets, monsoon); the environmental soak needs a post-pilot Chennai install at the next natural family touchpoint. ~$40–50 hub+sensor, zero pilot contact.

### S5 — First-unlock-of-day 🔧 (Android; the market platform)
Still the best Android signal — fires on any use whatsoever, no app-inventory capability. But the draft's "no special permission" was false as engineering and as policy: `ACTION_USER_PRESENT` is not manifest-receivable (API 26+), so this is a **foreground service** with boot receiver and battery-optimization exemption, subject to Play's monitoring-app policy which **mandates a persistent notification and unique icon**, on Indian OEM ROMs (MIUI/ColorOS/Realme) engineered to kill exactly such services — whose silent death manufactures false absence. Intrusiveness honestly M, not H.
**Modification required:** build it visibly senior-owned — the mandated notification becomes the transparency feature ("Kettle is on — tap to see everything it has sent"); per-OEM autostart allowlisting is a first-class onboarding step; OEM-kill detection is part of the mechanism-health design (S2's job).
> Attacker: "Your purest signal requires a permanently running foreground service and a Play-mandated persistent notification on your mother's home screen, on ROMs engineered to kill exactly that service — the signal is not permissionless, it is the single most visible thing in the entire document."

**Cheapest gate-safe test (respecified):** the draft's emulator test was designed to return a false pass. Instead: a **30-day soak on a used Indian-market Xiaomi/Realme (~₹6–8k), with no allowlisting**, measuring silent-death rate. Zero pilot contact.

### C2 — Alarm-dismissed 🔧 (corroborator; bench-test gate before any install)
The only candidate with a true time anchor, where a daily alarm habit already exists. But it is also the only signal with a plausible **fire-without-a-human path**: if an unattended alarm's auto-silence can trigger "Is Stopped," the signal reports a human action that did not happen — false *presence*, the unaffordable error direction.
**Modification required:** empirically rule out the auto-silence path on a bench phone before any deployment; corroborator only, never the sole morning signal; habit-dependence honestly worse than "M" (lifelong 5am risers don't set alarms).
> Attacker: "You are considering promoting the only signal in the document with a plausible fire-without-a-human path, in the one direction of error your product cannot afford."

**Cheapest gate-safe test:** bench phone, alarm set, left untouched through auto-silence; observe whether the Shortcut fires. Cost 0, zero pilot contact.

## 4. Died in review

**❌ S4 — Anchor-appliance smart plug.** Killed on four converging blows: (1) its entire justification — "a second, differently-failing household channel" — was false: same mains, same router, same 2.4 GHz, same cloud as S3, so one power cut takes both and it buys zero marginal precision (negative-value by this document's own law); (2) the draft killed the smart bulb (B7) for the Indian wall-switch habit and withheld the identical kill from the plug — kitchen and TV sockets are habitually wall-switched too; (3) the hardware claims failed (sump pumps hardwired/inductive with 3–6× inrush; geysers at plug rating); (4) capability double standard — a continuous wattage curve streaming to a foreign cloud fingerprints appliances and reconstructs meal times regardless of what our database stores.
> Cause of death: "You justified S4 as a differently-failing channel and then specified a device that fails on the same mains, the same router, and the same cloud as S3 — and you killed the smart bulb for a wall-switch habit that kills the smart plug identically."

**❌ C1 — Smart-TV vendor API.** SmartThings personal access tokens now expire in 24 hours (OAuth2 partner path is the only production route); LG ThinQ has no open consumer path (third-party integrations are reverse-engineered — banned by product law #5); either way it means holding the parents' vendor credentials. Standby power states are ambiguous, and the joint probability (smart TV × vendor account × TV-not-DTH ritual) collapses the base rate.
> Cause of death: "A 24-hour token, a partner-gated OAuth path on one vendor and a reverse-engineered API on the other, and a credential-sharing posture — this is a weekend hack for one family that can never ship, which makes it a distraction for a company that must build exactly one thing."

**❌ F1 — Child-as-sensor, as drafted.** The draft's flagship inversion — timestamp the family-group message and call cadence the child already receives; "zero senior-side install" as GTM — died on its own centerpiece: a monitoring feed the monitored person never installs, never consents to, and ideally never learns about is the *definition* of the category this project exists to refuse. It is A15 (the rejected notification firehose) relocated 8,000 miles; Amma's message is her personal data and a company ingesting it as a monitored feed owes her DPDP notice and consent that the covert framing makes impossible; it structurally contradicts F3 (senior-as-owner); it does not exist on iOS (no notification-read API), which is the founder's own platform and much of the beachhead; and derived-presence-from-messages is the "last seen" class of signal by another door. **The retrospective chat-export test is deleted with it** — it would have put the whole family's message plaintext on the founder's laptop, during a live pilot, against a signed page that says "no message content… never collected."
> Cause of death: "A monitoring product that requires nothing from the monitored person, and works best when she never knows, is not reverse onboarding — it is the definition of the category you have spent three documents promising not to build."

*Successor question (new, unreviewed, explicitly not a survivor):* does the mechanism become admissible if the senior **knowingly consents** — "your normal good-morning message counts as your check-in, nothing new to do" — making her the sender-owner (the actual i-Pot posture), Android-child-side only, content matched and discarded on-device? That inverts the consent objection but was not what F1 proposed and has not faced the attacker. Park it for post-pilot review.

**❌ A10 — Steps (the item the draft wrongly spared).** The draft grandfathered steps as "incumbent-only." The reviewer's correction is accepted in full: daily step counts are body data outside the field law; they accumulate on the founder's phone *outside* the server and therefore outside the one-pager's "deleted in full at the end of the trial" promise; and a 30-day step series is the most decline-inference-shaped object in the entire system — product law #1's temptation sitting in the data. **Killed from all product plans.** Pilot handling is the founder's call: the signed one-pager's Steps row is the only entry that is not `(who, signal, when)` — if consent hasn't been finalized, fix the one-pager before signature; if it has, honor it as signed for 30 days and delete per its own deletion clause, sharing steps in no future phase.

**Other kill-list repairs from the review** (all accepted): C-f's "engineering aid" exception is closed — sensor online/offline may exist only as current-state in memory to render "unknown," never as a persisted series (named exceptions are how field laws die). C-i's "revisit per-family" clause is closed — a per-family exception path means every rejected signal returns. B3 (main door) stays dead but now **on principle** (boundary-crossing, §2.6), not optics. B6's lesson generalizes: fridge-first-event times plus any second kitchen signal drift toward meal-time reconstruction — which is why counts/series are banned and household signals stay corroborating.

## 5. Full inventory (Task 1 record, verdicts final)

Scoring: H/M/L, H always favorable. Rel = daily-routine reliability; FP$ = false-positive economics; Setup; Intru = senior-perceived intrusiveness; Dad = privacy-attorney redline; ToS = platform/legal. *The reviewer's critique of this rubric is accepted and recorded in §7 — read scores as priors.*

### A. Senior's existing smartphone — iOS (pilot platform)

| # | Signal | Stored fields | Rel | FP$ | Setup | Intru | Dad | ToS | Final verdict |
|---|---|---|---|---|---|---|---|---|---|
| A1 | App-open ping | who, app_open_x, ts | H | M | M | H | H | H | 🔧 **S1** |
| A2 | Charger-connected | who, charge_on, ts | M | M | L | H | H | H | 🔧 **S2** — corroborating, permanently |
| A3 | Battery-level crossing | who, batt_high, ts | M | M | L | H | H | H | Folded into S2 |
| A4 | Alarm stopped | who, alarm_stop, ts | M | M | L | H | H | H | 🔧 **C2** — bench-test gate first |
| A5 | Bluetooth connect (hearing aid / car) | who, bt_connect, ts | L–M | M | L | H | M | H | ❌ niche; car variant boundary-crossing |
| A6 | Wi-Fi home-SSID join | who, wifi_join, ts | — | — | — | — | L | — | ❌ rejected at the door — boundary-crossing (§2.6) |
| A7 | Sleep Focus off | who, focus_off, ts | L | — | — | — | — | — | ❌ requires a new habit |
| A8 | NFC tag tap | — | — | — | — | — | — | — | ❌ new learned action, DOA |
| A9 | Message/email/Wallet triggers | sender/txn context | — | — | — | — | — | — | ❌ rejected at the door — content |
| A10 | Steps / Health Sharing | body data | — | — | — | — | — | — | ❌ killed from product (§4) |
| A11 | Screen Time / pickups | usage inventory | — | — | — | — | — | — | ❌ entitlement wall + content-shaped |

### A. Android (market platform; not in pilot)

| # | Signal | Stored fields | Rel | FP$ | Setup | Intru | Dad | ToS | Final verdict |
|---|---|---|---|---|---|---|---|---|---|
| A12 | First unlock of day | who, first_unlock, ts | H | H | M | **M** (Play-mandated persistent notification) | H | M | 🔧 **S5** |
| A13 | Charger connected | who, charge_on, ts | M | M | L | H | H | H | Folds into S2 |
| A14 | Chosen-app first-open (UsageStats) | who, app_open_x, ts | H | M | M | H | M (capability vs. collection) | M | S1's Android twin; S5 preferred (narrower capability) |
| A15 | Notification listener (senior side) | notification stream | — | — | — | — | — | — | ❌ rejected at the door — content firehose (and see F1) |
| A16 | Accessibility-service anything | screen content | — | — | — | — | — | — | ❌ spyware-shaped; Play ban |

### B. Home retrofit hardware

| # | Signal | Stored fields | Final verdict |
|---|---|---|---|
| B1 | Fridge-door first-event | household, fridge_door, ts | 🔧 **S3** — only in the local-Zigbee, no-cloud form; corroborating; ₹3,000–3,500 honest BOM |
| B2 | Anchor-appliance plug (mixie/TV/pump) | household, anchor_on, ts | ❌ **died in review** (§4) |
| B3 | Main-door sensor | household, main_door, ts | ❌ boundary-crossing, on principle |
| B4 | PIR motion | household, motion, ts | ❌ dominated by B1 on optics and price |
| B5 | Bathroom / bedroom / medicine-cabinet | — | ❌ rejected at the door — health content |
| B6 | Pooja-cabinet sensor | household, cabinet, ts | ❌ protected-category adjacency no rename cures |
| B7 | Smart bulb (kitchen dawn) | household, light_on, ts | ❌ wall-switch habit kills it silently (the kill that also took B2) |
| B8 | Bed pressure mat | sleep occupancy | ❌ rejected at the door — body data |
| B9 | Camera / doorbell / audio | — | ❌ rejected at the door — content, categorically |
| B10 | Milk-box / newspaper sensor | household, milk_taken, ts | ❌ bespoke hardware for what B1 proves |

### C. Ambient / utility

| # | Signal | Final verdict |
|---|---|---|
| C-a | TANGEDCO electricity consumption | ❌ no consumer API; billing latency; consumption curve is a behavior profile |
| C-b | CMWSSB water | ❌ no access path |
| C-c | LPG refill cadence | ❌ rejected at the door — purchase data; monthly anyway |
| C-d | Telecom HLR reachability polling | ❌ lookup-ToS/TRAI wall; "phone on network" ≠ any human routine |
| C-e | Prepaid recharge cadence | ❌ rejected at the door — financial data |
| C-f | Broadband router uptime | ❌ CGNAT; measures the house's power, not a routine. Exception clause closed (§4) |
| C-g | Smart-TV vendor API | ❌ **died in review** (§4, C1) |
| C-h | DTH set-top viewing | ❌ no API |
| C-i | Smart-speaker interaction | ❌ near-zero existing-habit base; revisit clause closed (§4) |
| C-j | Delivery-person check-ins (Japan Post analog) | Not a signal — responder-partnership track (Emoha/Samarth/Yodda) |

## 6. Inversion findings (Task 2)

Assumptions inverted: phone is the kettle → the house is the kettle; the child is the watcher → the child is a sensor / the senior is the owner; alerts are the product → silence is the product; routine = app-opens → routine = any pre-existing threshold event; one monitored person → a household organism; more signals = better → every added signal must buy precision or it is negative-value; pilot validates the product → pilot validates the founder's-family variant of it.

Existing-access audit (what the diaspora child already holds): WhatsApp family group — ❌ unusable without senior consent (F1); child's own call log — same verdict, same reason; Apple Health Sharing — ❌ killed (A10); Find My / Family Sharing — banned, stays banned; shared OTT profiles — content, rejected; shared Google Photos — sporadic, content-adjacent, rejected. *Net result of the audit: the child's existing access is almost entirely inadmissible — a finding in itself: this product has no covert shortcut, which is the point of it.*

### F1 — The child is already a sensor ❌ died as drafted
Recorded in §4. The three sentences that survive it: the diaspora child's inbox is real signal; using it without the senior's knowing consent is the category this project refuses; the only living successor is the *consented* sender-owner variant, parked unreviewed.

### F2 — The household is the kettle 🔧
**What died:** the "coverage floor" claim — the house is stable only when the human is stationary, and the ICP (proud, independent, still traveling, often unannounced) generates multi-day guaranteed false alarms the phone never produces; the phone travels with her, the house does not. Also deleted: the "hardware-first for India-domestic" reframe — lowest willingness-to-pay segment, COGS/customs/RMA logistics, and incumbents (Emoha/Samarth/Yodda) already selling humans into it; that is a different company. The maid problem stands: at household grade she is an unconsented, timestamped data subject inside a power asymmetry — DPDP has no exception for her.
**What survived and got promoted:** the attribution-honesty rule — now proposed product law (§2.5): a household event must never imply a specific person is fine. And the combinator ambiguity the attacker exposed is resolved in its favor: household signals **corroborate only** (AND-logic with person-attributed signals for alarm suppression); they never sole-source an alarm and never sole-source reassurance.
> Attacker: "The house is only more stable than the human when the human is stationary — and your entire product story is that she is proud, independent, and still going places."

**Cheapest gate-safe test (moved):** household-facts questions (mixie daily? pump? geyser seasonality?) moved **out of the pilot window entirely** — the draft's "casual questions on normal calls" would cue both parents that routines are under study, contaminating Phase-1 blinded labels and the exact variable G5 measures. Ask after Day 30.

### F3 — The product is calm, not detection — and the pilot cannot see the customer 🔧
**Survives, with three demotions.** (1) *Fewer, higher-precision signals beat more signals* — stands, and governs this whole document: every expansion candidate is guilty until it demonstrably reduces alert entropy. (2) *Senior-as-owner* is demoted from product identity to **consent posture**: commercially, payer=child must keep the account (a kill-switch held by a non-paying party makes churn a function of someone else's mood), and senior-as-owner makes consent-degradation *harder*, not easier — DPDP guardian-consent is a legal process a $25/month product cannot operationalize. The senior keeps the kill-switch and full transparency (the pilot's consent script already does this); she does not become the account. The i-Pot is demoted from precedent to anecdote — family-paid, senior-as-sender-not-owner, and commercially modest. (3) *The shared blind spot stands and sharpens:* three diligence models and a motivated founder all reasoned from the founder's available family. The pilot cohort — married, cohabiting, iPhone-using, founder-trusting — is maximally unlike the ICP crisis case (solo, widowed, Android-or-feature-phone, trusting a stranger). Accepted correction: **G1 and G4 are near-unfalsifiable in this cohort** (G4's failure condition requires a father to reject his son's project; G1 at n=2 with aware subjects is close to preordained). The pilot's real yield is G3's threshold arithmetic and G5's contact-frequency delta — scope Day-30 conclusions accordingly, and say "anxiety relief plus faster discovery, clinical outcome delta unquantified" in any external claim.
> Attacker: "You correctly say the pilot cannot see the customer, then hand the pilot the gavel over every idea in the document — and the two gates you will pass most easily are the two that measure your father's love, not your consent design."

**Cheapest gate-safe test (moved and de-led):** the ownership/framing questions move to a **separate post-debrief session after Day 30**, outside the gate window — the Day-30 debrief is a one-shot instrument whose answers are binding spec (protocol §8), and "would you want to own this?" is a leading question no parent answers with "no." Present neutral alternative framings instead. The founder self-log (each Phase-2 day: did I check the digest or the alert channel first?) stays — founder-only, zero contact.

## 7. Adversarial pass record

**Method:** the full Task-1/Task-2 draft (conclusions and scores, no reasoning) was handed to an Opus 5 subagent under a hostile charter — argue failure in practice across senior adoption in urban India, false-positive economics at real base rates, the privacy-attorney redline, platform/ToS walls, ocean logistics, and decline-detection/content-observation creep; win by killing. It returned per-item verdicts (KILL/WOUNDED/STANDS), three standing objections, attacks on the kill list's coherence, and externally verified sources (Android implicit-broadcast exemption list; Google Play monitoring-app policy; SmartThings token-expiry change; DPDP extraterritoriality and guardian consent; Apple Shortcuts alarm triggers). Nothing received STANDS. All verdicts above are adjudicated, not transcribed: S4/C1/F1-as-drafted/A10 deaths accepted in full; S1/S2/S3/S5/C2/F2/F3 survive only with the named modifications.

**Its critique of the draft's scoring, accepted:** the rubric never scored a shortlisted item unfavorably (post-hoc rationalization signature); FP$ at "M for nearly everything" discriminated nothing; and the two decisive axes for a negative-space product — attribution and failure direction — were missing. They are now standing findings (§2.4) and re-ranked the shortlist (they are why every household signal is corroborating and why C2 sits last).

**Its test-table audit, accepted:** five of seven gate-safety/cost claims in the draft were false. F1's test deleted outright (family message plaintext on the founder's laptop during a live consent-governed pilot — a direct G4 interaction); F2's and F3's questions moved outside the pilot window; S5's emulator test replaced with an Indian-ROM soak ("testing on the wrong hardware for the wrong duration against the wrong failure is worse than no test, because it produces confidence"); S2's and S3's costs restated. Only S1's test survived as written — and even it was re-aimed at lone-coverage.

**Reviewer's structural recommendation, recorded:** the durable artifacts here are the kill list (so nothing gets re-derived), the attribution law, and the questions the pilot must answer — not the ranking, which has no rights until Day-30 data exists. Adopted as the reading order for future selves: §2 and §4 are the document; §3 is a prior.

## 8. Addendum — founder session, Jul 26 (post-review)

**Re-litigations sustained:** health data stays dead at product scale — not only on law/policy grounds but on a platform fact: Apple exposes no API to data shared *with* you via Health Sharing, so the only scalable route is a senior-side HealthKit/Health Connect uploader, which converts the company into a health-data processor for a weak, attribution-broken signal. Kill stands.

**Founder correction adopted (changes platform priors):** "Indian seniors are overwhelmingly Android" is population-wide; the NRI beachhead *selects for* iPhone parents (hand-me-down/gifted iPhones, FaceTime with grandkids). iOS tier moves from "someday" to a designed tier; device-mix question goes into any waitlist/next-pilot signup. See PLAN.md.

**iOS-tier feasibility sketch (agreed direction, pre-spec):** Shortcuts is the permanent iOS collection layer, wrapped in reliability engineering rather than replaced: child-guided setup (pre-built importable shortcuts + FaceTime wizard; the payer is the installer), heartbeat-detected silent death with a child-facing repair flow (time-to-repair as a product metric), charger channel as mechanism-health discriminator, and the senior-first "All good? Tap yes" delivered as a WhatsApp Business **template message with reply button** — platform-legal outbound ask in the app seniors already live in, phone-OS-agnostic, no senior-side install required. Optional later: minimal senior app — collects nothing, but unlocks three avenues (founder Q, Jul 26): (1) reliability — Shortcuts action targets the app's App Intent, which queues/retries pings offline instead of losing them to a raw URL fetch; (2) device-liveness — silent-push wakes give a "phone on + connected" plumbing signal, distinguishing dead phone from quiet person; (3) dignity UX — native "All good? Tap yes," on-device transparency page + kill switch, and (Apple-approved) critical alerts for top ladder rungs. Explicitly does NOT unlock unlock-events, other-app usage, notifications, or Screen Time (entitlement-walled). The kettle signals remain senior-owned Shortcuts automations; the app only makes them reliable. The live pilot doubles as this tier's prototype; G1 is its reliability gate, and every setup stumble on the Chennai call is usability data for it.

## 9. Constraint self-check

- No decline/diagnostic inference anywhere: no trends, no baselines beyond the pilot's existing gap thresholds, no scores; the one decline-shaped object found (A10 step series) was killed, not kept. ✅
- Every surviving signal reduces to `(who|household, signal_name, server_ts)`; every signal that could not was rejected at the door and is recorded as such. ✅
- Nothing requires the senior to learn, wear, charge, answer, or remember anything; the one mandated visible artifact (S5's Play notification) is a transparency feature the senior may ignore. ✅
- No test touches G1–G5, parent phones mid-pilot, Phase-1 label blinding, or the Day-30 debrief's one-shot instrument; every test that would have (F1, F2-questions, F3-questions) was deleted or moved outside the window. ✅
- Everything herein is post-pilot backlog; the only near-term founder decision flagged is the A10/one-pager accuracy question (§4), which is a pilot-consent matter, not expansion scope. ✅
