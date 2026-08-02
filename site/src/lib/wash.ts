/**
 * The corner wash (spec 006 §2, design-language §5).
 *
 * One geometry template, four tint sets. That is the whole time-of-day
 * mechanic: a panel differs from its neighbour by *tint alone*, never by
 * structure, so the page can feel like it moves through a day without ever
 * telling the reader anything new about a person.
 *
 * Invariants, all asserted in `tests/wash.test.ts`: anchored at edges and
 * corners, never centred on content; alpha 0.3–0.7; always fading to
 * `transparent`, never to another colour. The tint values themselves live in
 * `tokens.css` with every other colour — this file holds shape, not paint.
 */

export interface WashLayer {
  /** `radial-gradient(<shape> at <at>, …)`. */
  shape: "ellipse" | "circle";
  /** Corner or edge anchor. Never a centre. */
  at: string;
  /** Percentage at which the tint has fully faded to `transparent`. */
  fade: number;
}

/** The measured template, adopted verbatim as geometry (spec 006 §2). */
export const WASH_TEMPLATE: readonly WashLayer[] = [
  { shape: "ellipse", at: "0% 0%", fade: 20 },
  { shape: "circle", at: "99% 0%", fade: 30 },
  { shape: "circle", at: "10% 90%", fade: 50 },
  { shape: "circle", at: "99% 99%", fade: 40 },
] as const;

export type WashSet = "morning" | "afternoon" | "off" | "seen";

export const WASH_SETS: readonly WashSet[] = ["morning", "afternoon", "off", "seen"] as const;

/** The CSS custom properties holding one set's four tints. */
export function tintVariables(set: WashSet): string[] {
  return WASH_TEMPLATE.map((_, index) => `--tint-${set}-${index + 1}`);
}

/**
 * One `background-image` value: four radial gradients over a flat warm ground.
 *
 * Not a background image in the literal sense either — no asset, no request, no
 * foreign origin. Four gradients cost nothing and are the only reason this page
 * can carry four moods without four photographs.
 */
export function washBackground(set: WashSet): string {
  return WASH_TEMPLATE.map(
    (layer, index) =>
      `radial-gradient(${layer.shape} at ${layer.at}, ` +
      `var(--tint-${set}-${index + 1}) 0%, transparent ${layer.fade}%)`,
  ).join(", ");
}
