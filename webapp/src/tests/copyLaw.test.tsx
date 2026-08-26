/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * The copy law over the rendered spec-009 surfaces.
 *
 * The law that governs SMS governs pixels too, and spec 009 adds three bans
 * of its own to the standing lists: "ordinary" (the word is retired from
 * every rendered string — "normal" replaced it), "checked in" (Kettle hears
 * from, it never checks in on), and the "since N days ago" shape (the
 * unreachable duration reads "in N days"). Family-note BODIES are
 * family-authored content and are exempt the way the blog body is — the
 * fixtures here keep them benign so the scan exercises the chrome.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FamilyScreen } from "@/screens/Family";
import { NoFamily } from "@/screens/NoFamily";
import { ParentDetail } from "@/screens/ParentDetail";
import { Today } from "@/screens/Today";
import { computeParentToday, computeRollup } from "@/lib/parentState";
import { SIGNAL_DISPLAY_NAMES } from "@/lib/signalNames";
import { PRIVACY_FOOTER, SETUP_SEND_LABEL, STATE_QUIET } from "@/lib/copy";
import type { JournalEntry, Member, Parent, ParentSignal, Ping } from "@/lib/types";

const IST = "Asia/Kolkata";
const CHICAGO = "America/Chicago";
/** 12:00 IST — afternoon for the parents, small hours for the viewer. */
const NOON_IST = new Date("2026-08-03T06:30:00Z");

/**
 * One parent carries a phone number and one only a WhatsApp number, so both
 * call-href paths are exercised: the numbers ride in hrefs and must never
 * surface as text (DECISIONS 167) — `strayDigits` below would catch either.
 */
const parents: Parent[] = [
  {
    id: "p1",
    family_id: "f1",
    display_name: "Amma",
    tz: null,
    phone_e164: "+919812345678",
    whatsapp_e164: null,
    relationship: "Mom",
    city_label: "Chennai",
  },
  {
    id: "p2",
    family_id: "f1",
    display_name: "Appa",
    tz: null,
    phone_e164: null,
    whatsapp_e164: "+919876500000",
    relationship: "Dad",
    city_label: null,
  },
  {
    id: "p3",
    family_id: "f1",
    display_name: "Paati",
    tz: null,
    phone_e164: null,
    whatsapp_e164: null,
    relationship: "Grandma",
    city_label: null,
  },
];
const members: Member[] = [
  { id: "m1", family_id: "f1", display_name: "Hema", role: "owner", digest_channel: "sms" },
];
const signals: ParentSignal[] = parents.flatMap((p) => [
  { parent_id: p.id, signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: p.id, signal: "device_alive", alarm_grade: false, active: true },
]);

/**
 * The three glyph states, from ping histories the app could really see:
 * Amma pinged this morning (normal), Appa pinged yesterday inside cadence
 * (quiet), Paati's tripwires have all gone stale (unreachable).
 */
const ordinaryPings: Ping[] = [
  { parent_id: "p1", signal: "whatsapp", ts_utc: "2026-08-03T02:42:00Z" },
  { parent_id: "p1", signal: "device_alive", ts_utc: "2026-08-03T01:00:00Z" },
];
const quietPings: Ping[] = [
  { parent_id: "p2", signal: "whatsapp", ts_utc: "2026-08-02T05:30:00Z" },
];
const stalePings: Ping[] = [
  { parent_id: "p3", signal: "whatsapp", ts_utc: "2026-07-24T05:30:00Z" },
  { parent_id: "p3", signal: "device_alive", ts_utc: "2026-07-31T06:30:00Z" },
];
const allPings = [...ordinaryPings, ...quietPings, ...stalePings];

/** The latest-row set the snapshot would carry: newest per (parent, signal). */
function latestOf(pings: Ping[]): Ping[] {
  const newest = new Map<string, Ping>();
  for (const ping of pings) {
    const key = `${ping.parent_id} ${ping.signal}`;
    const held = newest.get(key);
    if (!held || ping.ts_utc > held.ts_utc) newest.set(key, ping);
  }
  return [...newest.values()];
}

