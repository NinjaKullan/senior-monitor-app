/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146).
 */
/**
 * Memory v1.1 (spec 012 §9): the filters, the scroll, the fourth tab and the
 * sentence that stopped appearing twice.
 *
 * What is worth pinning here is mostly about what the family SEES rather than
 * what is stored: a default view that DECISIONS 211 ruled (All parents, three
 * months), a filter that hides notes without ever suggesting they are gone, a
 * composer that stays reachable however far back the list is scrolled, and a
 * tab label ruled verbatim.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

// Explicit, because several tests here render the same screen twice with
// different props and a leftover tree would let one assertion answer for the
// other's DOM.
afterEach(cleanup);
import { MemoryScreen } from "@/screens/Memory";
import { WhoToCallScreen } from "@/screens/WhoToCall";
import {
  CONTACT_TAG_EVERYONE,
  FILTER_ALL_PARENTS,
  FILTER_EMPTY,
  MEMORY_EMPTY,
  NOTES_SUB,
  TIMEFRAME_3_MONTHS,
  TIMEFRAME_6_MONTHS,
  TIMEFRAME_ALL,
  TIMEFRAME_THIS_MONTH,
  WHO_TO_CALL_TAB,
} from "@/lib/copy";
import {
  DEFAULT_PARENT_FILTER,
  DEFAULT_TIMEFRAME,
  filterEntries,
  timeframeStart,
} from "@/lib/journal";
import type { FamilyContact, JournalEntry } from "@/lib/types";

const TODAY = "2026-08-30";
const noop = async () => undefined;

let nextId = 1;
const entry = (over: Partial<JournalEntry>): JournalEntry => ({
  id: nextId++,
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
  id: nextId++,
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

const PARENTS = [
  { parentId: "p1", label: "Amma" },
  { parentId: "p2", label: "Appa" },
];

function renderMemory(over: Partial<Parameters<typeof MemoryScreen>[0]> = {}) {
  return render(
    <MemoryScreen
      parentLabels={PARENTS}
      journal={[]}
      todayDate={TODAY}
      onAddNote={noop}
      {...over}
    />,
  );
}

function renderWhoToCall(over: Partial<Parameters<typeof WhoToCallScreen>[0]> = {}) {
  return render(
    <WhoToCallScreen
      parentLabels={PARENTS}
      contacts={[]}
      onAddContact={noop}
      onUpdateContact={noop}
      onRemoveContact={noop}
      onMoveContact={noop}
      {...over}
    />,
  );
}

/* --- §9.1 the filters, as pure logic ------------------------------------- */

describe("the timeframe windows", () => {
  it("opens on All parents over three months (DECISIONS 211)", () => {
    expect(DEFAULT_PARENT_FILTER).toBe(null);
    expect(DEFAULT_TIMEFRAME).toBe("3m");
  });

  it("treats 'this month' as the calendar month, not the last thirty days", () => {
    // On the 2nd, a family filtering to this month wants the 1st — not five
    // weeks of history dressed up as "this month".
    expect(timeframeStart("2026-08-02", "month")).toBe("2026-08-01");
    expect(timeframeStart("2026-08-30", "month")).toBe("2026-08-01");
  });

  it("rolls the other windows back from today, and All has no floor", () => {
    expect(timeframeStart(TODAY, "3m")).toBe("2026-05-30");
    expect(timeframeStart(TODAY, "6m")).toBe("2026-02-28");
    expect(timeframeStart(TODAY, "all")).toBe(null);
  });

  it("filters by parent and by window together", () => {
    const entries = [
      entry({ parent_id: "p1", created_utc: "2026-08-24T10:00:00Z", body: "recent amma" }),
      entry({ parent_id: "p2", created_utc: "2026-08-24T10:00:00Z", body: "recent appa" }),
      entry({ parent_id: "p1", created_utc: "2026-01-04T10:00:00Z", body: "old amma" }),
    ];
    const bodies = (parent: string | null, tf: "month" | "3m" | "6m" | "all") =>
      filterEntries(entries, TODAY, parent, tf).map((e) => e.body);

    expect(bodies(null, "3m")).toEqual(["recent amma", "recent appa"]);
    expect(bodies("p1", "3m")).toEqual(["recent amma"]);
    expect(bodies("p1", "all")).toEqual(["recent amma", "old amma"]);
    expect(bodies(null, "all")).toHaveLength(3);
  });

  it("filters a Kettle line with the parent it is tagged to (§9.1)", () => {
    // The spec's own requirement: Kettle-authored lines carry their parent tag
    // and filter with the parent. Nothing here reads `kind` — the tag is the
    // only thing consulted, which is what makes that true by construction.
    const kettleLine = entry({
      parent_id: "p1",
      kind: "started",
      author_label: "Kettle",
      body: "kettle line",
    });
    const other = entry({ parent_id: "p2", body: "other" });
    expect(filterEntries([kettleLine, other], TODAY, "p1", "3m").map((e) => e.body)).toEqual([
      "kettle line",
    ]);
  });
});

