import {
  GUIDE_CHANGES_LABEL,
  GUIDE_IN_CASE_LABEL,
  GUIDE_LIVING_ALONE_LABEL,
  GUIDE_NORMAL_DAY_LABEL,
  POST_CALL_LABEL,
  POST_HOW_OFTEN_LABEL,
  POST_INFORMATION_LABEL,
  POST_PHONE_LABEL,
  FOOTER_CONTACT_HREF,
  FOOTER_CONTACT_LABEL,
  FOOTER_LEGAL_LINE,
  FOOTER_LINE,
  FOOTER_PRIVACY_LABEL,
  FOOTER_WORDMARK,
  NAV_BLOG_LABEL,
  NAV_RESOURCES_LABEL,
} from "@/copy";

/** Every guide and every post, one click from the home page (seo-backlog D7). */
const GUIDES: ReadonlyArray<readonly [string, string]> = [
  ["/resources/okay-living-alone/", GUIDE_LIVING_ALONE_LABEL],
  ["/resources/normal-day/", GUIDE_NORMAL_DAY_LABEL],
  ["/resources/emergency-info/", GUIDE_IN_CASE_LABEL],
  ["/resources/changes-tracker/", GUIDE_CHANGES_LABEL],
];
const POSTS: ReadonlyArray<readonly [string, string]> = [
  ["/blog/parent-doesnt-answer-the-phone/", POST_PHONE_LABEL],
  ["/blog/how-often-should-you-check-on-a-parent/", POST_HOW_OFTEN_LABEL],
  ["/blog/the-information-youll-wish-you-had/", POST_INFORMATION_LABEL],
  ["/blog/the-call-ive-rehearsed-and-never-made/", POST_CALL_LABEL],
];

/**
 * Wordmark, the sentence the product is, the links, then every page by name.
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
          <a className="underline underline-offset-4" href="/blog/" data-testid="footer-blog">
            {NAV_BLOG_LABEL}
          </a>
          <a
            className="underline underline-offset-4"
            href="/resources/"
            data-testid="footer-resources"
          >
            {NAV_RESOURCES_LABEL}
          </a>
        </nav>
        <div className="flex flex-col gap-6 text-body sm:flex-row sm:gap-12" data-testid="footer-pages">
          {[GUIDES, POSTS].map((group, i) => (
            <ul key={i} className="flex flex-col gap-2">
              {group.map(([href, label]) => (
                <li key={href}>
                  <a className="underline underline-offset-4" href={href}>
                    {label}
                  </a>
                </li>
              ))}
            </ul>
          ))}
        </div>
        <p className="text-body text-secondary" data-testid="footer-legal">
          {FOOTER_LEGAL_LINE}
        </p>
      </div>
    </footer>
  );
}
