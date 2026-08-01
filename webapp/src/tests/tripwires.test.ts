/**
 * AC1 / AC2 — the tripwire health logic (spec 005d).
 *
 * The rules worth pinning here are the ones that keep a maintenance surface from
 * becoming an activity feed: recency counts *local days*, never elapsed hours,
 * and health counts elapsed hours, never days. They disagree at the edges on
 * purpose, and each of those disagreements has a test below.
 */
import { describe, expect, it } from "vitest";
import {
  CADENCE_HOURS,
  DEFAULT_CADENCE_HOURS,
  computeTripwires,
  displayName,
  recencyFor,
} from "@/lib/tripwires";
import { renderRecency } from "@/lib/copy";
import type { Parent, ParentSignal, Ping } from "@/lib/types";

const IST = "Asia/Kolkata";
const HOUR = 3_600_000;
/** 19:00 IST on 3 Aug. */
const NOW = new Date("2026-08-03T13:30:00Z");

const amma: Parent = { id: "p1", family_id: "f1", display_name: "Amma", tz: null };
const appa: Parent = { id: "p2", family_id: "f1", display_name: "Appa", tz: null };

const signals: ParentSignal[] = [
  { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: "p1", signal: "news", alarm_grade: true, active: true },
  { parent_id: "p1", signal: "device_alive", alarm_grade: false, active: true },
  { parent_id: "p1", signal: "youtube", alarm_grade: true, active: false },
  { parent_id: "p2", signal: "whatsapp", alarm_grade: true, active: true },
];

const ago = (signal: string, hours: number, parent = "p1"): Ping => ({
  parent_id: parent,
  signal,
  ts_utc: new Date(NOW.getTime() - hours * HOUR).toISOString(),
});

const view = (pings: Ping[], parent = amma) =>
  computeTripwires(parent, IST, signals, pings, NOW);
const rowFor = (pings: Ping[], signal: string) =>
  view(pings).rows.find((r) => r.signal === signal)!;

describe("which tripwires appear", () => {
  it("lists this parent's active signals, and no one else's", () => {
    expect(view([]).rows.map((r) => r.signal)).toEqual(["whatsapp", "news", "device_alive"]);
    expect(view([], appa).rows.map((r) => r.signal)).toEqual(["whatsapp"]);
  });

  it("leaves out a signal that has been deactivated", () => {
    expect(view([]).rows.map((r) => r.signal)).not.toContain("youtube");
  });

  it("names them the way the shortcut on the phone is named", () => {
    expect(view([]).rows.map((r) => r.name)).toEqual(["WhatsApp", "News", "Daily Check"]);
    expect(displayName("charge_on")).toBe("Charger On");
  });

  it("title-cases a signal it has no name for, rather than leaking the raw key", () => {
    expect(displayName("front_door")).toBe("Front Door");
  });
});

describe("health against the expected cadence", () => {
  it("calls the daily timer stale once it is past its 26 hours", () => {
    expect(rowFor([ago("device_alive", CADENCE_HOURS.device_alive + 1)], "device_alive").health)
      .toBe("stale");
  });

  it("lets the boundary breathe, so a tripwire cannot flap on the tick", () => {
    expect(rowFor([ago("device_alive", CADENCE_HOURS.device_alive)], "device_alive").health).toBe(
      "connected",
    );
  });

  it("keeps an app signal connected at three days — a quiet app is not a broken one", () => {
    const row = rowFor([ago("news", 72)], "news");
    expect(row.health).toBe("connected");
    expect(renderRecency(row.recency.kind, row.recency.days)).toBe("3 days ago");
  });

  it("calls an app signal stale past its generous window", () => {
    expect(rowFor([ago("news", DEFAULT_CADENCE_HOURS + 1)], "news").health).toBe("stale");
  });

  it("reads never — and unconfigured, not stale — for a signal that has never pinged", () => {
    // A shortcut nobody installed cannot be late for a deadline it never had
    // (PM ruling on item 60).
    const row = rowFor([ago("whatsapp", 1)], "news");
    expect(row.recency.kind).toBe("never");
    expect(row.health).toBe("unconfigured");
    expect(renderRecency(row.recency.kind, row.recency.days)).toBe("never");
  });

  it("ignores another parent's pings for the same signal", () => {
    expect(rowFor([ago("whatsapp", 1, "p2")], "whatsapp").recency.kind).toBe("never");
  });
});

describe("recency is counted in local days, not in elapsed hours", () => {
  const at = (iso: string) => new Date(iso);

  it("says yesterday two hours after midnight, not today", () => {
    // 23:00 IST, seen from 01:00 IST the next morning: two hours, one calendar day.
    expect(recencyFor(at("2026-08-02T17:30:00Z"), at("2026-08-02T19:30:00Z"), IST).kind).toBe(
      "yesterday",
    );
  });

  it("says today twenty hours later when the day has not turned", () => {
    // 00:30 IST to 20:30 IST on the same date.
    expect(recencyFor(at("2026-08-02T19:00:00Z"), at("2026-08-03T15:00:00Z"), IST).kind).toBe(
      "today",
    );
  });

  it("counts the days in the parent's zone, not the viewer's", () => {
    const utcMidnightCrossing = at("2026-08-02T23:00:00Z"); // already 3 Aug in IST
    expect(recencyFor(utcMidnightCrossing, at("2026-08-03T13:30:00Z"), IST).kind).toBe("today");
  });

  it("never reports a negative day count when a clock runs ahead", () => {
    expect(recencyFor(at("2026-08-05T00:00:00Z"), NOW, IST)).toEqual({ kind: "today", days: 0 });
  });
});

describe("the repair nudge", () => {
  it("stays away while everything is connected", () => {
    const healthy = view([ago("whatsapp", 1), ago("news", 2), ago("device_alive", 3)]);
    expect(healthy.rows.every((r) => r.health === "connected")).toBe(true);
    expect(healthy.needsRepair).toBe(false);
  });

  it("appears as soon as one tripwire is stale", () => {
    const one = view([ago("whatsapp", 1), ago("news", 2), ago("device_alive", 40)]);
    expect(one.needsRepair).toBe(true);
  });

  /**
   * The ruling on item 60, as the two cases the PM named. A family's first
   * minutes in the app must not open with "something needs fixing"; a tripwire
   * that used to work and stopped still must.
   */
  it("stays away from a parent whose shortcuts are not installed yet", () => {
    const fresh = view([]);
    expect(fresh.rows.every((r) => r.health === "unconfigured")).toBe(true);
    expect(fresh.rows.some((r) => r.health === "stale")).toBe(false);
    expect(fresh.needsRepair).toBe(false);
  });

  it("appears once a tripwire that really did report goes quiet for eight days", () => {
    const brokeAfterWorking = view([ago("news", 8 * 24)]);
    expect(rowFor([ago("news", 8 * 24)], "news").health).toBe("stale");
    expect(brokeAfterWorking.needsRepair).toBe(true);
  });
});
