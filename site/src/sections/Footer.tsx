import {
  FOOTER_CONTACT_HREF,
  FOOTER_CONTACT_LABEL,
  FOOTER_LINE,
  FOOTER_PRIVACY_LABEL,
  FOOTER_WORDMARK,
} from "@/copy";

/**
 * Wordmark, the sentence the product is, two links.
 *
 * No social icons. A row of them pointing at accounts that do not exist is a
 * claim about a company's presence, and this page does not make claims it
 * cannot cash — the same rule that governs everything above it.
 */
export function Footer() {
  return (
    <footer className="bg-canvas px-6 py-16 text-ink" data-testid="footer">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
        <p className="text-body font-semibold">{FOOTER_WORDMARK}</p>
        <p className="text-body text-secondary">{FOOTER_LINE}</p>
        <nav className="flex gap-6 text-body">
          <a className="underline underline-offset-4" href="/privacy.html">
            {FOOTER_PRIVACY_LABEL}
          </a>
          <a className="underline underline-offset-4" href={FOOTER_CONTACT_HREF}>
            {FOOTER_CONTACT_LABEL}
          </a>
        </nav>
      </div>
    </footer>
  );
}
