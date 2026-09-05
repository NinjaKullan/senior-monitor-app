/**
 * @vitest-environment jsdom
 *
 * Spec 019 §6, the webapp half: the consent screen with the ruled words,
 * Allow posting the session to /oauth/approve and following the redirect,
 * Not now denying the same way, the expired state; and the Assistants
 * section on Family — the address with Copy, the connections as
 * "{client} · since {date}" on the viewer's clock, Disconnect behind one
 * confirm line, and the empty state.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConnectScreen } from "@/screens/Connect";
import { FamilyScreen } from "@/screens/Family";
import { API_BASE, MCP_URL, approveConnect, pendingConnect } from "@/lib/data";
import {
  ASSISTANTS_DISCONNECT_CONFIRM,
  ASSISTANTS_INTRO,
  ASSISTANTS_NONE,
  ASSISTANT_FALLBACK,
  CONNECT_BODY,
  CONNECT_EXPIRED,
  CONNECT_READ_ONLY,
  CONNECT_TITLE,
} from "@/lib/copy";
import type { AssistantGrant } from "@/lib/types";

const noop = async () => undefined;

describe("the consent screen (spec 019 §6)", () => {
  it("names the assistant and every parent across the person's circles", () => {
    render(
      <ConnectScreen
        state={{ kind: "ready", clientName: "Claude", names: ["Amma", "Appa", "Mom"] }}
        onAllow={noop}
        onCancel={noop}
      />,
    );
    expect(screen.getByTestId("connect-title")).toHaveTextContent(CONNECT_TITLE.replace("{client}", "Claude"));
    expect(screen.getByTestId("connect-body")).toHaveTextContent(
      CONNECT_BODY.replace("{client}", "Claude").replace("{names}", "Amma, Appa and Mom"),
    );
    expect(screen.getByText(CONNECT_READ_ONLY)).toBeInTheDocument();
  });

  it("Allow and Not now each call their path", async () => {
    const onAllow = vi.fn().mockResolvedValue(undefined);
    const onCancel = vi.fn().mockResolvedValue(undefined);
    render(
      <ConnectScreen state={{ kind: "ready", clientName: "Claude", names: ["Amma"] }} onAllow={onAllow} onCancel={onCancel} />,
    );
    fireEvent.click(screen.getByTestId("connect-allow"));
    fireEvent.click(screen.getByTestId("connect-cancel"));
    await waitFor(() => expect(onAllow).toHaveBeenCalledTimes(1));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("an expired request says so and offers the way back", () => {
    render(<ConnectScreen state={{ kind: "expired" }} onAllow={noop} onCancel={noop} />);
    expect(screen.getByTestId("connect-expired")).toHaveTextContent(CONNECT_EXPIRED);
    expect(screen.getByTestId("connect-back").getAttribute("href")).toBe("/");
    expect(screen.queryByTestId("connect-allow")).toBeNull();
  });
});

describe("the two calls to the API", () => {
  it("approve posts the request and the decision with the session as a bearer, and returns the redirect", async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ redirect: "https://claude.ai/api/mcp/auth_callback?code=abc&state=s" }),
    });
    const redirect = await approveConnect("req-1", "allow", "session-jwt", fetcher as unknown as typeof fetch);
    expect(redirect).toBe("https://claude.ai/api/mcp/auth_callback?code=abc&state=s");
    const [url, init] = fetcher.mock.calls[0];
    expect(url).toBe(`${API_BASE}/oauth/approve`);
    expect(init.method).toBe("POST");
    expect(init.headers.authorization).toBe("Bearer session-jwt");
    expect(JSON.parse(init.body)).toEqual({ request_id: "req-1", decision: "allow" });
  });

  it("a refused approve and an expired pending request both read as null", async () => {
    const gone = vi.fn().mockResolvedValue({ ok: false, status: 410, json: async () => ({ error: "expired" }) });
    expect(await approveConnect("req-1", "allow", "t", gone as unknown as typeof fetch)).toBeNull();
    expect(await pendingConnect("req-1", gone as unknown as typeof fetch)).toBeNull();
    const fine = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ client_name: "Claude" }) });
    expect(await pendingConnect("req-1", fine as unknown as typeof fetch)).toEqual({ client_name: "Claude" });
    expect(fine.mock.calls[0][0]).toBe(`${API_BASE}/oauth/pending?request=req-1`);
  });

  it("the address the family copies is the MCP endpoint on the API host", () => {
    expect(MCP_URL).toBe(`${API_BASE}/mcp`);
    expect(MCP_URL.startsWith("https://")).toBe(true);
  });
});

const grant = (over: Partial<AssistantGrant>): AssistantGrant => ({
  id: "g1",
  client_name: "Claude",
  created_utc: "2026-09-05T03:30:00Z",
  last_used_utc: "2026-09-05T03:30:00Z",
  revoked_utc: null,
  ...over,
});

function renderFamily(assistants: AssistantGrant[], onRevoke = vi.fn().mockResolvedValue(undefined), viewerTz = "America/New_York") {
  render(
    <FamilyScreen
      parentStates={[]}
      cities={{}}
      members={[]}
      viewerId={null}
      circle={{ onAddSeat: noop, onRemoveSeat: noop, onSetRole: noop, onSetMail: noop, onLeave: noop }}
      setupEntries={[]}
      onOpen={() => undefined}
      onPickCity={noop}
      onClearCity={noop}
      assistants={assistants}
      onRevokeAssistant={onRevoke}
      viewerTz={viewerTz}
    />,
  );
  return onRevoke;
}

describe("the Assistants section on Family (spec 019 §6)", () => {
  it("explains, shows the address with Copy, and says when nothing is connected", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    renderFamily([]);
    expect(screen.getByTestId("assistants")).toHaveTextContent(ASSISTANTS_INTRO);
    expect(screen.getByTestId("mcp-url")).toHaveTextContent(MCP_URL);
    expect(screen.getByTestId("assistants-none")).toHaveTextContent(ASSISTANTS_NONE);
    fireEvent.click(screen.getByTestId("mcp-copy"));
    await waitFor(() => expect(screen.getByTestId("mcp-copy")).toHaveTextContent("Copied"));
    expect(writeText).toHaveBeenCalledWith(MCP_URL);
  });

  it("lists each connection since its date on the viewer's clock, with the fallback name", () => {
    // 03:30Z on Sep 5 is Sep 4 in New York.
    renderFamily([grant({}), grant({ id: "g2", client_name: null })]);
    const rows = screen.getAllByTestId("assistant-grant");
    expect(rows[0]).toHaveTextContent("Claude · since Sep 4");
    expect(rows[1]).toHaveTextContent(`${ASSISTANT_FALLBACK} · since Sep 4`);
    expect(screen.queryByTestId("assistants-none")).toBeNull();
  });

  it("disconnect needs the confirm line, and only the confirm revokes", async () => {
    const onRevoke = renderFamily([grant({})]);
    fireEvent.click(screen.getByTestId("assistant-disconnect"));
    expect(screen.getByTestId("assistant-confirm")).toHaveTextContent(
      ASSISTANTS_DISCONNECT_CONFIRM.replace("{client}", "Claude"),
    );
    expect(onRevoke).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("Keep it"));
    expect(screen.queryByTestId("assistant-confirm")).toBeNull();
    fireEvent.click(screen.getByTestId("assistant-disconnect"));
    fireEvent.click(screen.getByTestId("assistant-disconnect-yes"));
    await waitFor(() => expect(onRevoke).toHaveBeenCalledWith("g1"));
  });
});
