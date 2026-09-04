/**
 * Every table this app reads, and every column it asks for.
 *
 * Declared in one place on purpose. Isolation is RLS's job, and the client
 * asking politely would only hide a policy bug — the `family_id` filters in
 * data.ts (DECISIONS 263) choose which of an account's OWN families the app
 * shows, they never stand in for a policy. product/tests/test_webapp_contract.py
 * reads this file, checks each table is RLS-protected with a policy, and runs
 * the same selects as the `authenticated` role over two families to prove the
 * surface is covered.
 *
 * Spec 005d added a screen without adding a column — 005a already read both
 * tables whole — but it changed what two of them *mean* on screen.
 * `parent_signals.signal` used to pick a beacon's shade and now prints a named
 * list of one parent's apps; `pings.signal` now decides what that list says
 * about each of them. Nothing widened here, so the conscious act required by
 * standing structure 48 happened in the test instead: both tables are now
 * asserted row-by-row for isolation rather than riding on the loop's
 * spot-checks. DECISIONS item 58 records the reasoning.
 */

export const READ_SURFACE = {
  families: "id, name, tz",
  // phone_e164 joined in spec 008 (the detail hero's Call button) — a
  // conscious widening under standing structure 48, sanctioned by DECISIONS
  // 167: the number exists client-side solely to become a tel: href and is
  // never rendered as text. Spec 009 widens three more: whatsapp_e164 (§2,
  // the wa.me fallback href — same never-as-text law), relationship (§2 as
  // written; since DECISIONS 183 the webapp renders display_name instead and
  // the column rides along un-rendered — the PM may narrow this read), and
  // city_label (§5, the city line; the tz control since spec 010). Spec 010
  // adds tz_changed_utc: the changeover-day marker the Recent-days dots
  // classify by — an instant, never rendered as text.
  parents: "id, family_id, display_name, tz, phone_e164, whatsapp_e164, relationship, city_label, tz_changed_utc",
  // Spec 015: the seats list. auth_user_id is read for two facts and rendered
  // for neither — null means "Not signed in yet", and equality with the
  // session's own id marks the viewer's own row (the mail switch). `mail` is
  // the one per-member switch. digest_channel rides along un-rendered until
  // its cleanup (spec 015 §5).
  members: "id, family_id, display_name, role, digest_channel, auth_user_id, mail",
  parent_signals: "parent_id, signal, alarm_grade, active",
  pings: "parent_id, signal, ts_utc",
  // Spec 005b: the family's own setup links, so the Family screen can offer
  // "Mom's setup" as a forwardable card. parent_id is on the row precisely so
  // this surface never has to read `devices` — tokens stay out of the browser.
  setup_links: "parent_id, slug, created_utc, expires_utc, revoked_utc",
  // Spec 009 §4: the family's notes. Grows without bound, so it NEVER rides
  // readAll — every read is newest-first with an explicit limit (the
  // DECISIONS 160 discipline), one bounded read per scope.
  journal_entries: "id, family_id, parent_id, author_label, body, event_date, created_utc, kind",
  // Spec 012 §4: the family's own contacts sheet — small by nature (a
  // handful of rows), read whole, ordered by position. phone_e164 exists
  // client-side solely to become a tel: href (the DECISIONS 167 law);
  // phone_display is the one phone string a person sees.
  family_contacts: "id, family_id, parent_id, label, name, phone_e164, phone_display, note, position",
} as const;

export type ReadTable = keyof typeof READ_SURFACE;
