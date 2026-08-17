/**
 * Every rendered string on the landing page.
 *
 * One file, like the webapp's, for the same reason: the copy law is a test, and
 * a test needs somewhere to look. `src/tests/copyLaw.test.tsx` runs the marketing
 * bans over this module *and* over the rendered DOM, so a string that never
 * passes through here still gets caught — but a string that lives here gets
 * caught before it is ever wired up.
 *
 * **Role suffixes are load-bearing.** Every export ends in one, and the shape
 * test (AC12) uses them: `_H1` ≤7 words, `_H2` 3–5 words, `_BODY` ≤23 words. An
 * export with no recognised suffix fails rather than escaping the scan — the
 * same classify-or-fail structure the glance floor has carried since item 57,
 * because that is how a rule quietly stops applying.
 *
 * **Universal English** (Amendment A, founder site review): no romanized kinship
 * terms and no culture-coded vocabulary anywhere on this surface. The audience is
 * English-fluent and broader than any one culture; a word a reader cannot parse
 * costs more than it earns, and the photography carries the specificity instead.
 * `CULTURE_CODED` in the copy-law test enforces it with no allowlist at all —
 * unlike every other ban here, this one cannot be exempted.
 *
 * **The personas balance.** The scenarios follow one vivid parent because a day
 * needs a person in it; the page as a whole shows both, so the hero speaks of
 * parents, plural, and the sample digest names Dad. That asymmetry is deliberate
 * and is asserted — it is not a mismatch waiting to be tidied up.
 *
 * The strings themselves are the founder's shipping drafts and are swappable at
 * review. The rules around them are not.
 */

/* ---------------------------------------------------------------------- */
/* Hero                                                                     */
/* ---------------------------------------------------------------------- */

export const HERO_EYEBROW = "For families far away";
export const HERO_H1 = "Know the day started normally.";
export const HERO_BODY =
  "Kettle notices when your parents' ordinary routine doesn't happen, and asks them first, before anyone worries.";
/** The second half of the sub block. The objection this page answers before it
 *  is raised: nothing arrives, nothing is worn, nothing new has to be learned. */
export const HERO_NO_DEVICE_BODY = "No new devices. Only the phone they already have.";
export const HERO_CTA = "Join waitlist";
/*
 * The hero diptych (docs/hero-diptych-brief.md): parent left, adult child
 * right, profiles facing inward, each in their own light and their own city.
 * The photographs carry the distance; the alt text describes agency, never
 * waiting or worry.
 */
export const HERO_MORNING_ALT =
  "An older man at his kitchen window in first light, coffee in hand, a kettle on the counter.";
export const HERO_EVENING_ALT =
  "A woman at her apartment window in another city, tea in hand, the evening lights coming on.";

/* ---------------------------------------------------------------------- */
/* Scenario tabs                                                            */
/* ---------------------------------------------------------------------- */

export const SCENARIOS_H2 = "An ordinary day.";

/*
 * Each scenario is a sans lead sentence with the serif carrying its last phrase
 * — design-language §3's "italic phrase inside a sans sentence", which is the
 * only shape the serif is permitted in. The spec's drafted sentences are intact
 * word for word; only the element boundary falls inside them (QUESTIONS 79).
 */

export const MORNING_TAB = "Her morning";
export const MORNING_EYEBROW = "Her morning";
export const MORNING_LEAD =
  "By the time her coffee went cold she'd called her sister, read the news, and ";
export const MORNING_SERIF = "lost an argument with the crossword.";
export const MORNING_BODY = "Her phone did its ordinary things. That's all Kettle ever needs.";
export const MORNING_ALT =
  "A kitchen table in morning sun, a half-finished crossword, reading glasses, and a cup of coffee.";

export const AFTERNOON_TAB = "Her afternoon";
export const AFTERNOON_EYEBROW = "Her afternoon";
export const AFTERNOON_LEAD = "Kettle knows the shape of her whole day, so ";
export const AFTERNOON_SERIF = "a quiet afternoon reads as exactly that.";
export const AFTERNOON_BODY = "A nap is not a signal.";
export const AFTERNOON_ALT =
  "An armchair by a sunlit curtain, a paperback resting open on its arm, tea on the side table.";

export const OFF_TAB = "When something's off";
export const OFF_EYEBROW = "When something's off";
export const OFF_LEAD = "When the morning doesn't look like her morning, ";
export const OFF_SERIF = "Kettle asks her first, quietly.";
export const OFF_BODY = "Only if she doesn't answer does anyone else hear a thing.";
export const OFF_ALT =
  "A kettle steaming on the counter, a mug of tea beside it, a phone lit with one quiet line.";
/** Addressed *to* her, and a question rather than a claim — the one reason this
 *  string is on the pinned allowlist rather than banned. */
export const OFF_NOTIF = "Everything okay today? Reply whenever suits.";

