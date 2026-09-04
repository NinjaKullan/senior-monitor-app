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

Current green: **`pytest` 614 from the repo root** (567 product + 47 pilot —
the root run is what CI prints, DECISIONS 267), zero xfails, **`webapp` 202**,
**`site` 236**. `ruff check .` clean; `tools/printables/` is excluded by ruling
(266) pending its own lint-and-re-render pass.

* The 145 xfail is **gone the right way**: the midnight-reply defect was fixed as
  ruled (DECISIONS 153) and the marker became a plain assertion in the same commit.
* The webapp count moved 117 → 110 with the Digests screen's retirement (156), to
  115 with the 1000-row-cliff regression suite (160), to 119 with the
  latest-row reads (166), and to 101 with the v5 restyle (spec 008, DECISIONS
  170): three glance-era suites retired with their screens, `parentState` and
  `kettleGlyph` arrived. The product count grew to 386 through the outbound
  passes (152/153/154/159/163/165).
* Postgres has died mid-session in this container. `KETTLE_REQUIRE_POSTGRES=1` turns
  that into 169 loud errors instead of a silent skip. Restart and re-run.
* **Verify front-end changes on more than one Node.** The container has 22.22.2, the
  founder runs 24.18.1, and a suite that disagreed between them is what DECISIONS 146
  was about.

**Owed deploys (email polish, DECISIONS 184):** the site ships the email glyph
asset FIRST (`cd site && npm run ci && fly deploy` — the wrapper's one image is
https://heykettle.com/email-glyph.png), then the product
(`cd product && fly deploy`) for per-parent subjects, the recovered evening
body, and multipart HTML emails.

**Owed deploys (spec 010, DECISIONS 185), in this order:** (1) the PM applies
`product/migrations/0019_tz_changed.sql` via MCP — the webapp's pick writes tz
and tz_changed_utc, so the picker must not ship before the grant exists; (2)
`cd product && fly deploy` — the engine's transition honesty (fresh zone reads,
changeover conservatism, the move alert) lives in outbound.py; (3)
`cd webapp && fly deploy` (with the build-arg fly.toml, DECISIONS 114) for the
city picker, the auto journal note, and the changeover-day dot.

**Owed deploy (the living kettle, DECISIONS 187–190):** `cd site && npm run ci &&
fly deploy` ships the kettle mark above the hero kicker, and the hero's tightened
composition with it. The mark carries real alpha and **no blend mode** — the
multiply version worked in desktop Chrome and showed a white rectangle on every
iPhone, because iOS Safari will not blend across the rhythm canvas (190). One
command re-checks the lot against a preview server:
`node scripts/probe-kettle.mjs <preview-url>` — steam proportionality at
120/240/420px, the silhouette, the mark's transparency, the field's layering, and
the hero fitting a 390x844 phone.

**Owed deploy (the ordinary→normal ruling, DECISIONS 192):** `cd product && fly
deploy`. The evening digest body changes to "A normal day, start to finish. Next
note in the morning." — the last surface still saying "ordinary". Independent of
the site deploy below.

**Owed, spec 012 (DECISIONS 202): nothing deploys until the PM reads the build
against the spec.** Then, in order: PM applies migration 0020, then 0021, via MCP
(per-action, with Hema's ok) → `cd product && fly deploy` (the auto-note writer
rides the engine) → `cd webapp && fly deploy` (Memory tab; remember the
build-arg fly.toml, DECISIONS 114). The webapp's journal read now asks for the
`kind` column, so 0020 MUST be applied before the webapp deploys or every
journal read 400s. At the Phase 3
flip, also set `MEMORY_FIRST_REPLY=1` on kettle-api (DECISIONS 203) so the
first_reply journal line arms with the real number.

**Wave D is FLIPPED. The dark stage is complete (DECISIONS 260) and Phase 3
ran on Fri Sep 4 (263).** The ask now goes to real parents from the registered
number on the approved template. Everything in this file that used to say
"rolled back", "unset by design", or "the flip is off the table" described the
world between Sep 1 and Sep 4 and is gone; if you find that language anywhere
else, it is stale.

**One-family scoping is BUILT and unshipped (DECISIONS 263/265).** The webapp
snapshot reads one family — the oldest the account belongs to — and scopes
every other read to it, so the founder's two-family account no longer merges
households on the Family screen. Webapp-only; ships with the next
`cd webapp && fly deploy` (build-arg fly.toml, 114) alongside the 256 date
fix. The switcher is spec 015's (264). Still owed from the 263 post-flip
brief: the template-category watch (262) and, after the Android soak, the
spec 014 §6 items (261).

**The template-category watch is BUILT and unshipped (DECISIONS 262/267).**
Once a UTC day the heartbeat asks Twilio's Content API what v7's WhatsApp
status and category are and raises one founder-only `template_category` ops
alert per day on anything but approved/Utility. Owed, in order: the PM
applies migration **0024** (ops_alerts.family_id nullable — the alert is
about no family), then `cd product && fly deploy`. Until that deploy the
founder keeps reading the v7 template page each Monday (262).

