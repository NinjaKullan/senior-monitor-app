-- 0002 — Row Level Security (spec 002 §2).
--
-- Isolation between families is structural, not app-code courtesy. Every policy
-- here resolves the caller's families from their Supabase Auth user id, so a JWT
-- for family A cannot read family B's rows no matter what the API layer does or
-- forgets to do. There is no client yet; the policies land now precisely so that
-- the future PWA (spec 005) inherits isolation rather than being trusted with it.

-- Which families does the current JWT belong to?
--
-- SECURITY DEFINER on purpose: this reads `members`, which is itself RLS
-- protected, and a policy that queried `members` directly would recurse.
create or replace function public.app_current_family_ids()
returns setof uuid
language sql
stable
security definer
set search_path = public, auth
as $$
    select m.family_id
    from public.members m
    where m.auth_user_id = auth.uid();
$$;

revoke all on function public.app_current_family_ids() from public;
grant execute on function public.app_current_family_ids() to authenticated;

alter table families       enable row level security;
alter table members        enable row level security;
alter table parents        enable row level security;
alter table devices        enable row level security;
alter table parent_signals enable row level security;
alter table pings          enable row level security;
alter table ops_alerts     enable row level security;

-- Directly family-scoped tables.
create policy families_own_family on families
    for select to authenticated
    using (id in (select public.app_current_family_ids()));

create policy members_own_family on members
    for select to authenticated
    using (family_id in (select public.app_current_family_ids()));

create policy parents_own_family on parents
    for select to authenticated
    using (family_id in (select public.app_current_family_ids()));

-- Tables scoped through a parent.
create policy devices_own_family on devices
    for select to authenticated
    using (parent_id in (
        select p.id from parents p
        where p.family_id in (select public.app_current_family_ids())
    ));

create policy parent_signals_own_family on parent_signals
    for select to authenticated
    using (parent_id in (
        select p.id from parents p
        where p.family_id in (select public.app_current_family_ids())
    ));

create policy pings_own_family on pings
    for select to authenticated
    using (parent_id in (
        select p.id from parents p
        where p.family_id in (select public.app_current_family_ids())
    ));

-- ops_alerts is deliberately policy-free: RLS is on and nothing is granted, so
-- no end-user role can read it. Ops alerts are the founder's plumbing log, not
-- family-facing content (product law #3).

grant usage on schema public to authenticated;
grant select on families, members, parents, devices, parent_signals, pings to authenticated;

-- Reads only. Spec 002 has no client write path; ingestion runs as the service
-- role, which bypasses RLS.
revoke insert, update, delete on all tables in schema public from authenticated;
