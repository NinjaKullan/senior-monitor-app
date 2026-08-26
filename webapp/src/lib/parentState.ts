/**
 * The spec 009 state model: everything Today and the Parent detail render for
 * one parent, as pure functions over the snapshot's two ping sets. The
 * DECISIONS 160/166 read discipline is load-bearing here:
 *
 * - the WINDOWED set (14 days) feeds today's state, the day arc's segments
 *   and the seven recent-day dots — everything that is about recent time;
 * - the LATEST set (unwindowed, per signal) feeds the unreachable distinction
 *   and the last-heard line, the two facts that must reach past the window.
 *
 * Three states, unchanged from spec 008 (only the words moved to "normal"):
 * - ordinary:    an alarm-grade ping arrived today (the parent's local today);
 * - quiet:       none yet, while the phone's tripwires still report;
 * - unreachable: every tripwire that ever reported has gone stale — a
 *                sentence about the phone, never the person (law #6).
 */

import {
  ARC_AHEAD,
  ARC_HEARD,
  ARC_QUIET,
  ARC_QUIET_SO_FAR,
  CALL_LABEL,
  CITY_NOW,
  DAY_PARTS,
  DUAL_CITY,
  DUAL_CLOCK,
  MEANS_NORMAL_BODY,
  MEANS_NORMAL_HEAD,
  MEANS_QUIET_BODY,
  MEANS_QUIET_HEAD,
  MEANS_UNREACHABLE_HEAD,
  META_NOTHING_YET,
  ROLLUP_NORMAL,
  ROLLUP_QUIET,
  ROLLUP_SUB_EVENING,
  ROLLUP_SUB_MORNING,
  STATE_ORDINARY,
  STATE_QUIET,
  STATE_UNREACHABLE,
  TIME_BY_CLOCK,
  TZ_AHEAD,
  TZ_BEHIND,
  TZ_DIFFERENT,
  TZ_SAME,
  UNREACHABLE_ASIDE,
  VIEW_DAY_LABEL,
  renderClock,
  renderHeard,
  renderNothingIn,
} from "./copy";
import { effectiveTz, formatLocalTime, localDate, localDayStart } from "./time";
import { computeTripwires } from "./tripwires";
import type { Parent, ParentSignal, Ping } from "./types";

/** Parent-local segment boundaries (spec 009 §3): morning before noon,
 *  afternoon noon to 6 pm, evening after. */
export const AFTERNOON_START = 12;
export const EVENING_START = 18;

/**
 * The evening digest slot, family-local, mirrored from the outbound engine's
 * v1 constant (product/kettle/outbound.py EVENING_DIGEST = 20:30). The rollup
 * sub-line flips on it: "this evening" before, "in the morning" after.
 * FLAGGED in DECISIONS: a mirrored constant, so an engine retune must touch
 * both sides until a shared source exists.
 */
export const EVENING_DIGEST_MINUTES = 20 * 60 + 30;

export type ParentKind = "ordinary" | "quiet" | "unreachable";

export interface ArcCell {
  part: (typeof DAY_PARTS)[number];
  text: string;
  /** Future stretches render dimmed. */
  dim: boolean;
}

export type DotKind = "normal" | "quiet" | "none";

export interface RecentDot {
  /** Weekday abbreviation under the chip — words, never a count. */
  abbr: string;
  kind: DotKind;
}

export interface ParentToday {
  parentId: string;
  /** The parent's display name (DECISIONS 183: names disambiguate where a
   *  shared relationship label cannot). The card renders it uppercase. */
  label: string;
  kind: ParentKind;
  /** The card and hero state line. */
  sentence: string;
  /** "Heard from 12 minutes ago" / the unreachable duration / nothing yet. */
  heard: string;
  /** "7:52 pm in Chennai · 10:22 am your time" — the last-heard instant on
   *  both clocks; null when nothing has ever been heard. */
  dualLine: string | null;
  /** The card's second name line: "Chennai · 8:04 pm there now", or the
   *  clock fallback when no city label exists. */
  cityNow: string;
  /** "Amma · Chennai" (label alone when no city). */
  heroKicker: string;
  /** The dual line joined with the offset-in-words clause, middots. */
  heroSub: string;
  /** Fraction of the parent's local day elapsed, 0..1 (spec 009 §3). */
  arcFraction: number;
  arcCells: ArcCell[];
  /** Seven days, oldest left, today right. */
  recentDots: RecentDot[];
  meansHead: string;
  meansBody: string;
  /** tel: when a phone exists, wa.me when only WhatsApp does, else null —
   *  never a dead button. The numbers render only inside the href. */
  callHref: string | null;
  callLabel: string;
  viewLabel: string;
  /** The unreachable state's one extra sentence, else null. */
  aside: string | null;
  /** "The same time as yours." — the Family list's sub-line source. */
  tzNote: string;
  famSub: string;
  needsFix: boolean;
  timeZone: string;
}

