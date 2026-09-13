# Baton — state of the build

What a fresh session cannot reconstruct from the repo: what is live, what is owed and
by whom, what is deliberate and must not be "fixed", and which traps are specific to
this build. Everything else is written where it applies — product law in the root
`CLAUDE.md`, per-surface norms in each tree's `CLAUDE.md`, the reasoning for every
decision in `specs/DECISIONS.md`.

**Keep this current, and organise it by state, not by session.** A baton that
narrates history goes stale silently; one that states current facts fails loudly. The
narrative of how we got here belongs in DECISIONS. This file is the present tense.
Rewritten 2026-09-13 against DECISIONS 283 to 332; the previous one still called Wave A
unstarted and the site down.

---

## 1. Read these first

| When | Read |
|---|---|
| Always, before believing a green run | `docs/failure-families.md` — the ways work has actually gone wrong here |
| Before any product-suite claim | `product/CLAUDE.md` → Running anything (`KETTLE_REQUIRE_POSTGRES=1` is not optional) |
| Before touching onboarding / setup | `docs/setup-delivery-brief.md`, then `docs/onboarding-runbook.md`, then DECISIONS 92–127 |
| Before touching the ask, the roster or a Twilio setting | `docs/wave-d-dark-stage-runbook.md` |
| To know if a spec still describes the product | `specs/README.md` — one line per spec, current |

The next DECISIONS number is the line at the top of `specs/DECISIONS.md` and **nowhere
else**. Items 1–120 are in `DECISIONS-archive.md`; load it only for a number in range.

## 2. Running the suites

```bash
service postgresql start                       # not running on a fresh container
su postgres -c "psql -c \"alter user postgres with password 'postgres'\""   # fresh container: the role
su postgres -c "createdb kettle_test"                                       # and the database do not exist
python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt -r product/requirements-dev.txt
KETTLE_REQUIRE_POSTGRES=1 .venv/bin/python -m pytest -q     # the root run is what CI prints (267)
cd product && ../.venv/bin/ruff check .
cd webapp && npm ci && npm run ci
cd site   && npm ci && npm run ci
```

Current green: **root `pytest` 904** (857 product + 47 pilot), zero xfails;
**`webapp` 325**; **`site` 236**. `ruff check .` clean in `product/`;
`tools/printables/` is excluded by ruling (266). Never `ruff format` the whole tree;
name the files.

* `pg_isready` saying "accepting connections" is not enough on a fresh container: without
  the role and the database the suite reports "397 passed, 506 errors" and exits 1. Run
  the two `su postgres` lines above.
* Postgres has died mid-session in this container. Re-run `pg_isready` before believing
  any product result, and redirect long runs to a file rather than piping them.
* **Verify front-end changes on more than one Node.** The container has 22.x, the
  founder runs 24.x; the suite that disagreed between them is DECISIONS 146.
* `pip` has timed out on `files.pythonhosted.org` from this container; `uv pip install
  --python .venv/bin/python -r …` is the reliable route.

## 3. What is live

**Schema at 0033, every migration applied** (0033 by the PM, DECISIONS 331). Fly apps:
`kettle-api` (product), `kettle-app` (webapp), `kettle-site` (site).

**Product (`kettle-api`).**
* The outbound channel through Wave D (007, 011; flipped Sep 4, DECISIONS 263): the
  quiet-morning note and the evening note by email, the ask to the parent on WhatsApp
  from the registered HeyKettle number on the v7 Utility template, the follow-on to the
  family, the all-clear. Roster `OUTBOUND_TRANSPORT="twilio_whatsapp,twilio_sms,resend"`.
* SMS for +1 parents (011 Amendment A, 291–294): a +1 parent with no WhatsApp number and
  a recorded consent gets the ask by text through the 10DLC Messaging Service; a
  welcome text once; STOP/START/HELP arrive as `OptOutType` and are never replies. Dark
  stage complete on TestMom (310); a real +1 parent may be enrolled by text. Amma stays
  on WhatsApp.
* The assistant door (019, 285–288; Amendment A, 317–323): kettle-api is the MCP server
  at `/mcp` and its own OAuth authorization server; `today`, `parent_day`, `memory`,
  `who_to_call`, `circles` read-only, `add_note` and `reply` behind `kettle:write`,
  twenty writes an hour per grant, lines marked "{name} via {client}". Claude (phone,
  Cowork, Desktop) and Codex are connected. CIMD works through a shipped copy of Claude's
  client document (319–321, §5 below).
* The family's own devices (020, 313–315): `/d/<token>` records which address fired and
  when; swept at thirty days; nothing feeds the engine.
* Pause (017), the template-category watch (262/267), the demo family skip in both the
  engine and the heartbeat (242/296), the waitlist flood guards (308/312), the shipped
  CIMD copy (320/322).
