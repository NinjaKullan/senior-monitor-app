# Failure families

Every one of these has actually happened here, more than once. They are grouped by
what goes wrong rather than by which suite it happens in, because the shape repeats
across surfaces and the countermeasure is the same each time.

Pointed at from `CLAUDE.md`; read it when a run looks green and you are about to say
so, or when a test you just wrote passed on the first try.

## 1. The false green — a run that proves nothing and says it passed

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

- **A failed build leaves the previous `dist/` in place.** A verification step that
  reads `dist/` then passes against the *last* successful build. This is why every
  site and webapp build now removes `dist/` before it starts: a build that dies has
  to leave nothing behind for a checker to be fooled by. Found by planting a
  regression that `check-prerender.mjs` cheerfully passed (DECISIONS 136).
- **`pytest | tail` returns tail's exit code, not pytest's.** Read the summary counts,
  and redirect long runs to a file rather than piping them.

## 2. The test that passes for the wrong reason

- **Verify a guardrail test by planting the regression it exists to catch**,
  then reverting. Several tests in this repo passed for the wrong reason until
  this was done (fabricated future timestamps, substring matches, a count hidden
  in a DOM attribute that text scanning walked straight past). A green assertion
  is not evidence it is load-bearing.

## 3. Layout blindness — jsdom lays nothing out

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

## 4. Work lost, or buried

- **Commit WIP before destructive experiments.** `git checkout <file>` during a
  plant-and-revert cost an entire uncommitted rewrite here.

- **Commits are the PM's review surface.** Split by concern — logic, rendering,
  tests, docs — and write the message to explain *why*, not what the diff shows.
  A `git add -A` sweep that buries four concerns in one commit has to be undone.
