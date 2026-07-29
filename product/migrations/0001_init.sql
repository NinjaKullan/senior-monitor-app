-- 0001 — multi-tenant core schema (spec 002 §2).
--
-- The privacy promise is the column list. A ping is a parent, a signal name, a
-- server-side timestamp and a one-way IP hash. There is no column here that can
-- hold content, location, health data, a count, or a trend.

create table families (
    id                 uuid primary key default gen_random_uuid(),
    name               text not null,
    tz                 text not null default 'Asia/Kolkata',
    stripe_customer_id text,
    plan               text not null default 'founding',
    created_utc        timestamptz not null default now()
);

create table members (
    id           uuid primary key default gen_random_uuid(),
    family_id    uuid not null references families(id) on delete cascade,
    auth_user_id uuid,
    display_name text,
    role         text not null check (role in ('owner', 'child')),
    email        text,
    phone_e164   text,
    created_utc  timestamptz not null default now()
);
create index members_family_idx on members (family_id);
create index members_auth_user_idx on members (auth_user_id) where auth_user_id is not null;

-- Monitored loved ones. Unbounded per family, per the roadmap: a family may add a
-- grandparent or an aunt, each with their own timezone, signals and devices.
create table parents (
    id           uuid primary key default gen_random_uuid(),
    family_id    uuid not null references families(id) on delete cascade,
    display_name text not null,
    tz           text,  -- overrides the family tz when set (Mom visiting Texas)
    created_utc  timestamptz not null default now()
);
create index parents_family_idx on parents (family_id);

-- One row per phone. Tokens are per device so a lost phone is a single revoke
-- that leaves every other device in the family working.
create table devices (
    id           uuid primary key default gen_random_uuid(),
    parent_id    uuid not null references parents(id) on delete cascade,
    platform     text not null check (platform in ('ios_shortcuts', 'android')),
    device_token text unique not null
                 check (device_token ~ '^[A-Za-z0-9_-]{20,}$'),
    active       boolean not null default true,
    created_utc  timestamptz not null default now(),
    revoked_utc  timestamptz
);
create index devices_parent_idx on devices (parent_id);

-- Per-parent signal allowlist. A signal that is not here is a 400, so one
-- parent enabling a signal never enables it for anyone else.
create table parent_signals (
    id          uuid primary key default gen_random_uuid(),
    parent_id   uuid not null references parents(id) on delete cascade,
    signal      text not null,
    alarm_grade boolean not null,
    active      boolean not null default true,
    unique (parent_id, signal)
);

create table pings (
    id        bigint generated always as identity primary key,
    parent_id uuid not null references parents(id) on delete cascade,
    signal    text not null,
    ts_utc    timestamptz not null,
    ip_hash   text
);
create index pings_parent_ts_idx on pings (parent_id, ts_utc desc);
create index pings_ts_idx on pings (ts_utc desc);

-- Ops alerts only: heartbeat/pipeline events for the founder. Product law #3 —
-- nothing family- or parent-facing is written here or anywhere else in spec 002.
create table ops_alerts (
    id        bigint generated always as identity primary key,
    family_id uuid not null references families(id) on delete cascade,
    parent_id uuid references parents(id) on delete cascade,
    kind      text not null,
    detail    text not null,
    ts_utc    timestamptz not null default now()
);
create index ops_alerts_dedupe_idx on ops_alerts (kind, parent_id, ts_utc desc);
create index ops_alerts_family_idx on ops_alerts (family_id, ts_utc desc);
