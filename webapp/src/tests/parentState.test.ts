/**
 * @vitest-environment node
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146):
 * pure logic, no DOM — node says so out loud.
 */
/**
 * The spec 009 state model — computeParentToday and computeRollup as pure
 * logic. The edges a lazy mapping would get wrong stay pinned from spec 008
 * (never-configured is quiet, one connected tripwire vetoes unreachable),
 * and the new surfaces get theirs: relative-time buckets including the
 * 14-day boundary, the dual-clock line, rollup precedence, the arc's
 * segments and fraction, seven dots with today on the right, and the call
 * href's tel-then-wa.me-then-nothing ladder.
 */
import { describe, expect, it } from "vitest";
import {
  computeParentToday,
  computeRollup,
  joinNames,
  tzNoteFor,
} from "@/lib/parentState";
import { renderHeard } from "@/lib/copy";
import type { Parent, ParentSignal, Ping } from "@/lib/types";

const IST = "Asia/Kolkata";
const CHICAGO = "America/Chicago";
/** 12:00 IST, Monday 3 August. */
const NOON = new Date("2026-08-03T06:30:00Z");
/** 20:00 IST the same day — evening begun, not over. */
const EVENING = new Date("2026-08-03T14:30:00Z");

const amma: Parent = {
  id: "p1",
  family_id: "f1",
  display_name: "Amma",
  tz: null,
  phone_e164: "+919812345678",
  whatsapp_e164: null,
  relationship: "Mom",
  city_label: "Chennai",
  tz_changed_utc: null,
};

const signals: ParentSignal[] = [
  { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: "p1", signal: "device_alive", alarm_grade: false, active: true },
];

function latestOf(pings: Ping[]): Ping[] {
  const newest = new Map<string, Ping>();
  for (const ping of pings) {
    const key = `${ping.parent_id} ${ping.signal}`;
    const held = newest.get(key);
    if (!held || ping.ts_utc > held.ts_utc) newest.set(key, ping);
  }
  return [...newest.values()];
}

const ping = (signal: string, ts_utc: string): Ping => ({ parent_id: "p1", signal, ts_utc });

const stateOf = (
  pings: Ping[],
  { now = NOON, parent = amma, viewerTz = CHICAGO } = {},
) => computeParentToday(parent, IST, signals, pings, latestOf(pings), now, viewerTz);

/** This morning, 8:12 am IST. */
const MORNING_PING = ping("whatsapp", "2026-08-03T02:42:00Z");
/** Yesterday, 11:00 am IST — inside the whatsapp cadence, so still connected. */
const YESTERDAY_PING = ping("whatsapp", "2026-08-02T05:30:00Z");
/** Ten days stale against a seven-day cadence. */
const OLD_WHATSAPP = ping("whatsapp", "2026-07-24T05:30:00Z");
/** Three days stale against device_alive's 26-hour cadence. */
const OLD_DEVICE = ping("device_alive", "2026-07-31T06:30:00Z");

describe("the three states, and the words they wear now", () => {
  it("an alarm-grade ping today is a normal day", () => {
    const state = stateOf([MORNING_PING]);
    expect(state.kind).toBe("ordinary");
    expect(state.sentence).toBe("Today looks like a normal day.");
    expect(state.aside).toBeNull();
  });

  it("nothing yet today, tripwires still reporting: quiet", () => {
    expect(stateOf([YESTERDAY_PING]).sentence).toBe("Quiet so far today.");
  });

  it("every tripwire gone stale: unreachable, named by the display name", () => {
    const state = stateOf([OLD_WHATSAPP, OLD_DEVICE]);
    expect(state.kind).toBe("unreachable");
    expect(state.sentence).toBe("Kettle can't hear from Amma's phone right now.");
  });

  it("a phone the server has never heard from is quiet, not unreachable", () => {
    const state = stateOf([]);
    expect(state.kind).toBe("quiet");
    expect(state.heard).toBe("Nothing has reached Kettle yet.");
    expect(state.needsFix).toBe(false);
  });

  it("one connected tripwire vetoes unreachable, however stale the rest", () => {
    const state = stateOf([OLD_WHATSAPP, ping("device_alive", "2026-08-03T01:00:00Z")]);
    expect(state.kind).toBe("quiet");
    expect(state.needsFix).toBe(true);
  });
});

