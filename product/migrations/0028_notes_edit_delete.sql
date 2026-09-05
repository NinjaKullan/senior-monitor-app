-- 0028 — notes: authorship, edit, delete (spec 018, DECISIONS 280).
--
-- A typo was a permanent record. Now: the author edits their own text and
-- deletes their own notes and replies; an admin deletes anyone's but rewrites
-- nobody else's words; Kettle's own lines (city_change, started, first_reply,
-- clean_month) are untouchable. An edited entry carries the instant it was
-- edited, which the app renders as "edited" beside the date.
--
-- Authorship is recorded server-side: 0026's insert trigger now writes
-- author_member_id from the caller's member row in that family, from the
-- JWT, and ignores anything the client sends in that column. Rows written
-- before this migration have no author; on those only an admin may edit or
-- delete — a legacy row is nobody's to rewrite.
--
-- Two SECURITY DEFINER functions in the 0025 pattern are the only write
-- paths after the insert: no client UPDATE or DELETE policy on
-- journal_entries. Refusals: 42501 for who-may (not_author, not_allowed),
-- 23514 for what-may (kettle_line, body_too_long, body_empty).

alter table journal_entries
    add column author_member_id uuid references members(id) on delete set null,
    add column edited_utc timestamptz;

create or replace function public.journal_entries_reply_rule()
returns trigger
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    parent journal_entries%rowtype;
begin
    -- Spec 018: the author is the caller's seat in this family, from the
    -- JWT, never from the row. Service writes (Kettle's own lines) carry no
    -- JWT and get null.
    new.author_member_id := (
        select m.id from members m
        where m.family_id = new.family_id and m.auth_user_id = auth.uid()
        order by m.created_utc, m.id
        limit 1
    );
    new.edited_utc := null;

    if new.parent_entry_id is null then
        return new;
    end if;
    if new.kind <> 'note' then
        raise exception 'reply_must_be_note' using errcode = '23514';
    end if;
    if new.event_date is not null then
        raise exception 'reply_with_date' using errcode = '23514';
    end if;
    select * into parent from journal_entries where id = new.parent_entry_id;
    if not found then
        raise exception 'reply_parent_missing' using errcode = '23514';
    end if;
    if parent.family_id <> new.family_id then
        raise exception 'reply_across_families' using errcode = '23514';
    end if;
    if parent.parent_entry_id is not null then
        raise exception 'reply_to_reply' using errcode = '23514';
    end if;
    if parent.kind <> 'note' then
        raise exception 'reply_to_kettle_line' using errcode = '23514';
    end if;
    new.parent_id := parent.parent_id;
    return new;
end;
$$;

create or replace function public.app_edit_entry(p_entry_id bigint, p_body text)
returns void
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    entry journal_entries%rowtype;
    caller uuid;
    v_body text := p_body;
begin
    select * into entry from journal_entries where id = p_entry_id;
    if not found then
        raise exception 'not_author' using errcode = '42501';
    end if;
    if entry.kind <> 'note' then
        raise exception 'kettle_line' using errcode = '23514';
    end if;
    select m.id into caller from members m
    where m.family_id = entry.family_id and m.auth_user_id = auth.uid()
    order by m.created_utc, m.id limit 1;
    if caller is null then
        raise exception 'not_author' using errcode = '42501';
    end if;
    if entry.author_member_id is null then
        -- A legacy row: admin only (spec 018 §2).
        if not exists (
            select 1 from members where id = caller and role = 'admin'
        ) then
            raise exception 'not_author' using errcode = '42501';
        end if;
    elsif entry.author_member_id <> caller then
        raise exception 'not_author' using errcode = '42501';
    end if;
    if v_body is null or trim(v_body) = '' then
        raise exception 'body_empty' using errcode = '23514';
    end if;
    if char_length(v_body) > 2000 then
        raise exception 'body_too_long' using errcode = '23514';
    end if;
    update journal_entries set body = v_body, edited_utc = now() where id = p_entry_id;
end;
$$;

create or replace function public.app_delete_entry(p_entry_id bigint)
returns void
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    entry journal_entries%rowtype;
    caller members%rowtype;
begin
    select * into entry from journal_entries where id = p_entry_id;
    if not found then
        raise exception 'not_allowed' using errcode = '42501';
    end if;
    if entry.kind <> 'note' then
        raise exception 'kettle_line' using errcode = '23514';
    end if;
    select m.* into caller from members m
    where m.family_id = entry.family_id and m.auth_user_id = auth.uid()
    order by m.created_utc, m.id limit 1;
    if caller.id is null then
        raise exception 'not_allowed' using errcode = '42501';
    end if;
    if caller.role <> 'admin' and (
        entry.author_member_id is null or entry.author_member_id <> caller.id
    ) then
        raise exception 'not_allowed' using errcode = '42501';
    end if;
    delete from journal_entries where id = p_entry_id;  -- replies cascade (0026)
end;
$$;

revoke all on function public.app_edit_entry(bigint, text) from public, anon;
revoke all on function public.app_delete_entry(bigint) from public, anon;
grant execute on function public.app_edit_entry(bigint, text) to authenticated;
grant execute on function public.app_delete_entry(bigint) to authenticated;
