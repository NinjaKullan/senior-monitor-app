/** Local-time helpers. Storage is UTC everywhere; display is the parent's zone. */

/** "8:12 am" — the same shape the backend renders into a digest. */
export function formatLocalTime(iso: string, timeZone: string): string {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).formatToParts(new Date(iso));
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  return `${get("hour")}:${get("minute")} ${get("dayPeriod").toLowerCase()}`;
}

/** The local calendar date (YYYY-MM-DD) an instant falls on, in a given zone. */
export function localDate(instant: Date, timeZone: string): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(instant);
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  return `${get("year")}-${get("month")}-${get("day")}`;
}

/** Start of the local day containing `instant`, as a UTC instant. */
export function localDayStart(instant: Date, timeZone: string): Date {
  const date = localDate(instant, timeZone);
  // Walk back from the instant to the first moment whose local date matches.
  // Binary search over a 48h window keeps this correct across DST shifts.
  let low = new Date(instant.getTime() - 48 * 3600 * 1000).getTime();
  let high = instant.getTime();
  while (high - low > 60_000) {
    const mid = Math.floor((low + high) / 2);
    if (localDate(new Date(mid), timeZone) === date) high = mid;
    else low = mid;
  }
  return new Date(high - (high % 60_000));
}

/** A parent's own zone when set, otherwise the family's. */
export function effectiveTz(parentTz: string | null, familyTz: string): string {
  return parentTz ?? familyTz;
}
