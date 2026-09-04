/**
 * @vitest-environment jsdom
 *
 * Spec 015 §12, the webapp half: the switcher is hidden for one circle and
 * shown for two; the chosen id scopes every read and is remembered; the seats
 * list renders roles and the pending state; admin controls render for admins
 * and for nobody else; the refusals a person can act on become §9's words.
 */
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FamilyScreen } from "@/screens/Family";
import { chooseFamily, type FamilySnapshot } from "@/lib/data";
import { circleRefusal } from "@/lib/circle";
import {
  CIRCLE_ADD,
  CIRCLE_FULL,
  CIRCLE_LAST_ADMIN,
  CIRCLE_MAKE_ADMIN,
  CIRCLE_NO_MAIL,
  CIRCLE_PENDING,
  CIRCLE_REMOVE_CONFIRM,
  CIRCLE_SWITCHER_LABEL,
} from "@/lib/copy";
import type { Family, Member } from "@/lib/types";

const ME = "u-me";
const AUTH_KEY = "sb-test-auth-token";
const storedSession = {
  access_token: "t",
  refresh_token: "r",
  user: { id: ME, email: "me@example.test" },
};

const older: Family = { id: "f-older", name: "Suryaprakasam", tz: "Asia/Kolkata" };
const newer: Family = { id: "f-newer", name: "Rehearsal", tz: "America/Chicago" };

const seat = (over: Partial<Member>): Member => ({
  id: "m",
  family_id: older.id,
  display_name: "Someone",
  role: "member",
  digest_channel: "none",
  auth_user_id: null,
  mail: true,
  ...over,
});

function snapshotOf(families: Family[], family: Family): FamilySnapshot {
  return {
    families,
    family,
    parents: [],
    members: [seat({ id: "m-me", display_name: "Hema", role: "admin", auth_user_id: ME })],
    signals: [],
    pings: [],
    latestPings: [],
    setupLinks: [],
    journal: [],
    journalByParent: {},
    contacts: [],
  };
}

/** Mount the real App over a mocked session and a mocked loader. */
async function mountApp(families: Family[]) {
  const loadSnapshot = vi.fn(async (_now: Date, preferred: string | null) =>
    snapshotOf(families, chooseFamily(families, preferred) as Family),
  );
  vi.doMock("@/lib/supabase", () => ({
    supabase: {
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: storedSession } }),
        onAuthStateChange: vi
          .fn()
          .mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
        signOut: vi.fn(),
      },
    },
    isConfigured: true,
  }));
  vi.doMock("@/lib/data", () => ({
    claimMembership: vi.fn().mockResolvedValue(undefined),
    loadSnapshot,
    sendSignInCode: vi.fn(),
    verifySignInCode: vi.fn(),
    addSeat: vi.fn(),
    removeSeat: vi.fn(),
    setSeatRole: vi.fn(),
    setOwnMail: vi.fn(),
    leaveCircle: vi.fn(),
  }));
  const { default: App } = await import("@/App");
  await act(async () => {
    render(<App />);
  });
  await waitFor(() => expect(loadSnapshot).toHaveBeenCalled());
  return loadSnapshot;
}

beforeEach(() => {
  vi.resetModules();
  localStorage.setItem(AUTH_KEY, JSON.stringify(storedSession));
});

afterEach(() => {
  vi.doUnmock("@/lib/supabase");
  vi.doUnmock("@/lib/data");
  localStorage.clear();
});

describe("the switcher (spec 015 §8)", () => {
  it("is hidden for a one-circle account, and so is the family name", async () => {
    await mountApp([older]);
    await waitFor(() => expect(screen.queryByText("Loading…")).toBeNull());
    expect(screen.queryByTestId("circle-switcher")).toBeNull();
    expect(document.body.textContent).not.toContain(older.name);
  });

  it("is shown for a two-circle account, labelled, listing the stored names", async () => {
    await mountApp([older, newer]);
    const switcher = await screen.findByTestId("circle-switcher");
    expect(switcher.textContent).toContain(CIRCLE_SWITCHER_LABEL);
    expect(switcher.textContent).toContain("Suryaprakasam");
    expect(switcher.textContent).toContain("Rehearsal");
  });

  it("choosing a circle reloads every read scoped to it, and the browser remembers", async () => {
    const loadSnapshot = await mountApp([older, newer]);
    // Default: the oldest, asked for with no preference on this browser.
    expect(loadSnapshot.mock.calls[0][1]).toBeNull();
    const select = (await screen.findByTestId("circle-switcher")).querySelector("select")!;
    expect(select.value).toBe(older.id);
    fireEvent.change(select, { target: { value: newer.id } });
    await waitFor(() =>
      expect(loadSnapshot.mock.calls.at(-1)?.[1]).toBe(newer.id),
    );
    expect(localStorage.getItem("kettle-circle")).toBe(newer.id);
  });

  it("a remembered circle is asked for on the next load", async () => {
    localStorage.setItem("kettle-circle", newer.id);
    const loadSnapshot = await mountApp([older, newer]);
    expect(loadSnapshot.mock.calls[0][1]).toBe(newer.id);
  });
});

describe("chooseFamily", () => {
  it("honours a preference it can find and falls back to the oldest otherwise", () => {
    expect(chooseFamily([older, newer], newer.id)?.id).toBe(newer.id);
    expect(chooseFamily([older, newer], "f-left")?.id).toBe(older.id);
    expect(chooseFamily([older, newer], null)?.id).toBe(older.id);
    expect(chooseFamily([], "anything")).toBeNull();
  });
});

const circleSpy = () => ({
  onAddSeat: vi.fn().mockResolvedValue(undefined),
  onRemoveSeat: vi.fn().mockResolvedValue(undefined),
  onSetRole: vi.fn().mockResolvedValue(undefined),
  onSetMail: vi.fn().mockResolvedValue(undefined),
  onLeave: vi.fn().mockResolvedValue(undefined),
});

