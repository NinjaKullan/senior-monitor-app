/**
 * The notification mockup's proportions (spec 006 §5, design-language §7).
 *
 * A component, not an asset. The reference ships a flat PNG; rebuilding it means
 * the fill can be transparent so the slot behind shows through, the stroke and
 * icon are our colours rather than someone else's, and — the part that matters —
 * the body text is real copy that the copy law reads. A PNG of a notification is
 * a sentence about a family that no test can see.
 *
 * Every number lives here so AC11 has one place to check, and so a "just this
 * once" tweak in a component shows up as a diff against a named constant.
 */

export const NOTIFICATION = {
  /** Card width ÷ height. */
  aspectRatio: 4.2,
  strokeWidthPx: 2,
  /** Stroke is ink at reduced opacity — present, never assertive. */
  strokeOpacity: 0.35,
  /** Corner radius as a percentage of card *width*. */
  radiusPercentOfWidth: 2,
  /** App icon edge as a percentage of card width. */
  iconPercentOfWidth: 13.5,
  /** The icon's own corner radius, as a percentage of the icon. */
  iconRadiusPercentOfIcon: 8,
} as const;

/**
 * `border-radius` that is a true 2% of width on all four corners.
 *
 * A bare `2%` would resolve vertically against the card's height and round the
 * corners into ellipses, and on a 4.2:1 card that is visible. The vertical half
 * is scaled by the aspect ratio so both axes describe the same distance.
 */
export function cardRadius(): string {
  const horizontal = NOTIFICATION.radiusPercentOfWidth;
  return `${horizontal}% / ${horizontal * NOTIFICATION.aspectRatio}%`;
}
