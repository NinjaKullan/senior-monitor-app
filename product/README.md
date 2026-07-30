# Kettle — product backend (multi-tenant core)

Spec `specs/002-multitenant-core.md`. This is the **product**, deployed as its own
Fly app (`kettle-api`) against its own Supabase project. It shares a git repo with
the pilot in `app/` and nothing else — no code, no database, no deployment. The
pilot is a running experiment and stays frozen.

## What is stored

The entire record of a ping is four columns:

| Column | Example | Why |
|---|---|---|
| `parent_id` | uuid | which monitored person |
| `signal` | `whatsapp` | which routine, by name only |
| `ts_utc` | `2026-08-03T06:30:00Z` | **server-side** clock; client time is ignored |
| `ip_hash` | `4f9c…` (16 hex) | salted, truncated SHA-256, ops/debug only, never displayed |

No message content, no browsing content, no audio, no location, no device identity,
no counts, no trends. Anything outside the URL path is read by nothing and stored
nowhere — see `tests/test_ingest.py::test_junk_params_are_never_stored`.

Uvicorn runs with `--no-access-log` deliberately: access logs would otherwise
record full request URLs, and the URL contains the device token.

## Isolation

Every table has Row Level Security on, and the policies resolve the caller's
families from their Supabase Auth user id — so family A's JWT cannot read family
B's rows regardless of what the API layer does. There is no client yet; the
policies land now precisely so the PWA (spec 005) inherits isolation rather than
being trusted with it. `ops_alerts` has RLS on and no policy at all: it is the
founder's plumbing log and no end-user role can read it.

`tests/test_rls.py` is the proof — two families, two auth users, one connection
acting as the `authenticated` role, asserting both that A sees its own rows and
that naming B's row ids explicitly still returns nothing.

### Grants, not just policies

Supabase's project bootstrap sets default privileges that grant the full
privilege set on new public-schema objects **directly** to `anon`,
`authenticated` and `service_role`. Revoking from `PUBLIC` does not remove a
direct role grant, so two migrations clean up after it:

- `0003_revoke_anon_rpc.sql` — takes EXECUTE on `app_current_family_ids()` away
  from `anon`. That helper is SECURITY DEFINER and reads `members` with RLS
  bypassed; the pre-login role has no business calling it.
- `0004_revoke_residual_table_privileges.sql` — takes every table and sequence
  privilege away from `anon`, reduces `authenticated` to exactly SELECT on the
  six family tables, removes its SELECT on `ops_alerts`, and revokes the default
  privileges so the next object created does not re-acquire any of it.

RLS alone was not sufficient cover for this: **TRUNCATE is not a row-level
operation**, so no policy governs it, and `anon` held TRUNCATE on all seven
tables. The end state is asserted directly against the catalog in
`tests/test_rls.py`, and `tests/test_deploy.py` reproduces the pre-migration
grants and proves each migration is what removes them.

The local shim reproduces the bootstrap grants for exactly this reason — without
them both migrations would pass vacuously in tests while being load-bearing in
production.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET\|POST /p/{device_token}/{signal}` | record a ping; returns `ok` |
| `GET /healthz` | `{"db": true}`, no auth, for Fly health checks |

The device token *is* the identity: there is no `who` in the URL to guess. Unknown,
deactivated and revoked tokens all get the same bare `403`. A signal that is not in
**that parent's** active allowlist is a `400`. Identical `(parent, signal)` within
60 s collapses into one row.

Signals are per parent (`parent_signals`), seeded from the standard set:
`whatsapp`, `youtube`, `news` (alarm-grade) and `charge_on`, `charge_off`,
`device_alive` (corroborating only). Alarm-grade means a human deliberately did
something — a timer ping or a charger event can never stand in for a person.

## Heartbeat (ops-only)

An in-process background task, once a minute, evaluated in **each person's own
effective timezone** (parent `tz` when set, else family `tz`).

| Check | Rule | Scope |
|---|---|---|
| Noon (12:00 local) | zero alarm-grade pings since 05:00 local | per parent |
| Evening (20:00 local) | still zero, **and** the noon alert already fired | per parent |
| Infra | no ping from any device in the family for 24 h, once the family has ever pinged | per family |

Each `(kind, parent-or-family)` fires at most once per local day, so running every
minute is safe. Every alert is written to `ops_alerts` and sent to the founder's
ntfy topic. **Nothing family- or parent-facing fires from this service** — the
escalation ladder is spec 004 and is not built (product law #3).

## Digests (spec 003)

The first family-facing feature, and the only one authorised to send: digests are
reassurance messages that go out **when routine is observed**. Nothing here
messages a family about the *absence* of activity, and nothing here messages the
senior at all — that is spec 004, unbuilt.

| Message | When | Copy |
|---|---|---|
| Morning | on the first alarm-grade ping of the parent's local day, before the cutoff (14:00 local) | `Good morning — {parent}'s day started normally (8:12 am local time).` |
| Evening | at 20:30 parent-local | `{parent} had a normal, active day.` / `{a} and {b} both had normal, active days.` |

