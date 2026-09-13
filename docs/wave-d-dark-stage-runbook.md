# Wave D Phase 3 — dark-stage runbook (founder + PM)

> **Status (DECISIONS 336, 2026-09-13).** The flip is done: the ask has run
> from the real HeyKettle number since 2026-09-04 (263), the clean week held,
> and the sandbox is retired from the everyday story. Its rollback is no longer
> a re-point to the sandbox — it is the **fail-loud posture** below, with the
> sandbox kept joinable only as **time-boxed break-glass** through the first
> stranger family's first clean week. The "one pass", Pass 1 and Pass 2
> sections are the **record of how the flip was done**, not a live procedure;
> read them for the reasoning, act on the rollback and break-glass sections.
> v6 stays approved in Twilio as break-glass; it is no longer the live template.

Precondition: Phase 2 built, PM-reviewed (209), deployed to prod.
Rehearsal parents' `whatsapp_e164` points at Hema's own WhatsApp —
VERIFY, don't assume: as of Aug 31 both Rehearsal parents had NO
number on file, so this is a real setup step (Hema, via Studio or
the app), and reply-matching keys on the same column.

Isolation caveat, decided with eyes open (see DECISIONS 210): the
two Fly secrets are GLOBAL — setting them moves every family's ask
to the real number at once; there is no per-family routing. The real
family's exposure is small (the ask rung is rare for them — roughly
one ask in two weeks, and any leak arrives as the approved copy from
"HeyKettle", i.e. the flip arriving early for one message) but it is
not zero. Keep the dark stage SHORT.

## The one pass that matters (a quiet morning on Rehearsal)

Arrange or wait for a quiet morning so the ask fires. Then verify, in
order, PIXELS FIRST:

1. **The message arrives** on Hema's WhatsApp FROM "HeyKettle" — the
   name shown is HeyKettle, not a bare number. Screenshot it.
2. **The copy is character-exact**: "Hi. Hema asked Kettle to check
   in with you when your morning is not as usual. Is everything
   okay? Reply with a 👍 when you can." — the DECISIONS 225 wording
   (v7), {{1}} = the Rehearsal owner's first name (fallback "Your
   family"); the 206 and 221 sentences are retired. There is NO
   button (Meta forbids emoji in buttons, DECISIONS 205); a button
   appearing is itself a stop signal. Any drift = stop, do not
   reply, bring it back.
3. **Reply by typing 👍** (just the emoji, nothing else). Expect:
   Kettle answers with NOTHING (silence by design), and the pending
   follow-on is cancelled — the child email at ask+2h must NOT
   arrive.
4. **Ledger check (PM, via MCP read)**: the send row names the real
   transport/template; the inbound row matches the parent and pending
   ask; timestamps sane in parent-local terms.
5. **ops_alerts**: none fired. If any did, each must be honest.
6. **Repeat next quiet morning with a REACTION 👍** — long-press the
   ask and react with 👍 instead of replying. RUN, ANSWERED: the
   reaction never arrives. See "A reaction is not a reply" below.
7. **One negative pass**: a quiet morning where nobody replies — the
   ladder proceeds exactly as it does today (follow-on email at +2h,
   evening digest, escalation copy unchanged). The real number must
   not have changed one word of the ladder.

### A reaction is not a reply (DECISIONS 247)

**A WhatsApp reaction never reaches the reply webhook. Only a typed
message does.** Proven on 2026-09-03: the ask was delivered at 11:00:49
ET, the founder long-pressed and reacted 👍 at about 11:51, and at 11:56
`replied_utc` was still null with no ops alert. A typed 👍 the day before
had matched within a second. The ladder ran on to the follow-on as a
no-reply day, which is correct behaviour on the evidence it had.

This is a Twilio Programmable Messaging property, not a Kettle bug: the
inbound webhook carries MESSAGES, and a reaction is not a message. It is
the edge DECISIONS 210 named, made real.

It cannot be fixed in copy. A quick-reply button would sidestep it, and
that was tried: v11 (v7 plus one "All good" button) came back
Marketing, as did v10, so iteration stopped and v7 stands (253). The
gap is closed by INSTRUCTION instead.

**So the parent instruction at setup is: "type the 👍, don't react."**
Say it while the phone is in your hand during setup, not in writing
afterwards. A parent who reacts is a parent Kettle believes did not
answer, and the family gets a follow-on about a morning that was fine.

## Watch items running in the background

- Meta quality rating on the sender stays green/none (Twilio senders
  list) — a dip during dark stage is a stop signal.
- Template status stays Approved (not Paused) all week.
- Sandbox family (real parents) completely unaffected throughout —
  their asks still ride the sandbox until the flip.

## The flip decision

After both reply modes + one no-reply ladder pass clean: PM writes
the flip order, Hema says go, config moves the REAL family to the
real number, and the first real ask after the flip is watched live,
same as Wave C's first ask. Sandbox sunsets after ONE CLEAN WEEK on
the real number, then DECISIONS records the retirement.

Every screenshot from this runbook goes into the Day-30 memo's
evidence pile.

## Rollback: fail-loud, with the sandbox as break-glass (DECISIONS 336)

The sandbox retirement removed the old one-command rollback (re-point
`TWILIO_WHATSAPP_FROM` to the sandbox number). That is deliberate. The
primary posture now is **fail-loud, which the system already does:** a
refused or undeliverable ask records a `failed` ledger row and fires an
ops alert carrying Twilio's own code and message (`outbound_whatsapp.py`
`_refusal`), and **everything child-facing stays on email regardless**, so
a broken WhatsApp sender never silences a family's digests or escalations.
What a broken sender costs is the parent *ask* until it is fixed — loudly,
not silently.

