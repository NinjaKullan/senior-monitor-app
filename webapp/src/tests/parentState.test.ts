/**
 * @vitest-environment node
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146):
 * pure logic, no DOM — node says so out loud.
 */
/**
 * The v5 state model (spec 008 §4) — computeParentToday as pure logic.
 *
 * The mapping under test: ordinary is an alarm-grade ping on the parent's
 * local today; quiet is none yet while the plumbing still reports; and
 * unreachable is *every* tripwire that ever reported gone stale — a sentence
 * about the phone, never the person. The edges that matter most are the ones
 * a lazy mapping would get wrong: a never-configured signal is a setup step
 * and must not read as silence, and one connected tripwire vetoes
 * unreachable however stale the others are.
 */
import { describe, expect, it } from "vitest";
import { computeParentToday, tzNoteFor } from "@/lib/parentState";
import type { Parent, ParentSignal, Ping, SetupLink } from "@/lib/types";

const IST = "Asia/Kolkata";
const CHICAGO = "America/Chicago";
/** 12:00 IST, Monday 3 August. */
const NOON = new Date("2026-08-03T06:30:00Z");
/** 20:00 IST the same day — every day part begun, evening unfinished. */
const EVENING = new Date("2026-08-03T14:30:00Z");

const amma: Parent = {
  id: "p1",
  family_id: "f1",
  display_name: "Amma",
  tz: null,
  phone_e164: "+919812345678",
};

const signals: ParentSignal[] = [
  { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: "p1", signal: "device_alive", alarm_grade: false, active: true },
];

/** Newest per (parent, signal) — the shape the snapshot's latest set carries. */
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
  {
    now = NOON,
    parent = amma,
    links = [] as SetupLink[],
    viewerTz = CHICAGO,
  } = {},
) => computeParentToday(parent, IST, signals, pings, latestOf(pings), links, now, viewerTz);

/** This morning, 8:12 am IST. */
const MORNING_PING = ping("whatsapp", "2026-08-03T02:42:00Z");
/** Yesterday, 11:00 am IST — inside the whatsapp cadence, so still connected. */
const YESTERDAY_PING = ping("whatsapp", "2026-08-02T05:30:00Z");
/** Ten days stale against a seven-day cadence. */
const OLD_WHATSAPP = ping("whatsapp", "2026-07-24T05:30:00Z");
/** Three days stale against device_alive's 26-hour cadence. */
const OLD_DEVICE = ping("device_alive", "2026-07-31T06:30:00Z");

describe("the three states", () => {
  it("an alarm-grade ping today is an ordinary day", () => {
    const state = stateOf([MORNING_PING]);
    expect(state.kind).toBe("ordinary");
    expect(state.sentence).toBe("Today looks like an ordinary day.");
    expect(state.aside).toBeNull();
  });

  it("nothing yet today, tripwires still reporting: quiet", () => {
    const state = stateOf([YESTERDAY_PING]);
    expect(state.kind).toBe("quiet");
    expect(state.sentence).toBe("Quiet so far today.");
  });

  it("every tripwire that ever reported gone stale: unreachable, about the phone", () => {
    const state = stateOf([OLD_WHATSAPP, OLD_DEVICE]);
    expect(state.kind).toBe("unreachable");
    expect(state.sentence).toBe("Kettle can't hear from Amma's phone right now.");
    expect(state.aside).toBe("A call still works fine — this is only about the phone.");
  });

  it("a phone the server has never heard from is quiet, not unreachable", () => {
    // Never-configured is a setup step (spec 005d's ruling, carried forward):
    // a family's first minutes in the app must not open with the darkest state.
    const state = stateOf([]);
    expect(state.kind).toBe("quiet");
    expect(state.meta).toBe("Nothing has reached Kettle yet.");
    expect(state.needsFix).toBe(false);
  });

  it("one connected tripwire vetoes unreachable, however stale the rest", () => {
    const state = stateOf([OLD_WHATSAPP, ping("device_alive", "2026-08-03T01:00:00Z")]);
    expect(state.kind).toBe("quiet");
    // The stale one still asks for its two-minute fix.
    expect(state.needsFix).toBe(true);
  });
});

describe("the last-heard meta", () => {
  it("today, with a clock time on the parent's clock", () => {
    expect(stateOf([MORNING_PING]).meta).toBe("Heard from at 8:12 am Amma's time.");
  });

  it("yesterday, still at clock grain", () => {
    expect(stateOf([YESTERDAY_PING]).meta).toBe(
      "Last heard from yesterday at 11:00 am Amma's time.",
    );
  });

  it("beyond yesterday, day words only — no clock time to argue over", () => {
    // A connected device_alive keeps this quiet rather than unreachable; the
    // meta still reaches back to the last *alarm-grade* word.
    const state = stateOf([OLD_WHATSAPP, ping("device_alive", "2026-08-03T01:00:00Z")]);
    expect(state.meta).toBe("Last heard from 10 days ago.");
  });

  it("unreachable dates the silence from the newest ping of any grade", () => {
    expect(stateOf([OLD_WHATSAPP, OLD_DEVICE]).meta).toBe(
      "Nothing has reached Kettle since 3 days ago.",
    );
  });
});

