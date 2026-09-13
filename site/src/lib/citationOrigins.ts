/**
 * The only origins a static page may link to (seo-backlog D3, founder ruling
 * 2026-09-13). The standalone-page posture bans absolute URLs because the
 * page must fetch nothing; an anchor fetches nothing until a reader clicks
 * it, so a citation link to a public-sector source is admitted, and nothing
 * else is. Public sector only: a link here is a citation, never an
 * endorsement, and no vendor ever appears. blog.test.tsx and
 * resources.test.tsx strip these anchors before the flat bans run, so a
 * foreign stylesheet, script, image or any other host still fails.
 */
export const CITATION_ORIGINS = [
  "https://www.nia.nih.gov/",
  "https://www.cdc.gov/",
  "https://www.consumerfinance.gov/",
  "https://www.fema.gov/",
  "https://www.usfa.fema.gov/",
  "https://eldercare.acl.gov/",
  "https://acl.gov/",
  "https://www.medicare.gov/",
] as const;

/** Matches one citation anchor and nothing else: an allowed origin, a path,
 *  no attributes before href, no rel, no target. */
export const CITATION_ANCHOR = new RegExp(
  `<a href="(?:${CITATION_ORIGINS.map((o) => o.replace(/[.]/g, "\\.")).join("|")})[^"\\s]*">`,
  "g",
);
