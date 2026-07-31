/**
 * Recompose the digest list from what was actually sent.
 *
 * `digest_sends` records that a message went out — to whom, for which parent,
 * of which kind, on which local date — and deliberately stores no text. So the
 * list is rebuilt from the same templates the backend used, and the morning
 * message's one clock time is recomputed from the pings it was derived from.
 * Nothing new is stored to make this screen possible.
 */

import { renderEvening, renderMorning } from "./copy";
import type { DigestSend, Parent, ParentSignal, Ping } from "./types";
import { alarmGradeSignals } from "./glance";
import { effectiveTz, formatLocalTime, localDate } from "./time";

export interface DigestEntry {
  key: string;
  kind: "morning" | "evening";
  localDate: string;
  message: string;
  sentAt: string;
}

function firstRoutineOfDay(
  parent: Parent,
  familyTz: string,
  signals: ParentSignal[],
  pings: Ping[],
  day: string,
): string | null {
  const timeZone = effectiveTz(parent.tz, familyTz);
  const alarmGrade = alarmGradeSignals(signals, parent.id);
  const sameDay = pings
    .filter(
      (p) =>
        p.parent_id === parent.id &&
        alarmGrade.has(p.signal) &&
        localDate(new Date(p.ts_utc), timeZone) === day,
    )
    .sort((a, b) => a.ts_utc.localeCompare(b.ts_utc));
  return sameDay.length > 0 ? formatLocalTime(sameDay[0].ts_utc, timeZone) : null;
}

export function buildDigestEntries(
  sends: DigestSend[],
  parents: Parent[],
  familyTz: string,
  signals: ParentSignal[],
  pings: Ping[],
): DigestEntry[] {
  const byParent = new Map(parents.map((p) => [p.id, p]));

  // One delivered message may have produced several rows — an aggregated
  // evening records one per parent it vouched for — so group them back.
  const groups = new Map<string, DigestSend[]>();
  for (const send of sends) {
    const key = `${send.kind}|${send.local_date}`;
    groups.set(key, [...(groups.get(key) ?? []), send]);
  }

  const entries: DigestEntry[] = [];
  for (const [key, rows] of groups) {
    const [kind, day] = key.split("|") as ["morning" | "evening", string];
    const named = rows
      .map((r) => byParent.get(r.parent_id))
      .filter((p): p is Parent => Boolean(p));
    if (named.length === 0) continue;

    const sentAt = rows
      .map((r) => r.ts_utc)
      .sort()
      .slice(-1)[0];

    if (kind === "morning") {
      for (const parent of named) {
        const time = firstRoutineOfDay(parent, familyTz, signals, pings, day);
        if (time === null) continue; // no evidence left to recompose from
        entries.push({
          key: `${key}|${parent.id}`,
          kind,
          localDate: day,
          message: renderMorning(parent.display_name, time),
          sentAt,
        });
      }
    } else {
      const names = named
        .map((p) => p.display_name)
        .sort((a, b) => a.localeCompare(b));
      entries.push({
        key,
        kind,
        localDate: day,
        message: renderEvening(names),
        sentAt,
      });
    }
  }

  return entries.sort(
    (a, b) => b.localDate.localeCompare(a.localDate) || b.kind.localeCompare(a.kind),
  );
}