function renderFamily(members: Member[], viewerId: string, circle = circleSpy()) {
  render(
    <FamilyScreen
      parentStates={[]}
      cities={{}}
      members={members}
      viewerId={viewerId}
      circle={circle}
      setupEntries={[]}
      onOpen={() => undefined}
      onPickCity={async () => undefined}
      onClearCity={async () => undefined}
    />,
  );
  return circle;
}

const roster = [
  seat({ id: "m-me", display_name: "Hema", role: "admin", auth_user_id: ME }),
  seat({ id: "m-sis", display_name: "Priya", role: "member", auth_user_id: "u-sis" }),
  seat({ id: "m-new", display_name: "Arun", role: "member", auth_user_id: null }),
];

describe("the seats list (spec 015 §8)", () => {
  it("renders name · role, and the pending state for an unclaimed seat", () => {
    renderFamily(roster, ME);
    const rows = screen.getAllByTestId("roster-member");
    expect(rows.map((row) => row.textContent)).toEqual([
      expect.stringContaining("Hema · Admin"),
      expect.stringContaining("Priya · Member"),
      expect.stringContaining(`Arun · Member${CIRCLE_PENDING}`),
    ]);
    expect(screen.getAllByTestId("seat-pending")).toHaveLength(1);
    expect(rows[2].getAttribute("data-pending")).toBe("true");
  });

  it("an admin sees Add someone and the per-row controls, never on their own row", () => {
    renderFamily(roster, ME);
    expect(screen.getByTestId("seat-add")).toHaveTextContent(CIRCLE_ADD);
    expect(screen.getAllByTestId("seat-role")).toHaveLength(2);
    expect(screen.getAllByTestId("seat-remove")).toHaveLength(2);
    expect(screen.getAllByTestId("mail-switch")).toHaveLength(1);
    expect(screen.getAllByTestId("seat-leave")).toHaveLength(1);
  });

  it("a member sees no admin controls, only their own switch and leave", () => {
    renderFamily(roster, "u-sis");
    expect(screen.queryByTestId("seat-add")).toBeNull();
    expect(screen.queryByTestId("seat-role")).toBeNull();
    expect(screen.queryByTestId("seat-remove")).toBeNull();
    expect(screen.getAllByTestId("mail-switch")).toHaveLength(1);
    expect(screen.getAllByTestId("seat-leave")).toHaveLength(1);
  });

  it("removing shows the confirm line, and only the confirm calls through", async () => {
    const circle = renderFamily(roster, ME);
    fireEvent.click(screen.getAllByTestId("seat-remove")[0]);
    expect(screen.getByTestId("seat-confirm")).toHaveTextContent(CIRCLE_REMOVE_CONFIRM);
    expect(circle.onRemoveSeat).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("seat-remove-confirm"));
    await waitFor(() => expect(circle.onRemoveSeat).toHaveBeenCalledWith("m-sis"));
    // The confirm line collapses once the write is through.
    await waitFor(() => expect(screen.queryByTestId("seat-confirm")).toBeNull());
  });

  it("promotes with the right words and the right role", async () => {
    const circle = renderFamily(roster, ME);
    const [promote] = screen.getAllByTestId("seat-role");
    expect(promote).toHaveTextContent(CIRCLE_MAKE_ADMIN);
    fireEvent.click(promote);
    await waitFor(() => expect(circle.onSetRole).toHaveBeenCalledWith("m-sis", "admin"));
  });

  it("the mail switch writes the viewer's own choice", async () => {
    const circle = renderFamily(roster, ME);
    fireEvent.click(screen.getByTestId("mail-switch"));
    await waitFor(() => expect(circle.onSetMail).toHaveBeenCalledWith(false));
  });

  it("a refused write becomes the §9 sentence, in place", async () => {
    const circle = circleSpy();
    circle.onLeave.mockRejectedValue(new Error("last_admin"));
    renderFamily(roster, ME, circle);
    fireEvent.click(screen.getByTestId("seat-leave"));
    await waitFor(() =>
      expect(screen.getByTestId("circle-note")).toHaveTextContent(CIRCLE_LAST_ADMIN),
    );
  });

  it("says when nobody in the circle is listening", () => {
    renderFamily(roster.map((m) => ({ ...m, mail: false })), ME);
    expect(screen.getByTestId("circle-no-mail")).toHaveTextContent(CIRCLE_NO_MAIL);
  });

  it("adding submits name and email, then says what happens next", async () => {
    const circle = renderFamily(roster, ME);
    fireEvent.click(screen.getByTestId("seat-add"));
    const form = screen.getByTestId("seat-add-form");
    const [name, email] = form.querySelectorAll("input");
    fireEvent.change(name, { target: { value: "Sister" } });
    fireEvent.change(email, { target: { value: "sister@example.test" } });
    fireEvent.submit(form);
    await waitFor(() =>
      expect(circle.onAddSeat).toHaveBeenCalledWith("Sister", "sister@example.test"),
    );
    expect(screen.getByTestId("circle-note").textContent).toContain("Kettle will let them in");
  });
});

describe("circleRefusal", () => {
  it("maps the three actionable codes and nothing else", () => {
    expect(circleRefusal(new Error("P0001: last_admin"))).toBe(CIRCLE_LAST_ADMIN);
    expect(circleRefusal({ message: "circle_full" })).toBe(CIRCLE_FULL);
    expect(circleRefusal({ message: "duplicate_email" })).not.toBeNull();
    expect(circleRefusal(new Error("not_admin"))).toBeNull();
    expect(circleRefusal(undefined)).toBeNull();
  });
});
