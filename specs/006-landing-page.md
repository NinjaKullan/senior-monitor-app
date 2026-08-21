# Spec 006 — Landing page (getkettle.*)

**STATUS: BUILT — `1effca4..0bbf9cc`, reviewed and approved by PM 2026-08-02 (rulings 78–83 in DECISIONS.md). Amendment A (§10) is BUILT (`369f33e..66457ee`, approved). Amendment B (§11, the kettle story) is ACTIVE — build it. Site is LIVE at kettle-site.fly.dev; remaining founder steps: migration 0009 to `kettle-prod`, `WAITLIST_ORIGINS` to include the serving origin, DNS.**

*PM: Fable, 2026-08-02. The Wave-0 landing page: one static page whose job is to collect a waitlist and ask THE question ("What phone does your parent use?" — it decides Wave 2 priority with data, per the GTM roadmap). `docs/design-language.md` is the law of this surface; this spec locks its TBD-at-spec-time values, defines the page, and wires the copy-law tests into marketing. Rulings 74–76 govern typography, the eyebrow slot, and the trade-dress line. Where this spec drafts copy, the **rules** are binding and the **strings** are founder-editable at review — swap a sentence freely, but it must still pass the tests in §8.*

## 1. Scope and non-goals

Deliverables: a static site in `site/` (new top-level directory), plus the smallest possible waitlist backend — migration 0009 and one public endpoint on kettle-api. Founder owns DNS, hosting, and deploy; the build produces a `dist/` and a README section saying exactly what to point where.