const stateFor = (parent: Parent, pings: Ping[] = allPings, now: Date = NOON_IST) =>
  computeParentToday(parent, IST, signals, pings, latestOf(pings), now, CHICAGO);

const statesAt = (now: Date = NOON_IST, pings: Ping[] = allPings) =>
  parents.map((p) => stateFor(p, pings, now));

/** Benign note fixtures: the chrome around them is what the scan holds. */
const notes: JournalEntry[] = [
  {
    id: 1,
    family_id: "f1",
    parent_id: "p1",
    author_label: "Hema",
    body: "New reading glasses arrive Thursday.",
    event_date: null,
    created_utc: "2026-08-01T10:00:00Z",
  },
  {
    id: 2,
    family_id: "f1",
    parent_id: null,
    author_label: "",
    body: "Eye doctor",
    event_date: "2026-09-01",
    created_utc: "2026-08-02T10:00:00Z",
  },
];
const TODAY_DATE = "2026-08-03";
const noop = async () => undefined;

const detailProps = {
  todayDate: TODAY_DATE,
  onBack: () => undefined,
  onAddNote: noop,
  onSteps: () => undefined,
};

const URGENCY = [
  "emergency", "urgent", "immediately", "critical", "alarm", "alert", "danger",
  "panic", "hurry", "asap", "worried", "worry", "afraid", "scared", "crisis", "fear",
];
const MEDICAL = [
  "fall", "fallen", "ill", "sick", "hospital", "ambulance", "unwell", "injured",
  "collapse", "dementia", "health", "medical", "symptom", "diagnosis",
];
const PROFILE = [
  "whatsapp", "youtube", "news", "charger", "charge_on", "charge_off", "device_alive",
  "app", "apps", "opened", "times", "count", "pings", "ping", "average", "streak",
  "trend", "score", "percent",
  // DECISIONS 172: internal mechanism vocabulary, never customer-facing.
  "tripwire", "tripwires",
  // Spec 009 §1: "normal" replaced it in every rendered string.
  "ordinary",
];
const SIGNAL_NAMES = Object.values(SIGNAL_DISPLAY_NAMES).map((name) => name.toLowerCase());
/**
 * Gendered pronouns, banned at the rendered surface (items 24/34): nothing
 * may infer a pronoun from a name, so no default render may contain one.
 * `they/their` stays legal — it is the neutral default.
 */
const PRONOUNS = ["she", "her", "hers", "he", "him", "his"];
/** Spec 009 §7's phrase bans, scanned as phrases rather than words. */
const PHRASES = ["checked in", "checking in on"];
const BANNED = [...URGENCY, ...MEDICAL, ...PROFILE, ...SIGNAL_NAMES, ...PRONOUNS];
const NAMES = ["Amma", "Appa", "Paati", "Hema", "Kettle", "Mom", "Dad", "Grandma", "Chennai"];

const CLOCK = /\b\d{1,2}:\d{2}\s?[ap]m\b/gi;

/**
 * Digit allowances beyond clock times and ISO dates, each a pinned shape:
 * relative time ("12 minutes ago", "2 hours ago", "6 days ago"), the
 * unreachable duration ("in 3 days"), the kicker date ("Wednesday ·
 * August 26"), and note metadata's month-day ("Aug 24" / "Sep 1").
 */
const REL_TIME = /\b\d+ (?:minutes|hours|days) ago\b|\b1 (?:minute|hour|day) ago\b/g;
const IN_DAYS = /\bin \d+ days?\b/g;
const KICKER_DATE =
  /\b(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday) · (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}\b/g;
const MONTH_DAY = /\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2}\b/g;
const APP_ALLOW = [REL_TIME, IN_DAYS, KICKER_DATE, MONTH_DAY];

