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

## 5. The state with no exit — a failure that waits instead of failing

- **Stale credentials must degrade to re-authentication, never hang.** A stored
  session is a *claim* about being signed in, and only the server can settle it.
  Anything that says the claim is false — a 401, an expired JWT, a refresh that
  will not refresh — has to end at the screen a person can act on. The family
  app shipped for weeks with the opposite: a rejected token produced "Loading…"
  for as long as the tab stayed open, because `claimMembership()` rejected into
  a bare `.catch(() => undefined)`, `loadSnapshot()` rejected into nothing at
  all, and `!session` could not tell *restoring* from *signed out* (DECISIONS
  142). The founder found it on a real phone. The countermeasures generalise:

  * **Name the in-between state.** `restoring` has to be distinct from
    signed-out before anything can watch a clock over it. A state that is
    indistinguishable from a resting state is a state nobody bounds.
  * **Bound every wait, including the ones you think cannot happen.** The
    timeout must know nothing about *why* the wait stalled — the anticipated
    failures are already handled by name, so the bound exists precisely for the
    ones nobody anticipated, including a promise that simply never settles.
  * **Do not swallow a rejection to keep a chain running.** `.catch(() =>
    undefined)` on an optional step also discards the one error that means the
    session is over.
  * **Do not trust a cleanup call that talks to the thing that is refusing
    you.** `signOut()` calls the server; the server rejecting this token is the
    whole reason we are signing out. Clear the local copy by hand afterwards, or
    the next page load lands in the same hole.
  * **Keep the trigger narrow in the other direction too.** A 500, a 429 or a
    dropped connection is not a rejected credential, and ending a working
    session over a train tunnel is this bug's mirror image. Hold that line with
    a test written from the other side.

- **The test that is only green for part of the day.** `/outbound/reply` read
  wall time while its test wrote the ask on a fixed calendar day, so the suite
  passed every morning and failed every evening once IST rolled past midnight
  (DECISIONS 142). It was written, reviewed and reported green in a single
  afternoon, which is the entire window in which it worked. **A test that mixes
  a fake clock with a real one is a scheduled failure, not a flake** — and the
  fix is a seam, not a retry: every other decision in that spec takes `now` as
  an argument, and the one route that did not was the one that broke.
