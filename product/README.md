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
| `GET /s/{slug}` | one parent's setup page (spec 005b), or a plain-language dead end |
| `GET /s/{slug}/state` | the page's live verify check; `?since=` compares against alarm-grade pings only |
| `POST /outbound/reply` | a parent's reply to the ask (spec 007); **404 unless `OUTBOUND_REPLY_TOKEN` is set** |
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
| Template category | the live ask template (`TWILIO_ASK_CONTENT_SID`) is anything but approved/Utility at Twilio's Content API, checked once a UTC day | one row, no family (0024) |

Each `(kind, parent-or-family)` fires at most once per local day, so running every
minute is safe. Every alert is written to `ops_alerts` and sent to the founder's
ntfy topic. Nothing family- or parent-facing fires from the heartbeat itself;
family-facing sending lives in the digest (003) and the ladder (004), each behind
its own switches.

The template-category row (DECISIONS 262/267) is the one alert about no family:
Meta can re-review a template into Marketing without notice, and a non-Utility
template stops US delivery with no error on our side. The watch is a no-op
until the three Twilio settings exist; a failed fetch is a warning and an hourly
retry, never an alert.

## Digests (spec 003) — RETIRED

Superseded by spec 007 (DECISIONS 141). The engine, its copy module and its
channel abstraction are deleted. **`digest_sends` is deliberately left in**
place: `webapp/src/lib/queries.ts` declares it in the app's read surface and
the Digests screen renders from it, while spec 007's `sent_messages` is RLS
deny-all by design and cannot be read by a client at all. Moving that screen is
a decision in front of a webapp pass, not a line in a migration.

The rule worth carrying forward, which 007 states differently: reassurance
requires evidence. The old engine sent nothing at all on a quiet morning and
told the founder instead; 007 reports the absence to the child in words that
do not interpret it, and asks the parent first.

## Escalation ladder (spec 004) — RETIRED

Superseded by spec 007 (DECISIONS 141). The module, its copy, its CLI and the
`/twilio/inbound` webhook are deleted; migration 0013 drops its tables where
they never held a row and archives them where they did. The ask and the
follow-on live in the outbound channel now. What the old engine had that 007
does not yet — the unreachable-handset distinction, the all-clear, the max-gap
trigger, the per-family shadow/live gate — is listed in DECISIONS 141 rather
than lost.

## The outbound channel (spec 007, Wave A)

Kettle's own voice, and in this wave it does not use it. The decision core is
complete and runs in production **dark**: it evaluates each day, writes its
ledger, and hands every message to a transport that writes a log line. Waves B
to D add transports that actually send, each gated on one founder errand.

Three message kinds and nothing else speaks: the **digest** to the circle twice
daily, the **ask** to the parent on a quiet morning, and the **follow-on** to
the circle only after the ask has gone unanswered past a grace window.

"The circle" (spec 015 §7, migration 0025) is every member with `mail` on and an
email on file, admins first. Each slot fans out to all of them; per-member
idempotency lives in `digest_sends`, and the slot's ledger row says 'sent' only
when everyone has been reached — a partial failure stays retryable and the
retry reaches only the members it missed. Nobody listening is a skip plus one
`circle_unreachable` ops alert per family per day. Membership itself changes
only through the five `app_*` functions in 0025 (add, remove, set role, set
mail, leave); the last admin cannot leave, be demoted or be removed.

| Piece | Where |
|---|---|
| Quiet-morning evaluation, the scheduler, the transport seam | `kettle/outbound.py` |
| Every string the channel can say | `kettle/outbound_templates.py` |
| The sent-once ledger | migration 0012, `sent_messages` |
| Reply intake | `POST /outbound/reply` |

**v1 constants**, per parent, in her own timezone: the morning window opens at
06:00, the ask threshold is 11:00, the follow-on grace is 2 hours, and the two
digests go at 08:30 and 20:30. Per-family configuration is a later spec.

Four properties are structural rather than remembered:

- **Parent-first cannot be skipped.** A follow-on is reachable only through a
  ledger row proving the ask already went, unanswered, more than the grace
  window ago. Delete that row and the deadline passes in silence — there is no
  query that returns a follow-on without it.
- **Nothing is interpreted.** A quiet morning is the *absence* of an
  alarm-grade ping in a window, reported as absence. Charger and `device_alive`
  rows are invisible to the evaluator because the grade comes from each
  parent's own allowlist (law #6).
- **Sent once.** Every send goes through a unique index on
  `(family_id, parent_id, local_date, kind)`, so a scheduler that crashes and
  restarts mid-day re-decides and records nothing. Every acceptance scenario
  runs the scheduler twice and asserts the second run is silent.
- **No body is ever stored.** The ledger keeps a template *id*. Templates are
  code, which is also what makes the copy law scannable over all of them.

`/outbound/reply` **does not exist until `OUTBOUND_REPLY_TOKEN` is set** — it
404s. Cancelling a follow-on is safety-relevant, and an unauthenticated route
would let anyone who knows a number suppress an escalation. It reads the sender
and nothing else: what she said is content, and this product does not hold
content. Wave C swaps the shared secret for the provider's signature.

