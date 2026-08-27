/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * The illustration set (DECISIONS 136).
 *
 * The site's imagery moved from photographs to one drawn set, on two
 * independent reviewer reports about authenticity. The swap is easy to do
 * halfway — a retired file left in `public/`, a path still pointing at one, a
 * new image that quietly loads eagerly and pushes the hero down the page — so
 * what is asserted here is the *set*, not any one picture: every image the page
 * renders comes from it, nothing references a retired name, and the loading
 * discipline the hero depends on is unchanged.
 *
 * The matching tree-side assertion (public/ holds these six and nothing else)
 * lives in product/tests/test_site_caching.py, because it is also the premise
 * the cache contract rests on.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "@/App";
import { HOW_STRIP_ALT } from "@/copy";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..");

/** The set, by name. A seventh image is a decision, not a detail — and this
 *  one was made: the kettle mark (DECISIONS 187), which is not an
 *  illustration at all but the brand's own object, living above the kicker.
 *  It is the sole member of DECORATIVE below, and everything the set asserts
 *  about alt text and loading is asserted about it separately rather than
 *  waived. */
const SET = [
  "/hero-two-cities.webp",
  "/ill-her-afternoon.webp",
  "/ill-her-morning.webp",
  "/ill-somethings-off.webp",
  "/ill-story-strip.webp",
  "/ill-what-you-see.webp",
  "/kettle-hero.webp",
];

/** Images that carry no meaning and must therefore carry no alt text. One
 *  entry, by name: a decorative image is an exemption from the alt-text rule,
 *  so the list of them is the exemption, and it is written out. */
const DECORATIVE = ["/kettle-hero.webp"];

/** The photographs this set replaced, by every name they went by. */
const RETIRED = [
  "hero-morning.webp",
  "hero-evening.webp",
  "section-her-morning.webp",
  "section-her-afternoon.webp",
  "section-somethings-off.webp",
  "section-what-you-see.webp",
];

/** Ships to the browser — the tests are excluded, since this file names every
 *  retired photograph in order to look for them. */
function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) return path.includes("/tests") ? [] : sourceFiles(path);
    return /\.(tsx?|css)$/.test(path) ? [path] : [];
  });
}

describe("the illustration set", () => {
  it("is every image the page renders, and nothing else", () => {
    const { container } = render(<App />);
    const sources = Array.from(container.querySelectorAll("img"))
      .map((image) => image.getAttribute("src") ?? "")
      .sort();
    expect(sources).toEqual(SET);
  });

  it("gives every image alt text that is actually written", () => {
    const { container } = render(<App />);
    for (const image of Array.from(container.querySelectorAll("img"))) {
      const src = image.getAttribute("src") ?? "";
      const alt = image.getAttribute("alt") ?? "";
      if (DECORATIVE.includes(src)) continue;
      expect(alt.length, `${src} has no alt text`).toBeGreaterThan(20);
    }
  });

  it("makes the decorative image say so in both of the ways that matter", () => {
    // Half-done decoration is worse than none: an empty alt with no
    // aria-hidden still lands in the accessibility tree as an unlabelled
    // graphic, and aria-hidden with alt text is a contradiction the screen
    // reader resolves by ignoring the picture anyway. Both, or it is not
    // decorative.
    const { container } = render(<App />);
    for (const src of DECORATIVE) {
      const image = container.querySelector(`img[src="${src}"]`)!;
      expect(image, `${src} is not on the page`).not.toBeNull();
      expect(image.getAttribute("alt")).toBe("");
      expect(image.getAttribute("aria-hidden")).toBe("true");
    }
  });

  it("names no retired photograph anywhere in the source", () => {
    // The half-done swap this test exists for: a path left behind still
    // resolves to a 404 rather than to a picture, and nothing else notices.
    const offenders: string[] = [];
    for (const file of sourceFiles(SRC)) {
      const source = readFileSync(file, "utf8");
      for (const name of RETIRED) {
        if (source.includes(name)) offenders.push(`${file.slice(SRC.length + 1)}: ${name}`);
      }
    }
    expect(offenders).toEqual([]);
  });

  it("keeps the hero eager and everything below it lazy", () => {
    // The rule the page's first paint depends on: one eager image, and it is
    // the hero's. A lazily-loaded hero pops in; an eagerly-loaded strip
    // competes with it for the same first bytes.
    const { container } = render(<App />);
    const eager = Array.from(container.querySelectorAll("img")).filter(
      (image) => image.getAttribute("loading") !== "lazy",
    );
    // Two now, and both above the fold in the same section: the kettle mark
    // is eager for the same reason the illustration is — it is in the first
    // paint, and at 61KB a lazy one would pop in over the kicker (DECISIONS
    // 187). A third eager image anywhere is the rule breaking.
    expect(eager.map((image) => image.getAttribute("src"))).toEqual([
      "/kettle-hero.webp",
      "/hero-two-cities.webp",
    ]);
    for (const image of eager) {
      expect(image.closest("section")!.getAttribute("id")).toBe("hero");
    }
  });
});

describe("the narrative strip", () => {
  it("opens the how-it-works section, after its heading and before the steps", () => {
    render(<App />);
    const strip = screen.getByTestId("story-strip");
    const section = strip.closest("section")!;
    const heading = section.querySelector('[data-testid="section-heading"]')!;
    const steps = section.querySelector("ol")!;

    // Heading, then the picture, then the mechanism. Every section on this
    // page starts with its heading; an image that outranked one would be the
    // first exception to that, so the strip opens the section's *body*.
    expect(
      heading.compareDocumentPosition(strip) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(strip.compareDocumentPosition(steps) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("is decorative narrative: no copy of its own beyond its alt text", () => {
    render(<App />);
    const strip = screen.getByTestId("story-strip");
    expect(strip.getAttribute("alt")).toBe(HOW_STRIP_ALT);
    expect(strip.getAttribute("loading")).toBe("lazy");
    // Full content width at the artwork's own ratio, so the four panels are
    // never cropped to three and a sliver.
    expect(strip.className).toContain("w-full");
    expect(strip.className).toContain("aspect-[1600/686]");
  });
});
