-- 0004 — strip the residual table/sequence privileges Supabase's bootstrap left
-- on `anon` and `authenticated`.
--
-- This file is the canonical text (PM ruling, 2026-07-29). Production reached the
-- same end state in two steps — a differently-worded 0004 that revoked default
-- privileges from `anon` only, then a follow-up applying the both-roles form
-- below — and has been converged to this. See specs/QUESTIONS.md item 22.
--
-- End state, asserted by tests rather than described:
--   * anon holds zero privileges on every public table and sequence
--   * authenticated holds exactly SELECT on the six family tables
--   * authenticated holds nothing at all on ops_alerts
--
-- Why this is needed: Supabase's project bootstrap sets default privileges that
-- grant the FULL privilege set on new public-schema objects to anon,
-- authenticated and service_role. RLS is not a complete answer to that:
--   * TRUNCATE is not row-level and RLS does not govern it at all — anon holding
--     TRUNCATE on `pings` is a data-loss primitive, not a read risk.
--   * REFERENCES and TRIGGER let a role attach objects to our tables.
--   * SELECT on `ops_alerts` was blocked only by that table having no policy,
--     which is one gate where the design intends none at all (product law #3:
--     ops alerts are the founder's plumbing log).
-- 0002 revoked INSERT/UPDATE/DELETE from `authenticated` only, and revoking from
-- PUBLIC never touches these direct role grants.

-- anon is the pre-login role. It needs nothing here, ever.
revoke all on all tables in schema public from anon;
revoke all on all sequences in schema public from anon;

-- authenticated keeps exactly one thing: SELECT on the family-scoped tables,
-- filtered by the RLS policies in 0002.
revoke truncate, references, trigger on all tables in schema public from authenticated;
revoke insert, update, delete on all tables in schema public from authenticated;
revoke all on all sequences in schema public from authenticated;

-- ops_alerts is service-only: no policy, and now no privilege either.
revoke all on ops_alerts from authenticated;

-- Stop the bootstrap defaults from re-granting all of this to the next table,
-- sequence or function anyone creates. From here, access is explicit or absent.
--
-- These affect only defaults owned by the role running the migration (postgres,
-- implicitly — equivalent to `for role postgres`). A hosted Supabase project also
-- carries default-ACL rows owned by `supabase_admin` that still name anon and
-- authenticated; those govern objects the platform creates, not ours, and cannot
-- be altered from the postgres role. Auditing `pg_default_acl` after this
-- migration, filter on the migrating role or those rows will look like a failure.
alter default privileges in schema public revoke all on tables from anon, authenticated;
alter default privileges in schema public revoke all on sequences from anon, authenticated;
alter default privileges in schema public revoke all on functions from anon, authenticated;