/**
 * The channel-name exemption (DECISIONS 122): one key, its value pinned by a
 * test below, and no wider.
 */
const SHARE_CTA_EXEMPTION = [SETUP_SEND_LABEL];

/** Digits are allowed only inside a clock time or an ISO date. */
function strayDigits(text: string): string {
  return text
    .replace(CLOCK, "")
    .replace(/\b\d{4}-\d{2}-\d{2}\b/g, "")
    .replace(/[^\d]/g, "");
}

function assertCopyLaw(text: string, allow: (string | RegExp)[] = []) {
  let scanned = text;
  for (const name of NAMES) scanned = scanned.split(name).join("«name»");
  for (const allowed of allow) {
    scanned =
      typeof allowed === "string"
        ? scanned.split(allowed).join("«allowed»")
        : scanned.replace(allowed, "«allowed»");
  }
  const lowered = scanned.toLowerCase();
  for (const word of BANNED) {
    expect(
      new RegExp(`\\b${word}\\b`).test(lowered),
      `"${word}" appeared in rendered output: ${text}`,
    ).toBe(false);
  }
  for (const phrase of PHRASES) {
    expect(lowered.includes(phrase), `"${phrase}" appeared in: ${text}`).toBe(false);
  }
  // Spec 009 §1: the "since ... ago" duration shape is retired. Scanned
  // against the UNMASKED text (the Amendment-A move): the relative-time
  // allowance must not be able to hide the shape it sits inside.
  expect(
    /since\s+\d+\s+days?\s+ago/.test(text.toLowerCase()),
    `"since N days ago" in: ${text}`,
  ).toBe(false);
  expect(strayDigits(scanned), `stray digits in: ${text}`).toBe("");
}

/**
 * The DOM's visible text with a space at every element seam — element
 * boundaries become word boundaries, so a banned word is caught wherever the
 * markup puts it (found by plant, 005b build).
 */
function renderedText(): string {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const parts: string[] = [];
  while (walker.nextNode()) {
    const value = walker.currentNode.nodeValue?.trim();
    if (value) parts.push(value);
  }
  return parts.join(" ");
}

function renderToday(states = statesAt(), now = NOON_IST) {
  return render(
    <Today
      states={states}
      rollup={computeRollup(states, IST, now)}
      dateLine="Wednesday · August 26"
      onOpen={() => undefined}
    />,
  );
}

