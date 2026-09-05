/**
 * @vitest-environment jsdom
 *
 * Spec 016 §6, the webapp half: the Reply link is on top-level family notes
 * only; the composer opens and closes; a reply renders indented under its
 * note, oldest first, dated on the family's day (251); filters carry replies
 * with their note and key on the note's written-at; the upcoming strip shows
 * the note alone.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { NotesPanel } from "@/components/NotesPanel";
import { MemoryScreen } from "@/screens/Memory";
import { REPLY_CANCEL, REPLY_LINK, REPLY_PLACEHOLDER, REPLY_SUBMIT } from "@/lib/copy";
import { canReply, filterEntries, splitThreads } from "@/lib/journal";
import type { JournalEntry } from "@/lib/types";

const TODAY = "2026-09-04";
const NY = "America/New_York";
const noop = async () => undefined;

const entry = (over: Partial<JournalEntry>): JournalEntry => ({
  id: 1,
  family_id: "f1",
  parent_id: null,
  author_label: "Hema",
  body: "Dr. Reed, Thursday 2pm",
  event_date: null,
  created_utc: "2026-08-20T10:00:00Z",
  kind: "note",
  parent_entry_id: null,
  ...over,
});

const note = entry({ id: 1, parent_id: "p1" });
const kettleLine = entry({ id: 2, author_label: "Kettle", body: "Amma is in Chennai now.", kind: "city_change" });
// Written 9:05pm New York on Aug 22 — Aug 23 in UTC (the 251 bug's shape).
const replyLate = entry({ id: 3, parent_entry_id: 1, author_label: "Priya", body: "Took her, all fine", created_utc: "2026-08-23T01:05:00Z" });
const replyEarly = entry({ id: 4, parent_entry_id: 1, author_label: "Arun", body: "I can drive", created_utc: "2026-08-21T12:00:00Z" });
const all = [note, kettleLine, replyLate, replyEarly];

function renderPanel(entries: JournalEntry[], onReply = vi.fn().mockResolvedValue(undefined)) {
  render(
    <NotesPanel entries={entries} todayDate={TODAY} tz={NY} onAdd={noop} onReply={onReply} fixedParentId={null} />,
  );
  return onReply;
}

describe("threads (spec 016)", () => {
  it("splits notes from replies and orders replies oldest first", () => {
    const { notes, repliesByNote } = splitThreads(all);
    expect(notes.map((n) => n.id)).toEqual([1, 2]);
    expect(repliesByNote.get(1)?.map((r) => r.id)).toEqual([4, 3]);
  });

  it("a reply can be written on a family note, never on a Kettle line or a reply", () => {
    expect(canReply(note)).toBe(true);
    expect(canReply(kettleLine)).toBe(false);
    expect(canReply(replyLate)).toBe(false);
  });
});

describe("the Reply link and composer", () => {
  it("renders on the note only, not on the Kettle line and not on replies", () => {
    renderPanel(all);
    expect(screen.getAllByTestId("reply-link")).toHaveLength(1);
    expect(screen.getByTestId("reply-link")).toHaveTextContent(REPLY_LINK);
    expect(screen.getAllByTestId("note-reply")).toHaveLength(2);
  });

  it("does not render at all when the screen offers no reply path", () => {
    render(<NotesPanel entries={all} todayDate={TODAY} tz={NY} onAdd={noop} fixedParentId={null} />);
    expect(screen.queryByTestId("reply-link")).toBeNull();
  });

  it("opens a one-line composer with the ruled words, and Not now closes it", () => {
    renderPanel(all);
    fireEvent.click(screen.getByTestId("reply-link"));
    const input = screen.getByTestId("reply-input") as HTMLInputElement;
    expect(input.placeholder).toBe(REPLY_PLACEHOLDER);
    expect(screen.getByTestId("reply-submit")).toHaveTextContent(REPLY_SUBMIT);
    expect(screen.getByTestId("reply-cancel")).toHaveTextContent(REPLY_CANCEL);
    expect(screen.queryByTestId("reply-link")).toBeNull();
    fireEvent.click(screen.getByTestId("reply-cancel"));
    expect(screen.queryByTestId("reply-composer")).toBeNull();
    expect(screen.getByTestId("reply-link")).toBeInTheDocument();
  });

  it("Esc closes it too", () => {
    renderPanel(all);
    fireEvent.click(screen.getByTestId("reply-link"));
    fireEvent.keyDown(screen.getByTestId("reply-input"), { key: "Escape" });
    expect(screen.queryByTestId("reply-composer")).toBeNull();
  });

  it("submits the body and the signed-as author against the note, then closes", async () => {
    const onReply = renderPanel([note]);
    fireEvent.click(screen.getByTestId("reply-link"));
    fireEvent.change(screen.getByTestId("reply-input"), { target: { value: "  Next visit Oct 2 " } });
    fireEvent.keyDown(screen.getByTestId("reply-input"), { key: "Enter" });
    await waitFor(() =>
      expect(onReply).toHaveBeenCalledWith({ parentEntryId: 1, body: "Next visit Oct 2", authorLabel: "" }),
    );
    await waitFor(() => expect(screen.queryByTestId("reply-composer")).toBeNull());
  });

  it("sends nothing for an empty reply", () => {
    const onReply = renderPanel([note]);
    fireEvent.click(screen.getByTestId("reply-link"));
    fireEvent.click(screen.getByTestId("reply-submit"));
    expect(onReply).not.toHaveBeenCalled();
  });
});

describe("how replies render", () => {
  it("indents them under their note, oldest first, with author and the family's day", () => {
    renderPanel(all);
    const replies = screen.getAllByTestId("note-reply");
    expect(replies[0]).toHaveTextContent("Aug 21 · Arun");
    expect(replies[0]).toHaveTextContent("I can drive");
    // 9:05pm New York on Aug 22 is Aug 23 in UTC; the label says Aug 22.
    expect(replies[1]).toHaveTextContent("Aug 22 · Priya");
    // Inside the note's own entry, not loose in the feed.
    const [noteEntry, lineEntry] = screen.getAllByTestId("note-entry");
    expect(noteEntry).toContainElement(replies[1]);
    expect(lineEntry).not.toContainElement(replies[1]);
  });

  it("the upcoming strip shows a note's replies beneath it (DECISIONS 277)", () => {
    const upcoming = entry({ id: 9, event_date: "2026-09-20", body: "Eye doctor" });
    const reply = entry({ id: 10, parent_entry_id: 9, author_label: "Arun", body: "I will drive" });
    renderPanel([upcoming, reply]);
    const strip = screen.getByTestId("upcoming-entry");
    expect(strip).toHaveTextContent("Eye doctor");
    expect(strip).toContainElement(screen.getByTestId("note-reply"));
    expect(screen.getByTestId("note-reply")).toHaveTextContent("Aug 20 · Arun");
    expect(screen.getByTestId("note-reply")).toHaveTextContent("I will drive");
    // The strip stays a strip: no Reply link and no list entry for it.
    expect(screen.queryByTestId("note-entry")).toBeNull();
  });
});

describe("filters carry replies with their note (§4)", () => {
  it("keys the timeframe on the note's written-at, not the replies'", () => {
    const oldNote = entry({ id: 20, created_utc: "2026-01-10T10:00:00Z" });
    const freshReply = entry({ id: 21, parent_entry_id: 20, created_utc: "2026-09-01T10:00:00Z" });
    // Three months back from Sep 4 excludes January: the note is out, and
    // its fresh reply goes with it rather than surfacing on its own.
    expect(filterEntries([oldNote, freshReply], TODAY, null, "3m", NY)).toEqual([]);
    // All time keeps both, note first then its reply.
    expect(filterEntries([oldNote, freshReply], TODAY, null, "all", NY).map((e) => e.id)).toEqual([20, 21]);
  });

  it("a parent filter keeps a note's replies with it on the Memory screen", () => {
    const appaNote = entry({ id: 30, parent_id: "p2", body: "Appa's glasses" });
    const appaReply = entry({ id: 31, parent_entry_id: 30, parent_id: "p2", body: "Picked up" });
    render(
      <MemoryScreen
        parentLabels={[{ parentId: "p1", label: "Amma" }, { parentId: "p2", label: "Appa" }]}
        journal={[note, replyLate, appaNote, appaReply]}
        todayDate={TODAY}
        tz={NY}
        onAddNote={noop}
        onAddReply={noop}
      />,
    );
    fireEvent.click(screen.getByRole("radio", { name: "Appa" }));
    expect(screen.getAllByTestId("note-entry")).toHaveLength(1);
    expect(screen.getByTestId("note-reply")).toHaveTextContent("Picked up");
    expect(screen.queryByText("Took her, all fine")).toBeNull();
  });
});
