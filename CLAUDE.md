# CLAUDE.md — Project Kettle (working name)

Passive peace-of-mind monitoring for adult children with aging parents far away. Core principle: **negative-space monitoring** — detect the absence of normal phone routine; never observe content. Currently: 30-day family pilot on the founder's parents' iPhones (Chennai) + YC Fall 2026 application.

## Roles & workflow

- **Hema** — founder, decisions, phone setup, YC app.
- **Fable 5 (Cowork session)** — PM/project manager: writes specs in `specs/`, reviews every build after Hema does `git pull`.
- **Claude Code (you)** — implementer. Build exactly what the active spec says. If a spec is ambiguous or seems wrong, stop and leave a question in `specs/QUESTIONS.md` rather than guessing.

Build against the lowest-numbered spec in `specs/` that isn't marked done. Commit in coherent units with descriptive messages — commits are the review surface, and they are reviewed **from `main`**: merge the working branch and push there when a build is green.

## Hard constraints (product law — never violate, never "improve" around)

1. **No decline/dementia/diagnostic detection or claims.** Permanently ruled out by diligence (`docs/research-synthesis.md`). Do not add trend inference, anomaly ML, or health scoring.
2. **No keystroke logging, no message/call/browsing content, no audio, no location trails.** The only stored signal fields are `who`, `signal`, server timestamp. Drop anything else at the door.
3. **No family- or senior-facing alerts in pilot code.** All alerting goes to the founder only (ntfy). The escalation ladder is design, not implementation, until a spec says otherwise.
4. **No third-party analytics, tracking, or telemetry libraries.** Privacy engineering is a day-one requirement (FTC HBNR posture).
5. **Never scrape WhatsApp "last seen"** or any platform-ToS-violating signal.
6. **A household event must never be presented as evidence that a specific person is fine.** Household-grade signals (if ever built) corroborate; only person-attributed signals may anchor reassurance or alarm. (Adopted from the adversarial signal review, `docs/signal-expansion-ideas.md` §2.5.)

## Stack conventions

- Python 3.12, FastAPI, SQLite, pytest, ruff. Type hints on public functions. Pin dependencies.
- Store UTC, display IST (`Asia/Kolkata`, stdlib `zoneinfo`).
- Minimal dependencies — justify any new dep in the commit message.
- Secrets only via env vars; `.env.example` documents them; never commit real values.

## Definition of done

Tests pass (`pytest`), `ruff check` clean, acceptance criteria in the spec each verifiably met, README updated if setup changed, no secrets in the diff.

## Implementer notes (session handoff — keep current)

Things a fresh implementer cannot reconstruct from the repo. Everything else —
specs, product law, conventions — is written down already; read it there.

### Container quirks

- **Postgres stops between sessions.** `service postgresql start`, then
  `pg_isready`. Without it the product suite *skips* rather than fails, and the
  run reports "N passed" while proving nothing. The skip banner says so
  explicitly ("this is NOT a green run of spec 002") — believe it. This has bitten
  three times; it is the single most likely way to report a false green.
- **`KETTLE_REQUIRE_POSTGRES=1` turns that skip into a failure.** CI sets it
  (`.github/workflows/ci.yml`, with a Postgres service container). Set it locally
  when you want a missing database to be loud.
- **A fresh container has no `.venv` and no `node_modules`.** Rebuild with
  `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt -r
  product/requirements-dev.txt`, and `cd webapp && npm ci`.
- **`service postgresql start` is not enough on a fresh container** — the role
  and the database do not exist yet, so `pg_isready` says "accepting
  connections" while the suite skips anyway. The rest of the recipe is in
  `product/README.md`: `su postgres -c "psql -c \"alter user postgres with
  password 'postgres'\""` then `su postgres -c "createdb kettle_test"`.
- **Use `.venv/bin/python -m pytest` / `.venv/bin/ruff`** — system Python has
  neither installed.
- **Webapp:** `cd webapp && npm run ci` (lint → vitest → tsc+build → secret scan).
  `npx vitest run src/tests/<file>` for one file while iterating.
- **Docker is unavailable**; local Postgres plus `product/migrations/local/`'s
  Supabase shim is the substitute. Fly and Supabase deploys cannot run from here.

### Working norms settled in practice

- **Commits are the PM's review surface.** Split by concern — logic, rendering,
  tests, docs — and write the message to explain *why*, not what the diff shows.
  A `git add -A` sweep that buries four concerns in one commit has to be undone.
- **Verify a guardrail test by planting the regression it exists to catch**,
  then reverting. Several tests in this repo passed for the wrong reason until
  this was done (fabricated future timestamps, substring matches, a count hidden
  in a DOM attribute that text scanning walked straight past). A green assertion
  is not evidence it is load-bearing.
