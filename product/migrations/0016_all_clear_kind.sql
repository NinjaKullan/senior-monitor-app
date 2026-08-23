-- 0016 — the ledger learns the all-clear (DECISIONS 157/161, Wave C).
--
-- A fifth message kind is a spec change, and this is that change arriving in
-- the schema: after a follow-on has gone out, the first alarm-grade signal of
-- the day sends the all-clear to the child, once. The ledger row IS the
-- resolution record — one 'all_clear' row per (family, parent, local day)
-- under the same unique index, so resolution bookkeeping needs no new table.
--
-- Postgres auto-named the original inline check; the drop uses that name and
-- the replacement is named explicitly so the next widening reads better.
alter table sent_messages drop constraint sent_messages_kind_check;
alter table sent_messages add constraint sent_messages_kind_check check (
    kind in ('digest_morning', 'digest_evening', 'ask', 'follow_on', 'all_clear')
);
