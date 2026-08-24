/**
 * The v5 state model (spec 008 §4): everything the Today card and the Parent
 * detail render for one parent, as pure functions over the snapshot's two ping
 * sets. The DECISIONS 160/166 read discipline is load-bearing here:
 *
 * - the WINDOWED set (14 days) feeds today's sentence, the day rows and the
 *   recent-days list — everything that is about recent time;
 * - the LATEST set (unwindowed, per signal) feeds the unreachable distinction
 *   and the last-heard line, the two facts that must reach past the window.
 *
 * Three states, mapped onto what the app can honestly know:
 * - ordinary:    an alarm-grade ping arrived today (the parent's local today);
 * - quiet:       none yet, while the phone's tripwires still report — the
 *                existing honest-absence floor, unchanged in darkness;
 * - unreachable: every tripwire that ever reported has gone stale — a sentence
 *                about the phone, never the person (law #6).
 */

import {
  CALL_LABEL,
  DAY_HEARD,
  DAY_MORNING_HEARD,
  DAY_NOTHING,
  DAY_PARTS,
  DAY_QUIET,
  DAY_QUIET_SO_FAR,
  DAY_STILL_TO_COME,
  LOCAL_LINE,
  META_HEARD_DAYS,
  META_HEARD_TODAY,
  META_HEARD_YESTERDAY,
  META_NOTHING_SINCE,
  META_NOTHING_YET,
  RECENT_NOTHING,
  RECENT_ORDINARY,
  RECENT_QUIET,
  SETUP_MONTH,
  STATE_ORDINARY,
  STATE_QUIET,
  STATE_UNREACHABLE,
  TZ_AHEAD,
  TZ_BEHIND,
  TZ_DIFFERENT,
  TZ_SAME,
  UNREACHABLE_ASIDE,
  renderClock,
  renderRecency,
} from "./copy";
import { effectiveTz, formatLocalTime, localDate, localDayStart } from "./time";
import { computeTripwires } from "./tripwires";
import type { Parent, ParentSignal, Ping, SetupLink } from "./types";

/** Parent-local day-part boundaries (unchanged from spec 005c §2). */
export const MORNING_START = 5;
export const AFTERNOON_START = 12;
export const EVENING_START = 17;

export type ParentKind = "ordinary" | "quiet" | "unreachable";

export interface DayRow {
  part: (typeof DAY_PARTS)[number];
  text: string;
  /** Future stretches and unreachable rows render dimmed. */
  dim: boolean;
}

export interface RecentDay {
  day: string;
  line: string;
}

export interface ParentToday {
  parentId: string;
  name: string;
  kind: ParentKind;
  /** The card and hero sentence. */
  sentence: string;
  /** The last-heard line under it. */
  meta: string;
  /** "4:08 pm" in the parent's zone. */
  localTime: string;
  /** "It's 4:08 pm, Amma's time, right now." for the detail hero. */
  localLine: string;
  /** The unreachable state's one extra sentence, else null. */
  aside: string | null;
  dayRows: DayRow[];
  recentDays: RecentDay[];
  /** "The same time as yours." / "Four and a half hours ahead of you." */
  tzNote: string;
  /** The Family list's sub-line: the tzNote without its full stop. */
  famSub: string;
  /** "The phone was set up in May." — null when no setup link exists. */
  setupLine: string | null;
  /** tel: href, only when a phone number exists (spec 008 §5.2) — the number
   *  itself never renders as text (DECISIONS 167: tap-to-act links only). */
  tel: string | null;
  callLabel: string;
  /** The two-minute-fix card's gate: same condition as the repair nudge. */
  needsFix: boolean;
  timeZone: string;
}

export function localHour(instant: Date, timeZone: string): number {
  const hour = new Intl.DateTimeFormat("en-GB", {
    timeZone,
    hour: "2-digit",
    hour12: false,
  }).format(instant);
  return Number(hour) % 24;
}

export function alarmGradeSignals(signals: ParentSignal[], parentId: string): Set<string> {
  return new Set(
    signals
      .filter((s) => s.parent_id === parentId && s.alarm_grade && s.active)
      .map((s) => s.signal),
  );
}

/** Minutes this zone's wall clock reads ahead of UTC at `instant`. */
function offsetMinutes(instant: Date, timeZone: string): number {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(instant);
  const get = (type: string) => Number(parts.find((p) => p.type === type)?.value ?? "0");
  const wall = Date.UTC(get("year"), get("month") - 1, get("day"), get("hour") % 24, get("minute"));
  return Math.round((wall - instant.getTime()) / 60_000);
}

