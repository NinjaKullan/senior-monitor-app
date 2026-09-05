/**
 * Family-facing copy.
 *
 * Spec 009 is the third vocabulary this file has carried, and the discipline
 * is unchanged: strings the screens no longer render are DELETED, not left
 * around (the `never` precedent, DECISIONS 68) — retired copy that still
 * exists is how it leaks back. "normal" replaces "ordinary" in every rendered
 * string (spec 009 §1); the internal state name stays `ordinary`.
 */

/** The three state sentences (spec 009 §1/§2). "Quiet so far" is still as
 *  dark as this app gets about a person; unreachable is about a phone. */
export const STATE_ORDINARY = "Today looks like a normal day.";
export const STATE_QUIET = "Quiet so far today.";
export const STATE_UNREACHABLE = "Kettle can't hear from {name}'s phone right now.";
/** The unreachable reassurance — also the "Worth a look." card's body. */
export const UNREACHABLE_ASIDE =
  "A call still works fine — this is only about the phone.";

/* ---------------------------------------------------------------------- */
/* Today (spec 009 §2)                                                      */
/* ---------------------------------------------------------------------- */

export const ROLLUP_NORMAL = "Everything looks normal today.";
export const ROLLUP_QUIET = "Quiet so far for {names}.";
export const ROLLUP_SUB_EVENING = "Next note this evening.";
export const ROLLUP_SUB_MORNING = "Next note in the morning.";
/** The footer, rendered only when every parent is normal; the first sentence
 *  carries the weight (bold at render, per the mockup). */
export const TODAY_FOOT_STRONG = "Nothing needs you today.";
export const TODAY_FOOT_REST = "Kettle will write if that changes.";

/** Relative time leads everywhere — "heard from", never "checked in". */
export const HEARD_MOMENTS = "Heard from moments ago";
export const HEARD_MINUTES = "Heard from {n} minutes ago";
export const HEARD_HOUR = "Heard from 1 hour ago";
export const HEARD_HOURS = "Heard from {n} hours ago";
export const HEARD_DAY = "Heard from 1 day ago";
export const HEARD_DAYS = "Heard from {n} days ago";
/** Beyond the 14-day window the DECISIONS 166 wording stands (spec 009 §2). */
export const META_HEARD_DAYS = "Last heard from {days} days ago.";
export const META_NOTHING_YET = "Nothing has reached Kettle yet.";
/** The unreachable duration (spec 009 §1): "in", never "since ... ago". */
export const META_NOTHING_IN_DAY = "Nothing has reached Kettle in 1 day.";
export const META_NOTHING_IN_DAYS = "Nothing has reached Kettle in {n} days.";

/** The card's second name line, and the small dual-clock line. */
export const CITY_NOW = "{city} · {time} there now";
export const TIME_BY_CLOCK = "{time} {clock}";
export const DUAL_CITY = "{ptime} in {city} · {vtime} your time";
export const DUAL_CLOCK = "{ptime} {clock} · {vtime} your time";

export const CALL_LABEL = "Call {name} ↗";
export const VIEW_DAY_LABEL = "View {name}'s day →";

/** The clock difference, in words — the hero sub's closing clause and the
 *  Family list's sub-line. Vague beats wrong: a shape the word list cannot
 *  carry falls back to the plain sentence. */
export const TZ_SAME = "The same time as yours.";
export const TZ_AHEAD = "{words} ahead of you.";
export const TZ_BEHIND = "{words} behind you.";
export const TZ_DIFFERENT = "A different clock from yours.";

/* ---------------------------------------------------------------------- */
/* Parent detail (spec 009 §3)                                              */
/* ---------------------------------------------------------------------- */

export const DAY_TITLE = "The day";
/** The day's three parts, in order. Names only — never counts. */
export const DAY_PARTS = ["Morning", "Afternoon", "Evening"] as const;
export const ARC_HEARD = "Heard from {time}";
export const ARC_QUIET = "Quiet";
/** FLAGGED (DECISIONS): the spec captions past-with-none "Quiet" and future
 *  "Still ahead" but is silent on the CURRENT segment with none. "Quiet" on
 *  unfinished time would be a verdict (the standing spec-008 rule), so the
 *  stretch being stood in keeps the floor's hedged form. PM may veto. */
export const ARC_QUIET_SO_FAR = "Quiet so far";
export const ARC_AHEAD = "Still ahead";

export const RECENT_TITLE = "Recent days";
export const LEGEND_NORMAL = "A normal day";
export const LEGEND_QUIET = "A quiet start";
export const LEGEND_UNHEARD = "Couldn't hear";

export const MEANS_NORMAL_HEAD = "No action needed.";
export const MEANS_NORMAL_BODY =
  "{name}'s day looks like most days. Kettle will write if that changes.";
