/**
 * Spec 020: the family's own devices, as facts. Everything here is a pure
 * function over the snapshot's device and household-ping rows. Nothing here
 * is read by a verdict: computeParentToday never sees these rows, the arc
 * and the dots are untouched, and the line and the block are suppressed
 * whenever the card is in its night, paused or unreachable state.
 */
import {
  DEVICE_LINE_AFTERNOON,
  DEVICE_LINE_EVENING,
  DEVICE_LINE_MORNING,
  DEVICE_NOTHING_YET,
  DEVICE_ROW,
  KIND_LABEL,
  renderHeard,
} from "./copy";
import {
  AFTERNOON_START,
  DAY_START_HOUR,
  EVENING_START,
  countsForDay,
  localHour,
  type ParentToday,
} from "./parentState";
import { formatLocalTime, localDate } from "./time";
import type { HouseholdDevice, HouseholdPing } from "./types";

/** The most devices one parent may have (spec 020 §2). */
export const DEVICE_LIMIT_PER_PARENT = 3;

export type KindValue = keyof typeof KIND_LABEL;

export function kindLabel(kind: string): string {
  return (KIND_LABEL as Record<string, string>)[kind] ?? kind;
}

export interface DeviceRow {
  id: string;
  kind: string;
  /** "Plug · 8:05 am" — the day view's row. */
  text: string;
}

export interface DeviceSetupRow {
  id: string;
  parentId: string;
  kind: string;
  platform: string | null;
  /** "Plug · Heard from 12 minutes ago" / "Plug · Nothing heard yet". */
  text: string;
}

function liveFor(devices: HouseholdDevice[], parentId: string): HouseholdDevice[] {
  return devices.filter((d) => d.parent_id === parentId && d.removed_utc === null);
}

/** A device's pings today from DAY_START_HOUR on, newest first, not ahead
 *  of now (299's clock: a ping before six belongs to no day). */
function todaysPings(
  device: HouseholdDevice,
  pings: HouseholdPing[],
  timeZone: string,
  now: Date,
): HouseholdPing[] {
  const today = localDate(now, timeZone);
  return pings
    .filter(
      (p) =>
        p.device_id === device.id &&
        new Date(p.ts_utc).getTime() <= now.getTime() &&
        countsForDay({ parent_id: device.parent_id, signal: "", ts_utc: p.ts_utc }, today, timeZone),
    )
    .sort((a, b) => b.ts_utc.localeCompare(a.ts_utc));
}

/** The card suppresses the house while it is not showing a day. */
function cardShowsADay(state: ParentToday): boolean {
  return !state.night && !state.paused && state.kind !== "unreachable";
}

/** The Today card's one line (§5): the most recent device today, by the
 *  ping's local hour. Null means no line and no placeholder. */
export function deviceLine(
  state: ParentToday,
  devices: HouseholdDevice[],
  pings: HouseholdPing[],
  now: Date,
): string | null {
  if (!cardShowsADay(state)) return null;
  const timeZone = state.timeZone;
  let newest: { device: HouseholdDevice; ping: HouseholdPing } | null = null;
  for (const device of liveFor(devices, state.parentId)) {
    const [ping] = todaysPings(device, pings, timeZone, now);
    if (ping && (!newest || ping.ts_utc > newest.ping.ts_utc)) newest = { device, ping };
  }
  if (!newest) return null;
  const hour = localHour(new Date(newest.ping.ts_utc), timeZone);
  const form =
    hour < AFTERNOON_START
      ? DEVICE_LINE_MORNING
      : hour < EVENING_START
        ? DEVICE_LINE_AFTERNOON
        : DEVICE_LINE_EVENING;
  return form
    .replace("{kind}", kindLabel(newest.device.kind))
    .replace("{time}", formatLocalTime(newest.ping.ts_utc, timeZone));
}

/**
 * The day view's block (§5): null when the parent has no device (the block
 * is absent), else each device heard today from six on, most recent first,
 * at most three — an empty list is DEVICES_NONE_TODAY. Today only.
 */
export function devicesToday(
  state: ParentToday,
  devices: HouseholdDevice[],
  pings: HouseholdPing[],
  now: Date,
): DeviceRow[] | null {
  const live = liveFor(devices, state.parentId);
  if (live.length === 0) return null;
  if (!cardShowsADay(state)) return [];
  const rows = live
    .map((device) => ({ device, ping: todaysPings(device, pings, state.timeZone, now)[0] }))
    .filter((r): r is { device: HouseholdDevice; ping: HouseholdPing } => Boolean(r.ping))
    .sort((a, b) => b.ping.ts_utc.localeCompare(a.ping.ts_utc))
    .slice(0, DEVICE_LIMIT_PER_PARENT);
  return rows.map(({ device, ping }) => ({
    id: device.id,
    kind: device.kind,
    text: DEVICE_ROW.replace("{kind}", kindLabel(device.kind)).replace(
      "{time}",
      formatLocalTime(ping.ts_utc, state.timeZone),
    ),
  }));
}

/** The setup rows (§5): every live device with its heard line from the
 *  newest ping at any hour — a fact about the plumbing, not a verdict. */
export function deviceSetupRows(
  parentId: string,
  devices: HouseholdDevice[],
  pings: HouseholdPing[],
  now: Date,
): DeviceSetupRow[] {
  return liveFor(devices, parentId)
    .sort((a, b) => a.created_utc.localeCompare(b.created_utc))
    .map((device) => {
      const newest = pings
        .filter((p) => p.device_id === device.id)
        .map((p) => new Date(p.ts_utc).getTime())
        .reduce((a, b) => Math.max(a, b), 0);
      const heard = newest > 0 ? renderHeard(now.getTime() - newest) : DEVICE_NOTHING_YET;
      return {
        id: device.id,
        parentId,
        kind: device.kind,
        platform: device.platform,
        text: DEVICE_ROW.replace("{kind}", kindLabel(device.kind)).replace("{time}", heard),
      };
    });
}

/** The verdict clock, re-exported so a reader of this module sees the rule
 *  it follows: nothing before DAY_START_HOUR is today's. */
export { DAY_START_HOUR };