const HOUR_WORDS = [
  "", "One hour", "Two hours", "Three hours", "Four hours", "Five hours",
  "Six hours", "Seven hours", "Eight hours", "Nine hours", "Ten hours",
  "Eleven hours", "Twelve hours",
];
const HALF_WORDS = [
  "Half an hour", "One and a half hours", "Two and a half hours",
  "Three and a half hours", "Four and a half hours", "Five and a half hours",
  "Six and a half hours", "Seven and a half hours", "Eight and a half hours",
  "Nine and a half hours", "Ten and a half hours", "Eleven and a half hours",
  "Twelve and a half hours",
];

/** The clock difference, in words (the v5 register: no digits in the About
 *  block). A shape words cannot carry cleanly falls back to a plain sentence
 *  rather than a wrong one. */
export function tzNoteFor(parentTz: string, viewerTz: string, now: Date): string {
  const diff = offsetMinutes(now, parentTz) - offsetMinutes(now, viewerTz);
  if (diff === 0) return TZ_SAME;
  const abs = Math.abs(diff);
  const whole = Math.floor(abs / 60);
  const words =
    abs % 60 === 0 && whole >= 1 && whole <= 12
      ? HOUR_WORDS[whole]
      : abs % 60 === 30 && whole <= 12
        ? HALF_WORDS[whole]
        : null;
  if (!words) return TZ_DIFFERENT;
  return (diff > 0 ? TZ_AHEAD : TZ_BEHIND).replace("{words}", words);
}

const MS_DAY = 86_400_000;

function newestAlarmInstant(
  latestPings: Ping[],
  parentId: string,
  alarm: Set<string>,
): Date | null {
  const times = latestPings
    .filter((p) => p.parent_id === parentId && alarm.has(p.signal))
    .map((p) => new Date(p.ts_utc).getTime());
  return times.length > 0 ? new Date(Math.max(...times)) : null;
}

function weekdayName(instant: Date, timeZone: string): string {
  return new Intl.DateTimeFormat("en-US", { timeZone, weekday: "long" }).format(instant);
}

