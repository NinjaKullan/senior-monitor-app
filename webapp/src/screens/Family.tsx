/**
 * Family (spec 009): the parents list (with the §5 city field), the
 * consolidated Family notes list (§4 — every entry, tag-prefixed, and a
 * composer whose tag is selectable), the spec-005b setup card (the DECISIONS
 * 122 CTA pin), the member roster, and the privacy footer.
 */
import { useState } from "react";
import { NotesPanel, type NoteDraft, type TagOption } from "@/components/NotesPanel";
import {
  AUTHOR_FALLBACK,
  CITY_FIELD_LABEL,
  CITY_MAX_CHARS,
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
import type { JournalEntry, Member } from "@/lib/types";

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

function CityField({
  parentId,
  initial,
  onSave,
}: {
  parentId: string;
  initial: string;
  onSave: (parentId: string, city: string | null) => Promise<void>;
}) {
  const [value, setValue] = useState(initial);
  const save = () => {
    const trimmed = value.trim().slice(0, CITY_MAX_CHARS);
    if (trimmed === initial) return;
    void onSave(parentId, trimmed === "" ? null : trimmed);
  };
  return (
    <label
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.375rem",
        fontSize: "0.8125rem",
        color: "var(--mute)",
      }}
    >
      {CITY_FIELD_LABEL}
      <input
        type="text"
        value={value}
        maxLength={CITY_MAX_CHARS}
        onChange={(event) => setValue(event.target.value)}
        onBlur={save}
        onKeyDown={(event) => {
          if (event.key === "Enter") save();
        }}
        style={{
          border: "1px solid var(--hair)",
          borderRadius: "999px",
          padding: "0.375rem 0.75rem",
          fontSize: "0.8125rem",
          color: "var(--ink)",
          background: "var(--paper)",
          width: "9rem",
        }}
        data-testid="city-input"
      />
    </label>
  );
}

export function FamilyScreen({
  parentStates,
  cities,
  members,
  setupEntries,
  journal,
  todayDate,
  onOpen,
  onAddNote,
  onSaveCity,
}: {
  parentStates: ParentToday[];
  /** parentId → current city label ("" when unset), for the §5 field. */
  cities: Record<string, string>;
  members: Member[];
  setupEntries: SetupEntry[];
  journal: JournalEntry[];
  todayDate: string;
  onOpen: (parentId: string) => void;
  onAddNote: (draft: NoteDraft) => Promise<void>;
  onSaveCity: (parentId: string, city: string | null) => Promise<void>;
}) {
  const labelById = new Map(parentStates.map((s) => [s.parentId, s.label]));
  const tagOptions: TagOption[] = [
    ...parentStates.map((s) => ({ parentId: s.parentId, label: s.label })),
    { parentId: null, label: AUTHOR_FALLBACK },
  ];
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
            <CityField
              parentId={state.parentId}
              initial={cities[state.parentId] ?? ""}
              onSave={onSaveCity}
            />
          </div>
        ))}
      </div>

      <div style={{ marginTop: "1.75rem" }}>
        <NotesPanel
          entries={journal}
          todayDate={todayDate}
          onAdd={onAddNote}
          tagOptions={tagOptions}
          tagLabelFor={(entry: JournalEntry) =>
            entry.parent_id === null
              ? AUTHOR_FALLBACK
              : (labelById.get(entry.parent_id) ?? AUTHOR_FALLBACK)
          }
        />
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
