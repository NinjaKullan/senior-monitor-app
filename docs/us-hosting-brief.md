# Move the database and the product hosts to the United States (brief for Claude Code)

Founder ruling, 2026-10-18 (DECISIONS 365). The privacy page says data is stored in
the United States. Today the Supabase project is in ap-south-1 (Mumbai) and
kettle-api and kettle-app run in Fly region sin (Singapore), a leftover of the
Chennai pilot. The page stays as written; the hosting moves to match it. One
family's worth of data, so the move is small now and only gets bigger.

Target: Supabase project in us-east-1; kettle-api and kettle-app in Fly region
iad (where kettle-site already is). Nothing changes for parents' phones, the
Twilio webhook, Resend, the assistant connectors or any public address.

## 1. Code changes (the whole list; nothing else)

1. `product/fly.toml` and `webapp/fly.toml`: `primary_region = "iad"`, comment
   updated (the Chennai latency note goes).
2. Any test or doc that pins `sin` or Mumbai as the live region (grep
   `sin"`, `ap-south`, `Mumbai`, `Singapore` across product/, webapp/, docs/,
   README files): update to iad / us-east-1. `docs/baton.md` host lines included.
3. A runbook section at the end of this file, §3, written by CC with the exact
   commands, in the order below. The PM's draft of the order is §2; CC corrects
   it where the tools say otherwise, as happened in 357.
4. No schema change, no migration, no copy change. The privacy page is not
   touched.

## 2. Cutover order (PM draft; CC rewrites as §3)

Before: founder enables two-factor on the Supabase account (done or in
progress), and confirms migration 0034 is applied on the old project.

1. Founder creates the new Supabase project (us-east-1, same org), records the
   project ref, the service-role DATABASE_URL, the publishable key, the JWKS URL.
2. PM applies migrations 0001 to 0034 in order to the new project, one file at
   a time. Empty database at this point.