* The Android server side (014 §6 items 1, 2, 4, 5; 330/331) is **built, 0033 applied,
  NOT deployed** — see §4.

**Webapp (`kettle-app`).** Code sign-in (013), Today with the rollup and per-parent
cards, the parent detail with the day arc, Memory with the filter and "Who to call"
(012, v1.1), the city picker (010), circles with the switcher for two-circle accounts
(015), replies (016), pause (017), edit/delete and the optimistic composer (018),
Assistants on Family (019), devices on Family and the card (020), the button pass
(324–327): one `Action` component, three variants, styles in kettle.css. A day counts
from 06:00 local (299–301) and night is not quiet (303–307). The webapp count of 325 has
no test for the login buttons' look; the PM checks that in Chrome after the deploy.

**Site (`kettle-site`).** heykettle.com, live on Fly behind Cloudflare's proxy (306,
Bot Fight Mode on). The SEO pass of Sep 12–13 is live (332): www 301s to the apex,
robots.txt is the repo's and states the AI policy, the four guides carry a
self-canonical, the footer links every guide and post by its H1, one Organization
record on the home page. Next SEO review 2026-10-06; Search Console after Sep 15.

**Families.** Amma and Appa are live in production, Amma on the old per-app keys and
Appa on merged routine+charger (107/126); Amma's card is on the Austin clock, Appa's on
Chennai. The Rehearsal circle holds TestDad (Raleigh) and TestMom (the founder's own
WhatsApp). The Whitakers are the demo family (`families.demo`, Phoenix): the engine and
the heartbeat skip them, the app renders them unchanged. Beta invitations went out Sep
12 (328, `docs/beta-invitation.md`): free during the beta, $10 a month per parent after
for early families, nothing charged and no payment path built.

**Not known to be live, and not owed either.** The weekly log-summary job (212) is on
main; its three Fly secrets were never recorded as set, so assume it sends nothing.
`WAITLIST_ORIGINS` on kettle-api was never confirmed set (143); the form posts today
(306), so it presumably is.

## 4. Built and not yet shipped; owed

**Product deploy (founder): `cd product && fly deploy`.** Carries the Android server
side (330: the vocabulary, `--platform android`, `POST /s/{slug}/claim`, the two claim
columns) and this pass (333: a claim on a link that is not Android is refused). No
secret, no migration; 0033 is applied.

**Webapp deploy (founder): `cd webapp && npm run ci && fly deploy`.** Carries the login
buttons in the app's primary look, "Phone unlocked" and "Phone moved" in the signal-name
map, and device pings read for thirty days (333). Then the PM in Chrome: the login page
copper, not blue.

**Held by ruling, spec 014.**
* `GET /s/{slug}` **raises for an Android parent** ("no automation instruction for signal
  'unlock'") until the setup page's Android branch lands (§6.3, held by 329 until the Play
  listing exists and its strings are ruled). Do not hand an Android family the link; the
  claim route works without the page.
* The runbook's Android section (§6.7) is written from the first real install.
* The Xiaomi soak (§8.1) waits on the Redmi 15C; `android/SOAK.md` is the checklist.
  The app is in `android/` and is the Android session's, not this one's.

**Founder errands.** The Google Play developer account (014 §9.3, 329). As beta replies
arrive: the PM provisions, the founder runs the FaceTime setup, and the first stranger
family's install produces the field-note block (005b AC1, 328).

**Rulings owed by the PM.** The sandbox sunset (011; one clean week on the real number
has long passed, the retirement needs its own ruling). Nothing else is open.

## 5. Live facts that must not be broken

**Deploys and secrets.**
* **`fly secrets set` restarts the machine on the OLD image** (294). The transport
  registry refuses the boot on a name it does not know, so for any new transport deploy
  the code first, then set `OUTBOUND_TRANSPORT`, with the transport's own secrets in the
  same command. `twilio_sms` without its Messaging Service SID refuses the boot too.
  Rollback is the roster alone. The runbook has the order.
* **Twilio's Advanced Opt-Out is off until its button is pressed** (294). A filled-in
  keyword page is not enough; Twilio's stock STOP confirmation arriving is the tell, and
  until then STOP and START reach `/outbound/reply` without `OptOutType`.
* **A bare `fly deploy` of the webapp ships a deaf app** (114): the API base URL is a
  build arg carried by `webapp/fly.toml`.
* **After any Cloudflare change, read robots.txt from the outside and check Search
  Console within the week** (332). A crawler setting was due to block Googlebot, Bingbot
  and Applebot from Sep 15, and Cloudflare was serving its own robots.txt over the
  repo's; a test now holds the repo's, but nothing in any suite reaches the edge.
