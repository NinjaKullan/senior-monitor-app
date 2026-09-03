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

---

## Amendment A (2026-09-02): SMS transport for +1 parents

Status: RATIFIED by Hema, 2026-09-02 (DECISIONS 231): A.4 = option
(a); A.6 "They said yes" stands; A.5 family-facing opt-out copy
deferred. Filed because DECISIONS 228 fixed the strings and DECISIONS
230 cleared the carrier gate (campaign CM267f6c7e5b77d9bb9d57c0bc13945c01
Approved, bound to Messaging Service MG0e9fbf94ad89764c8a6f121f2027675c).
CC builds after the Phase 3 flip; nothing here changes WhatsApp
behaviour.

### A.1 What this adds

A parent in the US who does not use WhatsApp can receive the same ask
by SMS. That is the whole feature. Same ask, same 👍-or-silence, same
ladder to the family. No new surface for the family.

### A.2 Routing (per parent, not per kind)

Today the roster picks a transport by message kind. For `ask`, the
carrier is chosen per parent instead:

1. `parents.whatsapp_e164` set → `twilio_whatsapp` (unchanged).
2. else `parents.phone_e164` set AND starts with `+1` AND
   `sms_consent_utc` set AND `sms_opted_out_utc` null → `twilio_sms`.
3. else → recorded skip, reason names which condition failed.

No cross-transport retry in v1: a failed WhatsApp send does not fall
through to SMS. A non-+1 phone never routes to SMS (India DLT remains
deferred). Digests, follow-on, all-clear: unchanged (email to family).

### A.3 Outbound: `twilio_sms` transport

- New transport `twilio_sms`, kinds `(ask, sms_welcome)`. Registered
  under that name in OUTBOUND_TRANSPORT; fails closed if
  `TWILIO_MESSAGING_SERVICE_SID` is unset (same posture as
  TWILIO_WHATSAPP_FROM).
- Messages API payload: `MessagingServiceSid`, `To` (bare E.164, no
  prefix), `Body`. Never a bare `From`; the 10DLC registration is on
  the service. No ContentSid (SMS has no templates).
- `sent_messages.transport = 'twilio_sms'`; everything else in the
  ledger identical to the WhatsApp ask row, so the reply match, the
  follow-on cancel, and DECISIONS 145/153 logic need no change.
- 👍 in the body forces UCS-2 encoding: the v7 ask is about 3
  segments. Accepted; strings stay verbatim. Note the cost in the
  Costs section when this ships.

### A.4 Bodies (VERBATIM, from DECISIONS 228 and
docs/a2p-10dlc-campaign.md)

**SMS ask** (RATIFIED: option (a)): the filed sample, always. v7
body + newline + "Reply STOP to end these texts." Named form:
"Hi. {{1}} asked Kettle to check in with you when your morning is not
as usual. Is everything okay? Reply with a 👍 when you can.
Reply STOP to end these texts."
`{{1}}` resolves exactly as WhatsApp does (`owner_first_name`,
fallback "Your family", DECISIONS 217). Rejected alternative, for the
record: STOP line only in the welcome text (campaign-doc option (c));
weaker against an audit.

**Welcome text**, kind `sms_welcome`, once per parent, at enrollment:
"HeyKettle: [name] set you up to get a short text from Kettle when
your morning is not as usual. At most one question a day, and one
reminder. Message and data rates may apply. Reply HELP for help or
STOP to end these texts. heykettle.com"
`[name]` = the same owner-first-name resolution; fallback reads
"HeyKettle: Your family set you up…". Idempotent: keyed by
(parent_id, kind) in sent_messages; a re-run never sends twice.

**HELP reply**: not sent by Kettle. Twilio's Messaging Service
Opt-Out Management answers HELP; founder pastes the filed text there:
"HeyKettle: a family service. Questions: hello@heykettle.com. Reply
STOP to end these texts."

**"One reminder"**: the script and welcome promise "at most one
question a day, and one reminder". That is a ceiling, not a
commitment. v1 sends the parent no reminder (the follow-on goes to
the family, as today). Filed here so nobody builds a parent reminder
to honour wording that does not require it.

### A.5 Inbound: STOP / START / HELP without reading content

The Messaging Service's inbound request URL is pointed at
`/outbound/reply` (founder, console; A.8). Twilio's Advanced Opt-Out
handles the keywords itself and adds an `OptOutType` parameter
(STOP / START / HELP) to the webhook. The endpoint keeps its §2.6 law:
the body is never read; only `From` and `OptOutType` are.

- `From` without `whatsapp:` prefix → look up by `phone_e164`
  (`db.parent_by_phone`, currently unused, becomes live). With the
  prefix → `whatsapp_e164`, as today. Channel of arrival decides,
  so one number in both columns of different parents cannot cross.