- **Commit WIP before destructive experiments.** `git checkout <file>` during a
  plant-and-revert cost an entire uncommitted rewrite here.
- **`specs/QUESTIONS.md` is the PM channel.** Number every question or judgement
  call; the PM appends a rulings section referencing those numbers. **Next item
  number is 124.** Ambiguity goes there rather than into a guess. Rulings that
  graduate to standing rules get made structural — stated where the rule lives
  and enforced by a test, not just recorded (see items 35, 39, 48, 51).

### Start here after a session break

**`docs/setup-delivery-brief.md` (2026-08-13).** State of the world, the setup/delivery problem
stated properly — a parent faces ~78 interactions today and delivery is only ~15% of them — the two
cheap experiments that decide spec 005b's shape, and what is owed by whom. Read it before
`docs/onboarding-runbook.md` and QUESTIONS 92–102.

### State of the build (baton, 2026-08-16 evening — session handoff)

**All three suites green** (`pytest` 336 with Postgres up, `webapp` 100,
`site` 90 — always confirm the product suite with `KETTLE_REQUIRE_POSTGRES=1`,
never trust a skip). Specs 001–006 plus amendments A/B built and reviewed;
**spec 005b is now built** (this session); migrations through **0010**. The
working branch `claude/family-onboarding-setup-005b-vkqoef` merges to main per
the norm above.

**005b as built** (details in QUESTIONS 118–123): migration 0010
`setup_links` — per-device slug (144-bit), 7-day expiry, issuance-as-rotation,
dies with the device token; RLS select-only for the family, `parent_id`
denormalised so the webapp never reads `devices` [123]. `provision` prints a
`setup page:` URL per parent; `--setup-link <device_token>` re-issues (the
Appa case). The parent page is served by **kettle-api** at `/s/<slug>` [119]:
consent (per-method honesty — merged says "never which app", per-app names the
app), step zero, add, pre-empted warning naming the real host, automations
with Run Immediately on every row, verify-by-prediction with a live green
check. The page never serves a file, never shows a token, and the slug is only
in the address bar; every `/s/*` response is no-store + noindex + no-referrer
+ CSP. The verify check greens **only on an alarm-grade ping strictly after
the screen opened** [120] — law #6 at the check; charger can never green it;
tested by plant. The webapp Family screen gained the Setup card [122]: per
parent, reporting / ready-to-send / needs-a-fresh-link, with a wa.me share
intent carrying the link (slug never printed as text — tested). The copy-law
scanner gained word boundaries at element seams — `textContent` glues
elements and a banned word flush at a seam escaped `\b` scanning until the
plant drill caught it [122]. Rehearsal script + honest tap enumeration:
`docs/005b-test-script.md`.

**Open for the PM in QUESTIONS:** 118 (scope reading: provisioning stays
terminal until the signing runner exists — wizard = forwarding + status;
overrulable), 121 (**acceptance 2's ≤ 12 taps fails an honest count: ~37**;
re-bound or scope it), 122 (want "WhatsApp" named on the share button? Needs a
scoped channel-name exemption in the copy law — PM call).

**Queued, unchanged:** 93 (forge derives out path from token), 95
(`--add-device` / `--rotate`), 100 (platform-aware standard set), 101 (person
prefix on disk filenames). **Next QUESTIONS number: 124.**

**Owed by the founder, not by code:** apply migration 0010 and `fly deploy`
**kettle-api** (the setup page and 0009+0010 ship together; until then every
printed setup URL 404s in production); `fly deploy` of kettle-app (Q112 cache
headers — until then deploys white-screen returning browsers — plus login
words and the Setup card); `--set-signals` for Appa, then forge/sign/deliver
his two merged files and `--setup-link` him a page; the SMTP plan's DNS +
dashboard steps (`docs/auth-smtp-plan.md`) before any non-founder family.

**Live state to respect:** Amma is live on the *old per-app* keys — her setup
is never rebuilt remotely for elegance [107]. Production is at migration 0008
with 0009 and 0010 owed, and the waitlist form is CORS-dead until
`WAITLIST_ORIGINS` includes the serving origin. The live site runs a
pre-Amendment-B build until redeployed. Amma is physically in Texas while
provisioned `Asia/Kolkata` [108, backlog] — a shifted-looking routine there is
geography, not a bug.

**Read before touching 005b surfaces:** `docs/setup-delivery-brief.md`, then
`docs/onboarding-runbook.md`, then QUESTIONS 92–123. The runbook and consent
one-pager carry the item-107 field gotchas (charger trigger defaults to Run
After Confirmation and must be flipped to Run Immediately; merged automation
subtitles read "Kettle — Daily routine" and that is correct, not mislabelled).