describe("the day in words", () => {
  it("names the heard stretch, hedges the current one, dims the future", () => {
    const rows = stateOf([MORNING_PING]).dayRows;
    expect(rows).toEqual([
      { part: "Morning", text: "An ordinary morning — heard from at 8:12 am.", dim: false },
      { part: "Afternoon", text: "Quiet so far.", dim: false },
      { part: "Evening", text: "Still to come.", dim: true },
    ]);
  });

  it("passes verdicts only on finished stretches", () => {
    // 8 pm, nothing all day: morning and afternoon are over and simply quiet;
    // the evening is still being stood in and only gets "so far".
    const rows = stateOf([YESTERDAY_PING], { now: EVENING }).dayRows;
    expect(rows.map((r) => r.text)).toEqual(["Quiet.", "Quiet.", "Quiet so far."]);
  });

  it("keeps the morning's warmer sentence for the morning alone", () => {
    // 1:00 pm IST ping, read in the evening: the afternoon row carries the
    // plain form, not "An ordinary morning".
    const rows = stateOf([ping("whatsapp", "2026-08-03T07:30:00Z")], { now: EVENING }).dayRows;
    expect(rows[1].text).toBe("Heard from at 1:00 pm.");
  });

  it("says only that nothing reached Kettle when the phone is unreachable", () => {
    const rows = stateOf([OLD_WHATSAPP, OLD_DEVICE]).dayRows;
    expect(rows[0]).toEqual({ part: "Morning", text: "Nothing has reached Kettle.", dim: true });
    expect(rows[2]).toEqual({ part: "Evening", text: "Still to come.", dim: true });
  });
});

describe("recent days", () => {
  it("renders five days back, each in one of three honest lines", () => {
    const recent = stateOf([
      MORNING_PING,
      YESTERDAY_PING, // alarm-grade: an ordinary day
      ping("device_alive", "2026-08-01T06:30:00Z"), // pings, no routine: quiet
      // 31 July and 30 July: nothing at all
    ]).recentDays;
    expect(recent).toEqual([
      { day: "Yesterday", line: "An ordinary day." },
      { day: "Saturday", line: "A quiet day." },
      { day: "Friday", line: "Nothing reached Kettle." },
      { day: "Thursday", line: "Nothing reached Kettle." },
      { day: "Wednesday", line: "Nothing reached Kettle." },
    ]);
  });
});

describe("the clock difference, in words", () => {
  it("says nothing numeric in either direction", () => {
    expect(tzNoteFor(IST, IST, NOON)).toBe("The same time as yours.");
    expect(tzNoteFor(IST, CHICAGO, NOON)).toBe("Ten and a half hours ahead of you.");
    expect(tzNoteFor(CHICAGO, IST, NOON)).toBe("Ten and a half hours behind you.");
  });

  it("falls back to a plain sentence rather than a wrong word", () => {
    // Kathmandu is +5:45 — 10¾ hours from Chicago, a shape the word list
    // cannot carry. The fallback is vague on purpose; vague beats wrong.
    expect(tzNoteFor("Asia/Kathmandu", CHICAGO, NOON)).toBe("A different clock from yours.");
  });

  it("drops the full stop for the Family list's sub-line", () => {
    expect(stateOf([MORNING_PING]).famSub).toBe("Ten and a half hours ahead of you");
  });
});

describe("about and the call button", () => {
  const link = (created_utc: string): SetupLink => ({
    parent_id: "p1",
    slug: "slug000000000000000000A1",
    created_utc,
    expires_utc: "2026-08-01T00:00:00Z",
    revoked_utc: null,
  });

  it("dates the setup from the earliest link, month only", () => {
    const state = stateOf([MORNING_PING], {
      links: [link("2026-07-02T00:00:00Z"), link("2026-05-10T00:00:00Z")],
    });
    expect(state.setupLine).toBe("The phone was set up in May.");
  });

  it("says nothing about setup when no link ever existed", () => {
    expect(stateOf([MORNING_PING]).setupLine).toBeNull();
  });

  it("builds the tel: href only when a number exists (DECISIONS 167)", () => {
    expect(stateOf([MORNING_PING]).tel).toBe("tel:+919812345678");
    expect(stateOf([MORNING_PING]).callLabel).toBe("Call Amma");
    const unlisted = stateOf([MORNING_PING], { parent: { ...amma, phone_e164: null } });
    expect(unlisted.tel).toBeNull();
  });
});
