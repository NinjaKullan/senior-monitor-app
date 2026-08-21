/**
 * The scenario tab row on a phone (DECISIONS 136).
 *
 * Four tabs — "Her morning", "Her afternoon", "When something's off", "What you
 * see" — need about 540px of row. A phone gives 312–380, so a wrapping row
 * folds into a ragged two-line block, which is what the founder saw on a real
 * handset. Below the md breakpoint the row stops wrapping and scrolls sideways
 * instead.
 *
 * Two decisions live here rather than in the component, because they are
 * arithmetic and arithmetic is testable: whether the row is actually clipped,
 * and where it has to be scrolled so the active tab is wholly visible. jsdom
 * lays nothing out, so a test that read these off the DOM would be reading
 * zeroes; these take plain numbers and are checked against the cases that
 * matter, with the browser check in scripts/probe-responsive.mjs on top.
 */

/** The fade at the clipped edge, in px — it must also be the margin kept
 *  around the active tab, or the tab it points at ends up under it. */
export const EDGE_FADE = 40;

/** Clipped, and therefore worth a fade. Equal widths mean the row fits. */
export function isOverflowing(scrollWidth: number, clientWidth: number): boolean {
  return scrollWidth > clientWidth;
}

/**
 * Where the strip must be scrolled for `tab` to be wholly in view, keeping the
 * fade's width clear on the side it is scrolling from. Returns the current
 * position unchanged when the tab is already visible — a tab in the middle of
 * a visible row must not drag the strip around under the reader.
 */
export function scrollLeftFor(
  view: { scrollLeft: number; clientWidth: number; scrollWidth: number },
  tab: { offsetLeft: number; offsetWidth: number },
  margin: number = EDGE_FADE,
): number {
  const clamp = (value: number) => Math.min(Math.max(value, 0), Math.max(0, view.scrollWidth - view.clientWidth));
  const left = tab.offsetLeft - margin;
  const right = tab.offsetLeft + tab.offsetWidth + margin;
  if (left < view.scrollLeft) return clamp(left);
  if (right > view.scrollLeft + view.clientWidth) return clamp(right - view.clientWidth);
  return view.scrollLeft;
}
