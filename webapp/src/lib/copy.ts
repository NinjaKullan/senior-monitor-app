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

/**
 * Glance headlines, chosen by the parent's local day-part and whether routine
 * has been seen (spec 005c §1).
 *
 * Warmth rises; information stays coarse. Every one of these says the same
 * coarse thing the flat states said — routine seen, or not yet — in language a
 * person would actually use. None of them says more.
 *
 * `Quiet so far …` is still the floor. Nothing in this app is darker, because
 * anything darker belongs to the ladder and the ladder has no surface here.
 */
export const GLANCE_SEEN_MORNING = "{name}'s morning started the usual way";
export const GLANCE_SEEN_AFTERNOON = "A normal day so far";
export const GLANCE_SEEN_EVENING = "A normal, gentle day";
export const GLANCE_QUIET_MORNING = "Quiet so far this morning";
export const GLANCE_QUIET_TODAY = "Quiet so far today";

/** Shown before a parent has ever sent anything routine. */
export const GLANCE_NO_ROUTINE_YET = "No routine seen yet";

/**
 * Dual-timezone subline: their clock and the viewer's, side by side, because
 * "8:36 pm" means nothing to a child in Texas until they know it was evening in
 * Chennai.
 */
export const SUBLINE_TEMPLATE = "Last routine seen {time} {clock} · {viewerTime} yours";

/**
 * Whose clock the first time belongs to. A gendered form is used only when a
 * pronoun has actually been recorded — nothing is ever inferred from a name
 * (items 24/34, adopted as policy). With none recorded the parent's own name
 * carries it, which reads warmer than a pronoun would anyway.
 */
export const CLOCK_BY_PRONOUN: Record<string, string> = {
  she: "her time",
  he: "his time",
  they: "their time",
};
export const CLOCK_BY_NAME = "{name}'s time";

/** The day arc's three segments, in order. Names only — never counts. */
export const ARC_SEGMENTS = ["Morning", "Afternoon", "Evening"] as const;
export const ARC_LABEL_NONE = "No routine seen yet today";
export const ARC_LABEL_PREFIX = "Routine seen: ";

/** The beacon describes the handset, never the person (attribution law). */
export const BEACON_LABEL = "phone";

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

export function renderClock(name: string, pronoun?: string | null): string {
  const recorded = CLOCK_BY_PRONOUN[(pronoun ?? "").toLowerCase()];
  return recorded ?? CLOCK_BY_NAME.replace("{name}", name);
}

export function renderSubline(
  name: string,
  theirTime: string,
  viewerTime: string,
  pronoun?: string | null,
): string {
  // One clock when both read the same — a child in Chennai does not need to be
  // told twice.
  if (theirTime === viewerTime) {
    return `Last routine seen ${theirTime} ${renderClock(name, pronoun)}`;
  }
  return SUBLINE_TEMPLATE.replace("{time}", theirTime)
    .replace("{clock}", renderClock(name, pronoun))
    .replace("{viewerTime}", viewerTime);
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
