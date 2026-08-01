/**
 * The Glance screen's logic, as pure functions.
 *
 * Spec 005c's philosophy in one line: **warmth rises, information stays
 * coarse.** Everything below adds warmth — a headline that knows what time of
 * day it is, a shape for the day, a dot that breathes — and not one of them adds
 * a fact the flat version did not already show. No count, no history, no number
 * a family could turn into a behaviour profile.
 *
 * The floor is still `Quiet so far …`. Nothing here is darker, because anything
 * darker belongs to the escalation ladder, which has no surface in this app.
 */

import {
  ARC_SEGMENTS,
  GLANCE_QUIET_MORNING,
  GLANCE_QUIET_TODAY,
  GLANCE_SEEN_AFTERNOON,
  GLANCE_SEEN_EVENING,
  GLANCE_SEEN_MORNING,
  renderSubline,
} from "./copy";
import type { Parent, ParentSignal, Ping } from "./types";
import { effectiveTz, formatLocalTime, localDayStart } from "./time";

/** Parent-local day-part boundaries (§2). */
export const MORNING_START = 5;
export const AFTERNOON_START = 12;
export const EVENING_START = 17;
export const EVENING_END = 21;

/**
 * How stale a mechanism signal may be before the beacon stops breathing. The
 * timer fires daily, so 26 hours covers that cadence with slack for a phone
 * that charged late or a network that took its time.
 */
export const BEACON_FRESH_HOURS = 26;

export type DayPart = "morning" | "afternoon" | "evening";
export type SegmentState = "lit" | "quiet" | "ahead";
export type BeaconState = "breathing" | "still";

export interface ArcSegment {
  name: (typeof ARC_SEGMENTS)[number];
  state: SegmentState;
}

export interface GlanceState {
  parentId: string;
  name: string;
  /** The coarse fact under all the warmth: routine seen today, or not. */
  seenToday: boolean;
  dayPart: DayPart;
  headline: string;
  /** Dual-timezone line, or null when there is nothing yet to report. */
  subline: string | null;
  arc: ArcSegment[];
  /** null when this parent has no mechanism signals configured — never faked. */
  beacon: BeaconState | null;
  timeZone: string;
}

export function alarmGradeSignals(signals: ParentSignal[], parentId: string): Set<string> {
  return new Set(
    signals
      .filter((s) => s.parent_id === parentId && s.alarm_grade && s.active)
      .map((s) => s.signal),
  );
}

/**
 * Signals that say the handset is alive without saying anything about a person
 * — the timer and the charger. Law #6 lives here: these drive the beacon, which
 * is labelled `phone`, and they never touch the headline.
 */
export function mechanismSignals(signals: ParentSignal[], parentId: string): Set<string> {
  return new Set(
    signals
      .filter((s) => s.parent_id === parentId && !s.alarm_grade && s.active)
      .map((s) => s.signal),
  );
}

export function localHour(instant: Date, timeZone: string): number {
  const hour = new Intl.DateTimeFormat("en-GB", {
    timeZone,
    hour: "2-digit",
    hour12: false,
  }).format(instant);
  return Number(hour) % 24;
}

export function dayPartFor(hour: number): DayPart {
  if (hour < AFTERNOON_START) return "morning";
  if (hour < EVENING_START) return "afternoon";
  return "evening";
}

export function headlineFor(name: string, seen: boolean, dayPart: DayPart): string {
  if (!seen) {
    return dayPart === "morning" ? GLANCE_QUIET_MORNING : GLANCE_QUIET_TODAY;
  }
  if (dayPart === "morning") return GLANCE_SEEN_MORNING.replace("{name}", name);
  return dayPart === "afternoon" ? GLANCE_SEEN_AFTERNOON : GLANCE_SEEN_EVENING;
}

const SEGMENT_BOUNDS: [number, number][] = [
  [MORNING_START, AFTERNOON_START],
  [AFTERNOON_START, EVENING_START],
  [EVENING_START, EVENING_END],
];

/**
 * Three binary segments: routine happened in this stretch of the day, or it did
 * not. Deliberately not a bar chart — a segment glowing brighter for more pings
 * would be a count wearing a costume.
 */
export function buildArc(routineHours: number[], currentHour: number): ArcSegment[] {
  return SEGMENT_BOUNDS.map(([start, end], index) => {
    const lit = routineHours.some((h) => h >= start && h < end);
    if (lit) return { name: ARC_SEGMENTS[index], state: "lit" as const };
    // The current segment is still open for business, so it reads the same as
    // one that has not started: neutral, never dim.
    return { name: ARC_SEGMENTS[index], state: currentHour >= end ? "quiet" : "ahead" };
  });
}

/**
 * The beacon is honest or it is absent.
 *
 * It breathes only while a real signal is recent, goes still when one is not,
 * and does not exist at all for a parent with no mechanism signals configured.
 * An animation that ran unconditionally would be a liveness indicator that
 * indicates nothing — the most expensive kind of lie a reassurance product can
 * tell. Still is grey, never red: a quiet phone is not an emergency.
 */
export function computeBeacon(
  parentPings: Ping[],
  alarmGrade: Set<string>,
  mechanism: Set<string>,
  now: Date,
): BeaconState | null {
  if (mechanism.size === 0) return null;

  const relevant = parentPings.filter(
    (p) => mechanism.has(p.signal) || alarmGrade.has(p.signal),
  );
  if (relevant.length === 0) return "still";

  const newest = relevant
    .map((p) => new Date(p.ts_utc).getTime())
    .reduce((a, b) => Math.max(a, b));
  return (now.getTime() - newest) / 3_600_000 <= BEACON_FRESH_HOURS
    ? "breathing"
    : "still";
}

export function computeGlance(
  parent: Parent,
  familyTz: string,
  signals: ParentSignal[],
  pings: Ping[],
  now: Date,
  viewerTz: string = Intl.DateTimeFormat().resolvedOptions().timeZone,
): GlanceState {
  const timeZone = effectiveTz(parent.tz, familyTz);
  const alarmGrade = alarmGradeSignals(signals, parent.id);
  const mechanism = mechanismSignals(signals, parent.id);

  const mine = pings.filter((p) => p.parent_id === parent.id);
  const routine = mine
    .filter((p) => alarmGrade.has(p.signal))
    .sort((a, b) => a.ts_utc.localeCompare(b.ts_utc));

  const dayStart = localDayStart(now, timeZone);
  const routineToday = routine.filter((p) => new Date(p.ts_utc) >= dayStart);
  const last = routine.length > 0 ? routine[routine.length - 1] : null;
  const hour = localHour(now, timeZone);
  const dayPart = dayPartFor(hour);
  const seenToday = routineToday.length > 0;

  return {
    parentId: parent.id,
    name: parent.display_name,
    seenToday,
    dayPart,
    headline: headlineFor(parent.display_name, seenToday, dayPart),
    subline: last
      ? renderSubline(
          parent.display_name,
          formatLocalTime(last.ts_utc, timeZone),
          formatLocalTime(last.ts_utc, viewerTz),
        )
      : null,
    arc: buildArc(
      routineToday.map((p) => localHour(new Date(p.ts_utc), timeZone)),
      hour,
    ),
    beacon: computeBeacon(mine, alarmGrade, mechanism, now),
    timeZone,
  };
}
