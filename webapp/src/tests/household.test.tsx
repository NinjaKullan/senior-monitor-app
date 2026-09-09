/**
 * @vitest-environment jsdom
 *
 * Spec 020, the webapp half: the card's one line only with a ping today
 * from six on; morning, afternoon and evening by the parent's hour; night,
 * paused and unreachable suppress it; the most recent device wins; the day
 * view's block lists at most three, today only; the setup rows by role.
 * No verdict, arc or dot reads these rows: computeParentToday never sees
 * them, and a test holds the verdict unchanged with a house full of pings.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  DEVICE_ADD,
  DEVICE_ADDRESS,
  DEVICE_COPIED,
  DEVICE_LIMIT,
  DEVICE_NOTHING_YET,
  DEVICE_REMOVE,
  DEVICE_REMOVE_CONFIRM,
  DEVICE_TELL,
  DEVICES_NONE_TODAY,
  DEVICES_TODAY,
  RECIPE_IFTTT,
  STATE_QUIET,
} from "@/lib/copy";
import { householdAddress } from "@/lib/data";
import { deviceLine, deviceSetupRows, devicesToday } from "@/lib/household";
import { computeParentToday } from "@/lib/parentState";
import { FamilyScreen } from "@/screens/Family";
import { ParentDetail } from "@/screens/ParentDetail";
import { Today } from "@/screens/Today";
import type { HouseholdDevice, HouseholdPing, Parent, ParentSignal, Ping } from "@/lib/types";

vi.mock("@/lib/supabase", () => ({ isConfigured: true, supabase: {} }));

const IST = "Asia/Kolkata";
const CHICAGO = "America/Chicago";
/** 10:48 am IST, Tuesday 8 Sep. */
const MORNING = new Date("2026-09-08T05:18:00Z");
const AFTERNOON = new Date("2026-09-08T09:00:00Z"); // 2:30 pm
const EVENING = new Date("2026-09-08T14:30:00Z"); // 8:00 pm
const NIGHT = new Date("2026-09-07T19:32:00Z"); // 1:02 am

const amma: Parent = {
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
};
const signals: ParentSignal[] = [
  { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: "p1", signal: "device_alive", alarm_grade: false, active: true },
];
const phonePing: Ping = { parent_id: "p1", signal: "whatsapp", ts_utc: "2026-09-08T02:30:00Z" }; // 8:00 am
const device = (over: Partial<HouseholdDevice>): HouseholdDevice => ({
  id: "d1",
  parent_id: "p1",
  kind: "plug",
  platform: "ifttt",
  created_utc: "2026-09-01T00:00:00Z",
  removed_utc: null,
  ...over,
});
const plug = device({});
const door = device({ id: "d2", kind: "door", platform: "home_assistant", created_utc: "2026-09-02T00:00:00Z" });
const voice = device({ id: "d3", kind: "voice", platform: null, created_utc: "2026-09-03T00:00:00Z" });
const ping = (device_id: string, ts_utc: string): HouseholdPing => ({ device_id, ts_utc });
const AT_0805 = ping("d1", "2026-09-08T02:35:00Z");
const AT_0550 = ping("d1", "2026-09-08T00:20:00Z");
const AT_0600 = ping("d1", "2026-09-08T00:30:00Z");

const stateOf = (pings: Ping[] = [phonePing], now = MORNING, parent = amma) =>
  computeParentToday(parent, IST, signals, pings, pings, now, CHICAGO);

