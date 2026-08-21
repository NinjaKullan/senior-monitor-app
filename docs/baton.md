# Baton — state of the build

The session handoff: what is built, what is deployed, what is owed and by whom, and
which live facts a fresh session must not break. Everything else — product law, the
per-surface norms, the conventions — is written down where it applies; this file is
only the things a fresh implementer cannot reconstruct from the repo.

**Keep this current.** It is the first thing the next session reads, and a baton that
describes last week is worse than no baton at all.

## Start here after a session break

**`docs/setup-delivery-brief.md` (2026-08-13).** State of the world, the setup/delivery problem
stated properly — a parent faces ~78 interactions today and delivery is only ~15% of them — the two
cheap experiments that decide spec 005b's shape, and what is owed by whom. Read it before
`docs/onboarding-runbook.md` and DECISIONS 92–102.

## State of the build (baton, 2026-08-21 — session handoff, second pass)

**All three suites green** (`pytest` 277 + 1 xfail with Postgres up, `webapp` 117,
`site` 174 — the product count fell from 401 to 270 because the digest and ladder
suites went with their engines (DECISIONS 141); the xfail is a real open bug, not a
skipped test, see DECISIONS 145 — always confirm the product suite with `KETTLE_REQUIRE_POSTGRES=1`,
never trust a skip. The `--revoke` ~1-in-64 flake is *fixed* as of DECISIONS 139;
a failure there now means something new.). Specs 001–006 plus amendments A/B built and reviewed;
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

**005b as built** (details in DECISIONS 118–123): migration 0010
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
founder-PAUSED per DECISIONS 126):** 93 (forge derives out path from token), 95
(`--add-device` / `--rotate`), 100 (platform-aware standard set), 101 (person
prefix on disk filenames); 124 (family-context header on Today + the duplicated
Family-circle row); reconciling the built setup page's `kettle/setup_copy.py`
against the PM's keyed deck `specs/005b-copy.md` (landed with item 132, written
2026-08-16 — the page was built from the mock before the deck was in the repo;
queues behind the same pause).

**Done in the DECISIONS 139 context pass, and off this queue:** the item-122
channel-name exemption, the runbook §7 consent rewrite (125a), the `--revoke`
dashed-token fix, `dist/` cleared before every front-end build, and the
diptych brief marked superseded.
**The next DECISIONS number lives at the top of `specs/DECISIONS.md`** and nowhere
else — it used to be repeated here, and two copies of a counter is one too many.

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

**Spec 007 Wave A is in (DECISIONS 140, this session).** The outbound channel's
decision core is built and **runs dark**: the quiet-morning evaluator, the
scheduler, the sent-once ledger (migration **0012**, `sent_messages`), the
template registry with §5's bodies verbatim, the console transport behind the
`Transport` seam, and `/outbound/reply`, which nothing calls and which 404s
until `OUTBOUND_REPLY_TOKEN` is set. `OUTBOUND_ENABLED` is off by default and
"on" still reaches nobody in this wave. **That ruling has landed: 007
supersedes 003 and 004** (DECISIONS 141), so 007 is now the only engine in the tree
that can speak. See DECISIONS 140 for the rest of the execution calls.

**The front-end suites no longer depend on the host machine (DECISIONS 146).** `npm
run ci` for the webapp was green here and red on the founder's Node 24.18.1, on
identical code and lockfile. vitest's jsdom setup skips installing jsdom's
`localStorage` whenever the host global already has one, so the tests used the host's
object. `webapp/src/tests/setup.ts` now installs its **own** Storage unconditionally,
and all 22 test files across webapp and site carry `@vitest-environment jsdom`.

**Three things a fresh session must not undo here.** The storage stub's items are
**enumerable own properties** on purpose — `clearStoredSession` walks `Object.keys`,
and a Map-backed fake passes its own tests while breaking its only caller. The
non-enumerable marker the guardrail reads is what proves the stub won rather than that
"storage works"; without it the guardrail passes against the object that caused the
bug. And the per-file environment pin does **not** replace the stub — the shadowing
happens inside jsdom setup, so naming the environment does not prevent it.

