# Baton — state of the build

What a fresh session cannot reconstruct from the repo: what is live, what is owed and
by whom, what is deliberate and must not be "fixed", and which traps are specific to
this build. Everything else is written where it applies — product law in the root
`CLAUDE.md`, per-surface norms in each tree's `CLAUDE.md`, the reasoning for every
decision in `specs/DECISIONS.md`.

**Keep this current, and organise it by state, not by session.** It was rewritten on
2026-08-21 because seven passes of "the X pass is in (previous session)" had accreted
into 300 lines — and one of them still described six commissioned *photographs* and a
hero diptych that DECISIONS 136 had replaced with illustrations wholesale. A baton
that narrates history goes stale silently; one that states current facts fails loudly.
**The narrative of how we got here belongs in DECISIONS. This file is the present
tense.**

---

## 1. Read these first

| When | Read |
|---|---|
| Always, before believing a green run | `docs/failure-families.md` — six ways work has actually gone wrong here |
| Before any product-suite claim | `product/CLAUDE.md` → Running anything (`KETTLE_REQUIRE_POSTGRES=1` is not optional) |
| Before touching onboarding / setup | `docs/setup-delivery-brief.md`, then `docs/onboarding-runbook.md`, then DECISIONS 92–127 |
| To know if a spec still describes the product | `specs/README.md` |

The next DECISIONS number is the line at the top of `specs/DECISIONS.md` and **nowhere
else**. Items 1–120 are in `DECISIONS-archive.md`; load it only for a number in range.

## 2. Running the suites

```bash
service postgresql start                       # not running on a fresh container
KETTLE_REQUIRE_POSTGRES=1 .venv/bin/python -m pytest product -q
.venv/bin/ruff check .
cd webapp && npm run ci
cd site   && npm run ci
```

Current green: **`pytest` 346, zero xfails**, **`webapp` 115**, **`site` 174**.

* The 145 xfail is **gone the right way**: the midnight-reply defect was fixed as
  ruled (DECISIONS 153) and the marker became a plain assertion in the same commit.
* The webapp count moved 117 → 110 with the Digests screen's retirement (156), then
  to 115 with the 1000-row-cliff regression suite (160); the product count grew to
  346 through the outbound passes (152/153/154/159).
* Postgres has died mid-session in this container. `KETTLE_REQUIRE_POSTGRES=1` turns
  that into 169 loud errors instead of a silent skip. Restart and re-run.
* **Verify front-end changes on more than one Node.** The container has 22.22.2, the
  founder runs 24.18.1, and a suite that disagreed between them is what DECISIONS 146
  was about.

## 3. Live state — do not break

* **Both parents are live in production.** Amma on the old per-app keys (never rebuilt
  remotely for elegance, DECISIONS 107); Appa on merged routine+charger (126).
* **Amma is physically in Texas while provisioned `Asia/Kolkata`** (108, backlog). A
  shifted-looking routine there is geography, not a bug.
* **Onboarding-surface investment is founder-PAUSED** (126). Beta families get
  handholding; page improvements queue behind real beta evidence. Do not build
  onboarding polish unprompted.
* **`digest_sends` stays in the schema for now, and nothing reads OR writes it.**
  DECISIONS 156 retired the Digests screen and took the table out of the app's
  `READ_SURFACE` (built, DECISIONS 159); a later 0013-style migration retires the
  table itself — that migration is now unblocked but not yet written. `sent_messages`
  stays RLS deny-all; no client ever reads it.
* **The waitlist form is CORS-dead** until `WAITLIST_ORIGINS` on kettle-api includes the
  serving origin. Unconfirmed whether it was ever set. See §4.
* **kettle-site is serving a redirect loop in production right now.** The domain
  cascade shipped a config in which `heykettle.com` matched no `server_name`, fell
  into the fly.dev redirect block and 301'd to itself (DECISIONS 148 — my bug;
  `server_name _` is not a default server). **The fix is committed and NOT deployed.**
  Until `fly deploy` runs, the site is unreachable.

**Deployed as of 2026-08-18 (founder-reported):** migration 0011 applied and verified in
the live database; kettle-api healthy (`/healthz` → `{"db":true}`); kettle-site at
`2f1f2f5`. **Migrations 0012 and 0013 are written but NOT applied — confirm them before
the next kettle-api deploy, which starts the dark loop (§4 item 4).** Migration
**0014 IS applied** and both live parents' relationship labels are set (Mom / Dad) —
done 2026-08-23 by the PM via SQL. The site runs a build that predates six unshipped
passes (§4).

