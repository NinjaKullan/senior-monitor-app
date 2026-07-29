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
