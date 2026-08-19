import type { ReactNode } from "react";

/**
 * One idea per viewport, and the entry animation that carries it in.
 *
 * Fade plus a 20px rise over 1s, gated `motion-safe:` — under
 * `prefers-reduced-motion` the element is simply there, with no JavaScript
 * involved in deciding that. Keeping the gate in the class rather than in a
 * hook is what makes AC7 checkable by reading the DOM: a viewer who asked for
 * no motion gets none, and the test does not have to simulate a media query to
 * prove it.
 *
 * There is no backdrop slot any more (QUESTIONS 135). A decorative layer that
 * shares a box with flowing text will land on that text at some width, and did:
 * the rhythm field's second placement now owns a reserved band of its own
 * inside the content column instead of sitting behind it.
 */
export function Section({
  id,
  children,
  className = "",
  inverted = false,
}: {
  id?: string;
  children: ReactNode;
  className?: string;
  inverted?: boolean;
}) {
  return (
    <section
      id={id}
      data-testid="section"
      className={
        // `inverted` swaps the tokens themselves, so every colour below it
        // inverts exactly — ink ground, canvas text, no third scheme.
        `${inverted ? "inverted " : ""}relative bg-canvas text-ink motion-safe:animate-rise ` +
        `px-6 py-24 md:py-32 ${className}`
      }
    >
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-8">
        {children}
      </div>
    </section>
  );
}
