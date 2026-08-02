import type { ReactNode } from "react";

/**
 * Every clickable thing on this page is a full pill (design-language §7).
 *
 * Hover is a **colour shift only**, ~150ms: no elevation, no transform, no
 * scale. The reference's own buttons faux-bold a 400 weight file; ours renders
 * a true semibold, which is the one place this site is deliberately better than
 * what it learned from.
 *
 * `hover:scale` is planted in the motion test and must fail. A page whose job is
 * calm cannot have controls that jump.
 */
const PILL =
  "inline-flex items-center justify-center rounded-full px-6 py-3 text-feature " +
  "font-semibold transition-colors duration-150 focus-visible:outline-none " +
  "focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-2 " +
  "focus-visible:ring-offset-canvas";

export function PillLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a
      href={href}
      className={`${PILL} bg-ink text-canvas hover:bg-calm`}
      data-testid="cta"
    >
      {children}
    </a>
  );
}

export function PillButton({
  children,
  type = "submit",
}: {
  children: ReactNode;
  type?: "submit" | "button";
}) {
  return (
    <button type={type} className={`${PILL} bg-ink text-canvas hover:bg-calm`} data-testid="cta">
      {children}
    </button>
  );
}
