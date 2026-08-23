/**
 * Every table this app reads, and every column it asks for.
 *
 * Declared in one place on purpose. There is no `family_id = ?` filter
 * anywhere in this app: isolation is RLS's job, and the client asking politely
 * would only hide a policy bug. product/tests/test_webapp_surface.py reads this
 * file, checks each table is RLS-protected with a policy, and runs the same
 * selects as the `authenticated` role over two families to prove the surface is
 * covered.
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
  parents: "id, family_id, display_name, tz",
  members: "id, family_id, display_name, role, digest_channel",
  parent_signals: "parent_id, signal, alarm_grade, active",
  pings: "parent_id, signal, ts_utc",
  // Spec 005b: the family's own setup links, so the Family screen can offer
  // "Mom's setup" as a forwardable card. parent_id is on the row precisely so
  // this surface never has to read `devices` — tokens stay out of the browser.
  setup_links: "parent_id, slug, created_utc, expires_utc, revoked_utc",
} as const;

export type ReadTable = keyof typeof READ_SURFACE;