**v7 is the ask, and template iteration is STOPPED (253/262).** v7
(`kettle_ask_parent_v7`) is the only approved-and-Utility template. Everything
after it — v8 through v14, including a control submission of v7's own exact
words — came back Marketing, which is what closed the question: the classifier
was the variable, not the copy. Do not submit another template hoping for a
better category; that road was walked to the end. `tools/submit_ask_template.py`
is a RECORD of what was submitted, not something to run.

**A WhatsApp reaction is not a reply (247), and the fix is an instruction.**
Only a typed message reaches the inbound webhook. A parent who long-presses
and reacts 👍 is a parent Kettle believes did not answer, and the family gets a
follow-on about a morning that was fine. The gap is closed at setup by saying
"type the 👍, don't react" while the phone is in your hand. A quick-reply
button would sidestep it and was tried; it came back Marketing.

**The demo family (the Whitakers) is scenery and must stay that way.**
`families.demo` is true for them (migration 0023), and the outbound engine
skips demo families before it decides anything: no ledger rows, no ops alerts,
no sends. That flag is the ONLY thing stopping them mailing the owner a digest
and the founder an alert every day — "no phone number" (242) stops the ask and
nothing else. The app renders them unchanged. Re-seed with
`scripts.seed_demo_history --through-now`; retired note bodies live in a list
in that script so a renamed note cleans up after itself (251).

**The weekly log-summary job is BUILT and unshipped (DECISIONS 212).** Option C
from docs/log-summary-job-design.md: a counter beside nginx in the site image
tallies allowlisted paths and POSTs counts to kettle-api, which mails the
founder a plain-text summary Monday 9:00am ET. THREE Fly secrets, none set, and
until they are the site serves exactly as before and no email is sent:

    fly secrets set -a kettle-site SITE_METRICS_TOKEN=... \
        SITE_METRICS_ENDPOINT=https://kettle-api.fly.dev/site-metrics/daily
    fly secrets set -a kettle-api  SITE_METRICS_TOKEN=... SITE_METRICS_EMAIL=...

The token must be the SAME string on both apps. Migration 0022 is a file only
and must be applied before kettle-api deploys, or the endpoint 500s on a
missing table. Two things a reviewer should know before this ships: the site's
nginx now writes a three-field access log (timestamp, status, path — no
address, no user agent, no query string) where it previously wrote none, and
the site image gained python3 for the counter. Both are FLAG 1 and the
Dockerfile note in 212. Deploy is a founder step after PM review, post-Wave-D.

**Memory v1.1 is BUILT and unshipped (DECISIONS 214).** Spec 012 §9, all four
items: the notes filter by parent and timeframe (opening on All parents × 3
months per 211), the notes card scrolls inside itself with the composer pinned
below the scroll region, "If you can't reach them" is now its own tab labelled
"Who to call", and the sentence that appeared twice on Memory appears once.

**No migration in this pass, and that is deliberate** — 0021 already gave
`family_contacts` a nullable `parent_id` with policies that check the parent
belongs to the family, plus `position`, which is the rank the spec calls for.
v1.1 simply starts WRITING both from the browser, so policies that were dormant
are now load-bearing and are covered by four new RLS tests. Nothing is owed to
the database: this is a webapp-only deploy when the hold lifts, and it rides
the same hold as the log-summary job (213) — after the dark-stage pass.

One PM call is open in 214: whether to rename `position` to `rank` for
vocabulary alignment with the spec. The recommendation is no.

**Site CI is red on main and it is not the log-summary job.** The images pass
(4c18ed1) added `site/public/resources/img/` for the guide thumbnails, and
`src/tests/resources.test.tsx` treats every directory under `public/resources/`
as a resource page — so it fails five ways on an asset folder. Whoever takes it
decides whether the images move or the scan learns to skip a directory with no
`index.html`. DECISIONS 218 flag 5.

## 3. Live state — do not break

> **STALE BELOW THIS LINE (swept 2026-09-04).** Most of §3 and §4 was written
> between Aug 18 and Aug 23 and describes a world three waves back: Wave A
> unstarted, the site in a redirect loop, migrations 0012 to 0016 unapplied.
> All of that shipped long ago — the schema is at 0023, Wave D is flipped, and
> the site has been live for weeks. §1 and §2 above are current; the DECISIONS
> log is authoritative for anything here that looks like present tense. Left in
> place rather than deleted because the reasoning in it is still worth reading;
> trust the dates, not the tense.

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
* **(RESOLVED, Aug 2026) kettle-site was serving a redirect loop.** The domain
  cascade shipped a config in which `heykettle.com` matched no `server_name`, fell
  into the fly.dev redirect block and 301'd to itself (DECISIONS 148 — my bug;
  `server_name _` is not a default server). Fixed and deployed; the site has
  been live since. Kept for the lesson, which is the whole of DECISIONS 148.

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
   **After deploying, curl the canonical host.** The suite now asks the
   Host-shaped questions (canonicalHost.test.ts, DECISIONS 168) and the image
   build runs nginx -t, but a post-deploy curl of https://heykettle.com stays
   the last word — nothing in any suite reaches the running server.
