/**
 * The tripwire health view's logic, as pure functions (spec 005d).
 *
 * This is a **maintenance surface**, not an activity feed. Everything here
 * answers one question — is this piece of plumbing still reporting, and if not,
 * is it worth a FaceTime? — and nothing here answers "what has she been doing".
 * Two rules keep that line where it belongs:
 *
 * 1. **Day granularity, never clock time.** A per-app list stamped with times is
 *    ammunition ("why were you up at 2am?"). The repair question is answered by
 *    `today` / `yesterday` / `3 days ago` / `never`, so that is all this module
 *    can produce. The card's subline keeps its clock — one coarse "last routine"
 *    fact is not a per-app ledger.
 * 2. **Health describes equipment.** A tripwire that has stopped reporting is a
 *    Shortcuts problem until proven otherwise, so the worst state here is
 *    `stale`, its colour is amber, and its copy never reaches past the phone to
 *    the person holding it (product law #6).
 */

import { SIGNAL_DISPLAY_NAMES } from "./signalNames";
import type { Parent, ParentSignal, Ping } from "./types";
import { effectiveTz, localDate } from "./time";

/**
 * How long a signal may go unheard before it reads `Not heard in a while`.
 *
 * `device_alive` is a daily timer, so it gets one cadence plus slack — the same
 * 26 hours the beacon uses, for the same reason. Everything else is a human
 * opening an app, and humans skip days: a news app she reads on Sundays is not
 * broken plumbing on a Wednesday. v1 numbers are deliberate over-estimates,
 * because a false `Not heard in a while` spends the family's attention on a
 * tripwire that is working.
 *
 * These fixed windows stand until the threshold-analysis spec exists (PM ruling
 * on DECISIONS 59). Learning a cadence from a parent's own ping history is the
 * obvious tuning move and is **deferred, not rejected**: if it is ever built it
 * is mechanism-health only, never displayed and never compared across time —
 * and that ruling waits for that spec rather than being assumed here.
 */
export const CADENCE_HOURS: Record<string, number> = { device_alive: 26 };
export const DEFAULT_CADENCE_HOURS = 7 * 24;

/**
 * Three states, and the third is the one that matters most (PM ruling on
 * DECISIONS 60).
 *
 * `unconfigured` — never heard from, ever — is not `stale`. Absence of *ever* is
 * not-yet-configured, not broken: the same distinction the 001 item-4 ruling
 * drew when it suppressed the infra alert until the first ping arrived. It gets
 * a neutral chip, not amber, and it never triggers the repair nudge, because a
 * family's first minutes in the app must not open with "something needs fixing".
 */
export type TripwireHealth = "connected" | "stale" | "unconfigured";
export type RecencyKind = "today" | "yesterday" | "days" | "never";

export interface Recency {
  kind: RecencyKind;
  /** Whole local days since the last ping. Only meaningful when kind is `days`. */
  days: number;
}

export interface TripwireRow {
  /** The raw signal, for keys and tests. Never rendered — `name` is. */
  signal: string;
  /** The humanised name, matching the shortcut the family has on the phone. */
  name: string;
  health: TripwireHealth;
  recency: Recency;
}

export interface TripwireHealthView {
  parentId: string;
  parentName: string;
  rows: TripwireRow[];
  /**
   * True when at least one tripwire has *stopped* reporting. Deliberately not
   * `!== "connected"`: a parent whose shortcuts are not installed yet has no
   * repair to do, and greeting a new family with "something needs fixing" is
   * the alarm-fatigue failure this product exists to avoid.
   */
  needsRepair: boolean;
}

export function cadenceHoursFor(signal: string): number {
  return CADENCE_HOURS[signal] ?? DEFAULT_CADENCE_HOURS;
}

/**
 * A signal a parent has configured but that this app has no humanised name for.
 * Rendering the raw `charge_on` would leak the schema onto the one screen the
 * family reads names from, so it is title-cased instead. The standard set is
 * covered by `SIGNAL_DISPLAY_NAMES`, and a Python test fails if the two drift,
 * so this branch only ever runs for a signal nobody has provisioned yet.
 */
export function displayName(signal: string): string {
  const known = SIGNAL_DISPLAY_NAMES[signal];
  if (known) return known;
  return signal
    .split(/[_\s]+/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/** Whole local days between two instants, floored at zero against clock skew. */
export function localDaysBetween(earlier: Date, later: Date, timeZone: string): number {
  const day = (instant: Date) => Date.parse(`${localDate(instant, timeZone)}T00:00:00Z`);
  return Math.max(0, Math.round((day(later) - day(earlier)) / 86_400_000));
}

export function recencyFor(last: Date | null, now: Date, timeZone: string): Recency {
  if (last === null) return { kind: "never", days: 0 };
  const days = localDaysBetween(last, now, timeZone);
  if (days === 0) return { kind: "today", days };
  if (days === 1) return { kind: "yesterday", days };
  return { kind: "days", days };
}

/**
 * Health is a straight cadence comparison on hours, not on the day-granularity
 * recency above. The two deliberately disagree at the edges: a signal last heard
 * `yesterday` at 22:00 is 12 hours old and still connected. Recency is what the
 * family may *see*; the cadence is what the app *decides* with.
 *
 * The boundary breathes — exactly at cadence still reads connected — so a
 * tripwire cannot flap between states on the tick of an hour.
 *
 * Never heard from is `unconfigured`, and the cadence never enters into it: a
 * shortcut nobody installed cannot be late for a deadline it never had.
 */
export function healthFor(last: Date | null, now: Date, signal: string): TripwireHealth {
  if (last === null) return "unconfigured";
  const hours = (now.getTime() - last.getTime()) / 3_600_000;
  return hours <= cadenceHoursFor(signal) ? "connected" : "stale";
}

function newestPing(pings: Ping[], parentId: string, signal: string): Date | null {
  const times = pings
    .filter((p) => p.parent_id === parentId && p.signal === signal)
    .map((p) => new Date(p.ts_utc).getTime());
  return times.length > 0 ? new Date(Math.max(...times)) : null;
}

/**
 * One row per active `parent_signals` entry for this parent, in the order the
 * signals were configured. Deliberately not sorted stale-first: a maintenance
 * list whose rows rearrange themselves between polls is harder to read, and the
 * amber chip already carries the attention.
 */
export function computeTripwires(
  parent: Parent,
  familyTz: string,
  signals: ParentSignal[],
  pings: Ping[],
  now: Date,
): TripwireHealthView {
  const timeZone = effectiveTz(parent.tz, familyTz);
  const rows = signals
    .filter((s) => s.parent_id === parent.id && s.active)
    .map((s) => {
      const last = newestPing(pings, parent.id, s.signal);
      return {
        signal: s.signal,
        name: displayName(s.signal),
        health: healthFor(last, now, s.signal),
        recency: recencyFor(last, now, timeZone),
      };
    });

  return {
    parentId: parent.id,
    parentName: parent.display_name,
    rows,
    needsRepair: rows.some((row) => row.health === "stale"),
  };
}
