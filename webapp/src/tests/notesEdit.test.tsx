/**
 * @vitest-environment jsdom
 *
 * Spec 018 §6, the webapp half: Edit and Delete only where allowed; inline
 * edit; the confirm lines; the edited mark; the optimistic composer that
 * locks and never fires twice; failure restoring the text; and dates on the
 * VIEWER's clock — 03:30Z is yesterday in New York and today in Kolkata.
 */
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, type Mock } from "vitest";
import { NotesPanel } from "@/components/NotesPanel";
import {
  COMPOSER_FAILED,
  DELETE_NOTE_CONFIRM,
  DELETE_REPLY_CONFIRM,
  EDITED_MARK,
} from "@/lib/copy";
import { canDelete, canEdit } from "@/lib/journal";
import type { JournalEntry } from "@/lib/types";

const TODAY = "2026-09-05";
const noop = async () => undefined;
const ME = "seat-me";
const THEM = "seat-them";

const entry = (over: Partial<JournalEntry>): JournalEntry => ({
  id: 1,
  family_id: "f1",
  parent_id: null,
  author_label: "Hema",
  body: "Dr. Reed, Thursday 2pm",
  event_date: null,
  created_utc: "2026-09-01T10:00:00Z",
  kind: "note",
  parent_entry_id: null,
  author_member_id: ME,
  edited_utc: null,
  ...over,
});

const mine = entry({ id: 1 });
const theirs = entry({ id: 2, author_label: "Priya", author_member_id: THEM, body: "Glasses ordered" });
const legacy = entry({ id: 3, author_member_id: null, body: "from before" });
const kettle = entry({ id: 4, author_label: "Kettle", author_member_id: null, kind: "city_change", body: "Amma is in Chennai now." });
const myReply = entry({ id: 5, parent_entry_id: 2, body: "I can drive" });

const member = { memberId: ME, admin: false };
const admin = { memberId: ME, admin: true };

type Handlers = { onAdd: Mock; onReply: Mock; onEdit: Mock; onDelete: Mock };

function renderPanel(
  entries: JournalEntry[],
  viewer = member,
  handlers: Partial<Handlers> = {},
  tz = "America/New_York",
) {
  const h = {
    onAdd: vi.fn().mockResolvedValue(undefined),
    onReply: vi.fn().mockResolvedValue(undefined),
    onEdit: vi.fn().mockResolvedValue(undefined),
    onDelete: vi.fn().mockResolvedValue(undefined),
    ...handlers,
  };
  render(
    <NotesPanel
      entries={entries}
      todayDate={TODAY}
      tz={tz}
      onAdd={h.onAdd}
      onReply={h.onReply}
      viewer={viewer}
      onEdit={h.onEdit}
      onDelete={h.onDelete}
      fixedParentId={null}
    />,
  );
  return h;
}

describe("who may edit and delete (spec 018 §2)", () => {
  it("the author edits and deletes their own; a member touches nothing else", () => {
    expect([canEdit(mine, member), canDelete(mine, member)]).toEqual([true, true]);
    expect([canEdit(theirs, member), canDelete(theirs, member)]).toEqual([false, false]);
    expect([canEdit(legacy, member), canDelete(legacy, member)]).toEqual([false, false]);
    expect([canEdit(kettle, member), canDelete(kettle, member)]).toEqual([false, false]);
  });

  it("an admin deletes anyone's, edits nobody else's, and owns legacy rows; Kettle lines never", () => {
    expect([canEdit(theirs, admin), canDelete(theirs, admin)]).toEqual([false, true]);
    expect([canEdit(legacy, admin), canDelete(legacy, admin)]).toEqual([true, true]);
    expect([canEdit(kettle, admin), canDelete(kettle, admin)]).toEqual([false, false]);
  });

  it("renders the links only where allowed", () => {
    renderPanel([mine, theirs, legacy, kettle, myReply], member);
    // mine: Edit + Delete; my reply: Edit + Delete; theirs, legacy, kettle: none.
    expect(screen.getAllByTestId("edit-link")).toHaveLength(2);
    expect(screen.getAllByTestId("delete-link")).toHaveLength(2);
  });

  it("renders nothing at all without a viewer", () => {
    render(<NotesPanel entries={[mine]} todayDate={TODAY} tz="UTC" onAdd={noop} fixedParentId={null} />);
    expect(screen.queryByTestId("edit-link")).toBeNull();
    expect(screen.queryByTestId("delete-link")).toBeNull();
  });
});

