/** AC2 — the Glance states, as pure logic. */
import { describe, expect, it } from "vitest";
import { computeGlance } from "@/lib/glance";
import { GLANCE_ALL_NORMAL, GLANCE_QUIET } from "@/lib/copy";
import type { Parent, ParentSignal, Ping } from "@/lib/types";

const IST = "Asia/Kolkata";
const parent: Parent = { id: "p1", family_id: "f1", display_name: "Amma", tz: null };

const signals: ParentSignal[] = [
  { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: "p1", signal: "device_alive", alarm_grade: false, active: true },
];

// 2026-08-03, 08:12 IST == 02:42Z; "now" is 12:00 IST == 06:30Z.
const NOW = new Date("2026-08-03T06:30:00Z");

describe("computeGlance", () => {
  it("says All normal when a routine ping landed today", () => {
    const pings: Ping[] = [{ parent_id: "p1", signal: "whatsapp", ts_utc: "2026-08-03T02:42:00Z" }];
    const state = computeGlance(parent, IST, signals, pings, NOW);
    expect(state.status).toBe(GLANCE_ALL_NORMAL);
    expect(state.lastSeen).toBe("8:12 am");
  });

  it("says Quiet so far when nothing routine has landed yet", () => {
    const state = computeGlance(parent, IST, signals, [], NOW);
    expect(state.status).toBe(GLANCE_QUIET);
    expect(state.lastSeen).toBeNull();
  });

  it("never lets a timer ping stand in for a person", () => {
    const pings: Ping[] = [
      { parent_id: "p1", signal: "device_alive", ts_utc: "2026-08-03T01:30:00Z" },
    ];
    const state = computeGlance(parent, IST, signals, pings, NOW);
    expect(state.status).toBe(GLANCE_QUIET);
  });

  it("keeps yesterday's routine out of today's verdict", () => {
    const pings: Ping[] = [{ parent_id: "p1", signal: "whatsapp", ts_utc: "2026-08-02T14:00:00Z" }];
    const state = computeGlance(parent, IST, signals, pings, NOW);
    expect(state.status).toBe(GLANCE_QUIET);
    // …but still reports when they were last seen.
    expect(state.lastSeen).toBe("7:30 pm");
  });

  it("uses the parent's own timezone when they have one", () => {
    const travelling: Parent = { ...parent, tz: "America/Chicago" };
    // 02:42Z is 21:42 the previous day in Chicago, so this is not "today" there.
    const pings: Ping[] = [{ parent_id: "p1", signal: "whatsapp", ts_utc: "2026-08-03T02:42:00Z" }];
    const state = computeGlance(travelling, IST, signals, pings, NOW);
    expect(state.timeZone).toBe("America/Chicago");
    expect(state.status).toBe(GLANCE_QUIET);
  });

  it("ignores another parent's pings", () => {
    const pings: Ping[] = [{ parent_id: "p2", signal: "whatsapp", ts_utc: "2026-08-03T02:42:00Z" }];
    expect(computeGlance(parent, IST, signals, pings, NOW).status).toBe(GLANCE_QUIET);
  });

  it("respects a deactivated signal", () => {
    const off: ParentSignal[] = [
      { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: false },
    ];
    const pings: Ping[] = [{ parent_id: "p1", signal: "whatsapp", ts_utc: "2026-08-03T02:42:00Z" }];
    expect(computeGlance(parent, IST, off, pings, NOW).status).toBe(GLANCE_QUIET);
  });
});
