# Wave D Phase 3 — dark-stage runbook (founder + PM)

Precondition: Phase 2 built, PM-reviewed, deployed to prod. Rehearsal
family's parent numbers point at Hema's own WhatsApp. Real family
stays on the sandbox until the flip decision at the end of this
runbook.

## The one pass that matters (a quiet morning on Rehearsal)

Arrange or wait for a quiet morning so the ask fires. Then verify, in
order, PIXELS FIRST:

1. **The message arrives** on Hema's WhatsApp FROM "HeyKettle" — the
   name shown is HeyKettle, not a bare number. Screenshot it.
2. **The copy is character-exact**: "Everything okay today? Reply
   with a 👍 whenever suits." with the button showing 👍 beneath it.
   Any drift = stop, do not tap, bring it back.
3. **Tap the button** (do not type). Expect: Kettle answers with
   NOTHING (silence by design), and the pending follow-on is
   cancelled — the child email at ask+2h must NOT arrive.
4. **Ledger check (PM, via MCP read)**: the send row names the real
   transport/template; the inbound row matches the parent and pending
   ask; timestamps sane in parent-local terms.
5. **ops_alerts**: none fired. If any did, each must be honest.
6. **Repeat next quiet morning with a TYPED 👍** instead of the
   button — same stand-down, same silence, same ledger shape.
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
