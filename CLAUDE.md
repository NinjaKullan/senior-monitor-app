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

- **Postgres stops between sessions — and can die mid-session too.**
  `service postgresql start`, then `pg_isready`. Without it the product suite
  *skips* rather than fails, and the run reports "N passed" while proving
  nothing. The skip banner says so explicitly ("this is NOT a green run of
  spec 002") — believe it. This has bitten five times now, twice in the middle
  of a session (2026-08-17: a background re-run reported "133 passed, 203
  errors" while the pipeline exit code stayed 0 — `pytest | tail` returns
  tail's status, so read the summary counts, never the chain's exit;
  2026-08-19: "139 passed, 208 errors" ten minutes after a clean 347). It is
  the single most likely way to report a false green. Re-run `pg_isready`
  immediately before believing any product-suite result, and redirect the run
  to a file rather than piping it.
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
- **Check the site on a phone before the founder does.** Any pass that touches
  layout or adds a component checks the affected sections at **360, 390 and
  768** and treats a wrap, overlap or horizontal overflow there as a blocking
  finding. jsdom lays nothing out, so the suite is structurally blind to this:
  twice the founder has found on a real handset what the whole suite called
  green (the field's orbits on the section's words; the scenario tabs folding
  into two ragged lines). `site/scripts/probe-responsive.mjs` and
  `probe-field.mjs` measure it in a real browser — neither is in `npm run ci`,
  because Playwright is not a dependency; run them against a preview server.
  What they cannot reach, pin as classes **with the arithmetic beside them**.
- **Verify a guardrail test by planting the regression it exists to catch**,
  then reverting. Several tests in this repo passed for the wrong reason until
  this was done (fabricated future timestamps, substring matches, a count hidden
  in a DOM attribute that text scanning walked straight past). A green assertion
  is not evidence it is load-bearing.
- **Commit WIP before destructive experiments.** `git checkout <file>` during a
  plant-and-revert cost an entire uncommitted rewrite here.
- **`specs/QUESTIONS.md` is the PM channel.** Number every question or judgement
  call; the PM appends a rulings section referencing those numbers. **Next item
  number is 136.** Ambiguity goes there rather than into a guess. Rulings that
  graduate to standing rules get made structural — stated where the rule lives
  and enforced by a test, not just recorded (see items 35, 39, 48, 51).

### Start here after a session break

**`docs/setup-delivery-brief.md` (2026-08-13).** State of the world, the setup/delivery problem
stated properly — a parent faces ~78 interactions today and delivery is only ~15% of them — the two
cheap experiments that decide spec 005b's shape, and what is owed by whom. Read it before
`docs/onboarding-runbook.md` and QUESTIONS 92–102.

### State of the build (baton, 2026-08-18 — session handoff)

**All three suites green** (`pytest` 347 with Postgres up, `webapp` 100,
`site` 140 — always confirm the product suite with `KETTLE_REQUIRE_POSTGRES=1`,
never trust a skip). Specs 001–006 plus amendments A/B built and reviewed;
**spec 005b built and PM-approved** (rulings follow item 123: 118 upheld —
provisioning stays terminal until the signing runner; 121 amended in the spec
— honest enumeration ≤ 40, the automation builder is the named reduction
target; 122 exemption granted — the share CTA may say "Send on WhatsApp",
**implementation queued**: a channel-name exemption pinned to that one copy
key, sms-pinning style). Migrations through **0011** (0011: waitlist help_with). The working branch
`claude/family-onboarding-setup-005b-vkqoef` merges to main per the norm
above.

**The site image + copy pass is built (this session, item 127):** the six
commissioned webp photographs are wired — hero diptych (parent's morning left,
child's evening right, profiles inward per the photos' actual facing; pinned
by test), four section stills with rewritten honest alt text — and every em
dash in customer-facing site copy is rewritten with periods/commas, including
the founder's two hero lines ("ordinary routine", "No new devices. Only the
phone they already have."). The copy-law scan grew an `img[alt]` walk; all
seven planted regressions fail by name. The fix pass (item 128) made the
scenario tabs actually toggle (`[hidden]` now beats the display utility,
pinned twice) and moved the site off gostatic onto nginx with the Q112
caching contract (`test_site_caching.py`). **Founder deploys kettle-site
after review.**

**Both parents are live in production** (Q126: Appa on merged
routine+charger, first field run of the setup page) and the founder has
**PAUSED onboarding-surface investment** — beta families get handholding; page
improvements queue behind real beta evidence. Do not build onboarding polish
unprompted. Q125 killed the consent *ceremony* (one-pagers deleted; consent
lives in the product) and ruled surfaces English-only; the runbook §7 rewrite
("open the setup link together") is still owed.

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

**Queued for Claude Code (build only when asked — onboarding polish is
founder-PAUSED per Q126):** the item-122 channel-name exemption ("Send on
WhatsApp" on the setup card's share CTA, pinned to that single copy key); the
runbook §7 consent-step rewrite (Q125a); 93 (forge derives out path from
token), 95 (`--add-device` / `--rotate`), 100 (platform-aware standard set),
101 (person prefix on disk filenames); 124 (family-context header on Today +
the duplicated Family-circle row); reconciling the built setup page's
`kettle/setup_copy.py` against the PM's keyed deck `specs/005b-copy.md`
(landed with item 132, written 2026-08-16 — the page was built from the mock
before the deck was in the repo; queues behind the same pause).
**Next QUESTIONS number: 136.**

**The Rhythm Field is BUILT (Q131 — the mock landed mid-pass and resolved
Q130): Canvas 2D port of the approved mock, both placements, hard
requirements pinned as tests (reduced-motion still, inert without context,
off-screen park, half density on phones, dynamic-import-only, zero
fillText in the hero). The canvas ban and colour law were amended in the
open, scoped tight. The beta conversion, mobile hero and inference ban are
built (Q129). **The finishing pass is in (Q132 rulings, Q133 notes): the
founder note and privacy policy are live text, verbatim; the what-never-how
ruling is a MECHANISM ban across site copy and the privacy page; the
motion-law prose sits in design-language §6. PM review of e815276: approved,
no overrules.**

**The one-voice pass is in (Q135, this session).** The site speaks in one
typeface: the serif emphasis role is retired (Fraunces out of the bundle,
`font-serif` out of the Tailwind theme, the five fragments merged back into
their sentences), the scale is five roles with one job each — display 48 for
the single `h1`, heading 32 for every `h2`, lead 20, body 16, eyebrow 13 — and
the weights are three that exist as files (400/500/600). `font-light` was
written on every heading while Instrument Sans has no 300 file, so it never
rendered; it is gone. The three-fields canvas has a **reserved band** below the
words (`Section`'s backdrop slot is deleted, not merely unused) with ring size
derived from the band, and its dust can be **stirred by a desktop pointer** —
passive listener, nothing on touch, still still under reduced motion, rings and
labels never displaced. `site/scripts/probe-field.mjs` is committed: it reads
canvas pixels against laid-out text boxes at 360/390/768/1440 and currently
reports zero overlap; planting the old backdrop reproduces the reviewers'
report at every width. Eleven plants, one of which passed for the wrong reason
until it was re-aimed (see Q135).

**The presence pass is in (Q134, previous session).** The founder's note now reads
"twenty-five years ago" (spelled out — AC4's digit scan walks the letter), and
the Rhythm Field was ruled UP: on the live cream ground it painted 0.14% of the
hero's pixels and read as static specks. Every presence number now lives in one
`PRESENCE` block in `site/src/lib/rhythmField.ts` — bigger, brighter motes, amber
taking its share from graphite, a floor under the drift magnitude (the mock's
symmetric spread left half the motes frozen, which doubling alone would not have
fixed), and rings that arrive sooner and fade slowly enough to be caught
mid-breath. Density was deliberately NOT raised. The numbers are ported back into
`docs/mockups/rhythm-field-mock.html` and a parity test now reads each one out of
the mock and compares it to the shipped constant, both directions, five plants.
**Visibility itself is not testable here — the PM verifies it on the live site
after deploy, by ruling.** How the values were chosen: a throwaway Playwright
probe read the canvas' own pixels over the real ground (0.108% → 0.274% legible;
motion 0.23% → 0.56% of the frame per second).

**Owed by the founder, not by code:** review + `fly deploy` **kettle-site**
again — two passes are now unshipped (Q134's note correction and field
visibility, Q135's one-voice typography, the field band and the stir), and both
have acceptance tests that are the PM looking at the live site — the h2 size
drop and the 390px band fit especially; `fly deploy` of
kettle-app (Q112 cache headers — until then deploys white-screen returning
browsers — plus login words and the Setup card); the SMTP plan's DNS + dashboard
steps (`docs/auth-smtp-plan.md`) before any non-founder family; Q126's 48-hour
check that Appa's charger automation has both edges ticked.

**Deployed as of 2026-08-18 (founder-reported):** migration 0011 applied and the
`help_with` column verified in the live database; kettle-api out and healthy
(`/healthz` → `{"db":true}`); kettle-site shipped at 2f1f2f5 — founder note,
privacy policy and the Rhythm Field are live. The site therefore runs the
*pre-presence-pass* build until the next deploy.

**Live state to respect:** both parents are live — Amma on the old per-app
keys (never rebuilt remotely for elegance [107]), Appa on merged
routine+charger [126]. Onboarding-surface investment is founder-PAUSED [126].
The waitlist form is CORS-dead until `WAITLIST_ORIGINS` includes the serving
origin — kettle-api is deployed now, but whether that env var was set with it is
unconfirmed here, so check before believing the form works. Amma is
physically in Texas while provisioned `Asia/Kolkata` [108, backlog] — a
shifted-looking routine there is geography, not a bug.

**Read before touching 005b surfaces:** `docs/setup-delivery-brief.md`, then
`docs/onboarding-runbook.md`, then QUESTIONS 92–127 (the 2026-08-16 rulings
and the Appa field log especially). The runbook carries the item-107 field
gotchas (charger trigger defaults to Run After Confirmation and must be
flipped to Run Immediately; merged automation subtitles read "Kettle — Daily
routine" and that is correct, not mislabelled); the consent one-pager is gone
per Q125 — the setup page's first screen is the consent conversation now.
