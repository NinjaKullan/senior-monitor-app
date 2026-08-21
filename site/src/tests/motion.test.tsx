/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * AC7 / AC10 / AC11 — motion, the type scale, and the notification component.
 *
 * The three rules here are all about restraint, and all three are the kind that
 * decay quietly. Motion arrives one hover at a time. A type scale grows one
 * className at a time, and a second face comes back one emphasis at a time —
 * which is how the page ended up mix-and-matched enough for two reviewers to
 * say so (DECISIONS 135). And the notification mockup drifts toward a
 * screenshot the moment a proportion is nudged by hand.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "@/App";
import { NotificationCard } from "@/components/NotificationCard";
import { NOTIFICATION, cardRadius } from "@/lib/notification";
import { SEEN_NOTIF } from "@/copy";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..");

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const path = join(dir, entry);
    if (statSync(path).isDirectory() && !path.includes("/tests")) return sourceFiles(path);
    return /\.tsx?$/.test(path) && !path.includes("/tests/") ? [path] : [];
  });
}

/** Every Tailwind class token this codebase writes, with its file. */
function classTokens(): { file: string; token: string }[] {
  const found: { file: string; token: string }[] = [];
  for (const file of sourceFiles(SRC)) {
    const source = readFileSync(file, "utf8");
    for (const [, literal] of source.matchAll(/className=\{?["`']([^"`']+)["`']/g)) {
      for (const token of literal.split(/\s+/).filter(Boolean)) {
        found.push({ file: file.slice(SRC.length + 1), token });
      }
    }
    // Class strings assembled by concatenation, which the pattern above catches
    // only the first fragment of.
    for (const [, literal] of source.matchAll(/"([a-z0-9:\-[\]/ .]+)"\s*\+/g)) {
      for (const token of literal.split(/\s+/).filter(Boolean)) {
        found.push({ file: file.slice(SRC.length + 1), token });
      }
    }
  }
  return found;
}

/**
 * A class token that moves something. `motion-safe:animate-rise` does not match:
 * the prefix is the gate, and Tailwind emits it inside the media query.
 */
const MOVES = (token: string) =>
  /^(animate-|transform\b|translate-|scale-|rotate-)/.test(token) ||
  /^hover:(scale|translate|rotate)/.test(token);

describe("AC7 — every animation sits behind motion-safe", () => {
  it("finds enough classes to be scanning anything", () => {
    expect(classTokens().length).toBeGreaterThan(50);
  });

  it("gates every animation and every transform, in the rendered page", () => {
    // Scanned off the DOM, not off the source. Class strings get assembled from
    // template literals and concatenation, and a source scan that missed one
    // would report green over an animation a reduced-motion viewer still gets —
    // which is exactly what happened while this test was being written.
    const { container } = render(<App />);
    const ungated: string[] = [];
    for (const node of [container, ...Array.from(container.querySelectorAll("*"))]) {
      for (const token of Array.from(node.classList ?? [])) {
        if (MOVES(token)) ungated.push(`${node.tagName}: ${token}`);
      }
    }
    expect(ungated, "motion that a reduced-motion viewer would still get").toEqual([]);
  });

  it("gates them in the source too, as a second net", () => {
    const ungated = classTokens().filter(({ token }) => MOVES(token));
    expect(ungated.map((t) => `${t.file}: ${t.token}`)).toEqual([]);
  });

  it("keeps hovers to colour, with no elevation and no movement", () => {
    const moving = classTokens().filter(({ token }) =>
      /^hover:(scale|translate|rotate|shadow|drop-shadow)/.test(token),
    );
    expect(moving.map((t) => `${t.file}: ${t.token}`)).toEqual([]);

    render(<App />);
    for (const cta of screen.getAllByTestId("cta")) {
      expect(cta.className).toMatch(/hover:bg-/);
      expect(cta.className).toContain("duration-150");
      expect(cta.className).not.toMatch(/hover:(scale|shadow|translate)/);
    }
  });

  it("would catch a hover:scale and an ungated entry animation", () => {
    // The two regressions AC7 names, run through the same predicate both scans
    // use rather than a looser one written for the plant.
    expect(MOVES("hover:scale-105")).toBe(true);
    expect(MOVES("animate-rise")).toBe(true);
    expect(MOVES("motion-safe:animate-rise")).toBe(false);
    expect(MOVES("hover:bg-calm")).toBe(false);
    expect(MOVES("transition-colors")).toBe(false);
  });

  it("carries the entry animation on the sections themselves", () => {
    render(<App />);
    const animated = screen
      .getAllByTestId("section")
      .filter((s) => s.className.includes("motion-safe:animate-rise"));
    expect(animated.length).toBeGreaterThan(0);
  });
});

describe("AC10 — one typeface, five sizes, and no inline emphasis", () => {
  /** The whole type scale, and the only sizes a className may name. */
  const SIZES = new Set(["text-display", "text-heading", "text-lead", "text-body", "text-eyebrow"]);
  /** `text-` utilities that are not sizes. Anything outside both sets is a
   *  size nobody declared, which is how a scale grows back to seven. */
  const NOT_SIZES = new Set([
    "text-ink",
    "text-canvas",
    "text-secondary",
    "text-error",
    "text-center",
    "text-left",
  ]);
  /** The three real weights: 400, 500, 600. `font-light` is the trap — the
   *  class was written across every heading while Instrument Sans has no 300
   *  file, so the browser served 400 and the law was decoration. */
  const WEIGHTS = new Set(["font-normal", "font-medium", "font-semibold"]);

  it("renders no second face and no italics anywhere on the page", () => {
    const { container } = render(<App />);
    expect(container.querySelectorAll(".font-serif")).toHaveLength(0);
    expect(container.querySelectorAll(".italic")).toHaveLength(0);
  });

  it("carries no inline emphasis inside any sentence", () => {
    // The retired role, structurally: emphasis is a whole sentence carried by
    // weight, never a fragment spliced into someone else's. An <em>, <i>, <b>
    // or <strong> anywhere is that fragment coming back.
    const { container } = render(<App />);
    const inline = Array.from(container.querySelectorAll("em, i, b, strong"));
    expect(inline.map((n) => n.outerHTML)).toEqual([]);
  });

  it("spends its emphasis on one whole sentence, by weight", () => {
    render(<App />);
    const emphasis = screen.getAllByTestId("emphasis");
    expect(emphasis).toHaveLength(1);
    const text = emphasis[0].textContent ?? "";
    expect(text[0]).toBe(text[0].toUpperCase());
    expect(text.trimEnd().endsWith(".")).toBe(true);
    expect(emphasis[0].className).toContain("font-medium");
    expect(emphasis[0].tagName).toBe("P");
  });

  it("writes no retired face, slope or weight in any className", () => {
    // Off the same token scan AC7 uses, not off raw source: the words "serif"
    // and "italic" appear in the comments that explain why they are gone, and
    // a source-text scan would fail on its own documentation.
    const retired = classTokens().filter(({ token }) =>
      /^(font-serif|italic|not-italic|font-light|font-bold|font-black)$/.test(token),
    );
    expect(retired.map((t) => `${t.file}: ${t.token}`)).toEqual([]);
  });

  it("loads one family, and only weights that exist as files", () => {
    const css = readFileSync(join(SRC, "index.css"), "utf8");
    const families = [...css.matchAll(/@fontsource\/([a-z-]+)\//g)].map((m) => m[1]);
    expect([...new Set(families)]).toEqual(["instrument-sans"]);
    const config = readFileSync(join(SRC, "..", "tailwind.config.js"), "utf8");
    expect(config).not.toMatch(/serif:/);
  });

  it("uses only the five declared sizes, in the rendered page", () => {
    const { container } = render(<App />);
    const strays: string[] = [];
    const used = new Set<string>();
    for (const node of [container, ...Array.from(container.querySelectorAll("*"))]) {
      for (const token of Array.from(node.classList ?? [])) {
        if (!token.startsWith("text-")) continue;
        if (SIZES.has(token)) used.add(token);
        else if (!NOT_SIZES.has(token)) strays.push(`${node.tagName}: ${token}`);
      }
    }
    expect(strays, "a size role nobody declared").toEqual([]);
    // Not passing on a page that stopped rendering: every role is in use, and
    // a role only one element uses would have been merged into its neighbour.
    expect([...used].sort()).toEqual([...SIZES].sort());
  });

  it("uses only weights the stylesheet actually loads", () => {
    const { container } = render(<App />);
    const strays: string[] = [];
    for (const node of [container, ...Array.from(container.querySelectorAll("*"))]) {
      for (const token of Array.from(node.classList ?? [])) {
        if (!token.startsWith("font-") || token === "font-sans") continue;
        if (!WEIGHTS.has(token)) strays.push(`${node.tagName}: ${token}`);
      }
    }
    expect(strays).toEqual([]);
  });

  it("gives display exactly one job: the page's single h1", () => {
    const { container } = render(<App />);
    const display = Array.from(container.querySelectorAll(".text-display"));
    expect(display.map((n) => n.tagName)).toEqual(["H1"]);
    // And every section heading takes the role below it, so the two are never
    // the same size again.
    for (const heading of screen.getAllByTestId("section-heading")) {
      expect(heading.className, heading.textContent ?? "").toContain("text-heading");
    }
  });

  it("would catch the retired role returning", () => {
    // Planted, not asserted in the abstract: each of these is a way the serif
    // or the seven-size scale comes back.
    const scan = (html: string) => {
      const node = document.createElement("div");
      node.innerHTML = html;
      const strays: string[] = [];
      for (const el of Array.from(node.querySelectorAll("*"))) {
        for (const token of Array.from(el.classList)) {
          if (token.startsWith("text-") && !SIZES.has(token) && !NOT_SIZES.has(token)) {
            strays.push(token);
          }
          if (token.startsWith("font-") && token !== "font-sans" && !WEIGHTS.has(token)) {
            strays.push(token);
          }
        }
      }
      return { strays, inline: node.querySelectorAll("em, i, b, strong").length };
    };
    expect(scan('<p>and <em class="font-serif italic">a phrase</em></p>').inline).toBe(1);
    expect(scan('<p class="text-card">a lead</p>').strays).toEqual(["text-card"]);
    expect(scan('<p class="text-quote">a pull quote</p>').strays).toEqual(["text-quote"]);
    expect(scan('<h2 class="text-display font-light">a heading</h2>').strays).toEqual(["font-light"]);
    expect(scan('<p class="text-body font-medium">legal</p>').strays).toEqual([]);
  });
});

describe("AC11 — the notification component's proportions", () => {
  it("holds every number in one place", () => {
    expect(NOTIFICATION).toEqual({
      aspectRatio: 4.2,
      strokeWidthPx: 2,
      strokeOpacity: 0.35,
      radiusPercentOfWidth: 2,
      iconPercentOfWidth: 13.5,
      iconRadiusPercentOfIcon: 8,
    });
  });

  it("scales the radius so 2% means 2% of width on every corner", () => {
    // A bare `2%` resolves vertically against the height, which on a 4.2:1 card
    // turns the corners into visible ellipses.
    expect(cardRadius()).toBe("2% / 8.4%");
  });

  it("renders transparent, so the slot behind shows through", () => {
    render(<NotificationCard body={SEEN_NOTIF} />);
    const card = screen.getByTestId("notification");
    expect(card.className).toContain("bg-transparent");
    expect(card.style.aspectRatio).toBe("4.2");
    expect(card.style.borderWidth).toBe("2px");
    expect(card.style.borderRadius).toBe("2% / 8.4%");
  });

  it("sizes the icon and its radius from the same constants", () => {
    render(<NotificationCard body={SEEN_NOTIF} />);
    const icon = screen.getByTestId("notification-icon");
    expect(icon.style.width).toBe("13.5%");
    expect(icon.style.borderRadius).toBe("8%");
    // The Kettle mark on green — not a red badge, which there is no token for.
    expect(icon.className).toContain("bg-calm");
  });

  it("carries one single-line body and the word Today", () => {
    render(<NotificationCard body={SEEN_NOTIF} />);
    expect(screen.getByTestId("notification-body").className).toContain("truncate");
    expect(screen.getByTestId("notification-time").textContent).toBe("Today");
  });

  it("reads its numbers from the module rather than hard-coding them", () => {
    const source = readFileSync(join(SRC, "components", "NotificationCard.tsx"), "utf8");
    // Any bare proportion in the component is a number that stopped being tested.
    expect(source).not.toMatch(/\b4\.2\b|\b13\.5\b|\b0\.35\b/);
  });
});
