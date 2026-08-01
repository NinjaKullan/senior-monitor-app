/** AC1–AC3 — glance logic: day-part copy, the day arc, the beacon. */
import { describe, expect, it } from "vitest";
import {
  BEACON_FRESH_HOURS,
  buildArc,
  computeBeacon,
  computeGlance,
  dayPartFor,
  headlineFor,
} from "@/lib/glance";
import {
  GLANCE_QUIET_MORNING,
  GLANCE_QUIET_TODAY,
  GLANCE_SEEN_AFTERNOON,
  GLANCE_SEEN_EVENING,
} from "@/lib/copy";
import type { Parent, ParentSignal, Ping } from "@/lib/types";

const IST = "Asia/Kolkata";
const CHICAGO = "America/Chicago";
const parent: Parent = { id: "p1", family_id: "f1", display_name: "Amma", tz: null };

const signals: ParentSignal[] = [
  { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: "p1", signal: "device_alive", alarm_grade: false, active: true },
];
const alarmOnly: ParentSignal[] = [signals[0]];

// 2026-08-03. IST is UTC+5:30, so 08:12 IST == 02:42Z.
const AT = (istClock: string) => new Date(`2026-08-03T${istClock}:00+05:30`);
const ROUTINE_MORNING: Ping = {
  parent_id: "p1",
  signal: "whatsapp",
  ts_utc: "2026-08-03T02:42:00Z", // 08:12 IST
};
const ROUTINE_AFTERNOON: Ping = {
  parent_id: "p1",
  signal: "whatsapp",
  ts_utc: "2026-08-03T09:30:00Z", // 15:00 IST
};

describe("day parts", () => {
  it("splits the parent's local day into three", () => {
    expect(dayPartFor(5)).toBe("morning");
    expect(dayPartFor(11)).toBe("morning");
    expect(dayPartFor(12)).toBe("afternoon");
    expect(dayPartFor(16)).toBe("afternoon");
    expect(dayPartFor(17)).toBe("evening");
    expect(dayPartFor(23)).toBe("evening");
  });
});

describe("headlines", () => {
  it("covers the four state/day-part combinations", () => {
    expect(headlineFor("Amma", true, "morning")).toBe(
      "Amma's morning started the usual way",
    );
    expect(headlineFor("Amma", true, "afternoon")).toBe(GLANCE_SEEN_AFTERNOON);
    expect(headlineFor("Amma", true, "evening")).toBe(GLANCE_SEEN_EVENING);
    expect(headlineFor("Amma", false, "morning")).toBe(GLANCE_QUIET_MORNING);
    expect(headlineFor("Amma", false, "afternoon")).toBe(GLANCE_QUIET_TODAY);
    expect(headlineFor("Amma", false, "evening")).toBe(GLANCE_QUIET_TODAY);
  });

  it("keeps `Quiet so far` as the floor in every unseen case", () => {
    for (const part of ["morning", "afternoon", "evening"] as const) {
      expect(headlineFor("Amma", false, part).startsWith("Quiet so far")).toBe(true);
    }
  });
});

describe("computeGlance", () => {
  it("warms the headline once routine is seen, per day-part", () => {
    const morning = computeGlance(parent, IST, signals, [ROUTINE_MORNING], AT("09:00"), IST);
    expect(morning.seenToday).toBe(true);
    expect(morning.headline).toBe("Amma's morning started the usual way");

    const afternoon = computeGlance(parent, IST, signals, [ROUTINE_MORNING], AT("14:00"), IST);
    expect(afternoon.headline).toBe(GLANCE_SEEN_AFTERNOON);

    const evening = computeGlance(parent, IST, signals, [ROUTINE_MORNING], AT("19:00"), IST);
    expect(evening.headline).toBe(GLANCE_SEEN_EVENING);
  });

  it("stays quiet, and says which kind of quiet", () => {
    expect(computeGlance(parent, IST, signals, [], AT("09:00"), IST).headline).toBe(
      GLANCE_QUIET_MORNING,
    );
    expect(computeGlance(parent, IST, signals, [], AT("14:00"), IST).headline).toBe(
      GLANCE_QUIET_TODAY,
    );
  });

  it("renders a dual-timezone subline for a Chicago viewer of an IST parent", () => {
    const state = computeGlance(
      parent, IST, signals, [ROUTINE_AFTERNOON], AT("19:00"), CHICAGO,
    );
    // 09:30Z is 3:00 pm in Chennai and 4:30 am in Chicago.
    expect(state.subline).toBe("Last routine seen 3:00 pm Amma's time · 4:30 am yours");
  });

  it("collapses the subline to one clock when both zones agree", () => {
    const state = computeGlance(parent, IST, signals, [ROUTINE_AFTERNOON], AT("19:00"), IST);
    expect(state.subline).toBe("Last routine seen 3:00 pm Amma's time");
    expect(state.subline).not.toContain("yours");
  });

  it("has no subline before anything has ever been seen", () => {
    expect(computeGlance(parent, IST, signals, [], AT("09:00"), IST).subline).toBeNull();
  });

  it("never lets a timer ping warm the headline", () => {
    const timer: Ping = {
      parent_id: "p1",
      signal: "device_alive",
      ts_utc: "2026-08-03T01:30:00Z",
    };
    const state = computeGlance(parent, IST, signals, [timer], AT("09:00"), IST);
    expect(state.seenToday).toBe(false);
    expect(state.headline).toBe(GLANCE_QUIET_MORNING);
  });

  it("uses the parent's own timezone when they have one", () => {
    const travelling: Parent = { ...parent, tz: CHICAGO };
    // Noon in Chennai is 01:30 the same night in Chicago, so a ping that was
    // "this morning" back home belongs to yesterday for a parent in Texas.
    const state = computeGlance(travelling, IST, signals, [ROUTINE_MORNING], AT("12:00"), IST);
    expect(state.timeZone).toBe(CHICAGO);
    expect(state.seenToday).toBe(false);
    // 01:30 local — the small hours read as morning, which keeps the copy at
    // the gentlest thing true at that time rather than inventing a fourth part.
    expect(state.dayPart).toBe("morning");
    expect(state.headline).toBe(GLANCE_QUIET_MORNING);
  });
});

