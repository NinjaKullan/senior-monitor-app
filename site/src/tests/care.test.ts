/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146).
 */
/**
 * /care, the Care Compare page (spec 021 §7; DECISIONS 341 to 344).
 *
 * The strings are §10's PAGE_* and are read out of the spec itself, so the
 * ruling has one copy: an edited word on either side fails here. care/copy.py
 * is pinned to the same section by care/tests/test_copy.py.
 *
 * The page is a static document under the /resources/ posture, with one
 * difference written down here rather than left to be discovered: it carries
 * one inline script, for the Copy button, which reads the address off the page
 * and writes it to the clipboard. It has no src, fetches nothing, and with
 * scripts off the button stays hidden and the address is text to select. The
 * connector address is printed, never loaded and never an anchor: the page is
 * the link target, the address is not (§7).
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { HERO_H1 } from "@/copy";
import { BANNED, CULTURE_CODED } from "./copyBans";

// process.cwd() is site/ under vitest (environment.test.ts says why).
const SITE = process.cwd();
const PAGE = join(SITE, "public", "care", "index.html");
const SPEC = join(SITE, "..", "specs", "021-care-compare.md");
const ADDRESS = "https://care.heykettle.com/mcp";
/** Amendment A.1: the care app's search page, the one link to the care host. */
const SEARCH = "https://care.heykettle.com/search";

const html = () => readFileSync(PAGE, "utf8");

/** The PAGE_* strings in one stretch of the spec. */
function pageStringsBetween(start: string, stop: string): Record<string, string> {
  const section = readFileSync(SPEC, "utf8").split(start)[1].split(stop)[0];
  const found: Record<string, string> = {};
  for (const [, name, value] of section.matchAll(/\b(PAGE_[A-Z0-9_]+) = "([^"]*)"/g)) {
    found[name] = value;
  }
  return found;
}

/** Amendment A.5's two, retired by Amendment B.1. */
const retired = () => pageStringsBetween("\n### A.5", "\n### A.6");
/** Amendment B.3's two, verbatim. */
const amendmentB = () => pageStringsBetween("\n### B.3", "\n### B.4");

/** The page's strings today, straight from the spec: §10's, with PAGE_HOW
 *  replaced by PAGE_HOW_SECOND, and B.3's button (Amendment B.1). */
function pageStrings(): Record<string, string> {
  const found = pageStringsBetween("\n## 10.", "\n## Amendment A");
  const replaced = found.PAGE_HOW;
  delete found.PAGE_HOW;
  expect(replaced, "§10 lost PAGE_HOW; re-read Amendment B").toBeTruthy();
  return { ...found, ...amendmentB() };
}

/** What a reader sees: the body's text, the script left out. */
function readable(): string {
  const doc = new DOMParser().parseFromString(html(), "text/html");
  doc.querySelectorAll("script, style").forEach((n) => n.remove());
  return (doc.body.textContent ?? "").replace(/\s+/g, " ");
}