**Verify front-end changes on more than one Node.** Node 22.22.2 is the container's;
the founder runs 24.18.1. This pass was verified green on both, with a hostile host
`localStorage` present and absent. Injecting one requires `--import`, because a setup
file runs after the environment is built and cannot reproduce the condition.

**The domain is heykettle.com (DECISIONS 142–143, this session).** Live on Cloudflare
DNS, site still hosted on Fly, Resend verified on `send.heykettle.com`. The contact
address is `hello@heykettle.com`, `<link rel="canonical" href="https://heykettle.com/">`
is in the site head, and `site/nginx.conf` 301s `kettle-site.fly.dev` to the apex from
a **named server block** — requests on the real domain never enter it, so the caching
contract is structurally unaffected. `/healthz` deliberately answers on both hosts.
**privacy.html deliberately has NO canonical**: it is held to a stricter standing law
(stands alone, no `<link>`, no absolute URL) and that law won — do not "fix" it.

**Owed by the founder, one command:** `WAITLIST_ORIGINS` is an env var on kettle-api
and setting it **replaces** the default rather than adding to it, so the whole list
has to be named:

```bash
fly secrets set -a kettle-api \
  WAITLIST_ORIGINS="https://heykettle.com,https://www.heykettle.com,https://kettle-site.fly.dev"
```

The fly.dev entry comes out when the old host stops being used. The code default is
the heykettle pair plus localhost and deliberately excludes fly.dev.

**The family app's session restore is fixed (DECISIONS 144).** A stored session whose
token the server rejects now signs out, clears storage and lands on login; `restoring`
is a named state; "Loading…" is bounded at 15s. `webapp/src/lib/session.ts` carries the
reasoning. **Do not widen `isAuthFailure`** — a 500 or a dropped connection must not
end a working session, and a test holds that line.

**One open bug with a ruling owed (DECISIONS 145).** `record_parent_reply` matches the
ask by local calendar day, so a parent who answers after local midnight cancels
nothing and her family gets escalated to anyway. Pinned as a `strict=True` xfail in
`test_outbound.py` — when it is fixed the marker fails as XPASS and must be removed.
The repair is a spec choice (match the most recent unanswered ask, then bound
"recent"), which is why it was not made here.

**Specs 003 and 004 are RETIRED (DECISIONS 141, this session).** `digest.py`,
`ladder.py`, their copy modules, the channel abstraction, `scripts/ladder.py` and the
`/twilio/inbound` webhook are deleted; both background loops are gone from `main.py`;
the eight `DIGEST_*`/`LADDER_*`/`TWILIO_*` settings no longer exist. Migration **0013**
retires the ladder tables and **decides at apply time** — a table that never held a row
is dropped, a table with rows is renamed `retired_<name>` with policies dropped and
privileges revoked. `families.ladder_mode` and 0007's per-parent threshold columns are
left in place on purpose (the ruling named tables; a column drop is not reversible).
`specs/README.md` is the new index of what still describes the product.

**Two things a fresh session must not get wrong here.** First, **`digest_sends` is still
in the schema and must stay** until someone decides otherwise — the family app's Digests
screen renders from it (`webapp/src/lib/queries.ts` READ_SURFACE), and 007's
`sent_messages` is RLS deny-all so it cannot replace it. Nothing writes to
`digest_sends` any more, so the screen shows a log that stopped; the two ways out are in
DECISIONS 141 and both are the PM's call, not a migration. Second, **DECISIONS 141 lists
sixteen things 007 does not have that the retired engines did** — founder ops alerts on
delivery failure, `ask_skipped`, `mechanism_ok`, the evidence gate, the morning cutoff,
the all-clear, and the rest. None of it blocks Wave A, which runs dark; several are
load-bearing before a message reaches a family.

