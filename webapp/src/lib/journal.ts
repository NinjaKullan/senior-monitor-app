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

/** "Aug 24" — for entry metadata and the past-event tag. Date-only strings
 *  are pinned to UTC so a calendar date never shifts a day at render. */
export function monthDay(isoDate: string): string {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "UTC",
    month: "short",
    day: "numeric",
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
