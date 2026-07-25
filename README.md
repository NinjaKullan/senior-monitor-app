# Kettle — pilot webhook backend

Phase-1 infrastructure for the 30-day family pilot (spec `specs/001-pilot-backend.md`).

Two iPhones in Chennai fire iOS Shortcuts automations at this server when an app is
opened. The server stores a person, a signal name and its own UTC clock reading —
nothing else — renders a status page in IST, and alerts **the founder only** when a
device goes quiet.

## What is stored

The entire record of a ping is four columns:

| Column | Example | Why |
|---|---|---|
| `who` | `mom` | which phone |
| `signal` | `whatsapp` | which routine, by name only |
| `ts_utc` | `2026-07-25T09:15:03Z` | **server-side** clock; client time is ignored |
| `ip_hash` | `4f9c…` (16 hex) | salted, truncated SHA-256, ops/debug only, never displayed |

No message content, no browsing content, no audio, no location, no device identity,
no keystrokes, no third-party analytics. Extra query params on a request are read by
nothing and stored nowhere — see `tests/test_ping.py::test_extra_query_params_are_never_stored`.
`/pings/mom` and `/pings/dad` show a parent the complete record at any time.

Uvicorn runs with `--no-access-log` deliberately: access logs would otherwise capture
full request URLs, which contain the shared token.

## Endpoints

Every endpoint except `/healthz` requires `?token=<PING_TOKEN>` (query param — iOS
Shortcuts cannot set headers easily). A wrong or missing token is a bare `403`.

| Endpoint | Purpose |
|---|---|
| `GET\|POST /ping?token=&who=&signal=` | record a ping; returns `ok`. Identical `(who, signal)` within 60s collapses into one row |
| `GET /status?token=` | founder dashboard (IST). Blocked behind today's labels — see below |
| `GET\|POST /labels?token=` | blinded ground-truth label log; `who`, optional `note`, optional `date_ist` |
| `GET /labels.csv?token=` | label log as CSV |
| `GET /pings/{who}?token=` | full history for one person: time + signal name only |
| `GET /export.csv?token=` | all pings as `who,signal,ts_utc,ts_ist` — the Phase-1 analysis input |
| `GET /healthz` | `{"db": true}`, no token, for Fly health checks |

`who` ∈ `mom`, `dad`. `signal` ∈ `whatsapp`, `youtube`, `news`, `charge_on`, `charge_off`.
Alarm-grade (deliberate app opens) = `whatsapp`, `youtube`, `news`.

### Label blinding

`/status` will not show data until **both** parents have a label row for today (IST).
It first renders a form with a one-tap "Nothing unusual" button per person plus a
free-text note. This enforces the pilot protocol's write-the-label-before-you-look
rule in software. Every view — blocked or not — is recorded in `status_views`.

### Heartbeat monitor (founder-only)

An in-process background task, checked once a minute, with fixed IST wall-clock rules.
No thresholds, no percentiles, no inference — that is Phase 2 and a separate spec.

| Check | Rule | Alert |
|---|---|---|
| Noon (12:00 IST) | zero alarm-grade pings since 05:00 IST | `⚠️ {who}: no routine pings this morning (last seen X ago)…` |
| Evening (20:00 IST) | still zero, **and** the noon alert already fired | `⚠️ {who}: still no routine pings today…` |
| Infra (hourly) | no device at all has pinged in 24h | `🔧 Pipeline silent 24h — server up but nothing arriving.` |

Each `(kind, who)` fires at most once per IST day. Every alert is written to `alerts`
whether or not delivery succeeds. With `NTFY_TOPIC` empty the monitor is log-only.
There is no code path that notifies a parent or any other family member.

## Local run

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # fill in PING_TOKEN, set DB_PATH=./pilot.db

export PING_TOKEN='...' DB_PATH=./pilot.db
uvicorn app.main:create_app --factory --reload --port 8080

curl "http://localhost:8080/ping?token=$PING_TOKEN&who=mom&signal=whatsapp"
open "http://localhost:8080/status?token=$PING_TOKEN"
```

Tests and lint:

```bash
pytest
ruff check .
```

## Deploy to Fly.io

```bash
fly launch --no-deploy                 # sets `app` in fly.toml; keep the rest
fly volumes create kettle_data --size 1 --region sin

fly secrets set \
  PING_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')" \
  NTFY_TOPIC="kettle-$(python3 -c 'import secrets; print(secrets.token_urlsafe(12))')" \
  IP_HASH_SALT="$(python3 -c 'import secrets; print(secrets.token_hex(16))')"

fly deploy
fly logs                               # confirm boot + schema creation
curl -s https://<app>.fly.dev/healthz  # {"db": true}
```

Then subscribe to the ntfy topic on the founder's phone (ntfy app → Subscribe →
paste the topic). Read the values back with `fly secrets list` (names only) or from
the shell you generated them in — they are never printed by the app and never in git.

Notes:
- `auto_stop_machines = false` is required. The heartbeat is in-process; a stopped
  machine is a monitor that never fires.
- The volume holds the entire pilot dataset. `fly ssh console -C "ls -l /data"` to
  check it, and pull backups with `fly ssh sftp get /data/pilot.db`.
- "Last heartbeat check" on `/status` is in-process state and resets on each deploy;
  the `alerts` table is the durable record.

## iOS Shortcuts setup

On each parent's phone: Shortcuts → Automation → New Personal Automation → **App** →
choose the app → **Is Opened** → Add Action → **Get Contents of URL** → paste the URL
below → turn **off** "Ask Before Running" (Run Immediately). Three automations per phone.

Replace `<app>` with the Fly hostname and `<T>` with `PING_TOKEN`.

**Mom's phone**

```
https://<app>.fly.dev/ping?token=<T>&who=mom&signal=whatsapp
https://<app>.fly.dev/ping?token=<T>&who=mom&signal=youtube
https://<app>.fly.dev/ping?token=<T>&who=mom&signal=news
```

**Dad's phone**

```
https://<app>.fly.dev/ping?token=<T>&who=dad&signal=whatsapp
https://<app>.fly.dev/ping?token=<T>&who=dad&signal=youtube
https://<app>.fly.dev/ping?token=<T>&who=dad&signal=news
```

Optional charger automations (Automation → **Charger** → Is Connected / Is Disconnected),
corroborating only — they never satisfy the heartbeat check:

```
https://<app>.fly.dev/ping?token=<T>&who=mom&signal=charge_on
https://<app>.fly.dev/ping?token=<T>&who=mom&signal=charge_off
```

Verify by opening each app once and refreshing `/pings/mom` — new rows within seconds.

## Environment variables

| Var | Meaning | Default |
|---|---|---|
| `PING_TOKEN` | shared secret on every request | **required**, no default |
| `NTFY_TOPIC` | founder alert topic (secret) | empty = log-only |
| `DB_PATH` | SQLite path | `/data/pilot.db` |
| `TZ_DISPLAY` | display timezone | `Asia/Kolkata` |
| `IP_HASH_SALT` | salt for the IP hash | random per boot |
| `HEARTBEAT_LOOP` | `0` disables the background monitor (tests) | `1` |
