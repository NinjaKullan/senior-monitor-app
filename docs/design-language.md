# Kettle design language

*Working reference for the landing page and app polish. Decided items cite their ruling; the rest is
guidance until the landing-page spec locks it. Unmeasured values say **TBD at spec time** rather than
guessing.*

## 1 Purpose & sources

The single place the landing page, the child PWA and any future marketing surface take type, colour,
motion, component and imagery rules from. Three research inputs: the measured CSS/asset extraction of
ouraring.com (`docs/oura-design-analysis.md` — compiled Tailwind `@theme` block plus seven
pixel-measured assets); the rendered-page pass (`docs/oura_visual_pattern_analysis_openai.md`) for
the scenario-tab active state, hover timing, serif scarcity and the absence of alert states on
marketing; and `docs/eldercare_category_imagery_audit.md`, source of the banned-cliché list in §9.

## 2 Brand stance

Kettle is calm, plain and adult. It sells the aspiration — an ordinary week in which everyone is fine
— never the need. Distance is an ordinary family fact, not abandonment. The parent owns the agency in
every frame and every sentence; the payoff emotion belongs to the adult child, and it is quiet
relief, not rescue. Nothing here may describe a person's state: the product cannot know it (product
law #1), and a household-grade signal never speaks for a human being (law #6).

## 3 Typography

**DECIDED (PM ruling, founder-endorsed, DECISIONS 135 — supersedes the two-face pairing of rulings
74–76).** Two independent reviewers of the live site read the page as mix-and-matched, and they were
right: a second face carried emphasis, seven sizes were in play, and a weight class was being written
that the font file could not serve. The page speaks in **one voice**.

