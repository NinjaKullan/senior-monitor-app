/**
 * Family notes (spec 009 §4): pure helpers between the journal_entries rows
 * and the panel. Bodies are family-authored plain text — the app's job is to
 * render them INERT (React escapes every text node; linkify below never emits
 * markup from the body, only splits it into text and anchor elements) and to
 * keep every read bounded (DECISIONS 160: newest-first, explicit limit, per
 * scope).
 */

import type { JournalEntry } from "./types";

/** URLs a note may carry: explicit http(s), or a bare domain whose first
 *  label is at least two characters ("amazon.in/gp/…", "wa.me/x"), so prose
 *  like "e.g." never turns into a link. The pattern deliberately stops at
 *  whitespace and quote characters — a body cannot extend an href past its
 *  own text. */
const URL_PATTERN =
  /\bhttps?:\/\/[^\s<>"']+|\b(?:www\.)?[a-z0-9][a-z0-9-]+(?:\.[a-z0-9-]{2,})+(?:\/[^\s<>"']*)?/gi;

export type BodySegment = { kind: "text"; text: string } | { kind: "link"; href: string; label: string };

/** Split a body into text and link segments. The caller renders text
 *  segments as React text nodes (escaped by construction) and link segments
 *  as anchors with rel="noopener noreferrer" — never innerHTML. */
export function linkify(body: string): BodySegment[] {
  const segments: BodySegment[] = [];
  let cursor = 0;
  for (const match of body.matchAll(URL_PATTERN)) {
    const start = match.index ?? 0;
    // Trailing punctuation reads as prose, not address.
    const raw = match[0].replace(/[.,;:!?)]+$/, "");
    if (start > cursor) segments.push({ kind: "text", text: body.slice(cursor, start) });
    segments.push({
      kind: "link",
      href: /^https?:\/\//i.test(raw) ? raw : `https://${raw}`,
      label: raw,
    });
    cursor = start + raw.length;
  }
  if (cursor < body.length) segments.push({ kind: "text", text: body.slice(cursor) });
  return segments;
}

/**
 * The calendar date an INSTANT fell on, in a given timezone, as "YYYY-MM-DD".
 *
 * DECISIONS 251. `created_utc` is a moment, not a date, and slicing its first
 * ten characters reads the UTC day: a note written at 9:05pm in New York is
 * already tomorrow in UTC, so it was labelled with tomorrow's date. Every
 * family member in the Americas writing a note after about 8pm saw the wrong
 * day, on their own note, which is the kind of small wrongness that makes a
 * record feel untrustworthy.
 *
 * `en-CA` because it formats as YYYY-MM-DD, which is what the rest of this
 * module already speaks; the value is a key, never something a person reads.
 *
 * Note what this is NOT for. `event_date` is a date-only string with no
 * instant behind it, and the formatters below pin those to UTC deliberately
 * so a bare calendar date never shifts. Convert instants here; leave dates
 * alone.
 */
export function localDay(instantIso: string, tz: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: tz,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(instantIso));
}

/** "Aug 24" — for entry metadata and the past-event tag. Date-only strings
 *  are pinned to UTC so a calendar date never shifts a day at render. */
export function monthDay(isoDate: string): string {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "UTC",
    month: "short",
    day: "numeric",
  }).format(new Date(`${isoDate.slice(0, 10)}T00:00:00Z`));
}

/** "August 2026" — the Memory feed's month separators (spec 012 §2): the
 *  line that turns a list into a record. Same UTC pinning as monthDay. */
export function monthYear(isoDate: string): string {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "UTC",
    month: "long",
    year: "numeric",
  }).format(new Date(`${isoDate.slice(0, 10)}T00:00:00Z`));
}

/** "Tue, Sep 1" — the Upcoming strip's date form (spec 009 §4). */
export function weekdayMonthDay(isoDate: string): string {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "UTC",
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(new Date(`${isoDate.slice(0, 10)}T00:00:00Z`));
}

