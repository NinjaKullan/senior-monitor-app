/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * The blog (DECISIONS 174), and the one law that is different here.
 *
 * The post body is the founder's final draft and ships VERBATIM from
 * docs/blog-post-1-draft.md — it is exempt from every edit, including the
 * copy scans, because it is a person telling their own story in their own
 * words. Everything AROUND it is chrome this build authored, and chrome gets
 * the site's rules: no monitor/track/alert/elderly/seniors vocabulary, no em
 * dashes, and the privacy page's standalone posture — no scripts, no
 * stylesheets, no absolute URLs, nothing fetched.
 *
 * The verbatim claim is asserted structurally: the article's sentinel-marked
 * body is extracted and compared paragraph-for-paragraph against the draft's
 * body section, so a trimmed sentence, a "improved" word, or a paragraph
 * quietly dropped fails by diff — and the Editor's notes must not travel.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "@/App";

const SITE = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const DRAFT = join(SITE, "..", "docs", "blog-post-1-draft.md");
const INDEX = join(SITE, "public", "blog", "index.html");
const ARTICLE = join(
  SITE,
  "public",
  "blog",
  "the-call-ive-rehearsed-and-never-made",
  "index.html",
);

const TITLE = "The call I've rehearsed and never made";
const TEASER = "On the phone call every far-away child rehearses, and never wants to make.";
const DESCRIPTION =
  "My parents live in Chennai and I live in the US. This is about the call I hope I never have to make.";
const BYLINE = "Hema · Founder, HeyKettle";
const DATE = "August 26, 2026";

const article = () => readFileSync(ARTICLE, "utf8");
const index = () => readFileSync(INDEX, "utf8");

/** The draft's body: the section between the two `---` rules, by paragraph. */
function draftParagraphs(): string[] {
  const sections = readFileSync(DRAFT, "utf8").split("\n---\n");
  expect(sections, "draft shape changed — re-check what counts as the body").toHaveLength(3);
  return sections[1]
    .split("\n\n")
    .map((p) => p.trim())
    .filter(Boolean);
}

/** The article's body, from between the verbatim sentinels, by paragraph. */
function articleParagraphs(): string[] {
  const match = article().match(
    /<!-- post-body:verbatim:start[^>]*-->([\s\S]*?)<!-- post-body:verbatim:end -->/,
  );
  expect(match, "the verbatim sentinels are load-bearing — do not remove them").not.toBeNull();
  return [...match![1].matchAll(/<p class="body">([\s\S]*?)<\/p>/g)].map((m) => m[1].trim());
}

/** Both pages with the exempt body removed: everything this build authored. */
function chrome(): string {
  return (
    article().replace(
      /<!-- post-body:verbatim:start[^>]*-->[\s\S]*?<!-- post-body:verbatim:end -->/,
      "",
    ) + index()
  );
}

describe("post #1 ships verbatim (DECISIONS 174)", () => {
  it("is the draft's body, paragraph for paragraph, nothing edited or dropped", () => {
    const fromDraft = draftParagraphs();
    expect(fromDraft.length).toBeGreaterThanOrEqual(10);
    expect(articleParagraphs()).toEqual(fromDraft);
  });

  it("carries the exact title and none of the editor's apparatus", () => {
    const html = article();
    expect(html).toContain(`<h1>${TITLE}</h1>`);
    expect(html).toContain(`<title>${TITLE} · HeyKettle</title>`);
    expect(html).not.toContain("Editor's notes");
    // The title-options block must not travel either.
    expect(html).not.toContain("Alternate 1");
    expect(html).not.toContain("Working title");
  });

  it("carries the byline, the date, and the head tags as ruled", () => {
    const html = article();
    expect(html).toContain(BYLINE);
    expect(html).toContain(DATE);
    expect(html).toContain(`<meta name="description" content="${DESCRIPTION}" />`);
    expect(html).toContain(`<meta property="og:title" content="${TITLE}" />`);
    expect(html).toContain(`<meta property="og:description" content="${DESCRIPTION}" />`);
    expect(html).toContain(`<meta property="og:type" content="article" />`);
    // No og:image for now — an empty or placeholder one is worse than none.
    expect(html).not.toContain("og:image");
  });

  it("lists the post on /blog/ with title, date and the ruled teaser", () => {
    const html = index();
    expect(html).toContain(TITLE);
    expect(html).toContain(DATE);
    expect(html).toContain(TEASER);
    // The link carries the trailing slash so no reader pays the 301.
    expect(html).toContain('href="/blog/the-call-ive-rehearsed-and-never-made/"');
  });

  /**
   * DECISIONS 175: the founder read the entry as static text ("I had to
   * think about where the entire article was"), so the whole block became
   * the link. These pins hold the affordance, not just the destination.
   */
  it("the whole entry is one link to the article, named by the title", () => {
    // Located by href rather than by position: the index gained a second
    // entry (the first guide-genre post), and this pin is about post #1's
    // block, wherever it sits in the list.
    const entry = index()
      .match(/<a\s+class="entry"[\s\S]*?<\/a>/g)
      ?.find((e) => e.includes('href="/blog/the-call-ive-rehearsed-and-never-made/"'))
      ?.match(/([\s\S]*)/);
    expect(entry, "the entry block link is gone").not.toBeNull();
    expect(entry![0]).toContain('href="/blog/the-call-ive-rehearsed-and-never-made/"');
    // Title, date, teaser and the read line all ride inside the one anchor.
    expect(entry![0]).toContain(TITLE);
    expect(entry![0]).toContain(DATE);
    expect(entry![0]).toContain(TEASER);
    expect(entry![0]).toContain("Read the post →");
    // The accessible name is the post title, via the labelledby pair.
    expect(entry![0]).toContain('aria-labelledby="post-1-title"');
    expect(entry![0]).toContain('id="post-1-title"');
  });

  it("nests no link inside any entry link", () => {
    const entries = [...index().matchAll(/<a\s+class="entry"([\s\S]*?)<\/a>/g)];
    expect(entries.length).toBeGreaterThanOrEqual(1);
    for (const e of entries) {
      expect(/<a[\s>]/.test(e[1]), "an anchor inside an entry anchor").toBe(false);
    }
  });

  it("reads as clickable at rest, not only on hover", () => {
    const html = index();
    // The title carries the site's link treatment before the mouse moves,
    // and the block declares its hover and focus states.
    expect(html).toMatch(/\.entry-title\s*\{[^}]*text-decoration:\s*underline/);
    expect(html).toMatch(/a\.entry:hover\s*\{[^}]*background/);
    expect(html).toMatch(/a\.entry:focus-visible\s*\{[^}]*outline/);
    expect(html).toMatch(/a\.entry\s*\{[^}]*cursor:\s*pointer/);
  });
});

