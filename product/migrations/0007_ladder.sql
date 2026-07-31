-- 0007 — escalation ladder v1 (spec 004).
--
-- The highest-stakes path in the product, so the schema itself holds the safety
-- properties rather than trusting the code to remember them:
--
--   * ladder_mode defaults to 'off'. A family that exists escalates nothing.
--   * a CHECK makes 'live' impossible unless digest_enabled is already true —
--     a family meets Kettle as reassurance before it can meet it as alarm, and
--     that ordering is now unrepresentable in the wrong sequence rather than
--     merely enforced by whoever runs the CLI.
--   * one candidate per parent per local day, by unique index.
--
-- Rule v1's thresholds live in per-parent columns with deliberately conservative
-- defaults. The pilot's Phase-1 percentile analysis will fit real per-person
-- values later; that work updates rows, never this schema.

alter table families add column ladder_mode text not null default 'off'
    check (ladder_mode in ('off', 'shadow', 'live'));

-- Structural, not procedural: there is no order of operations that leaves a
-- family live without digests.
alter table families add constraint families_live_requires_digest
    check (ladder_mode <> 'live' or digest_enabled);

-- The senior's own number, used for the ASK stage only. Nullable: no phone
-- means the ask is skipped, not that the ladder stops.
alter table parents add column phone_e164 text;

-- Rule v1 thresholds and timings, per parent.
alter table parents add column alarm_deadline time not null default '12:00';
alter table parents add column max_gap_minutes int not null default 480;
alter table parents add column grace_minutes int not null default 90;
alter table parents add column family_gap_minutes int not null default 60;

-- A named local contact, suggested to the family at FAMILY-ALL. v1 never
-- contacts them — no call, no SMS. Populated by the wizard (spec 005).
create table family_contacts (
    id          uuid primary key default gen_random_uuid(),
    family_id   uuid not null references families(id) on delete cascade,
    name        text not null,
    phone_e164  text,
    relation    text,
    created_utc timestamptz not null default now()
);
create index family_contacts_family_idx on family_contacts (family_id);

create table ladder_candidates (
    id             bigint generated always as identity primary key,
    family_id      uuid not null references families(id) on delete cascade,
    parent_id      uuid not null references parents(id) on delete cascade,
    local_date     date not null,
    mode           text not null check (mode in ('shadow', 'live')),
    trigger        text not null check (trigger in ('deadline', 'max_gap')),
    -- Is anything at all still arriving from the phone? Decides whether asking
    -- the senior is even possible, and which family copy is honest.
    mechanism_ok   boolean not null,
    stage          text not null,
    opened_utc     timestamptz not null,
    ask_utc        timestamptz,
    family_1_utc   timestamptz,
    family_all_utc timestamptz,
    resolved_utc   timestamptz,
    resolution     text check (
        resolution in ('resolved_by_senior', 'resolved_by_activity', 'resolved_manually')
    )
);

-- One candidate per parent per local day: a resolved candidate does not re-arm
-- the same day in v1.
create unique index ladder_candidate_once_idx
    on ladder_candidates (parent_id, local_date);
create index ladder_candidates_open_idx
    on ladder_candidates (parent_id, resolved_utc) where resolved_utc is null;

-- Every transition, in order. In shadow mode this is the labelled ledger that
-- tunes the thresholds — the pilot's Phase-2 ledger, productized.
create table ladder_events (
    id           bigint generated always as identity primary key,
    candidate_id bigint not null references ladder_candidates(id) on delete cascade,
    family_id    uuid not null references families(id) on delete cascade,
    parent_id    uuid not null references parents(id) on delete cascade,
    stage        text not null,
    mode         text not null,
    detail       text not null,
    ts_utc       timestamptz not null default now()
);
create index ladder_events_candidate_idx on ladder_events (candidate_id, ts_utc);
create index ladder_events_family_idx on ladder_events (family_id, ts_utc desc);

alter table family_contacts    enable row level security;
alter table ladder_candidates  enable row level security;
alter table ladder_events      enable row level security;

create policy family_contacts_own_family on family_contacts
    for select to authenticated
    using (family_id in (select public.app_current_family_ids()));

create policy ladder_candidates_own_family on ladder_candidates
    for select to authenticated
    using (family_id in (select public.app_current_family_ids()));

create policy ladder_events_own_family on ladder_events
    for select to authenticated
    using (family_id in (select public.app_current_family_ids()));

-- 0004 doctrine: explicit or absent. These tables arrive with no grants and get
-- exactly the read the future PWA needs; writes are the service role's.
grant select on family_contacts, ladder_candidates, ladder_events to authenticated;
