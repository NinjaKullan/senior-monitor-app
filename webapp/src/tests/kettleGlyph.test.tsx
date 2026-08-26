/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * The glyph's grammar (spec 008 §3), and the detail surfaces it gates.
 *
 * One component carries the whole three-state language, so what it may say in
 * each state is pinned as behaviour: steam only when a parent's day is
 * ordinary, pause bars only when the phone is unreachable, "The kettle's on"
 * only inside the ordinary hero — and the steam *animates* only there, via
 * classes that exist solely under prefers-reduced-motion: no-preference. The
 * 44px card glyph is always still: a grid of eight animated cards is noise,
 * and motion someone opted out of is worse than noise.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { KettleGlyph, type GlyphState } from "@/components/KettleGlyph";
import { ParentDetail } from "@/screens/ParentDetail";
import type { ParentToday } from "@/lib/parentState";

const STATES: GlyphState[] = ["ordinary", "quiet", "unreachable"];
const SIZES = [44, 200] as const;

const NONE = "rgba(0,0,0,0)";

/** Inline fills/strokes, read off the style attribute React writes. */
function inline(el: Element, property: "fill" | "stroke"): string {
  const match = (el.getAttribute("style") ?? "").match(
    new RegExp(`(?:^|;)\\s*${property}:\\s*([^;]+)`),
  );
  return match ? match[1].trim() : "";
}

function renderGlyph(state: GlyphState, size: 44 | 200) {
  const view = render(<KettleGlyph state={state} size={size} />);
  const svg = screen.getByTestId("kettle-glyph");
  return { view, svg };
}

describe("the three-state glyph", () => {
  it("steams only on an ordinary day", () => {
    for (const state of STATES) {
      for (const size of SIZES) {
        const { view, svg } = renderGlyph(state, size);
        const steaming = [...svg.querySelectorAll("rect")].filter(
          (rect) => inline(rect, "fill") !== NONE && inline(rect, "fill") !== "var(--mute)",
        );
        expect(steaming.length, `${state} at ${size}`).toBe(state === "ordinary" ? 2 : 0);
        view.unmount();
      }
    }
  });

  it("shows the pause bars only when the phone is unreachable", () => {
    for (const state of STATES) {
      for (const size of SIZES) {
        const { view, svg } = renderGlyph(state, size);
        const paused = [...svg.querySelectorAll("rect")].filter(
          (rect) => inline(rect, "fill") === "var(--mute)",
        );
        expect(paused.length, `${state} at ${size}`).toBe(state === "unreachable" ? 2 : 0);
        view.unmount();
      }
    }
  });

  it("draws no cup when the phone is unreachable", () => {
    for (const state of STATES) {
      const { view, svg } = renderGlyph(state, 200);
      const drawnPaths = [...svg.querySelectorAll("path")].filter(
        (path) => inline(path, "stroke") !== NONE,
      );
      expect(drawnPaths.length, state).toBe(state === "unreachable" ? 0 : 2);
      view.unmount();
    }
  });

  it("says The kettle's on only inside the ordinary hero", () => {
    for (const state of STATES) {
      for (const size of SIZES) {
        const { view } = renderGlyph(state, size);
        const label = screen.queryByTestId("kettles-on");
        if (state === "ordinary" && size === 200) {
          expect(label?.textContent).toBe("The kettle’s on");
        } else {
          expect(label, `${state} at ${size}`).toBeNull();
        }
        view.unmount();
      }
    }
  });

  it("animates the steam only on the hero — the 44px card glyph is still", () => {
    for (const state of STATES) {
      for (const size of SIZES) {
        const { view, svg } = renderGlyph(state, size);
        const animated = svg.querySelectorAll(".kt-steam-hero, .kt-steam-hero-late");
        expect(animated.length, `${state} at ${size}`).toBe(
          state === "ordinary" && size === 200 ? 2 : 0,
        );
        view.unmount();
      }
    }
  });

  it("carries its state and size as data for the screens to trust", () => {
    const { svg } = renderGlyph("quiet", 44);
    expect(svg.getAttribute("data-glyph-state")).toBe("quiet");
    expect(svg.getAttribute("data-glyph-size")).toBe("44");
  });
});

/**
 * The detail's gates. Built on hand-rolled states so each gate is tested in
 * isolation — the mapping from pings to states is parentState.test.ts's job.
 */
