# CLAUDE.md — Project Kettle (working name)

Passive peace-of-mind monitoring for adult children with aging parents far away. Core principle: **negative-space monitoring** — detect the absence of normal phone routine; never observe content. Currently: 30-day family pilot on the founder's parents' iPhones (Chennai) + YC Fall 2026 application.

## Roles & workflow

- **Hema** — founder, decisions, phone setup, YC app.
- **Fable 5 (Cowork session)** — PM/project manager: writes specs in `specs/`, reviews every build after Hema does `git pull`.
- **Claude Code (you)** — implementer. Build exactly what the active spec says. If a spec is ambiguous or seems wrong, stop and leave a question in `specs/QUESTIONS.md` rather than guessing.

Build against the lowest-numbered spec in `specs/` that isn't marked done. Commit in coherent units with descriptive messages — commits are the review surface.

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
  number is 58.** Ambiguity goes there rather than into a guess. Rulings that
  graduate to standing rules get made structural — stated where the rule lives
  and enforced by a test, not just recorded (see items 35, 39, 48, 51).

### State of the build (2026-08-01)

Specs 001–005c are built and closed: the pilot backend (`app/`, frozen since 002),
the multi-tenant product backend (`product/`, migrations through 0008), the
digest engine, ladder v1, and the read-only child PWA (`webapp/`) with its warmth
pass. `main` is green on both suites. **`specs/005d-tripwire-health.md` is speced
and unbuilt — it is the next task.** Production (`kettle-prod`) is at migration
0008, advisor-clean; the founder applies migrations and runs deploys, so a spec
being "done" here means green locally and pushed, never shipped.
