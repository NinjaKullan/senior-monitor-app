import { useEffect, useState } from "react";
import { PillLink } from "@/components/Pill";
import { HERO_CTA } from "@/copy";

/**
 * The floating CTA (founder request, QUESTIONS 137).
 *
 * The ask stays reachable while someone reads, without the page acquiring a
 * permanent overlay. It is the same pill, pointed at the same anchor, carrying
 * the *same string* as the hero's — one CTA text on this page, one target — so
 * a reader who scrolls past the hero has not been handed a second offer.
 *
 * It yields rather than competes. While the hero is on screen its own CTA is
 * already there; while the waitlist is on screen the form itself is; and while
 * the footer is on screen there is a privacy link underneath it that a floating
 * button has no business covering. In all three cases this renders nothing at
 * all — not a hidden element, nothing — so there is no invisible layer over the
 * page, nothing for a pointer or a screen reader to find, and no focus stop in
 * the middle of the footer.
 *
 * Appearing is the motion law's one entry: fade and rise, gated `motion-safe:`,
 * so a reduced-motion reader gets the same button at the same moments with no
 * transition at all. There is no exit animation because the law has none.
 *
 * Discipline, the same as the three-fields stir: an IntersectionObserver and
 * nothing else — no scroll listener, no `preventDefault`, no measurement on the
 * main thread — the frame is `pointer-events-none` so it cannot intercept a
 * scroll or a tap, and the observer is disconnected on unmount.
 */

/** What the button gets out of the way of, in the order it was argued. */
export const YIELDS_TO = ["#hero", "#waitlist", '[data-testid="footer"]'] as const;

/**
 * The rule, as a function so it can be read and tested: the button floats only
 * when every one of those is off screen. An empty list means the page did not
 * look the way this component expects, and the safe answer there is silence —
 * a CTA that cannot tell where it is would be the permanent overlay the ruling
 * refuses.
 */
export function shouldFloat(inView: readonly boolean[]): boolean {
  return inView.length === YIELDS_TO.length && inView.every((visible) => !visible);
}

export function FloatingCta() {
  const [floating, setFloating] = useState(false);

  useEffect(() => {
    // No observer, no floating button. The page already carries this CTA twice;
    // the floating one is the addition, and an addition that cannot tell
    // whether it is on top of the form does not get to appear.
    if (typeof IntersectionObserver === "undefined") return;

    const targets = YIELDS_TO.map((selector) => document.querySelector(selector)).filter(
      (node): node is Element => node !== null,
    );
    if (targets.length !== YIELDS_TO.length) return;

    // Assume everything is in view until told otherwise, so the first frames
    // are silent rather than a button that flashes and then hides.
    const seen = new Map<Element, boolean>(targets.map((target) => [target, true]));
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) seen.set(entry.target, entry.isIntersecting);
      setFloating(shouldFloat([...seen.values()]));
    });
    for (const target of targets) observer.observe(target);
    return () => observer.disconnect();
  }, []);

  if (!floating) return null;

  return (
    // The frame spans the width so the button can sit centred on a phone and
    // at the end on a desktop without a transform doing the centring — and it
    // is `pointer-events-none`, so the strip of screen it covers stays the
    // page's. Only the pill itself takes a pointer.
    <div
      data-testid="floating-cta-frame"
      className={
        "pointer-events-none fixed inset-x-0 bottom-0 z-40 flex justify-center px-6 " +
        "pb-safe md:justify-end"
      }
    >
      <div className="pointer-events-auto motion-safe:animate-rise" data-testid="floating-cta">
        <PillLink href="#waitlist">{HERO_CTA}</PillLink>
      </div>
    </div>
  );
}
