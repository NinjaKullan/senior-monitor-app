import { HEADER_WORDMARK, NAV_BLOG_LABEL } from "@/copy";

/**
 * The site's first header (DECISIONS 174): the wordmark and one quiet link to
 * the blog. Deliberately this small — the hero below still offers exactly one
 * CTA, and a header full of destinations would be the page un-deciding what
 * it is for. Styled like the footer's links: colour and underline only, no
 * motion (the motion law's hover rule).
 */
export function Header() {
  return (
    <header className="bg-canvas px-6 py-5 text-ink" data-testid="site-header">
      <div className="mx-auto flex w-full max-w-3xl items-baseline justify-between">
        <a className="text-body font-semibold" href="/">
          {HEADER_WORDMARK}
        </a>
        <nav className="text-body">
          <a className="underline underline-offset-4" href="/blog/" data-testid="nav-blog">
            {NAV_BLOG_LABEL}
          </a>
        </nav>
      </div>
    </header>
  );
}
