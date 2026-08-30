/**
 * @vitest-environment node
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146):
 * pure file checks, no DOM — node says so out loud.
 */
/**
 * The favicon set (Asana 1217835128977059) — derived, declared, and sized.
 *
 * Everything here is a file check on purpose: the set is committed output of
 * `scripts/make-favicons.py` (a crop of the hero's own drawing, never
 * regenerated artwork), and the failure this suite exists for is the quiet
 * one — a head tag pointing at a file that is not there, which every browser
 * swallows as a silent 404 and a blank tab icon. Legibility at 16px is NOT
 * asserted here; jsdom renders nothing, so that check is a screenshot of the
 * real render, judged by a person (the task's own instruction).
 */
import { existsSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const SITE = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const PUBLIC = join(SITE, "public");
const HEAD = readFileSync(join(SITE, "index.html"), "utf8");

/** The set, by name — a manifest, like the illustrations'. */
const SET = [
  "favicon.ico",
  "favicon.svg",
  "favicon-16.png",
  "favicon-32.png",
  "apple-touch-icon.png",
  "og-image.png",
];

/** Width and height out of a PNG's IHDR — the first chunk, fixed offsets. */
function pngSize(path: string): [number, number] {
  const bytes = readFileSync(path);
  expect(bytes.subarray(0, 8).toString("latin1")).toBe("\x89PNG\r\n\x1a\n");
  return [bytes.readUInt32BE(16), bytes.readUInt32BE(20)];
}

describe("the files themselves", () => {
  it("are all present, and none is an accidental heavyweight", () => {
    for (const name of SET) {
      const path = join(PUBLIC, name);
      expect(existsSync(path), `${name} is missing`).toBe(true);
      expect(statSync(path).size, `${name} is empty`).toBeGreaterThan(200);
    }
    // The icons ride every page load; the share card is fetched by scrapers.
    // Loose ceilings, tripped only by a mistake like an uncropped source.
    expect(statSync(join(PUBLIC, "favicon.ico")).size).toBeLessThan(40_000);
    expect(statSync(join(PUBLIC, "og-image.png")).size).toBeLessThan(600_000);
  });

  it("packs the ico with exactly the three tab sizes", () => {
    const bytes = readFileSync(join(PUBLIC, "favicon.ico"));
    // ICONDIR: reserved 0, type 1, then one ICONDIRENTRY per image whose
    // first two bytes are width and height (0 meaning 256).
    expect(bytes.readUInt16LE(0)).toBe(0);
    expect(bytes.readUInt16LE(2)).toBe(1);
    const count = bytes.readUInt16LE(4);
    const sizes = Array.from({ length: count }, (_, i) => bytes[6 + i * 16]).sort(
      (a, b) => a - b,
    );
    expect(sizes).toEqual([16, 32, 48]);
  });

  it("sizes the pngs to their jobs", () => {
    expect(pngSize(join(PUBLIC, "favicon-16.png"))).toEqual([16, 16]);
    expect(pngSize(join(PUBLIC, "favicon-32.png"))).toEqual([32, 32]);
    // Apple's documented size; opaque by construction (the generator flattens
    // onto the canvas token, because iOS turns transparency into black).
    expect(pngSize(join(PUBLIC, "apple-touch-icon.png"))).toEqual([180, 180]);
    // The og card's declared dimensions and its real ones must be one fact.
    const [w, h] = pngSize(join(PUBLIC, "og-image.png"));
    expect(HEAD).toContain(`<meta property="og:image:width" content="${w}" />`);
    expect(HEAD).toContain(`<meta property="og:image:height" content="${h}" />`);
    expect([w, h]).toEqual([1200, 630]);
  });

  it("keeps the svg glyph inert: no script, no fetch, no foreign origin", () => {
    const raw = readFileSync(join(PUBLIC, "favicon.svg"), "utf8");
    expect(raw).toContain('viewBox="0 0 32 32"');
    // The xmlns namespace URI is an identifier, never fetched — stripped so
    // the ban below is about things that actually load.
    const svg = raw.replace(/xmlns(:[a-z]+)?="[^"]*"/g, "");
    for (const banned of ["<script", "onload", "href=", "http", "url("]) {
      expect(svg.toLowerCase(), `svg carries ${banned}`).not.toContain(banned);
    }
    // The dark-scheme block (founder-observed: a dark kettle on a dark tab
    // bar is invisible, and the SVG is the one icon a browser re-styles with
    // the bar). Pinned so a later tidy-up cannot drop it.
    expect(raw).toContain("@media (prefers-color-scheme: dark)");
  });
});

describe("the head declares the set", () => {
  it("links every icon, and every link resolves to a real file", () => {
    for (const tag of [
      '<link rel="icon" href="/favicon.ico" sizes="48x48" />',
      '<link rel="icon" type="image/svg+xml" href="/favicon.svg" />',
      '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png" />',
      '<link rel="apple-touch-icon" href="/apple-touch-icon.png" />',
      '<meta property="og:image" content="https://heykettle.com/og-image.png" />',
    ]) {
      expect(HEAD).toContain(tag);
    }
    // The silent-404 check: every root-relative href/content path the head
    // names must exist in public/, whatever tags get added later.
    for (const [, path] of HEAD.matchAll(/(?:href|content)="(?:https:\/\/heykettle\.com)?(\/[\w.-]+\.(?:ico|svg|png|webp))"/g)) {
      expect(existsSync(join(PUBLIC, path.slice(1))), `${path} is a 404`).toBe(true);
    }
  });

  it("gives the share card the canonical origin, not a foreign one", () => {
    // Scrapers resolve nothing, so the URL is absolute — and it must be the
    // same origin the canonical link names, or the card outlives a domain.
    const og = HEAD.match(/property="og:image" content="([^"]+)"/)![1];
    const canonical = HEAD.match(/rel="canonical" href="([^"]+)"/)![1];
    expect(og.startsWith(canonical)).toBe(true);
  });

  it("stays out of privacy.html, which fetches nothing by law", () => {
    // DECISIONS 142: that page carries no <link> and no absolute URL at all,
    // so the icon set must never be wired into it.
    const privacy = readFileSync(join(PUBLIC, "privacy.html"), "utf8");
    expect(privacy).not.toContain("favicon");
    expect(privacy).not.toContain("og:image");
  });
});