export const MEANS_QUIET_HEAD = "Nothing to do yet.";
export const MEANS_QUIET_BODY =
  "Kettle will check in with {name} first if the quiet continues.";
export const MEANS_UNREACHABLE_HEAD = "Worth a look.";

/**
 * The fix card (DECISIONS 172's body, verbatim and pinned product-side). The
 * mockup splits it at the sentence boundary — head, then body — which the
 * screen does at render so the constant stays one source of truth.
 */
export const FIX_BODY =
  "Something on {name}'s phone may need a quick fix. It's a two-minute FaceTime.";
export const FIX_STEPS_LABEL = "See the simple steps →";

/* ---------------------------------------------------------------------- */
/* Family notes (spec 009 §4)                                               */
/* ---------------------------------------------------------------------- */

export const NOTES_TITLE = "Family notes";
export const NOTES_SUB = "The family's memory. Everyone in the family can read and add.";
export const UPCOMING_LABEL = "Upcoming";
/** "Upcoming · {first line} on {Weekday, Mon D} · added by {author}" is
 *  assembled from these at render, middot-joined. */
export const UPCOMING_ON = "{first} on {date}";
export const ADDED_BY = "added by {author}";
/** A past event date rides in the entry metadata: "for Aug 20". */
export const EVENT_FOR = "for {date}";
export const NOTE_PLACEHOLDER = "Add a note for the family…";
export const DATE_CHIP_LABEL = "+ date";
export const SIGNED_AS_LABEL = "Signed as";
/** An empty author renders as the family itself, and the null parent tag
 *  renders under the same word. */
export const AUTHOR_FALLBACK = "Family";
/** FLAGGED (DECISIONS): the spec names no submit control; a keyboard-only
 *  Enter submit fails the accessibility law, so the composer carries the
 *  smallest possible button. PM may reword. */
export const NOTE_SUBMIT_LABEL = "Add";
/** FLAGGED (DECISIONS): the Family screen's tag picker (Mom / Dad / Family)
 *  needs an accessible name the spec does not provide. */
export const NOTE_TAG_LABEL = "Who this note is about";

/* Spec 016 §5, VERBATIM (DECISIONS 274): replies on a note. */
export const REPLY_LINK = "Reply";
export const REPLY_PLACEHOLDER = "Add to this note";
export const REPLY_SUBMIT = "Add";
export const REPLY_CANCEL = "Not now";
/** Reserved by §5, not shown in v1. */
export const REPLY_COUNT_ONE = "1 reply";

/* Spec 018 §5, VERBATIM (DECISIONS 280): edit, delete, the composer. */
export const EDIT_LINK = "Edit";
export const DELETE_LINK = "Delete";
export const SAVE = "Save";
export const EDIT_CANCEL = "Not now";
export const DELETE_NOTE_CONFIRM = "Delete this note? Its replies go with it.";
export const DELETE_REPLY_CONFIRM = "Delete this reply?";
export const DELETE_CONFIRM_YES = "Delete";
export const DELETE_CANCEL = "Keep it";
export const EDITED_MARK = "edited";
export const COMPOSER_FAILED = "That didn't save. Try again.";

/* ---------------------------------------------------------------------- */
/* City label (spec 009 §5)                                                 */
/* ---------------------------------------------------------------------- */

export const CITY_FIELD_LABEL = "City";
export const CITY_MAX_CHARS = 40;
/** Spec 010 §1, verbatim: the picker's placeholder and its quiet escape
 *  hatch. No raw timezone name is ever shown anywhere. */
export const CITY_PLACEHOLDER = "Where {name} lives";
export const CITY_ESCAPE_HATCH = "Can't find it? Pick the nearest big city.";
/** Spec 010 §4 (ruled BUILD): the journal remembers the move, authored by
 *  the product itself. */
export const AUTO_NOTE_AUTHOR = "Kettle";

/* Spec 012 (DECISIONS 200), each ruled verbatim. */
export const MEMORY_TITLE = "Memory";
export const MEMORY_EMPTY =
  "Notes from your family and from Kettle live here. The first ones arrive on their own.";
export const CONTACTS_TITLE = "If you can't reach them";
/* The four suggested rows (spec 012 par.4), offered as PLACEHOLDERS in empty
   label fields, never pre-inserted: the family owns every line. Wording is
   derived from the spec's own list and FLAGGED - the spec names the rows, not
   the strings. */
