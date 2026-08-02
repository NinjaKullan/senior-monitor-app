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

**DECIDED (PM rulings 74–76, Aug 2026 — ruling 74).** No commercial licences pre-revenue. Oura's
Akkurat LL and PP Editorial New are both paid; we adopt the *pairing pattern*, not the faces. Kettle
ships **Fraunces** (editorial serif — free, true italics, real weight range) and **Instrument Sans**
(workhorse sans — true semibold; Oura faux-bolds its CTAs from a 400 file and we will not). Google
Fonts, **self-hosted at build**, no runtime third-party requests (law #4).

**Serif scarcity is the rule.** In the measured corpus the serif appears a few dozen times against
hundreds of text nodes: an italic phrase inside a sans sentence (34 `<em class="font-serif italic">`
instances), large statistics, pull-quotes, a few display headings. Kettle's serif is permitted in
three places — the emotional phrase inside an otherwise plain sans sentence, a pull-quote, and a
card's reassurance sentence. Never body, buttons, UI chrome, or two consecutive elements.

**The scale is bimodal: big and quiet, or small and firm.** Display gets *lighter* as it grows, bold is reserved for small text, tracking tightens with size, body never varies.

| Role | Size ladder (px) | Family / weight | Leading | Tracking |
|---|---|---|---|---|
| Section display | 36 → 48 → 64 | sans 300 | 1.25 | −0.03em |
| Card title | 24 → 28 → 32 | sans 300 | 1.05 | 0 |
| Lead paragraph | 18–20 | sans 400 | 1.5 | 0 |
| Body | **16** (Oura's 14 is too small — read at arm's length at 6am) | sans 400 | 1.5 | 0 |
| Feature title / button | 18 | sans **600, true semibold** | 1.5 | 0 |
| Eyebrow | 13 | sans 400, uppercase | 1.5 | +0.05em |
| Serif emphasis phrase | inherits its sentence | serif 300 *italic* | inherits | inherits |
| Pull-quote | 30 | serif 200–300 | 1.5 | 0 |

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
miss," no exclamation CTAs; CTA labels are one or two flat words. This extends the product's existing
copy-law tests to marketing: the same banned-vocabulary and no-diagnosis assertions that guard digest
text apply to landing-page copy, and the landing-page spec wires them up rather than inventing a
second standard.

## 9 Imagery brief

**The register:** Oura's grading and light pointed at the people the category photographs, shown
alive and mid-moment. Grading fragments: warm side light, earthy grade, lifted blacks, shallow
domestic haze. Casting changes completely — elders in Chennai and their adult children abroad. Warm
and low-key tips from calm to elegiac fast when a subject is alone and still, so every frame moves.

**Banned clichés** (category audit — none of these, in any variation): toothpaste-ad senior smiles;
scrubs-as-competence caregiver leaning in; helper/recipient body hierarchy (young acts, old
receives); window-forlorn loneliness staging; hands-clutching-old-photo memory shorthand; sanitized
knitwear perfection with no real life visible; the facility / real-estate / insurance visual register
(badges, calculators, building exteriors). **The principle:** *agency imagery sells the aspiration,
passivity sells the need.* Kettle only ever sells the aspiration.

**Five commissioned concepts:**

1. Grandmother mid-laugh on a slightly crooked video call, chai steaming beside her phone, crossword
   and reading glasses messily in frame.
2. A 68-year-old father returning from the market on his scooter, helmet under one arm, daughter's
   voice note playing from the handlebar phone.
3. Mother tending an unruly balcony garden in Chennai while her adult son in Brooklyn exhales at a
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
