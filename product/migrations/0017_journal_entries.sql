-- 0017 — Family notes v1 (spec 009 §4).
--
-- The family's shared memory: plain-text notes, an optional date, an optional
-- parent tag. This is the app's FIRST client write path onto a table of its
-- own, so the grants are the narrowest that make the feature work: select and
-- insert for authenticated, no update, no delete (v1 has neither), and RLS
-- mirrors the 0002 per-family shape exactly — deny all, then family members
-- read and insert their own family's rows. Ingestion-style service writes do
-- not exist for this table; every row is authored by a signed-in family
-- member through the webapp.

create table journal_entries (
    id           bigint generated always as identity primary key,
    family_id    uuid not null references families(id),
    -- Null means the note is about the family, not one parent; when set, the
    -- insert policy requires the parent to belong to the same family, so a
    -- note can never tag a stranger's parent.
    parent_id    uuid references parents(id),
    author_label text not null default '',
    body         text not null check (char_length(body) <= 2000),
    event_date   date,
    created_utc  timestamptz not null default now()
);

alter table journal_entries enable row level security;

create policy journal_entries_select_own_family on journal_entries
    for select to authenticated
    using (family_id in (select public.app_current_family_ids()));

create policy journal_entries_insert_own_family on journal_entries
    for insert to authenticated
    with check (
        family_id in (select public.app_current_family_ids())
        and (
            parent_id is null
            or parent_id in (
                select p.id from parents p
                where p.family_id = journal_entries.family_id
            )
        )
    );

grant select, insert on journal_entries to authenticated;
-- The identity column draws from a sequence; inserting without naming the id
-- still needs usage on it for the authenticated role.
grant usage on sequence journal_entries_id_seq to authenticated;
