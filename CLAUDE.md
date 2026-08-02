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
  number is 88.** Ambiguity goes there rather than into a guess. Rulings that
  graduate to standing rules get made structural — stated where the rule lives
  and enforced by a test, not just recorded (see items 35, 39, 48, 51).

### State of the build (2026-08-02)

Specs 001–006 are built: the pilot backend (`app/`, frozen since 002), the
multi-tenant product backend (`product/`, migrations through **0009**), the
digest engine, ladder v1, the child PWA (`webapp/`) with its warmth pass and the
tripwire health detail view, the shortcut forge, and the landing page
(`site/`). **Three** suites now — `pytest`, `webapp && npm run ci`, and
`site && npm run ci` — all green on `main`.

006 added the first top-level directory since `webapp/` and the first table with
no family attached. `site/` reuses the webapp's toolchain with two extra CI
checks: a foreign-origin scan of `dist/` (law #4 made mechanical — a font CDN
would disclose every visitor's interest in elder monitoring before they had
decided to trust anything) and a prerender check (the page is rendered to HTML
at build time so it reads with JavaScript off, and a prerender step that stops
running looks fine to everyone whose browser runs scripts). `docs/design-language.md`
is the law of that surface; spec 006 §2 locked its values, and they live in
`site/src/tokens.css` alone.

005e's format debt is paid by field test (2026-08-02): a forge-generated,
signed shortcut **imported on a real iPhone with one tap — no Settings toggle,
no "Allow Untrusted Shortcuts" prompt**. QUESTIONS 70 is closed (005b's wizard
needs no "turn this on first" step) and 69 is downgraded to optional — the
`--inspect` diff against a hand-built export would still sharpen `validate()`'s
key-set contract but blocks nothing. One small fix owed from the same session:
**item 77, forge.py must lazy-import psycopg** so `--device-token` mode runs
dependency-free on a bare Mac — **done**, and it needed more than a lazy import
(QUESTIONS 78): the token path also queried for the parent's name and signal
list, so there is now an explicit offline mode, `--device-token TOKEN --name`.

005d's rulings (QUESTIONS 58–64, 2026-08-01): 58 and 61–64 approved, **59
deferred** — learned cadences wait for the threshold-analysis spec, fixed
windows stand — and **60 changed**: a signal never heard from reads `Not set up
yet`, neutral and outside the repair-nudge trigger, because absence of *ever*
means not-yet-configured rather than broken.

A founder-led UI polish round followed on-device (QUESTIONS 65–68, no spec): tap
affordance on the parent cards, `Back to today` as a control, taller tripwire
rows, and `never` deleted from the recency vocabulary. **The parent detail page
is the parent's future home — day-detail and per-parent digest views are
expected to live there**, which is why the affordance mattered enough to fix
before the next spec.

**Amendment A** (founder site review, 2026-08-02) is built: marketing copy is
universal English — no romanized kinship terms, no culture-coded vocabulary —
and the page shows both parents (hero plural, sample digest names Dad, scenarios
still follow one). `CULTURE_CODED` in `site/src/tests/copyLaw.test.tsx` is the
first ban here scanned against *unmasked* text, so it cannot be allowlisted past;
notes are QUESTIONS 84–87.

006's own notes are QUESTIONS 78–83. Two are worth a reader's time before
touching `site/`: **80**, where §3.2 and AC5 disagree about whether the
notification breaks panel structure (read as "the `off` panel must not be
escalated", tested that way, and **ruled that way** — AC5 amended to match,
nothing owed); and **82**, where a source-text scan of Tailwind classes was
found to miss any class built from a template literal — the motion guard now
walks the rendered DOM, and *any* future source-text class scan in this repo
should be assumed blind until proved otherwise.

**No unbuilt spec is in `specs/`** — 005b (onboarding wizard, family codes,
billing, TestFlight) is what the roadmap points at next; the tripwire view's
repair nudge hands off to its guided repair, and 005e's generation half is
already the piece 005b's macOS CI signer would reuse. The PM has not written
that spec yet.

Production (`kettle-prod`) is at migration 0008 and **0009 is owed** — the
waitlist table, which the landing page needs before it can collect anything. The
founder applies migrations and runs deploys, so a spec being "done" here means
green locally and pushed, never shipped; 006 additionally needs DNS and a static
host pointed at `site/dist/` (`site/README.md` has the three steps).
