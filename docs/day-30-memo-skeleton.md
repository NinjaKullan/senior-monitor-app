# Day-30 memo — skeleton (PM, started 2026-08-29)

Purpose: one honest document, thirty days after the real family went
live, that says what Kettle actually did — for founder judgment, the
beta go/no-go, and (if useful) investors. Numbers get filled when they
exist; the skeleton exists so nothing is reconstructed from memory.

## 1. What ran
- Families live (Rehearsal + Suryaprakasam), dates, channel history
  (email waves; WhatsApp sandbox → real number timeline).
- Every spec shipped in the window, one line each, DECISIONS refs.
- EVIDENCE SO FAR (Aug 29-31): spec 012 Family Memory live in prod
  same-day (200-204; DB-verified honest: zero false "started" rows
  across three days of digest cycles). Wave D template arc 205-210:
  Meta forbids emoji in template buttons (205, verbatim error on
  file); founder reword (206); approved in 9 minutes, recategorized
  Utility→Marketing (207); Phase 2 built/reviewed/deployed (208-209);
  dark stage armed (210). Content library wave 1 + articles 5/19
  live; measurement ruling (201).

## 2. Did the core loop hold?
- Asks sent / replies / ladders climbed / silent-day escalations —
  and for each escalation: was it right to escalate?
- Duplicates, misfires, wrong-clock incidents (should be: the Aug 27
  "duplicates" that weren't, and nothing else — verify).
- Deliverability: any email in spam, any WhatsApp send failure,
  ops_alerts fired and whether each was honest.
- ON FILE ALREADY: Aug 31 sandbox send to unjoined number, Twilio
  63015, failed clean, nobody received it (SM446d0c…893f8) — a
  config race during dark-stage arming, not a product defect; the
  ordering lesson is in DECISIONS 210 and the runbook precondition.

## 3. What the family actually felt (the only metric that matters)
- Mom and Dad: do they know Kettle exists in their day? Any moment of
  friction or confusion? (elder-proofing verdict)
- Hema-as-customer: did the notes change anything — fewer reflexive
  calls, earlier notice of anything, false comfort anywhere?

## 4. Watched questions (considered, not forgotten)
- **Content-blind replies (DECISIONS 197):** any reply stands the
  ladder down, typed distress included; Kettle neither answers nor
  forwards it. Watch: does any real reply carry content that deserved
  more than stand-down? Data decides a revisit, not intuition.
- Ask-inside-a-window oddities (DECISIONS 194): did the template-only
  rule cost anything in practice?
- **Reaction-👍 (new, from 205/210):** the approved template has NO
  button, so a parent's likeliest gesture is a long-press REACTION —
  which may never reach the webhook as an inbound message. Dark-stage
  pass 2 tests it deliberately; the answer (stands down / doesn't)
  is a flip-decision input and belongs here with data.
- Timezone moves (spec 010): any wrong-clock note after a move/DST?
- Anything a parent DID that the model says parents don't do.

## 5. Costs and ops
- Actual monthly spend by vendor (Fly, Twilio, Meta, Resend, domain).
- WhatsApp ask pricing rides the MARKETING category (Meta
  recategorized at approval, 207) — read actual per-message rates
  off the first real invoice rather than the rate card; at one ask
  per parent per quiet morning this is cents/month, but record it.
- Founder hours/week on ops vs build.

## 6. The call
- Beta go/no-go against the sequencing law (Wave D live before
  strangers' parents).
- The one thing to fix before any stranger's family joins.
