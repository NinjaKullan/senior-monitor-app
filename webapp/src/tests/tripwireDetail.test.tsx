/**
 * AC1 / AC3 / AC4 — what the tripwire health view actually puts in the DOM.
 *
 * `tripwires.test.ts` proves the logic; this proves the rendering honours the
 * two rules that make this a maintenance surface rather than an activity feed.
 * The load-bearing one is the digit walk: day-granularity is only real if *no*
 * clock time reached the DOM, in text or in an attribute, so the test scans both
 * and allows exactly one shape of digit — the `3` in `3 days ago`.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Glance } from "@/screens/Glance";
import { TripwireDetail } from "@/screens/TripwireDetail";
import { computeGlance } from "@/lib/glance";
import { computeTripwires } from "@/lib/tripwires";
import { TRIPWIRE_CONNECTED, TRIPWIRE_STALE } from "@/lib/copy";
import type { Parent, ParentSignal, Ping } from "@/lib/types";

const IST = "Asia/Kolkata";
const HOUR = 3_600_000;
const NOW = new Date("2026-08-03T13:30:00Z"); // 19:00 IST

const amma: Parent = { id: "p1", family_id: "f1", display_name: "Amma", tz: null };
const appa: Parent = { id: "p2", family_id: "f1", display_name: "Appa", tz: null };

const signals: ParentSignal[] = [
  { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: "p1", signal: "news", alarm_grade: true, active: true },
  { parent_id: "p1", signal: "device_alive", alarm_grade: false, active: true },
  { parent_id: "p2", signal: "youtube", alarm_grade: true, active: true },
];

const ago = (signal: string, hours: number, parent = "p1"): Ping => ({
  parent_id: parent,
  signal,
  ts_utc: new Date(NOW.getTime() - hours * HOUR).toISOString(),
});

/** Everything reporting: WhatsApp today, News three days back, timer this morning. */
const HEALTHY = [ago("whatsapp", 2), ago("news", 72), ago("device_alive", 8), ago("youtube", 1, "p2")];
/** The timer has stopped — the case the repair flow exists for. */
const STALE = [ago("whatsapp", 2), ago("news", 72), ago("device_alive", 40)];

function renderDetail(pings: Ping[], parent = amma) {
  return render(
    <TripwireDetail
      glance={computeGlance(parent, IST, signals, pings, NOW, IST)}
      tripwires={computeTripwires(parent, IST, signals, pings, NOW)}
      onBack={() => undefined}
    />,
  );
}

const names = () => screen.getAllByTestId("tripwire-name").map((n) => n.textContent);
const healths = () =>
  screen.getAllByTestId("tripwire-health").map((n) => n.dataset.health);

describe("tapping through from the card", () => {
  it("opens the tapped parent, and hands back their id", () => {
    const onOpen = vi.fn();
    const states = [amma, appa].map((p) => computeGlance(p, IST, signals, HEALTHY, NOW, IST));
    render(<Glance states={states} onOpen={onOpen} />);

    fireEvent.click(screen.getAllByTestId("glance-card-tap")[1]);
    expect(onOpen).toHaveBeenCalledWith("p2");
  });
});

describe("what the detail view lists", () => {
  it("shows this parent's tripwires and none of the other parent's", () => {
    renderDetail(HEALTHY);
    expect(names()).toEqual(["WhatsApp", "News", "Daily Check"]);
    expect(screen.getByTestId("tripwire-detail").textContent).not.toContain("YouTube");
  });

  it("repeats the card's own headline rather than computing a new state", () => {
    renderDetail(HEALTHY);
    const detail = screen.getByTestId("detail-headline").textContent;
    render(<Glance states={[computeGlance(amma, IST, signals, HEALTHY, NOW, IST)]} />);
    expect(screen.getByTestId("glance-headline").textContent).toBe(detail);
  });

  it("carries the beacon through unchanged — still phone status, never person status", () => {
    renderDetail(HEALTHY);
    expect(screen.getByTestId("beacon").textContent).toBe("phone");
    expect(screen.getByTestId("beacon")).toHaveAttribute("data-state", "breathing");
  });

  it("reads the day-granularity recency, and reads it in words for the near days", () => {
    renderDetail(HEALTHY);
    expect(screen.getAllByTestId("tripwire-recency").map((n) => n.textContent)).toEqual([
      "today",
      "3 days ago",
      "today",
    ]);
  });

  it("says never for a tripwire that has never reported", () => {
    renderDetail([ago("whatsapp", 2)]);
    expect(screen.getAllByTestId("tripwire-recency").map((n) => n.textContent)).toEqual([
      "today",
      "never",
      "never",
    ]);
  });
});

/**
 * The ruling on item 60, at the pixel: absence of *ever* is not-yet-configured,
 * not broken. Both cases the PM named, asserted against what actually renders.
 */