The gate to Wave B is human: the founder family runs Wave A dark for 48 hours
and the ledger is reviewed against what actually happened.

## Child PWA (spec 005a)

The read-only demo app lives in `webapp/` and is deployed separately. It talks to
this same database as the `authenticated` role, filtered by the same policies —
`webapp/README.md` has the deploy steps and the demo script.

`0008_claim_membership.sql` is the one backend piece it needs:
`members.auth_user_id` is null until the invited person signs up, and that RPC
links them at first login. SECURITY DEFINER, matching on the **verified** email
from the JWT rather than any parameter, filling only nulls, and linking every
matching membership — one person genuinely can belong to two families. Grants
follow the 0004 doctrine: `authenticated` only, `anon` explicitly revoked.

## Shortcut forge (spec 005e)

Provisioning prints ping URLs; the forge turns them into files a parent can
install by tapping. Each generated `.shortcut` is a plist holding exactly one
`Get Contents of URL` action, named `Kettle — {Signal}` (no parent name — an iPhone tile truncates it away,
DECISIONS 96a) — the same
string the app's tripwire health view shows when that signal needs repair, so a
family that reads "her WhatsApp tripwire needs attention" is looking for a
shortcut with that name on the phone.

### The founder loop

```bash
cd product

# 1. Generate (anywhere — Linux, CI, the container). Writes out/shortcuts/,
#    which .gitignore covers, and verifies what it wrote before it exits.
DATABASE_URL=... python -m scripts.forge \
    --parent "Amma" --base-url https://kettle-api.fly.dev

# 2. Sign (macOS only, signed in to iCloud, online).
./scripts/forge-sign.sh out/shortcuts out/signed

# 3. Send the signed files — AirDrop if you are in the room, WhatsApp if not.
# 4. On the phone: tap the file, "Add Shortcut". It appears in the library
#    under the name above. Nothing to type, nothing to assemble.
# 5. Build the automation: Shortcuts -> Automation -> + -> App -> WhatsApp ->
#    Is Opened -> Run Immediately -> Next -> pick the pre-made shortcut. The
#    automation wrapper is the one irreducibly manual step; the shortcut it
#    runs is not.
# 6. Verify for real: open WhatsApp on that phone, then check /status (or the
#    child app). A ping that does not arrive is a setup problem you want to
#    find while you are still holding the phone.
```

`--device-token <token>` selects a device directly when a person has more than
one, or when you are working from a provisioning printout rather than a name.
`--verify out/shortcuts` re-checks a directory at any time; `--inspect FILE`
prints a real shortcut's plist shape beside the forge's, which is how the format
assumptions in `specs/DECISIONS.md` item 69 get confirmed against a Mac.

### Adding a signal to the vocabulary (the DECISIONS 94 procedure)

A new key is a two-file code change with a drift test, never a database row:

1. `kettle/signals.py` — add the key to `SIGNAL_LABELS` (the humanised name is
   the shortcut's name on the phone) and to `ALARM_GRADE` (may this signal ever
   speak for a person? Charger/timer plumbing may not — law #6).
2. `webapp/src/lib/signalNames.ts` — the same key and label.
   `test_webapp_signal_names_match_the_shortcuts_on_the_phone` fails until the
   two agree, and the webapp's pinned copy-law exemption fails until the new
   name is added there *consciously* (`TRIPWIRE_NAME_EXEMPTION`).
3. If the parent should get it: `--signals` at provisioning, or
   `--set-signals <device_token> --signals …` for a live parent.
4. A browser-ish or ambiguous signal needs its consent sentence written into the
   setup page's first screen (`product/kettle/setup_copy.py`) before the call,
   not during — the one-pager it used to point at is gone, and consent is
   carried by the product (DECISIONS 125a). Financial apps are excluded at every
   tier, permanently.

### Treat the emitted files like the token

The device token is inside the URL, and anyone holding it can post pings as that
phone. So: files are written `0600`, `out/` and `*.shortcut` are both
gitignored (asserted by `git check-ignore` in `product/tests/test_forge.py`),
`--verify` fails on any file carrying a credential other than the token, and
both directories should be deleted once the phone is set up. Sending one is
sending a password — pick the channel accordingly.

Revocation is the recovery path: `python -m scripts.provision --revoke <token>`
kills exactly that device. A revoked device forges nothing, so a stale
`forge --device-token …` in someone's shell history cannot re-arm a lost phone.

### What `--mode anyone` asks of the receiving phone

`shortcuts sign --mode anyone` sends the shortcut to Apple for validation and
returns a signed file that **anyone** can import — as opposed to
`--mode people-who-know-me`, which restricts import to the signer's contacts.
Signing therefore needs a Mac that is online and signed in to iCloud; it is not
an offline operation.

On iOS 15 and later the receiving phone should need nothing: Apple removed the
standalone **Allow Untrusted Shortcuts** toggle, and a properly signed shortcut
imports on its own. **This has not been confirmed on a real handset from here**
— the container has no Mac to sign with and no phone to import to — so treat it
as expected behaviour, not established fact, and confirm it on the first real
send. If a phone does refuse the import, the fallback is Settings → Shortcuts →
Allow Untrusted Shortcuts, which only appears after the Shortcuts app has been
opened at least once. Record the answer in DECISIONS 69 either way; it decides
whether the 005b wizard needs a "turn this on first" step.

Sources for the above: [Apple, *Run shortcuts from the command
line*](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac);
[Apple, *Share shortcuts on iPhone or
iPad*](https://support.apple.com/guide/shortcuts/share-shortcuts-apdf01f8c054/ios);
[ss64, `shortcuts` command reference](https://ss64.com/mac/shortcuts.html).

### Scale (not built)

This is a founder tool for the beta. The remaining gap is a macOS CI runner
that signs a family's files at provisioning time, which removes the founder's
laptop from the loop entirely. Nothing here needs to change for that — the
generation half already runs anywhere; only the signing half needs the runner.
Note the files still travel by WhatsApp document attachment either way:
DECISIONS 117 closed the hosted-delivery experiment (iOS Safari downloads a
served `.shortcut` rather than opening the Add Shortcut sheet), so no server
of ours serves shortcut files.

## Setup links and the parent setup page (spec 005b)

Provisioning mints one **setup link** per device — a 144-bit url-safe slug,
seven-day expiry — and prints the page URL beside the token. The page at
`/s/{slug}` carries what only a page can: consent in plain language, the
visual steps, the pre-empted Apple permission warning, and the live
verify-by-prediction check. It never serves a file and never shows a token;
files travel by WhatsApp document attachment (DECISIONS 117).

```bash
# A fresh link for an existing parent (the Appa case). Issuance is rotation:
# the previous link stops answering, including copies already in a chat.
python -m scripts.provision --setup-link <DEVICE_TOKEN>
```

The link lives and dies with its device: `--revoke` kills the page too. An
expired or replaced link serves a plain-language dead end naming the family's
owner — never steps, never a file. The child app reads `setup_links` (RLS,
select-only) to show each parent's link as a forwardable card with a WhatsApp
share intent; issuance stays service-side because a client that could write
links could mint indefinite credentials.

The verify check (`/s/{slug}/state?since=…`) greens **only on an alarm-grade
ping strictly after the screen opened** — law #6 applied to setup: a charger
edge or a daily timer must never be what turns the named card green, and a
stale first-run ping must never satisfy the crossed-pair drill. Baselines come
from the endpoint's own `now`; no client clock is consulted.

The rehearsal script for a full run — including the crossed-URL drill and the
honest tap count — is `docs/005b-test-script.md`.

## Waitlist (spec 006)

`POST /waitlist` is the landing page's one write, and migration `0009` is the
table behind it. Both are shaped around not leaking:

* A **duplicate signup is indistinguishable from a first one** — same status,
  same body — so the endpoint cannot be asked whether an address is on the list.
* A **honeypot hit looks exactly like a success.** Telling a bot it was caught
  teaches whoever wrote it which field to leave alone.
* The row holds **an address and one fixed-choice answer**. No IP, no user agent,
  no referrer; the page carries no analytics (law #4) and this endpoint does not
  become the analytics by the back door. A test asserts the column list.
* The table has RLS on and **no policy at all** — the same shape `ops_alerts`
  has carried since 002. Nothing reads it from a client, so there is nothing to
  write a policy for, and 0004's revoked defaults plus an explicit revoke in
  0009 mean neither client role holds a privilege either.
* `parent_phone` is a CHECK constraint, not validation (standing structure 39).
  The answer decides Wave 2 platform priority, and a typo in it is a silently
  wrong decision months later.

`WAITLIST_ORIGINS` sets the browser origins allowed to POST — an explicit list,
never a wildcard. It defaults to `heykettle.com`, `www.heykettle.com` and the
Vite dev server (DECISIONS 142).

**It is an env var on kettle-api, and setting it replaces the default outright** —
`_origins()` falls back to the shipped tuple only when the variable is empty, so a
partial list is a lockout, not an addition. During the domain transition the
fly.dev origin has to be named explicitly, because it is deliberately not in the
default:

```bash
fly secrets set -a kettle-api \
  WAITLIST_ORIGINS="https://heykettle.com,https://www.heykettle.com,https://kettle-site.fly.dev"
```

Drop the fly.dev entry once the old host stops being used; the two apex origins are
then the same as the default and the variable can be unset entirely.

Counting signups is `python -c` against the database, deliberately: there is no
endpoint that reads this table.

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
psql "$DATABASE_URL" -f migrations/0007_ladder.sql
psql "$DATABASE_URL" -f migrations/0008_claim_membership.sql

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
the name of the shortcut that URL belongs in ("Kettle — WhatsApp"). A
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
| `WAITLIST_ORIGINS` | comma-separated browser origins allowed to POST /waitlist (default: the heykettle.com pair plus localhost dev; setting it REPLACES the default) |
| `OUTBOUND_ENABLED` | global outbound-channel kill-switch; "on" still reaches nobody in Wave A | **off** |
| `OUTBOUND_REPLY_TOKEN` | shared secret `/outbound/reply` requires; empty means the route 404s | empty |
| `TEST_DATABASE_URL` | tests only | local `kettle_test` |
