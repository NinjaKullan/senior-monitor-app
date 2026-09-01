# US A2P 10DLC — brand and campaign notes (PM, 2026-09-01; DECISIONS 216 option B)

Why: +1 984-370-4452 shows "Messaging disabled — Complete A2P
registration". No SMS reaches a US phone from it until a 10DLC brand
and campaign are approved. This is the SMS fallback for US parents,
since Meta blocks Marketing templates to US numbers (216).

## Status 2026-09-01 ~3:45pm ET: PAUSED at the review screen — root
cause found (DECISIONS 226). The Trust Hub primary profile is an
INDIVIDUAL profile (the founder personally), so the wizard was
registering a Sole Proprietor brand and never asked for an EIN. Do
NOT submit. Path chosen from 226: ask Twilio support to convert/
replace the primary profile with a Business profile for LINKABIT AI
LABS LLC (type LLC, EIN, business address), then rerun the wizard on
the Standard track. Earlier notes kept below for the record.

## Status 2026-09-01 ~1:30pm ET: BLOCKED on Twilio's side

Brand registration cannot start: the onboarding checklist's brand step
returns "An unexpected error occurred while setting up your A2P Brand
registration", and Trust Hub → Compliance profiles → Primary shows
"Failed to load compliance profile" — Twilio cannot read this
account's primary Customer Profile, which brand registration requires
(the checklist nevertheless marks the profile "Complete"). Twilio
status: Trust Hub operational, so this is account-specific. Founder:
retry in a few hours; if it persists, Twilio support ticket quoting
both error strings. Nothing below changes.

## Brand registration (founder enters; PM does not handle identifiers)

- Legal name as on tax records: LINKABIT AI LABS LLC (footer:
  "HeyKettle · a LINKABIT AI LABS LLC service"). Brand type: Standard
  (low-volume) — a private US LLC with an EIN. Website:
  https://heykettle.com. Vertical: closest honest fit is
  "Technology" or "Communication"; do NOT choose "Healthcare" (Kettle
  is not a medical service and says so). Stock symbol: none.
- Expect a one-time brand fee and a small monthly campaign fee;
  approval is usually days, vetting can take longer.

## Campaign (paste-ready text, Kettle register, copy-law clean)

**Use case:** Account Notifications (or "Low Volume Mixed" if the
form insists on multiple). Not Marketing. Messages are service
notifications to a person who set the service up for themselves.

**Campaign description:**
HeyKettle is a family service. An adult child sets it up for a
parent, and the parent agrees to it during setup. When the parent's
normal morning has not started as usual, HeyKettle sends the parent
one short text asking whether everything is okay; the parent replies
with a thumbs-up or ignores it. Messages are sent only to phone
numbers the family entered during setup, at most once per day, and
never contain promotions or offers.

**Sample message 1** (the v7 ask, DECISIONS 225, + STOP line):
Hi. {{1}} asked Kettle to check in with you when your morning is not
as usual. Is everything okay? Reply with a 👍 when you can.
Reply STOP to end these texts.

**Sample message 2** (the fallback form):
Hi. Your family asked Kettle to check in with you when your morning
is not as usual. Is everything okay? Reply with a 👍 when you can.
Reply STOP to end these texts.

**How end users opt in (message flow):**
The parent's phone number is entered by a family member during a
setup call, and the parent confirms in person or by phone that they
want HeyKettle's texts before any message is sent. Consent is
recorded with the parent's record at setup. There is no web form
that adds a number without the parent's agreement.

**Opt-in keywords:** none (consent is given at setup, not by
keyword).  **Opt-out:** STOP (standard).  **Help:** HELP →
"HeyKettle: a family service. Questions: hello@heykettle.com.
Reply STOP to end these texts."

**Embedded links / phone numbers in messages:** No.  **Age-gated
content:** No.  **Direct lending:** No.

## The copy decision this creates (founder, when SMS is specced)

Carrier guidelines expect opt-out language ("Reply STOP to end these
texts.") in at least the first message and periodically after. That
sentence is not in the 217 ask. Options: (a) append it to SMS asks
only, always; (b) append it to the FIRST SMS ask a parent ever
receives, plus the HELP reply; (c) a one-time SMS welcome at setup
that carries the STOP line, so the daily ask stays the 217 body
verbatim. PM leans (c): honest, elder-friendly, and keeps the ask
identical across channels.
