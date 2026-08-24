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
export const HERO_NO_DEVICE_BODY =
  "Nothing new to wear, charge, or install in their home.";
export const HERO_CTA = "Apply for the family beta";
/*
 * The hero image. The diptych's two photographs are one drawing now (founder
 * decision, DECISIONS 136): the artwork carries both rooms *and* the gap
 * between them, so the frame that used to be a two-column grid is a single
 * wide illustration. The brief's law survives the change of medium — parent
 * on the left, profiles facing inward, the distance doing the work no drawn
 * connection line is allowed to do — and the alt text still describes agency,
 * never waiting or worry. PM-drafted, verbatim.
 */
export const HERO_ALT =
  "Two rooms in one drawing: a mother at her suburban kitchen window in morning light, her "
  + "daughter at a city window at dusk, each holding a mug, facing each other across the space "
  + "between.";

/* ---------------------------------------------------------------------- */
/* Scenario tabs                                                            */
/* ---------------------------------------------------------------------- */

export const SCENARIOS_H2 = "An ordinary day.";

/*
 * Each scenario is one lead sentence, whole. It used to be split at the last
 * phrase so the serif could carry the ending; DECISIONS 135 retired that role
 * and the two halves are one string again. The spec's drafted sentences are
 * still intact word for word — the element boundary that used to fall inside
 * them (DECISIONS 79) is simply gone.
 */

export const MORNING_TAB = "Her morning";
export const MORNING_H3 = "A morning like any other.";
export const MORNING_LEAD =
  "By the time her coffee went cold she'd called her sister, read the news, and lost "
  + "an argument with the crossword.";
export const MORNING_BODY = "Her phone did its ordinary things. That's all Kettle ever needs.";
export const MORNING_ALT =
  "A silver-haired woman does the crossword at a sunny kitchen table, coffee in hand, her phone "
  + "lying ignored at the table's edge.";

export const AFTERNOON_TAB = "Her afternoon";
export const AFTERNOON_H3 = "Quiet is allowed.";
export const AFTERNOON_LEAD =
  "Kettle knows the shape of her whole day, so a quiet afternoon reads as exactly that.";
export const AFTERNOON_BODY = "A nap is not a signal.";
export const AFTERNOON_ALT =
  "The same woman asleep in an armchair in soft afternoon light, a paperback open on the chair's "
  + "arm, tea cooling on the side table.";

export const OFF_TAB = "When something's off";
export const OFF_H3 = "She hears from Kettle first.";
export const OFF_LEAD =
  "When the morning doesn't look like her morning, Kettle asks her first, quietly.";
export const OFF_BODY = "Only if she doesn't answer does anyone else hear a thing.";
export const OFF_ALT =
  "The same kitchen, bright and tidy but empty: the crossword untouched, the chair pushed back, "
  + "her phone on the table showing one small amber glow.";
/** Addressed *to* her, and a question rather than a claim — the one reason this
 *  string is on the pinned allowlist rather than banned. */
export const OFF_NOTIF = "Everything okay today? Reply whenever suits.";

export const SEEN_TAB = "What you see";
export const SEEN_H3 = "Reassurance, twice a day.";
export const SEEN_LEAD =
  "Two short messages a day, and a phrase when there's something worth saying.";
export const SEEN_BODY = "Never a feed, never a score, never a graph.";
export const SEEN_ALT =
  "Her daughter curled on a city sofa in lamplight, glancing at her phone with a quiet, relieved "
  + "smile.";
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
export const STORY_TWO_LEAD = "The gentle idea was to notice the ordinary, and say so.";
export const STORY_TWO_BODY = "Kettle does the same with the phone your parents already own.";
export const STORY_THREE_BODY =
  "Nothing to install in their home. Nothing to wear, nothing to charge, nothing to learn.";

/* ---------------------------------------------------------------------- */
/* The three fields                                                         */
/* ---------------------------------------------------------------------- */

export const FIELDS_H2 = "Three fields. Nothing else.";
/** The chips, and the literal truth of the schema. AC3 plants a drifted claim. */
export const FIELDS_CHIPS = ["who", "signal", "when"] as const;
/** The page's one emphasis line, and the shape the law now allows: a whole
 *  sentence, carried by weight in the body face — never an italic fragment
 *  inside someone else's sentence (DECISIONS 135). */
export const FIELDS_EMPHASIS = "What isn't collected can't leak.";
export const FIELDS_BODY =
  "This is the whole record Kettle keeps. Not what she typed. Not who she called. Not where she went.";

/* ---------------------------------------------------------------------- */
/* How it works                                                             */
/* ---------------------------------------------------------------------- */

export const HOW_H2 = "How Kettle works.";
/** The narrative strip that opens the section (DECISIONS 136). It is
 *  decorative — it restates the ladder in pictures and adds no claim the steps
 *  below do not already make — so it carries no copy of its own beyond this
 *  alt text. PM-drafted, verbatim. */
export const HOW_STRIP_ALT =
  "Four drawn panels: her ordinary morning, her daughter at ease in the city, a morning that has "
  + "not started marked by an amber glow on her phone, and the mother replying as the day resumes.";

export const STEP_ONE_LABEL = "Set up together on one video call.";
/** What, never how (DECISIONS 132): public surfaces describe what is
 *  collected, never the mechanism — so this sentence names no tooling. */
export const STEP_ONE_BODY =
  "Kettle notices her phone's ordinary moments. She approves every part of the setup, and can switch any of it off herself.";

export const STEP_TWO_LABEL = "Kettle watches for the absence of normal.";
export const STEP_TWO_BODY =
  "No content, no location, no listening. The only thing observed is that routine happened at all.";

