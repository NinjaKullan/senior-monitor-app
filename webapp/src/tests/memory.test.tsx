/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * The Memory tab (spec 012): the journal promoted to a place, the contacts
 * sheet beside it. What is worth pinning: the month separators that turn a
 * list into a record (consolidated feed ONLY — the parent panel stays as it
 * was), the ruled empty state, the contacts card's tap-to-call shape (E.164
 * in the href, the display string as the one sanctioned phone-as-text), and
 * the nav gaining its third tab without the Family screen keeping a copy of
 * the feed.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { NotesPanel } from "@/components/NotesPanel";
import { ContactsCard } from "@/components/ContactsCard";
import { MemoryScreen } from "@/screens/Memory";
import { telHrefNumber } from "@/lib/data";
import { CONTACT_SUGGESTED_LABELS, MEMORY_EMPTY } from "@/lib/copy";
import type { FamilyContact, JournalEntry } from "@/lib/types";

const TODAY = "2026-08-30";
const noop = async () => undefined;

const entry = (over: Partial<JournalEntry>): JournalEntry => ({
  id: Math.floor(Math.random() * 1e6),
  family_id: "f1",
  parent_id: null,
  author_label: "Hema",
  body: "a note",
  event_date: null,
  created_utc: "2026-08-24T10:00:00Z",
  kind: "note",
  ...over,
});

const contact = (over: Partial<FamilyContact>): FamilyContact => ({
  id: 1,
  family_id: "f1",
  parent_id: null,
  label: "A neighbor",
  name: "Lakshmi",
  phone_e164: "+919845550111",
  phone_display: "98455 50111",
  note: "",
  position: 0,
  ...over,
});

function renderMemory(over: Partial<Parameters<typeof MemoryScreen>[0]> = {}) {
  return render(
    <MemoryScreen
      parentLabels={[{ parentId: "p1", label: "Amma" }]}
      journal={[]}
      contacts={[]}
      todayDate={TODAY}
      onAddNote={noop}
      onAddContact={noop}
      onUpdateContact={noop}
      onRemoveContact={noop}
      {...over}
    />,
  );
}

describe("month separators (spec 012 §2)", () => {
  const feed = [
    entry({ id: 1, created_utc: "2026-08-24T10:00:00Z" }),
    entry({ id: 2, created_utc: "2026-08-02T10:00:00Z" }),
    entry({ id: 3, created_utc: "2026-07-30T10:00:00Z" }),
  ];

  it("turns the consolidated list into a record, one heading per month", () => {
    renderMemory({ journal: feed });
    const separators = screen.getAllByTestId("month-separator").map((n) => n.textContent);
    // One per month, not one per entry: the two August notes share a heading.
    expect(separators).toEqual(["August 2026", "July 2026"]);
  });

  it("stays out of the parent panel, which spec 012 leaves unchanged", () => {
    render(<NotesPanel entries={feed} todayDate={TODAY} onAdd={noop} fixedParentId="p1" />);
    expect(screen.queryAllByTestId("month-separator")).toEqual([]);
  });
});

describe("the empty state", () => {
  it("shows the ruled line, verbatim, only when there is nothing yet", () => {
    const empty = renderMemory();
    expect(screen.getByTestId("memory-empty").textContent).toBe(MEMORY_EMPTY);
    expect(MEMORY_EMPTY).toBe(
      "Notes from your family and from Kettle live here. The first ones arrive on their own.",
    );
    empty.unmount();

    renderMemory({ journal: [entry({})] });
    expect(screen.queryByTestId("memory-empty")).toBeNull();
  });
});