**Wave A has NOT started.** The running kettle-api build has no outbound loop — the
old lifespan declined to start one — so nothing has ever written `sent_messages`, and
the §6.3 48-hour review clock has never started (DECISIONS 155 corrects the record).
The loop is wired as of this pass and starts, dark, with the next kettle-api deploy.

## 4. Owed — by the founder

1. **One command, blocks the waitlist form.** Setting `WAITLIST_ORIGINS` *replaces* the
   default rather than adding to it, so the whole list must be named:
   ```bash
   fly secrets set -a kettle-api \
     WAITLIST_ORIGINS="https://heykettle.com,https://www.heykettle.com,https://kettle-site.fly.dev"
   ```
   Drop the fly.dev entry when the old host stops being used.
2. **`fly deploy` kettle-site — URGENT, the site is down.** It is serving a redirect
   loop; DECISIONS 148's one-word fix is committed and unshipped. Six passes ride
   along: 134 (presence), 135 (one-voice typography, field band, stir), 136
   (illustrations, mobile tab row), 137 (floating CTA), 142 (domain cascade), 148.
   **After deploying, curl the canonical host** — nothing in the suite reaches a
   running server, which is how the loop got out (see §7).
3. **`fly deploy` kettle-app.** Carries the 112 cache headers — until then deploys
   white-screen returning browsers — plus the login words, the Setup card, and now the
   session-restore fix (144).
4. **Apply migrations 0012, 0013 and 0015, then `fly deploy` kettle-api — this
   deploy starts Wave A, dark** (DECISIONS 154/155/159). 0013 decides per-table at
   apply time and prints notices saying what it did; read them. 0012 creates
   `sent_messages`, which the loop writes — deploying before applying it means a
   loop that fails every pass — and 0015 adds the status column the engine now
   writes. (0014 and the relationship labels are already done — PM, 2026-08-23.)
   After deploying, check the logs for `outbound (dark):` lines at the expected
   local times, and expect founder ntfy alerts for anything skipped or failed.
5. **Run Wave A dark for 48 hours** and review the ledger against what actually
   happened (spec 007 §6.3) — statuses included: skipped and failed rows say why a
   slot is empty. That review is the gate to Wave B. The clock starts at the deploy
   in item 4, not at any earlier date (155).
6. **The Wave B flip, AFTER the review — two secrets, no deploy, no code change:**
   ```bash
   fly secrets set -a kettle-api RESEND_API_KEY=re_... OUTBOUND_TRANSPORT=resend
   ```
   (Fly secrets override `[env]`, so fly.toml keeps `console` as the written
   default; `fly secrets unset -a kettle-api OUTBOUND_TRANSPORT` is the rollback.)
   Before flipping: Resend DNS verified on `send.heykettle.com` and open/click
   tracking OFF in the Resend dashboard (docs/auth-smtp-plan.md). After flipping:
   digests go to the child's account email; asks and follow-ons record as skipped
   with an ntfy alert each morning that is quiet — that is Wave C's gap, expected
   and visible, not a bug.
7. **The Resend DNS records** on `send.heykettle.com` before any non-founder family
   (`docs/auth-smtp-plan.md`).
8. **Confirm Appa's charger automation has both edges ticked** (126).

## 5. Owed — rulings from the PM

Nothing is currently owed. The four standing questions all closed on 2026-08-23:
**156** retired the Digests screen (built, 159), **157** ranked the sixteen missing
capabilities into waves (the Wave B tier is built, 159; the Wave C tier — ask_skipped
escalation, the all-clear, mechanism_ok — is the next ruling-backed build), **158**
confirmed the 142 calls and closed 152's open question (the child-facing label picker
joins the setup page when the onboarding pause lifts, not before), **153** fixed the
145 midnight-reply bug (zero xfails since).

## 6. The Wave B pass (157 hardening + Resend transport + 156 retirement) — built

Landed 2026-08-23 (DECISIONS 159). The ledger records sent/failed/skipped per row
(migration 0015; 'sent' final, the rest retryable); every non-sent outcome ops-alerts
the founder once per transition (ntfy + `ops_alerts`, `outbound_*` kinds); a morning
digest is never sent more than two hours late; the evening-normal body never renders
from a zero-signal day; the `resend` transport carries digests to the child's email
behind the same seam, fail-closed without its key; asks and follow-ons record as
skipped until Wave C. **Deployed config stays console — the only thing between the
ledger review and real digests is the two-secret flip in §4.** Webapp: Digests screen
retired (156), suite now 110.

## 7. Deliberate, and easy to "fix" by mistake

