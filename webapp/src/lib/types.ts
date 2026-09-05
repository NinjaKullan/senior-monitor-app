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
  /** Spec 017: Kettle is paused for this parent until this instant — the
   *  string "infinity" for the open-ended pause. Null or past = running. */
  paused_until: string | null;
  paused_since: string | null;
}

/** A family note (spec 009 §4): plain text, an optional date, an optional
 *  parent tag. Insert-only in v1 — no edit, no delete. Spec 012 adds `kind`:
 *  'note' for everything the family writes, the gentle-whats kinds for
 *  Kettle's own lines (city_change, started, first_reply, clean_month). */
export interface JournalEntry {
  id: number;
  family_id: string;
  parent_id: string | null;
  author_label: string;
  body: string;
  event_date: string | null;
  created_utc: string;
  kind: string;
  /** Spec 016: null on a note, the note's id on a reply. One level only —
   *  the schema refuses a reply to a reply — and a reply inherits the note's
   *  parent tag (the trigger writes it) and carries no event date. */
  parent_entry_id: number | null;
  /** Spec 018: the seat that wrote it, set server-side from the JWT; null
   *  on Kettle's lines and on rows from before the column existed. */
  author_member_id: string | null;
  /** Spec 018: when the author last edited it; null = never. */
  edited_utc: string | null;
}

/** One line of the family's own contacts sheet (spec 012 §4). UNLIKE the
 *  journal, contacts are editable and deletable — reference data, not
 *  record. E.164 rides the tel: href; phone_display is what a person sees. */
export interface FamilyContact {
  id: number;
  family_id: string;
  parent_id: string | null;
  label: string;
  name: string;
  phone_e164: string;
  phone_display: string;
  note: string;
  position: number;
}

/** A seat in the circle (spec 015). `role` is 'admin' or 'member' (0025);
 *  a null auth_user_id is a seat nobody has signed in to yet; `mail` is the
 *  one switch a person holds over Kettle's mail to them. */
export interface Member {
  id: string;
  family_id: string;
  display_name: string | null;
  role: string;
  digest_channel: string;
  auth_user_id: string | null;
  mail: boolean;
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
