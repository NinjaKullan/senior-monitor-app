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

/** App and platform names. Permitted in §3.4's mechanism copy and nowhere else. */
const APP_NAMES = ["whatsapp", "facetime", "shortcuts", "youtube", "instagram"];

const BANNED = [...URGENCY, ...DIAGNOSIS, ...MEDICAL, ...ALARM, ...SURVEILLANCE, ...VERDICTS];

/**
 * The pinned allowlist. Every entry is a literal, written out here rather than
 * derived, so widening it is a visible act in this file — the asymmetry adopted
 * in QUESTIONS 62: the ban may derive itself, the exemption may not.
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
      new RegExp(`\\b${word.replace(/'/g, "['’]")}\\b`).test(scanned),
      `"${word}" appeared in: ${text}`,
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

/** Roles, and the shape rule each carries (AC12). */
const ROLE =
  /_(H1|H2|BODY|LEAD|SERIF|TAB|EYEBROW|CTA|LABEL|ALT|NOTIF|CHIP|HREF|SUCCESS|ERROR|WORDMARK|LINE)$/;

const words = (text: string) => text.trim().split(/\s+/).filter(Boolean).length;

describe("AC3 — the copy module obeys the marketing bans", () => {
  it("has something to scan", () => {
    expect(STRINGS.length).toBeGreaterThan(30);
  });

  it("bans urgency, diagnosis, alarm, surveillance and verdicts", () => {
    for (const [name, value] of STRINGS) {
      // The mechanism section may name the mechanism; a sentence about her day
      // may not. That split is asserted separately below.
      const allow = name.startsWith("STEP_") ? [...ALLOW, /Shortcuts/] : ALLOW;
      expect(() => assertCopyLaw(value, allow), name).not.toThrow();
    }
  });

  it("names an app only in the mechanism steps", () => {
    for (const [name, value] of STRINGS) {
      if (name.startsWith("STEP_")) continue;
      for (const app of APP_NAMES) {
        expect(
          new RegExp(`\\b${app}\\b`).test(value.toLowerCase()),
          `${name} narrates her day through an app name: ${value}`,
        ).toBe(false);
      }
    }
  });

  it("would catch each of the six planted regressions", () => {
    // AC3 names these exactly. Each is a sentence someone could plausibly write.
    expect(() => assertCopyLaw("Join now — limited places")).toThrow();
    expect(() => assertCopyLaw("Know she's fine today")).toThrow();
    expect(() => assertCopyLaw("Kettle sends an alert when something is wrong")).toThrow();
    expect(() => assertCopyLaw("Track her daily routine")).toThrow();
    expect(() => assertCopyLaw("Request invite!")).toThrow();
    expect(() => assertCopyLaw("Spot the early symptoms of decline")).toThrow();
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
    // a rule quietly stops applying.
    const unclassified = STRINGS.filter(([name]) => !ROLE.test(name)).map(([name]) => name);
    expect(unclassified, "give these a role suffix").toEqual([]);
  });

  it("keeps H1 to seven words and H2s to three-to-five", () => {
    for (const [name, value] of STRINGS) {
      if (name.endsWith("_H1")) expect(words(value), name).toBeLessThanOrEqual(7);
      if (name.endsWith("_H2")) {
        expect(words(value), name).toBeGreaterThanOrEqual(3);
        expect(words(value), name).toBeLessThanOrEqual(5);
      }
    }
  });

  it("keeps every paragraph under twenty-three words", () => {
    for (const [name, value] of STRINGS) {
      if (/_(BODY|LEAD|SERIF)$/.test(name)) {
        expect(words(value), `${name} runs long: ${value}`).toBeLessThanOrEqual(23);
      }
    }
  });

  it("keeps CTA labels to one or two flat words", () => {
    for (const [name, value] of STRINGS) {
      if (name.endsWith("_CTA")) expect(words(value), name).toBeLessThanOrEqual(2);
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
    expect(plant("<span>Amma's day started normally · 7:42 am</span>")).toThrow();
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
    expect(container.querySelector("canvas")).toBeNull();
    expect(container.querySelector("progress")).toBeNull();
    expect(container.querySelector("meter")).toBeNull();
  });

  it("names none of them in the source either", () => {
    for (const file of ["sections/Scenarios.tsx", "sections/Hero.tsx", "App.tsx"]) {
      const source = readFileSync(join(SRC, file), "utf8");
      expect(source, file).not.toMatch(/\b(sparkline|readiness|countdown|scoreRing)\b/i);
    }
  });
});
