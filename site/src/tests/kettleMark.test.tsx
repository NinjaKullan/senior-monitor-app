/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * The living kettle (DECISIONS 187) — placement, decoration, and the scaling
 * law that is the whole reason this component has a stylesheet of its own.
 *
 * The bug this file exists to keep fixed: the approved mockup expresses the
 * steam in pixels calibrated for a 420px kettle, and the mark renders at a
 * third of that. Fixed pixels there are not smaller steam, they are the same
 * steam on a smaller pot — wisps wider than the spout, travel that carries
 * them across the lid. The founder saw it. So every length in
 * `kettle-mark.css` is a multiple of one container-relative unit, and the
 * scan below refuses a bare `px`: at any render size the steam is the same
 * fraction of the kettle it was drawn as.
 *
 * The other half is restraint. This is the page's THIRD animated element
 * (design-language §6), it says nothing, and it must be invisible to a
 * reduced-motion viewer's clock and to a screen reader alike.
 */
import { existsSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "@/App";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..");
const CSS_PATH = join(SRC, "kettle-mark.css");
/** Comments first: this file explains the pixel bug in pixels, and a scan that
 *  cannot tell an explanation from a declaration would force the explanation
 *  out — which is how the next reader repeats the bug. */
const CSS = readFileSync(CSS_PATH, "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

/** The body of a block that starts at `opener`, by brace matching. */
function blockBody(css: string, opener: string): string {
  const start = css.indexOf(opener);
  expect(start, `no ${opener} block`).toBeGreaterThan(-1);
  let depth = 0;
  for (let i = css.indexOf("{", start); i < css.length; i++) {
    if (css[i] === "{") depth++;
    if (css[i] === "}" && --depth === 0) return css.slice(start, i + 1);
  }
  throw new Error(`${opener} block never closes`);
}

const NO_PREFERENCE = blockBody(CSS, "@media (prefers-reduced-motion: no-preference)");
const REDUCE = blockBody(CSS, "@media (prefers-reduced-motion: reduce)");

/** Every length that is not container-relative. Percentages, unitless numbers
 *  and the single rem that sets the mark's own size are the vocabulary; a
 *  `px` anywhere is the fixed-geometry bug returning. */
function fixedLengths(css: string): string[] {
  return [...css.matchAll(/-?\d*\.?\d+(px|em|vw|vh|vmin|vmax)\b/g)].map((m) => m[0]);
}

describe("the asset itself", () => {
  it("is present, unhashed, and the weight it is claimed to be", () => {
    const asset = join(SRC, "..", "public", "kettle-hero.webp");
    expect(existsSync(asset), "site/public/kettle-hero.webp is missing").toBe(true);
    // Unhashed and stable, which is what puts it under the revalidate half of
    // the cache contract rather than the immutable half (DECISIONS 112).
    expect("kettle-hero.webp").not.toMatch(/[.-][0-9a-f]{8,}\.webp$/);
    const bytes = statSync(asset).size;
    expect(bytes).toBeGreaterThan(1_000);
    // Eager above the fold is a promise about weight: an asset that grew to
    // half a megabyte would need that decision made again, not inherited.
    expect(bytes).toBeLessThan(120_000);
  });

  it("is served by the same rule as every other unhashed file", () => {
    // The kettle is not under /assets/, so it falls into the catch-all — the
    // same `no-cache` (revalidate before use) the illustrations get. The
    // matching tree-side manifest lives in product/tests/test_site_caching.py.
    const conf = readFileSync(join(SRC, "..", "nginx.conf"), "utf8");
    const catchAll = conf.slice(conf.lastIndexOf("location / {"));
    expect(catchAll).toContain('add_header Cache-Control "no-cache"');
    expect(conf).not.toContain("kettle-hero");
  });
});

describe("where it sits (placement Option A)", () => {
  it("is a small mark above the kicker, inside the hero, and nowhere else", () => {
    render(<App />);
    const marks = screen.getAllByTestId("kettle-mark");
    expect(marks).toHaveLength(1);
    const mark = marks[0];
    expect(mark.closest("section")!.getAttribute("id")).toBe("hero");

    // Above the kicker: the wireframe's Option A, which is the placement that
    // changes no layout. B put the kettle beside the copy; C put it between
    // the copy and the illustration. Both moved things.
    const eyebrow = screen.getAllByTestId("eyebrow")[0];
    expect(
      mark.compareDocumentPosition(eyebrow) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    const heading = screen.getByTestId("page-heading");
    expect(
      mark.compareDocumentPosition(heading) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("renders the image and the steam, and says nothing at all", () => {
    render(<App />);
    const mark = screen.getByTestId("kettle-mark");
    expect(screen.getByTestId("kettle-image").getAttribute("src")).toBe("/kettle-hero.webp");
    expect(screen.getByTestId("kettle-image").getAttribute("loading")).toBe("eager");
    // Four wisps at the spout, one fainter at the lid rim (the approved v5
    // count) — and both layers hidden from assistive technology, since the
    // steam is not information.
    expect(screen.getAllByTestId("kettle-wisp")).toHaveLength(5);
    expect(screen.getByTestId("kettle-steam").children).toHaveLength(4);
    expect(screen.getByTestId("kettle-steam-lid").children).toHaveLength(1);
    for (const id of ["kettle-steam", "kettle-steam-lid"]) {
      expect(screen.getByTestId(id).getAttribute("aria-hidden")).toBe("true");
    }
    expect(mark.textContent).toBe("");
  });

  it("writes no geometry into the component, so the stylesheet's law is whole", () => {
    // A width or an offset written in the TSX would be a number the scaling
    // scan below cannot see. The component names classes and nothing else.
    const source = readFileSync(join(SRC, "components", "KettleMark.tsx"), "utf8").replace(
      /\/\*[\s\S]*?\*\/|\/\/.*$/gm,
      "",
    );
    expect(source).not.toMatch(/style=/);
    expect(source).not.toMatch(/\d+(px|rem|%)/);
  });
});

describe("the scaling law", () => {
  it("expresses every steam length as a multiple of one container unit", () => {
    expect(fixedLengths(CSS), "fixed geometry in the steam").toEqual([]);
    // The unit itself, and the container it measures: without container-type
    // the cqw values would resolve against the viewport, which is the same
    // bug wearing a different hat.
    expect(CSS).toMatch(/container-type:\s*inline-size/);
    expect(CSS).toMatch(/--kt-u:\s*[\d.]+cqw/);
    // The mark's own size is the ONE length that is not derived — everything
    // else follows it — and it is a rem, not a px.
    expect(CSS.match(/width:\s*[\d.]+rem/g)).toHaveLength(1);
  });

  it("derives every offset, size, blur and travel from that unit", () => {
    // Positively, class by class: a wisp that lost its calc() would still
    // pass a scan that only looks for px, because `left: 22` is not a length
    // at all — it is a silently dropped declaration.
    for (const selector of [
      ".kt-steam",
      ".kt-steam-lid",
      ".kt-wisp-a",
      ".kt-wisp-b",
      ".kt-wisp-c",
      ".kt-wisp-d",
      ".kt-wisp-lid",
    ]) {
      const body = blockBody(CSS, `${selector} {`);
      expect(body, `${selector} has no container-relative geometry`).toContain(
        "calc(var(--kt-u)",
      );
    }
    expect(blockBody(CSS, ".kt-wisp {")).toMatch(/filter:\s*blur\(calc\(var\(--kt-u\)/);
    // The travel — the half of the geometry that actually drifts over the lid
    // when it is written in pixels.
    for (const frames of ["@keyframes kt-rise", "@keyframes kt-lidrise"]) {
      const body = blockBody(NO_PREFERENCE, frames);
      // One per keyframe stop that moves: four stops on the lid leak, more
      // on the spout rise, which also drifts sideways.
      expect(body.match(/calc\(var\(--kt-u\)/g)!.length).toBeGreaterThanOrEqual(4);
    }
  });

  it("would catch the mockup being copied literally", () => {
    // The regression by name: v5's own values, pasted in.
    expect(fixedLengths("left: 22px; width: 30px;")).toEqual(["22px", "30px"]);
    expect(fixedLengths("transform: translateY(-124px) scaleY(1.6);")).toEqual(["-124px"]);
    expect(fixedLengths("filter: blur(3px);")).toEqual(["3px"]);
    // And the vocabulary that is allowed stays allowed.
    expect(fixedLengths("left: 26%; width: calc(var(--kt-u) * 110); opacity: 0.4;")).toEqual([]);
  });
});

describe("motion, and the viewer who asked for none", () => {
  it("keeps every keyframe and every animation inside the no-preference block", () => {
    // The site's motion law, in the one place Tailwind's `motion-safe:` prefix
    // cannot reach: hand-written component CSS. Scanned by position, so a
    // declaration that drifts out of the block by one brace fails.
    const start = CSS.indexOf(NO_PREFERENCE);
    const end = start + NO_PREFERENCE.length;
    const moving = [...CSS.matchAll(/@keyframes|animation(?:-delay|-duration|-name)?\s*:/g)];
    expect(moving.length).toBeGreaterThan(5);
    const escaped = moving
      .filter((match) => match.index! < start || match.index! >= end)
      .map((match) => match[0]);
    expect(escaped, "motion a reduced-motion viewer would still get").toEqual([]);
  });

  it("stands down to a designed still: one faint wisp, going nowhere", () => {
    expect(REDUCE).not.toMatch(/animation|@keyframes|transform/);
    // Exactly one wisp is left visible, and it is faint rather than full.
    const opacities = [...REDUCE.matchAll(/opacity:\s*([\d.]+)/g)].map((m) => Number(m[1]));
    expect(opacities).toHaveLength(1);
    expect(opacities[0]).toBeGreaterThan(0);
    expect(opacities[0]).toBeLessThan(0.5);
    // And the still is a still of the SPOUT wisp: the lid leak is the
    // full-boil flourish, which a static frame has no way to explain.
    expect(REDUCE).toContain(".kt-wisp-a");
  });

  it("starts mid-rise rather than lighting the stove on page load", () => {
    // Negative delays are the whole difference between a kettle that has been
    // on all morning and one that starts when you arrive.
    const delays = [...NO_PREFERENCE.matchAll(/animation-delay:\s*(-?[\d.]+)s/g)].map((m) =>
      Number(m[1]),
    );
    expect(delays.length).toBeGreaterThanOrEqual(5);
    expect(delays.every((delay) => delay < 0)).toBe(true);
  });

  it("paints its colour from tokens, never from a literal", () => {
    // AC1 covers this globally; asserted here too because a gradient is the
    // easiest place on the page to write three rgba() values by hand.
    expect(CSS).not.toMatch(/#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(/);
    for (const token of ["--steam-core", "--steam-body", "--steam-edge"]) {
      expect(CSS).toContain(`var(${token})`);
    }
  });

  it("stays out of the way of the pointer", () => {
    // The steam sits on top of the mark; anything above the kicker that eats
    // a tap is a bug on a phone.
    for (const selector of [".kt-steam {", ".kt-steam-lid {"]) {
      expect(blockBody(CSS, selector)).toContain("pointer-events: none");
    }
  });
});
