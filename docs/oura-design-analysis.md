# Oura design analysis — tokens for adaptation

*Implementer research, 2026-08-02. Input to the landing-page spec. Commissioned by
the founder's "Design language decision" (`docs/gtm-roadmap.md`, Aug 1): Oura's
**register** is adopted — warm gradient palettes, editorial serif for human
moments, scenario-tab storytelling, calm authority of tone. Oura's **instrument
panel is refused** — no scores, no charts, no graphs.*

## Adaptation boundary (read before using anything below)

This document extracts *how the system is built*: type ratios, spacing units,
component mechanics, tonal rules. Those are patterns, and patterns are ours to
learn from.

What is **not** ours: their exact palette as a set, their layout, their
photography, their sentences, their marks. Every number below is evidence of a
method, not a value to paste. §11 says, row by row, which ones carry across as
structure and which must be re-chosen so Kettle looks like Kettle. Short quoted
fragments appear only where the voice analysis needs a specimen; they are Oura's
words and none of them may be reused as Kettle copy.

Two hard product constraints override anything attractive in here:

- **Product law #1** — no decline/diagnostic detection or claims. Oura's status
  eyebrows (`PAY ATTENTION`, `STRESSFUL DAY`) are *judgements of a person's
  state*. The typographic form is adaptable; the semantic is not.
- **Product law #6** — a household event never proves a person is fine. Nothing
  in their reassurance grammar may be borrowed in a way that attributes a
  device-grade signal to a human being.

---

## §0 Method, and what "I saw this" means here

Fetched 2026-08-02 with `curl` (desktop UA), raw bytes, no JS execution:

| URL | Bytes | SSR text (scripts stripped) |
|---|---|---|
| `https://ouraring.com/` (home) | 1,440,117 | ~3.1 KB |
| `https://ouraring.com/store/rings/oura-ring-5` (product) | 1,450,320 | ~6.3 KB |
| `https://ouraring.com/why-oura` (editorial) | 1,450,615 | ~4.1 KB |
| `https://ouraring.com/how-it-works` (editorial / scenario) | 1,330,199 | ~2.0 KB |
| `https://ouraring.com/membership`, `/sleep-and-rest` | — | probed only, for §4 gap-hunting |

All four pages reference **one** stylesheet:
`/b/a/ecom-website/v1.118.0/_next/static/css/fddafce3ec3b16c1.css` (217,667
bytes), fetched directly. It is a compiled **Tailwind v4** build, so the
`@theme` block at the top *is* their design-token file, verbatim. That is the
single most valuable artifact here and it is not an inference.

The site is Next.js App Router. The pages *are* server-rendered — the DOM is
present in the bytes — but most of the page also exists a second time inside
the RSC flight payload. Both were parsed. Where a value below is a hex, a rem,
or a class name, it was read out of the CSS or out of rendered markup. Where it
is a judgement ("reads as calm"), it is labelled as one.

Seven image assets were downloaded from their imgix CDN and measured
pixel-by-pixel (Pillow, in a scratch venv) — that is the source of the
notification-mockup geometry in §6.5 and the colour-grading numbers in §9. Those
are measurements, not impressions.

**What no fetch can give**: scroll choreography, hover states as rendered, and
anything whose final look depends on compositing a PNG over a photo. §10 lists
exactly what still needs founder screenshots and why.

---

## §1 Fonts — the sans/serif split

Five `@font-face` declarations, all self-hosted `.woff2` from
`/assets/fonts/`, declared in an inline `<style>` in `<head>` (not in the
stylesheet):

| Family | Weight | Style | File |
|---|---|---|---|
| `AkkuratLL` | 400 | normal | `AkkuratLL-Regular.woff2` |
| `AkkuratLL` | 300 | normal | `AkkuratLL-Light.woff2` |
| `Editorial New` | 300 | normal | `PPEditorialNew-Light.woff2` |
| `Editorial New` | 200 | normal | `PPEditorialNew-Ultralight.woff2` |
| `Editorial New` | 200 | *italic* | `PPEditorialNew-UltralightItalic.woff2` |

Stacks: `--font-sans: "AkkuratLL"`, `--font-serif: "Editorial New"`,
`--default-font-family: "AkkuratLL", sans-serif`. Body copy is sans by default;
serif is opt-in per element.

Both are commercial licences — Akkurat LL is Lineto, PP Editorial New is Pangram
Pangram. Kettle cannot use either without buying them (**DECISIONS 74**).

### Two loading facts worth not repeating

- **There is no bold Akkurat face.** Only 300 and 400 are declared, yet
  `font-bold` (700) is applied to every CTA and every feature title. With
  `font-family: AkkuratLL, sans-serif`, the browser synthesises faux-bold from
  the 400 file rather than falling through to the system sans. Whatever Kettle
  picks, load a *real* medium/semibold.
- **`font-thin` (100) is used on the big serif numerals**, but the lightest
  declared Editorial New face is 200. Those numerals render as Ultralight 200.
  So the *intended* display weight is 200, not 100.

### Where each family is actually used

Counted across all four pages. The split is **not** "serif for headings" — it is
much more disciplined than that:

| Serif is used for | Evidence |
|---|---|
| **An italic phrase inside a sans headline** — the single most characteristic move on the site | 34 instances of `<em class="font-serif italic">` nested in sans `<h*>`/`<p>`; e.g. the sans line "Oura Membership gives your body" with `a voice` set in serif italic |
| **Large statistics** | `font-serif font-thin text-heading-2xl` on `99%`, `98%`; `font-extralight` variants at `lg:text-heading-5xl` |
| **Pull-quote testimonials** | `font-serif font-thin text-3xl leading-normal` |
| **A handful of display H1/H2** | product hero; two section headers on the product page at `lg:text-[6.125rem]` |
| **The newsletter heading in the footer** | `font-serif font-light text-heading-base` |

Everything else — all body copy, all eyebrows, most section headings, every
button, every card title, every metric label — is **sans**. The serif appears a
few dozen times on a page with hundreds of text nodes. Its power is entirely in
its scarcity.

