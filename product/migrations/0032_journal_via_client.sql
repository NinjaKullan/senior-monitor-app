-- 0032 — notes and replies through the assistant (spec 019 Amendment A).
--
-- Three small things, all server-side; no RLS change.
--
-- 1. journal_entries.via_client: a dictated note or reply carries the
--    assistant client's name here, so every surface can render the author as
--    "{name} via {client}". author_member_id stays the person and author_label
--    their display name, as a typed note would carry.
-- 2. assistant_grants.scope: what the grant was given (A.2 said the column
--    exists; it did not — every grant to date is kettle:read, which is the
--    default). The family app reads it on its own rows to say "can add notes";
--    the hash columns stay ungranted.
-- 3. The 0028 trigger keeps a service-role write's author. The webapp writes
--    as the person (auth.uid() from the JWT) and the trigger overrides
--    whatever the row said; kettle-api writes as the service role on behalf
--    of the resolved member, with no JWT, and the trigger used to null the
--    author. Now, with no JWT, a provided author_member_id survives only if
--    that member belongs to the row's family; Kettle's own lines still carry
--    none. A client session can never set it: auth.uid() is present there.

alter table journal_entries add column via_client text
    check (via_client is null or char_length(via_client) <= 120);

alter table assistant_grants add column scope text not null default 'kettle:read';

revoke all on assistant_grants from anon, authenticated;
grant select (id, client_name, created_utc, last_used_utc, revoked_utc, scope)
    on assistant_grants to authenticated;

create or replace function public.journal_entries_reply_rule()
returns trigger
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    parent journal_entries%rowtype;
begin
    if auth.uid() is not null then
        -- Spec 018: the author is the caller's seat in this family, from the
        -- JWT, never from the row.
        new.author_member_id := (
            select m.id from members m
            where m.family_id = new.family_id and m.auth_user_id = auth.uid()
            order by m.created_utc, m.id
            limit 1
        );
    elsif new.author_member_id is not null and not exists (
        select 1 from members m where m.id = new.author_member_id and m.family_id = new.family_id
    ) then
        -- A service write naming a member of another family is a bug, not a
        -- note; Kettle's own lines carry no author at all.
        new.author_member_id := null;
    end if;
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
