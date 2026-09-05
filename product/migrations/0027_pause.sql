-- 0027 — pause Kettle for one parent (spec 017, DECISIONS 274).
--
-- An admin pauses Kettle for one parent: a hospital stay, travel with a
-- child, a broken phone. While paused Kettle sends nothing about that
-- parent and raises nothing; the app says so plainly. Per parent, never per
-- circle; two durations, a week or open-ended.
--
-- `paused_until` carries both durations: a week pause stores the instant,
-- the open-ended one stores 'infinity'. Null = not paused, and so is an
-- instant in the past — the engine and the app both read "paused" as
-- paused_until > now, so a pause ends by itself. `paused_since` is the
-- resume-day rule's memory (spec 017 §4): the engine reads it on the first
-- pass after the pause ends and clears both fields once that local day is
-- over.
--
-- app_resume_parent does NOT null the fields (spec §3 said it would; filed
-- as a disagreement in the ledger). It ends the pause NOW — paused_until =
-- now() — so a manual resume and a week's expiry are one path through the
-- engine, and the resume day can apply the fresh-first-day rule from the
-- instant the pause ended. The engine clears both fields on the first pass
-- after that local day, exactly as it does after an expiry.
--
-- Same pattern as 0025: SECURITY DEFINER, admin of the parent's circle,
-- errcode 42501 for the permission refusals and 23514 for the rule ones,
-- revoked from public and anon, authenticated only. No client UPDATE on
-- these columns: the 0018/0019 column grants are unchanged.

alter table parents add column paused_until timestamptz;
alter table parents add column paused_since timestamptz;

comment on column parents.paused_until is
    'Kettle is paused for this parent until this instant (infinity = until '
    'someone turns it back on). Null or past = running. Spec 017.';

create or replace function public.app_pause_parent(p_parent_id uuid, p_until timestamptz)
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
    if p_until is null or p_until <= now() then
        raise exception 'pause_in_the_past' using errcode = '23514';
    end if;
    update parents
    set paused_until = p_until,
        -- A pause extended while running keeps its original start.
        paused_since = case
            when paused_until is not null and paused_until > now() then paused_since
            else now()
        end
    where id = p_parent_id;
end;
$$;

create or replace function public.app_resume_parent(p_parent_id uuid)
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
    if target.paused_until is null or target.paused_until <= now() then
        return;  -- already running; nothing to end
    end if;
    update parents set paused_until = now() where id = p_parent_id;
end;
$$;

revoke all on function public.app_pause_parent(uuid, timestamptz) from public, anon;
revoke all on function public.app_resume_parent(uuid) from public, anon;
grant execute on function public.app_pause_parent(uuid, timestamptz) to authenticated;
grant execute on function public.app_resume_parent(uuid) to authenticated;