**Pattern for Kettle**: reserve the serif for the human moment inside an
otherwise plain sentence, and for numbers-as-objects. Never for UI chrome, never
for body text, never for two consecutive elements.

---

## §2 Type scale — actual values

Read from the compiled `@theme` block. Root is 16px, so rem×16 = px.

### The semantic scale (their own tokens)

| Token | rem | px | Observed use |
|---|---|---|---|
| `--text-eyebrow` | 0.75 | **12** | category chips over photos, footer legal, footnotes |
| `--text-body-sm` | 0.875 | **14** | default body paragraph (23 instances, the most-used text style on the site) |
| `--text-body-lg` | 1.125 | **18** | lead paragraphs, feature titles (at `font-bold`), all-caps section labels |
| `--text-heading-xs` | 1.25 | **20** | hero subhead (mobile) |
| `--text-heading-sm` | 1.5 | **24** | news-card headlines |
| `--text-heading-base` | 1.75 | **28** | card titles (mobile), scenario titles (mobile) |
| `--text-heading-lg` | 2 | **32** | card titles (md), section H3 (mobile) |
| `--text-heading-xl` | 2.5 | **40** | card titles (lg), section H2 (mobile) |
| `--text-heading-2xl` | 3 | **48** | stat numerals; product section H2 (mobile) |
| `--text-heading-3xl` | 3.5 | **56** | section H3 (lg) |
| `--text-heading-4xl` | 4 | **64** | — (declared; not observed on these four pages) |
| `--text-heading-5xl` | 4.25 | **68** | stat numerals (lg); section H3 (xxl) |
| `--text-heading-6xl` | 5 | **80** | section H2 (lg) — the workhorse display size |
| `--text-title-md` | 4.5 | **72** | — (declared; not observed here) |
| `--text-title-lg` | 6 | **96** | — (declared; `xl:text-title-lg` exists for CJK only) |
| `--text-title-xl` | 7.5 | **120** | — (declared; not observed here) |
| `--text-h1-md` | 3.25 | **52** | the md-breakpoint step for hero/section H2 |
| `--text-h2-base` | 2 | **32** | base size for the big-stat block |

Plus stock Tailwind sizes still in play: `text-3xl` 30, `text-5xl` 48,
`text-6xl` 60, `text-7xl` 72, `text-8xl` 96, `text-9xl` 128, and two arbitrary
display sizes `6.125rem` (98) and `6.875rem` (110).

> **Trap I nearly fell into:** every semantic token is defined **twice** in the
> CSS. The second set is *not* a breakpoint override — it is
> `:lang(ja),:lang(ko)`, which shrinks the whole display scale for CJK
> (`heading-6xl` 80 → 72, `title-xl` 120 → 104). The Latin scale is the first
> set, above. Responsiveness is done in markup, not in the token.

### Line-height and tracking tokens

`--leading-tighter: 1.1` · `--leading-tight: 1.25` · `--leading-snug: 1.375` ·
`--leading-normal: 1.5` · `--leading-relaxed: 1.625` · `--leading-loose: 2` ·
`leading-none: 1`.

`--tracking-tighter: -0.05em` · `--tracking-tight: -0.025em` ·
`--tracking-normal: 0` · `--tracking-wide: 0.025em` · `--tracking-wider: 0.05em`
· `--tracking-widest: 0.1em`.

(Two arbitrary values also appear on display text: `lg:tracking-[-2px]` and
`lg:tracking-[-1.12px]`.)

### The ladders, as actually composed

Each row is one real element, with its responsive steps in order. `→` is a
breakpoint (md 768 / lg 1024 / xl 1280 / xxl 1440).

| Role | Size ladder (px) | Family / weight | Leading | Tracking |
|---|---|---|---|---|
| **Home hero H1** | 48 → 72 → 96 → 110 | serif 300 | 1.1 | −0.05em |
| **Product hero H1** | 48 → 60 → 72 → 96 → 128 | serif 400 | 1.5 | −0.05em |
| **Section H2 (display)** | 40 → 52 → 80 | sans **300** | 1.25 | −0.025 / −0.05em |
| **Section H3** | 32 → 40 → 56 → 52 → 68 | sans 300 | 1.25 | −0.05em |
| **Card title** | 28 → 32 → 40 | sans 300 | **1.0** | 0 |
| **Feature title** | 18 | sans **700** | 1.5 | 0 (`mb-3` below) |
| **Body paragraph** | 14 | sans 400 | 1.5 | 0 |
| **Lead paragraph** | 18 | sans 400 | 1.5 | 0 |
| **Eyebrow / chip label** | 12 | sans 400 | 1.5 | 0 |
| **All-caps section label** | 18 | sans 700, `uppercase` | 1.5 | 0 (one instance uses `tracking-wide`) |
| **Stat numeral** | 32 → 48 → 68 | serif 200 | 1.25 | 0 → −2px |
| **Pull quote** | 30 | serif 200 | 1.5 | 0 |
| **Time marker** (`6:00 AM`) | 14 → 16 | sans 700 | 1.0 | +0.025em |

The shape of the system, stated plainly:

1. **Display text gets lighter as it gets bigger.** 80px headings are weight
   300. Nothing large is ever bold.
2. **Bold is reserved for small text** — 18px feature titles, buttons, time
   markers. Weight and size move in opposite directions.
3. **Tracking tightens as size grows** (0 at 14px, −0.05em at 48px+), which is
   the ordinary optical correction, applied consistently.
4. **Card titles sit at `leading-none`** (1.0) — two-line titles nearly touch.
   That tightness is a large part of the "considered" feel.
5. **Body copy never varies.** 14/1.5/0, everywhere.

