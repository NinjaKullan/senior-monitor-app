# Spec 007 — The outbound channel: Kettle learns to speak

*PM: Fable, 2026-08-21. The site promises "you hear twice a day" and "asks them first,
quietly." This spec makes both true. The ladder's first two rungs, built in waves so the
core ships before any external dependency lands. DECISIONS numbering continues from the
live file's counter.*

## 1. What it is

Three message kinds, and nothing else speaks:

- **The digest** (to the child, twice daily): a short reassurance message. Morning edition
  says the day started; evening edition says the day happened. Never a feed, never a
  score, never a graph — the site's own words are the contract.
- **The ask** (to the parent, on a quiet morning): English plus a universal icon a
  parent who reads no English can still act on: "Everything okay today? Reply with a 👍
  whenever suits." (DECISIONS 150/151; the site's older quote of this string is
  illustrative, not binding). Addressed to the parent, never about them. Parent-first
  is law #6's ladder made real.
- **The follow-on** (to the child, only after the ask has gone unanswered AND signals
  stay silent past a grace window): the only message that ever tells a child about a
  quiet day, and it reports facts, not verdicts.

## 2. The decision core (Wave A — no external dependencies, buildable now)

1. **Quiet-morning evaluation.** A day is "quiet so far" for a parent when no
   ALARM_GRADE signal has arrived between the morning-window start and the ask
   threshold, both in the parent's provisioned timezone. v1 constants (per-family
   config is a later spec): window opens 06:00, ask threshold 11:00, follow-on grace
   2 hours. Charger signals never count toward "the morning happened" (vocabulary law:
   charger is not alarm-grade); they exist for the health surface, not the ladder.
