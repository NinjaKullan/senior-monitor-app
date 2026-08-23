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

Current green: **`pytest` 321, zero xfails**, **`webapp` 117**, **`site` 174**.

* The 145 xfail is **gone the right way**: the midnight-reply defect was fixed as
  ruled (DECISIONS 153) and the marker became a plain assertion in the same commit.
* The product count fell from 401 to 270 when the digest and ladder suites went with
  their engines (DECISIONS 141); the outbound copy pass and the reply repair brought
  it to 321.
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
* **`digest_sends` must stay in the schema.** Nothing writes to it since the retirement,
  but the family app's Digests screen reads it (`webapp/src/lib/queries.ts`
  `READ_SURFACE`), and 007's `sent_messages` is RLS deny-all so it cannot replace it.
  Retiring it empties a screen in a live app. Two ways out in DECISIONS 141; both are
  the PM's call, not a migration.
* **The waitlist form is CORS-dead** until `WAITLIST_ORIGINS` on kettle-api includes the
  serving origin. Unconfirmed whether it was ever set. See §4.
* **kettle-site is serving a redirect loop in production right now.** The domain
  cascade shipped a config in which `heykettle.com` matched no `server_name`, fell
  into the fly.dev redirect block and 301'd to itself (DECISIONS 148 — my bug;
  `server_name _` is not a default server). **The fix is committed and NOT deployed.**
  Until `fly deploy` runs, the site is unreachable.

**Deployed as of 2026-08-18 (founder-reported):** migration 0011 applied and verified in
the live database; kettle-api healthy (`/healthz` → `{"db":true}`); kettle-site at
`2f1f2f5`. **Migrations 0012 and 0013 are written but NOT applied.** The site runs a
build that predates six unshipped passes (§4).

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
4. **Apply migrations 0012, 0013 and 0014.** 0013 decides per-table at apply time and
   prints notices saying what it did; read them. After 0014, **set the relationship
   labels for both live parents** (DECISIONS 149/152):
   ```bash
   python -m scripts.provision --set-relationship <amma-device-token> --relationship Mom
   python -m scripts.provision --set-relationship <appa-device-token> --relationship Dad
   ```
   Until set, relationship-bearing messages (morning digest, follow-on) skip that
   parent — silently in the ledger, loudly in the logs — while asks still go.
5. **Run Wave A dark for 48 hours** and review the ledger against what actually
   happened (spec 007 §6.3). That review is the gate to Wave B.
6. **The Resend DNS records** on `send.heykettle.com` before any non-founder family
   (`docs/auth-smtp-plan.md`).
7. **Confirm Appa's charger automation has both edges ticked** (126).

## 5. Owed — rulings from the PM

| # | The question |
|---|---|
| **141** | `digest_sends`: give `sent_messages` a family-scoped read policy and move the Digests screen, or retire the screen? |
| **141** | Sixteen capabilities 007 lacks that the retired engines had — founder ops alerts on delivery failure, `ask_skipped`, `mechanism_ok`, the evidence gate, the morning cutoff, the all-clear. None blocks Wave A; several are load-bearing before a message reaches a family. |
| **142** | Two cheap-to-overrule calls: `/healthz` answers on both hosts instead of redirecting; privacy.html has no canonical. |
| **152** | Where the *child* picks the relationship label. For beta it is founder-entered at provisioning (`--parent "Amma::Mom"`, `--set-relationship`); 149 says "the child picks at setup" without naming the surface, and onboarding investment is founder-PAUSED (126). |

Resolved since: **151** delivered the five template bodies, **149** ruled relationship
labels over names, **150** ruled the ask's icon — and **152** built all three (§6).
**145's midnight-reply bug is fixed as ruled** (pending-ask match, 24-hour bound,
no-pending-ask replies noted only — DECISIONS 153, spec 007 §2.6 amended); the
suite's only xfail went with it.

## 6. The outbound copy pass (149, 150, 151) — built

Landed 2026-08-23 (DECISIONS 152). The registry renders the five approved bodies
verbatim; `{relationship}` superseded `{parent_name}`; the copy-law scan now enforces
no-gendered-pronoun (149, closing 24) and no-em-dash (151, extending 127) as law, with
plants. Migration 0014 adds `parents.relationship`, nullable, closed to the standard
set by a check constraint that a test holds identical to
`kettle.provisioning.RELATIONSHIP_LABELS`.

**Live consequence until the founder acts (§4 item 4): both live parents have no
label**, so their morning digests and follow-ons are skipped (slot left free, warning
logged) while asks still go — parent-first survives the gap by construction. Template
ids are unchanged, so the ledger and Wave D's future WhatsApp registration are
unaffected. The site's quoted ask string is deliberately untouched (150's scope
ruling).

## 7. Deliberate, and easy to "fix" by mistake

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
is built and runs dark** — evaluator, scheduler, sent-once ledger (0012 `sent_messages`),
template registry (the DECISIONS 151 bodies, rendered by relationship label), console
transport behind the `Transport` seam, and a reply endpoint nothing calls.
`OUTBOUND_ENABLED` is off and "on" still reaches nobody. Waves B–D are each gated on a
founder errand. Migrations through **0014**.

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
