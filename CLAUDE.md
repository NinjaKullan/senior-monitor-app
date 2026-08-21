# CLAUDE.md — Project Kettle (working name)

Passive peace-of-mind monitoring for adult children with aging parents far away. Core principle: **negative-space monitoring** — detect the absence of normal phone routine; never observe content. Currently: 30-day family pilot on the founder's parents' iPhones (Chennai) + YC Fall 2026 application.

## Roles & workflow

- **Hema** — founder, decisions, phone setup, YC app.
- **Fable 5 (Cowork session)** — PM/project manager: writes specs in `specs/`, reviews every build after Hema does `git pull`.
- **Claude Code (you)** — implementer. Build exactly what the active spec says. If a spec is ambiguous or seems wrong, stop and file it in `specs/DECISIONS.md` rather than guessing.

Build against the lowest-numbered spec in `specs/` that isn't marked done. Commit in coherent units with descriptive messages — commits are the review surface, and they are reviewed **from `main`**: merge the working branch and push there when a build is green.

## Hard constraints (product law — never violate, never "improve" around)

These bind every surface. Nothing below this section overrides them.

1. **No decline/dementia/diagnostic detection or claims.** Permanently ruled out by diligence (`docs/research-synthesis.md`). Do not add trend inference, anomaly ML, or health scoring.
2. **No keystroke logging, no message/call/browsing content, no audio, no location trails.** The only stored signal fields are `who`, `signal`, server timestamp. Drop anything else at the door.
3. **No family- or senior-facing alerts in pilot code.** All alerting goes to the founder only (ntfy). The escalation ladder is design, not implementation, until a spec says otherwise.
4. **No third-party analytics, tracking, or telemetry libraries.** Privacy engineering is a day-one requirement (FTC HBNR posture).
5. **Never scrape WhatsApp "last seen"** or any platform-ToS-violating signal.
6. **A household event must never be presented as evidence that a specific person is fine.** Household-grade signals (if ever built) corroborate; only person-attributed signals may anchor reassurance or alarm. (Adopted from the adversarial signal review, `docs/signal-expansion-ideas.md` §2.5.)

## The three surfaces

Each carries its own norms in its own `CLAUDE.md`, loaded when you work in that tree.
A session touching only one surface does not pay for the other two.

| Tree | What it is | Its rules |
|---|---|---|
| `product/` | FastAPI + Postgres backend, the ladder, the digests, the forge | `product/CLAUDE.md`, `product/README.md` |
| `site/` | The marketing page (heykettle.com) | `site/CLAUDE.md`, `site/README.md`, `docs/design-language.md` |
| `webapp/` | The family app (kettle-app) | `webapp/CLAUDE.md`, `webapp/README.md` |

## Stack conventions

- Python 3.12, FastAPI, SQLite, pytest, ruff. Type hints on public functions. Pin dependencies.
- Store UTC, display IST (`Asia/Kolkata`, stdlib `zoneinfo`).
- Minimal dependencies — justify any new dep in the commit message.
- Secrets only via env vars; `.env.example` documents them; never commit real values.

## Definition of done

Tests pass (`pytest`), `ruff check` clean, acceptance criteria in the spec each verifiably met, README updated if setup changed, no secrets in the diff.

## Working norms that bind every surface

- **Commits are the PM's review surface.** Split by concern — logic, rendering, tests,
  docs — and write the message to explain *why*, not what the diff shows. A
  `git add -A` sweep that buries four concerns in one commit has to be undone.
- **Verify a guardrail test by planting the regression it exists to catch**, then
  reverting. A green assertion is not evidence it is load-bearing.
- **Commit WIP before destructive experiments.** `git checkout <file>` during a
  plant-and-revert has cost an entire uncommitted rewrite here.
- **Rulings that graduate to standing rules get made structural** — stated where the
  rule lives and enforced by a test, not merely recorded.

## Where things are written down

- **`specs/DECISIONS.md`** — the PM channel and the decision log. Number every question
  or judgement call; the PM appends rulings referencing those numbers. **The next
  number is the line at the top of that file** — it is the single place it is recorded.
  Items 1 through 120 are in `specs/DECISIONS-archive.md`; load the archive only when a
  cited number falls in that range.
- **`docs/baton.md`** — state of the build: what is deployed, what is owed and by whom,
  and the live facts a session must not break. **Read this first after a break.**
- **`docs/failure-families.md`** — the ways work has actually gone wrong here, grouped
  by shape. Read it when a run looks green and you are about to say so.
- **`docs/setup-delivery-brief.md`** — the setup/delivery problem stated properly. Read
  it before `docs/onboarding-runbook.md` and DECISIONS 92–102.
- **`specs/`** for the specs, **`docs/design-language.md`** for the site's law,
  **`docs/PLAN.md`** for where the product is going.
