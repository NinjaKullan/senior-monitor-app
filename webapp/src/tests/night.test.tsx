/**
 * @vitest-environment jsdom
 *
 * DECISIONS 303: night is not quiet. Between midnight and DAY_START_HOUR in
 * the parent's zone the card says the night; paused and unreachable still
 * win; the rollup leaves a night parent out like a paused one, and says the
 * night when nobody is left. The arc and the dots are unchanged (299).
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  NIGHT_CARD,
  NIGHT_CARD_NO_CITY,
  PAUSED_CARD,
  ROLLUP_NIGHT_ALL,
  ROLLUP_NORMAL,
  ROLLUP_SUB_EVENING,
  ROLLUP_SUB_MORNING,
  STATE_QUIET,
  STATE_UNREACHABLE,
  renderHeard,
} from "@/lib/copy";
import { DAY_START_HOUR, computeParentToday, computeRollup } from "@/lib/parentState";
import { Today } from "@/screens/Today";
import type { Parent, ParentSignal, Ping } from "@/lib/types";

const IST = "Asia/Kolkata";
const CHICAGO = "America/Chicago";
/** Appa's card at 1:02 am Chennai, Sunday Sep 6 — a US Saturday afternoon. */
const AT_0102 = new Date("2026-09-05T19:32:00Z");
const AT_0559 = new Date("2026-09-06T00:29:00Z");
const AT_0600 = new Date("2026-09-06T00:30:00Z");

const parent = (over: Partial<Parent>): Parent => ({
  id: "p2",
  family_id: "f1",
  display_name: "Appa",
  tz: null,
  phone_e164: "+919812345678",
  whatsapp_e164: null,
  relationship: "Dad",
  city_label: "Chennai",
  tz_changed_utc: null,
  paused_until: null,
  paused_since: null,
  sms_consent_utc: null,
  sms_opted_out_utc: null,
  ...over,
});
const appa = parent({});
const amma = parent({ id: "p1", display_name: "Amma", relationship: "Mom" });

const signals: ParentSignal[] = [amma, appa].flatMap((p) => [
  { parent_id: p.id, signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: p.id, signal: "device_alive", alarm_grade: false, active: true },
]);
/** 11:19 pm Chennai the evening before. */
const LATE_PING: Ping = { parent_id: "p2", signal: "whatsapp", ts_utc: "2026-09-05T17:49:00Z" };
const stateOf = (p: Parent, pings: Ping[], now = AT_0102) =>
  computeParentToday(p, IST, signals, pings, pings, now, CHICAGO);

