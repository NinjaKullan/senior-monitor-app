/**
 * AC4 — the copy law, extended to rendered UI.
 *
 * The law that governs SMS governs pixels too: what a family reads on a screen
 * at an anxious moment is the same product promise as what arrives in a text.
 * So this renders all three screens with realistic data and walks the resulting
 * DOM text, not the source.
 *
 * Spec 005c adds warmth to that surface, and with warmth the temptation to
 * quantify. The law grows to match: at most two clock times (the dual-timezone
 * subline), and — the assertion that matters most here — nothing rendered may
 * encode *how much* activity there was, in text or in structure.
 *
 * Spec 005d adds the law's first exemption, and it is written as an allowlist
 * rather than as a softening: `assertCopyLaw` still bans signal names by
 * default, and exactly one view passes exactly the six humanised names. Every
 * other surface in this file calls it with no allowlist at all, so a signal name
 * leaking into a digest or a glance headline still fails here.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Digests } from "@/screens/Digests";
import { FamilyScreen } from "@/screens/Family";
import { Glance } from "@/screens/Glance";
import { NoFamily } from "@/screens/NoFamily";
import { TripwireDetail } from "@/screens/TripwireDetail";
import { buildDigestEntries } from "@/lib/digests";
import { computeGlance } from "@/lib/glance";
import { computeTripwires } from "@/lib/tripwires";
import { SIGNAL_DISPLAY_NAMES } from "@/lib/signalNames";
import { PRIVACY_FOOTER } from "@/lib/copy";
import type { DigestSend, Member, Parent, ParentSignal, Ping } from "@/lib/types";

const IST = "Asia/Kolkata";
const CHICAGO = "America/Chicago";
/** 12:00 IST — afternoon for the parents, small hours for the viewer. */
const NOON_IST = new Date("2026-08-03T06:30:00Z");
/** 09:00 IST — the day part whose headline carries a parent's name. */
const MORNING_IST = new Date("2026-08-03T03:30:00Z");

const parents: Parent[] = [
  { id: "p1", family_id: "f1", display_name: "Amma", tz: null },
  { id: "p2", family_id: "f1", display_name: "Appa", tz: null },
];
const members: Member[] = [
  { id: "m1", family_id: "f1", display_name: "Hema", role: "owner", digest_channel: "sms" },
];
const signals: ParentSignal[] = parents.flatMap((p) => [
  { parent_id: p.id, signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: p.id, signal: "device_alive", alarm_grade: false, active: true },
]);
const pings: Ping[] = [{ parent_id: "p1", signal: "whatsapp", ts_utc: "2026-08-03T02:42:00Z" }];
/**
 * Setup entries in all three states (spec 005b), so the Family screen's
 * forwarding surface is scanned under the full law: the slug rides in the
 * href, which the DOM-text walk ignores — but a slug *printed* as text, or a
 * signal name in a status label, fails here like anywhere else.
 */
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
const sends: DigestSend[] = [
  { parent_id: "p1", kind: "morning", local_date: "2026-08-03", ts_utc: "2026-08-03T03:00:00Z" },
  { parent_id: "p1", kind: "evening", local_date: "2026-08-02", ts_utc: "2026-08-02T15:00:00Z" },
];

const glanceAt = (now: Date, given: Ping[] = pings) =>
  parents.map((p) => computeGlance(p, IST, signals, given, now, CHICAGO));

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
];
/**
 * The humanised signal names are banned by default too.
 *
 * The raw keys already were, but `Daily Check` is ordinary English and walked
 * straight past this list until 005d went looking — it could have appeared on a
 * digest or a glance headline and nothing here would have objected. Derived from
 * the same map the app renders from, so a new signal joins the ban for free.
 * (The *allowlist* below is pinned by hand for the opposite reason: deriving it
 * would let a new name exempt itself.)
 */
const SIGNAL_NAMES = Object.values(SIGNAL_DISPLAY_NAMES).map((name) => name.toLowerCase());
const BANNED = [...URGENCY, ...MEDICAL, ...PROFILE, ...SIGNAL_NAMES];
const NAMES = ["Amma", "Appa", "Hema", "Kettle"];

