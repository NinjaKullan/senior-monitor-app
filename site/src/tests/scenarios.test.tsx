/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * AC5 / AC6 / AC9 — the scenario tabs.
 *
 * The centrepiece, and the place a well-meaning change does the most damage.
 * Two rules carry the weight. The four panels must differ by tint and content
 * only, because the moment `When something's off` gets a border or a heavier
 * weight the page has escalated a question into an alarm. And every panel must
 * be in the static HTML, because a reader with no JavaScript is not a reader
 * this product gets to skip.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { SCENARIOS, Scenarios } from "@/sections/Scenarios";
import { EDGE_FADE, isOverflowing, scrollLeftFor } from "@/lib/tabStrip";
import { OFF_NOTIF, OFF_TAB, SEEN_NOTIF, SEEN_TAB } from "@/copy";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..");

const tabs = () => screen.getAllByTestId("scenario-tab");
const panels = () => screen.getAllByTestId("scenario-panel");

/** Tag names and attribute *names* — structure with the content taken out. */
function skeleton(root: Element): string {
  const parts: string[] = [];
  const walk = (node: Element, depth: number) => {
    const attrs = Array.from(node.attributes)
      .map((a) => a.name)
      // `id`/`aria-labelledby`/`data-scenario` name the panel; `hidden` is which
      // one is showing. Both are identity and state — the structure is what is
      // left when you take them out.
      .filter(
        (name) =>
          !["id", "aria-labelledby", "data-scenario", "hidden", "aria-controls"].includes(name),
      )
      .sort()
      .join(",");
    parts.push(`${"  ".repeat(depth)}${node.tagName}[${attrs}]`);
    for (const child of Array.from(node.children)) walk(child, depth + 1);
  };
  walk(root, 0);
  return parts.join("\n");
}

describe("AC5 — panels differ by tint and content, never by structure", () => {
  it("gives the four panels the same skeleton", () => {
    render(<Scenarios />);
    const shapes = panels().map(skeleton);

    // Morning and afternoon carry no notification; off and seen do, because
    // §3.2 assigns one per panel. That is content the spec places, so the
    // comparison is between panels that carry the same components — and the
    // pair that matters most, `off` against `seen`, is compared directly.
    expect(shapes[0]).toBe(shapes[1]);
    expect(shapes[2]).toBe(shapes[3]);
    // And the escalation risk: `off` must not have acquired anything `morning`
    // lacks beyond that notification. The prefix is morning's own length rather
    // than a hard-coded count — the panel lost an element when the serif was
    // retired (DECISIONS 135), and a literal 6 here quietly stopped comparing
    // the whole of morning against the start of off.
    const morning = shapes[0].split("\n");
    expect(shapes[2].split("\n").slice(0, morning.length)).toEqual(morning);
  });

  it("gives every panel identical classes", () => {
    render(<Scenarios />);
    const classes = new Set(panels().map((p) => p.className));
    expect(classes.size, "a panel is styled differently from its siblings").toBe(1);
  });

  it("changes the wash when the tab changes, and changes nothing else", () => {
    const { container } = render(<Scenarios />);
    const section = container.querySelector("section")!;
    const morning = section.getAttribute("style");

    fireEvent.click(screen.getByRole("tab", { name: OFF_TAB }));
    const off = section.getAttribute("style");

    expect(off).not.toBe(morning);
    expect(off).toContain("--tint-off-1");
    expect(new Set(panels().map((p) => p.className)).size).toBe(1);
  });
});