**Still owed from this pass: §5's five corrected template bodies.** The ruling was to
replace them with the founder's strings verbatim; that message was not in the session's
context, and `specs/007-outbound-channel.md` §5 still carries the originals, so
`outbound_templates.py` is unchanged and still renders "Appa's morning looked like her
morning." The DECISIONS 24 pronoun problem and the DECISIONS 127 em dash are both still
live in product copy. **Ask for the five strings; it is a ten-minute pass.**

**The context pass is in (DECISIONS 139, previous session).** The decision log is
renamed and split (1–120 archived), CLAUDE.md is 72 lines with the surface norms
in `site/CLAUDE.md`, `product/CLAUDE.md` and `webapp/CLAUDE.md`, and the traps
live in `docs/failure-families.md`. This file is what is left of the old root
file's baton section.

**The floating CTA is in (Q137, previous session).** One fixed pill, the same
PillLink, the hero's exact string, pointed at `#waitlist`. It yields by
rendering `null` — not a hidden element — whenever the hero, the form or the
footer is on screen, so the page never carries an overlay; the frame is
`pointer-events-none` and does the centring so no transform is involved; entry
is the motion law's `motion-safe:animate-rise` and there is no exit animation;
and with no IntersectionObserver it never appears at all. `probe-responsive.mjs`
now walks five scroll stops at 360/390/428/768/1440. **Known and recorded: the
footer entry in the yield list is redundant at present page proportions** (the
form is still on screen whenever the footer is) — the unit test holds it, the
browser probe cannot reach it.

**The illustration pass is in (Q136, previous session).** The site's imagery is one
drawn set: the hero is a single wide illustration (the two-frame grid deleted, not
collapsed — the artwork holds the gap), the four scenario panels and a new narrative
strip above the how-it-works steps carry the rest, and all six alt strings are the
PM's words, which passed the copy law unmodified. The scenario tab row no longer
folds into two ragged lines on a phone: below md it is one sideways-scrolling row
with a measured mask fade and 40px targets, kept in view by `scrollLeft` (never
`scrollIntoView`, which would take the page with it). Retired photographs, the dead
Fraunces dependency and `site/Pill.tsx` are gone, and the caching test's manifest is
the new six. **Mobile verification is now a standing norm** (see the working norms
above) with `site/scripts/probe-responsive.mjs` behind it. Two things found on the
way and left for the PM: `--revoke <token>` fails on ~1 device token in 64 (argparse
reads a leading `-` as a flag; `--setup-link` has the same exposure), and
`docs/hero-diptych-brief.md` now describes a retired form.

**The one-voice pass is in (Q135, previous session).** The site speaks in one
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
again — four passes are now unshipped (Q134's note correction and field
visibility, Q135's one-voice typography plus the field band and the stir, Q136's
illustration set and mobile tab row, Q137's floating CTA), and their acceptance
tests are the PM and the founder looking at the live site — the h2 size drop, the 390px band fit and the
strip's placement under the how-it-works heading especially; `fly deploy` of
kettle-app (Q112 cache headers — until then deploys white-screen returning
browsers — plus login words and the Setup card); the SMTP plan's DNS + dashboard
steps (`docs/auth-smtp-plan.md`) before any non-founder family; Q126's 48-hour
check that Appa's charger automation has both edges ticked.

**Owed before Wave B (spec 007 §6.3):** the founder family runs Wave A dark for
48 hours and the ledger is reviewed against what actually happened. The SMTP plan
now says Resend (DECISIONS 138), so the domain and its DNS records are the next
thing on that critical path.

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
`docs/onboarding-runbook.md`, then DECISIONS 92–127 (the 2026-08-16 rulings
and the Appa field log especially). The runbook carries the item-107 field
gotchas (charger trigger defaults to Run After Confirmation and must be
flipped to Run Immediately; merged automation subtitles read "Kettle — Daily
routine" and that is correct, not mislabelled); the consent one-pager is gone
per Q125 — the setup page's first screen is the consent conversation now.
