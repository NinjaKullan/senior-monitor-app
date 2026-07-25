# Spec 001 — Pilot Webhook Backend

*Owner: Hema. PM: Fable 5 (Cowork). Implementer: Claude Code (Opus 5), cloud container. Status: ready to build. Target: deployed by Sat Jul 26 so phones can be instrumented this weekend.*

Read `/CLAUDE.md` and `docs/pilot-protocol.md` before implementing. The hard constraints there are non-negotiable.

---

## 1. Purpose

Receive content-free routine pings from two iPhones (Mom, Dad — Chennai, IST) via iOS Shortcuts, store them, show a status page, and alert **the founder only** (never family, never parents) when a device goes silent — which catches dead Shortcuts and is also the product's core logic in embryo.

This is Phase-1 pilot infrastructure. **No thresholds, no ML, no family alerts, no escalation ladder execution.** Shadow alerting (Phase 2, Day 15+) will be a separate spec.

## 2. Stack & deployment

- Python 3.12, FastAPI, uvicorn, SQLite (WAL mode), stdlib `zoneinfo` for IST.
- Single app module is fine (`app/main.py` + `app/db.py`); no ORM required.
- Deploy: Fly.io, single small VM, persistent volume mounted at `/data`; DB at `/data/pilot.db` (env-overridable for local dev/tests).
- Include `Dockerfile`, `fly.toml` (with volume + health check on `/healthz`), `requirements.txt` (pinned), `.env.example`.
- Founder alerts: ntfy.sh — `POST https://ntfy.sh/{NTFY_TOPIC}`. Topic from env; treat it as a secret (it's the only auth ntfy has).

### Environment variables

| Var | Meaning | Default |
|---|---|---|
| `PING_TOKEN` | shared secret required on every request | required, no default |
| `NTFY_TOPIC` | founder alert topic | required in prod; empty = log-only |
| `DB_PATH` | SQLite path | `/data/pilot.db` |
| `TZ_DISPLAY` | display timezone | `Asia/Kolkata` |

## 3. Data model

```sql
pings(id INTEGER PK, who TEXT, signal TEXT, ts_utc TEXT, ip_hash TEXT)
labels(id INTEGER PK, date_ist TEXT, who TEXT, note TEXT, created_utc TEXT)
alerts(id INTEGER PK, kind TEXT, who TEXT, detail TEXT, ts_utc TEXT)   -- heartbeat events, founder-only
status_views(id INTEGER PK, date_ist TEXT, ts_utc TEXT)               -- for blinding audit
```

- `who` ∈ {`mom`, `dad`}. `signal` ∈ {`whatsapp`, `youtube`, `news`, `charge_on`, `charge_off`}. Alarm-grade = {whatsapp, youtube, news}.
- **Timestamps are server-side UTC only.** Ignore any client-supplied time.
- Store **only** allowlisted fields. Any extra query params are dropped and never persisted (this is a privacy promise, not a nicety — Dad may audit).
- `ip_hash` = salted SHA-256 truncated; ops/debug only, never displayed.

## 4. Endpoints

All endpoints require `token=<PING_TOKEN>` (query param; Shortcuts can't do headers easily). Wrong/missing token → 403, nothing stored, no information leaked in the body.

### `GET|POST /ping?token=&who=&signal=`
- Valid → insert row, return 200 with tiny plain-text body (`ok`). Must respond fast; Shortcuts has short timeouts.
- Invalid `who`/`signal` → 400, not stored.
- Idempotency/dedupe: collapse identical (who, signal) pings within 60s into one row (Shortcuts sometimes double-fires).

### `GET /status?token=`
HTML, phone-friendly, no JS frameworks (inline CSS fine). Shows, all in IST:
- Per person × signal: last-seen time + humanized gap ("2h 14m ago").
- Per person: today's ping count, current gap since last **alarm-grade** ping.
- Heartbeat state (last check, last alert if any).
- Recent 50 pings table.
- **Blinding interstitial:** if today (IST) has no label row for each parent, `/status` first renders a form: "Log today's labels before viewing data" with a one-tap "Nothing unusual" button per person, plus a free-text note. Only after labels exist for today does the data render. Log every status view in `status_views`. This enforces the pilot protocol's write-labels-before-looking rule.

### `GET|POST /labels?token=`
Add/view labels directly (date defaults to today IST; person; note). Also `GET /labels.csv?token=`.

### `GET /pings/{who}?token=`
Full ping history for one person, plain table. This is the Dad-transparency view ("you can see every ping it has ever sent"). Content: timestamp + signal name only.

### `GET /export.csv?token=`
All pings as CSV (`who,signal,ts_utc,ts_ist`). This is the Phase-1 analysis input.

### `GET /healthz`
No token. Returns 200 + `{"db": true}`. For Fly checks only.

## 5. Heartbeat monitor (founder-only)

Async background task inside the app (no external cron):

- **Noon check (12:00 IST):** for each person, if zero alarm-grade pings since 05:00 IST → ntfy: `"⚠️ {who}: no routine pings this morning (last seen {X} ago). Check Shortcut or check in."`
- **Evening check (20:00 IST):** same rule over the full day; only fires if noon alert for that person already fired and still zero pings (escalation of the *ops* concern, not the family ladder).
- **Infra check (hourly):** if *no device at all* has pinged in 24h → `"🔧 Pipeline silent 24h — server up but nothing arriving."`
- Every alert also inserted into `alerts` table. Alerts are deduped: max one per (kind, who) per IST day.
- If `NTFY_TOPIC` unset, log-only. Never any path that notifies anyone but the founder.

## 6. Non-goals (do not build)

No family notifications. No senior-facing anything. No thresholds/percentile math (Phase-2 spec). No accounts/multi-tenant. No location, content, or device fields. No analytics/tracking. No admin UI beyond the pages above.

## 7. Acceptance criteria

1. `curl "https://<app>/ping?token=T&who=mom&signal=whatsapp"` → 200, row visible on `/status` within one refresh, IST times correct.
2. Bad token → 403 and zero DB writes (test asserts row count unchanged).
3. Duplicate ping within 60s stored once.
4. Extra query params (`&location=x&text=y`) are absent from DB (assert schema + raw row).
5. `/status` without today's labels shows the interstitial, not data; after submitting labels, shows data.
6. Heartbeat: with a frozen/fake clock at 12:01 IST and no pings since 05:00 IST for `dad`, exactly one ntfy POST is attempted (mock HTTP), one `alerts` row written; re-running the check writes nothing (dedupe).
7. `/export.csv` round-trips into pandas with correct dtypes.
8. Fresh deploy on Fly with empty volume boots, creates schema, passes `/healthz`.

## 8. Test plan

pytest + httpx TestClient; temp SQLite per test; freezegun (or injectable clock) for heartbeat tests; mock ntfy HTTP. Cover: all acceptance criteria above, plus IST/UTC conversion around midnight (a 23:50 IST ping must land on the right IST day for labels/heartbeat).

## 9. Deliverables checklist

- [ ] `app/` code, tests passing, `ruff check` clean
- [ ] `Dockerfile`, `fly.toml`, `requirements.txt`, `.env.example`
- [ ] `README.md`: local run, deploy steps, and the two Shortcuts URL templates:
  - Mom WhatsApp: `https://<app>.fly.dev/ping?token=<T>&who=mom&signal=whatsapp` (repeat per app/person)
- [ ] Nothing in git history contains the real token or ntfy topic
