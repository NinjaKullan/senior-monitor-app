-- 0015 — delivery status on the outbound ledger (DECISIONS 157, Wave B tier).
--
-- A row used to exist only when a send was delivered, which made three real
-- outcomes unrepresentable: a transport that tried and failed, a send with
-- nowhere to go, and a send the engine deliberately withheld (the DECISIONS
-- 152 label skip, the staleness cutoff, the evidence gate). Each of those now
-- writes its row with a status, so the ledger the founder reviews (spec 007
-- §6.3) shows what the engine decided *not* to say and why the slot is empty —
-- and so the ops alerting can fire once per transition instead of once per
-- minutely pass.
--
-- 'sent' is final. 'failed' and 'skipped' are retryable: the unique slot is
-- claimed but a later pass may upgrade the row (kettle/db.py
-- record_sent_message carries the transition rule). Only 'sent' rows are
-- messages; every decision that reads the ledger — the sent-once check, the
-- follow-on's ask precondition, the reply matcher — counts 'sent' rows only.
--
-- The default backfills nothing in production (the loop has never run there,
-- DECISIONS 155) and keeps the dev path simple; code always writes the status
-- explicitly.
alter table sent_messages add column status text not null default 'sent'
    constraint sent_messages_status_known check (
        status in ('sent', 'failed', 'skipped')
    );
