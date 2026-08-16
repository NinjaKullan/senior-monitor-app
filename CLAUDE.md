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
  number is 118.** Ambiguity goes there rather than into a guess. Rulings that
  graduate to standing rules get made structural — stated where the rule lives
  and enforced by a test, not just recorded (see items 35, 39, 48, 51).

### Start here after a session break

**`docs/setup-delivery-brief.md` (2026-08-13).** State of the world, the setup/delivery problem
stated properly — a parent faces ~78 interactions today and delivery is only ~15% of them — the two
cheap experiments that decide spec 005b's shape, and what is owed by whom. Read it before
`docs/onboarding-runbook.md` and QUESTIONS 92–102.

### State of the build (baton, 2026-08-16 — session handoff)

**`main` is at `c63b3b3`; all three suites green** (`pytest` 305 with Postgres
up, `webapp` 93, `site` 90 — always confirm the product suite with
`KETTLE_REQUIRE_POSTGRES=1`, never trust a skip). Specs 001–006 plus amendments
A/B are built and reviewed; migrations through 0009. The working branch
`claude/tripwire-health-detail-view-6e1txw` tracks main exactly — develop there
or on main per the merge-to-main norm above.

**`specs/005b-family-onboarding.md` is written, its last fork is resolved, and
it is the next build target.** §5.1 CLOSED (item 117, five taps on the
founder's phone): iOS Safari will not hand an HTTPS-served `.shortcut` to the
Shortcuts app under any content type — every attempt was a download prompt. The
delivery ruling: **files travel by WhatsApp document attachment** (field-proven
on Amma's install); the hosted per-parent setup page stands for consent, steps,
the permission warning and verify-by-prediction, and never serves a
`.shortcut`; iCloud link generation stays off the table. The `/x/` nginx block
and `stage_shortcut.py` remain as a harness for future delivery experiments;
the staged slug is deleted.

**This session built** (details in QUESTIONS, numbers in brackets):
`Kettle — {Signal}` naming, no parent [96a]; measured `WFWorkflowIcon`
constants, item 69 closed [96b]; the merged end-state signal pair `routine` /
`charger` in both label maps with `ALARM_GRADE` as vocabulary [107];
`provision --signals` and `--set-signals <token>` (the Appa migration is a
printed command; old rows go inactive, not deleted) [94/107]; the §5.1 harness
[102]; nginx caching — shell `no-cache`, `/assets/` immutable, regex locations
banned by test, **and there is deliberately no service worker: HTTP caching is
the whole update story** [112]; staged files 0644 [113]; deploy docs — webapp
build args live in `fly.toml`, bare `fly deploy` is the command [114]; login
failures surface as words via `sendMagicLink` (supabase-js *returns* errors —
the try/catch that looks sufficient is unreachable without the re-throw) and
`docs/auth-smtp-plan.md` [115/116].

**Queued, unchanged:** 93 (forge derives its own out path from the token),
95 (`--add-device` / `--rotate`), 100 (platform-aware standard set; depends on
94, now landed), 101 (person prefix on *disk* filenames + never import into the
founder's own Shortcuts library). **Next QUESTIONS number: 118.**

**Owed by the founder, not by code:** `fly deploy` of kettle-app (picks up the
Q112 cache headers — until then every deploy still white-screens returning
browsers — plus the login words); `--set-signals` for Appa, then forge/sign/
deliver his two merged files; the SMTP plan's DNS + dashboard steps
(`docs/auth-smtp-plan.md`) before any non-founder family.

**Live state to respect:** Amma is live on the *old per-app* keys — her setup
is never rebuilt remotely for elegance [107]. Production is at migration 0008
with 0009 owed, and the waitlist form is CORS-dead until `WAITLIST_ORIGINS`
includes the serving origin. The live site runs a pre-Amendment-B build until
redeployed. Amma is physically in Texas while provisioned `Asia/Kolkata` [108,
backlog] — a shifted-looking routine there is geography, not a bug.

**Read before building 005b:** `docs/setup-delivery-brief.md`, then
`docs/onboarding-runbook.md`, then QUESTIONS 92–116. The runbook and consent
one-pager carry the item-107 field gotchas (charger trigger defaults to Run
After Confirmation and must be flipped to Run Immediately; merged automation
subtitles read "Kettle — Daily routine" and that is correct, not mislabelled).