describe("the contacts card (spec 012 §4)", () => {
  it("renders a row as label, name, and a tap-to-call number", () => {
    renderMemory({ contacts: [contact({ note: "Two doors down" })] });
    expect(screen.getByText("If you can't reach them")).toBeTruthy();
    expect(screen.getByTestId("contact-label").textContent).toBe("A neighbor");
    const phone = screen.getByTestId("contact-phone");
    // E.164 dials; the display string is what a person sees — the ONE
    // sanctioned phone-as-text in the app, scoped to this testid.
    expect(phone.getAttribute("href")).toBe("tel:+919845550111");
    expect(phone.textContent).toBe("98455 50111");
    expect(screen.getByText("Two doors down")).toBeTruthy();
  });

  it("offers the printable's suggested rows as placeholders, never as rows", () => {
    renderMemory();
    // Nothing pre-inserted: the family owns every line (DECISIONS 200).
    expect(screen.queryAllByTestId("contact-row")).toEqual([]);
    fireEvent.click(screen.getByTestId("contact-add"));
    expect(screen.getByTestId("contact-label-input").getAttribute("placeholder")).toBe(
      "A neighbor",
    );
    expect(CONTACT_SUGGESTED_LABELS).toEqual([
      "A neighbor",
      "Someone in the family nearby",
      "Their building or front desk",
      "Their doctor",
    ]);
  });

  it("saves a new contact with the number normalized beside the typed form", async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined);
    render(
      <ContactsCard contacts={[]} onAdd={onAdd} onUpdate={noop} onRemove={noop} />,
    );
    fireEvent.click(screen.getByTestId("contact-add"));
    fireEvent.change(screen.getByTestId("contact-label-input"), { target: { value: "Their doctor" } });
    fireEvent.change(screen.getByTestId("contact-name-input"), { target: { value: "Dr. Rao" } });
    fireEvent.change(screen.getByTestId("contact-phone-input"), { target: { value: "+1 (984) 370-4452" } });
    fireEvent.click(screen.getByTestId("contact-save"));
    await Promise.resolve();
    expect(onAdd).toHaveBeenCalledWith({
      label: "Their doctor",
      name: "Dr. Rao",
      phone_display: "+1 (984) 370-4452",
      phone_e164: "+19843704452",
      note: "",
    });
  });

  it("edits and removes — contacts are reference data, not record", async () => {
    const onUpdate = vi.fn().mockResolvedValue(undefined);
    const onRemove = vi.fn().mockResolvedValue(undefined);
    render(
      <ContactsCard
        contacts={[contact({ id: 7 })]}
        onAdd={noop}
        onUpdate={onUpdate}
        onRemove={onRemove}
      />,
    );
    fireEvent.click(screen.getByTestId("contact-edit"));
    fireEvent.change(screen.getByTestId("contact-name-input"), { target: { value: "Lakshmi R" } });
    fireEvent.click(screen.getByTestId("contact-save"));
    expect(onUpdate).toHaveBeenCalledWith(7, expect.objectContaining({ name: "Lakshmi R" }));

    // The row view returns once the save settles.
    fireEvent.click(await screen.findByTestId("contact-remove"));
    expect(onRemove).toHaveBeenCalledWith(7);
  });
});

describe("the number normalizer", () => {
  it("keeps a leading plus, drops everything that is not a digit", () => {
    expect(telHrefNumber("+1 (984) 370-4452")).toBe("+19843704452");
    expect(telHrefNumber("98455 50111")).toBe("9845550111");
    expect(telHrefNumber("  +91 98455-50111 ")).toBe("+919845550111");
  });
});

describe("the nav and the slimmed Family screen, pinned at the source", () => {
  it("Memory sits between Today and Family, and Family keeps no feed", async () => {
    const fs = await import("node:fs");
    const app = fs.readFileSync("src/App.tsx", "utf8");
    const tabs = app.slice(app.indexOf("const TABS"), app.indexOf("];", app.indexOf("const TABS")));
    expect(tabs.indexOf('"today"')).toBeGreaterThan(-1);
    expect(tabs.indexOf('"today"')).toBeLessThan(tabs.indexOf('"memory"'));
    expect(tabs.indexOf('"memory"')).toBeLessThan(tabs.indexOf('"family"'));
    expect(tabs).toContain('label: "Memory"');
    // The Family render carries no journal prop and no notes panel: the feed
    // lives in ONE place now.
    const familyRender = app.slice(app.indexOf("<FamilyScreen"), app.indexOf("/>", app.indexOf("<FamilyScreen")));
    expect(familyRender).not.toContain("journal");
    const familyScreen = fs.readFileSync("src/screens/Family.tsx", "utf8");
    expect(familyScreen).not.toContain("NotesPanel");
  });
});
