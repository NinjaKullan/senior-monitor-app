-- 0025 — the circle (spec 015, DECISIONS 264/269).
--
-- A `families` row already IS a circle; what it lacked was a way to add and
-- remove people from inside the app and a way for one person to belong to
-- two. This migration gives `members` its two roles and its one mail switch,
-- and adds the five SECURITY DEFINER functions that are the ONLY write path
-- to membership. `members` gains no insert/update/delete policy: 0004's "no
-- client write to membership" stands, and every change below goes through a
-- function that resolves the caller's circles from the JWT, never from an
-- argument the caller could aim at someone else's household.
--
-- Roles: two, and only two (264). ADMIN adds and removes seats, changes
-- roles, and (later) the parents' numbers, timezone and the card. MEMBER
-- writes everything a family writes. `owner` becomes `admin`, `child`
-- becomes `member`; the check constraint follows. No read-only tier.
--
-- Mail: every member gets Kettle's mail unless they turn it off; one switch
-- per member, on their own row only (`mail`). `digest_channel` is untouched
-- (spec 015 §5: a cleanup item once nothing reads it).
--
-- ALSO: `digest_sends.kind` widens to the outbound kinds. Spec 015 §7 says
-- per-member idempotency for digests AND follow-ons rides `digest_sends`
-- "which 0006 already has" — but 0005's check constraint admits only
-- 'morning' and 'evening', the retired spec-003 vocabulary. Without this the
-- follow-on could not record a per-member row at all, and a circle of three
-- where one send failed would re-send to the other two on retry. The old
-- values stay admitted so no existing row breaks. Filed in the ledger as a
-- spec/code disagreement; the brief said "nothing else in the schema" and
-- this is the one exception, taken so §7 can be true.

-- 1. Roles.
alter table members drop constraint members_role_check;
update members set role = 'admin'  where role = 'owner';
update members set role = 'member' where role = 'child';
alter table members add constraint members_role_check check (role in ('admin', 'member'));

-- 2. The mail switch.
alter table members add column mail boolean not null default true;

-- 3. The per-member ledger admits the outbound kinds.
alter table digest_sends drop constraint digest_sends_kind_check;
alter table digest_sends add constraint digest_sends_kind_check check (
    kind in ('morning', 'evening', 'digest_morning', 'digest_evening', 'follow_on', 'all_clear')
);

-- 4. The functions. Every refusal raises with a short machine-readable
-- message the app can match on (not_admin, not_member, circle_full,
-- duplicate_email, last_admin, bad_role) and errcode 42501 (insufficient
-- privilege) for the two permission refusals, 23514 (check violation) for
-- the rule refusals — the same codes PostgREST already turns into 403 / 400.

create or replace function public.app_add_seat(
    p_family_id uuid, p_display_name text, p_email text
)
returns uuid
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    v_email text := lower(trim(p_email));
    v_id uuid;
begin
    if auth.uid() is null then
        raise exception 'not_member' using errcode = '42501';
    end if;
    if not exists (
        select 1 from members
        where family_id = p_family_id and auth_user_id = auth.uid() and role = 'admin'
    ) then
        raise exception 'not_admin' using errcode = '42501';
    end if;
    if v_email is null or v_email = '' or position('@' in v_email) = 0 then
        raise exception 'bad_email' using errcode = '23514';
    end if;
    if (select count(*) from members where family_id = p_family_id) >= 8 then
        raise exception 'circle_full' using errcode = '23514';
    end if;
    if exists (
        select 1 from members
        where family_id = p_family_id and email is not null and lower(email) = v_email
    ) then
        raise exception 'duplicate_email' using errcode = '23514';
    end if;
    insert into members (family_id, display_name, role, email, mail)
    values (p_family_id, nullif(trim(p_display_name), ''), 'member', v_email, true)
    returning id into v_id;
    return v_id;
end;
$$;

create or replace function public.app_remove_seat(p_member_id uuid)
returns void
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    target members%rowtype;
begin
    select * into target from members where id = p_member_id;
    if not found then
        -- Indistinguishable from "not yours": a probe learns nothing.
        raise exception 'not_admin' using errcode = '42501';
    end if;
    if not exists (
        select 1 from members
        where family_id = target.family_id and auth_user_id = auth.uid() and role = 'admin'
    ) then
        raise exception 'not_admin' using errcode = '42501';
    end if;
    if target.role = 'admin' and (
        select count(*) from members where family_id = target.family_id and role = 'admin'
    ) <= 1 then
        raise exception 'last_admin' using errcode = '23514';
    end if;
    delete from members where id = p_member_id;
end;
$$;

create or replace function public.app_set_role(p_member_id uuid, p_role text)
returns void
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    target members%rowtype;
begin
    if p_role not in ('admin', 'member') then
        raise exception 'bad_role' using errcode = '23514';
    end if;
    select * into target from members where id = p_member_id;
    if not found then
        raise exception 'not_admin' using errcode = '42501';
    end if;
    if not exists (
        select 1 from members
        where family_id = target.family_id and auth_user_id = auth.uid() and role = 'admin'
    ) then
        raise exception 'not_admin' using errcode = '42501';
    end if;
    if p_role = 'member' and target.role = 'admin' and (
        select count(*) from members where family_id = target.family_id and role = 'admin'
    ) <= 1 then
        raise exception 'last_admin' using errcode = '23514';
    end if;
    update members set role = p_role where id = p_member_id;
end;
$$;

-- Own row only, in the named circle: a person in two circles has two rows,
-- and the switch is per circle (spec 015 §6 wrote `app_set_mail(mail)`; the
-- circle id is added because "own row" is ambiguous for the in-laws case).
create or replace function public.app_set_mail(p_family_id uuid, p_mail boolean)
returns void
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    n integer;
begin
    update members set mail = p_mail
    where family_id = p_family_id and auth_user_id = auth.uid();
    get diagnostics n = row_count;
    if n = 0 then
        raise exception 'not_member' using errcode = '42501';
    end if;
end;
$$;

create or replace function public.app_leave_circle(p_family_id uuid)
returns void
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    own members%rowtype;
begin
    select * into own from members
    where family_id = p_family_id and auth_user_id = auth.uid();
    if not found then
        raise exception 'not_member' using errcode = '42501';
    end if;
    if own.role = 'admin' and (
        select count(*) from members where family_id = p_family_id and role = 'admin'
    ) <= 1 then
        raise exception 'last_admin' using errcode = '23514';
    end if;
    delete from members where id = own.id;
end;
$$;

-- Grants: 0008's pattern, 0004's doctrine. Revoke from PUBLIC and from anon
-- (the bootstrap hands anon EXECUTE at creation), grant to authenticated only.
revoke all on function public.app_add_seat(uuid, text, text) from public, anon;
revoke all on function public.app_remove_seat(uuid) from public, anon;
revoke all on function public.app_set_role(uuid, text) from public, anon;
revoke all on function public.app_set_mail(uuid, boolean) from public, anon;
revoke all on function public.app_leave_circle(uuid) from public, anon;
grant execute on function public.app_add_seat(uuid, text, text) to authenticated;
grant execute on function public.app_remove_seat(uuid) to authenticated;
grant execute on function public.app_set_role(uuid, text) to authenticated;
grant execute on function public.app_set_mail(uuid, boolean) to authenticated;
grant execute on function public.app_leave_circle(uuid) to authenticated;