**Break-glass (time-boxed, through the first stranger family's first clean
week).** Only if the ask must go out while the real sender is broken: the
Twilio sandbox project is still joinable. Re-point the ask to it —

```
fly secrets unset TWILIO_ASK_CONTENT_SID --stage
fly secrets set TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

— which drops back to the body-send path (a registered template is not
used on the sandbox). NEVER `fly secrets unset TWILIO_WHATSAPP_FROM`: the
transport requires a sender and the app fails closed at startup without
one. Each parent must have re-joined the sandbox (sent the join code once)
before Twilio will deliver, so this is not instant. Undo it by setting the
real `TWILIO_WHATSAPP_FROM` and v7 SID back (the Pass 2 block below).
After the first stranger family's clean week, the sandbox project's
retirement gets its own DECISIONS line and this break-glass goes away.

**Precondition for any send from the real number:** the template in
`TWILIO_ASK_CONTENT_SID` must be UTILITY category (or the recipient must
be outside +1). A Marketing template cannot deliver to a US number (Meta,
error 63049; DECISIONS 216).

## How the flip was done (historical record)

*Pass 1 and Pass 2 below are the record of the Sep 1–4 flip, kept for the
reasoning. They are not a live procedure; the rollback above supersedes
their rollback language.*

Pass 1 FAILED for a structural reason, not a copy one: Twilio error
63049 — Meta blocks every Marketing-category template to US (+1)
numbers since 2025-04-01, and the then-approved template was Marketing
(207). See DECISIONS 216. Rolled back the same hour.

## A new outbound transport: deploy the code, then set the roster (DECISIONS 294)

`fly secrets set` restarts the machine on the image it is already running.
The transport registry is closed and refuses the boot on a name it does not
know (154/159), so an `OUTBOUND_TRANSPORT` roster that names a transport the
running image has never heard of restarts it into a refusal: the CLI waits on
health checks until they time out and nothing serves until `fly deploy`
replaces the image. That is what happened on Sep 5 when the roster gained
`twilio_sms` before the code that knew the name was live.

For any transport the running image does not carry, in this order:

1. `cd product && fly deploy` — the new code boots on the old roster, which it
   still understands.
2. `fly secrets set -a kettle-api OUTBOUND_TRANSPORT="..."` with the
   transport's own secrets in the same command, so a half-set roster never
   refuses the boot (`twilio_sms` without its Messaging Service SID does).
3. `curl -s -o /dev/null -w "%{http_code}" https://kettle-api.fly.dev/healthz`
   reads 200; the next engine pass logs the new leaf.

Rollback touches only the roster: set `OUTBOUND_TRANSPORT` back to the
previous value. The code can stay.

Same evening, the Twilio side: Advanced Opt-Out on a Messaging Service is not
on until the "Enable advanced opt-out" button has been pressed. A filled-in
keyword page is not enough, and Twilio's stock STOP confirmation arriving
instead of ours is the tell; until it is on, STOP and START reach
`/outbound/reply` without `OptOutType` and are read as replies.

## Pass 2 setup (2026-09-01, v6 Approved as Utility)

`kettle_ask_parent_v7` = `HX1ebee977bfd531bf7fdee2bf0d1484ad`, Approved,
WhatsApp category **Utility** (DECISIONS 225), was set live on Sep 1 and is
the ask today. v6 (`HX61758012edba26686ec7ee361a0f493f`) stays approved in
Twilio as break-glass only — it is not the live template. Secrets set Sep 1:
FROM = whatsapp:+19843704452, SID = v7 (swapped from v6 the same day):
```
fly secrets set TWILIO_WHATSAPP_FROM=whatsapp:+19843704452 TWILIO_ASK_CONTENT_SID=HX1ebee977bfd531bf7fdee2bf0d1484ad
```
That command is also how a break-glass sandbox re-point is undone (above).
TestMom already carried Hema's number (set Tue before pass 1) — no address
SQL this time, so the ordering law could not bite. The first real ask fired
11:00 parent-local on the next quiet Rehearsal morning; the verification
list above was walked with the approved copy.

### Sender-swap checklist

Pass 2 delivered cleanly and the first 👍 still recorded nothing: the
real sender's Messaging Endpoint Configuration in the Twilio console
was entirely empty, because the reply path had only ever been wired on
the sandbox (DECISIONS 229). Outbound proves nothing about inbound.
A sender swap is not done until all four are true:

1. **Outbound secrets set** — `TWILIO_WHATSAPP_FROM` and
   `TWILIO_ASK_CONTENT_SID` on kettle-api, and an ask seen delivered.
2. **Inbound webhook set on the NEW sender** — incoming message
   webhook = `https://kettle-api.fly.dev/outbound/reply`, method POST.
   It is per-sender: the sandbox's setting does not carry over, and an
   empty box looks exactly like a working one from the outside.
3. **One typed reply round-tripped** — send a 👍 from the parent's own
   phone and confirm `replied_utc` is set on that day's ask row. A
   delivered ask is not evidence the answer has anywhere to land.
4. **Only then is the swap done.** Until step 3 passes, treat the
   sender as outbound-only: a parent who answers is being ignored, and
   the follow-on will fire as though nobody replied.