export const CONTACT_SUGGESTED_LABELS = [
  "A neighbor",
  "Someone in the family nearby",
  "Their building or front desk",
  "Their doctor",
] as const;
/* Contacts chrome, spec-silent and FLAGGED. */
export const CONTACT_ADD_LABEL = "Add a contact";
export const CONTACT_SAVE_LABEL = "Save";
export const CONTACT_REMOVE_LABEL = "Remove";
export const CONTACT_EDIT_LABEL = "Edit";
export const CONTACT_NAME_PLACEHOLDER = "Name";
export const CONTACT_PHONE_PLACEHOLDER = "Phone number";
export const CONTACT_NOTE_PLACEHOLDER = "Anything worth knowing";
export const CITY_CHANGED_NOTE = "{name}'s city changed to {city}.";

/* ---------------------------------------------------------------------- */
/* Chrome                                                                   */
/* ---------------------------------------------------------------------- */

export const TODAY_TITLE = "Today";
export const FAMILY_TITLE = "Family";
export const FAMILY_SUB =
  "Everyone here sees the same Today screen and gets the same notes.";
export const PARENTS_LABEL = "Parents";
/* Spec 015 §9, VERBATIM (DECISIONS 269): the circle. Role words are nouns a
   sibling already knows; "owner" and "seat" never render. */
export const CIRCLE_SECTION = "Family circle";
export const CIRCLE_ROLE_ADMIN = "Admin";
export const CIRCLE_ROLE_MEMBER = "Member";
export const CIRCLE_PENDING = "Not signed in yet";
export const CIRCLE_ADD = "Add someone";
export const CIRCLE_ADD_NAME = "Their name";
export const CIRCLE_ADD_EMAIL = "Their email";
export const CIRCLE_ADD_SUBMIT = "Add";
export const CIRCLE_ADDED = "Kettle will let them in when they sign in with this email.";
export const CIRCLE_MAKE_ADMIN = "Make admin";
export const CIRCLE_MAKE_MEMBER = "Make member";
export const CIRCLE_REMOVE = "Remove";
export const CIRCLE_REMOVE_CONFIRM = "Remove them from the circle? They will not be told.";
export const CIRCLE_LAST_ADMIN = "Make someone else an admin first.";
export const CIRCLE_FULL = "This circle has eight people, which is the most for now.";
export const CIRCLE_MAIL_SWITCH = "Kettle emails me";
export const CIRCLE_NO_MAIL = "No one in the circle is getting Kettle's notes.";
export const CIRCLE_SWITCHER_LABEL = "Looking at";
export const CIRCLE_LEAVE = "Leave this circle";
/* FLAGGED (DECISIONS): §9 names no string for a duplicate email, which
   app_add_seat refuses. Spec-silent, PM may reword. */
export const CIRCLE_DUPLICATE = "Someone in the circle already uses that email.";
/* FLAGGED (DECISIONS): the confirm line's two buttons. §9 gives the line and
   no buttons; "Remove" reuses CIRCLE_REMOVE, the other is spec-silent. */
export const CIRCLE_KEEP = "Keep them";
export const CIRCLE_ADD_CANCEL = "Not now";
export const TAGLINE = "For checking in, not checking up.";
export const BACK_TO_TODAY = "Today";
/** DECISIONS 172's veto: the empty state says only what is true about setup. */
export const EMPTY_TODAY = "No one is set up yet.";

/**
 * Whose clock the fallback time lines carry. A gendered form is used only
 * when a pronoun has actually been recorded — nothing is ever inferred from a
 * name (items 24/34, adopted as policy). With none recorded the parent's own
 * name carries it.
 */
export const CLOCK_BY_PRONOUN: Record<string, string> = {
  she: "her time",
  he: "his time",
  they: "their time",
};
export const CLOCK_BY_NAME = "{name}'s time";

/**
 * Login (DECISIONS 115). The mailer is equipment, so its failures are worded
 * like equipment — calm, specific, and with the next step in the sentence.
 */
/* Spec 013 §3, VERBATIM. The button asks for a CODE now: on a phone the link
   opens inside the mail app's browser rather than the installed Kettle app, so
   the session lands somewhere the family never sees. A code has no context to
   get wrong — they read it in Mail and type it here. The link still rides in
   the same email for laptops, where it is one tap. */
export const LOGIN_BUTTON = "Email me a code";
export const LOGIN_SENT =
  "Check your email for a 6-digit code and type it below. It can take a minute. Look in spam if it hasn't arrived.";
export const LOGIN_CODE_LABEL = "6-digit code";
export const LOGIN_CODE_BUTTON = "Sign in";
export const LOGIN_CODE_RESEND = "Send a new code";
/* Distinct from LOGIN_FAILED on purpose (DECISIONS 115): a mistyped digit and
   a dead mailer are different problems with different next steps, and one
   sentence for both teaches a family to retry the thing that cannot work. */
export const LOGIN_CODE_WRONG =
  "That code didn't match, or it has expired. Check the newest email, or ask for a new code.";