const base: ParentToday = {
  parentId: "p1",
  label: "Amma",
  kind: "ordinary",
  sentence: "Today looks like a normal day.",
  heard: "Heard from 12 minutes ago",
  dualLine: "7:52 pm in Chennai · 10:22 am your time",
  cityNow: "Chennai · 8:04 pm there now",
  heroKicker: "Amma · Chennai",
  heroSub: "7:52 pm in Chennai · 10:22 am your time · nine and a half hours ahead of you",
  arcFraction: 0.82,
  arcCells: [
    { part: "Morning", text: "Heard from 7:19 am", dim: false },
    { part: "Afternoon", text: "Heard from 12:07 pm", dim: false },
    { part: "Evening", text: "Heard from 7:52 pm", dim: false },
  ],
  recentDots: [
    { abbr: "Wed", kind: "normal" },
    { abbr: "Thu", kind: "normal" },
    { abbr: "Fri", kind: "normal" },
    { abbr: "Sat", kind: "quiet" },
    { abbr: "Sun", kind: "none" },
    { abbr: "Mon", kind: "normal" },
    { abbr: "Tue", kind: "normal" },
  ],
  meansHead: "No action needed.",
  meansBody: "Amma's day looks like most days. Kettle will write if that changes.",
  callHref: null,
  callLabel: "Call Amma ↗",
  viewLabel: "View Amma's day →",
  aside: null,
  tzNote: "Nine and a half hours ahead of you.",
  famSub: "Nine and a half hours ahead of you",
  needsFix: false,
  timeZone: "Asia/Kolkata",
};

const detailProps = {
  notes: [],
  todayDate: "2026-08-26",
  onBack: () => undefined,
  onAddNote: async () => undefined,
  onSteps: () => undefined,
};

describe("the parent detail's gates", () => {
  it("renders the Call button only when a number exists — never a dead button", () => {
    const without = render(<ParentDetail state={base} {...detailProps} />);
    expect(screen.queryByTestId("call-button")).toBeNull();
    without.unmount();

    render(
      <ParentDetail state={{ ...base, callHref: "tel:+919812345678" }} {...detailProps} />,
    );
    const button = screen.getByTestId("call-button");
    expect(button.getAttribute("href")).toBe("tel:+919812345678");
    expect(button.textContent).toBe("Call Amma ↗");
  });

  it("shows the fix card only when something has actually stopped reporting", () => {
    const calm = render(<ParentDetail state={base} {...detailProps} />);
    expect(screen.queryByTestId("fix-card")).toBeNull();
    calm.unmount();

    render(<ParentDetail state={{ ...base, needsFix: true }} {...detailProps} />);
    // DECISIONS 172's body, split head/body at the sentence per the mockup —
    // nothing reworded in the split.
    expect(screen.getByTestId("fix-head").textContent).toBe(
      "Something on Amma's phone may need a quick fix.",
    );
    expect(screen.getByTestId("fix-body").textContent).toBe("It's a two-minute FaceTime.");
    expect(screen.getByTestId("fix-steps").textContent).toBe("See the simple steps →");
  });

  it("keeps the unreachable aside out of the other states", () => {
    const ordinary = render(<ParentDetail state={base} {...detailProps} />);
    expect(screen.queryByTestId("detail-aside")).toBeNull();
    ordinary.unmount();

    render(
      <ParentDetail
        state={{
          ...base,
          kind: "unreachable",
          aside: "A call still works fine — this is only about the phone.",
        }}
        {...detailProps}
      />,
    );
    expect(screen.getByTestId("detail-aside")).toBeInTheDocument();
    expect(screen.getByTestId("kettle-glyph").getAttribute("data-glyph-state")).toBe(
      "unreachable",
    );
  });

  it("draws the arc as one curve twice, with the dot on the reveal's end", () => {
    // Spec 009 §3: never two different curves — both path elements carry an
    // identical d, the reveal uses pathLength/dasharray, and the dot's
    // coordinates come from the same quadratic at the same t.
    render(<ParentDetail state={base} {...detailProps} />);
    const svg = screen.getByTestId("day-arc-svg");
    const paths = [...svg.querySelectorAll("path")];
    expect(paths).toHaveLength(2);
    expect(paths[0].getAttribute("d")).toBe(paths[1].getAttribute("d"));
    expect(paths[1].getAttribute("pathLength")).toBe("100");
    expect(paths[1].getAttribute("stroke-dasharray")).toBe("82.0 100");
    const dot = svg.querySelector("circle")!;
    // The mockup's own 82% point, to one decimal: (254.7, 35.3).
    expect(dot.getAttribute("cx")).toBe("254.7");
    expect(dot.getAttribute("cy")).toBe("35.3");
  });

  it("keeps every digit out of the dots panel — chips carry no tally", () => {
    render(<ParentDetail state={base} {...detailProps} />);
    const panel = screen.getByTestId("recent-panel");
    expect(panel.textContent ?? "").not.toMatch(/\d/);
    expect(screen.getAllByTestId("recent-dot")).toHaveLength(7);
    // The legend is always visible, in words.
    expect(panel.textContent).toContain("A normal day");
    expect(panel.textContent).toContain("A quiet start");
    expect(panel.textContent).toContain("Couldn't hear");
  });

  it("keeps the normal dot the only filled chip — never color alone", () => {
    render(<ParentDetail state={base} {...detailProps} />);
    for (const cell of screen.getAllByTestId("recent-dot")) {
      const chip = cell.querySelector("span")!;
      const style = chip.getAttribute("style") ?? "";
      if (cell.getAttribute("data-dot-kind") === "normal") {
        expect(style).toContain("background: var(--hearthfill)");
      } else {
        expect(style).toContain("background: none");
      }
    }
  });
});
