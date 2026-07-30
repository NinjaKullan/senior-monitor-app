-- LOCAL / CI ONLY — never apply this to a real Supabase project.
--
-- Supabase hands you the `auth` schema, `auth.uid()`, and the anon/authenticated/
-- service_role roles. A bare Postgres container does not, so the numbered
-- migrations would fail on the first GRANT. This file creates just enough of
-- that surface for the real migrations to run unchanged, which is what makes the
-- RLS tests a genuine test of the shipped policies rather than of a local rewrite
-- of them.
--
-- auth.uid() below is the same expression Supabase uses: the `sub` claim of the
-- request JWT, published to the session as `request.jwt.claims`.

create schema if not exists auth;

create table if not exists auth.users (
    id    uuid primary key,
    email text
);

create or replace function auth.uid()
returns uuid
language sql
stable
as $$
    -- nullif the *setting* before casting: an unauthenticated session leaves
    -- request.jwt.claims as the empty string, and ''::jsonb is an error, not a
    -- null. Supabase's own definition guards it in exactly this order.
    select nullif(
        nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub',
        ''
    )::uuid;
$$;

do $$
begin
    create role anon nologin;
exception when duplicate_object then null;
end
$$;

do $$
begin
    create role authenticated nologin;
exception when duplicate_object then null;
end
$$;

-- The service role bypasses RLS in Supabase; mirror that locally so the
-- ingestion service behaves the same way in tests as in production.
do $$
begin
    create role service_role nologin bypassrls;
exception when duplicate_object then null;
end
$$;

grant usage on schema auth to anon, authenticated, service_role;
grant execute on function auth.uid() to anon, authenticated, service_role;

-- Supabase grants USAGE on the public schema to all three roles, and configures
-- default privileges so every function created there is granted EXECUTE to them
-- at creation time.
--
-- Reproducing both matters. The EXECUTE grant is *direct*, so `revoke all ...
-- from public` does not remove it — without this line 0003 would look like a
-- no-op in tests while being load-bearing in production. And without the schema
-- USAGE, an anon test would pass because anon cannot see `public` at all, which
-- is the right answer for the wrong reason.
grant usage on schema public to anon, authenticated, service_role;

-- The bootstrap grants the full privilege set on tables and sequences too, not
-- just EXECUTE on functions — which is how anon ended up holding TRUNCATE on
-- every table in production. 0004 strips all of it; reproducing the grants here
-- is what makes that migration testable instead of vacuous.
alter default privileges in schema public
    grant all on tables to anon, authenticated, service_role;

alter default privileges in schema public
    grant all on sequences to anon, authenticated, service_role;

alter default privileges in schema public
    grant all on functions to anon, authenticated, service_role;