The morning message cannot be rendered without a real first-ping time: a "day
started normally" with no evidence behind it is manufactured reassurance. A parent
with no alarm-grade pings is silently omitted from the evening message and
surfaced to the founder as a `digest_skipped` ops alert; if nobody qualifies, the
family hears nothing at all.

**The evening is final once sent**, per timezone group per local date. A parent
whose first ping lands after their group's summary went out is omitted from that
day's digest rather than triggering a second text — the contract is a predictable
cadence, and a surprise late message is an anomaly even when the content is good.
A parent silent until 9pm is heartbeat information, not digest information.

**The copy is product law, not styling.** No counts, no app or signal names, no
trends or comparisons, and no digits anywhere except the one clock time — two
independent derivations reached that rule (PLAN.md, Jul 26), and
`tests/test_digest_copy.py` enforces it, including a test that no template in the
module describes absence.

**Two switches, both off by default.** `DIGEST_ENABLED` globally, and
`families.digest_enabled` per family. A family that exists is not a family that
gets messaged.

**Idempotency is the database's job.** The scheduler asks `digest_sends` what it
has already sent — never its own memory. Restart mid-pass, re-run the pass, ping
again: still one message. One message goes out per recipient, and one row is
recorded per parent that message vouched for, so an aggregated evening summary
leaves an audit trail naming everyone it covered and two timezone groups in one
family cannot collide on the unique index.

One known window, accepted deliberately: a crash between the provider accepting a
message and its rows landing would re-send on the next pass. A duplicate "good
morning" is a harmless oddity; a silent loss is a missing reassurance. Revisit if
a digest ever carries anything heavier than reassurance.

Delivery goes through a channel abstraction: Twilio SMS today, a WhatsApp
template stub that honestly reports "not sent" until Meta verification lands, and
a log-only fallback when no credentials are configured (rows record `log`, so a
`digest_sends` row never claims an SMS nobody sent). A failed send is retried
once, then recorded as failed with a `digest_delivery_failed` ops alert — the row
holds the slot so the next pass does not re-dial.

A member on a channel that is not live yet (WhatsApp, today) is skipped without
any attempt and **without a row**: a failed row would hold that day's slot and
eat the first real digest on the day the channel goes live. The founder is told
once per member per day instead. Likewise, an enabled family with no member who
has both a channel and a phone number is a misconfiguration, not a quiet day, and
gets a `digest_unroutable` ops row once per day.

Ops alert kinds from the digest engine — all founder-only: `digest_skipped`
(a quiet parent omitted), `digest_delivery_failed`, `digest_channel_unavailable`,
`digest_unroutable`.

## Running the tests

RLS cannot be tested against a fake, so the suite needs a real Postgres. Two
supported ways:

**Local Postgres (what CI uses).** Any Postgres 14+ will do:

```bash
# Debian/Ubuntu, or use a container: docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16
service postgresql start
su postgres -c "psql -c \"alter user postgres with password 'postgres'\""
su postgres -c "createdb kettle_test"

pip install -r product/requirements-dev.txt
pytest product/tests            # or just `pytest` for the whole repo
```

The suite reads `TEST_DATABASE_URL`, defaulting to
`postgresql://postgres:postgres@127.0.0.1:5432/kettle_test` — the standard GitHub
Actions `postgres` service-container credentials, which is why that default is a
throwaway and not a secret.

If no Postgres is reachable the product tests **skip** rather than fail, so the
pilot suite still runs on a bare machine. The skip reason says so in words:

```
product suite SKIPPED — no Postgres reachable; this is NOT a green run of
spec 002. Tried postgresql://... (OperationalError).
```

`-rs` is in the root pytest `addopts` so that reason always appears in the
summary — otherwise a run that skipped everything just says "56 skipped", which
reads as green.

In CI that fallback is off: `.github/workflows/ci.yml` runs both suites against a
Postgres service container and sets `KETTLE_REQUIRE_POSTGRES=1`, which turns the
skip into a hard failure. A missing database on a developer laptop is a machine
without Postgres; in CI it is a broken pipeline. Setting that variable locally
gives you the same strictness.

Each session drops and recreates `public`, then applies
`migrations/local/0000_supabase_shim.sql` followed by the real numbered
migrations. The shim creates only what a hosted Supabase project already has —
the `auth` schema, `auth.uid()`, and the `anon`/`authenticated`/`service_role`
roles — so the policies under test are the exact ones that ship.

