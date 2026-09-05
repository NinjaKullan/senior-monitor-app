/**
 * @vitest-environment jsdom
 *
 * Spec 011 Amendment A.6 (DECISIONS 290), the webapp half: the consent
 * script and "They said yes" render on the Family setup row for admins
 * only, and only for a parent with a +1 phone, no WhatsApp number and no
 * consent yet; the row reads "Texts on" after the yes and "Texts stopped by
 * {name}" after STOP; members see the state and never the button; the four
 * strings and the carrier-filed script are verbatim and obey the copy law.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  PAUSED_SETUP,
  SETUP_READY,
  SETUP_REPORTING,
  SETUP_SEND_LABEL,
  SMS_CONSENT_BUTTON,
  SMS_CONSENT_SCRIPT,
  SMS_ROW_ON,
  SMS_ROW_STOPPED,
  SMS_SCRIPT_LABEL,
} from "@/lib/copy";
import { buildSetupEntries, smsStateFor } from "@/lib/setupLinks";
import { FamilyScreen } from "@/screens/Family";
import type { Parent, Ping, SetupLink } from "@/lib/types";

const NOW = new Date("2026-09-05T12:00:00Z");

const parent = (over: Partial<Parent>): Parent => ({
  id: "p1",
  family_id: "f1",
  display_name: "Dad",
  tz: null,
  phone_e164: "+14155550123",
  whatsapp_e164: null,
  relationship: "Dad",
  city_label: null,
  tz_changed_utc: null,
  paused_until: null,
  paused_since: null,
  sms_consent_utc: null,
  sms_opted_out_utc: null,
  ...over,
});

const eligible = parent({});
const consented = parent({ sms_consent_utc: "2026-09-04T15:00:00Z" });
const stopped = parent({
  sms_consent_utc: "2026-09-04T15:00:00Z",
  sms_opted_out_utc: "2026-09-05T01:00:00Z",
});
const onWhatsApp = parent({ whatsapp_e164: "+919845550001" });
const ukPhone = parent({ phone_e164: "+442079460123" });
const noPhone = parent({ phone_e164: null });

const reported: Ping[] = [{ parent_id: "p1", signal: "routine", ts_utc: "2026-09-05T02:00:00Z" }];
const liveLink: SetupLink = {
  parent_id: "p1",
  slug: "slugB000000000000000000B",
  created_utc: "2026-09-04T00:00:00Z",
  expires_utc: "2026-09-11T00:00:00Z",
  revoked_utc: null,
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
};

function renderRow(p: Parent, onSmsConsent?: (parentId: string) => Promise<void>, pings: Ping[] = reported) {
  const entries = buildSetupEntries([p], [liveLink], pings, NOW);
  render(<FamilyScreen {...shared} setupEntries={entries} onSmsConsent={onSmsConsent} />);
  return entries[0];
}

describe("the three conditions (DECISIONS 290)", () => {
  it("offers consent only for a +1 phone with no WhatsApp number and no consent", () => {
    expect(smsStateFor(eligible)).toBe("offer");
    expect(smsStateFor(onWhatsApp)).toBeNull();
    expect(smsStateFor(ukPhone)).toBeNull();
    expect(smsStateFor(noPhone)).toBeNull();
    expect(smsStateFor(consented)).toBe("on");
    expect(smsStateFor(stopped)).toBe("stopped");
  });

  it("a WhatsApp number wins even beside a consented +1 phone", () => {
    expect(smsStateFor({ ...consented, whatsapp_e164: "+919845550001" })).toBeNull();
  });
});

describe("the button, by role", () => {
  it("shows the script and the button to an admin, and taps through to the function", async () => {
    const onSmsConsent = vi.fn().mockResolvedValue(undefined);
    renderRow(eligible, onSmsConsent);
    expect(screen.getByText(SMS_SCRIPT_LABEL.replace("{name}", "Dad"))).toBeInTheDocument();
    expect(screen.getByTestId("sms-consent-script")).toHaveTextContent(SMS_CONSENT_SCRIPT);
    fireEvent.click(screen.getByTestId("sms-consent-button"));
    await waitFor(() => expect(onSmsConsent).toHaveBeenCalledWith("p1"));
    expect(screen.getByTestId("sms-consent-button")).toHaveTextContent(SMS_CONSENT_BUTTON);
  });

  it("shows a member the row state and never the button or the script", () => {
    renderRow(eligible, undefined);
    expect(screen.queryByTestId("sms-consent")).toBeNull();
    expect(document.body.textContent).not.toContain(SMS_CONSENT_BUTTON);
    expect(document.body.textContent).not.toContain("Kettle is a service from HeyKettle");
    expect(screen.getByTestId("setup-status")).toHaveTextContent(SETUP_REPORTING);
  });

  it("shows an admin no button for a parent on WhatsApp, on a non-+1 number, or already consented", () => {
    const onSmsConsent = vi.fn();
    for (const p of [onWhatsApp, ukPhone, noPhone, consented, stopped]) {
      const { unmount } = render(
        <FamilyScreen
          {...shared}
          setupEntries={buildSetupEntries([p], [], reported, NOW)}
          onSmsConsent={onSmsConsent}
        />,
      );
      expect(screen.queryByTestId("sms-consent")).toBeNull();
      unmount();
    }
    expect(onSmsConsent).not.toHaveBeenCalled();
  });

  it("does not offer consent on a paused row", () => {
    const paused = parent({ paused_until: "infinity", paused_since: "2026-09-04T00:00:00Z" });
    renderRow(paused, vi.fn());
    expect(screen.queryByTestId("sms-consent")).toBeNull();
    expect(screen.getByTestId("setup-status")).toHaveTextContent(PAUSED_SETUP);
  });
});

describe("the row states", () => {
  it("reads Texts on in place of reporting once consent is recorded", () => {
    renderRow(consented, vi.fn());
    expect(screen.getByTestId("setup-status")).toHaveTextContent(SMS_ROW_ON);
    expect(document.body.textContent).not.toContain(SETUP_REPORTING);
  });

  it("reads Texts stopped by {name} after STOP, for admins and members alike", () => {
    const { unmount } = render(
      <FamilyScreen {...shared} setupEntries={buildSetupEntries([stopped], [], reported, NOW)} onSmsConsent={vi.fn()} />,
    );
    expect(screen.getByTestId("setup-status")).toHaveTextContent("Texts stopped by Dad");
    unmount();
    renderRow(stopped, undefined);
    expect(screen.getByTestId("setup-status")).toHaveTextContent("Texts stopped by Dad");
  });

  it("keeps the share link for a texting parent whose phone has not reported yet", () => {
    const entry = renderRow(consented, vi.fn(), []);
    expect(entry.status).toBe("ready");
    expect(screen.getByTestId("setup-status")).toHaveTextContent(SMS_ROW_ON);
    expect(screen.getByTestId("setup-share")).toHaveTextContent(SETUP_SEND_LABEL);
    expect(document.body.textContent).not.toContain(SETUP_READY);
  });

  it("Paused wins over the texting state", () => {
    const paused = parent({ ...stopped, paused_until: "infinity", paused_since: "2026-09-04T00:00:00Z" });
    renderRow(paused, undefined);
    expect(screen.getByTestId("setup-status")).toHaveTextContent(PAUSED_SETUP);
  });

  it("never prints the phone number as text", () => {
    renderRow(eligible, vi.fn());
    expect(document.body.textContent).not.toContain("4155550123");
  });
});

describe("the copy contract (A.6, VERBATIM)", () => {
  it("holds the four strings and the carrier-filed script", () => {
    expect(SMS_SCRIPT_LABEL).toBe("Say this to {name}, then tap the button.");
    expect(SMS_CONSENT_BUTTON).toBe("They said yes");
    expect(SMS_ROW_ON).toBe("Texts on");
    expect(SMS_ROW_STOPPED).toBe("Texts stopped by {name}");
    expect(SMS_CONSENT_SCRIPT).toBe(
      "Kettle is a service from HeyKettle. It sends you a short text when your morning is not as usual, to ask if everything is okay. You would get at most one question a day, and one reminder if you do not reply. Message and data rates may apply. You can reply HELP for help, or STOP to end the texts at any time. The terms are at heykettle.com/terms.html and the privacy policy at heykettle.com/privacy.html. Do you want these texts? Please say yes or no.",
    );
  });
});
