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
 * The v5 state vocabulary (spec 008 §4, from docs/Kettle-Design.html).
 *
 * Three sentences for three states, and the floor has not moved: "Quiet so
 * far" is still as dark as this app gets about a person; "unreachable" is a
 * sentence about a phone. The v5 file's she/her forms are restructured here —
 * nothing infers a pronoun from a name (items 24/34, standing policy), so
 * strings parameterize on the name or need no pronoun at all.
 */
export const STATE_ORDINARY = "Today looks like an ordinary day.";
export const STATE_QUIET = "Quiet so far today.";
export const STATE_UNREACHABLE = "Kettle can't hear from {name}'s phone right now.";
/** The unreachable state's one reassurance, de-pronouned from the v5 file. */
export const UNREACHABLE_ASIDE =
  "A call still works fine — this is only about the phone.";

/** Last-heard metas. Clock times at day-or-yesterday reach; day words beyond. */
export const META_HEARD_TODAY = "Heard from at {time} {clock}.";
export const META_HEARD_YESTERDAY = "Last heard from yesterday at {time} {clock}.";
export const META_HEARD_DAYS = "Last heard from {days} days ago.";
export const META_NOTHING_SINCE = "Nothing has reached Kettle since {when}.";
export const META_NOTHING_YET = "Nothing has reached Kettle yet.";
export const LOCAL_LINE = "It's {time} {clock} right now.";

/** The day, in words (spec 008 §5.2). No verdicts on unfinished time: the
 *  stretch being stood in says "so far", and only a finished stretch is
 *  simply quiet. */
export const DAY_TITLE = "The day";
export const DAY_MORNING_HEARD = "An ordinary morning — heard from at {time}.";
export const DAY_HEARD = "Heard from at {time}.";
export const DAY_QUIET_SO_FAR = "Quiet so far.";
export const DAY_QUIET = "Quiet.";
export const DAY_STILL_TO_COME = "Still to come.";
export const DAY_NOTHING = "Nothing has reached Kettle.";

export const RECENT_TITLE = "Recent days";
export const RECENT_ORDINARY = "An ordinary day.";
export const RECENT_QUIET = "A quiet day.";
export const RECENT_NOTHING = "Nothing reached Kettle.";

export const ABOUT_TITLE = "About";
export const TZ_SAME = "The same time as yours.";
export const TZ_AHEAD = "{words} ahead of you.";
export const TZ_BEHIND = "{words} behind you.";
export const TZ_DIFFERENT = "A different clock from yours.";
export const SETUP_MONTH = "The phone was set up in {month}.";

export const CALL_LABEL = "Call {name}";
export const FIX_TITLE = "A small thing to fix";

export const TODAY_TITLE = "Today";
export const FAMILY_TITLE = "Family";
export const FAMILY_SUB =
  "Everyone here sees the same Today screen and gets the same notes.";
export const PARENTS_LABEL = "Parents";
export const FAMILY_CIRCLE_LABEL = "Family circle";
export const TAGLINE = "For checking in, not checking up.";
export const BACK_TO_TODAY = "Today";
/** DECISIONS 172's veto: "watched over" is the framing this product exists
 *  to avoid, so the empty state says only what is true about setup. */
export const EMPTY_TODAY = "No one is set up yet.";

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

/** The day's three parts, in order. Names only — never counts. */
export const DAY_PARTS = ["Morning", "Afternoon", "Evening"] as const;

/**
 * The fix card's body (spec 008 §5.2, reworded by DECISIONS 172). It kept the
 * honest FaceTime repair over the v5 file's steps for an app the parent does
 * not have — and lost the word the old body opened with: "tripwire" is
 * internal vocabulary, never customer-facing, and it joined the copy-law
 * scan's mechanism bans so it cannot return. Internal identifiers, filenames
 * and test names keep the word; rendered strings do not.
 */
export const FIX_BODY =
  "Something on {name}'s phone may need a quick fix. It's a two-minute FaceTime.";
/** The card's accessible name for its tap target — it names the destination. */
export const OPEN_PARENT_LABEL = "More about {name}'s day";

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

export function renderFixBody(name: string): string {
  return FIX_BODY.replace("{name}", name);
}
