/**
 * AC5 — the corner wash: one geometry, four tints.
 *
 * The invariants matter more than the values. A gradient centred on content
 * becomes a spotlight; an alpha above 0.7 becomes a colour wash the text has to
 * fight; a terminal stop that is another colour instead of `transparent` turns
 * four soft corners into a band. And the "off" set must stay cool: the moment it
 * warms toward red, a page that refuses alarm states has one anyway, drawn
 * rather than written, where no copy test would ever find it.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { WASH_SETS, WASH_TEMPLATE, type WashSet, washBackground } from "@/lib/wash";

const tokensSource = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "..", "tokens.css"),
  "utf8",
);

function tint(set: WashSet, index: number): string {
  const match = tokensSource.match(new RegExp(`--tint-${set}-${index}:\\s*([^;]+);`));
  expect(match, `--tint-${set}-${index} is not declared`).not.toBeNull();
  return match![1].trim();
}

function alpha(rgba: string): number {
  const parts = rgba.replace(/rgba?\(|\)/g, "").split(",");
  return Number(parts[3] ?? 1);
}

describe("the geometry template", () => {
  it("is the measured one, verbatim", () => {
    expect(WASH_TEMPLATE).toEqual([
      { shape: "ellipse", at: "0% 0%", fade: 20 },
      { shape: "circle", at: "99% 0%", fade: 30 },
      { shape: "circle", at: "10% 90%", fade: 50 },
      { shape: "circle", at: "99% 99%", fade: 40 },
    ]);
  });

  it("anchors every layer at an edge or a corner, never on content", () => {
    for (const layer of WASH_TEMPLATE) {
      const [x, y] = layer.at.split(" ").map((v) => Number(v.replace("%", "")));
      const edge = (v: number) => v <= 10 || v >= 90;
      expect(edge(x) || edge(y), `${layer.at} is centred on content`).toBe(true);
    }
  });

  it("always fades to transparent, and never to another colour", () => {
    for (const set of WASH_SETS) {
      const css = washBackground(set);
      expect(css.match(/transparent/g) ?? []).toHaveLength(WASH_TEMPLATE.length);
      expect(css).not.toMatch(/,\s*(?:#|rgb|hsl)[^)]*\)\s*\d+%\)/);
    }
  });

  it("references the tokens rather than carrying colour of its own", () => {
    const source = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "..", "lib", "wash.ts"),
      "utf8",
    );
    expect(source).not.toMatch(/#[0-9a-f]{3,8}\b|rgba?\(|hsla?\(/i);
    expect(washBackground("morning")).toContain("var(--tint-morning-1)");
  });
});

describe("the four tint sets", () => {
  it("match the values spec 006 §2 locked", () => {
    expect(WASH_SETS.map((set) => WASH_TEMPLATE.map((_, i) => tint(set, i + 1)))).toEqual([
      [
        "rgba(226, 178, 140, 0.5)",
        "rgba(233, 199, 158, 0.45)",
        "rgba(214, 169, 133, 0.5)",
        "rgba(226, 178, 140, 0.4)",
      ],
      [
        "rgba(178, 182, 166, 0.4)",
        "rgba(196, 196, 182, 0.35)",
        "rgba(170, 178, 164, 0.4)",
        "rgba(186, 188, 172, 0.35)",
      ],
      [
        "rgba(84, 110, 100, 0.4)",
        "rgba(100, 124, 114, 0.35)",
        "rgba(76, 104, 94, 0.45)",
        "rgba(92, 116, 106, 0.35)",
      ],
      [
        "rgba(122, 164, 146, 0.35)",
        "rgba(180, 190, 178, 0.3)",
        "rgba(134, 170, 152, 0.35)",
        "rgba(160, 180, 168, 0.3)",
      ],
    ]);
  });

  it("keeps every alpha inside 0.3–0.7", () => {
    for (const set of WASH_SETS) {
      for (let i = 1; i <= WASH_TEMPLATE.length; i += 1) {
        const a = alpha(tint(set, i));
        expect(a, `--tint-${set}-${i}`).toBeGreaterThanOrEqual(0.3);
        expect(a, `--tint-${set}-${i}`).toBeLessThanOrEqual(0.7);
      }
    }
  });

  it("keeps the off set cool — never red, never warm-alarm", () => {
    // Green ≥ red on every layer. A tint that drifted warm would be an alarm
    // state drawn instead of written, in the one place no copy test can see.
    for (let i = 1; i <= WASH_TEMPLATE.length; i += 1) {
      const [r, g] = tint("off", i)
        .replace(/rgba?\(|\)/g, "")
        .split(",")
        .map(Number);
      expect(g, `--tint-off-${i} has drifted warm`).toBeGreaterThan(r);
    }
  });

  it("gives each set its own four tints", () => {
    const all = WASH_SETS.map((set) => washBackground(set));
    expect(new Set(all).size).toBe(WASH_SETS.length);
  });
});
