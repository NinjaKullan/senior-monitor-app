-- 0013 — retire specs 003 and 004, superseded by 007 (DECISIONS 141).
--
-- ⚠️  READ BEFORE APPLYING. This migration does not touch `digest_sends`, and
--     that is deliberate: **the family app reads it.** `webapp/src/lib/
--     queries.ts` declares `digest_sends` in its READ_SURFACE and the Digests
--     screen renders from it. Spec 007's `sent_messages` is not a replacement —
--     it is RLS deny-all by design, so no client can read it at all. Dropping
--     or renaming `digest_sends` would empty a screen in a live app. Retiring
--     it is a webapp pass with a decision in front of it (give `sent_messages`
--     a family-scoped read policy and move the screen, or retire the screen),
--     not a line in a migration. DECISIONS 141 states the options.
--
-- What this does retire: the escalation ladder's own tables. Each is **checked,
-- not assumed** — the decision happens at apply time against the real database
-- rather than against anybody's memory of whether the ladder ever ran:
--
--   * never held a row  -> dropped outright.
--   * holds rows        -> renamed to `retired_<name>`, every policy on it
--                          dropped, and privileges revoked. The rows survive
--                          because they are history: shadow-mode ladder rows
--                          are the labelled ledger that was meant to tune the
--                          thresholds, and deleting them silently would be the
--                          wrong call to make on someone else's behalf.
--
-- `families.ladder_mode`, its CHECK, and the per-parent threshold columns 0007
-- added (`phone_e164`, `alarm_deadline`, `max_gap_minutes`, `grace_minutes`,
-- `family_gap_minutes`) are left in place. The ruling named tables; a column
-- drop is not reversible, `phone_e164` holds a real number the founder entered,
-- and nothing reads any of them once the ladder module is gone. They cost a few
-- bytes and can go in a later migration once 007's own contact fields have been
-- through a wave that actually sends.

do $$
declare
    target      text;
    archived    text;
    row_count   bigint;
    policy_name text;
begin
    -- Events before candidates: the first references the second.
    foreach target in array array['ladder_events', 'ladder_candidates', 'family_contacts']
    loop
        if to_regclass('public.' || target) is null then
            raise notice 'retire 003/004: % is already gone', target;
            continue;
        end if;

        execute format('select count(*) from %I', target) into row_count;
        archived := 'retired_' || target;

        if row_count = 0 then
            execute format('drop table %I cascade', target);
            raise notice 'retire 003/004: dropped % (never held a row)', target;
        else
            execute format('alter table %I rename to %I', target, archived);
            for policy_name in
                select policyname from pg_policies
                where schemaname = 'public' and tablename = archived
            loop
                execute format('drop policy %I on %I', policy_name, archived);
            end loop;
            execute format('alter table %I enable row level security', archived);
            execute format('revoke all on %I from anon, authenticated', archived);
            raise notice
                'retire 003/004: archived % as % (% rows kept, access revoked)',
                target, archived, row_count;
        end if;
    end loop;
end
$$;
