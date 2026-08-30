/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * The free-guides register, and the one word that is allowed to break the
 * vocabulary law.
 *
 * `/resources/` is the library's front door. Every asset that ships gets a row
 * on it and a line in `sitemap.xml`, and the surest way for that rule to rot is
 * for it to live only in a handoff note, so it lives here instead: this reads
 * the directory, and a resource page on disk that is missing from either list
 * fails the build.
 *
 * The exception, DECISIONS 195's Google rule: a page built to catch a search
 * MAY carry the searcher's vocabulary in two places and no others. The
 * doorway, meaning the title tag and the meta description. And ONE paragraph
 * in contrast position, naming the category being replaced, never Kettle,
 * marked `class="body contrast"` so the hole is a thing you can see in the
 * markup rather than a habit nobody is counting. The H1, og:title and every
 * other line are our voice.
 *
 * The scan below removes those three and applies the site's normal bans to
 * what is left, then checks the hole itself: at most one contrast paragraph
 * per page, and the doorway still carrying the phrase it exists for.
 */
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "@/App";

const SITE = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const PUBLIC = join(SITE, "public");
const REGISTER = join(PUBLIC, "resources", "index.html");
const SITEMAP = join(PUBLIC, "sitemap.xml");
const ROBOTS = join(PUBLIC, "robots.txt");
const ORIGIN = "https://heykettle.com";

const register = () => readFileSync(REGISTER, "utf8");
const sitemap = () => readFileSync(SITEMAP, "utf8");

/** Every resource page on disk, as the site path each one is served at. */
function resourceSlugs(): string[] {
  return readdirSync(join(PUBLIC, "resources"), { withFileTypes: true })
    .filter((e) => e.isDirectory())
    .map((e) => e.name)
    .sort();
}

/** A page's authored text, with the doorway removed but contrast kept. */
function belowTheDoorway(html: string): string {
  return html
    .replace(/<title>[\s\S]*?<\/title>/i, "")
    .replace(/<meta\s+name="description"[^>]*>/i, "");
}

/** Every paragraph a page has declared as contrast position. */
function contrastParagraphs(html: string): string[] {
  return [...html.matchAll(/<p class="body contrast">([\s\S]*?)<\/p>/g)].map((m) => m[1]);
}

/** What this build must answer for: no doorway, no contrast paragraph. */
function ourVoice(html: string): string {
  return belowTheDoorway(html).replace(/<p class="body contrast">[\s\S]*?<\/p>/g, "");
}

const BANNED = [
  "monitor", "monitoring", "track", "tracking", "surveillance",
  "alert", "alerts", "elderly", "senior", "seniors",
  // Retired by DECISIONS 192; "normal" is the word for this concept.
  "ordinary", "ordinarily",
];

describe("the register lists what actually ships", () => {
  it("has a row for every resource page on disk", () => {
    const html = register();
    const slugs = resourceSlugs();
    expect(slugs.length).toBeGreaterThan(0);
    for (const slug of slugs) {
      expect(html, `/resources/${slug}/ is not listed on the register`).toContain(
        `href="/resources/${slug}/"`,
      );
    }
  });

  it("every row points at a page that exists, with its trailing slash", () => {
    for (const href of [...register().matchAll(/href="\/resources\/([^"/]+)\/"/g)]) {
      expect(
        existsSync(join(PUBLIC, "resources", href[1], "index.html")),
        `the register links /resources/${href[1]}/ but no such page exists`,
      ).toBe(true);
    }
  });

  it("the whole entry is one link, named by its title, with nothing nested", () => {
    const entry = register().match(/<a\s+class="entry"([\s\S]*?)<\/a>/);
    expect(entry, "the entry block link is gone").not.toBeNull();
    expect(entry![1]).toContain('id="guide-1-title"');
    expect(register()).toContain('aria-labelledby="guide-1-title"');
    expect(/<a[\s>]/.test(entry![1]), "an anchor inside the entry anchor").toBe(false);
  });
});

