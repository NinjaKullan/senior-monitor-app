-- 0005 — digest engine (spec 003).
--
-- The first family-facing feature. Spec 003 §0 authorises reassurance messages
-- sent when routine IS observed, and nothing else: no absence messaging to
-- families, nothing to the senior. That boundary lives in code, but the schema
-- keeps its own guard rail — `digest_enabled` defaults FALSE, so a family that
-- exists is not a family that gets messaged.

alter table families add column digest_enabled boolean not null default false;

alter table members add column digest_channel text not null default 'sms'
    check (digest_channel in ('sms', 'whatsapp', 'none'));

-- One row per (message, recipient). This table *is* the idempotency: the
-- scheduler asks the database what it has already sent, never its own memory,
-- so a restart mid-pass cannot produce a second "good morning".
create table digest_sends (
    id         bigint generated always as identity primary key,
    family_id  uuid not null references families(id) on delete cascade,
    parent_id  uuid references parents(id) on delete cascade,  -- null when aggregated
    kind       text not null check (kind in ('morning', 'evening')),
    local_date date not null,
    member_id  uuid not null references members(id) on delete cascade,
    channel    text not null,
    status     text not null check (status in ('sent', 'failed')),
    ts_utc     timestamptz not null default now()
);

create unique index digest_once_idx on digest_sends (
    family_id,
    coalesce(parent_id, '00000000-0000-0000-0000-000000000000'::uuid),
    kind,
    local_date,
    member_id
);

create index digest_sends_family_idx on digest_sends (family_id, ts_utc desc);

alter table digest_sends enable row level security;

create policy digest_sends_own_family on digest_sends
    for select to authenticated
    using (family_id in (select public.app_current_family_ids()));

-- 0004 doctrine: explicit or absent. The bootstrap's default privileges were
-- revoked for anon and authenticated, so this table arrives with no grants at
-- all and gets exactly the one it needs. Writes are the service role's.
grant select on digest_sends to authenticated;