export const SEEN_TAB = "What you see";
export const SEEN_EYEBROW = "What you see";
export const SEEN_LEAD = "Two short messages a day, and ";
export const SEEN_SERIF = "a phrase when there's something worth saying.";
export const SEEN_BODY = "Never a feed, never a score, never a graph.";
export const SEEN_ALT =
  "A desk at the end of the day, laptop closed, keys set down, a child's drawing on the wall.";
export const SEEN_NOTIF = "Dad's day started normally.";

/* ---------------------------------------------------------------------- */
/* Why the name (Amendment B)                                               */
/* ---------------------------------------------------------------------- */

/*
 * The story stays anonymous by design: a real service inspired it, and
 * marketing does not borrow someone else's trademark to explain its own name.
 *
 * It is also deliberately silent about what happens next. The founder's
 * "before alerting family" framing is not here — `alert` is banned on this
 * surface, and the senior-first mechanism is already the off-panel's copy. A
 * story section that restated it would be selling the ladder twice.
 */
export const STORY_EYEBROW = "Why the name";
export const STORY_H2 = "Named after a kettle.";
export const STORY_ONE_BODY =
  "In Japan, a tea kettle once told faraway families that their parents had started the day as usual.";
export const STORY_TWO_LEAD = "The gentle idea was to ";
export const STORY_TWO_SERIF = "notice the ordinary, and say so.";
export const STORY_TWO_BODY = "Kettle does the same with the phone your parents already own.";
export const STORY_THREE_BODY =
  "Nothing to install in their home. Nothing to wear, nothing to charge, nothing to learn.";

/* ---------------------------------------------------------------------- */
/* The three fields                                                         */
/* ---------------------------------------------------------------------- */

export const FIELDS_H2 = "Three fields. Nothing else.";
/** The chips, and the literal truth of the schema. AC3 plants a drifted claim. */
export const FIELDS_CHIPS = ["who", "signal", "when"] as const;
export const FIELDS_SERIF = "What isn't collected can't leak.";
export const FIELDS_BODY =
  "This is the whole record Kettle keeps. Not what she typed. Not who she called. Not where she went.";

/* ---------------------------------------------------------------------- */
/* How it works                                                             */
/* ---------------------------------------------------------------------- */

export const HOW_H2 = "How Kettle works.";

export const STEP_ONE_LABEL = "Set up together on one video call.";
export const STEP_ONE_BODY =
  "Pre-built shortcuts note her phone's ordinary moments. She approves every one, and can switch any of it off herself.";

export const STEP_TWO_LABEL = "Kettle watches for the absence of normal.";
export const STEP_TWO_BODY =
  "No content, no location, no listening. The only thing observed is that routine happened at all.";

export const STEP_THREE_LABEL = "You hear twice a day. She's asked first.";
export const STEP_THREE_BODY =
  "Quiet reassurance, morning and evening. If the day looks unusual, the first message goes to her, not about her.";

/* ---------------------------------------------------------------------- */
/* Waitlist                                                                 */
/* ---------------------------------------------------------------------- */

export const WAITLIST_H2 = "Join the founding families.";
export const WAITLIST_BODY =
  "The founding rate is $10 a month per loved one, honoured for as long as you stay.";
export const WAITLIST_EMAIL_LABEL = "Your email";
export const WAITLIST_PHONE_LABEL = "What phone does your parent use?";
export const WAITLIST_IPHONE_LABEL = "iPhone";
export const WAITLIST_ANDROID_LABEL = "Android";
export const WAITLIST_UNSURE_LABEL = "Not sure";
export const WAITLIST_CTA = "Request invite";
/** Mirrored in `kettle/waitlist.py`: with JavaScript off the browser shows the
 *  API's response directly, and both paths must say the same words (item 47). */
export const WAITLIST_SUCCESS = "You're on the list.";
export const WAITLIST_ERROR = "That didn't go through. Check the address and try again.";

/* ---------------------------------------------------------------------- */
/* Footer                                                                   */
/* ---------------------------------------------------------------------- */

export const FOOTER_WORDMARK = "Kettle";
export const FOOTER_LINE = "Three fields. Nothing else.";
export const FOOTER_PRIVACY_LABEL = "Privacy";
export const FOOTER_CONTACT_LABEL = "Say hello";
export const FOOTER_CONTACT_HREF = "mailto:hello@getkettle.com";

/* ---------------------------------------------------------------------- */
/* Privacy placeholder                                                      */
/* ---------------------------------------------------------------------- */

export const PRIVACY_H1 = "Privacy";
export const PRIVACY_BODY =
  "Kettle stores three things: who, which routine, when. Nothing else exists to show you.";
export const PRIVACY_PLACEHOLDER_BODY =
  "The full policy is being written with counsel and will appear here before the first family joins.";

/* ---------------------------------------------------------------------- */
/* Chrome                                                                   */
/* ---------------------------------------------------------------------- */

export const PAGE_TITLE_LABEL = "Kettle. Know the day started normally.";
export const NOTIF_TIMESTAMP_LABEL = "Today";
export const NOTIF_APP_LABEL = "Kettle";