* **The webapp's pings read is per-parent, windowed, ordered and limited on
  purpose** (`webapp/src/lib/data.ts`, DECISIONS 160). "Simplifying" it back to a
  plain select re-opens the 1000-row cliff: PostgREST silently caps unbounded
  responses, and prod crossed the cap and showed a stale Today card. A test pins
  the order, the limit, the window and the audit of every other table.
* **privacy.html has no `<link rel="canonical">`.** It is held to a stricter law —
  stands alone, no `<link>`, no absolute URL — so a reader can verify it fetches
  nothing. The 301 already prevents the duplication a canonical would address (142).
* **The webapp test suite installs its own `localStorage`** (`webapp/src/tests/setup.ts`).
  Items are **enumerable own properties** because `clearStoredSession` walks
  `Object.keys`; a Map-backed fake passes its own tests and breaks its only caller. The
  non-enumerable marker is what lets the guardrail prove the *stub* won rather than that
  "storage works". The per-file `@vitest-environment jsdom` pin does **not** replace the
  stub — the shadowing happens inside jsdom setup (146).
* **`isAuthFailure` is narrow on purpose** (`webapp/src/lib/session.ts`). A 500, a 429 or
  a dropped connection must not end a working session; a test holds that line from the
  other side (144).
* **`families.ladder_mode` and 0007's per-parent threshold columns survive** the
  retirement. The ruling named tables, a column drop is not reversible, and
  `phone_e164` holds a real number the founder entered (141).
* **`/outbound/reply` 404s until `OUTBOUND_REPLY_TOKEN` is set.** Cancelling a follow-on
  is safety-relevant; an unauthenticated endpoint would let anyone who knows a number
  suppress an escalation (140).
* **`site/nginx.conf`'s redirect is a named `server` block, not an `if`.** nginx resolves
  an exact `server_name` before `_`, so requests on the real domain never enter it and
  the caching contract is structurally unaffected. A test asserts there is no `if (` in
  the config (142).
* **`site/nginx.conf`'s serving block carries `listen 8080 default_server`.** Not
  cosmetic: `server_name _` is *not* a default, and without the flag nginx routes every
  unmatched Host to the first block — the redirect — which took the site down (148). A
  test now fails by name if it is removed.
* **`docs/failure-families.md` sections are appended, never renumbered** — DECISIONS 145
  cites "family 5" by number.

## 8. Where things stand, by surface

**`product/`** — FastAPI + Postgres. Specs 001, 001a, 002, 005b, 005e built. Specs 003
and 004 **retired**: engines, copy, CLI and `/twilio/inbound` deleted; migration 0013
retires their tables, dropping the empty and archiving the non-empty. Spec **007 Wave A
is built and wired to run dark** — evaluator, scheduler loop in the lifespan (154),
sent-once ledger (0012 `sent_messages`), template registry (the DECISIONS 151 bodies,
rendered by relationship label), console transport behind a closed registry that fails
unknown names — and missing credentials — at boot, and a reply endpoint nothing
calls. fly.toml carries `OUTBOUND_LOOP = "1"` and `OUTBOUND_ENABLED = "1"`; the dark
run itself starts with the next kettle-api deploy, not before (155 — the running
build predates the loop). **Wave B is code-complete** (159): ledger statuses, founder
ops alerts, staleness cutoff, evidence gate, and the `resend` transport, behind the
console default until the founder flips it (§4 item 6). Waves C–D are each gated on a
founder errand. Migrations through **0015**.

**`site/`** — heykettle.com, live on Cloudflare DNS, hosted on Fly. One illustration set
(six webps at unhashed stable names the cache contract depends on — there are no
photographs in the tree). One typeface, five type roles, three weights. Rhythm Field
built and tuned. Floating CTA. Domain cascade done. Everything since DECISIONS 134 is
unshipped.

**`webapp/`** — the family app. 005a/005c/005d built. Session restore hardened (144):
a stored session the server rejects signs out, clears storage and lands on login;
`restoring` is a named state; "Loading…" is bounded at 15s.

## 9. Working norms worth repeating

* **Commit WIP before destructive experiments.** `git checkout <file>` during a
  plant-and-revert has cost uncommitted work here **twice**, most recently in this
  session. Copy the file aside instead.
* **`git rm` + a bare `git commit` sweeps unrelated deletions into your commit.** Also
  twice.
* **Verify a guardrail by planting the regression it exists to catch.** In the last two
  sessions this moved the code three times — a guardrail that failed via a fixture
  instead of its own assertion, a claim-path guard nothing isolated, and a storage test
  that would have passed against the object that caused the bug.
* **Commits are the PM's review surface.** Split by concern; explain *why*.
