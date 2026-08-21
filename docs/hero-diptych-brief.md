# Kettle — hero diptych brief

*PM: Fable, 2026-08-03. Hand this to any design session working on the landing-page hero. It is
self-contained, but the binding law is `docs/design-language.md` and the tests in `site/src/tests/`
— where this brief and the law disagree, the law wins.*

## 1 What this is

A redesign of the hero's visual: one full-width photographic composition in the "two lives, one
frame" pattern — the parent in their world on one side, the adult child in theirs on the other,
distance present between them, both mid-moment. Inspired by a travel-site reference (Triverra) whose
composition is worth taking and whose treatment is not.

## 2 Adopt / refuse (decided — do not relitigate)

**Adopt: the composition.** Two panels, one frame. Parent left, adult child right, each in their own
light and their own life. Neither watches the other; the distance between them is calm, not sad.
This is commissioned concept 3 (`design-language.md` §9) evolved into a diptych.

**Refuse — each of these is enforced by an existing test and will fail CI:**

- **The dark-cinema treatment.** No full-bleed dark hero, no white-on-black display type. Kettle's
  ground is warm canvas `#F6F2EC`, ink `#403C36`; dark sections exist only as exact inversions and
  the hero is not one. Text sits on canvas above or beside the image — never overlaid on the
  photograph, no scrim tricks. The contrast tests (ink ≥7:1, secondary ≥4.5:1 on canvas) must pass
  untouched.
- **Rotation/carousel.** No rotating images, no crossfading personas. Motion law: entry fade + rise
  only, everything behind `motion-safe:`, hover is colour-only. Alternating which parent appears is
  a decision for a future photo shoot, not a runtime behaviour.
- **Social-proof numerals.** No "8370+ trips · 4.9"-style bar. The digit walk allows the price and
  step numerals only; numbers-as-verdicts are refused product-wide.
- **Urgency and register.** No overlay taglines in the "Dream deeper" mould. Hero copy is locked
  (`HERO_*` in `site/src/copy.ts`) and changes only via a spec amendment; headings 3–5 words,
  no urgency vocabulary, the culture-coded ban is unexemptable.

## 3 Composition spec

- **Format:** one wide slot, roughly 21:9 to 2:1, full content-width (not full-bleed to the viewport
  edge if it would crowd the beats — one idea per viewport, ~700–1,100px rhythm).
- **Left panel — the parent:** mid-action in their own space (balcony garden, market return,
  rehearsal — see §9 concepts). Warmer light.
- **Right panel — the adult child:** their own life in another city — desk by a window, kitchen,
  commute. A phone present but incidental (face-up, dark or showing one quiet line — never a
  rendered UI screenshot inside a photograph). Slightly cooler light, same grade family.
- **The seam:** a soft division — architectural edge, window frame, or a simple hard cut. No map
  lines, no dotted "connection" graphics, no arrows between them; the *absence* of a drawn link is
  the point.
- **Both figures have agency.** Neither is waiting, worried, or watching a screen anxiously. The
  child's payoff is quiet relief, not vigilance. Grading: warm side light, earthy grade, lifted
  blacks, shallow domestic haze (design-language §9 register).
- **Radius/placement:** image card at the 8px content radius, sitting below the H1/sub/CTA block on
  canvas, replacing the current concept-3 slot.

## 4 Banned imagery (unchanged, applies fully)

No toothpaste-ad smiles; no scrubs or caregiver-leaning-in; no helper/recipient hierarchy; no
window-forlorn staging; no clutched photographs; no sanitized knitwear perfection; no facility /
insurance register; no red badges, sirens, alarm UI, or worried faces — **no alert imagery, ever**,
including inside any mockup visible in the photo.

## 5 Implementation notes

- Ship as the same placeholder-block pattern as the five existing slots until photography exists;
  alt text lives in `copy.ts`, passes the full copy law, and describes agency. Draft alt:
  `A mother tending her balcony garden in one city; her son at his kitchen table in another,
  at ease.`
- No new tokens, no new type styles, no motion beyond the section's existing entry fade.
- Log the change as a numbered `specs/DECISIONS.md` item (next number per `CLAUDE.md`); if any test
  needs weakening to land this, stop — that is a PM question, not a design decision.

## 6 Prompt seeds (generation or shoot brief)

Style prefix: *documentary lifestyle photograph, candid mid-moment, warm side light, earthy colour
grade, lifted blacks, shallow depth of field, imperfect framing, natural skin texture, wide 2:1
diptych.*

- *Left half: a mother in her 60s tending an overgrown balcony garden, hands in soil, late-afternoon
  gold. Right half: her adult son at a kitchen table in another city, morning coffee, phone face-down
  beside his laptop, at ease. Divided by a soft architectural seam; two cities, one calm.*
- Variant (father/daughter): *left half: a father in his late 60s returning from the market, bags in
  hand, keys in the door. Right half: his adult daughter on a balcony in another city, tea in hand,
  unhurried.*
