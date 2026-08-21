/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * AC3 / AC4 / AC12 — the copy law, extended to marketing.
 *
 * Design-language §8 asks for the product's existing copy-law tests to reach
 * this surface rather than a second standard being invented for it, and that is
 * the right instinct for a reason worth stating: marketing is where a company
 * says what it is, and a promise made here that the product cannot keep is worse
 * than the same sentence in a digest, because a stranger reads this one *before*
 * deciding to trust anything.
 *
 * So the bans are stricter here, not looser. The ladder is described as asking
 * and hearing, never alerting. Nothing claims a person's state. No app name
 * appears inside a sentence about her day. And the only digits on the page are
 * a price and three step numerals.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "@/App";
import * as copy from "@/copy";
import { OFF_NOTIF, WAITLIST_BODY } from "@/copy";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..");

/* --------------------------------------------------------------------- */
/* The bans                                                               */
/* --------------------------------------------------------------------- */

/** No urgency vocabulary, ever (design-language §8). */
const URGENCY = [
  "now", "hurry", "don't miss", "limited", "last chance", "act fast",
  "today only", "instantly", "immediately", "before it's too late",
];

/** Law #1 reaches marketing with less licence, not more. */
const DIAGNOSIS = [
  "dementia", "decline", "declining", "deteriorate", "deteriorating",
  "deterioration", "symptom", "symptoms", "health score", "cognitive",
  "diagnosis", "condition",
];

/** Nothing on this page describes a person's body. */
const MEDICAL = [
  "unwell", "ill", "hospital", "fallen", "injured", "collapse", "frail", "at risk",
];

/** The ladder asks and is heard. It never alerts. */
const ALARM = ["alert", "alerts", "alarm", "emergency", "sos", "urgent", "panic", "crisis"];

/** What this product is not, said in the words people use for it. */
const SURVEILLANCE = ["track", "tracking", "tracked", "surveillance", "monitor her", "watch her", "spy"];

/** Verdicts about a person's state, as assertions. */
const VERDICTS = ["she's fine", "she is fine", "is safe", "doing well", "she's okay", "she is okay"];

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
const INFERENCE = ["learns", "learning", "intelligence", "ai"];

/**
 * Mechanism vocabulary (founder IP ruling, DECISIONS 132, standing): public
 * surfaces describe what is collected, never how. No tooling names, no
 * automation vocabulary, no named infrastructure — providers are "established
 * cloud infrastructure providers", named on request. Mechanism transparency
 * for joined families lives on the setup surface behind expiring links.
 * Dots in entries are escaped by the scan (the "a.i." lesson).
 */