/** The body's first line, for the Upcoming strip. */
export function firstLine(body: string): string {
  return body.split("\n")[0].trim();
}

/** Entries whose event date is today or later, soonest first. `todayDate` is
 *  the viewer's local calendar date (YYYY-MM-DD). */
export function upcomingEntries(entries: JournalEntry[], todayDate: string): JournalEntry[] {
  return entries
    .filter((e) => e.event_date !== null && e.event_date >= todayDate)
    .sort((a, b) => (a.event_date ?? "").localeCompare(b.event_date ?? ""));
}

/** Everything that is not upcoming, newest first (the rows' own order). */
export function pastEntries(entries: JournalEntry[], todayDate: string): JournalEntry[] {
  return entries.filter((e) => e.event_date === null || e.event_date < todayDate);
}

/* --- spec 012 §9.1: the notes filters ------------------------------------ */

/** The four timeframes, as the chips offer them. `null` months = all time. */
export const TIMEFRAMES = [
  { id: "month", months: 1 },
  { id: "3m", months: 3 },
  { id: "6m", months: 6 },
  { id: "all", months: null },
] as const;

export type TimeframeId = (typeof TIMEFRAMES)[number]["id"];

/** DECISIONS 211: the view opens on All parents over three months. */
export const DEFAULT_TIMEFRAME: TimeframeId = "3m";
export const DEFAULT_PARENT_FILTER: string | null = null;

/**
 * The oldest date a timeframe admits, as an ISO day.
 *
 * "This month" means the calendar month `todayDate` falls in, not the last
 * thirty days: on the 2nd, a family filtering to this month wants the 1st,
 * not five weeks of history. The others are rolling windows back from today,
 * which is what "3 months" reads as.
 */
export function timeframeStart(todayDate: string, id: TimeframeId): string | null {
  const months = TIMEFRAMES.find((t) => t.id === id)?.months ?? null;
  if (months === null) return null;
  const [year, month, day] = todayDate.split("-").map(Number);
  if (id === "month") return `${todayDate.slice(0, 7)}-01`;
  // Date arithmetic in UTC so a browser west of Greenwich cannot roll the
  // boundary a day, the way every other date in this app is handled.
  //
  // The day is CLAMPED to the target month's length first. Without it,
  // Date.UTC overflows a short month — six months back from August 30th asks
  // for February 30th and silently lands on March 2nd, quietly excluding two
  // days of notes from a window the family believes is six months wide.
  const targetMonth = month - 1 - months;
  const lastDay = new Date(Date.UTC(year, targetMonth + 1, 0)).getUTCDate();
  const start = new Date(Date.UTC(year, targetMonth, Math.min(day, lastDay)));
  return start.toISOString().slice(0, 10);
}

/**
 * Filter the feed by parent and timeframe (§9.1).
 *
 * Kettle's own lines carry a parent tag and filter with that parent, exactly
 * as the spec requires — nothing here treats an authored note and a Kettle
 * line differently, because the tag is the only thing being read.
 *
 * The timeframe is measured on `created_utc` read in the FAMILY's timezone -
 * the day the note was written where it was written -
 * so an entry does not slip out of view because someone dated an event far
 * ahead; upcoming entries are pulled out by `upcomingEntries` regardless.
 */
export function filterEntries(
  entries: JournalEntry[],
  todayDate: string,
  parentId: string | null,
  timeframe: TimeframeId,
  tz: string,
): JournalEntry[] {
  const start = timeframeStart(todayDate, timeframe);
  return entries.filter((entry) => {
    if (parentId !== null && entry.parent_id !== parentId) return false;
    // The family's day, not UTC's (DECISIONS 251). A note written late on the
    // last evening of August belongs in August, and a window that measured it
    // in UTC would quietly drop it into the next month.
    if (start !== null && localDay(entry.created_utc, tz) < start) return false;
    return true;
  });
}
