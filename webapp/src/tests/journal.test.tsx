/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * Family notes (spec 009 §4): scoping, the Upcoming strip, and — the one that
 * carries a security property — linkification over ESCAPED text. A note body
 * is family-authored content; it must never become markup, only text nodes
 * and anchors the panel itself builds.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { NotesPanel } from "@/components/NotesPanel";
import { MemoryScreen } from "@/screens/Memory";
import { firstLine, linkify, monthDay, pastEntries, upcomingEntries, weekdayMonthDay } from "@/lib/journal";
import { computeParentToday } from "@/lib/parentState";
import type { JournalEntry, Parent, ParentSignal, Ping } from "@/lib/types";

const TODAY = "2026-08-26";

const entry = (over: Partial<JournalEntry>): JournalEntry => ({
  id: Math.floor(Math.random() * 1e6),
  family_id: "f1",
  parent_id: null,
  author_label: "",
  body: "a note",
  event_date: null,
  created_utc: "2026-08-24T10:00:00Z",
  kind: "note",
  parent_entry_id: null,
  author_member_id: null,
  edited_utc: null,
  ...over,
});

const noop = async () => undefined;

describe("linkify, over escaped text", () => {
  it("splits https, http and bare domains into anchors", () => {
    const segments = linkify("Portal notes here: apollo247.com/visit/8823 and https://amazon.in/gp/order/2841");
    const links = segments.filter((s) => s.kind === "link");
    expect(links).toEqual([
      { kind: "link", href: "https://apollo247.com/visit/8823", label: "apollo247.com/visit/8823" },
      { kind: "link", href: "https://amazon.in/gp/order/2841", label: "https://amazon.in/gp/order/2841" },
    ]);
  });

  it("does not linkify prose abbreviations or bare words", () => {
    for (const text of ["e.g. tomorrow", "Dr. Raman moved the review", "at 7 in the morning"]) {
      expect(linkify(text).every((s) => s.kind === "text"), text).toBe(true);
    }
  });

  it("renders a body containing <script> inert — text, never markup", () => {
    render(
      <NotesPanel
        entries={[entry({ id: 1, body: '<script>alert(1)</script> see kettle.example/x' })]}
        todayDate={TODAY}
        tz="America/New_York"
        onAdd={noop}
        fixedParentId={null}
      />,
    );
    // The tag arrives as visible TEXT (escaped by construction)…
    expect(document.body.textContent).toContain("<script>alert(1)</script>");
    // …and never as an element; the only anchor is the one linkify built.
    expect(document.querySelector("script")).toBeNull();
    const anchor = document.querySelector('[data-testid="note-entry"] a')!;
    expect(anchor.getAttribute("href")).toBe("https://kettle.example/x");
    expect(anchor.getAttribute("target")).toBe("_blank");
    expect(anchor.getAttribute("rel")).toBe("noopener noreferrer");
  });

  it("a body cannot smuggle an href of its own", () => {
    render(
      <NotesPanel
        entries={[entry({ id: 2, body: '<a href="https://evil.example">click</a>' })]}
        todayDate={TODAY}
        tz="America/New_York"
        onAdd={noop}
        fixedParentId={null}
      />,
    );
    // evil.example appears only where linkify put it — as a label and its
    // derived href — never as an element the body authored.
    const anchors = [...document.querySelectorAll('[data-testid="note-entry"] a')];
    for (const a of anchors) expect(a.textContent).not.toBe("click");
  });
});

describe("the Upcoming strip and entry metadata", () => {
  const entries = [
    entry({ id: 1, body: "Hearing aid batteries arrive", created_utc: "2026-08-24T10:00:00Z" }),
    entry({ id: 2, body: "Eye doctor", event_date: "2026-09-01", author_label: "Hema", created_utc: "2026-08-20T10:00:00Z" }),
    entry({ id: 3, body: "Water filter service", event_date: "2026-09-10", created_utc: "2026-08-25T10:00:00Z" }),
    entry({ id: 4, body: "Old visit", event_date: "2026-08-20", author_label: "Ravi", created_utc: "2026-08-21T10:00:00Z" }),
  ];

  it("floats today-or-later events to the top, soonest first", () => {
    const up = upcomingEntries(entries, TODAY);
    expect(up.map((e) => e.id)).toEqual([2, 3]);
    expect(pastEntries(entries, TODAY).map((e) => e.id)).toEqual([1, 4]);
  });

  it("renders the strip as ruled: Upcoming · first line on Weekday, Mon D · added by author", () => {
    render(
      <NotesPanel entries={entries} todayDate={TODAY} tz="America/New_York" onAdd={noop} fixedParentId={null} />,
    );
    const strips = screen.getAllByTestId("upcoming-entry").map((n) => n.textContent);
    expect(strips[0]).toBe("Upcoming · Eye doctor on Tue, Sep 1 · added by Hema");
    // An empty author renders as the family itself.
    expect(strips[1]).toBe("Upcoming · Water filter service on Thu, Sep 10 · added by Family");
  });

  it("renders a past event inline in the metadata, not in the strip", () => {
    render(
      <NotesPanel entries={entries} todayDate={TODAY} tz="America/New_York" onAdd={noop} fixedParentId={null} />,
    );
    const metas = screen.getAllByTestId("note-meta").map((n) => n.textContent);
    expect(metas).toContain("Aug 21 · Ravi · for Aug 20");
  });

  it("formats dates at UTC so a calendar date never slips a day", () => {
    expect(monthDay("2026-09-01")).toBe("Sep 1");
    expect(weekdayMonthDay("2026-09-01")).toBe("Tue, Sep 1");
    expect(firstLine("line one\nline two")).toBe("line one");
  });
});

