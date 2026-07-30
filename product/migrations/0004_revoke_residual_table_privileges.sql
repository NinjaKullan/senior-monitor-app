-- 0004 — strip the residual table/sequence privileges Supabase's bootstrap left
-- on `anon` and `authenticated`.
--
-- NOTE FOR REVIEW (Claude Code, 2026-07-29): the PM's message pasted a
-- placeholder rather than the SQL they ran against production, so the statements
-- below are written to reach the END STATE they specified, not copied from that
-- run. The end state is asserted by tests:
--   * anon holds zero privileges on every public table and sequence
--   * authenticated holds exactly SELECT on the six family tables
--   * authenticated holds nothing at all on ops_alerts
-- Diff this against what was applied to production and replace it verbatim if
-- the statements differ; see specs/QUESTIONS.md item 21.
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
alter default privileges in schema public revoke all on tables from anon, authenticated;
alter default privileges in schema public revoke all on sequences from anon, authenticated;
alter default privileges in schema public revoke all on functions from anon, authenticated;
