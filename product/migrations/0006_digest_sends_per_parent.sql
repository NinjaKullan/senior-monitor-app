-- 0006 — record every digest send against a specific parent (PM ruling on
-- DECISIONS.md item 27).
--
-- 0005 recorded an aggregated evening message as one row with a null parent_id,
-- which meant the unique index had to coalesce nulls to a sentinel uuid. Two
-- consequences, both fixed here: a family with two timezone groups that each had
-- two or more active parents produced two null-parent rows on the same
-- local_date and the second was silently blocked, and the audit could not say
-- which parents a given send actually covered.
--
-- Now: the delivered message is still aggregated per timezone group ("Amma and
-- Appa both had normal, active days."), but it is recorded once per included
-- parent per recipient. parent_id is NOT NULL for both kinds, the sentinel is
-- gone, and the collision cannot happen.
--
-- A separate migration rather than an edit to 0005 on purpose: this converges
-- the schema whether or not 0005 has already been applied anywhere. See
-- DECISIONS.md item 22 for why the repo no longer assumes.

-- Refuse rather than destroy. Aggregated rows can only exist if digests ran
-- under the 0005 shape; with DIGEST_ENABLED off by default there should be
-- none. If there are, they are send history and deleting them silently would be
-- the wrong call — decide deliberately, then re-run.
do $$
begin
    if exists (select 1 from digest_sends where parent_id is null) then
        raise exception
            'digest_sends still has aggregated rows (parent_id is null). These '
            'are send history from the 0005 shape and cannot be back-filled: '
            'which parents a row covered was never recorded. Archive or delete '
            'them deliberately, then re-run this migration.';
    end if;
end
$$;

alter table digest_sends alter column parent_id set not null;

drop index digest_once_idx;

create unique index digest_once_idx
    on digest_sends (family_id, parent_id, kind, local_date, member_id);
