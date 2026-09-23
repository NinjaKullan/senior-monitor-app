/**
 * The site's copy-law ban lists, in one place (moved out of copyLaw.test.tsx
 * unchanged for spec 021's /care page, DECISIONS 344). A second page scanned
 * against its own copy of these lists would drift from the first the day
 * someone widened one of them; importing them is the only way both pages
 * stay under one law. Not a test file: vitest collects `*.test.*` only.
 */

/* --------------------------------------------------------------------- */
/* The bans                                                               */
/* --------------------------------------------------------------------- */

/** No urgency vocabulary, ever (design-language §8). */
export const URGENCY = [
  "now", "hurry", "don't miss", "limited", "last chance", "act fast",
  "today only", "instantly", "immediately", "before it's too late",
];

/** Law #1 reaches marketing with less licence, not more. */
export const DIAGNOSIS = [
  "dementia", "decline", "declining", "deteriorate", "deteriorating",
  "deterioration", "symptom", "symptoms", "health score", "cognitive",
  "diagnosis", "condition",
];

/** Nothing on this page describes a person's body. */
export const MEDICAL = [
  "unwell", "ill", "hospital", "fallen", "injured", "collapse", "frail", "at risk",
];

/** The ladder asks and is heard. It never alerts. */
export const ALARM = ["alert", "alerts", "alarm", "emergency", "sos", "urgent", "panic", "crisis"];

/** What this product is not, said in the words people use for it. */
export const SURVEILLANCE = ["track", "tracking", "tracked", "surveillance", "monitor her", "watch her", "spy"];

/** Verdicts about a person's state, as assertions. */
export const VERDICTS = ["she's fine", "she is fine", "is safe", "doing well", "she's okay", "she is okay"];

/**
 * Inference vocabulary (founder decision, DECISIONS 129). Law #1 rules out
 * decline detection; this bans the site from *sounding* like it does it.
 * Kettle notices absence against a fixed expectation — it does not learn, and
 * a page that says "learns her routine" has promised a model that product law
 * forbids building. "learn" in the plain sense stays free ("nothing to
 * learn"); the machine-flavoured forms do not. Exactly these four words — a
 * dotted "a.i." entry was tried and dropped: the unescaped dots turned the
 * word-bounded scan into a wildcard that banned "amid" and "axis".
 */
export const INFERENCE = ["learns", "learning", "intelligence", "ai"];

/**
 * Mechanism vocabulary (founder IP ruling, DECISIONS 132, standing): public
 * surfaces describe what is collected, never how. No tooling names, no
 * automation vocabulary, no named infrastructure — providers are "established
 * cloud infrastructure providers", named on request. Mechanism transparency
 * for joined families lives on the setup surface behind expiring links.
 * Dots in entries are escaped by the scan (the "a.i." lesson).
 */
export const MECHANISM = [
  "shortcut", "shortcuts", "automation", "automations", "supabase", "postgres",
  "postgresql", "fly.io", "fly.dev", "aws", "vercel", "netlify", "postmark",
  "resend", "twilio", "ntfy",
];

/**
 * Romanized kinship terms and culture-coded vocabulary (Amendment A).
 *
 * The audience is English-fluent and broader than any one culture, so a word a
 * reader cannot parse costs more than it earns — the photography carries the
 * specificity instead. Case-insensitive, like every ban here, because the scan
 * lowercases first.
 *
 * `beta` is deliberately absent. It is a kinship term in several languages and
 * also the word this product will one day use for its own beta, and a ban that
 * fights the roadmap is a ban someone deletes.
 */
export const CULTURE_CODED = ["amma", "appa", "chai", "paati", "thatha", "nani", "dadi", "ajji"];

/** App and platform names. Permitted in §3.4's mechanism copy and nowhere else. */
export const APP_NAMES = ["whatsapp", "facetime", "shortcuts", "youtube", "instagram"];

export const BANNED = [
  ...URGENCY,
  ...DIAGNOSIS,
  ...MEDICAL,
  ...ALARM,
  ...SURVEILLANCE,
  ...VERDICTS,
  ...INFERENCE,
  ...MECHANISM,
];