const CLOCK = /\b\d{1,2}:\d{2}\s?[ap]m\b/gi;

/**
 * AC5 — the exemption, written out as literals.
 *
 * The tripwire health view is the one surface where a signal name is *necessary*
 * copy: "her WhatsApp tripwire needs attention" cannot be said without it. This
 * list is pinned here rather than read from `SIGNAL_DISPLAY_NAMES` so that
 * widening it is a visible act in this file — a test below asserts the two agree,
 * which means adding a signal to the app fails here until someone consciously
 * adds it to the exemption too.
 */
const TRIPWIRE_NAME_EXEMPTION = [
  "WhatsApp",
  "YouTube",
  "News",
  "Charger On",
  "Charger Off",
  "Daily Check",
  // The merged end-state pair (QUESTIONS 107). "Charger" sits after the two
  // per-edge names so the longer strings mask first.
  "Daily routine",
  "Charger",
  // §2: day-granularity recency is words plus one digit. Scoped like the names
  // are — the digest and glance surfaces get no such allowance.
  /\d+ days ago/g,
];

/** Digits are allowed only inside a clock time or an ISO date. */
function strayDigits(text: string): string {
  return text
    .replace(CLOCK, "")
    .replace(/\b\d{4}-\d{2}-\d{2}\b/g, "")
    .replace(/[^\d]/g, "");
}

/**
 * `allow` is a per-view allowlist, masked out before the ban scan. It defaults
 * to empty: a caller that passes nothing gets the full law, which is what every
 * surface but one does.
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
  it("holds for the Glance screen in both states", () => {
    render(<Glance states={glanceAt(NOON_IST)} />);
    const text = renderedText();
    // Both states really are on screen — this is not passing on an empty render.
    expect(text).toContain("A normal day so far");
    expect(text).toContain("Quiet so far");
    assertCopyLaw(text);
  });

  it("holds for the warmest headline, the one that says a parent's name", () => {
    render(<Glance states={glanceAt(MORNING_IST)} />);
    const text = renderedText();
    expect(text).toContain("Amma's morning started the usual way");
    assertCopyLaw(text);
  });

  it("never renders anything darker than Quiet so far", () => {
    for (const now of [MORNING_IST, NOON_IST]) {
      const { unmount } = render(<Glance states={glanceAt(now, [])} />);
      const headlines = screen.getAllByTestId("glance-headline").map((n) => n.textContent ?? "");
      expect(headlines).toHaveLength(parents.length);
      for (const headline of headlines) {
        expect(headline.startsWith("Quiet so far"), `darker than the floor: ${headline}`).toBe(
          true,
        );
      }
      unmount();
    }
  });

  it("spends at most two clock times per card — theirs and yours", () => {
    render(<Glance states={glanceAt(NOON_IST)} />);
    for (const card of screen.getAllByTestId("glance-card")) {
      expect((card.textContent ?? "").match(CLOCK) ?? []).toHaveLength(
        card.textContent?.includes("Last routine seen") ? 2 : 0,
      );
    }
  });

  /**
   * The load-bearing one. Warmth may not smuggle in a count: a card built from
   * one ping and a card built from many must be the same pixels, structure
   * included — no digit, no extra segment, no brighter shade. Comparing markup
   * (minus the clock, which legitimately tracks the newest ping) catches a count
   * hiding in an attribute or a class that text scanning would walk straight
   * past.
   */
  it("encodes no ping count anywhere in the rendered card", () => {
    const morning = (minute: number): Ping => ({
      parent_id: "p1",
      signal: "whatsapp",
      ts_utc: `2026-08-03T02:${String(minute).padStart(2, "0")}:00Z`,
    });
    const strip = (html: string) => html.replace(CLOCK, "«clock»");

    const sparse = render(<Glance states={glanceAt(NOON_IST, [morning(42)])} />);
    const sparseHtml = strip(sparse.container.innerHTML);
    sparse.unmount();

    const busy = render(
      <Glance states={glanceAt(NOON_IST, [10, 18, 25, 33, 42].map(morning))} />,
    );
    expect(strip(busy.container.innerHTML)).toBe(sparseHtml);
  });

  it("holds for the Digests screen", () => {
    const entries = buildDigestEntries(sends, parents, IST, signals, pings);
    render(<Digests entries={entries} />);
    const text = renderedText();
    expect(text).toContain("day started normally");
    assertCopyLaw(text);
  });

  it("holds for the empty Digests state", () => {
    render(<Digests entries={[]} />);
    expect(renderedText()).toContain("Your daily digests will appear here.");
    assertCopyLaw(renderedText());
  });

  it("holds for the Family screen, and carries the privacy line verbatim", () => {
    render(
      <FamilyScreen
        parents={parents}
        members={members}
        familyTz={IST}
        setupEntries={setupEntries}
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
    assertCopyLaw(text);
  });

  it("holds for the no-family screen", () => {
    render(<NoFamily />);
    assertCopyLaw(renderedText());
  });

  it("would catch a regression", () => {
    expect(() => assertCopyLaw("Kettle: this is urgent")).toThrow();
    expect(() => assertCopyLaw("Amma opened WhatsApp 4 times")).toThrow();
  });
});

