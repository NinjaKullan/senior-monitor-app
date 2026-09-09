/**
 * /connect (spec 019 §6): the one consent screen between an assistant's
 * request and Allow. Reached from kettle-api's /oauth/authorize; if the
 * person is not signed in, App shows the 013 login first and comes back here
 * with the same URL. Allow posts to /oauth/approve with the person's session
 * and follows the redirect the API hands back; Not now denies the same way.
 */
import {
  CONNECT_ALLOW,
  CONNECT_BACK,
  CONNECT_BODY,
  CONNECT_BODY_WRITE,
  CONNECT_CANCEL,
  CONNECT_EXPIRED,
  CONNECT_LOADING,
  CONNECT_READ_ONLY,
  CONNECT_TITLE,
  CONNECT_WRITE_NOTE,
} from "@/lib/copy";
import { Action } from "@/components/ui/action";
import { joinNames } from "@/lib/parentState";

export type ConnectState =
  | { kind: "loading" }
  | { kind: "expired" }
  | { kind: "ready"; clientName: string; names: string[]; write?: boolean };

export function ConnectScreen({
  state,
  onAllow,
  onCancel,
}: {
  state: ConnectState;
  onAllow: () => Promise<void>;
  onCancel: () => Promise<void>;
}) {
  return (
    <div className="kt-view" style={{ maxWidth: "28rem", margin: "0 auto" }} data-testid="connect-screen">
      {state.kind === "loading" && <p style={{ color: "var(--ink2)" }}>{CONNECT_LOADING}</p>}
      {state.kind === "expired" && (
        <>
          <p style={{ color: "var(--ink2)", lineHeight: 1.5 }} data-testid="connect-expired">
            {CONNECT_EXPIRED}
          </p>
          <Action variant="quiet" href="/" data-testid="connect-back">
            {CONNECT_BACK}
          </Action>
        </>
      )}
      {state.kind === "ready" && (
        <>
          <h1
            className="kt-serif"
            style={{ margin: 0, fontWeight: 500, fontSize: "1.875rem", lineHeight: 1.2 }}
            data-testid="connect-title"
          >
            {CONNECT_TITLE.replace("{client}", state.clientName)}
          </h1>
          <p style={{ fontSize: "0.9375rem", lineHeight: 1.5, color: "var(--ink)" }} data-testid="connect-body">
            {(state.write ? CONNECT_BODY_WRITE : CONNECT_BODY)
              .replace("{client}", state.clientName)
              .replace("{names}", joinNames(state.names))}
          </p>
          <p style={{ fontSize: "0.875rem", lineHeight: 1.5, color: "var(--ink2)" }} data-testid="connect-note">
            {state.write ? CONNECT_WRITE_NOTE : CONNECT_READ_ONLY}
          </p>
          <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.25rem" }}>
            <Action variant="primary" onClick={() => void onAllow()} data-testid="connect-allow">
              {CONNECT_ALLOW}
            </Action>
            <Action variant="quiet" onClick={() => void onCancel()} data-testid="connect-cancel">
              {CONNECT_CANCEL}
            </Action>
          </div>
        </>
      )}
    </div>
  );
}
