-- 0026 — replies on a note (spec 016, DECISIONS 274).
--
-- A reply is a journal row that belongs to another journal row. One level
-- only: a note can have replies, a reply cannot. Kettle's own lines
-- (city_change, started, first_reply, clean_month) take no replies — they
-- are the house speaking, not a conversation. A reply has an author and a
-- written-at instant like a note; it has no event date and no parent tag of
-- its own, it INHERITS the tag from the note it belongs to (§2), which the
-- trigger below writes so the per-parent read (webapp data.ts) carries a
-- thread whole.
--
-- Enforced by a BEFORE INSERT trigger rather than an insert function, so the
-- app's one write path onto this table — a plain insert under 0017's RLS
-- policy — stays the write path, and a reply is the same insert with one
-- more column. The trigger function is SECURITY DEFINER so it can read the
-- parent row regardless of the caller's RLS view: a reply aimed at another
-- family's note is refused by name (reply_across_families) rather than as
-- "no such note", and 0017's WITH CHECK still bounds the row's own family.
-- Refusals use errcode 23514 (check violation), the 0025 convention.
--
-- RLS unchanged. Deleting a note deletes its replies (cascade); no UI for
-- deleting exists today.

alter table journal_entries
    add column parent_entry_id bigint references journal_entries(id) on delete cascade;

create index journal_entries_parent_entry_idx
    on journal_entries (parent_entry_id) where parent_entry_id is not null;

create or replace function public.journal_entries_reply_rule()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    parent journal_entries%rowtype;
begin
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
    -- The tag is the note's, never the reply's own (§2).
    new.parent_id := parent.parent_id;
    return new;
end;
$$;

revoke all on function public.journal_entries_reply_rule() from public, anon, authenticated;

create trigger journal_entries_reply_rule
    before insert on journal_entries
    for each row execute function public.journal_entries_reply_rule();