/* --- §9.1 the filters, on screen ----------------------------------------- */

describe("the filters on the Memory screen", () => {
  it("offers the four windows in the spec's order", () => {
    renderMemory();
    const labels = within(screen.getByTestId("notes-time-filter"))
      .getAllByTestId("notes-time-filter-option")
      .map((n) => n.textContent);
    expect(labels).toEqual([
      TIMEFRAME_THIS_MONTH,
      TIMEFRAME_3_MONTHS,
      TIMEFRAME_6_MONTHS,
      TIMEFRAME_ALL,
    ]);
  });

  it("opens with three months chosen and All parents chosen", () => {
    renderMemory();
    const chosen = (testId: string) =>
      within(screen.getByTestId(testId))
        .getAllByTestId(`${testId}-option`)
        .find((n) => n.getAttribute("aria-checked") === "true")?.textContent;
    expect(chosen("notes-time-filter")).toBe(TIMEFRAME_3_MONTHS);
    expect(chosen("notes-parent-filter")).toBe(FILTER_ALL_PARENTS);
  });

  it("hides older notes until All-time is one tap away (DECISIONS 211)", () => {
    const journal = [
      entry({ created_utc: "2026-08-24T10:00:00Z", body: "inside the window" }),
      entry({ created_utc: "2026-01-04T10:00:00Z", body: "older than three months" }),
    ];
    renderMemory({ journal });
    expect(screen.queryByText("older than three months")).toBeNull();

    const allTime = within(screen.getByTestId("notes-time-filter"))
      .getAllByTestId("notes-time-filter-option")
      .find((n) => n.textContent === TIMEFRAME_ALL)!;
    fireEvent.click(allTime);
    expect(screen.getByText("older than three months")).toBeTruthy();
  });

  it("narrows to one parent when that chip is chosen", () => {
    const journal = [
      entry({ parent_id: "p1", body: "about Amma" }),
      entry({ parent_id: "p2", body: "about Appa" }),
    ];
    renderMemory({ journal });
    const amma = within(screen.getByTestId("notes-parent-filter"))
      .getAllByTestId("notes-parent-filter-option")
      .find((n) => n.textContent === "Amma")!;
    fireEvent.click(amma);
    expect(screen.getByText("about Amma")).toBeTruthy();
    expect(screen.queryByText("about Appa")).toBeNull();
  });

  it("says something different when a FILTER empties the feed, not the family", () => {
    // Two silences that must not read alike: a family with nothing written yet
    // gets the ruled line about first notes arriving on their own; a family
    // that filtered past its own history gets told the window is narrow.
    renderMemory({ journal: [] });
    expect(screen.getByTestId("memory-empty").textContent).toBe(MEMORY_EMPTY);

    cleanup();
    renderMemory({ journal: [entry({ created_utc: "2026-01-04T10:00:00Z" })] });
    expect(screen.getByTestId("memory-empty").textContent).toBe(FILTER_EMPTY);
  });

  it("hides the parent chips when there is only one parent to choose", () => {
    renderMemory({ parentLabels: [PARENTS[0]] });
    expect(screen.queryByTestId("notes-parent-filter")).toBeNull();
    expect(screen.getByTestId("notes-time-filter")).toBeTruthy();
  });
});

/* --- §9.2 the scroll ------------------------------------------------------ */