*(Minor: several headings carry both `leading-heading` and `leading-normal`.
`.leading-heading` is not defined anywhere in the stylesheet — dead class,
`leading-normal` wins. Don't copy the mistake.)*

---

## §3 Colour palette

All hexes below are literal from the `@theme` block. Grouped by role, with usage
counts from the four pages' markup.

### Warm neutrals — the base of the whole site

| Token | Hex | What it does |
|---|---|---|
| `sandstone-100` | `#FEFAEF` | lightest cream; one `md:` background |
| `sandstone-200` | `#F7F1E8` | **the page background** (54 uses) and the light-on-dark text colour (96 uses) |
| `sandstone-300` | `#EFEAE2` | selected state of segmented controls |
| `sandstone-400` | `#EFE6DB` | rare, deeper card wash |
| `sandstone-450` | `#E6DED3` | rare |
| `sandstone-500` | `#4A4741` | **the ink** — warm dark brown-grey, the primary text colour (142 uses) and the dark section background (47 uses) |
| `cream-50` | `#F7F1E8` | duplicate of sandstone-200 under another name |
| `cream-100` | `#EEE6DC` | — |

The core move is a **two-token page**: `#F7F1E8` and `#4A4741`, swapped. Light
sections are sandstone-200 ground with sandstone-500 ink; dark sections invert
exactly. There is no true black text and no true white background anywhere in
the body — `#000`/`#fff` exist as tokens but appear only in overlays, product
photography backdrops and form fields.

`#4A4741` is the quiet protagonist: it is a *warm* dark (R>G>B), so the dark
sections read as brown-charcoal rather than as grey. That single choice is most
of the "calm authority."

### Cool neutrals (utility greys)

`gray-100 #F3F1F0` · `gray-150 #E2E1DA` · `gray-300 #D3D1CE` · `gray-350
#A8A5A0` (footer/legal text, 24 uses) · `gray-400 #838280` · `gray-450 #5A5958`
· `gray-500 #202020` · `gray-550 #19191C` · `gray-600 #1C1B1A` ·
`backdrop-500 #222428` · `backdrop-600 #151619`.

`backdrop-500/600` exist for one job: the translucent scrim behind chips and
menus (see §6.4).

### Accents

| Token | Hex | Where |
|---|---|---|
| `blue-100` | `#2A72DE` | **the only CTA fill on the site** — primary buttons |
| `blue-200` | `#2056A6` | CTA hover |
| `brown-100/500/600/700` | `#DBCDC2` `#715956` `#6B443D` `#39221E` | editorial section grounds |
| `olive-400…800` | `#849671` `#7B886D` `#5C6F5D` `#5B6550` `#224228` | `olive-700` is the testimonial byline colour |
| `mustard-50…700` | `#FFEFD8` `#DDAA61` `#DDBE78` `#BC924C` `#AF751B` `#684D07` | warm highlight family; `mustard-500` is a gradient stop |
| `slate-100…900` | `#D7E2E8` `#4F5F68` `#4B5F68` `#394A54` `#1B3449` `#1D2C38` `#1A232C` `#1E2427` | cool/night sections |
| `green-100 #E2EDD5`, `green-600 #55DC83` | | sparse |
| `red-100 #F2D0CB`, `red-600 #D22C15` | | **not used for status anywhere I saw** — form errors only |
| `orange-300 #C0865D`, `purple-600 #4A4657`, `purple-700 #3E2242` | | editorial grounds |

The accent worth stealing conceptually: **the alerting colour is not red.** In
their app cards (measured off the PNG in §6.6), the caution eyebrow is
`#D89078` — a clay/salmon — and the strongest state is `#F06898`, a pink. Red
appears nowhere in the status vocabulary. For a product whose entire promise is
*not alarming people*, that is the most transferable colour decision on the
site.

### Text colours in practice

`sandstone-500 #4A4741` (dark-on-light) · `sandstone-200 #F7F1E8`
(light-on-dark) · `gray-350 #A8A5A0` (legal/secondary) · `white/60` (form
placeholder). Inside their dark app cards the type is a **warm** off-white
(`#F0E8E8`–`#F8F0E8` measured), never `#FFF`.

---

## §4 Gradients — where they start and stop

There are two distinct gradient systems, and they do different jobs.

### 4.1 The corner wash (the signature)

Not a background-image — a stack of 3–4 absolutely-positioned `<div>`s over a
flat `sandstone-200` ground, each with one radial gradient anchored to a corner,
each fading to `transparent` well before the centre. Every one of these was read
verbatim out of inline styles.

**Warm / morning** (`how-it-works`, "Starting your day"):

```css
radial-gradient(ellipse at 0%   0%,   rgba(245,190,141,0.4) 0px, transparent 20%)
radial-gradient(circle  at 99%  0%,   rgba(251,206,151,0.5) 0px, transparent 30%)
radial-gradient(circle  at 10%  90%,  rgba(253,195,130,0.5) 0px, transparent 50%)
radial-gradient(circle  at 99%  99%,  rgba(245,190,141,0.5) 0px, transparent 40%)
```

**Cool / midday** — same four anchor points, one colour: `rgba(123,135,146,0.5)`,
stops at 40% / 30% / 40% / 40%.

**Night / teal** — same geometry again: `rgba(60,91,98,0.5)`.

So a *single* geometric template is re-tinted to say what time of day it is.
That is the mechanism behind "the page feels like morning" — and it is exactly
the mechanism Kettle's `Her morning · Her afternoon` tabs want.

Other washes observed:

- **Home hero**: cream `rgba(234,220,207,1)` @ 20%/20% → transparent 20%; pale
  blue `rgba(182,207,221,0.5)` @ 0%/40%; `rgba(243,235,225,1)` @ 20%/55%; sky
  `rgba(181,228,254,0.5)` @ 99%/27%; a broad taupe ellipse
  `rgba(213,195,171,0.4)` @ 45%/55% → transparent **60%**; amber
  `rgba(255,182,72,0.3)` @ 50%/85%.
- **why-oura**: bone `rgba(220,207,187,0.7)` and clay `rgba(216,167,140,0.4)`
  at ~10% radii (tight, jewel-like); cool `rgba(212,217,221,1)`; and for the
  dark band, deep browns `rgba(69,43,29,0.6)` @ 50%/0% and `rgba(64,37,24,0.8)`
  @ 50%/100%, both → transparent 50%.

Rules that hold across all of them: **anchored at edges/corners, never centred
on content; low alpha (0.3–0.7) except the opaque cream ones; always fading to
`transparent`, never to another colour; always over a flat warm ground.**

### 4.2 Linear gradients

Far rarer, and almost always functional rather than decorative:

- **Photo scrim** (home, product cards):
  `absolute bottom-0 h-[45%] w-full bg-linear-to-t from-black/65 to-transparent`
  — bottom 45% of the image only, black at 65% → transparent, and
  `max-md:hidden` (mobile drops it). This is how they keep white text legible on
  photography without dimming the whole picture.
- **Fade-out over a spec strip** (product): `before:bg-linear-to-t
  before:from-transparent before:from-70% before:to-100%` with the `to` colour
  swapped per section — `#E2DBD3`, `#E6E4E2`, `#E7E0D9`, or `gray-450`.
- **Product-metal radials** (ring renders): 9-stop radial ramps, e.g.
  `#E3E5E7 10% → #C8CBCE 20% → … → #19191C 90%` at
  `334.64% 412.19% at 194.27% -174.96%`. Pure product photography support;
  irrelevant to Kettle.
- **Angled washes**: `bg-linear-215`, `bg-linear-271`, `lg:bg-linear-55`, and
  `lg:bg-[linear-gradient(45deg, rgba(192,139,48,0.8) -25%, transparent 60%)]`.

**Honest gap:** the stylesheet compiles a warm gradient pair
`from-[#C7B5A1] … to-[#887C6C]`, plus `from-[#D0C2AD]`, `from-[#EDE9E4]`,
`to-mustard-500`, and `lg:landscape:from-[#C7B5A1]/90 … to-55%`. These appear in
**no** markup I fetched — not on the four target pages, and not on `/membership`
or `/sleep-and-rest`, which I probed specifically to find them. The values are
real (they are compiled, so some route uses them); their placement is unknown.
Listed in §10.

---

## §5 Spacing rhythm

### The grid

`.gridContainerV3` is the whole layout system, and it is one rule:

```css
--smallGutter: 24px;  --largeGutter: 64px;
--maxContent: 1440px; --maxCol: calc(1440px / 22);   /* = 65.4545px */
```

| Breakpoint | Columns | Gutter |
|---|---|---|
| base (<768) | **8** | 24px |
| ≥768 (md) | **22** | 24px |
| ≥1024 (lg) | 22 | **64px** |
| ≥1568 | 22 × fixed 65.45px, content centred | ≥64px, flexible |

Named lines — `[full-start] gutter [main-start] … [main-end] gutter [full-end]`
— so a component says `col-start-main col-end-main` for text and
`col-start-full col-end-full` to bleed an image to the viewport edge, with no
negative margins anywhere. **22 columns** (not 12) is what lets them place
things at 1/22 precision without arbitrary widths.

Breakpoints: `md 768` · `lg 1024` · `xl 1280` · `xxl 1440`, plus the 1568 grid
switch. Base spacing unit `--spacing: 0.25rem` (4px), so every `p-*`/`gap-*`
number ×4 = px.

### Vertical rhythm

Section padding, as observed (`py` unless stated):

| Page | Mobile | Desktop |
|---|---|---|
| why-oura, most sections | **64** (`py-16`) | **128** top (`lg:pt-32`), 64 bottom |
| why-oura, dark band | 64 top only (`pt-16`) | 64 top |
| home, module blocks | 48–64 (`pb-12`, `pb-16`) | **96** (`lg:pb-24`) |
| home, footer band | 32 (`py-8`) | 64 (`lg:py-16`) |
| product, section gaps | 120 (`mt-30`) | **168** (`lg:mt-42`) |
| product, closing | 96 top / 128 bottom | 112 top |
| how-it-works timeline | full-viewport sticky panes | `lg:h-screen` |

So: **64 mobile → 128 desktop** is the default section rhythm, with the product
page running looser (120 → 168). Halving the desktop value for mobile is
consistent.

### Horizontal padding and gaps

- Page edge: `px-6` (24) mobile → `lg:px-4`/`px-0` where the grid takes over.
- Card interior: **`p-6` (24)** is the standard card padding; `p-4`/`p-5` (16/20)
  for circular icon buttons; `px-4 py-3` → `md:px-6 md:py-4` for glass chips.
- Card grid gaps: `gap-y-2` (8) inside a card's text block, `gap-x-6` / `gap-y-6`
  (24) between cards, `gap-y-10` (40) between card rows, `gap-4`/`gap-6` (16/24)
  in flex clusters.
- Text rhythm inside a card: title `mb-3` (12) above its paragraph; section
  labels `mb-6`/`mb-8` (24/32); big display headers `mb-9` → `md:mb-12` →
  `lg:mb-16` (36/48/64).
- Prose blocks (`.TypographyRhythm`): `p`/`ul`/`ol` margin 1rem block; `h2`
  `margin-top: 3rem`; `h3` `margin-top: 2rem`; first-child headings zeroed;
  heading→paragraph gap `0.25rem`.
- Header height: `calc(0.0107 × 100vw + 50.48px)`, clamped to 55px and 72px at
  the ends — a fluid nav bar, not stepped.

---

## §6 Component grammar

### 6.1 Buttons

Every button on the site is a **full pill** (`rounded-full`). There are no
rectangles and no small radii on interactive elements.

| Variant | Classes (as found) |
|---|---|
| **Primary CTA** | `rounded-full py-3 px-6 font-bold bg-blue-100 text-white hover:bg-blue-200 transition` → 12/24 padding, `#2A72DE` on `#FFF` |
| **Compact CTA** (sticky bar) | same, `py-2 px-4` |
| **Light CTA on dark hero** | `rounded-full py-3 px-6 font-bold bg-gray-100 text-gray-550 hover:bg-gray-400` |
| **Secondary / outline** | `rounded-full py-2 px-4 font-bold bg-transparent border border-solid border-current text-sandstone-200 hover:text-gray-400`, scaling to `xl:px-6 xl:py-3` |
| **Icon button (nav)** | `rounded-full size-10 md:size-12 p-0 border border-sandstone-500/25 hover:border-sandstone-500 hover:bg-sandstone-500/10 transition-colors duration-300` |
| **Icon button (on card)** | `rounded-full p-4 md:p-5 bg-sandstone-200 text-sandstone-500` — and the inverse `bg-sandstone-500 text-sandstone-200` |
| **Nav item** | `rounded-full px-6 py-3` with an underline `<span>` animated via `scaleX(0)→1` |

Note the hover convention: **10% tint of the ink colour** (`bg-sandstone-500/10`)
plus a border going from 25% to 100% opacity. Nothing jumps; nothing changes hue.

### 6.2 Radii

Frequency across the four pages: `rounded-lg` (8px) 95× · `rounded-full` 80× ·
`rounded-sm` (4) 52× · `rounded-xl` (12) 34× · `rounded-3xl` (24) 29× ·
`rounded-[24px]` 19× · `rounded-md` (6) 18× · `rounded-[100px]` 14× ·
`rounded-[40px]` 13× · `rounded-[70px]` 6× · `lg:rounded-[22px]` 6×. Tokens:
`--radius-sm .25rem` · `md .375` · `lg .5` · `xl .75` · `2xl 1` · `3xl 1.5` ·
`4xl 2` · `5xl 3.75rem`.

Read as a rule: **8px for photo/content cards, 24px for glass chips and media
tiles, 40px for large feature panels, full pill for anything clickable.**

### 6.3 Cards

- **Content card**: `bg-sandstone-200 p-6 rounded-lg flex flex-col h-full
  justify-between w-[75vw] md:w-full` — the `75vw` is the carousel peek that
  tells you to swipe.
- **Media tile**: `aspect-square rounded-[24px] overflow-hidden bg-cover mb-6`
  — image tile first, caption block below, 24px gap.
- **Glass panel card**: `absolute inset-0 mx-3 md:mx-6 rounded-lg
  backdrop-blur-[2rem] bg-sandstone-500/10 border-sandstone-500/25
  hover:border-sandstone-500 transition-colors duration-300/400`.
- **Elevation**: shadows are almost absent. What exists is soft and offset —
  `-5px 5px 20px rgba(66,66,66,0.25)`, `0px 6px 30px -4px rgba(0,0,0,0.1)`,
  `0px 4px 4px rgba(0,0,0,0.11)`, and an inset hairline `inset 0 1px 0
  rgba(255,255,255,0.06)` on dark form fields. Separation is done with
  *background* changes, not shadow.

### 6.4 The glass chip over photography

This is the pattern the founder called the "notification mockup," and in the DOM
it is this:

```
<div class="relative inline-flex items-center gap-x-2.5 overflow-hidden
            px-4 py-3 md:px-6 md:py-4">
  <div class="absolute inset-0 rounded-3xl backdrop-blur-xl
              bg-backdrop-500/40 bg-blend-multiply" aria-hidden="true"></div>
  [icon]
  <span class="text-eyebrow text-sandstone-200 relative">Sleep and Rest</span>
</div>
```

Concretely: a 24px-radius blurred plate (`backdrop-blur-xl` = 24px) at **40%
opacity of `#222428`**, multiply-blended, sitting on the photo; icon + 12px
label at 10px gap; 16/12 padding growing to 24/16 on md. The light variant is
`bg-sandstone-200/10`. Placed top-left of a photo card (`pt-6 pl-6`), with a
circular expand button at top-right.

That is a *label*, not a notification. Which brings us to:

### 6.5 The actual phone-notification mockup — it is a PNG, not markup

Their notification mockups (`walk-stretch-notification-ui-en-1.png`,
`wind-down-notification-ui-en-1.png`) are **flat image assets** composited over
photography. There is no component to read. So I measured the pixels
(native 680×163 and 656×162, ratio ≈ 4.17:1):

| Property | Measured |
|---|---|
| Fill | **fully transparent** (alpha 0 across the interior) |
| Stroke | ~2px, `#2E2E2E`, all four sides |
| Corner radius | ~14px on a 680px card (≈2% of width) |
| App icon | 92px square (13.5% of card width), inset 35/35 from top-left, corner radius ~7px (~8% of the icon) |
| Icon fill | `#2F4A73` (navy) with a white mark |
| Title / timestamp | `#F6F6F6`, "now" right-aligned |
| Body line | white at ~94% alpha, one sentence, single line |

The transparent fill is the point: the banner is designed to be *laid on a
photograph* so the photo shows through, exactly like a real iOS banner over a
lock-screen wallpaper. Kettle would build this as a component rather than an
asset — but the proportions above (4.2:1, icon at 13.5% of width, one line of
body) are a good starting geometry.

### 6.6 Data-card grammar (the part Kettle refuses, and the part it can keep)

Measured off `june_app_ui-en.png` — one of their in-app card renders:

- Card: `#211E1D` (warm near-black), radius ≈36px on a 674px card (≈5.5%), with
  a soft radial glow at the top edge lifting it to `#382C29`.
- Header row: circular icon chip, then a sans label, then a **status eyebrow in
  small caps with wide tracking** — `#D89078` clay for caution, `#F06898` pink
  for the strongest state.
- Then a large serif numeral (Editorial New ~200).
- Then, directly under the number, **a short serif sentence that interprets it**
  — their low-sleep card follows `55` with a five-word reassurance.
- Then a thin timeline bar of rounded dashes with two endpoint labels
  (`10:00 pm` … `6:30 am`).
- Then a metric row: icon + bold sans value pairs.
- Chips below the card: pill-shaped, one outline ("add") and the rest filled.
- The long-form card is a serif heading + a ~40-word second-person paragraph
  that ends in **questions**, not instructions.

**For Kettle**: the numeral, the score, the chart and the timeline are all
refused by product law #1. What transfers is the *sequence* — status word →
interpreting sentence → plain facts → optional detail — and the fact that the
interpreting sentence is set in the serif and written to lower the reader's
pulse. Kettle's version of "the number" is a phrase, not a figure.

### 6.7 Scenario tabs

Found on the home page, and it is precisely the structure the roadmap asks for.
Five tabs — the labels are moments of a day ("Starting your day," "Taking a
walk," "Under the weather," "Winding down," "Hosting a party"). Each tab:

```
appearance-none bg-transparent flex items-center justify-center
border-0 border-b-[3px] border-b-transparent border-solid   /* active: border-b-current */
opacity-70 hover:opacity-100                                 /* active: opacity-100 */
px-0 pt-3 pb-4  lg:px-12 lg:pt-5 lg:pb-7
text-sm lg:text-base
transition-opacity duration-300
```

So the active state is carried by **two** cues — a 3px bottom rule in the
current text colour, and opacity 70→100. No fill, no colour change, no weight
change. Panel content per tab: a photo, a glass chip label, an app-UI PNG, and a
heading pair `<h4>` (28→32→40, weight 300) + 14px body.

A second, chunkier tab style exists (`role="tab"`, horizontally snap-scrolling):
`border-2 border-[#CCCAC7] px-6 py-4 rounded-[100px] font-bold text-lg
text-gray-550 whitespace-nowrap snap-start`.

And a third — a **segmented pill** for time series (`June` / `July` / `August`):
`flex-1 px-5 py-3 rounded-[70px]`, inactive `bg-transparent`, active
`bg-white` or `bg-sandstone-300`, `transition-colors duration-300`.

### 6.8 Progress indicator

`bg-[#D9D9D9]/30 px-4 py-2 rounded-[100px] w-[240px]` containing a 1px bar
`bg-sandstone-500` animated with `transform: scaleX()` from `origin-left`. A
story-style progress track, 240px fixed.

### 6.9 Form field

`bg-sandstone-500 rounded-xl py-2 pl-5 pr-12 text-white placeholder-white
tracking-wide shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]` with an absolutely
positioned 32px submit button inset right-2. Dark field on a dark footer; the
inset white hairline is the only affordance.

---

## §7 Motion

- Default transition: `0.15s cubic-bezier(0.4, 0, 0.2, 1)`. In markup the
  durations actually used are **300** (57×), **1000** (30×), 500, 400, 700, with
  `ease-in-out` 34×.
- Entry animation, read off inline styles on `.motionComponent` elements:
  `opacity: 0; filter: blur(5px); transform: translateY(25px)` → animating to
  `opacity: 1; blur(0); translateY(0)`. Tokens `--y-initial: 20px`,
  `--y-exit: -20px` corroborate it.
- Scroll: `how-it-works` is a stack of `lg:h-screen` sticky panes with
  opacity/`h-[200svh]` scroll-linked transitions; the product page uses
  `h-[200svh]` scroll sequences.
- `motion-reduce:` and `nojs:` variants exist on the sticky panes — they degrade
  to static full-height sections. Worth copying as a habit.

**A blur-in of 5px with a 25px rise is the single most characteristic motion on
the site**, and it is cheap to reproduce.

---

## §8 Copy voice

Measured over 226 unique text nodes across the four pages.

| Measure | Value |
|---|---|
| Median words per text node | **4** |
| Mean | 7.8 |
| 90th percentile | 22 |
| Longest | 45 |
| Distribution | 58 nodes ≤2 words; 61 at 3–5; 24 at 6–8; then a gap, then 23 nodes at 21–23 |
| `you` / `your` | **109 / 72** |
| `we` | **3** |
| `their` | 2 |
| Question marks | **2** |
| Em dashes | 6 |

The distribution is the finding: it is **bimodal**. Headings are 3–5 words.
Paragraphs are 21–23 words. There is almost nothing in between, and almost
nothing above 23. They do not write medium-length sentences.

Other rules, all verifiable from the corpus:

1. **Second person, overwhelmingly.** 181 uses of you/your against 3 of "we."
   The company is not a character in its own copy; the reader is.
2. **Headings are noun phrases or short imperatives**, 3–4 words, frequently
   with the emotional word set in serif italic — the sans carries the claim, the
   serif carries the feeling.
3. **Almost no questions.** Two on four pages, both rhetorical setups
   immediately answered. They do not interrogate the reader.
4. **Numbers appear only as credentials, never as instructions** — accuracy
   percentages, years, counts of metrics. Each is paired with a footnote marker
   and a plain label beneath it.
5. **Data is captioned, never announced.** In their app cards, a bad number is
   followed by a short serif sentence of reassurance; a stressful day is
   described in past tense, credits the reader for getting through it, and ends
   by inviting reflection rather than prescribing action. The verb tense matters:
   *what happened*, not *what you must do*.
6. **No urgency vocabulary.** Across all four pages I found no "now," "hurry,"
   "don't miss," no exclamation-driven CTAs. CTA labels are one or two flat
   words.
7. **Time is spoken as time**, not as duration — the scenario page marks moments
   (`6:00 AM`) rather than intervals.

**For Kettle**, the two rules that matter most are #5 and #7. Kettle's whole copy
problem is describing an absence of routine without frightening anybody, and
this corpus shows the method: describe in the past tense, name the moment rather
than the gap, and let a serif sentence do the reassuring while the sans states
the fact. What Kettle must *not* import is the health-state vocabulary attached
to it.

---

## §9 Imagery — precise enough to prompt from

Delivery: **imgix**, `ourahealth.imgix.net`, params
`auto=format&fit=max|crop&fm=png&q=70&w=<256…3840>` with signed `s=`. Where
cropping is art-directed they use focal points: `crop=focalpoint&fp-x&fp-y&fp-z`
(zoom up to 2.0) and `ar=10:7` or `ar=1:1`. Occasional `flip=h`, `trim`,
`trim-color`. Ten `w=` steps per image, so every photo ships at the exact
rendered width.

### Measured grading

Downsampled to 40×40 and averaged (mean RGB, mean HSV saturation/value, mean hue
of pixels with S>0.08):

| Asset | Mean | Sat | Val | Hue | R−B |
|---|---|---|---|---|---|
| `why-oura-hero` (portrait, indoors) | `#694D39` | 0.44 | 0.41 | **48°** | **+49** |
| `host-party-primary` (outdoors, dusk) | `#B08C72` | 0.38 | 0.69 | **36°** | **+62** |
| `start-day` (bedroom, dawn) | `#343F43` | 0.33 | 0.27 | **207°** | −15 |
| `june` (night) | `#151620` | 0.46 | 0.13 | 247° | −11 |

So the grade is not one look — it is **two**, and they are used as time
signals. Warm scenes sit at hue 36–48° with red exceeding blue by 50–60 points
and mid-to-high value. Night scenes invert to hue 207–247° and crush value to
0.13–0.27. Saturation stays modest throughout (0.33–0.46): nothing is vivid.

### Treatment and framing (from viewing the assets)

- **Light**: single-source and directional. Warm frames read as low window light
  or golden hour with visible falloff across the face; the night frame is lit
  almost entirely by the phone screen the subject is holding, with a cool
  ambient fill behind.
- **Blacks are lifted-then-crushed**: large areas go to near-black with detail
  retained only where the key light lands. The dawn bedroom frame is 30% pure
  black by pixel count.
- **Skin is not retouched flat** — freckles, texture and colour variation are
  visible and kept.
- **Subjects rarely meet the camera.** Eyes closed, looking down at a phone,
  turned away, or in three-quarter profile mid-conversation. Where two people
  appear, they are touching (a hand on a shoulder, hands interlaced).
- **Framing** is close: head-and-shoulders or hands-and-object. Backgrounds are
  plain plaster, foliage, or bokeh — never a busy interior.
- **Aspect ratios** in use: 1:1 for editorial heroes, 10:7 for product cards,
  ~4:3 for scenario photography.
- **The device is present but never the subject** — it appears on a hand at the
  frame's edge, in focus but off-centre.
- **App screens are separate transparent PNGs layered over the photo**, not
  composited into it. That is how the same photo can serve three months of a
  time series (`june.jpg` + `june_app_ui-en.png`).

### Prompt-shaped summary for later image generation

> Close-framed candid of one person in a domestic interior, single directional
> window light from camera-left with visible falloff, deep shadows retaining
> detail, warm grade (hue ≈40°, red channel ~50 points above blue), saturation
> low-to-moderate (~0.4), skin texture preserved and unretouched, subject not
> looking at camera, plain plaster or foliage background at shallow depth, 1:1 or
> 4:3, no props competing for attention.

And the night counterpart: *same construction, single cool light source at hue
≈210°, overall value ≈0.25, subject silhouetted with rim light only.*

Two cautions before generating anything for Kettle. First, their casting is
uniformly young-to-middle-aged and athletic; Kettle's subjects are elders in
Chennai and their adult children abroad, so the *casting* must change completely
even where the grade carries. Second, this grade in an eldercare context can
tip from "calm" to "elegiac" fast — warm and low-key reads as memorial if the
subject is alone and still. Kettle's warm frames should show ordinary motion
(a kettle, a doorway, a phone in use), not repose.

---

## §10 What fetch could not see — founder screenshots needed

Honest per-item list. Nothing below is guessed at elsewhere in this document.

| # | What's missing | Why fetch can't get it | Screenshot needed |
|---|---|---|---|
| 1 | **Scroll choreography** on `/how-it-works` — how the sticky panes hand off, what moves, at what rate | Requires a running browser and a scroll position; the DOM only shows `lg:h-screen`, `h-[200svh]`, `js:sticky` | `/how-it-works`, a short screen recording or 4–5 stills through one full scroll |
| 2 | **The scenario tab set in its active state**, and how the panel transitions between tabs | Only the first tab's panel is server-rendered; the rest is client state | `ouraring.com` home, the "Spend a day with Oura"-style scenario block, one still per tab |
| 3 | **Hover/focus as rendered** on the primary CTA and the cards | Classes give the target values (`hover:bg-blue-200`, `hover:border-sandstone-500`); the perceived transition is not derivable | Optional — low value; classes are sufficient |
| 4 | **Where the warm gradient pair `#C7B5A1 → #887C6C` lives** (also `#D0C2AD`, `#EDE9E4`, `to-mustard-500`, `lg:landscape:` variants) | Compiled into the stylesheet but present in no markup I fetched, including `/membership` and `/sleep-and-rest` | Founder: if you have a screen showing a large warm two-stop wash behind content, capture it with its URL |
| 5 | **The full app-card set** — I measured one (`june_app_ui-en.png`). The status-eyebrow colour vocabulary may have more states than the two I found | Each is a separate flat PNG; I sampled one page's worth | Optional; only matters if we want the full status-colour ramp |
| 6 | **Type rendering at real viewport widths** — the ladders in §2 are exact, but which step lands on a given screen depends on the device | Breakpoints are known; the visual result is not | Optional |
| 7 | **Nav/menu open state and the mega-menu** | Client-rendered on interaction | Only if the landing page grows a nav; not needed for v1 |

Items 1, 2 and 4 are the ones I'd actually ask for. 1 and 2 because the
storytelling mechanic is the thing being adopted and I can describe only its
skeleton; 4 because it is a real token pair whose intended use I cannot honestly
report.

---

## §11 Candidate tokens for Kettle

One page. **Carry** = structural, safe to adopt as-is (ratios, mechanics,
spacing maths). **Re-choose** = must differ from Oura's values so Kettle does not
wear their clothes. **Refuse** = ruled out by product law.

| Role | Oura's value | Kettle candidate | Carry / Re-choose / Refuse |
|---|---|---|---|
| **Sans family** | Akkurat LL 300/400 (commercial) | A grotesque with real 300/400/**600**; licensed or open — decision in DECISIONS 74 | Re-choose (licence) |
| **Serif family** | PP Editorial New 200/300 + italic | A high-contrast editorial serif with a true italic at ~200–300 | Re-choose (licence) |
| **Serif usage rule** | ~34 italic `<em>` inside sans lines; stats; pull quotes; nothing else | Identical discipline: the human phrase inside a plain sentence, and numbers-as-objects | **Carry** |
| **Base body** | 14 / 1.5 / 0 tracking | **16** / 1.5 / 0 — Kettle's readers include people reading at arm's length on a phone at 6am | Re-choose (larger) |
| **Lead paragraph** | 18 | 18–20 | Carry |
| **Eyebrow** | 12 | 13 | Carry (scaled) |
| **Card title** | 28 → 32 → 40, weight 300, leading **1.0** | 24 → 28 → 32, weight 300, leading 1.05 | Carry (mechanics), scale down |
| **Section display** | 40 → 52 → 80, weight 300, tracking −0.05em | 36 → 48 → 64, weight 300, tracking −0.03em | Carry (ladder shape) |
| **Weight/size inversion** | large = 300, small = 700 | same rule | **Carry** |
| **Page ground** | `#F7F1E8` sandstone-200 | A warm off-white that is *not* theirs — candidate `#F6F2EC` or a faintly greener `#F4F1E9` | Re-choose |
| **Ink** | `#4A4741` (warm dark, R>G>B) | Warm dark of the same family but distinct — candidate `#403C36` | Re-choose (keep the warmth rule) |
| **Two-token inversion** | light section = ground/ink; dark section = ink/ground | same | **Carry** |
| **Secondary text** | `#A8A5A0` | ~`#8F8B84` (needs ≥4.5:1 on ground) | Re-choose |
| **Primary CTA** | `#2A72DE` blue, pill, `py-3 px-6`, bold | Kettle's own accent — *not* blue, *not* red; candidate a deep warm green or clay. Geometry and padding carry | Carry (form) / Re-choose (hue) |
| **Caution colour** | `#D89078` clay | A muted clay/amber; **never** red, **never** used to describe a person | Carry (principle) |
| **Alarm colour** | `#F06898` pink | Kettle has no alarm colour on the landing page | Refuse |
| **Corner-wash gradient** | 3–4 corner-anchored radials, alpha 0.3–0.7, → transparent at 10–60%, over flat ground | Same mechanism, Kettle's own tints; morning/afternoon/evening triple to drive the scenario tabs | **Carry** (mechanism) |
| **Time-of-day tinting** | one geometry re-tinted warm / grey / teal | same idea: `Her morning` warm, `Her afternoon` neutral, `When something's off` cooler but never red | **Carry** |
| **Photo scrim** | `bottom 45%`, `black/65 → transparent`, desktop only | identical | **Carry** |
| **Grid** | 22 cols, gutters 24 → 64, max 1440, named full/main lines | Same construction (22 or 12; the named-line idea is what matters) | **Carry** |
| **Spacing unit** | 4px | 4px | **Carry** |
| **Section rhythm** | 64 mobile → 128 desktop | 64 → 112 | Carry |
| **Card padding** | `p-6` (24) | 24 | Carry |
| **Card gaps** | 24 between cards, 40 between rows, 8 inside | same | Carry |
| **Radii** | 8 content · 24 glass/media · 40 feature panel · full pill interactive | same ladder | **Carry** |
| **Shadows** | near-absent; soft offset `-5px 5px 20px rgba(66,66,66,.25)` | same restraint | Carry |
| **Button hover** | ink at 10% tint + border 25%→100% | same | Carry |
| **Glass chip** | `backdrop-blur-xl`(24) · `#222428` @40% · multiply · radius 24 · 16/12 pad · 12px label | same mechanics, Kettle's ink at 40% | **Carry** |
| **Notification mockup** | flat PNG, 4.17:1, transparent fill, 2px `#2E2E2E` stroke, icon 13.5% of width, one body line | Build as a real component at those proportions | Carry (geometry) |
| **Scenario tabs** | 3px bottom rule + opacity 70→100, no fill, `pt-3 pb-4` → `lg:pt-5 lg:pb-7`, 14→16px | identical; labels become `Her morning · Her afternoon · When something's off · What you see` | **Carry** |
| **Segmented pill** | `rounded-[70px] px-5 py-3`, active = filled | same | Carry |
| **Entry motion** | opacity 0→1, blur 5px→0, translateY 25px→0, ~300ms | same, ≤300ms, with `motion-reduce` fallback | **Carry** |
| **Copy: heading length** | 3–5 words | same | **Carry** |
| **Copy: paragraph length** | 21–23 words | same | **Carry** |
| **Copy: person** | `you/your` 181× vs `we` 3× | same, addressing the adult child | **Carry** |
| **Copy: data caption** | status word → serif reassurance → plain facts | same sequence, but the "status word" describes *the routine*, never the person, and there is no numeral | Carry (form) / Refuse (semantics) |
| **Score / numeral** | `55` in serif, 48–68px | Kettle has no score. The slot holds a phrase | **Refuse** |
| **Charts, timelines, sparklines** | dashes-and-dots timeline, stress graph | none | **Refuse** |
| **Status eyebrow text** | `PAY ATTENTION`, `STRESSFUL DAY` | typographic form only; wording must never diagnose | Carry (form) / Refuse (wording) |
| **Imagery grade — warm** | hue ≈40°, R−B ≈ +55, sat ≈0.4, val 0.4–0.7 | same numbers, elder subjects, ordinary motion not repose | Carry (grade) / Re-choose (casting) |
| **Imagery grade — night** | hue ≈210°, val 0.13–0.27 | same, used sparingly | Carry |
| **Imagery framing** | close, subject not facing camera, device at frame edge | same, with the phone as the quiet protagonist | Carry |
| **Photography source** | commissioned shoot | generated or licensed; §9 has the prompt skeleton | Re-choose |

---

## §12 Open questions for the PM

Filed as **DECISIONS 74–76**. Summary: the two typefaces are commercial and need
a licensing decision; the "status eyebrow" pattern is typographically desirable
but semantically forbidden by product law #1 and needs a ruling on how far the
form can travel without the meaning; and the trade-dress line needs a concrete
threshold for the palette, because "warm neutrals" is a look many products share
but `#F7F1E8`/`#4A4741` as a *pair* is theirs.