describe("the relative-time buckets (spec 009 §2)", () => {
  const MIN = 60_000;
  it("moments, minutes, hours, days, then the DECISIONS 166 form", () => {
    expect(renderHeard(0)).toBe("Heard from moments ago");
    expect(renderHeard(1 * MIN + 59_000)).toBe("Heard from moments ago");
    expect(renderHeard(2 * MIN)).toBe("Heard from 2 minutes ago");
    expect(renderHeard(59 * MIN)).toBe("Heard from 59 minutes ago");
    expect(renderHeard(60 * MIN)).toBe("Heard from 1 hour ago");
    expect(renderHeard(2 * 60 * MIN)).toBe("Heard from 2 hours ago");
    expect(renderHeard(23 * 60 * MIN)).toBe("Heard from 23 hours ago");
    expect(renderHeard(24 * 60 * MIN)).toBe("Heard from 1 day ago");
    expect(renderHeard(6 * 24 * 60 * MIN)).toBe("Heard from 6 days ago");
    // The 14-day boundary: the window's last day keeps the relative form,
    // one past it moves to the standing beyond-window wording.
    expect(renderHeard(14 * 24 * 60 * MIN)).toBe("Heard from 14 days ago");
    expect(renderHeard(15 * 24 * 60 * MIN)).toBe("Last heard from 15 days ago.");
  });

  it("dates the unreachable silence as in-N-days, singular included", () => {
    expect(stateOf([OLD_WHATSAPP, OLD_DEVICE]).heard).toBe(
      "Nothing has reached Kettle in 3 days.",
    );
    const oneDay = [
      ping("whatsapp", "2026-07-24T05:30:00Z"),
      ping("device_alive", "2026-08-02T04:00:00Z"),
    ];
    expect(stateOf(oneDay).heard).toBe("Nothing has reached Kettle in 1 day.");
  });
});

describe("clocks and cities", () => {
  it("writes the dual line from the heard instant on both clocks", () => {
    // 02:42Z is 8:12 am in Chennai and 9:42 pm the previous evening in
    // Chicago (CDT, UTC-5).
    expect(stateOf([MORNING_PING]).dualLine).toBe("8:12 am in Chennai · 9:42 pm your time");
  });

  it("falls back to the name's clock when no city label exists", () => {
    const unlabeled = { ...amma, city_label: null };
    const state = stateOf([MORNING_PING], { parent: unlabeled });
    expect(state.dualLine).toBe("8:12 am Amma's time · 9:42 pm your time");
    expect(state.cityNow).toBe("12:00 pm Amma's time");
    expect(state.heroKicker).toBe("Amma");
  });

  it("says where and what time it is there now on the card", () => {
    const state = stateOf([MORNING_PING]);
    expect(state.cityNow).toBe("Chennai · 12:00 pm there now");
    expect(state.heroKicker).toBe("Amma · Chennai");
  });

  it("joins the hero sub with middots and the offset in lowercase words", () => {
    expect(stateOf([MORNING_PING]).heroSub).toBe(
      "8:12 am in Chennai · 9:42 pm your time · ten and a half hours ahead of you",
    );
  });

  it("keeps the offset-in-words fallback vague rather than wrong", () => {
    expect(tzNoteFor(IST, IST, NOON)).toBe("The same time as yours.");
    expect(tzNoteFor("Asia/Kathmandu", CHICAGO, NOON)).toBe("A different clock from yours.");
  });
});