**One typeface: Instrument Sans**, self-hosted at build (Google Fonts, no runtime third-party
request — law #4). Fraunces is retired along with the role it existed for. Reference point for the
discipline, chosen by the founder: headspace.com — one face everywhere, hierarchy from size and
weight, warmth from colour, and a handful of sizes on the whole page.

**Hierarchy comes from size and weight. Warmth comes from colour.** Nothing else is a hierarchy
tool: no second face, no italics, no letter-spacing tricks, no all-caps outside the eyebrow.

**Five roles, each with one job.** If a size would be used by exactly one element, it merges into its
neighbour instead of becoming a sixth role. A new size is an amendment to this section, not a
decision to be made inside a `className`.

| Role | Size | Weight | Leading | Tracking | Its one job |
|---|---|---|---|---|---|
| Display | 48 | 400 | 1.15 | −0.03em | The page's single `h1`. Nothing else. |
| Heading | 32 | 400 | 1.2 | −0.02em | Every section `h2`. |
| Lead | 20 | 400, or 500 for a sub-head | 1.5 | 0 | Opening paragraphs, panel headlines, the emphasis line. |
| Body | **16** (14 is too small — read at arm's length at 6am) | 400, or 600 for buttons and labels | 1.5 | 0 | Everything else, including buttons. |
| Eyebrow | 13 | 400, uppercase | 1.5 | +0.05em | Section eyebrows and timestamps. |

**Three weights, and all three are real files: 400, 500, 600.** Instrument Sans has no 300; `font-light`
was written across every heading for months while the browser quietly served 400, so the type law's
old "display gets lighter as it grows" was describing something that never rendered. The reference
faux-bolds its CTAs from a 400 file; we ship a true 600. Neither mistake is available here — a weight
the stylesheet does not load may not be named.

**Emphasis is a whole sentence, or it is nothing.** It is expressed by weight (500) or by the accent
colour, and only ever on a complete sentence that stands on its own. An italic fragment spliced into
someone else's sentence — the old serif role — is banned, and so are `<em>`, `<i>`, `<b>` and
`<strong>` anywhere in the page's prose. The page currently spends this once, on the three-fields
section's closing line.

*Enforced, not merely written down:* the rendered page is scanned for a second face, for italics, for
inline emphasis elements, for any `text-` size outside the five, and for any weight class outside the
three — and each of those five regressions is planted in the test suite and required to fail.

## 4 Colour

**DECIDED (ruling 76).** Adopt Oura's *strategy* — warm low-contrast ground, no red in the status
vocabulary, time-of-day tinting — and re-choose every value around Kettle's existing green. **We ship
no Oura hex verbatim except generic neutrals.** The trade-dress line sits at *palette as a system*:
warm neutrals are common property; `#F7F1E8`/`#4A4741` as a pair is theirs.

| Role | Rule | Value |
|---|---|---|
| Warm canvas | near their measured ground (~`#F7F1E8`), deliberately not identical | TBD at spec time; candidates `#F6F2EC`, `#F4F1E9` |
| Warm ink | warm dark, R>G>B, never true black | TBD at spec time; candidate `#403C36` |
| Primary accent | **Kettle green stays primary** — the webapp's `--calm` | `hsl(158 50% 32%)` (existing, `webapp/src/index.css`) |
| Secondary warmth | soft clay; grounds and warm accents only | TBD at spec time |
| Secondary text | must clear 4.5:1 on canvas | TBD at spec time |
| Amber | **equipment only** — a device stopped reporting, never a person | `hsl(32 70% 38%)` (existing `--attention`, 005d rule) |
| Red | **form errors only** — never a status, never a person, never marketing | TBD at spec time |

Light sections are canvas-on-ink; dark sections invert exactly. No true white background, no true
black body text; high contrast used sparingly and on purpose. **Marketing carries zero alert states
and zero alarm colours** — the rendered-page pass found none on Oura, and we have less licence, not more.

## 5 Gradients & the time-of-day mechanic

Not a background image: 3–4 absolutely positioned divs over a **flat warm ground**, each with one
radial gradient anchored to a corner, each fading to `transparent` well before the centre. The
measured morning geometry (§4.1):

```
ellipse at 0%/0% → transparent 20% · circle 99%/0% → 30% · circle 10%/90% → 50% · circle 99%/99% → 40%
```

Their tints on it — `rgba(245,190,141,0.4)`, `rgba(251,206,151,0.5)`, `rgba(253,195,130,0.5)`,
`rgba(245,190,141,0.5)` warm; one `rgba(123,135,146,0.5)` midday; `rgba(60,91,98,0.5)` night — are
**reference, not our values**. One template re-tinted is the mechanism we take; Kettle's tints are
re-chosen around green and clay, TBD at spec time. Invariants: anchored at edges and corners, never
centred on content; alpha 0.3–0.7; always fading to `transparent`, never to another colour.

The template drives two surfaces. On the landing page it tints the scenario tabs — *Her morning*
warm, *Her afternoon* neutral, *When something's off* cooler but **never red**, *What you see*
neutral. In the app it tints the day-arc: morning and evening views of one screen differ by tint
alone, never by structure.

## 6 Motion

| Property | Value |
|---|---|
| Entry | fade + **10–30px rise**, **0.8–1.2s** |
| Button hover | **colour-only shift, ~150ms** — no elevation, no transform, no hue change |
| Tab switch | 300ms opacity ease on the tab; **panel swaps instantly** |
| Rhythm | **one idea per viewport**; beats ~700–1,100px apart |
| Reduced motion | every entry animation degrades to a static element under `prefers-reduced-motion` |

**v1 refuses scroll-scrubbed pinning.** Oura's sticky-pane choreography is the one thing the fetch
could not see, it is expensive to tune, and plain fades are cheaper and calmer.

**The first scripted exception (PM, 2026-08-17 — DECISIONS 132).** Motion on the page is entry fade
and rise, once, and nothing else — with one scripted exception, the Rhythm Field. The field earns
motion no other element gets because it depicts the product's one story and nothing beyond it:
signals arriving, and a quiet morning asked about, parent first. The exception is conditional and
the conditions are the law: it draws no words where it decorates the hero, implies no learning and
no verdicts, hides itself from assistive technology, pauses when unseen, stands down to a designed
still when the visitor asks for reduced motion, and the page must remain whole without it. A second
animated element is not covered by this exception; it is a new argument, to be made here first.

**The exception's one interactive extension (founder request — DECISIONS 135).** Everything above is
motion the page performs at the visitor. The three-fields band may also *respond*: with a desktop
pointer, dust within a modest reach is displaced away from the cursor and eases back to its orbit
when the cursor leaves. Disturb and recover, and nothing else — no trails, no colour change, no
effect on the orbit rings or the three words. The conditions are again the law: the listener is
passive and the canvas keeps `pointer-events: none`, so nothing can intercept a click or a scroll; a
touch device attaches no listener at all; and a reduced-motion viewer gets the designed still,
undisturbed. This extension covers the dust and only the dust. Any other element that answers the
pointer is a new argument, to be made here first.

**The third animated element (PM, 2026-08-27 — DECISIONS 187).** The two exceptions above are one
canvas; this one is a picture. A small kettle sits above the hero kicker and steams — placement
Option A of three wireframed, chosen because it is the only one that adds the heartbeat without
moving anything: the copy block, the CTA and the hero illustration are exactly where they were, and
the kettle reads as a wordmark that happens to be alive rather than as a second picture arguing with
the first. The argument for it is that the product is named after an object, and a marketing page
that shows that object once, quietly, is saying its own name.

The conditions are again the law. It carries no words and no meaning: empty alt, the steam layers
`aria-hidden`, nothing about anyone's day. It cannot be interacted with (`pointer-events: none`) and
answers no pointer — the three-fields extension covers the dust and only the dust. It stands down
to a designed still under `prefers-reduced-motion` — one faint wisp at the spout, going nowhere —
and every keyframe and animation declaration lives inside the `no-preference` block, which is what
`motion-safe:` compiles to and what hand-written component CSS has to do by hand.

And one rule that is specific to a drawn element rather than to motion in general: **the steam's
geometry is a property of the kettle, never of the page.** Every offset, size, blur radius and
keyframe travel is a multiple of one container-relative unit, so the steam is the same fraction of
the pot at any render size. The mockups expressed the same geometry in pixels calibrated for a
420px kettle; at the mark's real size those pixels are not smaller steam, they are the same steam on
a third of the kettle — wisps a quarter of the pot wide, travel one and a half kettle-widths high,
drifting off the left edge. A bare `px` in that stylesheet is that bug returning, and the suite
refuses one. A fourth animated element is a new argument, to be made here first.

## 7 Component grammar

- **CTAs are full pills**, 12/24 padding, sans at **true semibold**; hover is a colour shift only. No
  rectangles, no small radii on anything interactive.
- **Radii ladder:** 8px content/photo cards · 24px glass chips and media tiles · 40px feature panels
  · full pill for anything clickable.
- **Cards** separate by *background change*, not shadow; shadows near-absent and soft when present.
  Padding 24; gaps 8 inside a text block, 24 between cards, 40 between rows.
- **Scenario tabs** (measured): active = regular weight, black text, full opacity, **3px black bottom
  border**; inactive = **0.7 opacity, transparent border**; 300ms opacity ease. No fill, no colour
  change, no weight change between states.
- **Notification mockup is a component, not an asset.** Oura ships a flat PNG; we rebuild at the
  measured proportions (§6.5): **≈4.2:1** card, **transparent fill** so the photograph shows through,
  ~2px stroke, radius ≈2% of card width, app icon **13.5% of width** at ~8% icon radius, one
  single-line body sentence, timestamp right-aligned. Stroke and icon colours are ours, TBD at spec time.
- **Eyebrow rule — DECIDED (ruling 75).** The small-caps eyebrow labels **sections and scenarios
  only**. `HER MORNING` is fine; a person-status eyebrow in the `DAYTIME STRESS` / `PAY ATTENTION`
  mould is refused under law #1. The typographic form travels; the semantic does not.
- **Refused components:** scores, numerals-as-verdicts, charts, sparklines, timelines, readiness
  rings. Kettle's version of "the number" is a phrase.

## 8 Copy voice

Headings run **3–5 words**; paragraphs run **~20 words**; almost nothing sits in between or above 23.
**`you`/`your` dominate**, "we" is near-absent — the company is not a character in its own copy.
Describe in the past tense; name the moment, not the gap; let the serif phrase carry the feeling
while the sans states the fact. **No urgency vocabulary, ever** — no "now," no "hurry," no "don't
miss," no exclamation CTAs; CTA labels are one or two flat words.

**Universal English (founder ruling, Aug 2).** Marketing copy carries no romanized kinship terms and
no culture-coded vocabulary — no `Amma`, `Appa`, `chai`, `paati`, `thatha` or kin. The audience is
English-fluent and broader than any one culture; a word a reader can't parse costs more than it
earns, and the photography (§9) carries the specificity instead. Personas balance across the page:
scenarios may follow one vivid parent, but the page as a whole shows both — the hero speaks of
parents, plural, and the sample digest names Dad. Enforced by the copy-law ban list like everything
else in this section. This extends the product's existing
copy-law tests to marketing: the same banned-vocabulary and no-diagnosis assertions that guard digest
text apply to landing-page copy, and the landing-page spec wires them up rather than inventing a
second standard.

## 9 Imagery brief

**The register:** Oura's grading and light pointed at the people the category photographs, shown
alive and mid-moment. Grading fragments: warm side light, earthy grade, lifted blacks, shallow
domestic haze. Casting changes completely — elders with real lives and their adult children in other
cities, **cast broadly across the families the product serves, never coded to a single culture**
(founder ruling, Aug 2, alongside the universal-English copy rule in §8: warmth is carried by light
and moment, not by cultural props). Warm and low-key tips from calm to elegiac fast when a subject
is alone and still, so every frame moves.

**Banned clichés** (category audit — none of these, in any variation): toothpaste-ad senior smiles;
scrubs-as-competence caregiver leaning in; helper/recipient body hierarchy (young acts, old
receives); window-forlorn loneliness staging; hands-clutching-old-photo memory shorthand; sanitized
knitwear perfection with no real life visible; the facility / real-estate / insurance visual register
(badges, calculators, building exteriors). **The principle:** *agency imagery sells the aspiration,
passivity sells the need.* Kettle only ever sells the aspiration.

**Five commissioned concepts:**

1. Grandmother mid-laugh on a slightly crooked video call, a steaming cup beside her phone,
   crossword and reading glasses messily in frame.
2. A 68-year-old father returning from the market, bags in one hand, his daughter's voice note
   playing from the phone in the other.
3. Mother tending an unruly balcony garden while her adult son in another city exhales at a
   simple notification — distance present, anxiety absent.
4. Grandparents teaching a granddaughter a family recipe over a propped-up tablet, flour on the
   counter, everyone imperfectly framed.
5. An older woman at neighborhood dance rehearsal, phone resting on the piano, her daughter watching
   from another city — mother owns the action, daughter gets the relief.

## 10 Adopt / Adapt / Refuse

| Item | Call | Why |
|---|---|---|
| Serif scarcity (italic phrase inside a sans sentence) | **ADOPT** | The power is entirely in the scarcity; the discipline is the asset, not the face |
| Weight/size inversion (large = light, small = bold) | **ADOPT** | Structural, free, reads as considered |
| Copy: bimodal lengths, second person, no urgency vocabulary | **ADOPT** | Measured, and already product law in the digest copy tests |
| No-red status vocabulary | **ADOPT** | The most transferable colour decision on the site |
| Corner-wash gradient mechanic + time-of-day tinting | **ADAPT** | Geometry and alpha carry, tints re-chosen around Kettle green; drives scenario tabs and the app day-arc |
| Typeface pairing pattern | **ADAPT** | Pattern adopted, faces re-chosen — Fraunces + Instrument Sans (74) |
| Status-eyebrow typographic form | **ADAPT** | Sections and scenarios only; person-status wording refused (75) |
| Notification mockup | **ADAPT** | Rebuilt as a component at their measured proportions, our colours |
| Scores, charts, timelines, readiness numerals | **REFUSE** | Law #1 — a score is a diagnosis in a party dress |
| Scroll-scrubbed sticky pinning | **REFUSE (v1)** | Unseen by the research, expensive, and plain fades are calmer |
| Alert states / alarm colours on marketing | **REFUSE (always)** | Zero found on Oura's marketing; we have less licence, not more |
| Oura's palette as a pair, their layout, photography, sentences | **REFUSE** | Trade-dress line: palette as a system, not a set of hexes |

## 11 Open items

- **Final hex values** for canvas, ink, clay, secondary text and the gradient tints lock when the
  landing-page spec lands; secondary text must be verified at ≥4.5:1 on canvas.
- **Founder screenshots (optional)** would close `docs/oura-design-analysis.md` §10 items 1, 2 and 4
  — scroll choreography, the scenario-tab state set, the unlocated warm gradient pair. None block
  this document, and item 2 is now largely answered by the rendered-page pass recorded in §7.
- **Gemini cross-check (optional)** on the imagery brief before commissioning — a second read on
  whether the five concepts dodge the banned-cliché list in practice, not just in intent.
