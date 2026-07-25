# 30-Day Family Pilot Protocol

*Objective: validate the negative-space monitoring concept with the founder's own parents (both 70+, iPhones, Chennai / periodically Texas) before writing product code. Zero/near-zero build. Target start: before July 27, 2026 (so the YC application can say "pilot live" and any late-August interview has ~4 weeks of data).*

---

## 1. What this pilot must answer

1. **Baseline stability** — Do each parent's phone routines produce a stable enough personal baseline that outlier gaps are meaningful?
2. **False-positive economics** — At a chosen threshold, how many *unnecessary* escalations per person per month would have fired?
3. **Adoption/consent** — Do the parents tolerate (ideally, forget about) the system? Does the privacy-minded parent (Dad, attorney) accept the framing and *keep it installed*?
4. **Value over status quo** — Does the digest tell the founder/sister anything they didn't already know from normal contact? Does it prompt more calls?

Explicitly **not** tested: decline detection (out of scope permanently), ML models (none in pilot), scale.

## 2. Participants and roles

| Person | Role | Notes |
|---|---|---|
| Mom | Monitored participant | Compliant — weak disconfirmation signal; watch behavior, not words. Habit: leaves phone and walks around → her data tests the gap-threshold design. |
| Dad | Monitored participant | Privacy-minded attorney — the hard test. His objections are the privacy spec. If he keeps it installed 30 days, the consent design works. |
| Founder | Experimenter + primary "child" recipient | Runs webhook, digests, logs. |
| Sister (Texas) | Secondary recipient | Second escalation rung; helps with remote setup if needed. |

## 3. Signals (all consented, all content-free)

| Signal | Source | Mechanism | Grade |
|---|---|---|---|
| WhatsApp opened | iOS Shortcuts automation | "When WhatsApp is opened → Get contents of URL (webhook)" | Alarm-grade |
| YouTube opened | iOS Shortcuts automation | Same pattern | Alarm-grade |
| Safari/news opened | iOS Shortcuts automation | Same pattern (app-level trigger) | Alarm-grade |
| Steps | Apple Health Sharing → founder's phone | Native; no code | Corroborating only (undercounts when phone is left behind) |
| Charger connected/disconnected (optional) | Shortcuts automation (charging trigger) | Same webhook pattern | Corroborating |

Rules: no location, no audio, no message content, no browsing content. The webhook receives only `{who, signal, timestamp}`.

## 4. Setup (founder tasks, ~half a day)

### 4.1 Webhook endpoint (Python, ~1 hour)
- Tiny HTTPS endpoint (FastAPI/Flask on any host, or a serverless function) logging `person, signal, ts` to SQLite/Postgres. One row per ping. Add a `/status` page listing last-seen per person per signal.
- **Heartbeat monitor:** a daily job that alerts the *founder* (not family) if a device has sent zero pings — this catches silently disabled Shortcuts (iOS updates or curious taps can kill automations) and is conveniently also the product's core logic.

### 4.2 Parent phones (30–45 min each, in person or via FaceTime with sister assisting)
1. Shortcuts app → Automation → New Personal Automation → **App** → choose app → "Is Opened" → add action **Get Contents of URL** (the webhook, with query params for person+signal) → **turn OFF "Ask Before Running"** (Run Immediately). Repeat per app (3 automations per phone).
2. Health app → Sharing → share Steps (and Walking metrics if desired) with founder's Apple ID.
3. Verify: open each app, confirm webhook rows appear.
4. Note: automations are per-device; when Mom travels to Texas, everything keeps working (signal is app-open, not location).

### 4.3 Known fragility (accepted for pilot)
Shortcuts automations are a pilot hack, not a product mechanism. iOS updates may disable them; the heartbeat monitor is the mitigation. Product build (later) is Android-first where proper APIs exist.

## 5. Study design: two phases

### Phase 1 — Silent baseline (Days 1–14)
- Collect pings. **No alerts, no thresholds, no family notifications.**
- Founder computes per-person, per-daypart distributions of inter-touch gaps (time between successive pings from any alarm-grade signal, waking hours only).
- **Blinded ground-truth labels:** each parent (or via normal family chat, without revealing the purpose) notes unusual days — travel, visitors, illness, phone left at home, temple festival, etc. Founder logs these WITHOUT looking at the ping data first (write the label log before opening the dashboard each day). This is the honest-analysis discipline from the ChatGPT protocol.
- End of Phase 1: pick thresholds. Starting recommendation: alarm candidate = daytime gap > 99th percentile of that person's Phase-1 gaps, AND no alarm-grade ping by a personal "by-noon" deadline. Household rule: if both parents are co-located, candidate fires only when BOTH phones are silent past threshold.

### Phase 2 — Shadow alerting (Days 15–30)
- Apply the prewritten threshold rules **in shadow mode**: candidate alerts are logged and sent ONLY to the founder, never to parents or sister. No ML — fixed rules only (do not train models on n=2).
- For every candidate alert, founder records: timestamp, triggering rule, apparent cause (from label log / a normal casual call), and classification:
  - **True-useful** — something family genuinely wanted to know and didn't already;
  - **True-redundant** — real but already known via normal contact;
  - **False** — parent fine, routine just varied.