**Supabase CLI.** `supabase start` gives you the same surface plus Studio; point
`TEST_DATABASE_URL` at the printed DB URL and skip the shim (it is already there).
Requires Docker.

```bash
ruff check .        # from the repo root
```

## Deploy

### 1. Supabase project

```bash
# Create a project in the Supabase dashboard, then from its SQL editor or psql:
psql "$DATABASE_URL" -f migrations/0001_init.sql
psql "$DATABASE_URL" -f migrations/0002_rls.sql
psql "$DATABASE_URL" -f migrations/0003_revoke_anon_rpc.sql
psql "$DATABASE_URL" -f migrations/0004_revoke_residual_table_privileges.sql
psql "$DATABASE_URL" -f migrations/0005_digest.sql
psql "$DATABASE_URL" -f migrations/0006_digest_sends_per_parent.sql

# or, equivalently:
DATABASE_URL=... python -m scripts.migrate
```

Do **not** apply `migrations/local/` to a real Supabase project — those objects
already exist there.

`DATABASE_URL` is the service-role connection string (Settings → Database →
Connection string; use the pooler URI in production). It bypasses RLS by design,
because the ingestion service writes on behalf of every family. Treat it as the
most sensitive value in the system and never hand it to a client.

### 2. Fly app

```bash
cd product
fly launch --no-deploy            # sets `app` in fly.toml; keep the rest

fly secrets set \
  DATABASE_URL="postgresql://...supabase..." \
  NTFY_TOPIC="kettle-ops-$(python3 -c 'import secrets; print(secrets.token_urlsafe(12))')" \
  IP_HASH_SALT="$(python3 -c 'import secrets; print(secrets.token_hex(16))')"

fly deploy
curl -s https://kettle-api.fly.dev/healthz   # {"db": true}
```

`auto_stop_machines = "off"` is load-bearing, not a preference: the heartbeat is an
in-process background task, so a stopped machine is a monitor that never fires. It
must be the string `"off"` — Fly's tooling ignores the boolean.

### 3. Provision a family

```bash
DATABASE_URL=... PUBLIC_BASE_URL=https://kettle-api.fly.dev \
  python -m scripts.provision --family "Sharma" \
    --parent "Amma" --parent "Appa:America/Chicago" \
    --owner-email child@example.com

DATABASE_URL=... python -m scripts.provision --demo
```

It prints, per person: the device token, one ready-to-use ping URL per signal, and
the name of the shortcut that URL belongs in ("Kettle — Amma WhatsApp"). A
per-parent timezone (`Appa:America/Chicago`) overrides the family's, which is how
"Mom is visiting Texas" becomes a data change rather than a code change.

Nobody types these URLs. They ship inside pre-built shortcuts delivered as tapped
iCloud links or a QR scan (spec 005).

### 4. Revoke a lost phone

```bash
DATABASE_URL=... python -m scripts.provision --revoke <device_token>
```

Prints the family, person and platform it just killed, so you can confirm you got
the right phone before you put the laptop down:

```
Revoked device …7Q4Mxb
  family:   Sharma
  parent:   Amma
  platform: ios_shortcuts
```

Tokens are per device, so this leaves every other phone in the family working —
that ping route starts returning `403` and nothing else changes. An unknown token
is refused with a message and a non-zero exit, never a silent success. Running it
twice is safe: the second run reports "Already revoked" and keeps the original
revocation time.

## Environment variables

| Var | Meaning | Default |
|---|---|---|
| `DATABASE_URL` | Supabase service-role Postgres URI | **required**, no default |
| `NTFY_TOPIC` | ops alert topic (secret) | empty = log-only |
| `IP_HASH_SALT` | salt for the IP hash | random per boot |
| `DEFAULT_TZ` | default family timezone | `Asia/Kolkata` |
| `PUBLIC_BASE_URL` | base URL printed into provisioned links | `https://kettle-api.fly.dev` |
| `HEARTBEAT_LOOP` | `0` disables the background loops (tests) | `1` |
| `DIGEST_ENABLED` | global digest kill-switch | **off** |
| `DIGEST_MORNING_CUTOFF_HOUR` | no "day started" at/after this local hour | `14` |
| `DIGEST_EVENING_HOUR` / `_MINUTE` | parent-local summary time | `20` / `30` |
| `TWILIO_ACCOUNT_SID` / `_AUTH_TOKEN` / `_FROM` | SMS delivery (secrets) | unset = log-only |
| `TEST_DATABASE_URL` | tests only | local `kettle_test` |
