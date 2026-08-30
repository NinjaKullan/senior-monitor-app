-- 0021 — the family contacts sheet, "If you can't reach them" (spec 012 §4).
--
-- The digital twin of the emergency printable: the family's OWN four-or-so
-- numbers — a neighbor, family nearby, the building, their doctor. NEVER
-- auto-populated; a stale emergency number we suggested is worse than a
-- blank line the family owns (DECISIONS 200).
--
-- The NAME is a rebirth, on purpose: a table called family_contacts was the
-- retired ladder's call tree, archived/dropped by 0013. This one is a new
-- thing doing a different job — reference data the family edits, never an
-- escalation target; nothing in the engine reads it. It leaves the retired
-- set the way kettle/twilio_signature.py did (DECISIONS 163): written new,
-- not resurrected, and test_retirement records the distinction.
--
-- UNLIKE the journal, contacts are editable and deletable — reference data,
-- not record — so this table gets the full grant set, each bounded by the
-- same per-family RLS shape as 0017.

create table family_contacts (
    id            bigint generated always as identity primary key,
    family_id     uuid not null references families(id),
    -- Null means the contact is family-wide; when set, the policies require
    -- the parent to belong to the same family, exactly as journal tags do.
    parent_id     uuid references parents(id),
    label         text not null default '' check (char_length(label) <= 60),
    name          text not null default '' check (char_length(name) <= 80),
    -- E.164 stored, human-readable shown (the elder-proofing law): the tel:
    -- href uses phone_e164, the visible text uses phone_display, and the two
    -- travel together so neither is ever derived from the other at render.
    phone_e164    text not null default '' check (char_length(phone_e164) <= 20),
    phone_display text not null default '' check (char_length(phone_display) <= 30),
    note          text not null default '' check (char_length(note) <= 200),
    position      integer not null default 0,
    author_label  text not null default '',
    created_utc   timestamptz not null default now(),
    updated_utc   timestamptz not null default now()
);

alter table family_contacts enable row level security;

create policy family_contacts_select_own_family on family_contacts
    for select to authenticated
    using (family_id in (select public.app_current_family_ids()));

create policy family_contacts_insert_own_family on family_contacts
    for insert to authenticated
    with check (
        family_id in (select public.app_current_family_ids())
        and (
            parent_id is null
            or parent_id in (
                select p.id from parents p
                where p.family_id = family_contacts.family_id
            )
        )
    );

create policy family_contacts_update_own_family on family_contacts
    for update to authenticated
    using (family_id in (select public.app_current_family_ids()))
    with check (
        family_id in (select public.app_current_family_ids())
        and (
            parent_id is null
            or parent_id in (
                select p.id from parents p
                where p.family_id = family_contacts.family_id
            )
        )
    );

create policy family_contacts_delete_own_family on family_contacts
    for delete to authenticated
    using (family_id in (select public.app_current_family_ids()));

grant select, insert, update, delete on family_contacts to authenticated;
grant usage on sequence family_contacts_id_seq to authenticated;