export function computeParentToday(
  parent: Parent,
  familyTz: string,
  signals: ParentSignal[],
  windowPings: Ping[],
  latestPings: Ping[],
  setupLinks: SetupLink[],
  now: Date,
  viewerTz: string = Intl.DateTimeFormat().resolvedOptions().timeZone,
): ParentToday {
  const timeZone = effectiveTz(parent.tz, familyTz);
  const name = parent.display_name;
  const clock = renderClock(name);
  const alarm = alarmGradeSignals(signals, parent.id);

  const mine = windowPings.filter((p) => p.parent_id === parent.id);
  const dayStart = localDayStart(now, timeZone);
  const routineToday = mine.filter(
    (p) => alarm.has(p.signal) && new Date(p.ts_utc) >= dayStart,
  );
  const seenToday = routineToday.length > 0;

  // The unreachable distinction rides on the unwindowed tripwire ages
  // (DECISIONS 166): every tripwire that ever reported has gone stale, and at
  // least one exists. A never-configured signal is a setup step, not silence.
  const tripwires = computeTripwires(parent, familyTz, signals, latestPings, now);
  const rows = tripwires.rows;
  const unreachable =
    rows.length > 0 &&
    rows.some((r) => r.health === "stale") &&
    rows.every((r) => r.health !== "connected");

  const kind: ParentKind = unreachable ? "unreachable" : seenToday ? "ordinary" : "quiet";

  const sentence =
    kind === "ordinary"
      ? STATE_ORDINARY
      : kind === "quiet"
        ? STATE_QUIET
        : STATE_UNREACHABLE.replace("{name}", name);

  // Last heard, from the unwindowed latest rows so the sentence stays true
  // past the 14-day window.
  const lastHeard = newestAlarmInstant(latestPings, parent.id, alarm);
  const heardKind = lastHeard
    ? localDate(lastHeard, timeZone) === localDate(now, timeZone)
      ? ("today" as const)
      : localDate(lastHeard, timeZone) ===
          localDate(new Date(now.getTime() - MS_DAY), timeZone)
        ? ("yesterday" as const)
        : ("days" as const)
    : null;
  const heardDays = lastHeard
    ? Math.max(2, Math.round((now.getTime() - lastHeard.getTime()) / MS_DAY))
    : 0;

  let meta: string;
  if (kind === "unreachable") {
    // Since when the PHONE went silent: the newest ping of any grade.
    const anyTimes = latestPings
      .filter((p) => p.parent_id === parent.id)
      .map((p) => new Date(p.ts_utc).getTime());
    if (anyTimes.length === 0) {
      meta = META_NOTHING_YET;
    } else {
      const newest = new Date(Math.max(...anyTimes));
      const isYesterday =
        localDate(newest, timeZone) ===
        localDate(new Date(now.getTime() - MS_DAY), timeZone);
      const when = isYesterday
        ? renderRecency("yesterday")
        : renderRecency("days", Math.max(2, Math.round((now.getTime() - newest.getTime()) / MS_DAY)));
      meta = META_NOTHING_SINCE.replace("{when}", when);
    }
  } else if (lastHeard && heardKind === "today") {
    meta = META_HEARD_TODAY.replace(
      "{time}",
      formatLocalTime(lastHeard.toISOString(), timeZone),
    ).replace("{clock}", clock);
  } else if (lastHeard && heardKind === "yesterday") {
    meta = META_HEARD_YESTERDAY.replace(
      "{time}",
      formatLocalTime(lastHeard.toISOString(), timeZone),
    ).replace("{clock}", clock);
  } else if (lastHeard) {
    meta = META_HEARD_DAYS.replace("{days}", String(heardDays));
  } else {
    meta = META_NOTHING_YET;
  }

  const localTime = formatLocalTime(now.toISOString(), timeZone);
  const localLine = LOCAL_LINE.replace("{time}", localTime).replace("{clock}", clock);

  // The day, in words. No verdicts on unfinished time: the current stretch
  // says "so far", only a finished one is simply quiet.
  const hour = localHour(now, timeZone);
  const bounds: [number, number][] = [
    [MORNING_START, AFTERNOON_START],
    [AFTERNOON_START, EVENING_START],
    [EVENING_START, 24],
  ];
  const dayRows: DayRow[] = bounds.map(([start, end], index) => {
    const part = DAY_PARTS[index];
    if (hour < start) return { part, text: DAY_STILL_TO_COME, dim: true };
    if (kind === "unreachable") return { part, text: DAY_NOTHING, dim: true };
    const inPart = routineToday
      .filter((p) => {
        const h = localHour(new Date(p.ts_utc), timeZone);
        return h >= start && h < end;
      })
      .sort((a, b) => a.ts_utc.localeCompare(b.ts_utc));
    if (inPart.length > 0) {
      const time = formatLocalTime(inPart[0].ts_utc, timeZone);
      const template = part === "Morning" ? DAY_MORNING_HEARD : DAY_HEARD;
      return { part, text: template.replace("{time}", time), dim: false };
    }
    return { part, text: hour < end ? DAY_QUIET_SO_FAR : DAY_QUIET, dim: false };
  });

  // Recent days from the windowed set: yesterday back five days, each in one
  // of three honest lines — routine, pings-but-no-routine, or nothing at all.
  const recentDays: RecentDay[] = [];
  for (let back = 1; back <= 5; back++) {
    const dayInstant = new Date(now.getTime() - back * MS_DAY);
    const date = localDate(dayInstant, timeZone);
    const dayPings = mine.filter((p) => localDate(new Date(p.ts_utc), timeZone) === date);
    const line =
      dayPings.some((p) => alarm.has(p.signal))
        ? RECENT_ORDINARY
        : dayPings.length > 0
          ? RECENT_QUIET
          : RECENT_NOTHING;
    recentDays.push({
      day: back === 1 ? "Yesterday" : weekdayName(dayInstant, timeZone),
      line,
    });
  }

  const tzNote = tzNoteFor(timeZone, viewerTz, now);
  const famSub = tzNote.replace(/\.$/, "");

  const firstLink = setupLinks
    .filter((l) => l.parent_id === parent.id)
    .sort((a, b) => a.created_utc.localeCompare(b.created_utc))[0];
  const setupLine = firstLink
    ? SETUP_MONTH.replace(
        "{month}",
        new Intl.DateTimeFormat("en-US", { timeZone, month: "long" }).format(
          new Date(firstLink.created_utc),
        ),
      )
    : null;

  const phone = parent.phone_e164 ?? null;

  return {
    parentId: parent.id,
    name,
    kind,
    sentence,
    meta,
    localTime,
    localLine,
    aside: kind === "unreachable" ? UNREACHABLE_ASIDE : null,
    dayRows,
    recentDays,
    tzNote,
    famSub,
    setupLine,
    tel: phone ? `tel:${phone}` : null,
    callLabel: CALL_LABEL.replace("{name}", name),
    needsFix: tripwires.needsRepair,
    timeZone,
  };
}
