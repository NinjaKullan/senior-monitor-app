/**
 * The Glance screen's logic, as a pure function.
 *
 * Two states, and the darker one is `Quiet so far`. Nothing scarier exists in
 * this app: absence that matters belongs to the ladder, and the ladder has no
 * surface here. A family opening this at an anxious moment sees either
 * reassurance or an honest "not yet today" — never a verdict.
 */

import { GLANCE_ALL_NORMAL, GLANCE_QUIET } from "./copy";
import type { Parent, ParentSignal, Ping } from "./types";
import { effectiveTz, formatLocalTime, localDayStart } from "./time";

export interface GlanceState {
  parentId: string;
  name: string;
  status: typeof GLANCE_ALL_NORMAL | typeof GLANCE_QUIET;
  /** "8:12 am" for the last alarm-grade ping ever seen, or null. */
  lastSeen: string | null;
  timeZone: string;
}

export function alarmGradeSignals(signals: ParentSignal[], parentId: string): Set<string> {
  return new Set(
    signals
      .filter((s) => s.parent_id === parentId && s.alarm_grade && s.active)
      .map((s) => s.signal),
  );
}

export function computeGlance(
  parent: Parent,
  familyTz: string,
  signals: ParentSignal[],
  pings: Ping[],
  now: Date,
): GlanceState {
  const timeZone = effectiveTz(parent.tz, familyTz);
  const alarmGrade = alarmGradeSignals(signals, parent.id);

  const routine = pings
    .filter((p) => p.parent_id === parent.id && alarmGrade.has(p.signal))
    .sort((a, b) => a.ts_utc.localeCompare(b.ts_utc));

  const dayStart = localDayStart(now, timeZone);
  const seenToday = routine.some((p) => new Date(p.ts_utc) >= dayStart);
  const last = routine.length > 0 ? routine[routine.length - 1] : null;

  return {
    parentId: parent.id,
    name: parent.display_name,
    status: seenToday ? GLANCE_ALL_NORMAL : GLANCE_QUIET,
    lastSeen: last ? formatLocalTime(last.ts_utc, timeZone) : null,
    timeZone,
  };
}
