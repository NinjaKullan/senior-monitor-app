-- 0020 — the journal learns what KIND of line each entry is (spec 012 §5).
--
-- Kettle begins writing a few warm lines of its own into the family's
-- journal (spec 012 §3), and the feed needs to know a Kettle line from a
-- family note without parsing bodies. 'note' is every family-authored entry;
-- the auto kinds are the gentle-whats set, closed by a check constraint so a
-- fifth kind is a migration, not a typo.
--
-- The backfill: the only Kettle-authored rows that exist predate this column
-- and are all the city auto-note (spec 010 §4), so they become city_change.
-- Insert-only posture is UNCHANGED — no update, no delete; a correction is a
-- new entry.

alter table journal_entries add column kind text not null default 'note'
    constraint journal_entries_kind_check
    check (kind in ('note', 'city_change', 'started', 'first_reply', 'clean_month'));

update journal_entries set kind = 'city_change' where author_label = 'Kettle';

-- Idempotency at the schema, not in loop memory (the tz-alert precedent):
-- started and first_reply are once EVER per parent; clean_month is once per
-- (parent, month), keyed by event_date = the first day of the month the line
-- describes. The writer inserts ON CONFLICT DO NOTHING against these, so a
-- rerun, a crash-and-restart, or two schedulers racing all land one row.
create unique index journal_auto_once
    on journal_entries (parent_id, kind)
    where kind in ('started', 'first_reply');

create unique index journal_auto_month
    on journal_entries (parent_id, kind, event_date)
    where kind = 'clean_month';