describe("the day as a shape (spec 009 §3)", () => {
  it("reveals the fraction of the parent's local day elapsed", () => {
    // 12:00 noon local is exactly half the day.
    expect(stateOf([MORNING_PING]).arcFraction).toBeCloseTo(0.5, 5);
    expect(stateOf([MORNING_PING], { now: EVENING }).arcFraction).toBeCloseTo(20 / 24, 5);
  });

  it("captions segments with the LAST heard time, hedges the current, dims the future", () => {
    const twoMorning = [MORNING_PING, ping("whatsapp", "2026-08-03T01:40:00Z")];
    const cells = stateOf(twoMorning).arcCells;
    expect(cells).toEqual([
      { part: "Morning", text: "Heard from 8:12 am", dim: false },
      { part: "Afternoon", text: "Quiet so far", dim: false },
      { part: "Evening", text: "Still ahead", dim: true },
    ]);
  });

  it("calls only a finished stretch simply quiet", () => {
    const cells = stateOf([YESTERDAY_PING], { now: EVENING }).arcCells;
    expect(cells.map((c) => c.text)).toEqual(["Quiet", "Quiet", "Quiet so far"]);
  });

  it("splits afternoon from evening at six, not five", () => {
    // 5:30 pm IST ping lands in the AFTERNOON cell (spec 009 moved the
    // boundary to 6 pm from spec 005c's five).
    const cells = stateOf([ping("whatsapp", "2026-08-03T12:00:00Z")], { now: EVENING }).arcCells;
    expect(cells[1].text).toBe("Heard from 5:30 pm");
    expect(cells[2].text).toBe("Quiet so far");
  });
});