* **Claude sends the CIMD client_id whenever a server advertises
  `client_id_metadata_document_supported`**, and claude.ai's edge answers Fly's fetch of
  that document with a Cloudflare challenge (319–321). Hence `KNOWN_CLIENT_DOCUMENTS`
  in `assistant_auth.py`: a live fetch wins when it works, the shipped copy stands when
  it fails, a failure is remembered ten minutes. "Register automatically" in Claude is
  not a workaround.

**The ask.**
* **v7 is the ask and template iteration is STOPPED** (253/262). Every later
  submission, v7's own exact words included, came back Marketing. Do not submit
  another. `tools/submit_ask_template.py` is a record, not something to run.
* **A WhatsApp reaction is not a reply** (247): only a typed message reaches the
  webhook. The fix is the setup instruction, "type the 👍, don't react".
* **The demo family's `families.demo` flag is the only thing** stopping the Whitakers
  from mailing the owner a digest and the founder an alert every day.
* `families.ladder_mode` and 0007's threshold columns survive the 003/004 retirement
  (141); `digest_sends` stays in the schema with nothing reading or writing it.

**The app and its reads.**
* **Three ping-read shapes, all on purpose** (`webapp/src/lib/data.ts`, 160/166/314):
  the per-parent fourteen-day window for the card and the arc, the per-(parent, signal)
  unwindowed latest row for tripwire ages and the setup card, and device pings for the
  thirty days the sweep keeps them. A plain select re-opens the 1000-row cliff; a shared
  window puts "Not set up yet" over a twenty-day-old tripwire or "Nothing heard yet"
  over a three-week-old device. Tests pin the shapes; a product contract test holds the
  device window to `HOUSEHOLD_SWEEP_DAYS`.
* **The webapp test suite installs its own `localStorage`** (146): enumerable own
  properties, a non-enumerable marker the guardrail asserts. The jsdom pin does not
  replace it.
* **`isAuthFailure` is narrow on purpose** (144): a 500, a 429 or a dropped connection
  must not end a working session.
* **One action vocabulary** (324/325): every action is an `<Action>`; the styles live in
  kettle.css so a screen cannot grow a fourth style; the filter chips, the city list's
  options and the roster row are selection controls, allow-listed one per file. The
  shadcn `Button` is gone.
* The card, the arc and the dots count from 06:00 local, `DAY_START_HOUR`, held equal to
  the engine's `MORNING_WINDOW_START` by a product test (300). Night wins over quiet;
  paused and unreachable win over night (304).

**The doors.**
* **The 0032 trigger keeps a JWT caller's seat from the JWT**; with no JWT, a provided
  author survives only if that member belongs to the row's family (317/318). Kettle's
  own lines carry none.
* **`/mcp` answers directly, no redirect** (286): Claude's first probe must get the 401
  with its `resource_metadata` header. The MCP tests run with redirects off.
* `assistant_grants` is read by column grant; the token hashes are granted to nobody
  (285). `kettle:write` implies read and is what a both-scopes grant stores (317).
* **A claim never revokes** (330): the link's own Android row is claimed once, every later
  claim on the slug is a new row with a fresh token, and the earlier row stays active
  until the founder revokes it. A claim on a link that is not Android is refused (331).
* **The in-memory counters are process-local and reset on restart** (308, 330): the
  waitlist's five an hour per IP, the claim's ten an hour per slug. Accepted for a
  one-machine app; a second machine would need a shared store.

**The site.**
* **`site/nginx.conf`'s redirect is a named `server` block, not an `if`**, and the
  serving block carries `listen 8080 default_server` (142/148). Removing the flag took
  the site down once; a test fails by name if it goes.
* **`privacy.html` has no `<link rel="canonical">`** and no absolute URL, so a reader
  can verify it fetches nothing. The 332 self-canonical is on the four guides only.
* `docs/failure-families.md` sections are appended, never renumbered — rulings cite
  them by number.

## 6. Working norms worth repeating

* **Commit WIP before destructive experiments.** `git checkout <file>` during a
  plant-and-revert has cost uncommitted work here twice. Copy the file aside instead.
* **A `git rm` in one shell while a `git commit` runs in another sweeps the deletion
  into the wrong commit.** It happened again on 2026-09-13 and had to be re-split
  before the push. Stage with explicit paths, one commit at a time, and read `git show
  --stat` before moving on.
* **Verify a guardrail by planting the regression it exists to catch.** A green
  assertion is not evidence it is load-bearing; every build's DECISIONS entry lists its
  plants.
* **Commits are the PM's review surface.** Split by concern; explain *why*. Update the
  DECISIONS header line, not only the entry (297/301 both had to fix it).
