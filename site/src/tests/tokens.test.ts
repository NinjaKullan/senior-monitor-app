/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * AC1 / AC2 — the palette, checked rather than described.
 *
 * Two things are easy to get wrong here and impossible to notice afterwards.
 * A contrast ratio degrades one considered tweak at a time until the secondary
 * text is unreadable at 6am by someone who is already worried, so the ratios are
 * computed from the tokens rather than asserted in a comment. And an alarm
 * colour arrives on a marketing page the same way: one chip, for one state, that
 * seemed like an exception. The token to make one with does not exist, and this
 * proves it does not.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..");
const TOKENS = join(SRC, "tokens.css");
const tokensSource = readFileSync(TOKENS, "utf8");

function tokens(): Record<string, string> {
  const found: Record<string, string> = {};
  for (const [, name, value] of tokensSource.matchAll(/(--[a-z0-9-]+):\s*([^;]+);/g)) {
    if (!(name in found)) found[name] = value.trim();
  }
  return found;
}

/* --- WCAG relative luminance, from the spec's own formula ---------------- */

function channel(eight: number): number {
  const c = eight / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

function luminance(hex: string): number {
  const value = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(value.slice(i, i + 2), 16));
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

function contrast(a: string, b: string): number {
  const [high, low] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (high + 0.05) / (low + 0.05);
}

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) return sourceFiles(path);
    return /\.(tsx?|css)$/.test(path) ? [path] : [];
  });
}

describe("AC1 — one file holds every colour", () => {
  it("declares the values spec 006 §2 locked", () => {
    const t = tokens();
    expect(t["--canvas"]).toBe("#f6f2ec");
    expect(t["--ink"]).toBe("#403c36");
    // Kettle green stays primary, and stays the same value as the app's.
    expect(t["--calm"]).toBe("hsl(158 50% 32%)");
    expect(t["--clay"]).toBe("#c29179");
    expect(t["--text-secondary"]).toBe("#6c665d");
    expect(t["--error"]).toBe("#9e3b2e");
  });

  it("keeps every colour literal out of every other file", () => {
    // One scoped refinement (DECISIONS 131): the rhythm-field engine paints a
    // canvas, which has no CSS, so it may *compose* rgba() strings — but only
    // from channels interpolated out of tokens.css. In that one file the ban
    // moves from the function name to the values: any rgba( followed by a
    // digit, or any #hex, still fails, and a positive assertion below keeps
    // the engine actually reading the --field- tokens.
    const offenders: string[] = [];
    for (const file of sourceFiles(SRC)) {
      if (file.endsWith("tokens.css")) continue;
      if (file.includes("/tests/")) continue;
      const source = readFileSync(file, "utf8");
      const scan = file.endsWith("lib/rhythmField.ts")
        ? /#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(\s*\d/g
        : /#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(/g;
      for (const [literal] of source.matchAll(scan)) {
        offenders.push(`${file.slice(SRC.length + 1)}: ${literal}`);
      }
    }
    expect(offenders, "colour outside tokens.css").toEqual([]);

    const engine = readFileSync(join(SRC, "lib", "rhythmField.ts"), "utf8");
    expect(engine).toMatch(/--field-signal/);
    expect(engine).toMatch(/getPropertyValue/);
  });

  it("declares the field palette the approved mock specified", () => {
    // The mock's channel values, held where every colour lives (DECISIONS
    // 129/131). --field-signal is the kettle orange: the brand mark's hue,
    // depicting an ordinary signal arriving — not an alarm state, and no
    // utility class can reach it.
    const t = tokens();
    expect(t["--field-signal"]).toBe("253, 102, 49");
    expect(t["--field-sage"]).toBe("138, 152, 130");
    expect(t["--field-graphite"]).toBe("90, 82, 74");
    expect(t["--field-dust"]).toBe("244, 237, 228");
    expect(t["--field-label"]).toBe("250, 244, 236");
    expect(t["--field-glow"]).toBe("43, 35, 32");
  });

  it("clears the contrast the design language requires", () => {
    const t = tokens();
    // Warm dark on warm canvas: high contrast used on purpose, never true black.
    expect(contrast(t["--ink"], t["--canvas"])).toBeGreaterThanOrEqual(7);
    // Secondary text is the one most likely to drift pale.
    expect(contrast(t["--text-secondary"], t["--canvas"])).toBeGreaterThanOrEqual(4.5);
  });

  it("inverts dark sections exactly, with no third scheme", () => {
    const inverted = tokensSource.slice(tokensSource.indexOf(".inverted"));
    const swapped = Object.fromEntries(
      [...inverted.matchAll(/(--[a-z-]+):\s*([^;]+);/g)].map((m) => [m[1], m[2].trim()]),
    );
    const t = tokens();
    expect(swapped["--canvas"]).toBe(t["--ink"]);
    expect(swapped["--ink"]).toBe(t["--canvas"]);
    expect(contrast(swapped["--text-secondary"], swapped["--canvas"])).toBeGreaterThanOrEqual(4.5);
  });
});

describe("AC2 — no alarm colours exist on this surface", () => {
  it("has no amber token at all", () => {
    // Amber is equipment vocabulary for the app ("this tripwire stopped
    // reporting"). Marketing carries zero alert states, so the colour to build
    // one with must not be reachable.
    //
    // Comments are stripped first: tokens.css explains amber's absence in prose,
    // and a scan that cannot tell an explanation from a declaration would force
    // the explanation out — leaving the next reader to wonder why the app has a
    // token this file does not.
    expect(Object.keys(tokens())).not.toContain("--attention");
    for (const file of sourceFiles(SRC)) {
      if (file.includes("/tests/")) continue;
      const code = readFileSync(file, "utf8")
        .replace(/\/\*[\s\S]*?\*\//g, "")
        .replace(/^\s*(\/\/|\*).*$/gm, "");
      expect(code, file).not.toMatch(/--attention\b|-attention\b/);
    }
  });

  it("spends --error only inside the waitlist form", () => {
    const users = sourceFiles(SRC).filter(
      (file) =>
        !file.endsWith("tokens.css") &&
        !file.includes("/tests/") &&
        /(^|[^a-z-])(text|bg|border)-error\b|--error\b/.test(readFileSync(file, "utf8")),
    );
    expect(
      users.map((file) => file.slice(SRC.length + 1)),
      "red belongs to form errors and nowhere else",
    ).toEqual(["sections/Waitlist.tsx"]);
  });

  it("names no red anywhere in the utility vocabulary", () => {
    for (const file of sourceFiles(SRC)) {
      if (file.includes("/tests/")) continue;
      expect(readFileSync(file, "utf8"), file).not.toMatch(
        /\b(?:bg|text|border)-(?:red|rose|orange|amber|destructive)\b/,
      );
    }
  });
});