export function localHourMinute(
  instant: Date,
  timeZone: string,
): { hour: number; minute: number } {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(instant);
  const get = (type: string) => Number(parts.find((p) => p.type === type)?.value ?? "0");
  return { hour: get("hour") % 24, minute: get("minute") };
}

export function localHour(instant: Date, timeZone: string): number {
  return localHourMinute(instant, timeZone).hour;
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

/** The clock difference, in words. A shape words cannot carry cleanly falls
 *  back to a plain sentence rather than a wrong one. */
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

/** The hero sub joins sentences with middots, lowercase, no full stops —
 *  "nine and a half hours ahead of you" (the mockup's register). */
function asClause(sentence: string): string {
  const trimmed = sentence.replace(/\.$/, "");
  return trimmed.charAt(0).toLowerCase() + trimmed.slice(1);
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

function weekdayAbbr(instant: Date, timeZone: string): string {
  return new Intl.DateTimeFormat("en-US", { timeZone, weekday: "short" }).format(instant);
}

/**
 * The name every webapp surface renders (DECISIONS 183, correcting spec 009
 * §2): the DISPLAY name, never the relationship label. Two parents can share
 * a relationship — TestDad and Appa both read "DAD" — and duplicate cards
 * cannot be told apart; display_name is unique to a person. The relationship
 * vocabulary (149) remains the OUTBOUND channel's register by design.
 */
export function labelFor(parent: Parent): string {
  return parent.display_name;
}

export function computeParentToday(
  parent: Parent,
  familyTz: string,
  signals: ParentSignal[],
  windowPings: Ping[],
  latestPings: Ping[],
  now: Date,
  viewerTz: string = Intl.DateTimeFormat().resolvedOptions().timeZone,
): ParentToday {
  const timeZone = effectiveTz(parent.tz, familyTz);
  const label = labelFor(parent);
  const clock = renderClock(label);
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
        : STATE_UNREACHABLE.replace("{name}", label);

  // Last heard, from the unwindowed latest rows so the line stays true past
  // the 14-day window (DECISIONS 166).
  const lastHeard = newestAlarmInstant(latestPings, parent.id, alarm);

  let heard: string;
  if (kind === "unreachable") {
    // Since when the PHONE went silent: the newest ping of any grade.
    const anyTimes = latestPings
      .filter((p) => p.parent_id === parent.id)
      .map((p) => new Date(p.ts_utc).getTime());
    heard =
      anyTimes.length === 0
        ? META_NOTHING_YET
        : renderNothingIn(
            Math.max(1, Math.floor((now.getTime() - Math.max(...anyTimes)) / MS_DAY)),
          );
  } else if (lastHeard) {
    // renderHeard's default window matches data.ts's PINGS_WINDOW_DAYS; the
    // import is avoided so this module stays pure of the supabase client.
    heard = renderHeard(now.getTime() - lastHeard.getTime());
  } else {
    heard = META_NOTHING_YET;
  }

  const city = parent.city_label;
  const dualLine = lastHeard
    ? (city ? DUAL_CITY : DUAL_CLOCK)
        .replace("{ptime}", formatLocalTime(lastHeard.toISOString(), timeZone))
        .replace("{vtime}", formatLocalTime(lastHeard.toISOString(), viewerTz))
        .replace("{city}", city ?? "")
        .replace("{clock}", clock)
    : null;

  const nowThere = formatLocalTime(now.toISOString(), timeZone);
  const cityNow = city
    ? CITY_NOW.replace("{city}", city).replace("{time}", nowThere)
    : TIME_BY_CLOCK.replace("{time}", nowThere).replace("{clock}", clock);

  const heroKicker = city ? `${label} · ${city}` : label;

  const tzNote = tzNoteFor(timeZone, viewerTz, now);
  const heroSub = [dualLine, asClause(tzNote)].filter(Boolean).join(" · ");

  // The day as a shape (spec 009 §3): the fraction of the parent's local day
  // elapsed, midnight to midnight, drives the arc's reveal and its dot.
  const { hour, minute } = localHourMinute(now, timeZone);
  const arcFraction = (hour * 60 + minute) / 1440;

  const bounds: [number, number][] = [
    [0, AFTERNOON_START],
    [AFTERNOON_START, EVENING_START],
    [EVENING_START, 24],
  ];
  const arcCells: ArcCell[] = bounds.map(([start, end], index) => {
    const part = DAY_PARTS[index];
    if (hour < start) return { part, text: ARC_AHEAD, dim: true };
    const inPart = routineToday
      .filter((p) => {
        const h = localHour(new Date(p.ts_utc), timeZone);
        return h >= start && h < end;
      })
      .sort((a, b) => a.ts_utc.localeCompare(b.ts_utc));
    if (inPart.length > 0) {
      // The LAST heard time in the segment (spec 009 §3).
      const time = formatLocalTime(inPart[inPart.length - 1].ts_utc, timeZone);
      return { part, text: ARC_HEARD.replace("{time}", time), dim: false };
    }
    // Only a finished stretch is simply quiet; the one being stood in keeps
    // the hedged form (flagged execution call — see ARC_QUIET_SO_FAR).
    return { part, text: hour < end ? ARC_QUIET_SO_FAR : ARC_QUIET, dim: false };
  });

  // Seven dots, oldest left, today right (spec 009 §3), from the windowed
  // set: alarm-grade ping = a normal day, any ping = a quiet start, none =
  // couldn't hear. No tally, no counts — the chips carry no digits.
  //
  // The changeover day (spec 010 §3) is never "a quiet start": under a moved
  // clock, "quiet" is an artifact of the move, not evidence. It reads normal
  // if any routine ping arrived in either zone's version of that day, and
  // couldn't-hear only if none did. The OLD zone is not readable client-side,
  // so "either zone's version" is implemented as ANY zone's version — the
  // widest UTC span the calendar date can occupy (UTC+14 through UTC-12),
  // which can only ever upgrade the changeover day, the ruled direction.
  const changeDate = parent.tz_changed_utc
    ? localDate(new Date(parent.tz_changed_utc), timeZone)
    : null;
  const recentDots: RecentDot[] = [];
  for (let back = 6; back >= 0; back--) {
    const dayInstant = new Date(now.getTime() - back * MS_DAY);
    const date = localDate(dayInstant, timeZone);
    let dotKind: DotKind;
    if (date === changeDate) {
      const anyZoneStart = Date.parse(`${date}T00:00:00Z`) - 14 * 3_600_000;
      const anyZoneEnd = Date.parse(`${date}T00:00:00Z`) + 36 * 3_600_000;
      const routine = mine.some((p) => {
        const t = new Date(p.ts_utc).getTime();
        return alarm.has(p.signal) && t >= anyZoneStart && t < anyZoneEnd;
      });
      dotKind = routine ? "normal" : "none";
    } else {
      const dayPings = mine.filter(
        (p) => localDate(new Date(p.ts_utc), timeZone) === date,
      );
      dotKind = dayPings.some((p) => alarm.has(p.signal))
        ? "normal"
        : dayPings.length > 0
          ? "quiet"
          : "none";
    }
    recentDots.push({ abbr: weekdayAbbr(dayInstant, timeZone), kind: dotKind });
  }

  const meansHead =
    kind === "ordinary"
      ? MEANS_NORMAL_HEAD
      : kind === "quiet"
        ? MEANS_QUIET_HEAD
        : MEANS_UNREACHABLE_HEAD;
  const meansBody =
    kind === "ordinary"
      ? MEANS_NORMAL_BODY.replace("{name}", label)
      : kind === "quiet"
        ? MEANS_QUIET_BODY.replace("{name}", label)
        : UNREACHABLE_ASIDE;

  const phone = parent.phone_e164 ?? null;
  const whatsapp = parent.whatsapp_e164 ?? null;
  const callHref = phone
    ? `tel:${phone}`
    : whatsapp
      ? `https://wa.me/${whatsapp.replace(/\D/g, "")}`
      : null;

  return {
    parentId: parent.id,
    label,
    kind,
    sentence,
    heard,
    dualLine,
    cityNow,
    heroKicker,
    heroSub,
    arcFraction,
    arcCells,
    recentDots,
    meansHead,
    meansBody,
    callHref,
    callLabel: CALL_LABEL.replace("{name}", label),
    viewLabel: VIEW_DAY_LABEL.replace("{name}", label),
    aside: kind === "unreachable" ? UNREACHABLE_ASIDE : null,
    tzNote,
    famSub: tzNote.replace(/\.$/, ""),
    needsFix: tripwires.needsRepair,
    timeZone,
  };
}

/**
 * The Today rollup (spec 009 §2), precedence unreachable > quiet > normal,
 * and its next-note sub-line flipped on the family-local evening digest slot.
 */
export function computeRollup(
  states: ParentToday[],
  familyTz: string,
  now: Date,
): { line: string; sub: string } {
  const firstUnreachable = states.find((s) => s.kind === "unreachable");
  const quiet = states.filter((s) => s.kind === "quiet");
  const line = firstUnreachable
    ? STATE_UNREACHABLE.replace("{name}", firstUnreachable.label)
    : quiet.length > 0
      ? ROLLUP_QUIET.replace("{names}", joinNames(quiet.map((s) => s.label)))
      : ROLLUP_NORMAL;
  const { hour, minute } = localHourMinute(now, familyTz);
  const sub =
    hour * 60 + minute < EVENING_DIGEST_MINUTES ? ROLLUP_SUB_EVENING : ROLLUP_SUB_MORNING;
  return { line, sub };
}

/** "Mom", "Mom and Dad", "Mom, Dad and Grandma" — words, never a count. */
export function joinNames(names: string[]): string {
  if (names.length <= 1) return names[0] ?? "";
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}