describe("the Today card's line (spec 020 §5)", () => {
  it("shows the most recent device today from six on, in the morning form", () => {
    expect(deviceLine(stateOf(), [plug], [AT_0805], MORNING)).toBe("Plug, 8:05 am this morning");
  });

  it("shows nothing for a 5:50 ping, and counts a 6:00 one", () => {
    expect(deviceLine(stateOf(), [plug], [AT_0550], MORNING)).toBeNull();
    expect(deviceLine(stateOf(), [plug], [AT_0600], MORNING)).toBe("Plug, 6:00 am this morning");
  });

  it("takes the afternoon and evening forms by the parent's local hour", () => {
    const at1400 = ping("d2", "2026-09-08T08:30:00Z");
    expect(deviceLine(stateOf([phonePing], AFTERNOON), [door], [at1400], AFTERNOON)).toBe(
      "Door, 2:00 pm this afternoon",
    );
    const at1830 = ping("d3", "2026-09-08T13:00:00Z");
    expect(deviceLine(stateOf([phonePing], EVENING), [voice], [at1830], EVENING)).toBe(
      "Voice routine, 6:30 pm this evening",
    );
  });

  it("the most recent device wins, and a future-stamped ping is not yet today", () => {
    const later = ping("d2", "2026-09-08T04:00:00Z"); // 9:30 am
    expect(deviceLine(stateOf(), [plug, door], [AT_0805, later], MORNING)).toBe(
      "Door, 9:30 am this morning",
    );
    const ahead = ping("d2", "2026-09-08T09:00:00Z");
    expect(deviceLine(stateOf(), [plug, door], [AT_0805, ahead], MORNING)).toBe(
      "Plug, 8:05 am this morning",
    );
  });

  it("night, paused and unreachable each suppress the line", () => {
    const night = stateOf([phonePing], NIGHT);
    expect(night.night).toBe(true);
    expect(deviceLine(night, [plug], [ping("d1", "2026-09-07T13:00:00Z")], NIGHT)).toBeNull();
    const paused = stateOf([phonePing], MORNING, { ...amma, paused_until: "infinity", paused_since: "2026-09-01T00:00:00Z" });
    expect(paused.paused).toBe(true);
    expect(deviceLine(paused, [plug], [AT_0805], MORNING)).toBeNull();
    const stale: Ping[] = [
      { parent_id: "p1", signal: "whatsapp", ts_utc: "2026-08-20T02:30:00Z" },
      { parent_id: "p1", signal: "device_alive", ts_utc: "2026-08-20T02:30:00Z" },
    ];
    const unreachable = stateOf(stale, MORNING);
    expect(unreachable.kind).toBe("unreachable");
    expect(deviceLine(unreachable, [plug], [AT_0805], MORNING)).toBeNull();
  });

  it("a removed device's pings never show", () => {
    const gone = device({ removed_utc: "2026-09-08T03:00:00Z" });
    expect(deviceLine(stateOf(), [gone], [AT_0805], MORNING)).toBeNull();
  });

  it("never touches a verdict, the arc or the dots", () => {
    const quiet = stateOf([]);
    expect(quiet.kind).toBe("quiet");
    expect(quiet.sentence).toBe(STATE_QUIET);
    expect(quiet.arcCells[0].text).toBe("Quiet so far");
    expect(quiet.recentDots[6].kind).toBe("none");
    // The line exists beside the verdict, not inside it.
    expect(deviceLine(quiet, [plug], [AT_0805], MORNING)).toBe("Plug, 8:05 am this morning");
  });

  it("renders under the dual clock line, and not at all without a line", () => {
    const state = stateOf();
    const rollup = { line: "x", sub: "y" };
    const { unmount } = render(
      <Today states={[state]} rollup={rollup} dateLine="Tuesday · September 8" onOpen={() => undefined} deviceLines={{ p1: "Plug, 8:05 am this morning" }} />,
    );
    expect(screen.getByTestId("card-device")).toHaveTextContent("Plug, 8:05 am this morning");
    expect(screen.getByTestId("card-dual")).toBeInTheDocument();
    unmount();
    render(<Today states={[state]} rollup={rollup} dateLine="Tuesday · September 8" onOpen={() => undefined} deviceLines={{ p1: null }} />);
    expect(screen.queryByTestId("card-device")).toBeNull();
  });
});

describe("the day view's block (§5)", () => {
  const detailProps = {
    todayDate: "2026-09-08",
    tz: CHICAGO,
    onBack: () => undefined,
    onAddNote: async () => undefined,
    onSteps: () => undefined,
    notes: [],
  };

  it("lists each device heard today, most recent first, at most three", () => {
    const light = device({ id: "d4", kind: "light", created_utc: "2026-09-04T00:00:00Z" });
    const pings = [
      AT_0805,
      ping("d2", "2026-09-08T04:00:00Z"), // 9:30
      ping("d3", "2026-09-08T03:00:00Z"), // 8:30
      ping("d4", "2026-09-08T04:30:00Z"), // 10:00
      ping("d1", "2026-09-08T02:00:00Z"), // 7:30, older than the plug's 8:05
    ];
    const rows = devicesToday(stateOf(), [plug, door, voice, light], pings, MORNING);
    expect(rows?.map((r) => r.text)).toEqual(["Light · 10:00 am", "Door · 9:30 am", "Voice routine · 8:30 am"]);
  });

  it("is absent with no device, and says nothing yet with devices but no ping today", () => {
    expect(devicesToday(stateOf(), [], [AT_0805], MORNING)).toBeNull();
    expect(devicesToday(stateOf(), [plug], [AT_0550], MORNING)).toEqual([]);
    expect(devicesToday(stateOf(), [plug], [ping("d1", "2026-09-07T02:35:00Z")], MORNING)).toEqual([]);
  });

  it("renders the block, the empty sentence, and nothing without a device", () => {
    const state = stateOf();
    const { unmount } = render(
      <ParentDetail state={state} {...detailProps} devicesToday={[{ id: "d1", kind: "plug", text: "Plug · 8:05 am" }]} />,
    );
    expect(screen.getByTestId("devices-panel")).toHaveTextContent(DEVICES_TODAY);
    expect(screen.getByTestId("device-row")).toHaveTextContent("Plug · 8:05 am");
    unmount();
    const { unmount: second } = render(<ParentDetail state={state} {...detailProps} devicesToday={[]} />);
    expect(screen.getByTestId("devices-none")).toHaveTextContent(DEVICES_NONE_TODAY);
    second();
    render(<ParentDetail state={state} {...detailProps} devicesToday={null} />);
    expect(screen.queryByTestId("devices-panel")).toBeNull();
  });
});

