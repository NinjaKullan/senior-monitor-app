/**
 * @vitest-environment jsdom
 *
 * Spec 019 Amendment A, the webapp half: the consent screen says what can
 * be written when the request carries kettle:write and is unchanged
 * otherwise; the Family row says "can add notes" for a write grant; a line
 * dictated through an assistant is authored "{name} via {client}" wherever
 * an author is shown, with Edit and Delete as on any note of theirs.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { authorOf } from "@/components/NotesPanel";
import {
  ASSISTANTS_SINCE,
  ASSISTANTS_SINCE_WRITE,
  AUTHOR_VIA,
  CONNECT_BODY,
  CONNECT_BODY_WRITE,
  CONNECT_READ_ONLY,
  CONNECT_WRITE_NOTE,
} from "@/lib/copy";
import { ConnectScreen } from "@/screens/Connect";
import { FamilyScreen } from "@/screens/Family";
import { MemoryScreen } from "@/screens/Memory";
import type { AssistantGrant, JournalEntry } from "@/lib/types";

vi.mock("@/lib/supabase", () => ({ isConfigured: true, supabase: {} }));

const noop = async () => undefined;

describe("the consent screen (A.2)", () => {
  it("says what can be written for a write request", () => {
    render(
      <ConnectScreen
        state={{ kind: "ready", clientName: "Claude", names: ["Amma", "Appa"], write: true }}
        onAllow={noop}
        onCancel={noop}
      />,
    );
    expect(document.body.textContent).toContain(
      CONNECT_BODY_WRITE.replace("{client}", "Claude").replace("{names}", "Amma and Appa"),
    );
    expect(screen.getByTestId("connect-note")).toHaveTextContent(CONNECT_WRITE_NOTE);
    expect(document.body.textContent).not.toContain(CONNECT_READ_ONLY);
  });

  it("is unchanged for a read request", () => {
    render(
      <ConnectScreen state={{ kind: "ready", clientName: "Claude", names: ["Amma"] }} onAllow={noop} onCancel={noop} />,
    );
    expect(document.body.textContent).toContain(CONNECT_BODY.replace("{client}", "Claude").replace("{names}", "Amma"));
    expect(screen.getByTestId("connect-note")).toHaveTextContent(CONNECT_READ_ONLY);
    expect(document.body.textContent).not.toContain("add notes");
  });
});

describe("the Family row (A.2)", () => {
  const grant = (scope: string): AssistantGrant => ({
    id: `g-${scope}`,
    client_name: "Claude",
    created_utc: "2026-09-08T10:00:00Z",
    last_used_utc: "2026-09-08T10:00:00Z",
    revoked_utc: null,
    scope,
  });
  const shared = {
    parentStates: [],
    cities: {},
    members: [],
    viewerId: null,
    circle: { onAddSeat: noop, onRemoveSeat: noop, onSetRole: noop, onSetMail: noop, onLeave: noop },
    setupEntries: [],
    onOpen: () => undefined,
    onPickCity: noop,
    onClearCity: noop,
    viewerTz: "America/New_York",
  };

  it("says can add notes for a write grant and not for a read one", () => {
    render(<FamilyScreen {...shared} assistants={[grant("kettle:read"), grant("kettle:write")]} />);
    const rows = screen.getAllByTestId("assistant-grant").map((r) => r.textContent ?? "");
    expect(rows[0]).toContain(ASSISTANTS_SINCE.replace("{client}", "Claude").replace("{date}", "Sep 8"));
    expect(rows[0]).not.toContain("can add notes");
    expect(rows[1]).toContain(ASSISTANTS_SINCE_WRITE.replace("{client}", "Claude").replace("{date}", "Sep 8"));
  });
});

describe("the dictated line (A.4)", () => {
  const entry = (over: Partial<JournalEntry>): JournalEntry => ({
    id: 1,
    family_id: "f1",
    parent_id: null,
    author_label: "Hema",
    body: "Amma's doctor visit is Thursday",
    event_date: null,
    created_utc: "2026-09-08T14:00:00Z",
    kind: "note",
    parent_entry_id: null,
    author_member_id: "m1",
    edited_utc: null,
    via_client: null,
    ...over,
  });

  it("authors a via line as name via client, and a typed one as before", () => {
    expect(authorOf(entry({ via_client: "Claude" }))).toBe(AUTHOR_VIA.replace("{name}", "Hema").replace("{client}", "Claude"));
    expect(authorOf(entry({ via_client: "Claude" }))).toBe("Hema via Claude");
    expect(authorOf(entry({}))).toBe("Hema");
    expect(authorOf(entry({ author_label: "", via_client: "Codex" }))).toBe("Family via Codex");
  });

  it("renders the mark in Memory, on a note and on a reply, with Edit for its author", () => {
    const viewer = { memberId: "m1", admin: false };
    render(
      <MemoryScreen
        parentLabels={[{ parentId: "p1", label: "Amma" }]}
        journal={[
          entry({ via_client: "Claude" }),
          entry({ id: 2, body: "I'll call her tonight", parent_entry_id: 1, via_client: "Claude", created_utc: "2026-09-08T15:00:00Z" }),
          entry({ id: 3, body: "Typed", via_client: null, created_utc: "2026-09-07T15:00:00Z" }),
        ]}
        todayDate="2026-09-09"
        tz="America/New_York"
        onAddNote={noop}
        onAddReply={noop}
        viewer={viewer}
        onEdit={noop}
        onDelete={noop}
      />,
    );
    const text = document.body.textContent ?? "";
    expect(text.split("Hema via Claude").length - 1).toBe(2);
    expect(text).toContain("Sep 7 · Hema");
    expect(screen.getAllByTestId("edit-link").length).toBeGreaterThanOrEqual(2);
  });
});
