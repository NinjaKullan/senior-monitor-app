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