3. Announce a 30-minute window. Pings that land in the window are lost; that is
   acceptable (the day's "heard from" catches up at the next ping).
4. Founder dumps data from the old project: `public` schema data only, plus
   `auth.users` and `auth.identities` data so the user ids referenced from
   public tables match. Restores into the new project. CC writes the exact
   pg_dump / psql lines, including what to exclude (supabase-owned schemas,
   sequences are reset by the restore).
5. Founder sets kettle-api secrets `DATABASE_URL` and `SUPABASE_JWKS_URL` to
   the new project (one `fly secrets set`, so one restart).
6. Founder rebuilds and deploys kettle-app with the new `VITE_SUPABASE_URL` and
   `VITE_SUPABASE_PUBLISHABLE_KEY`.
7. New project's Auth settings: site URL and redirect list copied from the old
   project (app.heykettle.com and the fly.dev host; see 357), email-code sign
   in on, the same email template.
8. Fly regions: move kettle-api and kettle-app machines to iad and remove the
   sin machines. CC names the commands (clone-then-destroy, or scale by
   region) and what to check between them (`fly machines list`).
9. Verify: `/healthz` on api.heykettle.com; sign in on the app (everyone signs
   in again; sessions do not survive a JWKS change); a Rehearsal parent's
   ping lands; the Claude connector still answers `today` without
   re-authorising (grants live in the copied tables); the weekly site email
   still schedules.
10. Old project: pause for 14 days, then delete. Update `docs/baton.md`, the
    infra facts, and the Meta data-processing form (storage: United States
    only).

## 3. Runbook (CC writes this section)

Written 2026-10-18 from §2, corrected where the tools disagree. **Rehearsed
locally** on Postgres 16 with the repo's migrations and the test shim: the
migration loop (B4), the schema comparison (B5: four planted Studio-style
differences, an index, a grant, a function and a trigger on `auth.users`, all
reported and nothing else), and the dump and restore (W2 to W4: counts and
sequences identical, the next id continues from the old value). **Not
rehearsable here:** anything on Supabase's or Fly's side. Those commands are
checked against `flyctl` v0.4.118's own help, not run.

### What changed from §2, and why

* **Migrations run from a `psql` loop, not file by file in Studio.** The loop
  stops at the first error, and nothing gets pasted. It never touches
  `product/migrations/local/` (the test shim; it must never reach Supabase).
* **New: a schema comparison before any data moves (B5).** Some migrations
  were applied by hand in Studio, so prod may not match the repo.
* **Auth settings move before the window (B6) and gain two items §2 lacked.**
  The first is custom SMTP: without it, a new project sends sign-in codes
  only to team members, a few an hour, so no family can sign in. The second
  is the JWT signing key: kettle-api's `/oauth/approve` accepts ES256 only,
  so the new project must sign with an ECC P-256 key, or every connector
  approval is refused.
* **Nobody signs in to the new project before the restore.** A sign-in
  creates an `auth.users` row, and the copied row then collides with it.
* **The dump uses `--table`, not `--schema`.** `pg_dump` ignores `-n` once
  any `-t` is given, so `public` is selected as `--table='public.*'`.
* **"Sequences are reset by the restore", made precise:** the data dump
  carries one `setval` per sequence, so ids continue from the old project's
  values. Rehearsed.
* **kettle-app's Supabase values live in `webapp/fly.toml` `[build.args]`.**
  A one-off `--build-arg` deploy would be undone by the next bare
  `fly deploy`, so the file is edited and committed (W6).
* **Secrets go in through `fly secrets import`:** one release and one
  restart, as §2 wanted, with the database password kept out of shell
  history.
* **The owed deploys go first (B1).** `fly secrets set` restarts the
  machine on the current image (baton, 294).
* **Regions move by clone, then destroy, with kettle-api's `sin` machine
  stopped as soon as the `iad` one is healthy.** While both run, both run
  the heartbeat and outbound loops. Sends are protected by
  `sent_messages_once_idx` (0012: the second insert fails), but a founder
  ntfy alert may arrive twice that minute.

### 0. Tools and variables (the founder's Mac, the day before)

```bash
brew install postgresql@17        # client tools; match the servers' major (step B2 prints it)
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
export REPO=~/Projects/senior-monitor-app
mkdir -p ~/kettle-cutover && cd ~/kettle-cutover   # outside the repo: the dump holds personal data
```

Connection strings come from the Supabase dashboard: **Connect → Session
pooler** (port 5432). `pg_dump` needs session mode, not the transaction pooler
on 6543. The direct `db.<ref>.supabase.co` host is IPv6-only. URL-encode any
special characters in the password.

```bash
export OLD_DB='postgresql://postgres.<old-ref>:<password>@<old pooler host>:5432/postgres'
export NEW_DB='postgresql://postgres.<new-ref>:<password>@<new pooler host>:5432/postgres'
```

### Before the window

**B1. Preconditions.** Two-factor is on for Supabase, Fly and Twilio (365).
The owed deploys are done: `cd product && fly deploy` (359 to 365 §2) and
`cd webapp && npm run ci && fly deploy`; `fly releases -a kettle-api` shows
the new release.

**B2. New project (founder).** Same org, region East US (North Virginia),
us-east-1. Record the project ref, the Session pooler string, the publishable
key (Project Settings → API Keys, `sb_publishable_…`) and the JWKS URL,
`https://<new-ref>.supabase.co/auth/v1/.well-known/jwks.json`. Then:

```bash
psql "$OLD_DB" -Atc 'show server_version'
psql "$NEW_DB" -Atc 'show server_version'
```

If either major is not 17, install `postgresql@<the higher major>` and use
that one's `bin`.

**B3. Signing key.** Both of these must show a key with `"kty":"EC"` and
`"crv":"P-256"`:

```bash
curl -s https://<old-ref>.supabase.co/auth/v1/.well-known/jwks.json
curl -s https://<new-ref>.supabase.co/auth/v1/.well-known/jwks.json
```

If the new one shows no keys, or no EC key: Project Settings → JWT Keys,
create an ECC (P-256) standby key and rotate to it. Check again.

**B4. Migrations 0001 to 0034 (founder; PM watching).**

```bash
cd "$REPO" && git pull && cd ~/kettle-cutover
for f in "$REPO"/product/migrations/0*.sql; do
  echo "== $f"
  psql "$NEW_DB" -q -v ON_ERROR_STOP=1 --single-transaction -f "$f" || break
done
```

Done when the last line is `== …/0034_assistant_resource.sql` with no `ERROR`
after it. 0013 prints three `NOTICE: retire 003/004: dropped …` lines; those
are expected. If a file fails, the loop stops on that file, and that file
applied nothing. Stop and report it.

**B5. Schema comparison (new; before any data moves).** Both sides go
through the same `pg_dump` and the same filter. The filter drops comments,
`SET` lines and the random `\restrict` token newer `pg_dump` writes, so only
real differences remain.

```bash
cat > outside-public.sql <<'EOF'
select 'ext', extname, extversion from pg_extension order by 2;
select 'trigger', tgrelid::regclass::text, pg_get_triggerdef(oid) from pg_trigger
  where tgrelid in ('auth.users'::regclass, 'auth.identities'::regclass) and not tgisinternal order by 3;
select 'column', table_name, column_name || ' ' || data_type from information_schema.columns
  where table_schema = 'auth' and table_name in ('users', 'identities') order by 2, 3;
select 'publication', pubname, schemaname || '.' || tablename from pg_publication_tables order by 2, 3;
select 'cron', jobname, schedule || ' ' || command from cron.job order by 2;
EOF
for side in old new; do
  url=$([ $side = old ] && echo "$OLD_DB" || echo "$NEW_DB")
  pg_dump "$url" --schema-only --no-owner --schema=public \
    | grep -v -E '^(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict )' | sed '/^$/d' > schema-$side.sql
  psql "$url" -At -F ' | ' -f outside-public.sql > outside-$side.txt
done
diff schema-old.sql schema-new.sql
diff outside-old.txt outside-new.txt
```

Reading it:

* `<` lines exist in prod only: something applied by hand in Studio, or a
  table 0013 kept on prod because it held rows. `>` lines exist in the new
  project only: something in the repo that prod never got, or got
  differently.
* `GRANT` and `REVOKE` lines matter. Supabase's defaults for a new project
  may not match July's, and 0003 and 0004 exist because of exactly that.
* `column` lines are the auth tables the data goes into. A column on the
  old side only means the restore will fail. Stop.
* A `cron.job` error on both sides means pg_cron is not installed, which
  is fine. Jobs listed on the old side only must be recreated on the new
  side.
* `ext` lines may differ in version only; that is noise.

Paste both diffs into DECISIONS. For each line the PM rules whether to apply
it to the new project by hand or accept it, and the comparison is rerun until
only accepted lines remain. **No data moves until then.**

**B6. Auth settings on the new project (founder; copy from the old one,
side by side).**

* URL Configuration: Site URL `https://app.heykettle.com`; Redirect URLs
  exactly as the old project lists them (357).
* Email provider on, sign-in by code: the same code length and expiry as
  the old project. Email templates: the same text.
* SMTP Settings: custom SMTP on, `smtp.resend.com`, port 465, user `resend`,
  the Resend API key as password, sender `Kettle <hello@send.heykettle.com>`,
  60s minimum interval (`docs/auth-smtp-plan.md`). Rate Limits: the raised
  email limit from the old project (234).
* Data API: exposed schemas the same as the old project.
* **Do not sign in to the new project yet** (see above).

### The window (30 minutes; PM announces it)

Pings that land between W2 and W5 go to the old project and are not copied.
That loss is accepted (§2.3).

**W2. Dump (founder).**

```bash
cd ~/kettle-cutover
pg_dump "$OLD_DB" --data-only --no-owner --no-privileges \
  --table='public.*' --table=auth.users --table=auth.identities \
  --file=kettle-data.sql
```

One warning is expected, circular foreign keys on `journal_entries`; W3
handles it. Generated columns, such as `auth.identities.email`, are left out
by `pg_dump` and recomputed on load. Nothing else from `auth` (sessions,
refresh tokens) is copied, so everyone signs in again.

**W3. Restore.**

```bash
psql "$NEW_DB" -v ON_ERROR_STOP=1 --single-transaction \
  -c 'set session_replication_role = replica' -f kettle-data.sql
```

It runs as one transaction: an error leaves the new project as empty as
before, so fix and rerun. `replica` skips foreign-key checks and triggers
during the load, which is the line Supabase's own migration guide uses.
Nothing is re-checked afterwards, which is why W4 exists.

**W4. Counts and sequences, old against new. It must print nothing.**

```bash
cat > counts.sql <<'EOF'
select 'table', format('%I.%I', schemaname, relname), n from (
  select schemaname, relname, (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I.%I', schemaname, relname), false, true, '')))[1]::text::int as n
  from pg_stat_user_tables where schemaname = 'public' or (schemaname = 'auth' and relname in ('users', 'identities'))) t order by 2;
select 'seq', format('%I.%I', schemaname, sequencename), coalesce(last_value, 0) from pg_sequences where schemaname = 'public' order by 2;
EOF
psql "$OLD_DB" -At -F ' | ' -f counts.sql > counts-old.txt
psql "$NEW_DB" -At -F ' | ' -f counts.sql > counts-new.txt
diff counts-old.txt counts-new.txt
```

A ping landing on the old project after W2 shows here as `pings` one higher
on the old side. That is the accepted loss, not a fault.

**W5. kettle-api secrets: one command, one restart.**

> **As run 2026-10-18 (369):** `fly secrets import` read the two pasted lines
> as one and the API crash-looped. Use `fly secrets set` with each value as
> its own single-quoted argument instead; one command, one restart.

```bash
fly secrets import -a kettle-api
```

Paste these two lines, then press Ctrl-D:

```
DATABASE_URL=<new project's pooler string, the same pooler mode and port as the current secret>
SUPABASE_JWKS_URL=https://<new-ref>.supabase.co/auth/v1/.well-known/jwks.json
```

Then `curl -s https://api.heykettle.com/healthz` answers.

**W6. kettle-app rebuild.** In `webapp/fly.toml` `[build.args]`, set
`VITE_SUPABASE_URL = "https://<new-ref>.supabase.co"` and
`VITE_SUPABASE_PUBLISHABLE_KEY = "<new sb_publishable_…>"`. Both are public
by design, so commit them: `365: kettle-app talks to the us-east-1
project`. Push, then:

```bash
cd "$REPO/webapp" && npm run ci && fly deploy
```

**W7. Regions: kettle-api first, then kettle-app.**

```bash
fly machines list -a kettle-api                        # note the sin machine id
fly machine clone <sin-id> --region iad -a kettle-api
fly machines list -a kettle-api                        # wait: iad started, checks passing
fly machine stop <sin-id> -a kettle-api
fly machine destroy <sin-id> -a kettle-api
fly machines list -a kettle-api                        # iad only
```

Then the same for kettle-app, once per `sin` machine it lists. kettle-app
stops itself when idle, so its `iad` clone may show `stopped`; that is normal,
and it starts on the first request. Clone carries the machine's image and
config. Secrets are per app, so the clone has W5's values.

### Verify (founder and PM)

1. `curl -s https://api.heykettle.com/healthz` and
   `curl -s https://kettle-api.fly.dev/healthz` both answer;
   `curl -sI https://api.heykettle.com/healthz | grep -i fly-request-id`
   ends in `-iad`.
2. Sign in at `app.heykettle.com`. The code arrives from
   `hello@send.heykettle.com`, which proves SMTP; the family's Today
   renders, which proves the data and RLS.
3. A Rehearsal parent's ping lands:
   `psql "$NEW_DB" -Atc "select max(ts_utc) from pings"` shows this minute.
4. The Claude connector answers `today` without re-authorising.
5. The weekly site email still schedules.
6. `fly machines list` for kettle-api and kettle-app shows `iad` only.

**Rollback**, until the old project is paused: `fly secrets import` the two
old values and revert W6's commit and deploy. Anything written to the new
project since W5 stays there, and its loss is accepted.

### After

1. `rm -rf ~/kettle-cutover` once Verify passes. The dump holds personal
   data, and the old project is the backup.
2. Pause the old project now, so nothing can write to it unnoticed. Delete
   it after 14 days (§2.10).
3. Rewrite the baton's hosting paragraph, update the infra facts, and send
   the Meta form saying United States only (365).
4. **Retire kettle-pilot** (367 point 3, ruled 2026-10-18). The July pilot
   app is idle (no recent logs; its shortcuts were deleted in September) and
   its YC-evidence role is over. Copy the database off, then destroy the app,
   which removes its machine and the `kettle_data` volume:

   ```bash
   mkdir -p ~/kettle-pilot-copy
   fly ssh sftp get /data/pilot.db ~/kettle-pilot-copy/pilot.db -a kettle-pilot
   ls -l ~/kettle-pilot-copy/pilot.db     # non-zero size
   fly apps destroy kettle-pilot
   fly apps list                          # no kettle-pilot
   ```

   The copy holds the founder's own parents' pilot pings (who, signal, time)
   and stays on the founder's Mac, outside the repo. The root `fly.toml` and
   `app/` stay in the repo as history; nothing deploys them.