/**
 * AC5 — the exemption is a hole of a fixed shape in one wall, not a lower wall.
 */
describe("the tripwire view's scoped exemption", () => {
  const tripwirePings: Ping[] = [
    { parent_id: "p1", signal: "whatsapp", ts_utc: "2026-08-03T02:42:00Z" },
    { parent_id: "p1", signal: "device_alive", ts_utc: "2026-07-30T02:00:00Z" },
  ];
  const detailSignals: ParentSignal[] = [
    { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
    { parent_id: "p1", signal: "news", alarm_grade: true, active: true },
    { parent_id: "p1", signal: "device_alive", alarm_grade: false, active: true },
  ];

  function renderDetail() {
    const [parent] = parents;
    return render(
      <TripwireDetail
        glance={computeGlance(parent, IST, detailSignals, tripwirePings, NOON_IST, CHICAGO)}
        tripwires={computeTripwires(parent, IST, detailSignals, tripwirePings, NOON_IST)}
        onBack={() => undefined}
      />,
    );
  }

  it("holds for the tripwire view, with signal names allowed and nothing else", () => {
    renderDetail();
    const text = renderedText();
    // The exemption is being exercised, not passing on an empty render.
    expect(text).toContain("WhatsApp");
    expect(text).toContain("Daily Check");
    assertCopyLaw(text, TRIPWIRE_NAME_EXEMPTION);
  });

  it("still bans those same names on every other surface", () => {
    for (const name of ["WhatsApp", "YouTube", "News", "Charger On", "Daily Check"]) {
      expect(
        () => assertCopyLaw(`Last routine seen on ${name}`),
        `${name} escaped the law without an allowlist`,
      ).toThrow();
    }
    // And the surfaces themselves are asserted with no allowlist above — the
    // digest, glance and family tests call assertCopyLaw(text) unchanged.
  });

  it("exempts the names only, never the counting words that travel with them", () => {
    for (const smuggled of [
      "WhatsApp opened 4 times",
      "Daily Check streak",
      "News average this week",
      "WhatsApp — she may have fallen",
    ]) {
      expect(() => assertCopyLaw(smuggled, TRIPWIRE_NAME_EXEMPTION), smuggled).toThrow();
    }
  });

  it("is pinned to exactly the names the view can render", () => {
    // Add a signal to the app and this fails until the exemption is widened on
    // purpose — which is the only way a name should ever reach a screen.
    expect(new Set(Object.values(SIGNAL_DISPLAY_NAMES))).toEqual(
      new Set(TRIPWIRE_NAME_EXEMPTION.filter((e): e is string => typeof e === "string")),
    );
  });
});