export const STEP_THREE_LABEL = "You hear twice a day. She's asked first.";
export const STEP_THREE_BODY =
  "Quiet reassurance, morning and evening. If the day looks unusual, the first message goes to her, not about her.";

/* ---------------------------------------------------------------------- */
/* Founding families (beta conversion, DECISIONS 129)                       */
/* ---------------------------------------------------------------------- */

/*
 * Four promises, and only promises that will be kept: personal setup, direct
 * support, the founding price, a few short conversations. Nothing here about
 * outcomes, timelines, or features — a beta pitch that promises the roadmap
 * is borrowing from families it has not met yet.
 */
export const FOUNDING_H2 = "What founding families get.";
export const FOUNDING_SETUP_BODY =
  "Personal setup with the founder, together on one call.";
export const FOUNDING_SUPPORT_BODY =
  "Direct support during the beta, from a person you have already met.";
export const FOUNDING_PRICE_BODY =
  "The founding price, honoured for as long as you stay subscribed.";
export const FOUNDING_FEEDBACK_BODY =
  "A few short feedback conversations, so Kettle grows around real families.";

/** The founder's note, final and verbatim (DECISIONS 132; the STUB name
 *  retired with the stub). Six paragraphs in the founder's own words, with
 *  the one PM substitution the copy law required already applied ("Once in a
 *  while" — the page-wide urgency scan owns the word it replaced). It renders
 *  as paragraphs; the copy-law ban scan and the prerender contract both walk
 *  this array element by element, so the letter is covered like any sentence,
 *  while the AC12 shape rules stay what they are: rules for layout copy, not
 *  letters. */
export const FOUNDER_NAME_LABEL = "Hema, founder";
export const FOUNDER_WHY_BODY = [
  "I moved away from my parents twenty-five years ago. Somewhere between time zones, kids, and "
    + "work, my check-ins with them went from frequent to occasional. The calls that did "
    + "happen became tactical: How are you? How's work? How are the kids? Okay, good. "
    + "Talk soon.",
  "What was left was a kind of guilt that wasn't dramatic, just a quiet thought in the "
    + "back of my mind that never really went away. Once in a while, something small "
    + "would bring it to the surface: a movie, a story, a moment that made me think "
    + "about my parents getting older. And underneath it was a simple worry: how do I "
    + "know they're okay without making them feel watched?",
  "I built Kettle because I wanted something smaller and kinder than a worried phone "
    + "call. Something that didn't ask my parents to wear anything, charge anything, "
    + "press a button, or change how they live.",
  "Kettle simply notices that their ordinary day happened, and asks them first when it "
    + "doesn't.",
  "My mother and father were the first two people on it, and they are on it still. My "
    + "mother will happily use almost anything I set up for her. My father is a "
    + "privacy-minded attorney who questions every permission. Designing something that "
    + "felt right to both of them became the standard for Kettle.",
  "If your family joins the beta, I'll set you up personally, the same way I set up "
    + "mine.",
] as const;
export const FOUNDER_CONTACT_LABEL = "Write to Hema";

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
export const WAITLIST_CTA = "See if Kettle fits my family";
/** Under the button, answering the hesitation the button creates. */
export const WAITLIST_REASSURE_BODY = "A short conversation. No commitment.";
/** The one optional free-text field (DECISIONS 129): a kindness, not a gate. */
export const WAITLIST_HELP_LABEL = "What would you most like Kettle to help with?";
/** Mirrored in `kettle/waitlist.py`: with JavaScript off the browser shows the
 *  API's response directly, and both paths must say the same words (item 47). */
export const WAITLIST_SUCCESS = "You're on the list.";
export const WAITLIST_ERROR = "That didn't go through. Check the address and try again.";

/* ---------------------------------------------------------------------- */
/* Footer                                                                   */
/* ---------------------------------------------------------------------- */

export const FOOTER_WORDMARK = "Kettle";
export const FOOTER_LINE = "Three fields. Nothing else.";
/**
 * DECISIONS 171: "HeyKettle" is the formal public name and LINKABIT AI LABS
 * LLC the operating entity — the evidence line Meta asked to see. It says who
 * operates the service and nothing about how it works. The entity name is the
 * copy-law scan's one legal-name exemption, pinned by literal in
 * copyLaw.test.tsx; "AI" here is a registered name, not a product claim, and
 * the inference ban stands everywhere else.
 */
export const FOOTER_LEGAL_LINE = "HeyKettle · a LINKABIT AI LABS LLC service";
export const FOOTER_PRIVACY_LABEL = "Privacy";
export const FOOTER_CONTACT_LABEL = "Say hello";
export const FOOTER_CONTACT_HREF = "mailto:hello@heykettle.com";

/* ---------------------------------------------------------------------- */
/* Privacy                                                                  */
/* ---------------------------------------------------------------------- */

/*
 * The real policy shipped (DECISIONS 132), so the placeholder's "being
 * written with counsel" sentence retired with the placeholder. These two
 * constants tie this module to the standalone page: check-prerender requires
 * both to appear verbatim in privacy.html, so the page and the promise it
 * summarises cannot drift apart.
 */
export const PRIVACY_H1 = "Privacy";
export const PRIVACY_BODY =
  "Kettle stores three things about your parent: who, which routine, when.";

/* ---------------------------------------------------------------------- */
/* Chrome                                                                   */
/* ---------------------------------------------------------------------- */

/** DECISIONS 171: the formal name in the tab; the wordmark stays "Kettle". */
export const PAGE_TITLE_LABEL = "HeyKettle — Know the day started normally.";
export const NOTIF_TIMESTAMP_LABEL = "Today";
export const NOTIF_APP_LABEL = "Kettle";
