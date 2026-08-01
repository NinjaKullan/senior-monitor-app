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
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Digests } from "@/screens/Digests";
import { FamilyScreen } from "@/screens/Family";
import { Glance } from "@/screens/Glance";
import { NoFamily } from "@/screens/NoFamily";
import { buildDigestEntries } from "@/lib/digests";
import { computeGlance } from "@/lib/glance";
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
const BANNED = [...URGENCY, ...MEDICAL, ...PROFILE];
const NAMES = ["Amma", "Appa", "Hema", "Kettle"];

const CLOCK = /\b\d{1,2}:\d{2}\s?[ap]m\b/gi;

/** Digits are allowed only inside a clock time or an ISO date. */
function strayDigits(text: string): string {
  return text
    .replace(CLOCK, "")
    .replace(/\b\d{4}-\d{2}-\d{2}\b/g, "")
    .replace(/[^\d]/g, "");
}

function assertCopyLaw(text: string) {
  let scanned = text;
  for (const name of NAMES) scanned = scanned.split(name).join("«name»");
  const lowered = scanned.toLowerCase();
  for (const word of BANNED) {
    expect(
      new RegExp(`\\b${word}\\b`).test(lowered),
      `"${word}" appeared in rendered output: ${text}`,
    ).toBe(false);
  }
  expect(strayDigits(scanned), `stray digits in: ${text}`).toBe("");
}

function renderedText(): string {
  return document.body.textContent ?? "";
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
    render(<FamilyScreen parents={parents} members={members} familyTz={IST} />);
    const text = renderedText();
    expect(screen.getByTestId("privacy-footer")).toHaveTextContent(PRIVACY_FOOTER);
    // `sms` is a channel name, not a signal name — allowed, and worth pinning.
    expect(text).toContain("sms");
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
