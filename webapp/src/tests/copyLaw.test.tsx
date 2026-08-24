/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * AC4 — the copy law, extended to rendered UI.
 *
 * The law that governs SMS governs pixels too: what a family reads on a screen
 * at an anxious moment is the same product promise as what arrives in a text.
 * So this renders every screen with realistic data and walks the resulting DOM
 * text, not the source.
 *
 * Spec 008 replaces the glance and the per-signal tripwire rows with the v5
 * surfaces — Today, the parent detail, the restyled Family — and the law got
 * *stronger* in the trade: the tripwire view was the one surface allowed to
 * say a signal's name, and that surface is gone. Signal names now render
 * nowhere, so no scan in this file carries a signal-name allowlist any more.
 * Two narrow allowances remain, both pinned below: the day-granularity
 * recency ("6 days ago" — words plus one digit, no clock-time variant, the
 * same shape spec 005d §2 granted) and the Today screen's date line.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FamilyScreen } from "@/screens/Family";
import { NoFamily } from "@/screens/NoFamily";
import { ParentDetail } from "@/screens/ParentDetail";
import { Today } from "@/screens/Today";
import { computeParentToday } from "@/lib/parentState";
import { SIGNAL_DISPLAY_NAMES } from "@/lib/signalNames";
import { PRIVACY_FOOTER, SETUP_SEND_LABEL, STATE_QUIET } from "@/lib/copy";
import type { Member, Parent, ParentSignal, Ping, SetupLink } from "@/lib/types";

const IST = "Asia/Kolkata";
const CHICAGO = "America/Chicago";
/** 12:00 IST — afternoon for the parents, small hours for the viewer. */
const NOON_IST = new Date("2026-08-03T06:30:00Z");

/**
 * One parent carries a phone number so the Call button's law is exercised:
 * the number rides in the tel: href and must never surface as text
 * (DECISIONS 167) — `strayDigits` below would catch it anywhere it leaked.
 */
const parents: Parent[] = [
  { id: "p1", family_id: "f1", display_name: "Amma", tz: null, phone_e164: "+919812345678" },
  { id: "p2", family_id: "f1", display_name: "Appa", tz: null, phone_e164: null },
  { id: "p3", family_id: "f1", display_name: "Paati", tz: null, phone_e164: null },
];
const members: Member[] = [
  { id: "m1", family_id: "f1", display_name: "Hema", role: "owner", digest_channel: "sms" },
];
const signals: ParentSignal[] = parents.flatMap((p) => [
  { parent_id: p.id, signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: p.id, signal: "device_alive", alarm_grade: false, active: true },
]);
const setupLinks: SetupLink[] = [
  {
    parent_id: "p1",
    slug: "slug000000000000000000A1",
    created_utc: "2026-05-10T00:00:00Z",
    expires_utc: "2026-05-17T00:00:00Z",
    revoked_utc: null,
  },
];

/**
 * The three glyph states, built from ping histories the app could really see:
 * - Amma pinged this morning (ordinary);
 * - Appa pinged yesterday, tripwire still within cadence (quiet);
 * - Paati's tripwires have all gone stale (unreachable).
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
  computeParentToday(parent, IST, signals, pings, latestOf(pings), setupLinks, now, CHICAGO);

const statesAt = (now: Date = NOON_IST, pings: Ping[] = allPings) =>
  parents.map((p) => stateFor(p, pings, now));

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
  // DECISIONS 172: internal mechanism vocabulary, never customer-facing. The
  // word lives on in identifiers, filenames and test names — those are not
  // rendered text and this scan never sees them.
  "tripwire", "tripwires",
];
/**
 * The humanised signal names, banned with no surface exempted.
 *
 * The raw keys already were, but `Daily Check` is ordinary English and walked
 * straight past this list until 005d went looking. Derived from the same map
 * the tripwire logic still reads from, so a new signal joins the ban for free
 * — and since spec 008 retired the tripwire rows, no view anywhere may render
 * one of these. The scoped exemption did not move; it was deleted.
 */