describe("a parent whose shortcuts are not installed yet", () => {
  it("opens with no amber and no nudge — nothing needs fixing yet", () => {
    renderDetail([]);
    expect(healths()).toEqual(["unconfigured", "unconfigured", "unconfigured"]);
    expect(screen.getByTestId("tripwire-detail").textContent).toContain("Not set up yet");
    for (const chip of screen.getAllByTestId("tripwire-health")) {
      expect(chip.className, `${chip.textContent} rendered in amber`).not.toContain("attention");
    }
    expect(screen.queryByTestId("repair-nudge")).toBeNull();
  });

  it("turns amber and nudges once a tripwire that really reported goes quiet", () => {
    // One real ping, then eight days of silence — past the seven-day window.
    renderDetail([ago("news", 8 * 24)]);
    const news = screen.getAllByTestId("tripwire-health")[1];
    expect(news.dataset.health).toBe("stale");
    expect(news.className).toContain("text-attention");
    expect(screen.getByTestId("repair-nudge")).not.toBeNull();
  });

  it("keeps the unconfigured chip quieter than the connected one", () => {
    // It should read like an empty field, not like a state worth colouring.
    renderDetail([ago("whatsapp", 2)]);
    const [whatsapp, news] = screen.getAllByTestId("tripwire-health");
    expect(whatsapp.className).toContain("text-calm");
    expect(news.className).toContain("text-muted-foreground");
  });
});

describe("AC3 — day granularity, proved at the DOM", () => {
  // `3 days ago` is the only digit this view may render. No leading \b: element
  // text runs together into one string ("Connected3 days ago"), and a boundary
  // there would quietly stop the mask matching — and a mask that never matches
  // is a test that allows nothing but also proves nothing.
  const DAY_COUNT = /\d+ days ago/g;
  const CLOCK = /\b\d{1,2}:\d{2}\s?[ap]m\b/gi;

  function assertNoClockAnywhere(root: HTMLElement) {
    const text = (root.textContent ?? "").replace(DAY_COUNT, "");
    expect(text.match(CLOCK) ?? [], `clock time in: ${root.textContent}`).toHaveLength(0);
    expect(text.replace(/[^\d]/g, ""), `stray digits in: ${root.textContent}`).toBe("");

    for (const node of [root, ...Array.from(root.querySelectorAll("*"))]) {
      for (const attr of Array.from(node.attributes)) {
        // Classes carry Tailwind's sizing scale; nothing else may carry digits.
        if (attr.name === "class" || attr.name === "style") continue;
        expect(
          /\d/.test(attr.value),
          `${attr.name}="${attr.value}" carries a number a screen reader could read`,
        ).toBe(false);
      }
    }
  }

  it("spends no clock time and no stray digit, in text or in an attribute", () => {
    for (const pings of [HEALTHY, STALE, [] as Ping[]]) {
      const { unmount } = renderDetail(pings);
      assertNoClockAnywhere(screen.getByTestId("tripwire-detail"));
      unmount();
    }
  });

  it("would catch a clock time, or any other number, smuggled back in", () => {
    const plant = (html: string) => {
      const node = document.createElement("div");
      node.innerHTML = html;
      return () => assertNoClockAnywhere(node);
    };
    expect(plant("Daily Check · last heard 8:12 am")).toThrow();
    // The day-count mask must not become a blanket digit allowance.
    expect(plant("WhatsApp · opened 4 times")).toThrow();
    expect(plant('<span data-days="3">News</span>')).toThrow();
    expect(plant("News · 3 days ago")).not.toThrow();
  });

  it("renders no count of anything — the only numbers are day counts", () => {
    // One ping and many pings for the same signal must render identically: a
    // maintenance list that got denser with use would be an activity feed.
    const many = [10, 20, 30, 40].map((h) => ago("whatsapp", h)).concat(ago("news", 72));
    const sparse = renderDetail([ago("whatsapp", 10), ago("news", 72)]);
    const sparseHtml = sparse.container.innerHTML;
    sparse.unmount();
    expect(renderDetail(many).container.innerHTML).toBe(sparseHtml);
  });
});

describe("AC4 — the repair nudge, and the tone of the chip", () => {
  it("appears only when a tripwire is stale, with the copy the spec fixes", () => {
    const healthy = renderDetail(HEALTHY);
    expect(screen.queryByTestId("repair-nudge")).toBeNull();
    healthy.unmount();

    renderDetail(STALE);
    expect(screen.getByTestId("repair-nudge").textContent).toBe(
      "A tripwire may need a quick fix on Amma's phone. It's a two-minute FaceTime.",
    );
  });

  it("describes the equipment, in amber, and never reaches past it to the person", () => {
    renderDetail(STALE);
    expect(healths()).toEqual(["connected", "connected", "stale"]);

    const stale = screen
      .getAllByTestId("tripwire-health")
      .find((n) => n.dataset.health === "stale")!;
    expect(stale.textContent).toBe(TRIPWIRE_STALE);
    // Amber is the ceiling: no red, no destructive, on any chip on this screen.
    for (const chip of screen.getAllByTestId("tripwire-health")) {
      expect(chip.className).not.toMatch(/red|destructive/);
    }
    expect(stale.className).toContain("text-attention");
  });

  it("names no person-state anywhere in either chip", () => {
    for (const chip of [TRIPWIRE_CONNECTED, TRIPWIRE_STALE]) {
      expect(chip.toLowerCase()).not.toMatch(/\b(she|he|they|amma|appa|ok|fine|well)\b/);
    }
  });
});
