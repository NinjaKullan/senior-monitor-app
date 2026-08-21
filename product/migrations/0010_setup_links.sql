-- 0010 — per-parent setup links (spec 005b §4.2).
--
-- A setup link is the parent setup page's address: unguessable, expiring,
-- revocable. It resolves through its device, so revoking the device token kills
-- the URL with it — the URL is the token in transit (DECISIONS 102) and never
-- outlives it. The slug is a *separate* secret from the device token: the page
-- it unlocks shows steps and a live verify check, never the token, so a leaked
-- link burns a page, not a ping identity.
--
-- `parent_id` is deliberately denormalised from the device row. The child app
-- renders "Amma's setup" from this table alone; giving it the parent directly
-- means its read surface never has to touch `devices`, and device tokens stay
-- out of every browser (DECISIONS 101's standing rule, applied to the webapp).

create table setup_links (
    id          uuid primary key default gen_random_uuid(),
    device_id   uuid not null references devices(id) on delete cascade,
    parent_id   uuid not null references parents(id) on delete cascade,
    slug        text unique not null
                check (slug ~ '^[A-Za-z0-9_-]{20,}$'),
    created_utc timestamptz not null default now(),
    expires_utc timestamptz not null,
    revoked_utc timestamptz
);
create index setup_links_device_idx on setup_links (device_id);
create index setup_links_parent_idx on setup_links (parent_id);

alter table setup_links enable row level security;

-- The family may see its own links — that is how the child app shows "Mom's
-- setup" as a forwardable card. Scoped through parents, like parent_signals.
create policy setup_links_own_family on setup_links
    for select to authenticated
    using (parent_id in (
        select p.id from parents p
        where p.family_id in (select public.app_current_family_ids())
    ));

grant select on setup_links to authenticated;

-- Issuance and revocation are service-side only (provisioning, spec 002 §5
-- doctrine): a client that could mint links could mint indefinite ones. The
-- shim's default privileges hand the full set to every role at creation time,
-- so strip the rest explicitly (migration 0004's lesson).
revoke insert, update, delete, truncate, references, trigger
    on setup_links from anon, authenticated;
revoke all on setup_links from anon;
