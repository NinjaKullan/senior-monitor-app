/**
 * @vitest-environment jsdom
 *
 * Spec 017 §7, the webapp half: the control is hidden for members; the
 * paused card renders with the right second line for each duration; the
 * admin's resume button; the rollup and footer leave a paused parent out;
 * the Family setup row says Paused.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Today } from "@/screens/Today";
import {
  PAUSED_CARD,
  PAUSED_OPEN_ENDED,
  PAUSED_UNTIL,
  PAUSE_LINK,
  PAUSE_OPEN,
  PAUSE_WEEK,
  RESUME_BUTTON,
  ROLLUP_NORMAL,
  TODAY_FOOT_STRONG,
} from "@/lib/copy";
import { computeParentToday, computeRollup, isPaused, pausedLineFor } from "@/lib/parentState";
import { buildSetupEntries } from "@/lib/setupLinks";
import type { Parent, Ping } from "@/lib/types";

const IST = "Asia/Kolkata";
const NOW = new Date("2026-09-04T06:30:00Z"); // 12:00 IST

const parent = (over: Partial<Parent>): Parent => ({
  id: "p1",
  family_id: "f1",
  display_name: "Amma",
  tz: null,
  phone_e164: null,
  whatsapp_e164: null,
  relationship: "Mom",
  city_label: null,
  tz_changed_utc: null,
  paused_until: null,
  paused_since: null,
  ...over,
});

const amma = parent({});
const appa = parent({ id: "p2", display_name: "Appa", relationship: "Dad" });
const weekPaused = parent({ paused_until: "2026-09-10T20:30:00Z", paused_since: "2026-09-03T20:30:00Z" });
const openPaused = parent({ paused_until: "infinity", paused_since: "2026-09-03T20:30:00Z" });
const signals = [amma, appa].map((p) => ({ parent_id: p.id, signal: "whatsapp", alarm_grade: true, active: true }));
const pings: Ping[] = [
  { parent_id: "p1", signal: "whatsapp", ts_utc: "2026-09-04T02:00:00Z" },
  { parent_id: "p2", signal: "whatsapp", ts_utc: "2026-09-04T02:00:00Z" },
];
const stateOf = (p: Parent) => computeParentToday(p, IST, signals, pings, pings, NOW, "America/Chicago");

const actions = () => ({
  onPause: vi.fn().mockResolvedValue(undefined),
  onResume: vi.fn().mockResolvedValue(undefined),
});

function renderToday(parents: Parent[], pause?: ReturnType<typeof actions>) {
  const states = parents.map(stateOf);
  render(
    <Today
      states={states}
      rollup={computeRollup(states, IST, NOW)}
      dateLine="Friday · September 4"
      onOpen={() => undefined}
      pause={pause}
    />,
  );
}

describe("the paused state (spec 017)", () => {
  it("reads an instant ahead of now, or the open-ended value, as paused", () => {
    expect(isPaused(amma, NOW)).toBe(false);
    expect(isPaused(weekPaused, NOW)).toBe(true);
    expect(isPaused(openPaused, NOW)).toBe(true);
    // A pause that ended is not a pause, whatever the fields still say.
    expect(isPaused(parent({ paused_until: "2026-09-01T00:00:00Z" }), NOW)).toBe(false);
  });

  it("writes the second line on the family's day, or the open-ended sentence", () => {
    // 20:30 UTC on Sep 10 is 02:00 on Sep 11 in Chennai: the family's day.
    expect(pausedLineFor(weekPaused, IST)).toBe(PAUSED_UNTIL.replace("{date}", "Sep 11"));
    expect(pausedLineFor(openPaused, IST)).toBe(PAUSED_OPEN_ENDED);
  });
});

describe("the Today card", () => {
  it("shows the paused card with the week line and no day", () => {
    renderToday([weekPaused]);
    const card = screen.getByTestId("today-card");
    expect(card.getAttribute("data-paused")).toBe("true");
    expect(screen.getByTestId("card-line")).toHaveTextContent(PAUSED_CARD.replace("{name}", "Amma"));
    expect(screen.getByTestId("card-paused-line")).toHaveTextContent("Back on Sep 11.");
    expect(screen.queryByTestId("card-heard")).toBeNull();
    expect(screen.queryByTestId("view-day")).toBeNull();
  });

  it("shows the open-ended line for the open-ended pause", () => {
    renderToday([openPaused]);
    expect(screen.getByTestId("card-paused-line")).toHaveTextContent(PAUSED_OPEN_ENDED);
  });

  it("hides every control from a member", () => {
    renderToday([amma, openPaused]);
    expect(screen.queryByTestId("pause-link")).toBeNull();
    expect(screen.queryByTestId("resume-button")).toBeNull();
    expect(screen.getAllByTestId("today-card")).toHaveLength(2);
  });

  it("offers an admin the two durations behind one link, and Not now closes them", async () => {
    const pause = actions();
    renderToday([amma], pause);
    const link = screen.getByTestId("pause-link");
    expect(link).toHaveTextContent(PAUSE_LINK);
    fireEvent.click(link);
    expect(screen.getByTestId("pause-week")).toHaveTextContent(PAUSE_WEEK);
    expect(screen.getByTestId("pause-open")).toHaveTextContent(PAUSE_OPEN);
    fireEvent.click(screen.getByText("Not now"));
    expect(screen.queryByTestId("pause-choices")).toBeNull();
    fireEvent.click(screen.getByTestId("pause-link"));
    fireEvent.click(screen.getByTestId("pause-week"));
    await waitFor(() => expect(pause.onPause).toHaveBeenCalledWith("p1", "week"));
    fireEvent.click(screen.getByTestId("pause-link"));
    fireEvent.click(screen.getByTestId("pause-open"));
    await waitFor(() => expect(pause.onPause).toHaveBeenCalledWith("p1", "open"));
  });

  it("offers an admin the resume button on a paused card", async () => {
    const pause = actions();
    renderToday([openPaused], pause);
    const button = screen.getByTestId("resume-button");
    expect(button).toHaveTextContent(RESUME_BUTTON);
    fireEvent.click(button);
    await waitFor(() => expect(pause.onResume).toHaveBeenCalledWith("p1"));
  });

  it("leaves a paused parent out of the rollup and the footer", () => {
    // Amma normal, Appa paused AND silent all day: unpaused he would be
    // "Quiet so far for Appa" and no footer; paused, the day is normal.
    const quietAppa = parent({ ...appa, paused_until: "infinity" });
    const states = [
      stateOf(amma),
      computeParentToday(quietAppa, IST, signals, pings.slice(0, 1), pings.slice(0, 1), NOW, "America/Chicago"),
    ];
    expect(states[1].kind).not.toBe("ordinary");
    render(
      <Today states={states} rollup={computeRollup(states, IST, NOW)} dateLine="Friday · September 4" onOpen={() => undefined} />,
    );
    expect(screen.getByTestId("rollup")).toHaveTextContent(ROLLUP_NORMAL);
    expect(screen.getByTestId("today-foot")).toHaveTextContent(TODAY_FOOT_STRONG);
  });
});

describe("the Family setup row", () => {
  it("says Paused for a paused parent, whatever the phone is doing", () => {
    const entries = buildSetupEntries([weekPaused, appa], [], pings, NOW);
    expect(entries.map((e) => e.status)).toEqual(["paused", "reporting"]);
  });
});
