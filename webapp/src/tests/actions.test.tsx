/**
 * @vitest-environment jsdom
 *
 * DECISIONS 324, the button pass: one action vocabulary, three variants and
 * no others. No screen or component keeps an inline button style; every
 * variant is 44 px tall to the touch with a focus ring; the Today card
 * assigns Call, View day and Pause by variant; the city control sits under
 * the name on every parent row; a device row appears the moment Add
 * returns and goes if the add fails; the address line is an admin's only.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it, vi } from "vitest";
import { Action } from "@/components/ui/action";
import { DEVICE_NOTHING_YET, PAUSE_LINK } from "@/lib/copy";
import { deviceSetupRows } from "@/lib/household";
import { computeParentToday } from "@/lib/parentState";
import { FamilyScreen } from "@/screens/Family";
import { Today } from "@/screens/Today";
import type { HouseholdDevice, Parent, ParentSignal, Ping } from "@/lib/types";

vi.mock("@/lib/supabase", () => ({ isConfigured: true, supabase: {} }));

const SRC = join(__dirname, "..");
const CSS = readFileSync(join(SRC, "kettle.css"), "utf8");

function walk(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory() ? walk(join(dir, entry.name)) : [join(dir, entry.name)],
  );
}

describe("one vocabulary, in one place", () => {
  it("no screen or component keeps an inline button style or a deleted constant", () => {
    // Selection controls (the filter chips, the city list's options, the
    // roster row that opens a parent) are not actions and keep their own
    // markup; every action goes through <Action>.
    const allowed = new Set(["components/FilterChips.tsx", "components/CityPicker.tsx", "screens/Family.tsx"]);
    const files = [...walk(join(SRC, "screens")), ...walk(join(SRC, "components"))].filter(
      (f) => f.endsWith(".tsx") && !f.includes("/ui/"),
    );
    for (const file of files) {
      const source = readFileSync(file, "utf8");
      const rel = file.slice(SRC.length + 1);
      for (const name of ["SMALL_BTN", "LINK_BTN", "PILL_BUTTON", "PILL_PRIMARY", "LINK_BUTTON"]) {
        expect(source.includes(name), `${rel} still names ${name}`).toBe(false);
      }
      const styled = source.match(/<button[^>]*\sstyle=/g) ?? [];
      if (allowed.has(rel)) {
        // The allowed files carry exactly their selection control.
        expect(styled.length, `${rel} grew a styled button`).toBeLessThanOrEqual(1);
      } else {
        expect(styled, `${rel} has a raw styled button`).toEqual([]);
      }
    }
  });

  it("has exactly three variants, each 44 px tall to the touch, with a focus ring", () => {
    const variants = [...CSS.matchAll(/\.kt-action-([a-z]+)\s*\{/g)].map((m) => m[1]);
    expect(new Set(variants)).toEqual(new Set(["primary", "secondary", "quiet"]));
    expect(CSS).toMatch(/\.kt-action\s*\{[^}]*min-height:\s*2\.75rem/);
    expect(CSS).toMatch(/\.kt-action:focus-visible\s*\{[^}]*outline:\s*2px solid/);
    expect(CSS).toMatch(/\.kt-action:disabled[^{]*\{[^}]*opacity:\s*\.5/);
    // Quiet gives up the box but not the target: its vertical padding alone
    // reaches 44 px (2 × .875rem = 28 px, plus a 16 px line), on the baseline.
    const quiet = CSS.match(/\.kt-action-quiet\s*\{([^}]*)\}/)?.[1] ?? "";
    expect(quiet).toMatch(/padding:\s*\.875rem 0/);
    expect(quiet).toMatch(/margin:\s*-\.875rem 0/);
    expect(quiet).toMatch(/text-decoration:\s*underline/);
    expect(quiet).toMatch(/display:\s*inline;/);
    for (const variant of ["primary", "secondary", "quiet"] as const) {
      const { unmount } = render(<Action variant={variant} data-testid="a">Go</Action>);
      const el = screen.getByTestId("a");
      expect(el.className).toContain(`kt-action-${variant}`);
      expect(el.getAttribute("data-variant")).toBe(variant);
      expect(el.tagName).toBe("BUTTON");
      expect(el.getAttribute("type")).toBe("button");
      unmount();
    }
    render(<Action variant="primary" href="tel:+1" data-testid="link">Call</Action>);
    expect(screen.getByTestId("link").tagName).toBe("A");
  });
});

const IST = "Asia/Kolkata";
const NOW = new Date("2026-09-09T05:18:00Z");
const parent = (over: Partial<Parent>): Parent => ({
  id: "p1",
  family_id: "f1",
  display_name: "Amma",
  tz: null,
  phone_e164: "+919812345678",
  whatsapp_e164: null,
  relationship: "Mom",
  city_label: "Chennai",
  tz_changed_utc: null,
  paused_until: null,
  paused_since: null,
  sms_consent_utc: null,
  sms_opted_out_utc: null,
  ...over,
});
const signals: ParentSignal[] = [
  { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: "p2", signal: "whatsapp", alarm_grade: true, active: true },
];
const pings: Ping[] = [{ parent_id: "p1", signal: "whatsapp", ts_utc: "2026-09-09T02:30:00Z" }];
const stateOf = (p: Parent) => computeParentToday(p, IST, signals, pings, pings, NOW, "America/Chicago");

describe("the Today card (324)", () => {
  it("renders Call as primary, View day as secondary and Pause as quiet", () => {
    const state = stateOf(parent({}));
    render(
      <Today
        states={[state]}
        rollup={{ line: "x", sub: "y" }}
        dateLine="Wednesday · September 9"
        onOpen={() => undefined}
        pause={{ onPause: async () => undefined, onResume: async () => undefined }}
      />,
    );
    const call = screen.getByTestId("call-button");
    expect(call.tagName).toBe("A");
    expect(call.getAttribute("data-variant")).toBe("primary");
    expect(screen.getByRole("button", { name: state.viewLabel }).getAttribute("data-variant")).toBe("secondary");
    expect(screen.getByRole("button", { name: PAUSE_LINK }).getAttribute("data-variant")).toBe("quiet");
    fireEvent.click(screen.getByTestId("pause-link"));
    for (const id of ["pause-week", "pause-open"]) {
      expect(screen.getByTestId(id).getAttribute("data-variant")).toBe("secondary");
    }
    expect(screen.getAllByTestId(/^pause-/).length).toBeGreaterThan(0);
  });

  it("a card with no number has no primary, and View day stays secondary", () => {
    const state = stateOf(parent({ id: "p2", display_name: "TestDad", phone_e164: null }));
    render(<Today states={[state]} rollup={{ line: "x", sub: "y" }} dateLine="Wednesday · September 9" onOpen={() => undefined} />);
    expect(screen.queryByTestId("call-button")).toBeNull();
    expect(document.querySelectorAll('[data-variant="primary"]')).toHaveLength(0);
    expect(screen.getByTestId("view-day").getAttribute("data-variant")).toBe("secondary");
  });
});

const entry = (parentId: string, parentName: string) => ({
  parentId,
  parentName,
  status: "reporting" as const,
  sms: null,
  url: null,
  shareHref: null,
  expiresDate: null,
});
const shared = {
  cities: { p1: "Chennai", p2: "" },
  members: [],
  viewerId: null,
  circle: {
    onAddSeat: async () => undefined,
    onRemoveSeat: async () => undefined,
    onSetRole: async () => undefined,
    onSetMail: async () => undefined,
    onLeave: async () => undefined,
  },
  onOpen: () => undefined,
  onPickCity: async () => undefined,
  onClearCity: async () => undefined,
};

describe("the Family screen (324)", () => {
  it("puts the city control on its own line under the name on both parent rows", () => {
    const states = [stateOf(parent({})), stateOf(parent({ id: "p2", display_name: "Appa", city_label: null }))];
    render(<FamilyScreen {...shared} parentStates={states} setupEntries={[]} />);
    const pickers = screen.getAllByTestId("city-picker");
    expect(pickers).toHaveLength(2);
    for (const picker of pickers) {
      const row = picker.parentElement as HTMLElement;
      expect(row.style.flexDirection).toBe("column");
      // The name button precedes the picker inside the same column.
      expect(row.firstElementChild?.tagName).toBe("BUTTON");
      expect(row.lastElementChild).toBe(picker);
      expect(picker.querySelector("input")?.className).toContain("kt-cityfield");
    }
  });

  const plug: HouseholdDevice = {
    id: "d1",
    parent_id: "p1",
    kind: "plug",
    platform: "ifttt",
    created_utc: "2026-09-01T00:00:00Z",
    removed_utc: null,
  };

  it("shows the new device row the moment Add returns, before any refetch", async () => {
    let resolveAdd: (id: string) => void = () => undefined;
    const household = {
      onAdd: vi.fn(() => new Promise<string>((resolve) => (resolveAdd = resolve))),
      onRemove: vi.fn().mockResolvedValue(undefined),
      onAddress: vi.fn().mockResolvedValue("https://kettle-api.fly.dev/d/" + "t".repeat(32)),
    };
    render(<FamilyScreen {...shared} parentStates={[]} setupEntries={[entry("p1", "Amma")]} deviceRows={[]} household={household} />);
    fireEvent.click(screen.getByTestId("device-add"));
    fireEvent.change(screen.getByTestId("device-kind"), { target: { value: "door" } });
    fireEvent.click(screen.getByTestId("device-add-done"));
    expect(screen.queryByTestId("device-setup-row")).toBeNull();
    resolveAdd("d9");
    // No refetch has happened (deviceRows is still empty): the row is there.
    await waitFor(() => expect(screen.getByTestId("device-setup-row")).toBeInTheDocument());
    expect(screen.getByTestId("device-setup-text")).toHaveTextContent(`Door · ${DEVICE_NOTHING_YET}`);
    expect(screen.getByTestId("device-recipe")).toBeInTheDocument();
  });

  it("removes the row and shows nothing when the add fails", async () => {
    const household = {
      onAdd: vi.fn().mockRejectedValue(new Error("refused")),
      onRemove: vi.fn().mockResolvedValue(undefined),
      onAddress: vi.fn().mockResolvedValue("x"),
    };
    render(<FamilyScreen {...shared} parentStates={[]} setupEntries={[entry("p1", "Amma")]} deviceRows={[]} household={household} />);
    fireEvent.click(screen.getByTestId("device-add"));
    fireEvent.click(screen.getByTestId("device-add-done"));
    await waitFor(() => expect(household.onAdd).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByTestId("device-add-sheet")).not.toBeNull());
    expect(screen.queryByTestId("device-setup-row")).toBeNull();
  });

  it("a removed row goes at once", async () => {
    let resolveRemove: () => void = () => undefined;
    const household = {
      onAdd: vi.fn().mockResolvedValue("d9"),
      onRemove: vi.fn(() => new Promise<void>((resolve) => (resolveRemove = resolve))),
      onAddress: vi.fn().mockResolvedValue("x"),
    };
    render(
      <FamilyScreen {...shared} parentStates={[]} setupEntries={[entry("p1", "Amma")]} deviceRows={deviceSetupRows("p1", [plug], [], NOW)} household={household} />,
    );
    fireEvent.click(screen.getByTestId("device-remove"));
    fireEvent.click(screen.getByTestId("device-remove-yes"));
    expect(screen.queryByTestId("device-setup-row")).toBeNull();
    resolveRemove();
    await waitFor(() => expect(household.onRemove).toHaveBeenCalledWith("d1"));
    expect(screen.queryByTestId("device-setup-row")).toBeNull();
  });

  it("shows the address line for an admin who expands a row, never for a member", async () => {
    const address = "https://kettle-api.fly.dev/d/" + "t".repeat(32);
    const household = {
      onAdd: vi.fn().mockResolvedValue("d9"),
      onRemove: vi.fn().mockResolvedValue(undefined),
      onAddress: vi.fn().mockResolvedValue(address),
    };
    Object.assign(navigator, { clipboard: { writeText: vi.fn().mockResolvedValue(undefined) } });
    const { unmount } = render(
      <FamilyScreen {...shared} parentStates={[]} setupEntries={[entry("p1", "Amma")]} deviceRows={deviceSetupRows("p1", [plug], [], NOW)} household={household} />,
    );
    expect(screen.queryByTestId("device-address-line")).toBeNull();
    fireEvent.click(screen.getByTestId("device-address"));
    await waitFor(() => expect(screen.getByTestId("device-address-line")).toHaveTextContent(address));
    expect(screen.getByTestId("device-address-line").tagName).toBe("CODE");
    unmount();
    render(<FamilyScreen {...shared} parentStates={[]} setupEntries={[entry("p1", "Amma")]} deviceRows={deviceSetupRows("p1", [plug], [], NOW)} />);
    expect(screen.queryByTestId("device-address-line")).toBeNull();
    expect(screen.queryByTestId("device-address")).toBeNull();
    expect(document.body.textContent).not.toContain("t".repeat(32));
  });
});