describe("the notes card scrolls inside itself", () => {
  it("scrolls the list and leaves the composer outside the scroll region", () => {
    renderMemory({ journal: [entry({}), entry({})] });
    const scroll = screen.getByTestId("notes-scroll");
    expect(scroll.style.overflowY).toBe("auto");
    expect(scroll.style.maxHeight).toBeTruthy();
    // The composer is pinned: reachable without scrolling the list back.
    expect(scroll.contains(screen.getByTestId("note-input"))).toBe(false);
    expect(scroll.contains(screen.getByTestId("note-submit"))).toBe(false);
  });

  it("keeps the month dividers INSIDE the scroll region (§9.2)", () => {
    renderMemory({
      journal: [
        entry({ created_utc: "2026-08-24T10:00:00Z" }),
        entry({ created_utc: "2026-07-04T10:00:00Z" }),
      ],
    });
    const scroll = screen.getByTestId("notes-scroll");
    const dividers = screen.getAllByTestId("month-separator");
    expect(dividers.length).toBeGreaterThan(1);
    for (const divider of dividers) expect(scroll.contains(divider)).toBe(true);
  });
});

/* --- §9.3 the fourth tab -------------------------------------------------- */

describe("Who to call", () => {
  it("carries the label DECISIONS 211 ruled, verbatim", () => {
    expect(WHO_TO_CALL_TAB).toBe("Who to call");
  });

  it("keeps the DECISIONS-200 heading on the page, and prints it once", () => {
    renderWhoToCall({ contacts: [contact({})] });
    expect(screen.getAllByText("If you can't reach them")).toHaveLength(1);
  });

  it("no longer renders the contacts sheet on Memory (§9.3)", () => {
    renderMemory({ journal: [entry({})] });
    expect(screen.queryByTestId("contacts-card")).toBeNull();
  });

  it("shows a household contact under every parent's filter", () => {
    // A neighbour with a key is who you call about either parent. Hiding that
    // row while filtered to one of them would be the list lying about who is
    // reachable.
    renderWhoToCall({
      contacts: [
        contact({ name: "Lakshmi", parent_id: null }),
        contact({ name: "Ravi", parent_id: "p2" }),
      ],
    });
    const amma = within(screen.getByTestId("contact-parent-filter"))
      .getAllByTestId("contact-parent-filter-option")
      .find((n) => n.textContent === "Amma")!;
    fireEvent.click(amma);
    expect(screen.getByText("Lakshmi")).toBeTruthy();
    expect(screen.queryByText("Ravi")).toBeNull();
  });

  it("names who each contact is for", () => {
    renderWhoToCall({
      contacts: [
        contact({ name: "Lakshmi", parent_id: null }),
        contact({ name: "Ravi", parent_id: "p1" }),
      ],
    });
    const tags = screen.getAllByTestId("contact-tag-label").map((n) => n.textContent);
    expect(tags).toEqual([CONTACT_TAG_EVERYONE, "Amma"]);
  });

  it("saves the parent a contact is tagged to", async () => {
    const onAddContact = vi.fn().mockResolvedValue(undefined);
    renderWhoToCall({ onAddContact });
    fireEvent.click(screen.getByTestId("contact-add"));
    fireEvent.change(screen.getByTestId("contact-name-input"), { target: { value: "Ravi" } });
    fireEvent.change(screen.getByTestId("contact-tag"), { target: { value: "p2" } });
    fireEvent.click(screen.getByTestId("contact-save"));
    await Promise.resolve();
    expect(onAddContact.mock.calls[0][0].parent_id).toBe("p2");
  });

  it("renders rows in the family's own rank order, not by id", () => {
    renderWhoToCall({
      contacts: [
        contact({ id: 50, name: "Second", position: 1 }),
        contact({ id: 10, name: "First", position: 0 }),
      ],
    });
    const names = screen.getAllByTestId("contact-row").map((row) => row.textContent ?? "");
    expect(names[0]).toContain("First");
    expect(names[1]).toContain("Second");
  });

  it("moves a row up and down the call order", async () => {
    const onMoveContact = vi.fn().mockResolvedValue(undefined);
    renderWhoToCall({
      contacts: [contact({ id: 10, position: 0 }), contact({ id: 50, position: 1 })],
      onMoveContact,
    });
    fireEvent.click(screen.getAllByTestId("contact-down")[0]);
    expect(onMoveContact).toHaveBeenCalledWith(10, 1);
    fireEvent.click(screen.getAllByTestId("contact-up")[1]);
    expect(onMoveContact).toHaveBeenCalledWith(50, -1);
  });
});

/* --- §9.4 the sentence that appeared twice -------------------------------- */

describe("the duplicated subtitle", () => {
  it("appears exactly once on Memory now", () => {
    renderMemory({ journal: [entry({})] });
    const page = screen.getByTestId("memory-screen").textContent ?? "";
    expect(page.split(NOTES_SUB).length - 1).toBe(1);
  });
});