describe("the tabs actually toggle (DECISIONS 128)", () => {
  const visiblePanels = () => panels().filter((p) => !p.hasAttribute("hidden"));

  it("shows exactly one panel, and moves it on click", () => {
    // The field bug: every panel carried `hidden` correctly and every panel
    // rendered anyway, because the display utility beat the attribute. The
    // attribute half is asserted here; the cascade half is pinned below.
    render(<Scenarios />);
    expect(visiblePanels().map((p) => p.dataset.scenario)).toEqual(["morning"]);

    fireEvent.click(screen.getByRole("tab", { name: OFF_TAB }));
    expect(visiblePanels().map((p) => p.dataset.scenario)).toEqual(["off"]);

    fireEvent.click(screen.getByRole("tab", { name: SEEN_TAB }));
    expect(visiblePanels().map((p) => p.dataset.scenario)).toEqual(["seen"]);
  });

  it("moves the one visible panel with the arrow keys too", () => {
    render(<Scenarios />);
    fireEvent.keyDown(tabs()[0], { key: "ArrowRight" });
    expect(visiblePanels().map((p) => p.dataset.scenario)).toEqual(["afternoon"]);
  });

  it("pins the stylesheet rule that lets hidden beat the display utility", () => {
    // jsdom does not compute the cascade, so a behavioural assertion alone
    // would have passed while every real browser stacked all four panels —
    // author utilities (.flex) outrank the preflight's plain [hidden] rule.
    // The override that restores the attribute's meaning is pinned as text:
    // remove the !important and this fails before a browser has to.
    const css = readFileSync(join(SRC, "index.css"), "utf8");
    const rule = css.match(/\[hidden\]\s*\{[^}]*\}/s);
    expect(rule, "index.css lost its [hidden] override").not.toBeNull();
    expect(rule![0].replace(/\s+/g, " ")).toContain("display: none !important");
  });
});

describe("AC6 — the measured tab grammar", () => {
  it("marks the active tab with full opacity and an ink bottom border", () => {
    render(<Scenarios />);
    const [first] = tabs();
    expect(first.dataset.state).toBe("active");
    expect(first.className).toContain("opacity-100");
    expect(first.className).toContain("border-ink");
    expect(first.className).toContain("border-b-[3px]");
  });

  it("marks inactive tabs at 0.7 opacity with a transparent border", () => {
    render(<Scenarios />);
    for (const tab of tabs().slice(1)) {
      expect(tab.dataset.state).toBe("inactive");
      expect(tab.className).toContain("opacity-70");
      expect(tab.className).toContain("border-transparent");
    }
  });

  it("changes nothing but opacity and the border between states", () => {
    // No fill, no colour change, no weight change. The difference between an
    // active and an inactive tab is presence, not emphasis.
    render(<Scenarios />);
    const strip = (c: string) =>
      c
        .split(/\s+/)
        .filter((token) => !/^(opacity-|border-ink|border-transparent)/.test(token))
        .join(" ");
    const [active, ...rest] = tabs();
    for (const tab of rest) expect(strip(tab.className)).toBe(strip(active.className));
    // Neither state names a weight at all now: the tabs sit at the body role's
    // own 400, so "no weight change between states" is true by construction
    // rather than by both sides carrying the same override.
    for (const tab of tabs()) expect(tab.className).not.toMatch(/font-(light|medium|semibold|bold)/);
  });

  it("eases the tab over 300ms and never transitions the panel", () => {
    render(<Scenarios />);
    expect(tabs()[0].className).toContain("transition-opacity");
    expect(tabs()[0].className).toContain("duration-300");
    for (const panel of panels()) {
      expect(panel.className, "the panel must swap instantly").not.toMatch(/transition|duration/);
    }
  });

  it("wires the roles a screen reader needs", () => {
    render(<Scenarios />);
    expect(screen.getByRole("tablist")).toBeInTheDocument();
    expect(screen.getAllByRole("tab")).toHaveLength(SCENARIOS.length);
    const [first] = tabs();
    expect(first).toHaveAttribute("aria-selected", "true");
    expect(first).toHaveAttribute("aria-controls", panels()[0].id);
    expect(panels()[0]).toHaveAttribute("aria-labelledby", first.id);
  });

  it("is operable from the keyboard, and shows where focus is", () => {
    render(<Scenarios />);
    expect(tabs()[0].className).toContain("focus-visible:ring");

    fireEvent.keyDown(tabs()[0], { key: "ArrowRight" });
    expect(tabs()[1]).toHaveAttribute("aria-selected", "true");

    // Wraps, so the last tab is one key from the first.
    fireEvent.keyDown(tabs()[1], { key: "ArrowLeft" });
    fireEvent.keyDown(tabs()[0], { key: "ArrowLeft" });
    expect(screen.getByRole("tab", { name: SEEN_TAB })).toHaveAttribute("aria-selected", "true");
  });

  it("keeps only the active tab in the tab order", () => {
    render(<Scenarios />);
    expect(tabs().map((t) => t.getAttribute("tabindex"))).toEqual(["0", "-1", "-1", "-1"]);
  });
});

