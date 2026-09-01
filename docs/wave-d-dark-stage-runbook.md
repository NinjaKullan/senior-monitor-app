# Wave D Phase 3 — dark-stage runbook (founder + PM)

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
2. **The copy is character-exact**: "Hi. Priya asked Kettle to check
   in with you when a morning looks different. Is everything okay?
   Reply with a 👍 when you're free." — the DECISIONS 221 wording,
   with {{1}} = the Rehearsal owner's first name (fallback "Your
   family"); the 206 sentence is retired. There is NO button (Meta forbids emoji in buttons, DECISIONS 205); a button
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
   ask and react with 👍 instead of replying. With no button, this is
   the likeliest thing a parent actually does, and reactions may not
   arrive as inbound messages at all. Whatever happens is a FINDING:
   if the ladder stands down, record it; if it does not (reaction
   never reaches the webhook), that goes in the Day-30 memo as the
   content-blind reply edge made concrete, and the flip decision
   weighs it.
7. **One negative pass**: a quiet morning where nobody replies — the
   ladder proceeds exactly as it does today (follow-on email at +2h,
   evening digest, escalation copy unchanged). The real number must
   not have changed one word of the ladder.

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

## Pass 1 result (2026-09-01) and the rollback law

Pass 1 FAILED for a structural reason, not a copy one: Twilio error
63049 — Meta blocks every Marketing-category template to US (+1)
numbers since 2025-04-01, and our approved template is Marketing
(207). See DECISIONS 216. Rolled back the same hour.

**Rollback = restore, never delete.** To leave the real number:
```
fly secrets unset TWILIO_ASK_CONTENT_SID --stage
fly secrets set TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```
NEVER `fly secrets unset TWILIO_WHATSAPP_FROM` — the transport
requires a sender and the app fails closed at startup without one.
One restart, one shortcut blip.

**Precondition added for any future pass:** the template in
TWILIO_ASK_CONTENT_SID must be UTILITY category (or the recipient
must be outside +1). A Marketing template cannot pass this runbook
for a US rehearsal phone, whatever else is right.

## Pass 2 setup (2026-09-01, v6 Approved as Utility)

`kettle_ask_parent_v6` = `HX61758012edba26686ec7ee361a0f493f`, Approved,
WhatsApp category **Utility** (PM read both fields on the template
page at 13:57 EDT; DECISIONS 222). The precondition above is met.
To enter the dark stage again, from `product/`, ONE command so the
app restarts once with both values:
```
fly secrets set TWILIO_WHATSAPP_FROM=whatsapp:+19843704452 TWILIO_ASK_CONTENT_SID=HX61758012edba26686ec7ee361a0f493f
```
TestMom already carries Hema's number (set Tue before pass 1) — no
address SQL this time, so the ordering law cannot bite. Next ask
fires 11:00 parent-local on the next quiet Rehearsal morning; the
verification list above applies unchanged, step 2 with the v6 copy.
Rollback is the block above, unchanged.
