-- 0031 — the family's own devices (spec 020, DECISIONS 311/312).
--
-- A smart plug, a door sensor, a motion sensor, a voice routine: something
-- already in the parent's home that can open a web address. Kettle records
-- which address and when, and says exactly that. Nothing here feeds the
-- engine: these are SEPARATE tables from `pings` on purpose, because the
-- engine, the heartbeat and the webapp's verdicts all read `pings`, and a
-- household ping in that table would move a verdict (311 forbids it).
--
-- 0004 doctrine: no client insert or update. Writes go through three
-- SECURITY DEFINER functions for admins of the parent's circle. The token is
-- the device's address and never reaches `authenticated`: the table itself
-- carries no grant at all, the family reads `household_devices_view` (the
-- same rows without the token, scoped to the caller's circles), and the
-- token comes back only from app_household_device_address.

create table household_devices (
    id          uuid primary key default gen_random_uuid(),
    parent_id   uuid not null references parents(id),
    kind        text not null
                check (kind in ('plug', 'door', 'motion', 'voice', 'fridge', 'light')),
    platform    text
                check (platform is null or platform in
                       ('home_assistant', 'ifttt', 'smartthings', 'alexa', 'google_home', 'other')),
    -- Same shape as devices.device_token: the address is the credential.
    token       text unique not null check (token ~ '^[A-Za-z0-9_-]{20,}$'),
    created_utc timestamptz not null default now(),
    removed_utc timestamptz
);

create index household_devices_parent_idx on household_devices (parent_id);

create table household_pings (
    id        bigint generated always as identity primary key,
    device_id uuid not null references household_devices(id),
    -- The whole record: which address, when. No IP, hashed or plain; no body.
    ts_utc    timestamptz not null default now()
);

create index household_pings_device_ts_idx on household_pings (device_id, ts_utc desc);
create index household_pings_ts_idx on household_pings (ts_utc);

alter table household_devices enable row level security;
alter table household_pings enable row level security;

-- The caller's devices, by circle: the one place the family-to-device join
-- is written, used by the view and the pings policy alike. SECURITY DEFINER
-- so the policy can consult a table `authenticated` holds no grant on.
create or replace function public.app_household_device_ids()
returns setof uuid
language sql
stable
security definer
set search_path = public, auth
as $$
    select d.id
    from household_devices d
    join parents p on p.id = d.parent_id
    where p.family_id in (select public.app_current_family_ids());
$$;

revoke all on function public.app_household_device_ids() from public, anon;
grant execute on function public.app_household_device_ids() to authenticated;

-- household_devices: RLS on, no policy, no grant — service role only, like
-- the ledger. The family's read surface is the view below.
-- household_pings: family read through the device's parent's circle.
create policy household_pings_select_own_circle on household_pings
    for select to authenticated
    using (device_id in (select public.app_household_device_ids()));

grant select on household_pings to authenticated;

-- The read surface: every column but the token, the caller's circles only.
-- Owned by the migration's role (not security_invoker), so it can read a
-- table the caller cannot; the WHERE is the isolation.
create view household_devices_view as
    select d.id, d.parent_id, d.kind, d.platform, d.created_utc, d.removed_utc
    from household_devices d
    where d.id in (select public.app_household_device_ids());

revoke all on household_devices_view from public, anon;
grant select on household_devices_view to authenticated;

-- Admin of the parent's circle, or 42501 — the 017 shape.
create or replace function public.app_household_admin_check(p_parent_id uuid)
returns void
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    target parents%rowtype;
begin
    select * into target from parents where id = p_parent_id;
    if not found then
        raise exception 'not_admin' using errcode = '42501';
    end if;
    if not exists (
        select 1 from members
        where family_id = target.family_id and auth_user_id = auth.uid() and role = 'admin'
    ) then
        raise exception 'not_admin' using errcode = '42501';
    end if;
end;
$$;

revoke all on function public.app_household_admin_check(uuid) from public, anon, authenticated;

create or replace function public.app_add_household_device(
    p_parent_id uuid, p_kind text, p_platform text
)
returns uuid
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    new_id uuid;
begin
    perform public.app_household_admin_check(p_parent_id);
    if p_kind is null or p_kind not in ('plug', 'door', 'motion', 'voice', 'fridge', 'light') then
        raise exception 'unknown_kind' using errcode = '23514';
    end if;
    if p_platform is not null and p_platform not in
        ('home_assistant', 'ifttt', 'smartthings', 'alexa', 'google_home', 'other') then
        raise exception 'unknown_platform' using errcode = '23514';
    end if;
    if (select count(*) from household_devices
        where parent_id = p_parent_id and removed_utc is null) >= 3 then
        raise exception 'device_limit' using errcode = '23514';
    end if;
    -- Two v4 UUIDs' worth of pg_strong_random, hyphens dropped: 64 hex
    -- characters, the devices.device_token shape, no extension needed.
    insert into household_devices (parent_id, kind, platform, token)
    values (
        p_parent_id, p_kind, p_platform,
        replace(gen_random_uuid()::text || gen_random_uuid()::text, '-', '')
    )
    returning id into new_id;
    return new_id;
end;
$$;

create or replace function public.app_remove_household_device(p_device_id uuid)
returns void
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    target household_devices%rowtype;
begin
    select * into target from household_devices where id = p_device_id;
    if not found then
        raise exception 'not_admin' using errcode = '42501';
    end if;
    perform public.app_household_admin_check(target.parent_id);
    -- The address stops in this instant; the pings stay for the sweep and
    -- are never shown again.
    update household_devices
    set removed_utc = coalesce(removed_utc, now())
    where id = p_device_id;
end;
$$;

create or replace function public.app_household_device_address(p_device_id uuid)
returns text
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    target household_devices%rowtype;
begin
    select * into target from household_devices where id = p_device_id;
    if not found then
        raise exception 'not_admin' using errcode = '42501';
    end if;
    perform public.app_household_admin_check(target.parent_id);
    if target.removed_utc is not null then
        raise exception 'removed' using errcode = '23514';
    end if;
    return target.token;
end;
$$;

revoke all on function public.app_add_household_device(uuid, text, text) from public, anon;
revoke all on function public.app_remove_household_device(uuid) from public, anon;
revoke all on function public.app_household_device_address(uuid) from public, anon;
grant execute on function public.app_add_household_device(uuid, text, text) to authenticated;
grant execute on function public.app_remove_household_device(uuid) to authenticated;
grant execute on function public.app_household_device_address(uuid) to authenticated;