describe("rendered copy law", () => {
  it("holds for the Today screen with all three states on screen", () => {
    renderToday();
    const text = renderedText();
    expect(text).toContain("Today looks like a normal day.");
    expect(text).toContain("Quiet so far today.");
    expect(text).toContain("Kettle can't hear from Grandma's phone right now.");
    assertCopyLaw(text, APP_ALLOW);
  });

  it("holds for the parent detail in each of the three states", () => {
    for (const parent of parents) {
      const state = stateFor(parent);
      const { unmount } = render(
        <ParentDetail state={state} notes={notes} {...detailProps} />,
      );
      const text = renderedText();
      expect(text).toContain(state.sentence);
      assertCopyLaw(text, APP_ALLOW);
      unmount();
    }
  });

  it("scans the unreachable detail with its aside and fix card actually rendered", () => {
    const state = stateFor(parents[2]);
    expect(state.kind).toBe("unreachable");
    render(<ParentDetail state={state} notes={[]} {...detailProps} />);
    expect(screen.getByTestId("detail-aside")).toBeInTheDocument();
    expect(screen.getByTestId("fix-card")).toBeInTheDocument();
    assertCopyLaw(renderedText(), APP_ALLOW);
  });

  it("renders the empty state inside the law, and never as watching", () => {
    renderToday([]);
    const text = renderedText();
    expect(text).toContain("No one is set up yet.");
    expect(text.toLowerCase()).not.toContain("watch");
    assertCopyLaw(text, APP_ALLOW);
  });

  it("never renders anything darker than Quiet so far", () => {
    renderToday(statesAt(NOON_IST, []));
    const sentences = screen.getAllByTestId("card-line").map((n) => n.textContent ?? "");
    expect(sentences).toHaveLength(parents.length);
    for (const sentence of sentences) {
      expect(sentence, `darker than the floor: ${sentence}`).toBe(STATE_QUIET);
    }
  });

  it("puts the phone numbers in hrefs and nowhere in the visible text", () => {
    // DECISIONS 167: tel: for Amma, the wa.me fallback for Appa — and neither
    // number ever prints.
    renderToday();
    const hrefs = screen.getAllByTestId("call-button").map((n) => n.getAttribute("href"));
    expect(hrefs).toEqual(["tel:+919812345678", "https://wa.me/919876500000"]);
    expect(document.body.textContent).not.toContain("9812345678");
    expect(document.body.textContent).not.toContain("9876500000");
  });

  it("holds for the Family screen, and carries the privacy line verbatim", () => {
    const setupEntries = [
      {
        parentId: "p1",
        parentName: "Amma",
        status: "ready" as const,
        url: "https://kettle-api.fly.dev/s/slug000000000000000000A1",
        shareHref: "https://wa.me/?text=x",
        expiresDate: "2026-08-10",
      },
      {
        parentId: "p2",
        parentName: "Appa",
        status: "reporting" as const,
        url: null,
        shareHref: null,
        expiresDate: null,
      },
    ];
    render(
      <FamilyScreen
        parentStates={statesAt()}
        cities={{ p1: "Chennai", p2: "", p3: "" }}
        members={members}
        setupEntries={setupEntries}
        journal={notes}
        todayDate={TODAY_DATE}
        onOpen={() => undefined}
        onAddNote={noop}
        onSaveCity={noop}
      />,
    );
    const text = renderedText();
    expect(screen.getByTestId("privacy-footer")).toHaveTextContent(PRIVACY_FOOTER);
    expect(text).toContain("sms");
    expect(text).toContain("Ready to send");
    // The notes panel is genuinely on screen, upcoming strip included.
    expect(text).toContain("Family notes");
    expect(text).toContain("Upcoming");
    assertCopyLaw(text, [...SHARE_CTA_EXEMPTION, ...APP_ALLOW]);
  });

  it("spends the channel exemption on one key with one value, and no wider", () => {
    expect(SETUP_SEND_LABEL).toBe("Send on WhatsApp");
    expect(SHARE_CTA_EXEMPTION).toEqual(["Send on WhatsApp"]);
  });

  it("holds for the no-family screen", () => {
    render(<NoFamily />);
    assertCopyLaw(renderedText());
  });

  it("would catch a regression", () => {
    expect(() => assertCopyLaw("Kettle: this is urgent")).toThrow();
    expect(() => assertCopyLaw("Amma opened WhatsApp 4 times")).toThrow();
    // Spec 009's own bans: the retired word, the retired phrase, the retired
    // duration shape.
    expect(() => assertCopyLaw("Today looks like an ordinary day.")).toThrow();
    expect(() => assertCopyLaw("Mom checked in this morning")).toThrow();
    expect(() => assertCopyLaw("Nothing since 9 days ago", [REL_TIME])).toThrow();
  });
});

describe("signal names stay banned with no surface exempted", () => {
  it("bans every humanised signal name", () => {
    for (const name of Object.values(SIGNAL_DISPLAY_NAMES)) {
      expect(() => assertCopyLaw(`Last routine seen on ${name}`), name).toThrow();
    }
  });

  it("keeps the digit allowances from smuggling in counting words", () => {
    for (const smuggled of [
      "Heard 4 times in 2 days ago",
      "A streak, 3 days ago",
      "Pinged 12 minutes ago on average",
    ]) {
      expect(() => assertCopyLaw(smuggled, APP_ALLOW), smuggled).toThrow();
    }
  });
});
