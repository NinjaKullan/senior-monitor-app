/**
 * Family (spec 008 §5.3): the v5 parents-list card with honest sub-lines and
 * no toggles or invites — those are DECISIONS 157's later tier and 169 keeps
 * them out. The setup card (spec 005b) and the member roster are existing,
 * live surfaces and stay, restyled: the setup card is the founder's
 * forwarding flow and its "Send on WhatsApp" CTA is the DECISIONS 122 pin.
 */
import {
  FAMILY_CIRCLE_LABEL,
  FAMILY_SUB,
  FAMILY_TITLE,
  PARENTS_LABEL,
  PRIVACY_FOOTER,
  SETUP_EXPIRES,
  SETUP_HOW,
  SETUP_NEEDS_LINK,
  SETUP_READY,
  SETUP_REPORTING,
  SETUP_SEND_LABEL,
  SETUP_TITLE,
} from "@/lib/copy";
import type { ParentToday } from "@/lib/parentState";
import type { SetupEntry } from "@/lib/setupLinks";
import type { Member } from "@/lib/types";

const SETUP_STATUS_LABEL = {
  reporting: SETUP_REPORTING,
  ready: SETUP_READY,
  needs_link: SETUP_NEEDS_LINK,
} as const;

const KICKER: React.CSSProperties = {
  marginTop: 28,
  fontSize: 12,
  fontWeight: 700,
  letterSpacing: ".1em",
  textTransform: "uppercase",
  color: "var(--ink3)",
};

const CARD: React.CSSProperties = {
  boxSizing: "border-box",
  background: "var(--card)",
  border: "1px solid var(--hair)",
  borderRadius: 22,
  marginTop: 10,
  overflow: "hidden",
};

export function FamilyScreen({
  parentStates,
  members,
  setupEntries,
  onOpen,
}: {
  parentStates: ParentToday[];
  members: Member[];
  setupEntries: SetupEntry[];
  onOpen: (parentId: string) => void;
}) {
  return (
    <div className="kt-view" style={{ maxWidth: 700, margin: "0 auto" }} data-testid="family-screen">
      <h1
        className="kt-serif"
        style={{ margin: 0, fontWeight: 500, fontSize: 38, letterSpacing: "-.01em" }}
      >
        {FAMILY_TITLE}
      </h1>
      <div style={{ marginTop: 7, fontSize: 15, color: "var(--ink2)", lineHeight: 1.5 }}>
        {FAMILY_SUB}
      </div>

      <div style={KICKER}>{PARENTS_LABEL}</div>
      <div style={CARD}>
        {parentStates.map((state, index) => (
          <button
            key={state.parentId}
            type="button"
            className="kt-rowbtn"
            data-testid="roster-parent"
            onClick={() => onOpen(state.parentId)}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 12,
              width: "100%",
              boxSizing: "border-box",
              textAlign: "left",
              background: "none",
              border: "none",
              borderTop: index === 0 ? "1px solid rgba(0,0,0,0)" : "1px solid var(--hair)",
              padding: "15px 20px",
              cursor: "pointer",
            }}
          >
            <span style={{ minWidth: 0 }}>
              <span className="kt-serif" style={{ display: "block", fontWeight: 500, fontSize: 19 }}>
                {state.name}
              </span>
              <span
                style={{ display: "block", marginTop: 2, fontSize: 13.5, color: "var(--ink2)" }}
                data-testid="roster-sub"
              >
                {state.famSub}
              </span>
            </span>
            <span style={{ fontSize: 18, color: "var(--ink3)" }} aria-hidden="true">
              ›
            </span>
          </button>
        ))}
      </div>

      <div style={KICKER}>{SETUP_TITLE}</div>
      <div style={{ ...CARD, padding: "16px 20px" }}>
        {setupEntries.map((entry) => (
          <div key={entry.parentId} style={{ padding: "6px 0" }} data-testid="setup-entry">
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, fontSize: 15 }}>
              <span className="kt-serif" style={{ fontWeight: 500, fontSize: 17 }}>
                {entry.parentName}
              </span>
              <span style={{ color: "var(--ink2)", fontSize: 13.5 }} data-testid="setup-status">
                {SETUP_STATUS_LABEL[entry.status]}
              </span>
            </div>
            {entry.status === "ready" && entry.shareHref && (
              <div
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  justifyContent: "space-between",
                  gap: 8,
                  marginTop: 2,
                }}
              >
                {/* The slug travels inside the href only; the visible text
                    never prints it (it is the page's credential). */}
                <a className="kt-link" style={{ fontSize: 14.5, fontWeight: 600 }} href={entry.shareHref} data-testid="setup-share">
                  {SETUP_SEND_LABEL}
                </a>
                {entry.expiresDate && (
                  <span style={{ fontSize: 12.5, color: "var(--ink3)" }}>
                    {SETUP_EXPIRES.replace("{date}", entry.expiresDate)}
                  </span>
                )}
              </div>
            )}
          </div>
        ))}
        {setupEntries.some((entry) => entry.status === "ready") && (
          <div style={{ paddingTop: 6 }}>
            {SETUP_HOW.map((line) => (
              <p key={line} style={{ margin: "4px 0 0", fontSize: 12.5, color: "var(--ink3)", lineHeight: 1.5 }}>
                {line}
              </p>
            ))}
          </div>
        )}
      </div>

      <div style={KICKER}>{FAMILY_CIRCLE_LABEL}</div>
      <div style={CARD}>
        {members.map((member, index) => (
          <div
            key={member.id}
            data-testid="roster-member"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 12,
              padding: "15px 20px",
              borderTop: index === 0 ? "1px solid rgba(0,0,0,0)" : "1px solid var(--hair)",
            }}
          >
            <span className="kt-serif" style={{ fontWeight: 500, fontSize: 19 }}>
              {member.display_name ?? "—"}
            </span>
            <span style={{ fontSize: 13.5, color: "var(--ink2)" }}>{member.digest_channel}</span>
          </div>
        ))}
      </div>

      <p
        style={{ marginTop: 30, fontSize: 14, color: "var(--ink2)", lineHeight: 1.5 }}
        data-testid="privacy-footer"
      >
        {PRIVACY_FOOTER}
      </p>
    </div>
  );
}