describe("seven dots, today on the right", () => {
  it("classifies each of the seven days and never counts", () => {
    const dots = stateOf([
      MORNING_PING, // today: normal
      YESTERDAY_PING, // yesterday: normal
      ping("device_alive", "2026-08-01T06:30:00Z"), // Saturday: a quiet start
    ]).recentDots;
    expect(dots).toHaveLength(7);
    expect(dots.map((d) => d.abbr)).toEqual(["Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "Mon"]);
    expect(dots.map((d) => d.kind)).toEqual([
      "none", "none", "none", "none", "quiet", "normal", "normal",
    ]);
  });
});

describe("the changeover day's dot (spec 010 §3)", () => {
  /**
   * A parent moved to Chicago on 2 Aug, seen at 01:30 Chicago on 3 Aug.
   * "Quiet" on the changeover day would be an artifact of the moved clock,
   * so that day has exactly two readings: normal if any routine ping landed
   * in ANY zone's version of the date, couldn't-hear if none did.
   */
  const moved: Parent = {
    ...amma,
    tz: CHICAGO,
    tz_changed_utc: "2026-08-02T20:00:00Z", // 15:00 Chicago, 2 Aug
  };
  const dotsOf = (pings: Ping[]) =>
    computeParentToday(moved, IST, signals, pings, latestOf(pings), NOON, CHICAGO)
      .recentDots;
  /** Yesterday in Chicago at NOON's instant — the changeover day's dot. */
  const CHANGE_DOT = 5;

  it("is never merely quiet: a non-alarm ping cannot soften the day", () => {
    // On any other day this device_alive ping would read "a quiet start".
    const dots = dotsOf([ping("device_alive", "2026-08-02T18:00:00Z")]);
    expect(dots[CHANGE_DOT].kind).toBe("none");
  });

  it("reads normal from a routine ping in ANY zone's version of the date", () => {
    // 01:00 Chicago on 3 Aug — outside the Chicago-local 2 Aug, inside the
    // widest UTC span the calendar date can occupy. The widened window can
    // only upgrade the day, the ruled direction.
    const dots = dotsOf([ping("whatsapp", "2026-08-03T06:00:00Z")]);
    expect(dots[CHANGE_DOT].kind).toBe("normal");
  });

  it("stays couldn't-hear when no routine ping landed anywhere", () => {
    expect(dotsOf([])[CHANGE_DOT].kind).toBe("none");
  });

  it("leaves every other day's three-way reading alone", () => {
    // The same device_alive ping, one day earlier: not the changeover day,
    // so the ordinary "a quiet start" reading still applies there.
    const dots = dotsOf([ping("device_alive", "2026-08-01T18:00:00Z")]);
    expect(dots[CHANGE_DOT - 1].kind).toBe("quiet");
  });
});

describe("what this means, per state", () => {
  it("normal", () => {
    const state = stateOf([MORNING_PING]);
    expect(state.meansHead).toBe("No action needed.");
    expect(state.meansBody).toBe("Amma's day looks like most days. Kettle will write if that changes.");
  });
  it("quiet", () => {
    const state = stateOf([YESTERDAY_PING]);
    expect(state.meansHead).toBe("Nothing to do yet.");
    expect(state.meansBody).toBe("Kettle will check in with Amma first if the quiet continues.");
  });
  it("unreachable reuses the standing guidance", () => {
    const state = stateOf([OLD_WHATSAPP, OLD_DEVICE]);
    expect(state.meansHead).toBe("Worth a look.");
    expect(state.meansBody).toBe("A call still works fine — this is only about the phone.");
  });
});

describe("the call href ladder", () => {
  it("tel: first, wa.me when only WhatsApp exists, nothing when neither", () => {
    expect(stateOf([MORNING_PING]).callHref).toBe("tel:+919812345678");
    expect(
      stateOf([MORNING_PING], {
        parent: { ...amma, phone_e164: null, whatsapp_e164: "+91 98765 00000" },
      }).callHref,
    ).toBe("https://wa.me/919876500000");
    expect(
      stateOf([MORNING_PING], { parent: { ...amma, phone_e164: null, whatsapp_e164: null } })
        .callHref,
    ).toBeNull();
    expect(stateOf([MORNING_PING]).callLabel).toBe("Call Amma ↗");
    expect(stateOf([MORNING_PING]).viewLabel).toBe("View Amma's day →");
  });
});

describe("the rollup (spec 009 §2)", () => {
  const dad: Parent = { ...amma, id: "p2", display_name: "Appa", relationship: "Dad" };
  const dadSignals: ParentSignal[] = [
    { parent_id: "p2", signal: "whatsapp", alarm_grade: true, active: true },
  ];
  const both = [...signals, ...dadSignals];
  const dadPing = (ts: string): Ping => ({ parent_id: "p2", signal: "whatsapp", ts_utc: ts });

  const pairAt = (pings: Ping[], now = NOON) =>
    [amma, dad].map((p) =>
      computeParentToday(p, IST, both, pings, latestOf(pings), now, CHICAGO),
    );

  it("says everything looks normal only when everyone does", () => {
    const states = pairAt([MORNING_PING, dadPing("2026-08-03T03:00:00Z")]);
    expect(computeRollup(states, IST, NOON).line).toBe("Everything looks normal today.");
  });

  it("names the quiet parent, and both when both are quiet", () => {
    const oneQuiet = pairAt([MORNING_PING, dadPing("2026-08-02T05:30:00Z")]);
    expect(computeRollup(oneQuiet, IST, NOON).line).toBe("Quiet so far for Appa.");
    const bothQuiet = pairAt([YESTERDAY_PING, dadPing("2026-08-02T05:30:00Z")]);
    expect(computeRollup(bothQuiet, IST, NOON).line).toBe("Quiet so far for Amma and Appa.");
  });

  it("lets unreachable outrank quiet", () => {
    const states = pairAt([OLD_WHATSAPP, OLD_DEVICE, dadPing("2026-08-02T05:30:00Z")]);
    expect(computeRollup(states, IST, NOON).line).toBe(
      "Kettle can't hear from Amma's phone right now.",
    );
  });

  it("flips the next-note line on the family-local evening digest slot", () => {
    const states = pairAt([MORNING_PING, dadPing("2026-08-03T03:00:00Z")]);
    // 12:00 IST: the evening note is still ahead.
    expect(computeRollup(states, IST, NOON).sub).toBe("Next note this evening.");
    // 21:00 IST: past 20:30, the next note is the morning's.
    expect(computeRollup(states, IST, new Date("2026-08-03T15:30:00Z")).sub).toBe(
      "Next note in the morning.",
    );
  });

  it("joins names in words, never a count", () => {
    expect(joinNames(["Mom"])).toBe("Mom");
    expect(joinNames(["Mom", "Dad"])).toBe("Mom and Dad");
    expect(joinNames(["Mom", "Dad", "Grandma"])).toBe("Mom, Dad and Grandma");
  });
});