3. **`fly deploy` kettle-app.** Carries the 112 cache headers — until then deploys
   white-screen returning browsers — plus the login words, the Setup card, and now the
   session-restore fix (144).
4. **(DONE, Aug 2026) Apply migrations 0012, 0013, 0015 and 0016, then
   `fly deploy` kettle-api — this deploy starts Wave A, dark** (DECISIONS
   154/155/159/163). All applied; the schema is at 0023. 0013 decides
   per-table at apply time and prints notices saying what it did; read them. 0012
   creates `sent_messages`, which the loop writes — deploying before applying it
   means a loop that fails every pass — 0015 adds the status column the engine
   writes, and 0016 admits the all-clear kind. (0014 and the relationship labels are already done — PM, 2026-08-23.)
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
   digests, follow-ons and all-clears go to the child's account email; asks record
   as skipped with an ntfy alert each quiet morning — that is the gap Wave C's
   flip closes, expected and visible, not a bug.
7. **The Wave C flip, when Twilio is ready (DECISIONS 163) — after (or with) the
   Wave B flip:**
   1. Twilio console: note the account SID, auth token and sandbox number; have
      both parents send the sandbox join code once from their WhatsApp.
   2. Point the sandbox's inbound webhook at
      `https://kettle-api.fly.dev/outbound/reply` (POST). The route verifies
      Twilio's request signature; no other credential is needed.
   3. ```bash
      fly secrets set -a kettle-api \
        TWILIO_ACCOUNT_SID=AC... TWILIO_AUTH_TOKEN=... \
        TWILIO_WHATSAPP_FROM="whatsapp:+14155238886" \
        OUTBOUND_TRANSPORT="twilio_whatsapp,resend"
      ```
      The comma roster routes the ask by WhatsApp and everything child-facing by
      email; one bad name or missing secret refuses the boot rather than partially
      applying. Rollback: set OUTBOUND_TRANSPORT back to `resend` (or unset for
      console).
   4. Expect: a quiet morning asks the parent on WhatsApp; a 👍 (or anything)
      cancels the follow-on; an unanswered ask escalates by email at the deadline
      even if the WhatsApp send failed; an unjoined sandbox number surfaces as a
      failed send with an ntfy alert.
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

* **The webapp's pings reads come in exactly two shapes, both on purpose**
  (`webapp/src/lib/data.ts`, DECISIONS 160/166): the per-parent 14-day window for
  the Today card and day arc, and the per-(parent, signal) unwindowed latest row
  for tripwire ages and the Setup card. "Simplifying" either — a plain select, or
  one set serving both audiences — re-opens a shipped bug: the 1000-row cliff on
  one side, "Not set up yet" over a 20-day-old tripwire on the other. Tests pin
  the shapes, the audit, and the App call sites.
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
founder errand — and **Wave C is code-complete too** (163): the ask by Twilio
WhatsApp behind the comma roster, the signature-verified reply webhook, escalation
on any-status asks, the unreachable-phone follow-on and the all-clear (161's
bodies, migration 0016). Migrations through **0016**. Waves B and C flip on
secrets alone; Wave D (registered WhatsApp sender) remains the long pole.

**`site/`** — heykettle.com, live on Cloudflare DNS, hosted on Fly. One illustration set
(six webps at unhashed stable names the cache contract depends on — there are no
photographs in the tree). One typeface, five type roles, three weights. Rhythm Field
built and tuned. Floating CTA. Domain cascade done. Everything since DECISIONS 134 is
unshipped.

**`webapp/`** — the family app. 005a/005c/005d built, restyled to Kettle v5 (008),
then redesigned to spec 009 (DECISIONS 176–181): Today with the family rollup and
per-parent cards, the detail with the day arc, seven dots, what-this-means and the
restyled fix card, Family notes v1 (the app's first write paths: journal inserts
and the city_label column), and the accessibility law (rem, AA computed from the
tokens). "normal" replaced "ordinary" everywhere rendered. **Built and tested
only — NOT deployed**, and migrations 0017/0018 are written but NOT applied to
prod: the PM applies them via MCP after review, and they must land BEFORE the
webapp deploy (the app reads journal_entries and three new parents columns at
startup; against an unmigrated prod the snapshot load fails). Then Hema:
`cd webapp && fly deploy`. Session restore
hardened (144) and untouched:
a stored session the server rejects signs out, clears storage and lands on login;
`restoring` is a named state; "Loading…" is bounded at 15s.

## 9. Working norms worth repeating

* **Commit WIP before destructive experiments.** `git checkout <file>` during a
  plant-and-revert has cost uncommitted work here **twice**, most recently in this
  session. Copy the file aside instead.
* **`git rm` + a bare `git commit` sweeps unrelated deletions into your commit.** Three
  times now (caught before push in the 008 build — reset and re-split). Stage with
  explicit paths at commit time; check `git show --stat` before moving on.
* **Verify a guardrail by planting the regression it exists to catch.** In the last two
  sessions this moved the code three times — a guardrail that failed via a fixture
  instead of its own assertion, a claim-path guard nothing isolated, and a storage test
  that would have passed against the object that caused the bug.
* **Commits are the PM's review surface.** Split by concern; explain *why*.