**Non-goals, decided here so they are not re-litigated in DECISIONS:** no Phone Watch tier mention (post-beta decision, and its device/person language guardrail deserves its own spec), no checkout or billing, no blog, no analytics or tracking of any kind ever (law #4 — not even self-hosted page counters in v1), no A/B tooling, no confirmation email (no email infra exists; the success state is the confirmation), no scroll-scrubbed pinning (design-language §6 refuses it for v1).

## 2. Locked values (closes design-language §4/§5 open items)

All colour lives in one tokens file (`site/src/tokens.css` or equivalent single source). No hex/hsl/rgba literal may appear outside it (AC1).

| Token | Value | Notes |
|---|---|---|
| `--canvas` | `#F6F2EC` | Warm canvas. Deliberately not Oura's `#F7F1E8` — shifted greener, which both serves Kettle green and honours ruling 76 ("never their pair"). |
| `--ink` | `#403C36` | Warm dark, R>G>B, never true black. Measures ≈9.8:1 on canvas. |
| `--calm` | `hsl(158 50% 32%)` | Kettle green stays primary — same token value as `webapp/src/index.css`. |
| `--clay` | `#C29179` | Secondary warmth: grounds and warm accents only, never a status. Dustier and greyer than Oura's `#D89078` — same trade-dress reasoning as canvas. |
| `--text-secondary` | `#6C665D` | Measures ≈5.1:1 on canvas; AC1 verifies ≥4.5:1 programmatically, not by trust. |
| `--error` | `#9E3B2E` | **Form errors only.** Never a status, never a person, never decoration. The only red on the page, and only in §5's form. |

Amber (`--attention`) does **not** exist on this site — it is equipment vocabulary for the app, and marketing carries zero alert states. Its absence is asserted (AC2). Dark sections invert exactly: ink ground, canvas text, no third scheme.

**Gradient tints.** The measured corner-wash template is adopted verbatim as geometry; only the tints are ours:

```
ellipse at 0% 0% → transparent 20% · circle 99% 0% → 30% · circle 10% 90% → 50% · circle 99% 99% → 40%
```

Four tint sets, one per scenario tab; the hero shares the morning set. Locked here (founder may re-tint at review; the invariants may not move — anchored at edges/corners, never centred on content, alpha 0.3–0.7, always fading to `transparent`):

| Set | The four tints (in template order) |
|---|---|
| Morning (hero, *Her morning*) | `rgba(226,178,140,.5)` · `rgba(233,199,158,.45)` · `rgba(214,169,133,.5)` · `rgba(226,178,140,.4)` |
| Afternoon (*Her afternoon*) | `rgba(178,182,166,.4)` · `rgba(196,196,182,.35)` · `rgba(170,178,164,.4)` · `rgba(186,188,172,.35)` |
| Off (*When something's off*) | `rgba(84,110,100,.4)` · `rgba(100,124,114,.35)` · `rgba(76,104,94,.45)` · `rgba(92,116,106,.35)` |
| Seen (*What you see*) | `rgba(122,164,146,.35)` · `rgba(180,190,178,.3)` · `rgba(134,170,152,.35)` · `rgba(160,180,168,.3)` |

The "off" set is cooler slate-green — **never red, never warm-alarm**. Panels differ by tint alone, never by structure (AC5).

**Typography** is ruling 74, restated as build requirements: Fraunces + Instrument Sans, self-hosted at build (`@fontsource` packages are the sanctioned dependency — they vendor the woff2, zero runtime third-party requests), and the CTA weight must be a **true semibold file**, not a faux-bold. Scale, leading and tracking per design-language §3's table; body is 16px.

## 3. Page structure, top to bottom

One idea per viewport; beats ~700–1,100px apart. Every section entry is a fade + 10–30px rise, 0.8–1.2s, gated `motion-safe:` — under `prefers-reduced-motion` the page is fully static (AC7).

### 3.1 Hero

Morning tint over flat canvas. Eyebrow (sections/scenarios only, per ruling 75): `FOR FAMILIES FAR AWAY`. H1 is the YC one-liner slot; the shipping draft is `Know the day started normally.` (the founder may swap in the final YC phrasing later — a copy change, not a spec change) Sub, ~20 words, draft: `Kettle notices when your mother's ordinary phone routine doesn't happen — and asks her first, before anyone worries.` One CTA pill, `Join waitlist`, anchor-scrolls to §3.5. Image slot: **concept 3** (balcony garden in Chennai / son in Brooklyn exhaling).

### 3.2 Scenario tabs — the centrepiece

Tabs: `Her morning · Her afternoon · When something's off · What you see`. Grammar is the measured set, exactly: active = regular weight, ink text, full opacity, 3px ink bottom border; inactive = 0.7 opacity, transparent border; 300ms opacity ease on the tab, **panel swaps instantly**. Switching tabs changes the corner-wash tint set and the panel content; the panel DOM structure is identical across all four (AC5/AC6). Without JavaScript the four panels render stacked in order — the page must be fully readable with no script (AC13).

Each panel: scenario eyebrow, a serif emphasis phrase inside a sans sentence (the §3 serif budget), a short paragraph, an image slot, and — where noted — the notification component. Draft content; rules binding, strings editable:

- **Her morning** — image **concept 1** (chai, crooked video call, crossword). Copy names the moment, past tense: `By the time the chai went cold she'd called her sister, read the news, and lost an argument with the crossword.` Then the fact: `Her phone did its ordinary things. That's all Kettle ever needs.`
- **Her afternoon** — image **concept 2** (scooter, helmet, voice note). The quiet stretch is ordinary, not alarming: `A nap is not a signal. Kettle knows the shape of her whole day, so a quiet afternoon reads as exactly that.`
- **When something's off** — image **concept 5** (dance rehearsal, phone on the piano — the something-off that was nothing: she was dancing). Cooler tint, never red, no alarm styling of any kind. The panel shows the **senior-first ask** in the notification component, rendered on *her* phone: body `Everything okay today? Reply whenever suits.` (allowlisted string — it is a question to her, not a claim about her). Copy: `When the morning doesn't look like her morning, Kettle asks her first, quietly. Only if she doesn't answer does anyone else hear a thing.`
- **What you see** — image **concept 4** (recipe over the propped-up tablet). Notification component showing the morning digest on *your* phone: body `Amma's day started normally.` Copy: `Two short messages a day. Never a feed, never a score, never a graph — a phrase, when there's something worth saying.`

### 3.3 The three fields (privacy centrepiece)

Dark section — exact inversion, ink ground. Three pill chips: `who` · `signal` · `when`. H2: `Three fields. Nothing else.` Copy (sans states the fact, serif carries the feeling): `This is the whole record Kettle keeps. Not what she typed. Not who she called. Not where she went. What isn't collected can't leak.` This section's claims must be literally true of the schema — who, signal, server timestamp — and AC3's plants include a claim-drift case.

### 3.4 How it works

Three steps, numbered (numerals allowlisted). H2: `How Kettle works.`

1. `Set up together on one video call.` — pre-built shortcuts on her phone note its ordinary moments; she approves every one, and can switch any of it off herself.
2. `Kettle watches for the absence of normal.` — no content, no location, no listening; the only thing observed is that routine happened.
3. `You hear twice a day. She's asked first.` — quiet reassurance, morning and evening; if the day looks unusual, the first message goes to her, not about her.

Delivery-channel and setup vocabulary (WhatsApp, FaceTime, Shortcuts) is permitted **here and only here** — the mechanism may be named; her activity may never be narrated through app names (§4's line, tested).

### 3.5 Founding families (waitlist)

H2: `Join the founding families.` Price line (the GTM roadmap's decided founding rate): `The founding rate is $10 a month per loved one, honoured for as long as you stay.` (No urgency vocabulary — "limited-time" and countdowns are banned; the offer is stated flat.) Form, per the zero-free-text principle extended to marketing — the only typed field is the email:

- Email input (the page's one free-text field).
- `What phone does your parent use?` — fixed choices: `iPhone` / `Android` / `Not sure`.
- Hidden honeypot field (silently accepted and discarded server-side).
- Submit pill: `Request invite`. Success state, flat: `You're on the list.` Failure: inline form error in `--error` — the page's only red.

### 3.6 Footer

Wordmark, `Three fields. Nothing else.`, a link to a plain static privacy page (same copy law; legal text is founder+counsel, a placeholder page ships), a `mailto:` contact. No social icons pretending a presence that doesn't exist yet.

## 4. Copy law — the marketing extension

Design-language §8 requires extending the product's copy-law tests to marketing rather than inventing a second standard. Same pattern as the webapp: every rendered string lives in `site/src/copy.ts`; `assertCopyLaw(text, allow)` masks a pinned allowlist, then scans; the ban side is derived where possible so new entries join the ban for free (DECISIONS 62 precedent).

Banned on this surface, in addition to the existing product bans:

- **Urgency vocabulary:** `now`, `hurry`, `don't miss`, `limited`, `last chance`, `act fast`, `today only`, and any `!` in a CTA or heading.
- **Person-status verdicts as claims:** `she's fine`, `is safe`, `doing well`, `okay` *as assertions about the parent*. The senior-ask question string is a pinned allowlist literal — a question addressed to her, not a verdict about her.
- **Diagnosis/decline vocabulary:** `dementia`, `decline`, `deteriorat*`, `symptoms`, `health score` — law #1 applies to marketing with less licence, not more.
- **Alarm vocabulary:** `alert`, `alarm`, `emergency`, `SOS`, `urgent` — the ladder is described as *asking* and *hearing*, never alerting.
- **Surveillance vocabulary:** `track`, `tracking`, `surveillance`, `watch her` (negated forms in the founder's one-liner, if used, are pinned literals).
- **App names inside activity narration.** `WhatsApp`/`FaceTime`/`Shortcuts` may appear in §3.4's mechanism copy only; a sentence describing *her day* may never name an app (the digest-grade coarseness rule, applied to marketing).

**Digits:** DOM-walk digit scan per the 005d AC3 pattern (including the item-67 SVG-geometry narrowing precedent). The only digits allowed are a pinned literal allowlist: the price string, step numerals `1 2 3`, and nothing else. Notification-mockup timestamps therefore render the word `Today` — no clock times exist anywhere on this page. **Shape rules as tests:** H2s run 3–5 words; H1 ≤7; no paragraph exceeds 23 words.

## 5. Components

- **CTAs** are full pills, 12/24 padding, true semibold; hover is a colour-only shift ~150ms — no elevation, no transform (AC7 plants `hover:scale` and watches it fail).
- **Radii ladder:** 8 content/photo cards · 24 chips/media tiles · 40 feature panels · full pill for anything clickable. Cards separate by background change, not shadow.
- **Notification mockup is a component, not an asset**, at the measured proportions: ≈4.2:1 card, transparent fill so the slot behind shows through, ~2px stroke in `--ink` at reduced opacity, radius ≈2% of card width, app icon 13.5% of width at ~8% icon radius, one single-line body sentence, right-aligned `Today` timestamp. Icon is the Kettle mark on `--calm`. Constants live in one place and are tested (AC11).
- **Eyebrows** label sections and scenarios only (ruling 75). No person-status eyebrow exists, and AC3's plants include one to prove the test would catch it.
- **Refused components**, restated so no helpful implementer adds them: scores, numerals-as-verdicts, charts, sparklines, timelines, rings, countdowns, testimonial carousels with invented people.

## 6. Imagery

Five slots, keyed to design-language §9's commissioned concepts: hero→3, morning→1, afternoon→2, off→5, seen→4. Photography does not exist yet: slots ship as flat warm placeholder blocks (`--clay`/`--canvas` mixes) with the final **alt text baked in now** — no stock photography, ever; the banned-cliché list makes stock a liability, and an honest placeholder beats a toothpaste smile. Alt text is copy, lives in `copy.ts`, passes copy law, and describes agency (e.g. `Grandmother mid-laugh on a video call, chai steaming beside her phone`).

**No alert imagery, ever** — anywhere on this page, including inside the notification mockups: no red badges, no sirens, no worried faces, no clutched phones. Enforced three ways: the token scan (AC2 — no alarm colours exist to style it with), the copy law on all alt/aria text (AC3), and named at founder review as the human gate for the commissioned photos.

## 7. Implementation surface

`site/` reuses the webapp's stack and CI shape — React + Vite + TS + Tailwind, vitest + Testing Library, `npm run ci` = lint → vitest → tsc+build → secret scan — consistency beats novelty in a repo already carrying that toolchain. Two additions to its CI: a **foreign-origin scan** of `dist/` (no URL to any origin we don't control: fonts self-hosted, no CDN, no third-party script — law #4 made mechanical) and a **prerender check** (the built HTML contains the page copy, not an empty root — the page must read without JavaScript).

**Backend (kettle-api + migration 0009):** table `waitlist` — `id`, `email` (stored lowercased, unique), `parent_phone` CHECK-constrained to `('iphone','android','unsure')` (structure 39: preconditions are CHECK constraints), `created_at` UTC server timestamp. RLS enabled, **zero anon/authenticated policies** — only the API's service role writes, nothing reads from the client, and the structure-48 read-surface file in the webapp does not change (the webapp never sees this table; a test asserts it stays absent). `POST /waitlist`: validates email shape, discards honeypot submissions with a 200, upserts idempotently — duplicate email returns the same 200 and the same body as a first signup, so the endpoint cannot be used to probe who is on the list. CORS locked to `https://getkettle.com` and `https://www.getkettle.com` plus localhost dev (GTM: domains are getkettle.*; add further TLDs at deploy if the founder registered them).

## 8. Acceptance criteria

1. **Tokens & contrast.** No colour literal outside the tokens file; a test computes contrast from the tokens and asserts ink ≥7:1 and secondary text ≥4.5:1 on canvas. Dark sections are the exact inversion.
2. **No alarm colours.** No amber token exists in `site/`; `--error` appears in form-error styles and nowhere else — asserted by scanning built CSS/class usage, and verified by planting a red chip outside the form.
3. **Copy law.** The §4 bans run over `copy.ts` and the rendered DOM (including alt/aria); the allowlist is pinned literals; the ban side derives from shared vocabulary where possible. Plants, each verified caught then reverted: an urgency word, a `!` CTA, a person-status verdict, a person-status eyebrow, an app name inside activity narration, and a three-fields claim that drifts from `who · signal · when`.
4. **Digits.** DOM digit walk passes with only the pinned allowlist (price, step numerals); plants for a clock time in a mockup timestamp and a count of her activity both fail.
5. **Gradients & panel structure.** Tint constants match §2 exactly (geometry, corner anchoring, alpha bounds, `transparent` terminal stop, one template four tint-sets). Panel structure — amended per the ruling on DECISIONS 80, whose purpose is that the `off` panel must never be escalated: morning≡afternoon and off≡seen structurally, one class list across all four, and `off` adds nothing structural beyond the notification slot that `seen` also carries. An always-rendered empty slot on all four is explicitly not required.
6. **Tab grammar.** Active/inactive states match §3.2's measured set; 300ms opacity ease on tabs; no transition on the panel; tabs are keyboard-operable with `tablist`/`tab`/`tabpanel` roles and a visible focus ring.
7. **Motion.** Every animation sits behind `motion-safe:`; `prefers-reduced-motion` yields a fully static page; hovers are colour-only — planted `hover:scale` and a non-gated entry animation both fail.
8. **Self-containment.** `dist/` contains no foreign-origin reference; fonts are self-hosted woff2; no third-party script or beacon of any kind.
9. **No-JS readability.** Built HTML contains the full copy; the four scenario panels stack in order without script; the form degrades to a plain POST.
10. **Serif discipline.** The serif renders only in the three permitted slots (emphasis phrase, pull-quote, card reassurance sentence), never in body/buttons/chrome, never on two consecutive elements — asserted at component level.
11. **Notification component.** Proportion constants (≈4.2:1, ~2px stroke, 2% radius, 13.5% icon at 8% icon radius, single-line body, `Today` timestamp) live in one place and are tested; fill is transparent.
12. **Copy shape.** H2s 3–5 words, H1 ≤7, paragraphs ≤23 words — tested over `copy.ts`.
13. **Waitlist backend.** Migration 0009 as §7; RLS deny-by-default proven by a test that attempts an anon read and insert; duplicate signup indistinguishable from first; honeypot discarded with 200; webapp read-surface untouched and asserted.
14. **Suites.** `site/` ci green, product suite green (with Postgres up — not the false-green skip), `ruff` clean, README updated with the site build/deploy note, no secrets in the diff. Every guardrail test above verified by planting its regression and reverting (house norm).

## 9. Explicitly not decided here

Final photography (commission after the optional Gemini cross-check of the five concepts); privacy-policy legal text (founder + counsel — placeholder page ships); hosting/DNS (founder); the final H1 phrasing (draft ships; founder swaps when the one-liner is settled); Phone Watch tier presence on this page (post-beta, own spec).

## 10. Amendment A — universal English, both parents (founder site review, 2026-08-02)

Two founder rulings from reviewing the built page, now law in `docs/design-language.md` §8/§9: **the words are universal, the personas balance**. Marketing copy carries no romanized kinship terms or culture-coded vocabulary; the page shows both parents; the imagery brief is re-cast broadly (photography change is a commissioning matter — only alt text changes in code).

**Exact string changes in `site/src/copy.ts`** (ripple into pinned allowlists, MUST_RENDER prerender list, and any test asserting these literals):

1. Hero sub: `Kettle notices when your parents' ordinary phone routine doesn't happen — and asks them first, before anyone worries.` (plural parents, `asks them first`).
2. Morning lead: `By the time her coffee went cold she'd called her sister, read the news, and lost an argument with the crossword.`
3. *What you see* notification body: `Dad's day started normally.` (the page's persona balance: scenarios follow her, the sample digest names Dad — deliberate, do not "fix" to match).
4. All five image-slot alt texts re-written per design-language §9's re-cast concepts (universal English, agency intact): 1 `Grandmother mid-laugh on a slightly crooked video call, a steaming cup beside her phone, crossword and reading glasses in frame.` · 2 `A father back from the market, bags in one hand, his daughter's voice note playing from the phone in the other.` · 3 `A mother tending an unruly balcony garden while her son, in another city, exhales at a simple notification.` · 4 `Grandparents teaching a granddaughter a family recipe over a propped-up tablet, flour on the counter.` · 5 `An older woman at dance rehearsal, phone resting on the piano, her daughter watching from another city.`
5. Sweep every remaining string (including the privacy page) for the banned group below — the test, not memory, is the completeness check.

**Copy-law extension:** a new banned group `CULTURE_CODED`, case-insensitive: `amma`, `appa`, `chai`, `paati`, `thatha`, `nani`, `dadi`, `ajji`. (Deliberately excludes `beta` — a future "beta" product mention must not fight the ban.) No allowlist entries; nothing on the page may use these.

**Acceptance:** all §8 ACs still green after the ripple; the new ban verified by planting `Amma` in a heading and watching it fail; the *seen*-panel test asserts the `Dad's` string; prerender list updated; no structural or token change anywhere — this amendment is strings and tests only.

## 11. Amendment B — the kettle story (founder direction after launch, 2026-08-02)

The name gets its origin told. One new section plus one hero line; everything else untouched.

**11.1 Hero sub gains a second sentence.** After the existing sub: `No new devices — only the phone they already have.` (Both sentences render as one sub block; MUST_RENDER updated.)

**11.2 New section between the scenario tabs (§3.2) and the three fields (§3.3)** — deliberately placed so the story hands off to the privacy centrepiece: kettle → phone → three fields. Canvas ground, no gradient wash, standard entry motion, one idea per viewport. Structure: eyebrow + H2 + three short paragraphs, serif budget spent once. Strings:

- Eyebrow: `WHY THE NAME`
- H2: `Named after a kettle.`
- Para 1: `In Japan, a tea kettle once told faraway families that their parents had started the day as usual.`
- Para 2: `The idea was gentle — `*`notice the ordinary, and say so.`*` Kettle does the same with the phone your parents already own.` (the italic span is the section's serif phrase, per design-language §3)
- Para 3: `Nothing to install in their home. Nothing to wear, nothing to charge, nothing to learn.`

The story stays anonymous by design — no company or product named (a real service inspired it; marketing doesn't borrow its trademark). The founder's "before alerting family" framing is deliberately *not* added anywhere: `alert` is banned on this surface, and the senior-first mechanism is already the off-panel's copy — the story section must not restate it.

**11.3 Item-85 debt comes due in this build** (it touches `site/` mechanisms, per the PM ruling on 85): the prerender check asserts `index.html`'s meta description equals `HERO_BODY` structurally rather than by duplicated string.

**Acceptance:** all §8 ACs green after the change; the new section passes copy shape (H2 4 words, paragraphs ≤23), the serif-slot test, and the full ban set; prerender list includes the five new strings and the meta≡HERO_BODY tie; section order asserted (scenarios → kettle story → three fields); no token, tab, backend, or form change.