describe("the /care page says §10, verbatim", () => {
  it("carries every PAGE_ string", () => {
    const strings = pageStrings();
    expect(Object.keys(strings).sort()).toEqual([
      "PAGE_ADDRESS", "PAGE_COPIED", "PAGE_COPY", "PAGE_EXAMPLES_HEAD", "PAGE_EXAMPLE_1",
      "PAGE_EXAMPLE_2", "PAGE_EXAMPLE_3", "PAGE_HOW_SECOND", "PAGE_KETTLE", "PAGE_KETTLE_LINK",
      "PAGE_LEDE", "PAGE_SEARCH_BUTTON", "PAGE_SOURCE", "PAGE_TITLE",
    ]);
    expect(amendmentB()).toEqual({
      PAGE_SEARCH_BUTTON: "Search near a ZIP code",
      PAGE_HOW_SECOND: "Or add it to Claude, ChatGPT, or another assistant as a connector, "
        + "once, with this address. Then ask in your own words.",
    });
    const text = readable();
    const page = html();
    for (const [name, value] of Object.entries(strings)) {
      if (name === "PAGE_KETTLE") continue;
      if (name === "PAGE_COPIED") {
        // Said by the button after a copy; it lives in the script.
        expect(page, name).toContain(`button.textContent = "${value}"`);
        continue;
      }
      expect(text, name).toContain(value);
    }
    // "{tagline}" is the site's own: the hero line, which is also the title.
    const kettle = strings.PAGE_KETTLE.replace("{tagline}", HERO_H1);
    expect(text).toContain(`${kettle} ${strings.PAGE_KETTLE_LINK}`);
  });

  it("puts them where §7 says", () => {
    const page = html();
    const strings = pageStrings();
    expect(page).toContain(`<title>${strings.PAGE_TITLE}</title>`);
    expect(page).toContain(`<h1>${strings.PAGE_TITLE}</h1>`);
    expect(page).toContain(`<h2>${strings.PAGE_EXAMPLES_HEAD}</h2>`);
    expect(page).toContain(`<code id="care-address">${strings.PAGE_ADDRESS}</code>`);
    expect(page).toContain(`<button type="button" id="care-copy" hidden>${strings.PAGE_COPY}</button>`);
    expect(page).toContain(`<a href="/">${strings.PAGE_KETTLE_LINK}</a>`);
    // Amendment B.1: the search is a button-styled link, the primary action.
    expect(page).toContain(
      `<p class="search"><a class="search" href="${SEARCH}">${strings.PAGE_SEARCH_BUTTON}</a></p>`,
    );
    // The doorway says the lede; no new copy was written for it.
    expect(page).toContain(`<meta name="description" content="${strings.PAGE_LEDE}" />`);
    // Order (Amendment B.1): lede, the search, the assistant path second,
    // the address, where the numbers come from, the examples, Kettle.
    const at = (s: string) => page.indexOf(s);
    const order = [`<p class="body">${strings.PAGE_LEDE}`, `<p class="search">`,
      strings.PAGE_HOW_SECOND, `id="care-address"`, strings.PAGE_SOURCE,
      strings.PAGE_EXAMPLE_1, strings.PAGE_EXAMPLE_3, strings.PAGE_KETTLE_LINK].map((s) => at(`${s}`));
    expect(order.every((n) => n > 0)).toBe(true);
    expect([...order].sort((x, y) => x - y)).toEqual(order);
  });

  it("puts the search first: the first link after the lede (B.4.1)", () => {
    const page = html();
    const strings = pageStrings();
    const afterLede = page.split(`${strings.PAGE_LEDE}</p>`)[1];
    const first = afterLede.match(/<a\b[^>]*>([^<]*)<\/a>/);
    expect(first, "no link after the lede").not.toBeNull();
    expect(first![0]).toBe(`<a class="search" href="${SEARCH}">${strings.PAGE_SEARCH_BUTTON}</a>`);
  });

  it("retires A.5's footnote and §10's PAGE_HOW (Amendment B.1)", () => {
    const text = readable();
    const retiredStrings = retired();
    expect(Object.keys(retiredStrings).sort()).toEqual(["PAGE_SEARCH_LINE", "PAGE_SEARCH_LINK"]);
    expect(text).not.toContain(retiredStrings.PAGE_SEARCH_LINE);
    expect(text).not.toContain(retiredStrings.PAGE_SEARCH_LINK);
    const old = pageStringsBetween("\n## 10.", "\n## Amendment A").PAGE_HOW;
    expect(text).not.toContain(old);
  });

  it("styles the search as the primary action: Copy's look, 44px, full width on a phone", () => {
    const css = html().match(/<style>([\s\S]*?)<\/style>/)![1];
    const rule = css.match(/\n\s*a\.search \{([^}]*)\}/)![1];
    const copy = css.match(/\.address button \{([^}]*)\}/)![1];
    for (const decl of ["min-height: 44px", "background: #403c36", "color: #f6f2ec",
      "border: 1px solid #403c36", "border-radius: 999px"]) {
      expect(copy, `Copy lost ${decl}`).toContain(decl);
      expect(rule, decl).toContain(decl);
    }
    expect(rule).toContain("width: 100%");
    // Only past a phone's width does it size to its words.
    expect(css).toMatch(/@media \(min-width: 30rem\) \{\s*a\.search \{ display: inline-flex; width: auto; \}/);
    // Hover is colour only (the motion law).
    expect(css).toContain("a.search:hover { background: #2b2824; }");
  });

  it("has no other copy of its own beyond the site's nav", () => {
    const strings = Object.values(pageStrings()).map((s) =>
      s.replace("{tagline}", HERO_H1));
    let rest = readable();
    for (const s of [...strings].sort((x, y) => y.length - x.length)) rest = rest.split(s).join(" ");
    expect(rest.split(/\s+/).filter(Boolean)).toEqual(["Kettle", "Blog", "Free", "guides"]);
  });
});

describe("the /care page fetches nothing", () => {
  it("prints the address and never loads it or links it", () => {
    const page = html();
    expect(page.split(ADDRESS).length - 1).toBe(1);
    // One href to the care host, the search page; nothing loaded from it.
    const toCare = [...page.matchAll(/(src|href|action|srcset|data)="https:\/\/care\.heykettle\.com[^"]*"/g)]
      .map((m) => m[0]);
    expect(toCare).toEqual([`href="${SEARCH}"`]);
  });

  it("carries one inline script, which reads the page and writes the clipboard, and nothing else", () => {
    const scripts = [...html().matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)];
    expect(scripts).toHaveLength(1);
    const [, attributes, commented] = scripts[0];
    expect(attributes.trim()).toBe("");
    const body = commented.replace(/\/\*[\s\S]*?\*\//g, "");
    for (const reach of ["fetch", "XMLHttpRequest", "sendBeacon", "import(", "WebSocket",
      "EventSource", "new Image", "createElement", "innerHTML", "localStorage", "cookie"]) {
      expect(body, reach).not.toContain(reach);
    }
    expect(body).toContain("navigator.clipboard.writeText");
  });

  it("no image, no stylesheet, and no absolute URL but its canonical, the address and search", () => {
    const page = html()
      .replace('<link rel="canonical" href="https://heykettle.com/care/" />', "")
      .replace(ADDRESS, "")
      .replace(`<a class="search" href="${SEARCH}">`, "<a>");
    expect(page).not.toMatch(/<img|<link|<iframe|<video|<audio|<source/i);
    expect(page).not.toMatch(/https?:\/\//i);
  });
});

describe("the /care page obeys the copy law", () => {
  it("no em dash, no banned word, no culture-coded word", () => {
    expect(html()).not.toContain("—");
    const lowered = readable().toLowerCase();
    for (const word of [...BANNED, ...CULTURE_CODED]) {
      const escaped = word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      expect(new RegExp(`\\b${escaped}\\b`).test(lowered), word).toBe(false);
    }
  });

  it("never names a verdict: it does not pick", () => {
    for (const word of ["best", "better", "worse", "top", "safe", "recommend", "avoid"]) {
      expect(new RegExp(`\\b${word}\\b`, "i").test(readable()), word).toBe(false);
    }
  });

  it("is in the sitemap, at its trailing-slash address", () => {
    const sitemap = readFileSync(join(SITE, "public", "sitemap.xml"), "utf8");
    expect(sitemap).toContain("<loc>https://heykettle.com/care/</loc>");
  });
});