describe("the night card (DECISIONS 303)", () => {
  it("Appa at 1:02 am Chennai reads the night in his city, facts unchanged", () => {
    const state = stateOf(appa, [LATE_PING]);
    expect(state.night).toBe(true);
    expect(state.sentence).toBe(NIGHT_CARD.replace("{city}", "Chennai"));
    expect(state.sentence).toBe("Night in Chennai.");
    expect(state.heard).toBe(renderHeard(AT_0102.getTime() - Date.parse(LATE_PING.ts_utc)));
    expect(state.dualLine).toContain("11:19 pm");
    expect(state.callHref).toBe("tel:+919812345678");
    expect(state.viewLabel).toContain("Appa");
    // The arc and the dots are 299's: the night ping is yesterday's normal day.
    expect(state.arcCells[0].text).toBe("Quiet so far");
    expect(state.recentDots[5].kind).toBe("normal");
  });

  it("falls back to the name when there is no city label", () => {
    const state = stateOf(parent({ city_label: null }), [LATE_PING]);
    expect(state.sentence).toBe(NIGHT_CARD_NO_CITY.replace("{name}", "Appa"));
    expect(state.sentence).toBe("Night for Appa.");
  });

  it("is night at 5:59 and not at 6:00, on DAY_START_HOUR", () => {
    expect(DAY_START_HOUR).toBe(6);
    expect(stateOf(appa, [LATE_PING], AT_0559).night).toBe(true);
    const morning = stateOf(appa, [LATE_PING], AT_0600);
    expect(morning.night).toBe(false);
    expect(morning.sentence).toBe(STATE_QUIET);
  });

  it("paused wins over night", () => {
    const state = stateOf(parent({ paused_until: "infinity", paused_since: "2026-09-04T00:00:00Z" }), [LATE_PING]);
    expect(state.paused).toBe(true);
    expect(state.night).toBe(false);
    render(<Today states={[state]} rollup={computeRollup([state], IST, AT_0102)} dateLine="Saturday · September 5" onOpen={() => undefined} />);
    expect(screen.getByTestId("card-line")).toHaveTextContent(PAUSED_CARD.replace("{name}", "Appa"));
  });

  it("unreachable wins over night: a stale phone at night is still a stale phone", () => {
    const stale: Ping[] = [
      { parent_id: "p2", signal: "whatsapp", ts_utc: "2026-08-20T05:30:00Z" },
      { parent_id: "p2", signal: "device_alive", ts_utc: "2026-08-20T05:30:00Z" },
    ];
    const state = stateOf(appa, stale);
    expect(state.kind).toBe("unreachable");
    expect(state.night).toBe(false);
    expect(state.sentence).toBe(STATE_UNREACHABLE.replace("{name}", "Appa"));
  });

  it("renders the night sentence on the Today card with heard from beneath it", () => {
    const state = stateOf(appa, [LATE_PING]);
    render(<Today states={[state]} rollup={computeRollup([state], IST, AT_0102)} dateLine="Saturday · September 5" onOpen={() => undefined} />);
    expect(screen.getByTestId("card-line")).toHaveTextContent("Night in Chennai.");
    expect(screen.getByTestId("card-heard")).toHaveTextContent(state.heard);
    expect(screen.getByTestId("card-dual")).toHaveTextContent("11:19 pm");
    expect(screen.getByTestId("view-day")).toBeInTheDocument();
  });
});

describe("the rollup at night (303)", () => {
  /** Amma in Austin: a normal afternoon there while Appa sleeps in Chennai. */
  const austinAmma = parent({ ...amma, tz: CHICAGO, city_label: "Austin" });
  const ammaPing: Ping = { parent_id: "p1", signal: "whatsapp", ts_utc: "2026-09-05T13:00:00Z" };

  it("leaves a night parent out: one at night, one normal, reads normal", () => {
    const states = [stateOf(austinAmma, [ammaPing]), stateOf(appa, [LATE_PING])];
    expect(states.map((s) => [s.kind, s.night])).toEqual([["ordinary", false], ["quiet", true]]);
    const rollup = computeRollup(states, IST, AT_0102);
    expect(rollup.line).toBe(ROLLUP_NORMAL);
    expect(rollup.sub).toBe(ROLLUP_SUB_EVENING);
    render(<Today states={states} rollup={rollup} dateLine="Saturday · September 5" onOpen={() => undefined} />);
    expect(screen.getByTestId("rollup")).toHaveTextContent(ROLLUP_NORMAL);
    expect(screen.getByTestId("today-foot")).toBeInTheDocument();
  });

  it("says the night for everyone when nobody is left, with the morning sub line", () => {
    const states = [stateOf(amma, []), stateOf(appa, [LATE_PING])];
    const rollup = computeRollup(states, IST, AT_0102);
    expect(rollup.line).toBe(ROLLUP_NIGHT_ALL.replace("{names}", "Amma and Appa"));
    expect(rollup.line).toBe("Night for Amma and Appa.");
    expect(rollup.sub).toBe(ROLLUP_SUB_MORNING);
  });

  it("a paused parent beside a night one still reads the night for the night one", () => {
    const paused = stateOf(parent({ ...amma, paused_until: "infinity", paused_since: "2026-09-04T00:00:00Z" }), []);
    const rollup = computeRollup([paused, stateOf(appa, [LATE_PING])], IST, AT_0102);
    expect(rollup.line).toBe("Night for Appa.");
  });
});
