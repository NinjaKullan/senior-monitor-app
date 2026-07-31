/**
 * Every table this app reads, and every column it asks for.
 *
 * Declared in one place on purpose. There is no `family_id = ?` filter
 * anywhere in this app: isolation is RLS's job, and the client asking politely
 * would only hide a policy bug. product/tests/test_webapp_surface.py reads this
 * file, checks each table is RLS-protected with a policy, and runs the same
 * selects as the `authenticated` role over two families to prove the surface is
 * covered.
 */

export const READ_SURFACE = {
  families: "id, name, tz",
  parents: "id, family_id, display_name, tz",
  members: "id, family_id, display_name, role, digest_channel",
  parent_signals: "parent_id, signal, alarm_grade, active",
  pings: "parent_id, signal, ts_utc",
  digest_sends: "parent_id, kind, local_date, ts_utc",
} as const;

export type ReadTable = keyof typeof READ_SURFACE;
