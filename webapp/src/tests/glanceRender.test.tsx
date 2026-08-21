/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * AC2 / AC3 — what the day arc and the beacon actually put in the DOM.
 *
 * `glance.test.ts` proves the logic; this proves the rendering honours it. The
 * two assertions worth the file: the arc carries no number anywhere a reader or
 * a screen reader could find one, and the breathing animation is attached to a
 * data state rather than to every beacon that happens to render.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Glance } from "@/screens/Glance";
import { BEACON_FRESH_HOURS, computeGlance } from "@/lib/glance";
import type { Parent, ParentSignal, Ping } from "@/lib/types";

const IST = "Asia/Kolkata";
const NOW = new Date("2026-08-03T13:30:00Z"); // 19:00 IST — evening
const HOUR = 3_600_000;

const amma: Parent = { id: "p1", family_id: "f1", display_name: "Amma", tz: null };
const withMechanism: ParentSignal[] = [
  { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: "p1", signal: "device_alive", alarm_grade: false, active: true },
];
const alarmOnly: ParentSignal[] = [withMechanism[0]];

const routine = (istHour: number): Ping => ({
  parent_id: "p1",
  signal: "whatsapp",
  ts_utc: new Date(`2026-08-03T${String(istHour).padStart(2, "0")}:30:00+05:30`).toISOString(),
});
const timerAgo = (hours: number): Ping => ({
  parent_id: "p1",
  signal: "device_alive",
  ts_utc: new Date(NOW.getTime() - hours * HOUR).toISOString(),
});

function renderGlance(signals: ParentSignal[], pings: Ping[]) {
  return render(<Glance states={[computeGlance(amma, IST, signals, pings, NOW, IST)]} />);
}

describe("the day arc in the DOM", () => {
  it("glows the segments routine happened in and leaves the rest neutral", () => {
    renderGlance(withMechanism, [routine(8), routine(15)]);
    expect(screen.getAllByTestId("arc-segment").map((n) => n.dataset.state)).toEqual([
      "lit",
      "lit",
      "ahead",
    ]);
  });

  it("carries no number a reader or a screen reader could find", () => {
    renderGlance(withMechanism, [routine(8), routine(15)]);
    const arc = screen.getByTestId("day-arc");
    expect(arc.textContent).toBe("");
    for (const node of [arc, ...arc.querySelectorAll("*")]) {
      for (const attr of Array.from(node.attributes)) {
        // Classes carry Tailwind's sizing scale; nothing else may carry digits.
        if (attr.name === "class" || attr.name === "style") continue;
        expect(/\d/.test(attr.value), `${attr.name}="${attr.value}" carries a number`).toBe(
          false,
        );
      }
    }
    expect(arc.getAttribute("aria-label")).toBe("Routine seen: morning, afternoon");
  });

  it("says so plainly, without a number, when nothing has been seen", () => {
    renderGlance(withMechanism, []);
    expect(screen.getByTestId("day-arc")).toHaveAttribute(
      "aria-label",
      "No routine seen yet today",
    );
  });

  it("renders at most three states across every fixture", () => {
    const states = new Set<string | undefined>();
    for (const pings of [[], [routine(8)], [routine(8), routine(15), routine(19)]]) {
      const { unmount } = renderGlance(withMechanism, pings);
      screen.getAllByTestId("arc-segment").forEach((n) => states.add(n.dataset.state));
      unmount();
    }
    expect(states.size).toBeLessThanOrEqual(3);
  });
});

describe("the beacon in the DOM", () => {
  it("breathes only on a fresh mechanism signal", () => {
    renderGlance(withMechanism, [timerAgo(2)]);
    expect(screen.getByTestId("beacon")).toHaveAttribute("data-state", "breathing");
    expect(screen.getByTestId("beacon-dot").className).toContain("animate-breathe");
  });

  it("goes still and grey when the signal is stale — never red", () => {
    renderGlance(withMechanism, [timerAgo(BEACON_FRESH_HOURS + 2)]);
    const dot = screen.getByTestId("beacon-dot");
    expect(screen.getByTestId("beacon")).toHaveAttribute("data-state", "still");
    expect(dot.className).not.toContain("animate-breathe");
    expect(dot.className).not.toMatch(/red|destructive/);
  });

  it("is absent, not faked, when no mechanism signal is configured", () => {
    renderGlance(alarmOnly, [routine(8)]);
    expect(screen.queryByTestId("beacon")).toBeNull();
  });

  it("says nothing about the person — it is labelled phone", () => {
    renderGlance(withMechanism, [timerAgo(2)]);
    expect(screen.getByTestId("beacon").textContent).toBe("phone");
  });
});
