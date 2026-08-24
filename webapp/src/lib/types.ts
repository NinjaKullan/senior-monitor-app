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
