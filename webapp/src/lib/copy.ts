/**
 * Family-facing copy.
 *
 * The digest templates that used to open this file are gone with the Digests
 * screen (DECISIONS 156): from Wave B the digest IS the email, its copy lives
 * in the backend's template registry, and dead strings kept "just in case"
 * are how retired copy leaks back onto a screen. Deleted, not unrendered —
 * the same reasoning as `never` in the recency vocabulary.
 */

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

/**
 * The tripwire health view (spec 005d) — a maintenance surface, in equipment
 * tone throughout.
 *
 * Every string below describes plumbing. `Not heard in a while` is as dark as
 * this screen goes and it is amber, not red, because a tripwire that stopped
 * reporting is a Shortcuts problem until proven otherwise; the person it reports
 * on is not mentioned by any of it. The nudge is the one string that names the
 * parent, and it names them as the owner of a phone that needs two minutes.
 */
export const TRIPWIRE_TITLE = "Tripwires";
export const TRIPWIRE_CONNECTED = "Connected";
export const TRIPWIRE_STALE = "Not heard in a while";
/**
 * Never heard from. Neutral, not amber: absence of *ever* means nobody has
 * installed the shortcut yet, which is a setup step, not a fault (PM ruling on
 * DECISIONS 60).
 */
export const TRIPWIRE_UNSET = "Not set up yet";
export const TRIPWIRE_REPAIR =
  "A tripwire may need a quick fix on {name}'s phone. It's a two-minute FaceTime.";
export const TRIPWIRE_BACK = "Back to today";
/** The Glance card's accessible name for its tap target — it names the destination. */
export const TRIPWIRE_OPEN_LABEL = "Tripwire health for {name}";

/**
 * Recency, at day granularity and no finer. There is no clock-time variant of
 * these on purpose: a precise timestamp against each app is ammunition, and the
 * repair question — is this thing still reporting? — is answered in days.
 *
 * There is no `never` either, as of the founder's on-device round: a tripwire
 * that has never reported renders its chip and no recency at all. `never` beside
 * `Not set up yet` was redundant, and it read as a verdict. The word is gone
 * from the module rather than merely unused at the call site — the same
 * discipline as the missing clock variant, since a string that does not exist
 * cannot come back by accident.
 */
export const RECENCY_TODAY = "today";
export const RECENCY_YESTERDAY = "yesterday";
export const RECENCY_DAYS = "{days} days ago";

/**
 * Login (DECISIONS 115). The mailer is equipment, so its failures are worded
 * like equipment — calm, specific, and with the next step in the sentence. A
 * rate limit surfacing as silence was the founder's lost hour: the screen said
 * "check your email" over a link that was never sent.
 */
export const LOGIN_SENT =
  "Check your email for a sign-in link. It can take a minute — look in spam if it hasn't arrived.";
export const LOGIN_RATE_LIMITED =
  "That's a few links in a row, and the mailer needs a short break. Wait a few minutes, then try once more.";
export const LOGIN_FAILED = "That didn't go through. Check the address and try again.";

/**
 * The setup card (spec 005b §4.1) — the Family screen's forwarding surface.
 *
 * This copy renders on a surface the copy law scans with almost no allowlist:
 * it names no signal, and the only app name on it is the one the PM exempted
 * by ruling (DECISIONS 122) — `SETUP_SEND_LABEL`, and that key alone. The
 * rationale is the law's own shape: app names are banned where they would
 * describe *a parent's behaviour*, and this string describes the child's next
 * action. Navigation, not surveillance vocabulary.
 *
 * "Reach for on their phone" is the habits question (§4.5) phrased inside the
 * law; the answer guides which everyday things the routine watches, and it is
 * asked of the child, not the parent.
 */
export const SETUP_TITLE = "Setup";
export const SETUP_READY = "Ready to send";
export const SETUP_REPORTING = "Set up and reporting";
export const SETUP_NEEDS_LINK = "Needs a fresh link";
/** The one channel name this surface may carry, exempted by DECISIONS 122 and
 *  pinned by value in the copy-law test. The parent it belongs to is named on
 *  the line directly above it in the card. */
export const SETUP_SEND_LABEL = "Send on WhatsApp";
export const SETUP_EXPIRES = "Link works until {date}";
export const SETUP_HOW = [
  "Send the link first, then that person's button files into the same chat, " +
    "as documents — one person's set at a time.",
  "Before sending: ask what they reach for on their phone every day without " +
    "thinking. That is what the routine should watch.",
] as const;

export const NO_FAMILY_TITLE = "No family yet";
export const NO_FAMILY_BODY =
  "This account is not linked to a family. Once your family is set up, today's glance will appear here.";
export const PRIVACY_FOOTER =
  "Kettle stores three things: who, which routine, when. Nothing else exists to show you.";

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

/**
 * Day-granularity recency. The `days` argument is ignored unless kind is `days`.
 *
 * `never` is not in the parameter type: a tripwire that has never reported has
 * no recency to render, and the caller decides that by not calling. The type is
 * what stops a future caller reaching for a word that no longer exists.
 */
export function renderRecency(
  kind: "today" | "yesterday" | "days",
  days: number = 0,
): string {
  if (kind === "today") return RECENCY_TODAY;
  if (kind === "yesterday") return RECENCY_YESTERDAY;
  return RECENCY_DAYS.replace("{days}", String(days));
}

export function renderRepairNudge(name: string): string {
  return TRIPWIRE_REPAIR.replace("{name}", name);
}
