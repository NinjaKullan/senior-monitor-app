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

  it("both pages stand alone: no scripts, no stylesheets, no absolute URLs", () => {
    for (const html of [article(), index()]) {
      expect(html).not.toMatch(/<script/i);
      expect(html).not.toMatch(/<link/i);
      expect(html).not.toMatch(/https?:\/\//i);
    }
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
