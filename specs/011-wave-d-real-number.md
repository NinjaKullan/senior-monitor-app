# Spec 011 — Wave D: the real HeyKettle number

Status: RATIFIED by Hema, 2026-08-28 (DECISIONS 193) — architecture A
and the 👍 quick-reply button both stand. Phases may proceed in order,
starting with Phase 0. Asana: 1217926673817274.

Starting position: Meta approved the display name "HeyKettle"
(resubmission #3, Aug 27). The approved number +1 984-370-4452 lives in
the family's WhatsApp Business Account (WABA) in Meta Business Manager.
All WhatsApp asks today ride the Twilio sandbox, which requires each
parent to join with a code — fine for our parents, wrong for strangers'
parents. Wave D replaces the sandbox with the real number.

## 1. Architecture decision (the one that gates everything)

Two candidates were on the task:

- **A. Twilio WhatsApp sender** — register +1 984-370-4452 as a Twilio
  sender; the existing Twilio transport keeps working with a changed
  `from` and template SIDs.
- **B. Meta Cloud API direct** — a new `meta_whatsapp` transport speaking
  Meta's API: new webhook format and verification, token management,
  new send path, new failure modes.

**Recommendation: A, the Twilio sender.** Reasoning, on the record:

- The transport we have is *proven in production*: sends, inbound 👍
  parsing, idempotency, signature validation, ledger rows — all of it
  passed Wave C with a real parent. Option A changes configuration and
  templates; option B rewrites the riskiest I/O in the product and asks
  us to re-earn confidence we already paid for.
- Cost cannot decide this at our scale. Twilio adds $0.005 per message
  on top of Meta's ~$0.0034 utility-template fee; asks fire only on
  quiet mornings, so even an implausible 300 messages/month is under $3.
  Option B's fee advantage becomes real at volumes we will not see for
  years.
- One vendor console for the founder instead of two. Templates,
  numbers, logs, and the existing sandbox all live where Hema already
  works.
- Reversibility: the number and the WABA remain the family's own.
  If volume or a Twilio limitation ever justifies it, migrating a number
  to Cloud API later is a supported path; nothing in A forecloses B.
  Revisit trigger, recorded now: message volume exceeding ~10,000/month
  or a template capability Twilio cannot express.

## 2. Phase 0 — connect the number (Hema, consoles, no code)

- In Twilio Console → Messaging → Senders → WhatsApp senders → new
  sender. The embedded Meta signup connects Twilio to the existing Meta
  Business Manager; choose the existing WABA and +1 984-370-4452. The
  display name "HeyKettle" is already approved and rides with the WABA.
- Complete number verification if prompted (SMS/voice code to the
  number).
- Done when the sender shows Online in the Twilio console. No repo
  change; credentials and consoles are founder work throughout.

## 3. Phase 1 — message templates (business-initiated law)

A real number may only *initiate* a conversation with a Meta-approved
template. Once a parent replies, a 24-hour service window opens where
free-form messages are allowed. The ask ladder initiates; therefore the
ask must become a template.

- The template body must be the EXACT ask copy that ships today — the
  wording recorded verbatim in DECISIONS at Wave C. Nothing about the
  move to the real number may change what a parent reads. CC extracts
  the current strings; the PM reviews the template submission text
  against DECISIONS before Hema submits.
- (ruling) Add a quick-reply button to the ask template — a single
  button showing 👍 — so a parent can tap instead of typing. Tapping
  sends the button text as an ordinary inbound message, which the
  existing parser already accepts; typed 👍 keeps working unchanged.
  Elder-proof both ways. If declined, the template ships without
  buttons and nothing else changes.
- Follow-on ladder messages that occur within the service window a
  parent's reply opened may stay free-form (they are today's copy,
  unchanged). Any ladder message that can fire OUTSIDE a window must
  also be a template; CC audits the ladder's timing to enumerate which
  rungs those are, and files the list as a DECISIONS flag before
  building.
- Submission is through Twilio's Content Template Builder (Hema, in
  console, with PM-reviewed text). Meta approval is usually hours to a
  couple of days. Approved template copy is recorded VERBATIM in
  DECISIONS, per standing law.

## 4. Phase 2 — the build (CC, after templates approve)

- Config: the WhatsApp `from` becomes the real number; template Content
  SIDs land in config, never hardcoded in message bodies. The sandbox
  settings remain present and functional behind config until sunset.
- Send path: business-initiated ask sends use the template API
  (content SID + variables). The transport, webhook, parsing, ledger,
  and idempotency code are untouched except where the template call
  differs from a body send.
- Failure honesty: a template send rejected or a template later paused
  by Meta writes an ops_alert and ntfy — a parent silently not asked is
  the one failure Kettle must never absorb quietly.
- Tests: template-send path with SID + variables; sandbox behavior
  unchanged when config says sandbox; the 👍 inbound path identical for
  typed and button replies; copy scan over any new strings; ledger rows
  name the transport actually used.

## 5. Phase 3 — dark stage, flip, sunset

- Dark stage: the Rehearsal family's parents point at Hema's own
  WhatsApp; run the ladder end-to-end on the real number — template
  ask arrives from "HeyKettle", button tap stands the ladder down,
  ledger and ops_alerts correct — before any real parent sees it.
- Flip: the real family moves to the real number. The first real ask
  after the flip is watched live, same as Wave C's first ask.
- Sunset: after one clean week, sandbox config is removed and DECISIONS
  records the retirement. Parents never notice anything except that the
  sender now says HeyKettle.

## Costs (recorded so future-us knows what we knew)

Twilio: $0.005/message each direction, on top of Meta. Meta: utility
templates ~$0.0034 outside a service window, free inside one; service
messages free. Source: Twilio's WhatsApp pricing page, checked
2026-08-28. At beta scale this is single-digit dollars a month.

## Out of scope

Cloud API migration (revisit trigger in §1); marketing or onboarding
broadcast templates; multi-number routing; anything that changes ask
copy or ladder timing.
