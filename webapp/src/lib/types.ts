/** Row shapes, exactly as the RLS-protected tables expose them. */

export interface Family {
  id: string;
  name: string;
  tz: string;
}

export interface Parent {
  id: string;
  family_id: string;
  display_name: string;
  tz: string | null;
  /** E.164, or null. Renders only inside a tel: href — never as visible text
   *  (DECISIONS 167: family-facing numbers are tap-to-act links). */
  phone_e164: string | null;
  /** Same law as phone_e164: exists to build a wa.me href when no phone
   *  number is set (spec 009 §2), never rendered as text. */
  whatsapp_e164: string | null;
  /** The label the family actually uses (Mom, Dad, …) — DECISIONS 149's
   *  vocabulary, now the card's name line (spec 009 §2). Null falls back to
   *  display_name. */
  relationship: string | null;
  /** The city picked for this parent (spec 010: the city IS the timezone
   *  control — picking one writes label and tz together). */
  city_label: string | null;
  /** When the zone last actually changed (spec 010): the engine's
   *  changeover-conservatism clock, and the webapp's changeover-day marker
   *  for the Recent-days dots. */
  tz_changed_utc: string | null;
}

/** A family note (spec 009 §4): plain text, an optional date, an optional
 *  parent tag. Insert-only in v1 — no edit, no delete. */
export interface JournalEntry {
  id: number;
  family_id: string;
  parent_id: string | null;
  author_label: string;
  body: string;
  event_date: string | null;
  created_utc: string;
}

export interface Member {
  id: string;
  family_id: string;
  display_name: string | null;
  role: string;
  digest_channel: string;
}

export interface ParentSignal {
  parent_id: string;
  signal: string;
  alarm_grade: boolean;
  active: boolean;
}

export interface Ping {
  parent_id: string;
  signal: string;
  ts_utc: string;
}

/**
 * A parent's setup-page link (spec 005b). The slug is the page's credential;
 * this app may *forward* it — that is the whole point of the row — but must
 * never print it as visible text, only carry it inside an href.
 */
export interface SetupLink {
  parent_id: string;
  slug: string;
  created_utc: string;
  expires_utc: string;
  revoked_utc: string | null;
}