describe("the scenario illustrations", () => {
  it("gives every panel its own illustration, above the message card", () => {
    render(<Scenarios />);
    for (const panel of panels()) {
      const image = panel.querySelector("img")!;
      expect(image, "a panel lost its illustration").not.toBeNull();
      // Above the message card: the illustration sets the scene the card lands
      // in, so a panel that carries a notification renders it after the image.
      const card = panel.querySelector('[data-testid="notification"]');
      if (card) {
        expect(
          image.compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING,
          "the message card rose above its illustration",
        ).toBeTruthy();
      }
    }
  });

  it("lazy-loads them all — everything below the hero waits its turn", () => {
    render(<Scenarios />);
    for (const panel of panels()) {
      const image = panel.querySelector("img")!;
      expect(image.getAttribute("loading")).toBe("lazy");
      expect(image.getAttribute("src")).toMatch(/^\/ill-.+\.webp$/);
      // The container matches the artwork's own crop, so nothing is cut off
      // by a frame that disagrees with the drawing (DECISIONS 136).
      expect(image.className).toContain("aspect-[4/3]");
    }
  });
});

describe("the two notifications, and whose phone each is on", () => {
  it("shows the senior-first question on her phone and the digest naming Dad on yours", () => {
    // Amendment A's persona balance, asserted at the panel. The `off` panel is a
    // question addressed to her; the `seen` panel is the sample digest a child
    // receives, and it names Dad. The asymmetry is the point — the scenarios
    // follow one parent, the page shows both — so it is pinned here rather than
    // left to look like a mismatch someone should tidy.
    render(<Scenarios />);
    const bodies = screen.getAllByTestId("notification-body").map((n) => n.textContent);
    expect(bodies).toEqual([`Kettle: ${OFF_NOTIF}`, `Kettle: ${SEEN_NOTIF}`]);
    expect(bodies[1]).toContain("Dad's");
  });
});

