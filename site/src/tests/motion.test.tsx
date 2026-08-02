/**
 * AC7 / AC10 / AC11 — motion, the serif, and the notification component.
 *
 * The three rules here are all about restraint, and all three are the kind that
 * decay quietly. Motion arrives one hover at a time. The serif spreads because
 * it looks good in the one place it already is. And the notification mockup
 * drifts toward a screenshot the moment a proportion is nudged by hand.
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

describe("AC7 — every animation sits behind motion-safe", () => {
  it("finds enough classes to be scanning anything", () => {
    expect(classTokens().length).toBeGreaterThan(50);
  });

  it("gates every animation and every transform", () => {
    const ungated = classTokens().filter(
      ({ token }) =>
        /^(animate-|transform\b|translate-|scale-|rotate-)/.test(token) ||
        /^hover:(scale|translate|rotate)/.test(token),
    );
    expect(
      ungated.map((t) => `${t.file}: ${t.token}`),
      "motion that a reduced-motion viewer would still get",
    ).toEqual([]);
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
    // The two regressions AC7 names, run through the same predicate the real
    // scan uses rather than a looser one written for the plant.
    const gated = (token: string) =>
      /^(animate-|transform\b|translate-|scale-|rotate-)/.test(token) ||
      /^hover:(scale|translate|rotate)/.test(token);
    expect(gated("hover:scale-105")).toBe(true);
    expect(gated("animate-rise")).toBe(true);
    expect(gated("motion-safe:animate-rise")).toBe(false);
    expect(gated("hover:bg-calm")).toBe(false);
    expect(gated("transition-colors")).toBe(false);
  });

  it("carries the entry animation on the sections themselves", () => {
    render(<App />);
    const animated = screen
      .getAllByTestId("section")
      .filter((s) => s.className.includes("motion-safe:animate-rise"));
    expect(animated.length).toBeGreaterThan(0);
  });
});

describe("AC10 — the serif is scarce, and only in its permitted slots", () => {
  it("renders the serif only through the one component that may", () => {
    const { container } = render(<App />);
    const serifs = Array.from(container.querySelectorAll(".font-serif"));
    expect(serifs.length).toBeGreaterThan(0);
    for (const node of serifs) {
      expect(node.getAttribute("data-testid"), node.outerHTML).toBe("serif");
    }
  });

  it("never puts the serif on two consecutive elements", () => {
    const { container } = render(<App />);
    for (const node of Array.from(container.querySelectorAll(".font-serif"))) {
      const next = node.nextElementSibling;
      expect(next?.classList.contains("font-serif") ?? false, node.outerHTML).toBe(false);
      const previous = node.previousElementSibling;
      expect(previous?.classList.contains("font-serif") ?? false, node.outerHTML).toBe(false);
    }
  });

  it("keeps the serif out of body, buttons and chrome", () => {
    render(<App />);
    for (const cta of screen.getAllByTestId("cta")) {
      expect(cta.className).not.toContain("font-serif");
    }
    for (const eyebrow of screen.getAllByTestId("eyebrow")) {
      expect(eyebrow.className).not.toContain("font-serif");
    }
    expect(screen.getByTestId("footer").className).not.toContain("font-serif");
  });

  it("names font-serif in exactly one component file", () => {
    const users = sourceFiles(SRC).filter((file) =>
      /font-serif/.test(readFileSync(file, "utf8")),
    );
    expect(users.map((f) => f.slice(SRC.length + 1))).toEqual(["components/SerifPhrase.tsx"]);
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