describe("scoping (spec 009 §4)", () => {
  const bare = {
    tz: null,
    phone_e164: null,
    whatsapp_e164: null,
    relationship: null,
    city_label: null,
    tz_changed_utc: null, paused_until: null, paused_since: null,
  };
  const mom: Parent = { id: "p1", family_id: "f1", display_name: "Amma", ...bare, relationship: "Mom" };
  const dad: Parent = { id: "p2", family_id: "f1", display_name: "Appa", ...bare, relationship: "Dad" };
  const signals: ParentSignal[] = [
    { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
    { parent_id: "p2", signal: "whatsapp", alarm_grade: true, active: true },
  ];
  const pings: Ping[] = [
    { parent_id: "p1", signal: "whatsapp", ts_utc: "2026-08-26T02:00:00Z" },
    { parent_id: "p2", signal: "whatsapp", ts_utc: "2026-08-26T02:00:00Z" },
  ];
  const NOW = new Date("2026-08-26T06:30:00Z");
  const states = [mom, dad].map((p) =>
    computeParentToday(p, "Asia/Kolkata", signals, pings, pings, NOW, "America/Chicago"),
  );

  const journal = [
    entry({ id: 1, parent_id: "p1", body: "About Mom" }),
    entry({ id: 2, parent_id: "p2", body: "About Dad" }),
    entry({ id: 3, parent_id: null, body: "About the family" }),
  ];

  it("the Memory screen consolidates all entries and tags each one (spec 012)", () => {
    render(
      <MemoryScreen
        parentLabels={states.map((s) => ({ parentId: s.parentId, label: s.label }))}
        journal={journal}
        todayDate={TODAY}
        tz="America/New_York"
        onAddNote={noop}
      />,
    );
    const metas = screen.getAllByTestId("note-meta").map((n) => n.textContent ?? "");
    expect(metas.some((m) => m.startsWith("Amma · "))).toBe(true);
    expect(metas.some((m) => m.startsWith("Appa · "))).toBe(true);
    // The null tag renders as "Family".
    expect(metas.some((m) => m.startsWith("Family · "))).toBe(true);
    // And the composer's tag is selectable, by display name (DECISIONS 183).
    const tag = screen.getByTestId("note-input");
    fireEvent.focus(tag);
    const options = [...screen.getByTestId("note-tag").querySelectorAll("option")].map(
      (o) => o.textContent,
    );
    expect(options).toEqual(["Amma", "Appa", "Family"]);
  });

  it("a note added from a parent page defaults to that parent", async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined);
    render(
      <NotesPanel entries={[]} todayDate={TODAY} tz="America/New_York" onAdd={onAdd} fixedParentId="p1" />,
    );
    fireEvent.change(screen.getByTestId("note-input"), { target: { value: "Hearing aid" } });
    fireEvent.click(screen.getByTestId("note-submit"));
    expect(onAdd).toHaveBeenCalledWith({
      parentId: "p1",
      body: "Hearing aid",
      authorLabel: "",
      eventDate: null,
    });
  });

  it("remembers the signed-as value for the next note", async () => {
    localStorage.removeItem("kettle-signed-as");
    const onAdd = vi.fn().mockResolvedValue(undefined);
    const first = render(
      <NotesPanel entries={[]} todayDate={TODAY} tz="America/New_York" onAdd={onAdd} fixedParentId={null} />,
    );
    fireEvent.focus(screen.getByTestId("note-input"));
    fireEvent.change(screen.getByTestId("note-author"), { target: { value: "Hema" } });
    fireEvent.change(screen.getByTestId("note-input"), { target: { value: "x" } });
    fireEvent.click(screen.getByTestId("note-submit"));
    expect(onAdd).toHaveBeenCalledWith(
      expect.objectContaining({ authorLabel: "Hema" }),
    );
    first.unmount();

    render(<NotesPanel entries={[]} todayDate={TODAY} tz="America/New_York" onAdd={onAdd} fixedParentId={null} />);
    fireEvent.focus(screen.getByTestId("note-input"));
    expect((screen.getByTestId("note-author") as HTMLInputElement).value).toBe("Hema");
  });
});