describe("the setup rows (§5), by role", () => {
  const entry = {
    parentId: "p1",
    parentName: "Amma",
    status: "reporting" as const,
    sms: null,
    url: null,
    shareHref: null,
    expiresDate: null,
  };
  const shared = {
    parentStates: [],
    cities: {},
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
    setupEntries: [entry],
  };
  const actions = () => ({
    onAdd: vi.fn().mockResolvedValue("d9"),
    onRemove: vi.fn().mockResolvedValue(undefined),
    onAddress: vi.fn().mockResolvedValue(householdAddress("t".repeat(32))),
  });

  it("writes each row as kind and heard, or nothing heard yet", () => {
    const rows = deviceSetupRows("p1", [plug, door], [ping("d1", "2026-09-08T05:06:00Z")], MORNING);
    expect(rows.map((r) => r.text)).toEqual(["Plug · Heard from 12 minutes ago", `Door · ${DEVICE_NOTHING_YET}`]);
  });

  it("a member sees the rows, the intro and the told line, and no control or address", () => {
    render(<FamilyScreen {...shared} deviceRows={deviceSetupRows("p1", [plug], [], MORNING)} />);
    expect(screen.getByTestId("household")).toHaveTextContent("Something in Amma's home");
    expect(screen.getByTestId("device-tell")).toHaveTextContent(DEVICE_TELL.replace("{name}", "Amma"));
    expect(screen.getByTestId("device-setup-text")).toHaveTextContent(`Plug · ${DEVICE_NOTHING_YET}`);
    expect(screen.queryByTestId("device-add")).toBeNull();
    expect(screen.queryByTestId("device-address")).toBeNull();
    expect(screen.queryByTestId("device-remove")).toBeNull();
    expect(document.body.textContent).not.toContain("/d/");
  });

  it("an admin adds through the two-pick sheet and sees the recipe under the new row", async () => {
    const household = actions();
    const { rerender } = render(<FamilyScreen {...shared} deviceRows={[]} household={household} />);
    fireEvent.click(screen.getByTestId("device-add"));
    fireEvent.change(screen.getByTestId("device-kind"), { target: { value: "door" } });
    fireEvent.change(screen.getByTestId("device-platform"), { target: { value: "ifttt" } });
    fireEvent.click(screen.getByTestId("device-add-done"));
    await waitFor(() => expect(household.onAdd).toHaveBeenCalledWith("p1", "door", "ifttt"));
    const added = device({ id: "d9", kind: "door", platform: "ifttt" });
    rerender(<FamilyScreen {...shared} deviceRows={deviceSetupRows("p1", [added], [], MORNING)} household={household} />);
    expect(screen.getByTestId("device-recipe")).toHaveTextContent(RECIPE_IFTTT);
    expect(screen.queryByTestId("device-add-sheet")).toBeNull();
  });

  it("an admin copies the address to the clipboard and sees it in view (324)", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    const household = actions();
    render(<FamilyScreen {...shared} deviceRows={deviceSetupRows("p1", [plug], [], MORNING)} household={household} />);
    expect(screen.queryByTestId("device-address-line")).toBeNull();
    fireEvent.click(screen.getByTestId("device-address"));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(`https://kettle-api.fly.dev/d/${"t".repeat(32)}`));
    expect(screen.getByTestId("device-address")).toHaveTextContent(DEVICE_COPIED);
    expect(screen.getByTestId("device-address-line")).toHaveTextContent(`https://kettle-api.fly.dev/d/${"t".repeat(32)}`);
    expect(screen.getByTestId("device-address")).not.toHaveTextContent(DEVICE_ADDRESS);
  });

  it("Remove asks first, Keep it backs out, Remove goes through", async () => {
    const household = actions();
    render(<FamilyScreen {...shared} deviceRows={deviceSetupRows("p1", [plug], [], MORNING)} household={household} />);
    fireEvent.click(screen.getByTestId("device-remove"));
    expect(screen.getByTestId("device-remove-confirm")).toHaveTextContent(
      DEVICE_REMOVE_CONFIRM.replace("{kind}", "plug"),
    );
    fireEvent.click(screen.getByTestId("device-remove-no"));
    expect(screen.queryByTestId("device-remove-confirm")).toBeNull();
    expect(household.onRemove).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("device-remove"));
    fireEvent.click(screen.getByTestId("device-remove-yes"));
    await waitFor(() => expect(household.onRemove).toHaveBeenCalledWith("d1"));
  });

  it("at three the limit line replaces the button", () => {
    render(
      <FamilyScreen {...shared} deviceRows={deviceSetupRows("p1", [plug, door, voice], [], MORNING)} household={actions()} />,
    );
    expect(screen.queryByTestId("device-add")).toBeNull();
    expect(screen.getByTestId("device-limit")).toHaveTextContent(DEVICE_LIMIT.replace("{name}", "Amma"));
    expect(screen.getAllByTestId("device-remove")).toHaveLength(3);
    expect(screen.getAllByText(DEVICE_REMOVE)).toHaveLength(3);
    expect(screen.queryByText(DEVICE_ADD)).toBeNull();
  });
});