- `OptOutType=STOP` → set `parents.sms_opted_out_utc` (if null), one
  `ops_alerts` row kind `sms_opt_out`, and it is NOT a reply: no ask
  is marked answered, nothing is cancelled.
- `OptOutType=START` (or UNSTOP/YES) → clear `sms_opted_out_utc`, one
  ops_alerts row kind `sms_opt_in`. Not a reply either.
- `OptOutType=HELP` → nothing recorded. Not a reply.
- No `OptOutType` → a reply, exactly as today (`record_parent_reply`).
- Send-time error 21610 (recipient has opted out) → treat as STOP
  arrived: set `sms_opted_out_utc` if null, ledger status `failed`,
  one ops_alert. Scheduler then skips per A.2 with a quiet recorded
  skip, no daily alert.
- Signature verification unchanged: same public URL, same auth token.

DEFERRED (founder, 2026-09-02): what the FAMILY sees when a parent
has opted out. v1 is founder-only ops_alert; the family surface is a
copy decision, not a build decision. Until ruled, an opted-out
parent's not-as-usual mornings produce no ask and therefore no
follow-on.

### A.6 Enrollment and consent (the LAW-6 question)

The carrier filing says consent is verbal at setup and recorded with
the parent's record. The setup flow therefore, for a parent being
enrolled by phone number without WhatsApp:

- shows the child the consent script VERBATIM (228), as words to say
  to the parent, not as a form;
- the single enrollment control for that parent reads "They said yes"
  and, on tap, stores `sms_consent_utc = now()` and queues
  `sms_welcome`;
- with no `sms_consent_utc`, the number is stored and nothing is ever
  sent (A.2 condition 2).

RATIFIED: this is the enrollment action itself, not a consent
ceremony; the founder ruling "no consent ceremony ever" forbids a
separate gate, not a truthful label on the button that enrols. No
extra screen, no checkbox. Rejected alternative: `sms_consent_utc`
set by the provisioning script from a founder-attested call.

### A.7 Data and config

- Migration 0024 (renumbered from 0023, which families.demo took first; DECISIONS 246) (Studio, founder): `parents.sms_consent_utc
  timestamptz null`, `parents.sms_opted_out_utc timestamptz null`.
  No RLS change; no grants.
- New kind constant `KIND_SMS_WELCOME = "sms_welcome"`; ledger and
  scheduler treat it as send-once.
- Secrets on kettle-api: `TWILIO_MESSAGING_SERVICE_SID`
  (= MG0e9fbf94ad89764c8a6f121f2027675c). OUTBOUND_TRANSPORT becomes
  `twilio_whatsapp,twilio_sms,resend`.

### A.8 Founder console tasks (before dark stage)

1. Messaging Services → the Aug 11 service → Integration: incoming
   messages → "Send a webhook", request URL
   https://kettle-api.fly.dev/outbound/reply, POST.
2. Same service → Opt-Out Management: Advanced Opt-Out on; STOP
   keywords default; HELP reply text = the filed HELP string (A.4).
3. Phone Numbers → +1 984 370 4452 → confirm the SMS "Registration
   required" flag is gone (DECISIONS 230 left it unverified).
4. Migration 0024 in Studio.
5. Secrets: `fly secrets set TWILIO_MESSAGING_SERVICE_SID=…` then
   OUTBOUND_TRANSPORT.
Report each as a triplet, per the 229 standing rule: a sender is not
live until its inbound has round-tripped.

### A.9 Tests (CC)

- Routing: each of the three A.2 outcomes, plus "+44 phone, no
  WhatsApp → skip", plus "opted out → skip, no alert".
- Payload: MessagingServiceSid present, no From, bare To, Body equals
  the ratified A.4 string byte for byte (named and fallback forms).
- Welcome: sent once; second run is a no-op; fallback name form.
- Inbound: OptOutType STOP/START/HELP paths and their non-reply-ness;
  plain reply from a phone-only parent matches by phone_e164;
  whatsapp-prefixed From still matches by whatsapp_e164; the same
  digits in both columns of two parents resolve by channel.
- 21610 handling.
- Signature check unchanged for SMS-shaped params.

### A.10 Dark stage for SMS (Phase 4)

On TestMom, founder temporarily sets `whatsapp_e164 = null` and
`sms_consent_utc = now()` in Studio (SQL from PM), so A.2 routes to
SMS. Verify in order, each with a screenshot and a ledger read:
welcome arrives; next quiet-morning ask arrives as SMS with the
ratified body; typed 👍 → `replied_utc` set, no follow_on; text STOP →
`sms_opted_out_utc` set, ask row NOT answered, ops_alert row; text
START → cleared; then restore `whatsapp_e164`. Result → one DECISIONS
entry. Only then does a real +1 parent get enrolled by SMS.

### A.11 Out of scope

Parent-facing reminder; cross-transport fallback; non-+1 SMS; MMS;
family-facing opt-out copy (A.5 open); SMS for digests or follow-on.