describe("the day arc", () => {
  it("lights a segment once routine happened in it", () => {
    expect(buildArc([8], 14).map((s) => s.state)).toEqual(["lit", "ahead", "ahead"]);
    expect(buildArc([8, 15], 19).map((s) => s.state)).toEqual(["lit", "lit", "ahead"]);
  });

  it("dims a finished segment that stayed quiet, and leaves the future neutral", () => {
    // Mid-afternoon: the morning is over and empty, the afternoon still open.
    expect(buildArc([], 14).map((s) => s.state)).toEqual(["quiet", "ahead", "ahead"]);
  });

  it("renders no verdict on unfinished time, in any segment", () => {
    // Standing principle, alongside the floor: the stretch you are standing in
    // has not failed, it is still happening. 11am with nothing yet is a parent
    // who slept in, and the arc does not get to call that a bad morning.
    for (const [hour, segment] of [
      [11, 0],
      [14, 1],
      [19, 2],
    ] as const) {
      expect(buildArc([], hour)[segment].state, `hour ${hour} judged too early`).toBe(
        "ahead",
      );
    }
    // And it does dim, once the stretch is genuinely over.
    expect(buildArc([], 14)[0].state).toBe("quiet");
  });

  it("is binary — a busy segment looks exactly like a barely-present one", () => {
    const one = buildArc([8], 20);
    const many = buildArc([6, 7, 8, 9, 10, 11], 20);
    expect(many.map((s) => s.state)).toEqual(one.map((s) => s.state));
  });

  it("uses at most three states", () => {
    const states = new Set(
      [buildArc([], 6), buildArc([8, 15, 19], 22), buildArc([], 22)].flatMap((arc) =>
        arc.map((s) => s.state),
      ),
    );
    expect(states.size).toBeLessThanOrEqual(3);
  });

  it("counts only today's routine", () => {
    const state = computeGlance(
      parent,
      IST,
      signals,
      [{ parent_id: "p1", signal: "whatsapp", ts_utc: "2026-08-02T09:30:00Z" }],
      AT("19:00"),
      IST,
    );
    expect(state.arc.every((s) => s.state !== "lit")).toBe(true);
  });
});

describe("the liveness beacon", () => {
  const alarm = new Set(["whatsapp"]);
  const mechanism = new Set(["device_alive"]);
  const now = AT("12:00");

  it("breathes on a recent mechanism signal", () => {
    const fresh: Ping[] = [
      { parent_id: "p1", signal: "device_alive", ts_utc: "2026-08-03T01:00:00Z" },
    ];
    expect(computeBeacon(fresh, alarm, mechanism, now)).toBe("breathing");
  });

  it("goes still when the last signal is older than the timer cadence", () => {
    const stale: Ping[] = [
      {
        parent_id: "p1",
        signal: "device_alive",
        ts_utc: new Date(now.getTime() - (BEACON_FRESH_HOURS + 2) * 3_600_000).toISOString(),
      },
    ];
    expect(computeBeacon(stale, alarm, mechanism, now)).toBe("still");
  });

  it("is absent when the parent has no mechanism signals configured", () => {
    expect(computeBeacon([], alarm, new Set(), now)).toBeNull();
    const state = computeGlance(parent, IST, alarmOnly, [ROUTINE_MORNING], AT("12:00"), IST);
    expect(state.beacon).toBeNull();
  });

  it("is still, not absent, when configured but never heard from", () => {
    expect(computeBeacon([], alarm, mechanism, now)).toBe("still");
  });

  it("accepts an alarm-grade ping as proof the handset is alive", () => {
    expect(computeBeacon([ROUTINE_MORNING], alarm, mechanism, now)).toBe("breathing");
  });

  it("sits exactly on the boundary without flapping", () => {
    const exactly: Ping[] = [
      {
        parent_id: "p1",
        signal: "device_alive",
        ts_utc: new Date(now.getTime() - BEACON_FRESH_HOURS * 3_600_000).toISOString(),
      },
    ];
    expect(computeBeacon(exactly, alarm, mechanism, now)).toBe("breathing");
  });
});