describe("AC9 — the panels read with no JavaScript", () => {
  it("puts all four in the static markup, in the order a day happens", () => {
    const html = renderToStaticMarkup(<Scenarios />);
    const order = SCENARIOS.map((s) => html.indexOf(`data-scenario="${s.set}"`));
    expect(order.every((index) => index >= 0)).toBe(true);
    expect([...order].sort((a, b) => a - b)).toEqual(order);
  });

  it("carries every panel's copy, not just the active one's", () => {
    // Entities decoded first: React escapes apostrophes, and a test that
    // compared raw markup would fail on punctuation while claiming the copy is
    // missing — the most misleading kind of red.
    const html = renderToStaticMarkup(<Scenarios />)
      .replace(/&#x27;|&#39;/g, "'")
      .replace(/&quot;/g, '"')
      .replace(/&amp;/g, "&");
    for (const scenario of SCENARIOS) {
      expect(html, `${scenario.set} is missing from the static HTML`).toContain(scenario.body);
      expect(html).toContain(scenario.lead);
    }
  });
});

/* --------------------------------------------------------------------- */
/* The tab row on a phone (DECISIONS 136)                                  */
/* --------------------------------------------------------------------- */

describe("where the tab row has to be scrolled", () => {
  // The arithmetic lives in lib/tabStrip.ts precisely so it can be checked
  // with numbers: jsdom lays nothing out, so a test that read offsetLeft off
  // the DOM would be reading zeroes and passing on them.
  const view = (scrollLeft: number, clientWidth = 342, scrollWidth = 540) => ({
    scrollLeft,
    clientWidth,
    scrollWidth,
  });

  it("knows a clipped row from one that fits", () => {
    expect(isOverflowing(540, 342)).toBe(true);
    expect(isOverflowing(342, 342)).toBe(false);
    expect(isOverflowing(300, 342)).toBe(false);
  });

  it("leaves a visible tab where it is", () => {
    // A tab in the middle of what the reader can already see must not drag
    // the row around underneath them.
    expect(scrollLeftFor(view(0), { offsetLeft: 120, offsetWidth: 90 })).toBe(0);
  });

  it("brings a tab past the right edge fully into view, clear of the fade", () => {
    // "What you see" starts at 430 in a 342-wide window scrolled to 0: its
    // right edge plus the fade is 430 + 95 + 40 = 565, so the row scrolls to
    // 565 - 342 = 223 — except the row can only scroll to 540 - 342 = 198.
    expect(scrollLeftFor(view(0), { offsetLeft: 430, offsetWidth: 95 })).toBe(198);
  });

  it("brings a tab past the left edge back, and never scrolls past the start", () => {
    expect(scrollLeftFor(view(198), { offsetLeft: 100, offsetWidth: 90 })).toBe(60);
    expect(scrollLeftFor(view(198), { offsetLeft: 0, offsetWidth: 90 })).toBe(0);
  });

  it("keeps the fade's width and the margin the same number", () => {
    // If they drift apart the active tab lands under its own fade, which is
    // the failure this pass exists to avoid rather than to relocate.
    expect(EDGE_FADE).toBe(40);
    const css = readFileSync(join(SRC, "index.css"), "utf8");
    expect(css).toContain(`calc(100% - ${EDGE_FADE / 16}rem)`);
  });
});

describe("the tab row on a phone", () => {
  const strip = () => screen.getByTestId("scenario-tablist");

  it("scrolls sideways below md and wraps from md up", () => {
    // Four tabs need about 540px of row and a phone gives 312–380, so the
    // wrapping row folded into a ragged two-line block on a real handset.
    // jsdom cannot measure, so the classes are pinned with that arithmetic.
    render(<Scenarios />);
    expect(strip().className).toContain("overflow-x-auto");
    expect(strip().className).toContain("scrollbar-none");
    expect(strip().className).toContain("md:flex-wrap");
    expect(strip().className).toContain("md:overflow-x-visible");
    // Not wrapping below md is the whole fix: `flex` alone is nowrap, so a
    // bare `flex-wrap` here would restore the fold.
    expect(strip().className).not.toMatch(/(^|\s)flex-wrap(\s|$)/);
  });

  it("gives every tab a tap target and a label that cannot break", () => {
    render(<Scenarios />);
    for (const tab of tabs()) {
      // py-2 on body text is 24 + 8 + 8 = 40px of target.
      expect(tab.className).toContain("py-2");
      expect(tab.className).not.toContain("pb-2");
      // Without these two, flex compresses the tabs and "When something's
      // off" breaks across two lines inside its own tab.
      expect(tab.className).toContain("shrink-0");
      expect(tab.className).toContain("whitespace-nowrap");
    }
  });

  it("fades the clipped edge only while the row is actually clipped", () => {
    // jsdom reports every width as zero, so nothing is clipped and nothing is
    // faded — which is the assertion: the fade is measured, not assumed from
    // the breakpoint. A row that fits is never faded.
    render(<Scenarios />);
    expect(strip().className).not.toContain("fade-edge-x");
    const css = readFileSync(join(SRC, "index.css"), "utf8");
    expect(css).toMatch(/\.fade-edge-x\s*\{[^}]*mask-image/);
    expect(css).toMatch(/\.scrollbar-none::-webkit-scrollbar\s*\{\s*display: none/);
  });

  it("never reaches for scrollIntoView, which would take the page with it", () => {
    // A call, not the word: the comment that explains why we do not call it
    // says its name, and a bare substring scan would fail on its own reasoning.
    const source = readFileSync(join(SRC, "sections", "Scenarios.tsx"), "utf8");
    expect(source).not.toMatch(/scrollIntoView\s*\(/);
    expect(source).toMatch(/\.scrollLeft\s*=/);
  });
});
