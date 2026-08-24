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
  name: "Amma",
  kind: "ordinary",
  sentence: "Today looks like an ordinary day.",
  meta: "Heard from at 8:12 am Amma's time.",
  localTime: "12:00 pm",
  localLine: "It's 12:00 pm Amma's time right now.",
  aside: null,
  dayRows: [
    { part: "Morning", text: "An ordinary morning — heard from at 8:12 am.", dim: false },
    { part: "Afternoon", text: "Quiet so far.", dim: false },
    { part: "Evening", text: "Still to come.", dim: true },
  ],
  recentDays: [{ day: "Yesterday", line: "An ordinary day." }],
  tzNote: "The same time as yours.",
  famSub: "The same time as yours",
  setupLine: null,
  tel: null,
  callLabel: "Call Amma",
  needsFix: false,
  timeZone: "Asia/Kolkata",
};

describe("the parent detail's gates", () => {
  it("renders the Call button only when a number exists — never a dead button", () => {
    const without = render(<ParentDetail state={base} onBack={() => undefined} />);
    expect(screen.queryByTestId("call-button")).toBeNull();
    without.unmount();

    render(
      <ParentDetail state={{ ...base, tel: "tel:+919812345678" }} onBack={() => undefined} />,
    );
    const button = screen.getByTestId("call-button");
    expect(button.getAttribute("href")).toBe("tel:+919812345678");
    expect(button.textContent).toBe("Call Amma");
  });

  it("shows the fix card only when a tripwire has actually stopped reporting", () => {
    const calm = render(<ParentDetail state={base} onBack={() => undefined} />);
    expect(screen.queryByTestId("fix-card")).toBeNull();
    calm.unmount();

    render(<ParentDetail state={{ ...base, needsFix: true }} onBack={() => undefined} />);
    expect(screen.getByTestId("fix-body").textContent).toBe(
      "A tripwire may need a quick fix on Amma's phone. It's a two-minute FaceTime.",
    );
  });

  it("keeps the unreachable aside out of the other states", () => {
    const ordinary = render(<ParentDetail state={base} onBack={() => undefined} />);
    expect(screen.queryByTestId("detail-aside")).toBeNull();
    ordinary.unmount();

    render(
      <ParentDetail
        state={{
          ...base,
          kind: "unreachable",
          aside: "A call still works fine — this is only about the phone.",
        }}
        onBack={() => undefined}
      />,
    );
    expect(screen.getByTestId("detail-aside")).toBeInTheDocument();
    expect(screen.getByTestId("kettle-glyph").getAttribute("data-glyph-state")).toBe(
      "unreachable",
    );
  });
});