export const LOGIN_RATE_LIMITED =
  "That's a few codes in a row, and the mailer needs a short break. Wait a few minutes, then try once more.";
export const LOGIN_FAILED = "That didn't go through. Check the address and try again.";

/**
 * The setup card (spec 005b §4.1) — the Family screen's forwarding surface.
 * The only app name on it is the one the PM exempted by ruling (DECISIONS
 * 122): `SETUP_SEND_LABEL`, and that key alone.
 */
export const SETUP_TITLE = "Setup";
export const SETUP_READY = "Ready to send";
export const SETUP_REPORTING = "Set up and reporting";
export const SETUP_NEEDS_LINK = "Needs a fresh link";

/* Spec 017 §6, VERBATIM (DECISIONS 274): pause Kettle for one parent. */
export const PAUSE_LINK = "Pause Kettle";
export const PAUSE_WEEK = "For a week";
export const PAUSE_OPEN = "Until I turn it back on";
export const PAUSE_CANCEL = "Not now";
export const PAUSED_CARD = "Kettle is paused for {name}.";
export const PAUSED_UNTIL = "Back on {date}.";
export const PAUSED_OPEN_ENDED = "Until someone turns it back on.";
export const RESUME_BUTTON = "Turn Kettle back on";
export const PAUSED_SETUP = "Paused";
/** The digest's line lives product-side (outbound_templates); named here
 *  only so the copy-law walk and the spec read the same words. */
export const PAUSED_DIGEST = "Kettle is paused for {name}. Nothing to report.";
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

/** The relative last-heard line (spec 009 §2), bucket by bucket. Day words
 *  and no finer beyond the hours — and past the 14-day window the DECISIONS
 *  166 form takes over so the sentence stays honest at any age. */
export function renderHeard(msAgo: number, windowDays: number = 14): string {
  const minutes = Math.floor(msAgo / 60_000);
  if (minutes < 2) return HEARD_MOMENTS;
  if (minutes < 60) return HEARD_MINUTES.replace("{n}", String(minutes));
  const hours = Math.floor(minutes / 60);
  if (hours < 2) return HEARD_HOUR;
  if (hours < 24) return HEARD_HOURS.replace("{n}", String(hours));
  const days = Math.floor(hours / 24);
  if (days > windowDays) return META_HEARD_DAYS.replace("{days}", String(days));
  if (days < 2) return HEARD_DAY;
  return HEARD_DAYS.replace("{n}", String(days));
}

export function renderNothingIn(days: number): string {
  if (days < 2) return META_NOTHING_IN_DAY;
  return META_NOTHING_IN_DAYS.replace("{n}", String(days));
}

export function renderFixBody(name: string): string {
  return FIX_BODY.replace("{name}", name);
}

/* Spec 012 §9 (Memory v1.1). */

/* The fourth tab's label, ruled VERBATIM by DECISIONS 211. The PAGE keeps the
   DECISIONS-200 heading CONTACTS_TITLE above; the tab is the short name in the
   rail, and the two are deliberately different strings for different jobs. */
export const WHO_TO_CALL_TAB = "Who to call";

/* The notes filters (§9.1). The four timeframes are the spec's own words; the
   two numeric ones are the ONLY digits this app prints outside a date or a
   clock, and they are exempted by name in the copy scan rather than by
   widening the rule. FLAGGED in DECISIONS 214: spelling them ("Three months")
   would need no exemption, and is a one-line change if the PM prefers it. */
export const FILTER_ALL_PARENTS = "All";
export const TIMEFRAME_THIS_MONTH = "This month";
export const TIMEFRAME_3_MONTHS = "3 months";
export const TIMEFRAME_6_MONTHS = "6 months";
export const TIMEFRAME_ALL = "All";

/* Accessible names for the two chip groups. Spec-silent and FLAGGED: the spec
   names the filters, not the labels that introduce them. */
export const FILTER_PARENT_LABEL = "Show notes about";
export const FILTER_TIME_LABEL = "Show notes from";

/* Shown when a filter is narrow enough to hide everything (§9.1 does not name
   this case, so it is FLAGGED): the feed must not look broken or empty-by-
   nature when the family has simply filtered past its own notes. */
export const FILTER_EMPTY = "Nothing in this stretch. Try a longer one.";

/* The contacts tab's own filter (§9.3 iii) and the per-contact tag, spec-silent
   and FLAGGED. "Everyone" rather than "All" because a contact tagged to no
   parent is for the whole household, which is a different idea from an
   unfiltered list. */
export const CONTACT_TAG_LABEL = "Who this is for";
export const CONTACT_TAG_EVERYONE = "Everyone";
export const CONTACT_MOVE_UP = "Move up";
export const CONTACT_MOVE_DOWN = "Move down";