- Also simulate the ladder on paper: for each candidate, would the senior-first "tap yes" + 90-minute grace have absorbed it? (i.e., was the parent reachable/active within 90 min of the candidate firing?)

## 6. Escalation ladder (design being validated, even though pilot runs it in shadow)

1. Routine breaks (threshold exceeded) → notification on **senior's** phone: "All good? Tap yes." Grace period 90 min.
2. Silence → ping founder ("no activity since morning; she hasn't responded").
3. +60 min silence → ping sister.
4. +60 min → local responder call list. **Pilot gap:** no Chennai responder currently exists. Pilot action item: identify one candidate (neighbor / apartment watchman / family doctor / trial conversation with Emoha, Samarth, or Yodda). Finding this person is itself a pilot finding — every diaspora customer faces the same step.

## 7. The digest experiment (Days 15–30)

- Founder writes (manually, or a small script) a **daily one-line digest** to himself and sister: "Mom: active by 8:40am, 2,100 steps. Dad: active by 7:15am." Plus a weekly summary.
- Track: does the digest change behavior? Count calls/messages to parents per week, Phase 1 vs Phase 2. The thesis says digests *increase* contact (conversation prompts), not replace it.
- Optionally A/B the framing on sister: alerts-only vs. daily-positive digest — which does she prefer after 2 weeks?

## 8. Consent scripts (say it, don't wing it)

**To Dad (the attorney):** "I built a tripwire, not a camera. Your phone tells my server one thing: 'Dad did a normal thing today' — a timestamp, nothing else. No content, no location, no listening. You can see every ping it has ever sent, and you can turn it off yourself in Settings any time — I won't reinstall it without asking. Here's the one-page description of what's collected; strike anything you don't like. The point is that I'll never call you at 6am worried unless something is actually wrong — this is me pestering you *less*." Then hand him the one-pager and let him redline it. **Whatever he strikes is the product's privacy spec.**

**To Mom:** "This just lets me see that your day started normally so I don't worry. If your phone is quiet all morning it will ask *you* first if everything is okay — nobody gets bothered unless you don't answer."

Consent-degradation note (pilot-level): agree now, in writing, on what happens if a parent later wants it off or can no longer meaningfully consent — the answer is: it comes off. Product-level policy is an open question in the brief.

## 9. Predeclared pass/fail gates (write these down before Day 1 — do not move them after)

| Gate | Pass | Fail |
|---|---|---|
| G1 Signal completeness | ≥90% of days produce ≥1 alarm-grade ping per parent with zero effort from them | <80% → phone is not a reliable "kettle" for this demographic; rethink sensor (smart plug) |
| G2 Baseline stability | Phase-1 gap distributions stable enough that a fixed threshold yields <2 shadow candidates/person/week | Erratic beyond tuning → single-phone signal insufficient; add second routine source |
| G3 False-escalation rate | Simulated ladder (with senior-first + grace) produces ≤1 would-be family escalation per person per month that is FALSE | >3/month → threshold or design fails; do not build until fixed |
| G4 Adoption (the Dad test) | Both parents keep automations enabled 30 days; Dad does not ask for removal | Either parent disables or resents it → consent design fails; redesign before any build |
| G5 Value | ≥1 true-useful event surfaced, OR founder+sister report the digest measurably changed contact frequency/quality (calls up, worry down — ask sister for a 1–10 before/after worry score) | Digest ignored and nothing surfaced → concept adds nothing over status quo for healthy seniors; revisit target segment (older/sicker, living alone) |

**Interpretation rules:** a quiet 30 days cannot prove alert *sensitivity* (no real event may occur) — G1–G4 are the real gates; G5 measures the reassurance/connection value which is the actual product. Passing does not validate the business; it justifies building the Android MVP and running a 10–20 family pilot with strangers (the next gate that matters).

## 10. Data to keep (this becomes the YC evidence)

- Raw ping log (the founder's parents' anonymized baseline distributions make a great chart).
- Threshold math + shadow-alert ledger with classifications.
- The redlined one-pager from Dad (photograph it — it's a war story *and* a privacy spec).
- Call-frequency before/after. Sister's worry score before/after.
- A short written narrative of anything the system caught or missed.

## 11. Timeline

| Day | Action |
|---|---|
| 0 (now) | Build webhook + status page; write gates down; draft consent one-pager |
| 1–2 | Set up both phones (FaceTime with sister if needed); consent conversations |
| 1–14 | Phase 1 silent baseline + blinded labels |
| 14 | Threshold selection; write shadow rules |
| 15–30 | Phase 2 shadow alerts + daily digest + ladder simulation |
| 30+ | Score gates; write findings memo; go/no-go on Android MVP; (if YC interview: this is the demo) |