describe("inline edit and the confirm lines (§4)", () => {
  it("edits inline, prefilled, and saves the trimmed text", async () => {
    const h = renderPanel([mine]);
    fireEvent.click(screen.getByTestId("edit-link"));
    const input = screen.getByTestId("edit-input") as HTMLInputElement;
    expect(input.value).toBe("Dr. Reed, Thursday 2pm");
    fireEvent.change(input, { target: { value: " Dr. Reed, Thursday 3pm " } });
    fireEvent.click(screen.getByTestId("edit-save"));
    await waitFor(() => expect(h.onEdit).toHaveBeenCalledWith(1, "Dr. Reed, Thursday 3pm"));
    await waitFor(() => expect(screen.queryByTestId("edit-composer")).toBeNull());
  });

  it("Not now closes the editor with nothing saved", () => {
    const h = renderPanel([mine]);
    fireEvent.click(screen.getByTestId("edit-link"));
    fireEvent.click(screen.getByTestId("edit-cancel"));
    expect(screen.queryByTestId("edit-composer")).toBeNull();
    expect(h.onEdit).not.toHaveBeenCalled();
  });

  it("deleting a note asks about its replies; deleting a reply asks about the reply", async () => {
    const h = renderPanel([theirs, myReply], admin);
    const [noteLink, replyLink] = screen.getAllByTestId("delete-link");
    fireEvent.click(noteLink);
    expect(screen.getByTestId("delete-confirm")).toHaveTextContent(DELETE_NOTE_CONFIRM);
    fireEvent.click(screen.getByTestId("delete-cancel"));
    expect(screen.queryByTestId("delete-confirm")).toBeNull();
    fireEvent.click(replyLink);
    expect(screen.getByTestId("delete-confirm")).toHaveTextContent(DELETE_REPLY_CONFIRM);
    fireEvent.click(screen.getByTestId("delete-yes"));
    await waitFor(() => expect(h.onDelete).toHaveBeenCalledWith(5));
    expect(h.onDelete).toHaveBeenCalledTimes(1);
  });

  it("marks an edited entry beside its date", () => {
    renderPanel([entry({ edited_utc: "2026-09-02T10:00:00Z" })]);
    expect(screen.getByTestId("note-meta")).toHaveTextContent(`Sep 1 · ${EDITED_MARK} · Hema`);
    renderPanel([mine]);
  });
});

describe("the optimistic composer (§2)", () => {
  function deferred() {
    let resolve!: () => void;
    let reject!: (e: Error) => void;
    const promise = new Promise<void>((res, rej) => {
      resolve = res;
      reject = rej;
    });
    return { promise, resolve, reject };
  }

  it("shows the row at once, locks, and Enter then Add produce one call", async () => {
    const gate = deferred();
    const h = renderPanel([], member, { onAdd: vi.fn(() => gate.promise) });
    const input = screen.getByTestId("note-input") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Picked up the glasses" } });
    // Enter, then Add, then Enter again, in ONE batch: no re-render between
    // them, so the disabled attribute and the cleared field have not landed
    // yet and only the lock itself can stop the second and third fire. This
    // is the founder's double post (DECISIONS 280) at its fastest.
    act(() => {
      fireEvent.keyDown(input, { key: "Enter" });
      fireEvent.click(screen.getByTestId("note-submit"));
      fireEvent.keyDown(input, { key: "Enter" });
    });
    // Before the server answers: one pending row, an empty locked composer.
    const row = screen.getByTestId("note-entry");
    expect(row.getAttribute("data-pending")).toBe("true");
    expect(row).toHaveTextContent("Picked up the glasses");
    expect(input.value).toBe("");
    expect(input.disabled).toBe(true);
    expect((screen.getByTestId("note-submit") as HTMLButtonElement).disabled).toBe(true);
    expect(h.onAdd).toHaveBeenCalledTimes(1);
    await act(async () => {
      gate.resolve();
      await gate.promise;
    });
    await waitFor(() => expect(input.disabled).toBe(false));
    expect(screen.queryByTestId("note-entry")).toBeNull(); // the real row arrives via refresh
  });

  it("on failure removes the row and returns the text with the failure line", async () => {
    const h = renderPanel([], member, { onAdd: vi.fn().mockRejectedValue(new Error("500")) });
    const input = screen.getByTestId("note-input") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "Picked up the glasses" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("composer-failed")).toHaveTextContent(COMPOSER_FAILED));
    expect(input.value).toBe("Picked up the glasses");
    expect(input.disabled).toBe(false);
    expect(screen.queryByTestId("note-entry")).toBeNull();
    expect(h.onAdd).toHaveBeenCalledTimes(1);
  });

  it("a reply is optimistic too, under its note, and fires once", async () => {
    const gate = deferred();
    const h = renderPanel([theirs], member, { onReply: vi.fn(() => gate.promise) });
    fireEvent.click(screen.getByTestId("reply-link"));
    const input = screen.getByTestId("reply-input") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "On my way" } });
    act(() => {
      fireEvent.keyDown(input, { key: "Enter" });
      fireEvent.keyDown(input, { key: "Enter" });
    });
    const reply = screen.getByTestId("note-reply");
    expect(reply.getAttribute("data-pending")).toBe("true");
    expect(reply).toHaveTextContent("On my way");
    expect(h.onReply).toHaveBeenCalledTimes(1);
    await act(async () => {
      gate.resolve();
      await gate.promise;
    });
    await waitFor(() => expect(screen.queryByTestId("note-reply")).toBeNull());
  });
});

describe("dates on the viewer's clock (§2, DECISIONS 279)", () => {
  const reply = entry({ id: 9, parent_entry_id: 2, created_utc: "2026-09-05T03:30:00Z", body: "written late" });

  it("03:30Z is the day before in New York and the same day in Kolkata", () => {
    renderPanel([theirs, reply], member, {}, "America/New_York");
    expect(screen.getByTestId("reply-meta")).toHaveTextContent("Sep 4");
  });

  it("…and Sep 5 for a viewer in Kolkata", () => {
    renderPanel([theirs, reply], member, {}, "Asia/Kolkata");
    expect(screen.getByTestId("reply-meta")).toHaveTextContent("Sep 5");
  });
});
