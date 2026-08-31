# Wave D Phase 2 — CC handoff (PRE-DRAFTED, gated)

GATE: paste this to CC only after the template kettle_ask_parent_v4
shows **Approved** in Twilio (Content Template Builder → template →
WhatsApp approval status). v1 and v2 are dead — Meta forbids emoji
in buttons (DECISIONS 205). v4 carries the founder's reworded ask
(DECISIONS 206) and is the shipping template; v3 (older wording) is
in review only as fallback and ships ONLY on a fresh founder ruling.
If v4 shows Rejected or Paused instead, STOP — bring the exact
reason text back to the PM.

Also required first: PM records the approved copy verbatim in
DECISIONS (pull, then next free counter) — PM does this, not CC.

--- paste below this line ---

Push needed: no — main carries spec 011 (ratified, 193), the ladder
audit (194), Phase 0 completion (196), and the signed-off submission
page (docs/whatsapp-ask-template-submission.md). The template is now
APPROVED by Meta.

Build Phase 2 of spec 011 §4, exactly as written there. The specifics
that were placeholders are now real:

- WhatsApp sender (real number): +19843704452, WABA 1778487076826507.
- Approved template: kettle_ask_parent_v4, Content SID
  HXdb4e38c90d0ccc51bbcd264a002d0a8a, language en, approved category
  Marketing (submitted Utility; Meta recategorized at approval —
  DECISIONS 207; nothing in code branches on category),
  zero variables, type twilio/text — NO buttons (DECISIONS 205:
  Meta forbids emoji in buttons; parents reply with 👍 themselves,
  as the body invites). Body per DECISIONS 206: "Everything okay
  today? Reply with a 👍 when you're free." Build nothing that
  expects a button payload; the reply arrives as an ordinary
  inbound message.
- Config, never code: the real-number `from` and the Content SID land
  in config; sandbox settings REMAIN present and functional behind
  config until Phase 3 sunset. Nothing in this build touches the
  sandbox path's behavior.
- Send path: business-initiated asks on the real number use the
  template API (Content SID, no variables). Transport, webhook,
  parsing, ledger, idempotency untouched except where a template call
  differs from a body send.
- Failure honesty: a template send rejected, or the template later
  paused/disabled by Meta, writes an ops_alert and ntfy. A parent
  silently not asked is the one failure Kettle must never absorb
  quietly.
- Tests per spec 011 §4: template-send path with SID; sandbox
  behavior unchanged when config says sandbox; 👍 inbound identical
  for typed and button replies; copy scan over any new strings;
  ledger rows name the transport actually used. Plant-and-revert
  where the spec's claims are load-bearing.
- Do NOT flip any family to the real number. Dark stage (Phase 3) is
  a separate order after PM review of this build.

Commit and push; PM reviews from the pushed repo against spec 011 §4
and DECISIONS 194's audit before anything runs dark.
