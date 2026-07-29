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
throwaway and not a secret. If no Postgres is reachable the product tests **skip**
with that reason rather than fail, so the pilot suite still runs on a bare machine.
A green run that skipped them is not a green run of this spec.

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
iCloud links or a QR scan (spec 005). Tokens are per device, so a lost phone is one
revoke that leaves every other phone in the family working.

## Environment variables

| Var | Meaning | Default |
|---|---|---|
| `DATABASE_URL` | Supabase service-role Postgres URI | **required**, no default |
| `NTFY_TOPIC` | ops alert topic (secret) | empty = log-only |
| `IP_HASH_SALT` | salt for the IP hash | random per boot |
| `DEFAULT_TZ` | default family timezone | `Asia/Kolkata` |
| `PUBLIC_BASE_URL` | base URL printed into provisioned links | `https://kettle-api.fly.dev` |
| `HEARTBEAT_LOOP` | `0` disables the background monitor (tests) | `1` |
| `TEST_DATABASE_URL` | tests only | local `kettle_test` |