const MECHANISM = [
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
const CULTURE_CODED = ["amma", "appa", "chai", "paati", "thatha", "nani", "dadi", "ajji"];

/** App and platform names. Permitted in §3.4's mechanism copy and nowhere else. */
const APP_NAMES = ["whatsapp", "facetime", "shortcuts", "youtube", "instagram"];

const BANNED = [
  ...URGENCY,
  ...DIAGNOSIS,
  ...MEDICAL,
  ...ALARM,
  ...SURVEILLANCE,
  ...VERDICTS,
  ...INFERENCE,
  ...MECHANISM,
];

/**
 * The pinned allowlist. Every entry is a literal, written out here rather than
 * derived, so widening it is a visible act in this file — the asymmetry adopted
 * in DECISIONS 62: the ban may derive itself, the exemption may not.
 */
const ALLOW: (string | RegExp)[] = [
  // A question addressed *to her*, not a claim about her. That distinction is
  // the entire senior-first ladder, and it is why this string is exempt from
  // the verdict ban rather than in breach of it.
  OFF_NOTIF,
  // The founding rate: the page's one legitimate number.
  WAITLIST_BODY,
];

/** Digits allowed on the page: the price, and the three step numerals. */
const DIGIT_ALLOW: (string | RegExp)[] = [WAITLIST_BODY, /^[123]$/];

function mask(text: string, allow: (string | RegExp)[]): string {
  let scanned = text;
  for (const entry of allow) {
    scanned =
      typeof entry === "string"
        ? scanned.split(entry).join("«allowed»")
        : scanned.replace(entry, "«allowed»");
  }
  return scanned;
}

/**
 * Ruling 75 at the assertion: the slot labels a section or a scenario, and never
 * a person's condition. The typographic form travels; the semantics do not.
 */
function assertEyebrow(text: string) {
  assertCopyLaw(text);
  expect(
    /attention|stress|risk|concern|watch|mood|energy/i.test(text),
    `person-status eyebrow: ${text}`,
  ).toBe(false);
}

function assertCopyLaw(text: string, allow: (string | RegExp)[] = []) {
  const scanned = mask(text, allow).toLowerCase();
  for (const word of BANNED) {
    expect(
      new RegExp(`\\b${word.replace(/\./g, "\\.").replace(/'/g, "['’]")}\\b`).test(scanned),
      `"${word}" appeared in: ${text}`,
    ).toBe(false);
  }

  // Scanned against the *unmasked* text, unlike every other ban here. Amendment
  // A says "no allowlist entries", and the way to mean that is to make the
  // exemption unreachable rather than merely empty: a future allowlist addition
  // cannot smuggle a kinship term in behind it.
  const raw = text.toLowerCase();
  for (const word of CULTURE_CODED) {
    expect(
      new RegExp(`\\b${word}\\b`).test(raw),
      `culture-coded "${word}" appeared in: ${text}`,
    ).toBe(false);
  }
  // An exclamation mark in a heading or a CTA is urgency wearing punctuation.
  expect(/!/.test(scanned), `an exclamation mark appeared in: ${text}`).toBe(false);
}

/* --------------------------------------------------------------------- */
/* Over the copy module                                                   */
/* --------------------------------------------------------------------- */

const STRINGS = Object.entries(copy).flatMap(([name, value]) =>
  typeof value === "string" ? [[name, value] as const] : [],
);

/**
 * Everything a person can read, including array copy (the founder note's
 * paragraphs, the chips): the ban scans walk this; the AC12 shape rules stay
 * on STRINGS, because they are rules for layout copy, not for a letter.
 */
const ARRAYS = Object.entries(copy).flatMap(([name, value]) =>
  Array.isArray(value) && value.every((v) => typeof v === "string")
    ? value.map((v) => [name, v] as const)
    : [],
);
const PROSE = [...STRINGS, ...ARRAYS];

/** Roles, and the shape rule each carries (AC12). H3 joined with the scenario
 *  panel headlines (beta conversion, DECISIONS 129). SERIF retired and
 *  EMPHASIS replaced it (DECISIONS 135): the page's emphasis is a whole
 *  sentence carried by weight, never an italic fragment, so the role that
 *  named a sentence-fragment no longer exists. */
const ROLE =
  /_(H1|H2|H3|BODY|LEAD|EMPHASIS|TAB|EYEBROW|CTA|LABEL|ALT|NOTIF|CHIP|CHIPS|HREF|SUCCESS|ERROR|WORDMARK|LINE)$/;

const words = (text: string) => text.trim().split(/\s+/).filter(Boolean).length;

describe("AC3 — the copy module obeys the marketing bans", () => {
  it("has something to scan", () => {
    expect(STRINGS.length).toBeGreaterThan(30);
  });

  it("bans urgency, diagnosis, alarm, surveillance, verdicts and mechanism", () => {
    // The STEP_ mechanism exemption retired with DECISIONS 132's what-never-
    // how ruling: the setup steps describe what Kettle notices, not the
    // tooling that notices it, so no string on this surface names either.
    for (const [name, value] of PROSE) {
      expect(() => assertCopyLaw(value, ALLOW), name).not.toThrow();
    }
  });

  it("names no app anywhere on this surface", () => {
    for (const [name, value] of PROSE) {
      for (const app of APP_NAMES) {
        expect(
          new RegExp(`\\b${app}\\b`).test(value.toLowerCase()),
          `${name} narrates her day through an app name: ${value}`,
        ).toBe(false);
      }
    }
  });

  it("would catch each of the planted regressions", () => {
    // AC3 names the first six exactly; the inference pair joined with
    // DECISIONS 129. Each is a sentence someone could plausibly write.
    expect(() => assertCopyLaw("Join now — limited places")).toThrow();
    expect(() => assertCopyLaw("Know she's fine today")).toThrow();
    expect(() => assertCopyLaw("Kettle sends an alert when something is wrong")).toThrow();
    expect(() => assertCopyLaw("Track her daily routine")).toThrow();
    expect(() => assertCopyLaw("Request invite!")).toThrow();
    expect(() => assertCopyLaw("Spot the early symptoms of decline")).toThrow();
    expect(() => assertCopyLaw("Kettle learns her routine over time")).toThrow();
    expect(() => assertCopyLaw("Built with AI, tuned for families")).toThrow();
    // The plain sense stays free: the story's "nothing to learn" is a promise
    // about the parent's effort, not a claim about a model.
    expect(() => assertCopyLaw("Nothing to wear, nothing to learn.")).not.toThrow();
    // What, never how (DECISIONS 132): tooling and infrastructure names fail.
    expect(() => assertCopyLaw("Pre-built shortcuts note her phone's moments")).toThrow();
    expect(() => assertCopyLaw("One automation watches her morning")).toThrow();
    expect(() => assertCopyLaw("Hosted on AWS and Supabase")).toThrow();
    expect(() => assertCopyLaw("Deployed to fly.io")).toThrow();
    // And the plain word survives the dotted entries: escaping, not wildcards.
    expect(() => assertCopyLaw("Days fly by between visits.")).not.toThrow();
  });

  it("carries no romanized kinship term or culture-coded word", () => {
    // The sweep, done by the test rather than by memory — Amendment A says so
    // in those words, because a hand sweep is exactly what misses the one in an
    // alt text nobody rereads.
    for (const [name, value] of PROSE) {
      for (const word of CULTURE_CODED) {
        expect(
          new RegExp(`\\b${word}\\b`).test(value.toLowerCase()),
          `${name} carries "${word}": ${value}`,
        ).toBe(false);
      }
    }
  });

  it("would catch a kinship term in a heading, and cannot be allowlisted past", () => {
    expect(() => assertCopyLaw("Amma's day started normally.")).toThrow();
    expect(() => assertCopyLaw("By the time the chai went cold")).toThrow();
    expect(() => assertCopyLaw("APPA is up early")).toThrow();

    // The exemption is unreachable, not empty: passing the offending string as
    // its own allowlist entry still fails.
    const kin = "Amma's day started normally.";
    expect(() => assertCopyLaw(kin, [kin])).toThrow();
  });

  it("leaves beta alone, so a future beta mention does not fight the ban", () => {
    // A kinship term in several languages, and the word this product will use
    // for its own beta. Amendment A excludes it deliberately.
    expect(CULTURE_CODED).not.toContain("beta");
    expect(() => assertCopyLaw("Join the beta")).not.toThrow();
  });

  it("shows both parents: plural in the hero, Dad in the sample digest", () => {
    // The scenarios follow one parent because a day needs a person in it; the
    // page as a whole balances. Asserted so it is not tidied into a match.
    expect(copy.HERO_BODY).toContain("your parents'");
    expect(copy.HERO_BODY).toContain("asks them first");
    expect(copy.SEEN_NOTIF).toBe("Dad's day started normally.");
  });

  it("exempts the senior-first question without exempting a verdict", () => {
    // The allowlisted string is a question to her.
    expect(() => assertCopyLaw(OFF_NOTIF, ALLOW)).not.toThrow();
    // Its neighbour, a claim about her, is not exempt by association.
    expect(() => assertCopyLaw("Everything okay today? She's fine.", ALLOW)).toThrow();
  });
});

describe("AC12 — copy shape", () => {
  it("classifies every exported string, or fails", () => {
    // The floor-rot guard from item 57: a constant that escapes the scan is how
    // a rule quietly stops applying. Array exports carry a role on the array's
    // own name (…_BODY for the founder note's paragraphs, …_CHIPS).
    const unclassified = PROSE.filter(([name]) => !ROLE.test(name)).map(([name]) => name);
    expect([...new Set(unclassified)], "give these a role suffix").toEqual([]);
  });

  it("keeps H1 to seven words and H2s to three-to-five", () => {
    for (const [name, value] of STRINGS) {
      if (name.endsWith("_H1")) expect(words(value), name).toBeLessThanOrEqual(7);
      if (name.endsWith("_H2")) {
        expect(words(value), name).toBeGreaterThanOrEqual(3);
        expect(words(value), name).toBeLessThanOrEqual(5);
      }
      // Panel headlines: one line, no more room than the H1 gets.
      if (name.endsWith("_H3")) expect(words(value), name).toBeLessThanOrEqual(7);
    }
  });

  it("keeps every paragraph under twenty-three words", () => {
    for (const [name, value] of STRINGS) {
      if (/_(BODY|LEAD|EMPHASIS)$/.test(name)) {
        expect(words(value), `${name} runs long: ${value}`).toBeLessThanOrEqual(23);
      }
    }
  });

  it("keeps CTA labels to six plain words at most", () => {
    // Was two flat words ("Join waitlist"). The beta conversion's approved
    // CTAs are sentences a person would say — "See if Kettle fits my family"
    // — so the cap moves to fit them (founder decision, DECISIONS 129). The
    // flatness the old cap protected lives on in the urgency bans above: a
    // longer label may be warmer, never louder.
    for (const [name, value] of STRINGS) {
      if (name.endsWith("_CTA")) expect(words(value), name).toBeLessThanOrEqual(6);
    }
  });
});

/* --------------------------------------------------------------------- */
/* Over the rendered page                                                 */
/* --------------------------------------------------------------------- */

describe("AC3 — the rendered page obeys them too", () => {
  it("holds for the whole page, alt and aria text included", () => {
    render(<App />);
    const text = document.body.textContent ?? "";
    // Not passing on an empty render.
    expect(text).toContain(copy.HERO_H1);
    expect(text).toContain(copy.FIELDS_H2);

    assertCopyLaw(text, [...ALLOW, /Shortcuts/]);

    // Alt text and accessible names are copy, and are read aloud to exactly the
    // reader least able to skip them.
    for (const node of Array.from(document.querySelectorAll("[aria-label]"))) {
      assertCopyLaw(node.getAttribute("aria-label") ?? "", ALLOW);
    }
    // Photographs arrived with the 2026-08-17 build, so the page now has alt
    // attributes — text that is neither textContent nor aria-label, and that
    // the scans above would walk straight past. An inline alt written beside
    // the markup gets the same law as one from copy.ts.
    const images = Array.from(document.querySelectorAll("img"));
    expect(images.length).toBeGreaterThan(0);
    for (const image of images) {
      expect(image.hasAttribute("alt"), "an image with no alt text").toBe(true);
      assertCopyLaw(image.getAttribute("alt") ?? "", ALLOW);
    }
  });

  it("keeps the three-fields claim identical to the schema", () => {
    render(<App />);
    const chips = screen.getAllByTestId("field-chip").map((n) => n.textContent);
    // who, signal, when — the whole row, and the whole promise.
    expect(chips).toEqual(["who", "signal", "when"]);
    expect(screen.getByTestId("field-chips").textContent).toBe("whosignalwhen");
  });

  it("would catch a three-fields claim that drifted from the schema", () => {
    const drifted = ["who", "signal", "when", "roughly where"];
    expect(drifted).not.toEqual([...copy.FIELDS_CHIPS]);
  });

  it("carries no person-status eyebrow", () => {
    render(<App />);
    const eyebrows = screen.getAllByTestId("eyebrow").map((n) => n.textContent ?? "");
    expect(eyebrows.length).toBeGreaterThan(0);
    for (const eyebrow of eyebrows) assertEyebrow(eyebrow);
  });

  it("would catch a person-status eyebrow", () => {
    // Ruling 75's refused family, in its own words. The plant runs the same
    // assertion the real eyebrows run — a separate looser check here would
    // prove nothing about them.
    expect(() => assertEyebrow("PAY ATTENTION")).toThrow();
    expect(() => assertEyebrow("STRESSFUL DAY")).toThrow();
    expect(() => assertEyebrow("SHE MAY BE UNWELL")).toThrow();
    expect(() => assertEyebrow("HER MORNING")).not.toThrow();
  });
});

/* --------------------------------------------------------------------- */
/* The privacy page (DECISIONS 132)                                        */
/* --------------------------------------------------------------------- */

describe("the privacy page obeys the same law", () => {
  const PRIVACY = join(SRC, "..", "public", "privacy.html");

  function privacyText(): string {
    return readFileSync(PRIVACY, "utf8")
      .replace(/<style>[\s\S]*?<\/style>/g, " ")
      .replace(/<[^>]+>/g, " ")
      .replace(/&ldquo;|&rdquo;/g, '"')
      .replace(/&rsquo;|&lsquo;|&#x27;|&#39;/g, "'")
      .replace(/&amp;/g, "&")
      .replace(/\s+/g, " ");
  }

  it("is the founder's policy, and the placeholder is gone", () => {
    const text = privacyText();
    expect(text).toContain(copy.PRIVACY_H1);
    expect(text).toContain(copy.PRIVACY_BODY);
    expect(text).toContain("Last updated:");
    expect(text).toContain("Back to Kettle");
    expect(text).not.toContain("being written with counsel");
  });

  it("describes what is collected, never how — the full law, one pinned line", () => {
    // The standing IP ruling at its sharpest point: the page a privacy-minded
    // reader studies hardest names no tooling, no automation vocabulary, no
    // infrastructure. It also carries none of the vocabulary banned anywhere
    // else — a policy that says "alert" or "track" has already broken the
    // promise it documents. Two literal exemptions, in the DECISIONS-62 shape
    // (the exemption may never derive itself), and both are the same move:
    // a founder guarantee that uses a banned word to promise its *absence* —
    // deletion is immediate, delivery tracking is off. The words the bans
    // exist to stop are selling and surveilling; these sentences do the
    // opposite, and they are pinned whole so nothing else rides in on them.
    const PRIVACY_ALLOW = [
      "Turning off a parent's setup stops collection immediately.",
      "with delivery tracking turned off.",
    ];
    expect(() => assertCopyLaw(privacyText(), PRIVACY_ALLOW)).not.toThrow();
  });

  it("stands alone: no outbound requests, no scripts", () => {
    const html = readFileSync(PRIVACY, "utf8");
    expect(html).not.toMatch(/<script/i);
    expect(html).not.toMatch(/<link/i);
    expect(html).not.toMatch(/https?:\/\//i);
  });
});

/* --------------------------------------------------------------------- */
/* AC4 — digits                                                            */
/* --------------------------------------------------------------------- */

describe("AC4 — the only digits are a price and three numerals", () => {
  const SVG_NS = "http://www.w3.org/2000/svg";
  /** Attributes a person can actually reach (the item-67 narrowing). */
  const PERCEIVABLE = /^(aria-|data-|role$|title$|alt$)/;

  function digitWalk(root: HTMLElement) {
    // The three step numerals are allowed *as those elements*, not as the
    // digits 1-3 anywhere on the page: masking the characters would quietly
    // permit "3 falls this week". So the elements are removed from the text
    // scan and asserted separately, by content and by count.
    const copyOfRoot = root.cloneNode(true) as HTMLElement;
    for (const numeral of Array.from(copyOfRoot.querySelectorAll('[data-testid="step-number"]'))) {
      numeral.remove();
    }
    const stray = mask(copyOfRoot.textContent ?? "", DIGIT_ALLOW).replace(/[^\d]/g, "");
    expect(stray, `stray digits in the page text: ${stray}`).toBe("");

    for (const node of [root, ...Array.from(root.querySelectorAll("*"))]) {
      const isSvg = node.namespaceURI === SVG_NS;
      for (const attr of Array.from(node.attributes)) {
        if (attr.name === "class" || attr.name === "style") continue;
        if (isSvg && !PERCEIVABLE.test(attr.name)) continue;
        // React's own ids and the tab/panel wiring carry generated suffixes;
        // they are plumbing, not content, and are never read to anyone.
        if (["id", "aria-controls", "aria-labelledby", "for", "tabindex"].includes(attr.name)) {
          continue;
        }
        expect(
          /\d/.test(mask(attr.value, DIGIT_ALLOW)),
          `${attr.name}="${attr.value}" carries a number`,
        ).toBe(false);
      }
    }
  }

  it("passes over the whole rendered page", () => {
    const { container } = render(<App />);
    // The step numerals are present — this is not passing on an empty page.
    expect(screen.getAllByTestId("step-number").map((n) => n.textContent)).toEqual([
      "1",
      "2",
      "3",
    ]);
    digitWalk(container);
  });

  it("shows the word Today, never a clock time, in a notification", () => {
    render(<App />);
    for (const stamp of screen.getAllByTestId("notification-time")) {
      expect(stamp.textContent).toBe("Today");
    }
    expect(document.body.textContent).not.toMatch(/\b\d{1,2}:\d{2}\s?[ap]m\b/i);
  });

  it("would catch a clock time and a count of her activity", () => {
    const plant = (html: string) => {
      const node = document.createElement("div");
      node.innerHTML = html;
      return () => digitWalk(node);
    };
    expect(plant("<span>Dad's day started normally · 7:42 am</span>")).toThrow();
    expect(plant("<span>She opened 4 apps today</span>")).toThrow();
    expect(plant('<span data-count="9">Today</span>')).toThrow();
    expect(plant(`<span>${WAITLIST_BODY}</span>`)).not.toThrow();
  });
});

/* --------------------------------------------------------------------- */
/* The refused components                                                 */
/* --------------------------------------------------------------------- */

describe("the refused components stay refused", () => {
  it("renders no chart, ring, sparkline, countdown or score", () => {
    const { container } = render(<App />);
    expect(container.querySelector("svg")).toBeNull();
    expect(container.querySelector("progress")).toBeNull();
    expect(container.querySelector("meter")).toBeNull();
  });

  it("permits canvas only as the two aria-hidden rhythm-field backdrops", () => {
    // The blanket canvas ban was written against charts and scores. The
    // rhythm field (founder decision, DECISIONS 129/131) is a decorative
    // backdrop with a content-honesty rule of its own — signals and the
    // parent-first ask, never inference — so the exemption is scoped to
    // exactly that shape: marked, hidden from assistive tech, inert to the
    // pointer, and never more than the two approved placements. A third
    // canvas, or one that speaks to a screen reader, fails here.
    const { container } = render(<App />);
    const canvases = Array.from(container.querySelectorAll("canvas"));
    expect(canvases.length).toBeLessThanOrEqual(2);
    for (const canvas of canvases) {
      expect(canvas.hasAttribute("data-rhythm-field")).toBe(true);
      expect(canvas.getAttribute("aria-hidden")).toBe("true");
      expect(canvas.className).toContain("pointer-events-none");
    }
  });

  it("names none of them in the source either", () => {
    for (const file of ["sections/Scenarios.tsx", "sections/Hero.tsx", "App.tsx"]) {
      const source = readFileSync(join(SRC, file), "utf8");
      expect(source, file).not.toMatch(/\b(sparkline|readiness|countdown|scoreRing)\b/i);
    }
  });
});