const SIGNAL_NAMES = Object.values(SIGNAL_DISPLAY_NAMES).map((name) => name.toLowerCase());
/**
 * Gendered pronouns, banned at the rendered surface (items 24/34, and the
 * spec 008 restructure of the v5 file's she/her strings): nothing may infer a
 * pronoun from a name, so no default render may contain one. `they/their`
 * stays legal — it is the neutral default. The recorded-pronoun clock forms
 * (`her time`) exist in copy.ts but render only when a pronoun is actually
 * recorded, which no fixture here has — so a hardcoded pronoun sneaking into
 * any default string fails this scan.
 */
const PRONOUNS = ["she", "her", "hers", "he", "him", "his"];
const BANNED = [...URGENCY, ...MEDICAL, ...PROFILE, ...SIGNAL_NAMES, ...PRONOUNS];
const NAMES = ["Amma", "Appa", "Paati", "Hema", "Kettle"];

const CLOCK = /\b\d{1,2}:\d{2}\s?[ap]m\b/gi;

/**
 * Day-granularity recency: words plus one digit, and no clock-time variant
 * exists to smuggle precision back in. Spec 005d §2 granted this shape to the
 * tripwire rows; the rows are gone and the shape travels to the last-heard
 * meta ("Last heard from 6 days ago."), which reaches past yesterday only at
 * day grain. The Family scan deliberately does not receive it.
 */
const DAY_RECENCY = /\b\d+ days ago\b/g;
/** The Today screen's one dated line — "Sunday, August 3", never a year. */
const DATE_LINE =
  /\b(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday), (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}\b/g;

/**
 * The channel-name exemption (DECISIONS 122, granted in the rulings that follow
 * item 123), and the narrowest one this codebase has.
 *
 * It is one *key*, and that key's value is pinned by a test below. Both halves
 * matter: exempting the key alone would let anyone widen the law by rewriting
 * the string it points at, and exempting the string alone would let a second key
 * say the same word somewhere it has no business being. The law's shape is
 * unchanged — app names are banned where they would describe a parent's
 * behaviour, and this string describes the child's own next action.
 */
const SHARE_CTA_EXEMPTION = [SETUP_SEND_LABEL];

/** Digits are allowed only inside a clock time or an ISO date. */
function strayDigits(text: string): string {
  return text
    .replace(CLOCK, "")
    .replace(/\b\d{4}-\d{2}-\d{2}\b/g, "")
    .replace(/[^\d]/g, "");
}

/**
 * `allow` is a per-view allowlist, masked out before the ban scan. It defaults
 * to empty: a caller that passes nothing gets the full law.
 */
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
  expect(strayDigits(scanned), `stray digits in: ${text}`).toBe("");
}