2. **The scheduler.** Computes, per family per day: morning digest time, evening digest
   time (v1: 08:30 and 20:30 in the family timezone — v1 rule: family timezone = the
   parents' provisioned timezone; execution call, cheap to overrule), ask threshold,
   follow-on deadline. All arithmetic in UTC against per-tz windows; DST handled by the
   tz database, not by offsets.
3. **The sent-once ledger.** Migration 0012: a `sent_messages` table — family, date
   (parent-local), message kind, template id, transport, sent_at — with a UNIQUE
   constraint on (family, date, kind) so a crashed-and-restarted scheduler cannot
   double-send. RLS deny-all, service-role writes only, same posture as waitlist.
   No message body is ever stored: templates are code, the ledger stores the template
   id. Three-fields law untouched — this table records that Kettle spoke, not what
   anyone did.
4. **The template registry.** Every message is a named template in one module,
   copy-law-scanned like site copy (no alarm vocabulary, no verdicts about a person,
   no counts, no signal names, no mechanism). Digest morning/evening, the ask, the
   follow-on. Suggested v1 bodies below (§5); PM owns the words, founder approves.
5. **The transport seam.** A `Transport` interface: send(to, template_id, variables) →
   delivery result. Wave A ships with a console/log transport only — the whole engine
   runs "dark" in production, writing its ledger, sending nothing. **The dark run does
   not wait for a real transport: Wave A IS the scheduler loop running in production**
   (DECISIONS 154) — an in-process background task like the heartbeat monitor, gated
   on `OUTBOUND_LOOP`, with `OUTBOUND_ENABLED` as the live kill switch on the
   decisions themselves. Transport selection is config (`OUTBOUND_TRANSPORT`) against
   a closed registry with "console" as the only entry; an unknown name refuses to
   boot, so a misconfiguration can never fail open into something that sends. That is
   the acceptance path: watch the ledger match reality for the founder family for two
   days before any real message goes out.
6. **Reply intake (minimal).** A webhook endpoint that records "the parent replied"
   (timestamp only, never content) and cancels a pending follow-on. Intake is
   content-blind: a thumbs-up, a voice note, or a sentence in any language all count
   as "answered" — nothing parses content (DECISIONS 150). **The matching rule
   (DECISIONS 153, repairing the 145 defect):** a reply matches the parent's
   *pending* ask — the most recent ask that is (a) sent, (b) unanswered, (c) whose
   follow-on has not yet been sent — regardless of calendar day, bounded to asks
   sent within the last 24 hours. No pending ask in that window: the arrival is
   noted (timestamp only), nothing is cancelled, nothing escalates because of it.
   Matching by the parent's local calendar day is the ruled-out shape: an ask
   answered just after local midnight is the same conversation, and escalating over
   a parent who answered is worse than a missed message. **Wave C's inbound
   credential is Twilio's own request signature** (DECISIONS 163): HMAC-SHA1 over
   the public URL and sorted form params, constant-time compared, failing closed on
   any missing piece; the shared secret stays as the break-glass path, and with
   neither configured the route does not exist. The reply body participates in
   signature verification and is then discarded — content-blind survives the
   real channel.
7. **The engine reports what it withholds (DECISIONS 157/159, built with Wave B).**
   The ledger row carries a status — 'sent' is final; 'failed' and 'skipped' claim
   the day's slot but stay retryable — and every non-sent outcome fires one founder
   ops alert on the transition (ntfy + `ops_alerts`, law #3; alert copy is
   operational and may name mechanisms). Four withhold rules: a morning digest
   decided more than two hours past its slot is never sent late; the evening-normal
   body renders only from a day with at least one alarm-grade signal (a zero-signal
   day is an ops condition, not a family message — the morning quiet-so-far path is
   honest absence and stands); a relationship-bearing template with no label waits
   (DECISIONS 152); a kind the transport does not carry, or an address-requiring
   transport with no address, is a recorded skip, never an attempt. Only 'sent'
   rows count anywhere a row means "Kettle spoke" — the sent-once check and the
   reply matcher — with one ruled exception (DECISIONS 163, amending 159): the
   follow-on's precondition reads the ask's row at ANY status, so an ask that
   could not be sent still escalates on the clock and a missing phone number can
   never silently disable the ladder.

## 3. The transports (Waves B–D, each gated on one founder errand)

- **Wave B — email digest via Resend** (gated on: the domain). The child's digest goes
  to their account email. SMTP/API keys via Fly secrets; delivery tracking off; the
  sending subdomain per the SMTP plan doc (which updates Postmark→Resend in this pass).
  This makes "you hear twice a day" TRUE for the founder family before WhatsApp exists.
  **Code-complete (DECISIONS 159):** the `resend` transport is registered — digests
  only, address-required, fail-closed without `RESEND_API_KEY` — and asks/follow-ons
  record as skipped with a founder alert until Wave C gives them a channel. The
  deployed config stays `console` until the founder flips `OUTBOUND_TRANSPORT` after
  the Wave A ledger review (§6.3); the flip is two Fly secrets, no deploy.
- **Wave C — WhatsApp via Twilio sandbox** (gated on: Twilio account, ~an hour). The
  sandbox lets named testers join with a code — good enough for the founder family.
  The ask goes to the parent on WhatsApp; the reply hits the webhook. Rung 1 live.
  **Code-complete (DECISIONS 163):** the `twilio_whatsapp` transport carries the ask
  and nothing else (the sandbox is a parent-side channel; the follow-on and
  all-clear travel by email — resend's kinds widened accordingly); the reply webhook
  verifies Twilio's request signature against the public URL; the follow-on
  escalates on the clock whatever became of the ask; the unreachable-phone
  distinction and the all-clear (161's bodies 7 and 6) are live in the engine. The
  flip is `OUTBOUND_TRANSPORT=twilio_whatsapp,resend` — a comma roster, first-match
  by kind — plus the three Twilio secrets; console stays the deployed default until
  the founder flips after the Wave A review.
- **Wave D — WhatsApp Business sender** (gated on: display-name approval + template
  registration with WhatsApp, the long pole — start the founder errand early).
  Business-initiated WhatsApp messages outside a 24h session REQUIRE pre-approved
  templates; our template registry maps 1:1 onto that requirement by design. Stranger
  families ride only on Wave D.

## 4. Contact data

Rung 1 needs the parent's phone number — deliberately never collected until now.
Migration 0012 adds `family_contacts` (or extends the parent record; implementer's
call): parent WhatsApp number, child digest address, both service-role-only, RLS
deny-all, entered at provisioning by the founder for beta. The privacy policy already
covers account contact data for the child; the parent's number is setup-surface
disclosure (behind the expiring link), consistent with what-never-how.

## 5. Message copy, v1 (founder-approved 2026-08-23 — DECISIONS 149, 150, 151)

`{relationship}` is the label the child picks at setup from the standard set (Mom,
Dad, Grandma, Grandpa, Aunt, Uncle; extendable) — never a given name or a family's
own pet name, because Kettle cannot know what a family calls their elders (149,
superseding this section's original `{parent_name}`). Pronouns are never guessed:
singular they, or the sentence is restructured to need none (149, closing DECISIONS
24). No em dashes in any body (151, extending 127 to product copy).

- Digest, morning, normal: "{relationship}'s morning looked like a normal morning.
  Next note this evening."
- Digest, evening, normal: "An ordinary day, start to finish. Next note in the morning."
- Digest, morning, quiet-so-far (sent only if digest time lands before the ask
  threshold on a quiet day): "Quiet so far this morning. Kettle will check in with
  {relationship} first if that continues."
- The ask (to the parent; the 👍 is 150's universal icon, and the site's quote of the
  older string is illustrative, not binding): "Everything okay today? Reply with a 👍
  whenever suits."
- Follow-on (to the child, facts only): "{relationship}'s usual morning hasn't shown up
  today, and they haven't answered Kettle's note yet. You know their day best. A call
  from you beats anything Kettle can send."
All templates through the copy-law scan; the follow-on's last sentence is the ladder's
handoff — Kettle stops speaking where the family starts.

## 6. Requirements & acceptance

1. Fake-clock test suite drives whole days: normal day → two digests, no ask; quiet
   morning + signal at 10:40 → no ask; quiet past threshold → ask, then parent reply →
   no follow-on; quiet + no reply → follow-on at deadline. Every path asserts the
   ledger's uniqueness holds under a double-run of the scheduler.
2. Copy law extended to the template registry; plants for a verdict, a count, and a
   signal name inside a template.
3. Founder family runs Wave A dark for 48h; ledger review is the gate to Wave B.
4. Laws hold: no inference (quietness is reported as absence, never interpreted),
   three fields stored, household signals never speak for a person, parent-first
   ordering enforced by construction (follow-on cannot exist without a prior ask row).
5. Suites green, ruff clean, pilot untouched.

## 7. Non-goals (v1)

Per-family threshold config UI; learned cadences; multiple children per family; digest
localization; the native app; SMS fallback; quiet-hours customization; Q108 timezone
edit (display-only stands). Filed, not forgotten.
