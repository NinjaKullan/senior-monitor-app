/**
 * AC4 — the copy law, extended to rendered UI.
 *
 * The law that governs SMS governs pixels too: what a family reads on a screen
 * at an anxious moment is the same product promise as what arrives in a text.
 * So this renders all three screens with realistic data and walks the resulting
 * DOM text, not the source.
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
const NOW = new Date("2026-08-03T06:30:00Z");

const parents: Parent[] = [
  { id: "p1", family_id: "f1", display_name: "Amma", tz: null },
  { id: "p2", family_id: "f1", display_name: "Appa", tz: null },
];
const members: Member[] = [
  { id: "m1", family_id: "f1", display_name: "Hema", role: "owner", digest_channel: "sms" },
];
const signals: ParentSignal[] = parents.map((p) => ({
  parent_id: p.id,
  signal: "whatsapp",
  alarm_grade: true,
  active: true,
}));
const pings: Ping[] = [{ parent_id: "p1", signal: "whatsapp", ts_utc: "2026-08-03T02:42:00Z" }];
const sends: DigestSend[] = [
  { parent_id: "p1", kind: "morning", local_date: "2026-08-03", ts_utc: "2026-08-03T03:00:00Z" },
  { parent_id: "p1", kind: "evening", local_date: "2026-08-02", ts_utc: "2026-08-02T15:00:00Z" },
];

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

/** Digits are allowed only inside a clock time or an ISO date. */
function strayDigits(text: string): string {
  return text
    .replace(/\b\d{1,2}:\d{2}\s?[ap]m\b/gi, "")
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
    const states = parents.map((p) => computeGlance(p, IST, signals, pings, NOW));
    render(<Glance states={states} />);
    const text = renderedText();
    // Both states really are on screen — this is not passing on an empty render.
    expect(text).toContain("All normal");
    expect(text).toContain("Quiet so far");
    assertCopyLaw(text);
  });

  it("never renders anything darker than Quiet so far", () => {
    const states = parents.map((p) => computeGlance(p, IST, signals, [], NOW));
    render(<Glance states={states} />);
    const statuses = screen.getAllByTestId("glance-status").map((n) => n.textContent);
    expect(new Set(statuses)).toEqual(new Set(["Quiet so far"]));
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
