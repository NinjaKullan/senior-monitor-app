# Spec 002 — Product backend: multi-tenant core

*PM: Fable. Status: ready to build. This is the PRODUCT, not the pilot. The pilot app (`app/`, kettle-pilot on Fly) is frozen except for bugfixes — it is a running experiment and YC evidence. Do not modify it in this spec.*

## 0. Shape of the work

New top-level directory `product/` in this repo: its own FastAPI app, tests, Dockerfile, fly.toml (new Fly app, suggested name `kettle-api`), and SQL migrations for Supabase. Same product law as CLAUDE.md, same definition of done. Pilot code may be copied from (signal allowlisting, UTC discipline, dedupe, heartbeat idempotency patterns are all review-approved) but `product/` shares no runtime with `app/`.

## 1. Stack

- Python 3.12, FastAPI, uvicorn — ingestion + jobs service on Fly (always-on, same heartbeat-in-process reasoning as the pilot; `auto_stop_machines = "off"`).
- **Supabase** = Postgres + Auth + RLS. The service connects with the service-role key (env). Client-facing reads (the future PWA, spec 005) will use Supabase Auth JWTs against RLS-protected views — so RLS policies are in scope NOW even though no client exists yet: isolation must be structural, not app-code courtesy.
- Migrations as plain SQL files in `product/migrations/`, numbered, applied via supabase CLI or psql; no ORM.

## 2. Schema (v1)

```
families(id uuid pk, name text, tz text not null default 'Asia/Kolkata',
         stripe_customer_id text, plan text default 'founding', created_utc timestamptz)
members(id uuid pk, family_id fk, auth_user_id uuid null, display_name text,
        role text check in ('owner','child'), email text, phone_e164 text, created_utc)
parents(id uuid pk, family_id fk, display_name text, tz text null, created_utc)
   -- parent tz overrides family tz when set (Mom visiting Texas)
devices(id uuid pk, parent_id fk, platform text check in ('ios_shortcuts','android'),
        device_token text unique not null, active bool default true,
        created_utc, revoked_utc null)
parent_signals(id uuid pk, parent_id fk, signal text, alarm_grade bool not null,
               active bool default true)
   -- per-parent allowlist; seeded from the standard set:
   -- whatsapp/youtube/news (alarm_grade=true), charge_on/charge_off/device_alive (false)
pings(id bigint pk, parent_id fk, signal text, ts_utc timestamptz not null, ip_hash text)
ops_alerts(id bigint pk, family_id fk, parent_id fk null, kind text, detail text, ts_utc)
```

Indexes mirroring the pilot (parent_id+ts, ts). **RLS:** members can select only rows of their own family (join via family_id); parents/devices/pings likewise; `ops_alerts` service-only. Write a policy test that PROVES family A's JWT cannot read family B's pings.

## 3. Ingestion

`GET|POST /p/{device_token}/{signal}` — the human-readable route (`kettle-api.fly.dev/p/<token>/whatsapp`; a vanity domain fronts it later). Rules, all inherited from the pilot: token → device → parent, else silent 403; signal must be in that parent's active `parent_signals`, else 400; server-side UTC timestamp only; 60s dedupe per (parent, signal); ALL other params/fields dropped; salted ip_hash. `device_token`: 20+ chars, url-safe, generated server-side; per DEVICE, revocable individually.

`who` no longer exists in the URL — the token IS the identity. (This kills the pilot's who=mom guessability and shortens the link.)

`GET /healthz` — no auth, `{"db": true}`.

## 4. Heartbeat v2 (ops-only in this spec)

Same rules as pilot, generalized: per parent, in the PARENT's effective tz — noon check (no alarm-grade ping since 05:00 local), evening escalation (20:00, only if noon fired), infra check (suppressed until family's first-ever ping — pilot rule carries over). Idempotent per (kind, parent, local-day). Alerts go to `ops_alerts` + founder ntfy topic (env). NOTHING family- or parent-facing fires from this spec — that is spec 004's ladder, unbuilt. Product law #3 still binds.

## 5. Family provisioning (no UI yet)

A CLI script (`product/scripts/provision.py`): create family + parents + devices + seeded signals, print the ready-to-use ping URLs and (stub) iCloud-shortcut naming per signal. This is how beta families get onboarded until the PWA exists. Include a `--demo` flag that provisions a demo family for tests.

## 6. Non-goals (do not build)

Digest (003). Ladder/senior-ask (004). PWA/wizard/TestFlight (005). Android (006). Stripe wiring (fields exist, integration later). Labels/blinding (pilot-only instrument). No admin UI (Supabase Studio suffices). No analytics/telemetry (product law #4).

## 7. Acceptance criteria

1. Two families provisioned; ping via family A device token lands under family A; A's JWT cannot read B's rows (RLS test with two auth users).
2. Readable route works from a real iOS Shortcut (manual check by Hema; automated test covers GET with extra junk params → stored row has only allowlisted fields).
3. Bad/revoked token → 403, no write. Revoking one device kills only that device.
4. Signal not in parent's allowlist → 400, no write. Dedupe within 60s.
5. Heartbeat: two families in different timezones each get their own noon check at their own local noon (injectable clock test, pattern from pilot heartbeat tests).
6. Parent tz override: Mom set to America/Chicago gets Chicago-noon checks while family stays IST.
7. Fresh deploy to a new Fly app + empty Supabase project boots via documented steps in `product/README.md`.
8. `pytest` green, `ruff` clean, no secrets in diff; pilot directory untouched.
