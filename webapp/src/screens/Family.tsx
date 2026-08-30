/**
 * Family (spec 009, slimmed by spec 012 §2): the parents list with the city
 * picker, the spec-005b setup card (the DECISIONS 122 CTA pin), the member
 * roster, and the privacy footer. The consolidated notes feed moved to the
 * Memory tab — this screen is the household's SETTINGS now, and the record
 * lives where the record lives.
 */
import { CityPicker } from "@/components/CityPicker";
import type { CityEntry } from "@/lib/cities";
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
  marginTop: "1.75rem",
  fontSize: "0.75rem",
  fontWeight: 700,
  letterSpacing: ".1em",
  textTransform: "uppercase",
  color: "var(--mute)",
};

const CARD: React.CSSProperties = {
  boxSizing: "border-box",
  background: "var(--card)",
  border: "1px solid var(--hair)",
  borderRadius: "1.375rem",
  marginTop: "0.625rem",
  overflow: "hidden",
};

export function FamilyScreen({
  parentStates,
  cities,
  members,
  setupEntries,
  onOpen,
  onPickCity,
  onClearCity,
}: {
  parentStates: ParentToday[];
  /** parentId → current city label ("" when unset), for the §1 picker. */
  cities: Record<string, string>;
  members: Member[];
  setupEntries: SetupEntry[];
  onOpen: (parentId: string) => void;
  /** Spec 010 §1: the picker is the one surface that moves a parent. */
  onPickCity: (parentId: string, entry: CityEntry) => Promise<void>;
  onClearCity: (parentId: string) => Promise<void>;
}) {
  return (
    <div className="kt-view" style={{ maxWidth: "43.75rem", margin: "0 auto" }} data-testid="family-screen">
      <h1
        className="kt-serif"
        style={{ margin: 0, fontWeight: 500, fontSize: "2.375rem", letterSpacing: "-.01em" }}
      >
        {FAMILY_TITLE}
      </h1>
      <div style={{ marginTop: "0.4375rem", fontSize: "0.9375rem", color: "var(--ink2)", lineHeight: 1.5 }}>
        {FAMILY_SUB}
      </div>

      <div style={KICKER}>{PARENTS_LABEL}</div>
      <div style={CARD}>
        {parentStates.map((state, index) => (
          <div
            key={state.parentId}
            data-testid="roster-parent"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "0.75rem",
              flexWrap: "wrap",
              borderTop: index === 0 ? "1px solid rgba(0,0,0,0)" : "1px solid var(--hair)",
              padding: "0.9375rem 1.25rem",
            }}
          >
            <button
              type="button"
              className="kt-rowbtn"
              onClick={() => onOpen(state.parentId)}
              style={{
                background: "none",
                border: "none",
                textAlign: "left",
                padding: 0,
                cursor: "pointer",
                minWidth: 0,
                minHeight: "2.75rem",
              }}
            >
              <span className="kt-serif" style={{ display: "block", fontWeight: 500, fontSize: "1.1875rem" }}>
                {state.label}
              </span>
              <span
                style={{ display: "block", marginTop: "0.125rem", fontSize: "0.84375rem", color: "var(--ink2)" }}
                data-testid="roster-sub"
              >
                {state.famSub}
              </span>
            </button>
            <CityPicker
              name={state.label}
              committed={cities[state.parentId] ?? ""}
              onPick={(entry) => void onPickCity(state.parentId, entry)}
              onClear={() => void onClearCity(state.parentId)}
            />
          </div>
        ))}
      </div>

      <div style={KICKER}>{SETUP_TITLE}</div>
      <div style={{ ...CARD, padding: "1rem 1.25rem" }}>
        {setupEntries.map((entry) => (
          <div key={entry.parentId} style={{ padding: "0.375rem 0" }} data-testid="setup-entry">
            <div style={{ display: "flex", justifyContent: "space-between", gap: "0.75rem", fontSize: "0.9375rem" }}>
              <span className="kt-serif" style={{ fontWeight: 500, fontSize: "1.0625rem" }}>
                {entry.parentName}
              </span>
              <span style={{ color: "var(--ink2)", fontSize: "0.84375rem" }} data-testid="setup-status">
                {SETUP_STATUS_LABEL[entry.status]}
              </span>
            </div>
            {entry.status === "ready" && entry.shareHref && (
              <div
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  justifyContent: "space-between",
                  gap: "0.5rem",
                  marginTop: "0.125rem",
                }}
              >
                {/* The slug travels inside the href only; the visible text
                    never prints it (it is the page's credential). */}
                <a
                  className="kt-link"
                  style={{ fontSize: "0.90625rem", fontWeight: 600 }}
                  href={entry.shareHref}
                  data-testid="setup-share"
                >
                  {SETUP_SEND_LABEL}
                </a>
                {entry.expiresDate && (
                  <span style={{ fontSize: "0.78125rem", color: "var(--mute)" }}>
                    {SETUP_EXPIRES.replace("{date}", entry.expiresDate)}
                  </span>
                )}
              </div>
            )}
          </div>
        ))}
        {setupEntries.some((entry) => entry.status === "ready") && (
          <div style={{ paddingTop: "0.375rem" }}>
            {SETUP_HOW.map((line) => (
              <p
                key={line}
                style={{ margin: "0.25rem 0 0", fontSize: "0.78125rem", color: "var(--mute)", lineHeight: 1.5 }}
              >
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
              gap: "0.75rem",
              padding: "0.9375rem 1.25rem",
              borderTop: index === 0 ? "1px solid rgba(0,0,0,0)" : "1px solid var(--hair)",
            }}
          >
            <span className="kt-serif" style={{ fontWeight: 500, fontSize: "1.1875rem" }}>
              {member.display_name ?? "—"}
            </span>
            <span style={{ fontSize: "0.84375rem", color: "var(--ink2)" }}>{member.digest_channel}</span>
          </div>
        ))}
      </div>

      <p
        style={{ marginTop: "1.875rem", fontSize: "0.875rem", color: "var(--ink2)", lineHeight: 1.5 }}
        data-testid="privacy-footer"
      >
        {PRIVACY_FOOTER}
      </p>
    </div>
  );
}
