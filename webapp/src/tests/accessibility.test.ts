/**
 * @vitest-environment node
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146).
 */
/**
 * Spec 009 §6 as law, not intention.
 *
 * jsdom lays nothing out, so 200% zoom is verified the way the site verifies
 * mobile: by construction plus a source pin — every font size in the spec-009
 * surfaces is in rem, so browser zoom and user font-size preferences scale
 * the type; a hardcoded pixel size fails here by name. Contrast is computed
 * from kettle.css's own token values, both palettes, for exactly the
 * ink-on-surface pairs the screens use — the comments in that file are not
 * trusted, the arithmetic is (the tokens.test.ts discipline, ported).
 */
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const KETTLE_CSS = readFileSync("src/kettle.css", "utf8");

/** The spec-009 surfaces: every typography declaration in them is in rem. */
const REM_LAW_FILES = [
  "src/screens/Today.tsx",
  "src/screens/ParentDetail.tsx",
  "src/screens/Family.tsx",
  "src/components/DayArc.tsx",
  "src/components/RecentDots.tsx",
  "src/components/NotesPanel.tsx",
  "src/components/CityPicker.tsx",
];

describe("all typography in rem (spec 009 §6)", () => {
  it("declares no numeric fontSize in any spec-009 surface", () => {
    const offenders: string[] = [];
    for (const file of REM_LAW_FILES) {
      const source = readFileSync(file, "utf8");
      // A numeric fontSize is pixels to React; only rem strings pass.
      for (const match of source.matchAll(/fontSize:\s*([^,}\n]+)/g)) {
        const value = match[1].trim();
        if (!/^"[\d.]+rem"$/.test(value)) offenders.push(`${file}: fontSize: ${value}`);
      }
    }
    expect(offenders).toEqual([]);
  });
});

/** Token parsing: the Day set from `body {` and Night from `body[data-kt`. */
function tokenSet(block: string): Record<string, string> {
  const tokens: Record<string, string> = {};
  for (const match of block.matchAll(/(--[a-z0-9-]+):\s*([^;]+);/g)) {
    tokens[match[1]] = match[2].trim();
  }
  return tokens;
}

function blocks(): { day: Record<string, string>; night: Record<string, string> } {
  // lastIndexOf: the header comment mentions the selector too.
  const nightStart = KETTLE_CSS.lastIndexOf('body[data-kt="night"]');
  return {
    day: tokenSet(KETTLE_CSS.slice(0, nightStart)),
    night: tokenSet(KETTLE_CSS.slice(nightStart)),
  };
}

function luminance(hex: string): number {
  const value = hex.replace("#", "");
  const channel = (c: number) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(value.slice(i, i + 2), 16));
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

function contrast(a: string, b: string): number {
  const [high, low] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (high + 0.05) / (low + 0.05);
}

describe("AA contrast, computed from the tokens (spec 009 §6)", () => {
  const { day, night } = blocks();

  /**
   * The text-on-surface pairs the spec-009 screens actually use. --mute is
   * the smallest text's ink (metadata, captions, legends), so it carries the
   * full 4.5:1; nothing smaller than those sizes may use anything lighter.
   */
  const TEXT_PAIRS: [string, string][] = [
    ["--ink", "--card"],
    ["--ink", "--paper"],
    ["--inkmid", "--card"],
    ["--inkmid", "--paper"],
    ["--ink2", "--card"],
    ["--mute", "--card"],
    ["--mute", "--paper"],
    ["--copperdeep", "--card"],
    // The Call pill: --oncopper text on the --copperdeep fill (the mockup's
    // --copper ground is 3.9:1 with 14px bold text — below AA — so the pill
    // ships on copperdeep; flagged in DECISIONS for the PM).
    ["--oncopper", "--copperdeep"],
  ];

  for (const [name, set] of [
    ["day", day],
    ["night", night],
  ] as const) {
    it(`holds 4.5:1 for every text pair in the ${name} palette`, () => {
      for (const [ink, surface] of TEXT_PAIRS) {
        const ratio = contrast(set[ink], set[surface]);
        expect(
          ratio,
          `${name} ${ink} on ${surface} is ${ratio.toFixed(2)}:1`,
        ).toBeGreaterThanOrEqual(4.5);
      }
    });

    it(`holds 3:1 for the ${name} chip outlines against the card`, () => {
      // Non-text state indicators (the dots) still need to be seen — and the
      // states never rest on color alone: fill-vs-outline plus the legend.
      for (const chip of ["--copper", "--mute", "--olive"]) {
        expect(contrast(set[chip], set["--card"])).toBeGreaterThanOrEqual(3);
      }
    });
  }

  it("would catch a token drifting light again", () => {
    // The regression this file exists for: the v5 Day --mute (#9A968C) read
    // 2.85:1 on the card and spec 009 put metadata TEXT in it.
    expect(contrast("#9A968C", day["--card"])).toBeLessThan(4.5);
  });
});
