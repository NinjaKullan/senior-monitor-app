import type { ReactNode } from "react";

/**
 * The serif, and the only thing in this codebase allowed to render it.
 *
 * Scarcity is the whole mechanism: in the measured corpus the serif appears a
 * few dozen times against hundreds of text nodes, and its power is entirely in
 * how rarely it arrives. Permitted in three places — the emotional phrase inside
 * an otherwise plain sans sentence, a pull-quote, and a card's reassurance
 * sentence — and never in body, buttons, chrome, or on two consecutive elements.
 *
 * Funnelling every use through one component is what makes AC10 testable: the
 * test asserts that nothing else in the rendered DOM carries the serif class,
 * and that no two adjacent siblings do.
 */
export function SerifPhrase({
  children,
  as = "em",
}: {
  children: ReactNode;
  as?: "em" | "p";
}) {
  const className = "font-serif font-light italic";
  if (as === "p") {
    return (
      <p className={`${className} text-quote`} data-testid="serif">
        {children}
      </p>
    );
  }
  return (
    <em className={className} data-testid="serif">
      {children}
    </em>
  );
}
