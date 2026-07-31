/**
 * Family-facing copy, mirrored from the backend's kettle/messages.py.
 *
 * The digest list recomposes what was sent from the templates rather than
 * reading stored text — digest_sends deliberately holds no message body, and
 * this app adds no new place to put one.
 *
 * These strings must stay identical to the Python originals. That is not left
 * to discipline: product/tests/test_webapp_copy.py parses this file and fails
 * if the two ever drift.
 */

export const MORNING_TEMPLATE =
  "Good morning — {parent}'s day started normally ({time} {clock}).";
export const EVENING_ONE = "{parent} had a normal, active day.";
export const EVENING_TWO = "{first} and {second} both had normal, active days.";
export const EVENING_MANY = "{leading} and {last} all had normal, active days.";
export const CLOCK_NEUTRAL = "local time";

/** Glance states. `Quiet so far` is as dark as this app ever gets. */
export const GLANCE_ALL_NORMAL = "All normal";
export const GLANCE_QUIET = "Quiet so far";

export const DIGESTS_EMPTY = "Your daily digests will appear here.";
export const NO_FAMILY_TITLE = "No family yet";
export const NO_FAMILY_BODY =
  "This account is not linked to a family. Once your family is set up, today's glance will appear here.";
export const PRIVACY_FOOTER =
  "Kettle stores three things: who, which routine, when. Nothing else exists to show you.";

export function renderMorning(parent: string, time: string): string {
  return MORNING_TEMPLATE.replace("{parent}", parent)
    .replace("{time}", time)
    .replace("{clock}", CLOCK_NEUTRAL);
}

export function renderEvening(parents: string[]): string {
  if (parents.length === 0) throw new Error("an evening digest needs at least one parent");
  if (parents.length === 1) return EVENING_ONE.replace("{parent}", parents[0]);
  if (parents.length === 2)
    return EVENING_TWO.replace("{first}", parents[0]).replace("{second}", parents[1]);
  return EVENING_MANY.replace("{leading}", parents.slice(0, -1).join(", ")).replace(
    "{last}",
    parents[parents.length - 1],
  );
}