/**
 * The DOM's visible text with a space at every element seam.
 *
 * `document.body.textContent` glues adjacent elements — a status label ending
 * "…WhatsApp" followed by a link starting "Send…" scans as "whatsappsend",
 * which no word-bounded ban can match. Found by planting exactly that
 * regression (005b build): the law passed with a banned word on screen. Text
 * nodes joined with a separator make element boundaries word boundaries, so
 * a banned word is caught wherever the markup puts it.
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

describe("rendered copy law", () => {
  it("holds for the Today screen with all three states on screen", () => {
    render(
      <Today states={statesAt()} dateLine="Sunday, August 3" onOpen={() => undefined} />,
    );
    const text = renderedText();
    // All three states really are on screen — not passing on an empty render.
    expect(text).toContain("Today looks like an ordinary day.");
    expect(text).toContain("Quiet so far today.");
    expect(text).toContain("Kettle can't hear from Paati's phone right now.");
    assertCopyLaw(text, [DAY_RECENCY, DATE_LINE]);
  });

  it("holds for the parent detail in each of the three states", () => {
    for (const parent of parents) {
      const state = stateFor(parent);
      const { unmount } = render(<ParentDetail state={state} onBack={() => undefined} />);
      const text = renderedText();
      expect(text).toContain(state.sentence);
      assertCopyLaw(text, [DAY_RECENCY]);
      unmount();
    }
  });

  it("scans the unreachable detail with its aside and fix card actually rendered", () => {
    const state = stateFor(parents[2]);
    expect(state.kind).toBe("unreachable");
    render(<ParentDetail state={state} onBack={() => undefined} />);
    // The two surfaces unique to this state are on screen before the scan.
    expect(screen.getByTestId("detail-aside")).toBeInTheDocument();
    expect(screen.getByTestId("fix-card")).toBeInTheDocument();
    assertCopyLaw(renderedText(), [DAY_RECENCY]);
  });

  it("renders the empty state inside the law, and never as watching", () => {
    // DECISIONS 172: "watched over" is the framing this product exists to
    // avoid. The empty state renders only with no parents, so no other
    // fixture in this file ever puts it on screen — scanned here on purpose.
    render(<Today states={[]} dateLine="Sunday, August 3" onOpen={() => undefined} />);
    const text = renderedText();
    expect(text).toContain("No one is set up yet.");
    expect(text.toLowerCase()).not.toContain("watch");
    assertCopyLaw(text, [DATE_LINE]);
  });

  it("never renders anything darker than Quiet so far", () => {
    render(<Today states={statesAt(NOON_IST, [])} dateLine="Sunday, August 3" onOpen={() => undefined} />);
    const sentences = screen.getAllByTestId("today-sentence").map((n) => n.textContent ?? "");
    expect(sentences).toHaveLength(parents.length);
    for (const sentence of sentences) {
      expect(sentence, `darker than the floor: ${sentence}`).toBe(STATE_QUIET);
    }
  });

  it("spends at most two clock times per Today card — theirs and the last-heard", () => {
    render(<Today states={statesAt()} dateLine="Sunday, August 3" onOpen={() => undefined} />);
    for (const card of screen.getAllByTestId("today-card")) {
      const clocks = (card.textContent ?? "").match(CLOCK) ?? [];
      expect(clocks.length, card.textContent ?? "").toBeLessThanOrEqual(2);
    }
  });

  it("keeps the detail's clocks to the hero pair plus one per day row", () => {
    // Local time, the last-heard meta, and at most one first-heard time in
    // each of the three day rows: five, and a sixth is a leak.
    render(<ParentDetail state={stateFor(parents[0])} onBack={() => undefined} />);
    const clocks = renderedText().match(CLOCK) ?? [];
    expect(clocks.length).toBeLessThanOrEqual(5);
  });

  /**
   * The load-bearing one. Warmth may not smuggle in a count: a detail built
   * from one ping and a detail built from many must be the same pixels,
   * structure included — no digit, no extra segment, no brighter shade.
   * Comparing markup (minus the clock, which legitimately tracks real times)
   * catches a count hiding in an attribute or a class that text scanning
   * would walk straight past.
   */
  it("encodes no ping count anywhere in the rendered detail", () => {
    const morning = (minute: number): Ping => ({
      parent_id: "p1",
      signal: "whatsapp",
      ts_utc: `2026-08-03T02:${String(minute).padStart(2, "0")}:00Z`,
    });
    const strip = (html: string) => html.replace(CLOCK, "«clock»");

    const sparse = render(
      <ParentDetail state={stateFor(parents[0], [morning(42)])} onBack={() => undefined} />,
    );
    const sparseHtml = strip(sparse.container.innerHTML);
    sparse.unmount();

    const busy = render(
      <ParentDetail
        state={stateFor(parents[0], [10, 18, 25, 33, 42].map(morning))}
        onBack={() => undefined}
      />,
    );
    expect(strip(busy.container.innerHTML)).toBe(sparseHtml);
  });

  it("puts the phone number in the tel: href and nowhere in the visible text", () => {
    // DECISIONS 167: family-facing numbers are tap-to-act links, never prose.
    render(<ParentDetail state={stateFor(parents[0])} onBack={() => undefined} />);
    expect(screen.getByTestId("call-button").getAttribute("href")).toBe("tel:+919812345678");
    expect(document.body.textContent).not.toContain("9812345678");
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
      {
        parentId: "p3",
        parentName: "Paati",
        status: "needs_link" as const,
        url: null,
        shareHref: null,
        expiresDate: null,
      },
    ];
    render(
      <FamilyScreen
        parentStates={statesAt()}
        members={members}
        setupEntries={setupEntries}
        onOpen={() => undefined}
      />,
    );
    const text = renderedText();
    expect(screen.getByTestId("privacy-footer")).toHaveTextContent(PRIVACY_FOOTER);
    // `sms` is a channel name, not a signal name — allowed, and worth pinning.
    expect(text).toContain("sms");
    // The setup card is genuinely on screen in every state before the scan.
    expect(text).toContain("Ready to send");
    expect(text).toContain("Set up and reporting");
    expect(text).toContain("Needs a fresh link");
    // The parents list is on screen too, wearing its timezone sub-line.
    expect(screen.getAllByTestId("roster-parent")).toHaveLength(parents.length);
    assertCopyLaw(text, SHARE_CTA_EXEMPTION);
  });

  it("spends the channel exemption on one key with one value, and no wider", () => {
    // The value is pinned so the exemption cannot be widened by rewriting the
    // string it points at, and the list is pinned so a second key cannot join
    // it quietly. Changing either is a visible act in this file.
    expect(SETUP_SEND_LABEL).toBe("Send on WhatsApp");
    expect(SHARE_CTA_EXEMPTION).toEqual(["Send on WhatsApp"]);
  });

  it("is load-bearing: the Family screen fails the law without it", () => {
    // The exemption is a hole of a fixed shape, and this is the shape. Scanned
    // with no allowlist, the same screen must still be rejected.
    render(
      <FamilyScreen
        parentStates={statesAt()}
        members={members}
        setupEntries={[
          {
            parentId: "p1",
            parentName: "Amma",
            status: "ready" as const,
            url: "https://kettle-api.fly.dev/s/slug000000000000000000A1",
            shareHref: "https://wa.me/?text=x",
            expiresDate: "2026-08-10",
          },
        ]}
        onOpen={() => undefined}
      />,
    );
    expect(() => assertCopyLaw(renderedText())).toThrow(/whatsapp/i);
  });

  it("holds for the no-family screen", () => {
    render(<NoFamily />);
    assertCopyLaw(renderedText());
  });

  it("would catch a regression", () => {
    expect(() => assertCopyLaw("Kettle: this is urgent")).toThrow();
    expect(() => assertCopyLaw("Amma opened WhatsApp 4 times")).toThrow();
    // DECISIONS 172: the word the fix card used to open with, banned so the
    // vetoed body cannot come back.
    expect(() => assertCopyLaw("A tripwire may need a quick fix")).toThrow();
  });
});

/**
 * Spec 008 closed the law's one signal-name hole: the tripwire rows that
 * needed the names are retired, so the exemption that served them is deleted
 * rather than orphaned. This holds the wall where the hole used to be.
 */
describe("the retired tripwire exemption", () => {
  it("bans every humanised signal name with no surface exempted", () => {
    for (const name of Object.values(SIGNAL_DISPLAY_NAMES)) {
      expect(
        () => assertCopyLaw(`Last routine seen on ${name}`),
        `${name} escaped the law`,
      ).toThrow();
    }
    // And every real surface above is scanned with no signal-name allowlist —
    // the only allowances left are day-words recency, the date line, and the
    // one share CTA.
  });

  it("keeps day-granularity recency from smuggling in counting words", () => {
    for (const smuggled of [
      "Heard 4 times in 2 days ago",
      "A streak, 3 days ago",
      "Quiet for 10 days ago on average",
    ]) {
      expect(() => assertCopyLaw(smuggled, [DAY_RECENCY]), smuggled).toThrow();
    }
  });
});