describe("the chrome obeys the site's laws — the body alone is exempt", () => {
  it("authored chrome carries no em dash and none of the banned vocabulary", () => {
    const authored = chrome();
    expect(authored).not.toContain("—");
    for (const word of ["monitor", "monitoring", "track", "tracking", "alert", "elderly", "senior", "seniors"]) {
      expect(
        new RegExp(`\\b${word}\\b`, "i").test(authored),
        `"${word}" appeared in blog chrome`,
      ).toBe(false);
    }
  });

  /**
   * The posture, with the one hole canonicals opened.
   *
   * Blog pages now carry `<link rel="canonical">` (PM ruling, 2026-08-30:
   * canonicals are policy for the homepage and blog pages; resource pages
   * stay bare). That is a `<link` and an absolute URL, so the flat bans this
   * assertion used to make would fail on a page that is correct. The bans
   * are therefore narrowed rather than dropped: the canonical is removed
   * first, and everything else must still hold. A second `<link`, a script,
   * or any other absolute URL still fails, and the canonical itself is
   * checked for shape and origin below.
   */
  const CANONICAL = /<link rel="canonical" href="https:\/\/heykettle\.com\/[^"]*" \/>/;

  it("both pages stand alone: no scripts, no stylesheets, no other absolute URLs", () => {
    for (const html of [article(), index()]) {
      const rest = html.replace(CANONICAL, "");
      expect(rest).not.toMatch(/<script/i);
      expect(rest).not.toMatch(/<link/i);
      expect(rest).not.toMatch(/https?:\/\//i);
    }
  });

  it("the article's canonical names its own URL, and the index has none", () => {
    const found = article().match(CANONICAL);
    expect(found, "the post lost its canonical").not.toBeNull();
    expect(found![0]).toContain(
      'href="https://heykettle.com/blog/the-call-ive-rehearsed-and-never-made/"',
    );
    // One canonical, not two.
    expect(article().match(/rel="canonical"/g)!.length).toBe(1);
    // The register page is not a canonical target; it stays bare.
    expect(index()).not.toMatch(/rel="canonical"/);
  });

  it("the exemption is load-bearing: the body would fail the chrome scan", () => {
    // The founder's story says "fall" and "worried" because people do; the
    // scan must be catching the body's absence, not passing on a lax rule.
    const withBody = article();
    expect(/\bworried\b/i.test(withBody)).toBe(true);
    expect(/\bworried\b/i.test(chrome())).toBe(false);
  });
});

describe("the way in", () => {
  it("the header and footer both carry the Blog link", () => {
    render(<App />);
    expect(screen.getByTestId("nav-blog").getAttribute("href")).toBe("/blog/");
    expect(screen.getByTestId("nav-blog").textContent).toBe("Blog");
    expect(screen.getByTestId("footer-blog").getAttribute("href")).toBe("/blog/");
  });
});
