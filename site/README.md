# Kettle — landing page (getkettle.*)

Spec `specs/006-landing-page.md`. One static page whose job is to collect a
waitlist and ask the question that decides Wave 2 platform priority with data
rather than instinct: *what phone does your parent use?*

`docs/design-language.md` is the law of this surface. This README says what the
build enforces; the reasoning lives there and in the spec.

## What the tests hold

Marketing is where a company says what it is, and a promise made here that the
product cannot keep is worse than the same sentence in a digest — a stranger
reads this one *before* deciding to trust anything. So the product's copy-law
tests were extended here rather than a second standard invented, and they land
stricter.

| Rule | Enforced by |
|---|---|
| Every colour in one file; ink ≥7:1 and secondary ≥4.5:1 on canvas | `tokens.test.ts` computes the ratios from `tokens.css` |
| No amber token exists; `--error` only inside the waitlist form | `tokens.test.ts` names the one file allowed to spend red |
| No urgency, diagnosis, medical, alarm, surveillance or person-verdict copy | `copyLaw.test.tsx`, over `copy.ts` **and** the rendered DOM |
| No romanized kinship or culture-coded vocabulary | `copyLaw.test.tsx`'s `CULTURE_CODED`, scanned unmasked so no allowlist can reach it |
| App names only in the mechanism steps, never narrating her day | `copyLaw.test.tsx` |
| Only digits: the price and the three step numerals | DOM digit walk, attributes included |
| Four panels differ by tint and content, never by structure | `scenarios.test.tsx` compares DOM skeletons |
| Every animation behind `motion-safe:`; hovers colour-only | `motion.test.tsx`, scanned off the rendered DOM |
| Serif only in its three slots, never twice in a row | `motion.test.tsx` |
| Notification proportions live in one place | `motion.test.tsx` against `lib/notification.ts` |
| No foreign origin in `dist/` | `scripts/check-foreign-origins.mjs`, in `npm run ci` |
| The page reads with JavaScript off | `scripts/check-prerender.mjs`, in `npm run ci` |
| The meta description never drifts from `HERO_BODY` | `scripts/check-prerender.mjs` compares them structurally |
| Sections stay in argument order (scenarios → story → three fields) | `story.test.tsx`, rendered and static |

Every one of those was verified by planting the regression it exists to catch —
an urgency word, a `!` CTA, a person-status verdict, an app name inside a
scenario, a drifted three-fields claim, a clock time in a notification, a
`hover:scale`, an ungated entry animation, a red chip outside the form, a serif
on a second consecutive element, a kinship term in a heading, a reordered
section, a second serif, a drifted meta description — and watching it fail
before reverting.

**Universal English, and both parents** (Amendment A, founder site review). The
copy carries no romanized kinship terms and no culture-coded vocabulary: the
audience is English-fluent and broader than any one culture, a word a reader
cannot parse costs more than it earns, and the photography carries the
specificity instead. `CULTURE_CODED` enforces it, and it is the one ban here
scanned against the *unmasked* string — "no allowlist entries" means the
exemption is unreachable, not merely empty. `beta` is deliberately excluded so a
future beta mention does not fight the ban.

The hero speaks of parents, plural; the scenarios follow one parent, because a
day needs a person in it; the sample digest names Dad. **That asymmetry is the
balance, not a mismatch** — two tests pin it so it is not tidied into a match.

**Two things that are not decoration.** There is no amber on this site because
amber is equipment vocabulary for the app ("this tripwire stopped reporting"),
and marketing carries zero alert states; the token to build one with does not
exist. And the `When something's off` tint set is asserted green-over-red on
every layer, because an alarm state drawn rather than written is the one no copy
test would ever find.

## Local development

```bash
cd site
npm install
npm run dev
```

```bash
npm run lint         # eslint
npm run test         # vitest
npm run build        # tsc --noEmit && vite build && SSR build && prerender
npm run verify:build # secrets, foreign origins, prerender
npm run ci           # all four, in the order CI runs them
```

`VITE_API_BASE_URL` points the waitlist form at an API; it defaults to
`https://kettle-api.fly.dev`. It is a public URL and the only value this page
reads from its environment — there is no key here to leak.

This surface deliberately does not have the webapp's QUESTIONS-114 gap: the
site is built *locally* (`npm run ci`) before `fly deploy` ships `dist/`, and
the default above is baked into the code, so a build with no env var still
points at the production API rather than at an empty string. There is no
`[build.args]` to forget because the Fly image never builds the bundle.

## Deploy

`dist/` is a folder of static files, built and verified locally (`npm run ci`)
before `fly deploy` ships it. The image serves it with nginx under the
QUESTIONS 112 caching contract (`nginx.conf`, asserted by
`product/tests/test_site_caching.py`): the shell, the photographs and
privacy.html revalidate on every visit (`no-cache` — unchanged files are
304s), hashed `/assets/` are immutable for a year. Any other static host works
too, but it must honour that split — the photographs live at stable names, so
a host that invents a cache lifetime pins old imagery to returning visitors.

```bash
cd site
VITE_API_BASE_URL="https://kettle-api.fly.dev" npm run ci   # builds dist/
```

Then, on the founder's side:

1. Point `getkettle.com` and `www.getkettle.com` at the host serving `dist/`.
2. If the API moves, or another TLD is registered, set `WAITLIST_ORIGINS` on
   kettle-api to the comma-separated list of origins allowed to POST. The
   default already covers `getkettle.com`, `www.getkettle.com` and the Vite dev
   server.
3. Apply migration `0009_waitlist.sql`.

`/privacy.html` ships as a placeholder with the product's own privacy sentence
in it. The full policy is founder + counsel; the page exists so the footer link
never points at a 404.

## What is deliberately not here

No Phone Watch tier (post-beta, and its device/person language deserves its own
spec). No checkout, no billing, no blog. **No analytics of any kind, ever** —
not even self-hosted page counters; law #4 has no exception for the
privacy-friendly sort, and the foreign-origin scan makes that mechanical rather
than aspirational. No A/B tooling. No confirmation email — there is no email
infrastructure, and the success state is the confirmation. No scroll-scrubbed
pinning (design-language §6 refuses it for v1). No stock photography: the image
slots ship as flat warm blocks with the final alt text already written, because
the category's banned-cliché list makes stock a liability rather than a shortcut.