describe("the sitemap covers the site", () => {
  it("lists the homepage, the blog, every post and every resource page", () => {
    const xml = sitemap();
    const expected = [
      `${ORIGIN}/`,
      `${ORIGIN}/blog/`,
      `${ORIGIN}/resources/`,
      ...resourceSlugs().map((s) => `${ORIGIN}/resources/${s}/`),
      ...readdirSync(join(PUBLIC, "blog"), { withFileTypes: true })
        .filter((e) => e.isDirectory())
        .map((e) => `${ORIGIN}/blog/${e.name}/`),
    ];
    for (const loc of expected) {
      expect(xml, `${loc} is missing from sitemap.xml`).toContain(`<loc>${loc}</loc>`);
    }
  });

  it("lists every printable that ships with a resource page", () => {
    const xml = sitemap();
    for (const slug of resourceSlugs()) {
      for (const file of readdirSync(join(PUBLIC, "resources", slug))) {
        if (!file.endsWith(".pdf")) continue;
        expect(xml, `${file} is not in sitemap.xml`).toContain(
          `<loc>${ORIGIN}/resources/${slug}/${file}</loc>`,
        );
      }
    }
  });

  it("names one origin, and names each URL once", () => {
    const locs = [...sitemap().matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
    expect(locs.length).toBeGreaterThan(0);
    for (const loc of locs) expect(loc.startsWith(`${ORIGIN}/`)).toBe(true);
    expect(new Set(locs).size, "a URL is listed twice").toBe(locs.length);
  });

  it("robots.txt points crawlers at it", () => {
    expect(readFileSync(ROBOTS, "utf8")).toContain(`Sitemap: ${ORIGIN}/sitemap.xml`);
  });
});

describe("the resource pages obey the site's laws", () => {
  it("carry no em dash, and no banned word below the search doorway", () => {
    const pages = [REGISTER, ...resourceSlugs().map((s) =>
      join(PUBLIC, "resources", s, "index.html"))];
    for (const path of pages) {
      const html = readFileSync(path, "utf8");
      expect(html, `${path} has an em dash`).not.toContain("—");
      const authored = ourVoice(html);
      for (const word of BANNED) {
        expect(
          new RegExp(`\\b${word}\\b`, "i").test(authored),
          `"${word}" appeared in ${path} below the title and meta description`,
        ).toBe(false);
      }
    }
  });

  it("no page takes more than one paragraph of contrast position", () => {
    for (const path of [REGISTER, ...resourceSlugs().map((s) =>
      join(PUBLIC, "resources", s, "index.html"))]) {
      const found = contrastParagraphs(readFileSync(path, "utf8"));
      expect(found.length, `${path} declares ${found.length} contrast paragraphs`)
        .toBeLessThanOrEqual(1);
      // Contrast names the category being replaced. It never names us.
      for (const p of found) expect(/kettle/i.test(p), "contrast names Kettle").toBe(false);
    }
  });

  it("the exemption is load-bearing, and confined to the doorway and contrast", () => {
    // If the checklist page's title stopped carrying the search phrase, the
    // scans above would be passing on a page that no longer needs the hole.
    const html = readFileSync(
      join(PUBLIC, "resources", "okay-living-alone", "index.html"), "utf8");
    expect(/<title>[^<]*elderly/i.test(html), "the title lost the search phrase").toBe(true);
    expect(contrastParagraphs(html).length, "the contrast paragraph is gone").toBe(1);
    expect(/\belderly\b/i.test(contrastParagraphs(html)[0])).toBe(true);
    // Everything this build says in its own voice stays clean.
    expect(/\belderly\b/i.test(ourVoice(html))).toBe(false);
    // og:title is what a person sees when the page is shared: our voice.
    expect(/<meta property="og:title"[^>]*elderly/i.test(html)).toBe(false);
    expect(/<h1[^>]*>[^<]*elderly/i.test(html)).toBe(false);
  });

  it("stand alone: no scripts, no stylesheets, no absolute URLs", () => {
    const pages = [REGISTER, ...resourceSlugs().map((s) =>
      join(PUBLIC, "resources", s, "index.html"))];
    for (const path of pages) {
      const html = readFileSync(path, "utf8");
      expect(html, path).not.toMatch(/<script/i);
      expect(html, path).not.toMatch(/<link/i);
      expect(html, path).not.toMatch(/https?:\/\//i);
    }
  });
});

describe("the way in", () => {
  it("the footer carries the free-guides link", () => {
    render(<App />);
    const link = screen.getByTestId("footer-resources");
    expect(link.getAttribute("href")).toBe("/resources/");
    expect(link.textContent).toBe("Free guides");
  });

  it("the blog index offers it too", () => {
    expect(readFileSync(join(PUBLIC, "blog", "index.html"), "utf8")).toContain(
      'href="/resources/"',
    );
  });
});
