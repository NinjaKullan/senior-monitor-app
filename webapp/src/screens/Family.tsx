/**
 * Family (spec 009, slimmed by spec 012 §2): the parents list with the city
 * picker, the spec-005b setup card (the DECISIONS 122 CTA pin), the member
 * roster, and the privacy footer. The consolidated notes feed moved to the
 * Memory tab — this screen is the household's SETTINGS now, and the record
 * lives where the record lives.
 */
import { useState } from "react";
import { CityPicker } from "@/components/CityPicker";
import type { CityEntry } from "@/lib/cities";
import { circleRefusal, isAdmin, nobodyListening } from "@/lib/circle";
import {
  CIRCLE_ADD,
  CIRCLE_ADD_CANCEL,
  CIRCLE_ADD_EMAIL,
  CIRCLE_ADD_NAME,
  CIRCLE_ADD_SUBMIT,
  CIRCLE_ADDED,
  CIRCLE_KEEP,
  CIRCLE_LEAVE,
  CIRCLE_MAIL_SWITCH,
  CIRCLE_MAKE_ADMIN,
  CIRCLE_MAKE_MEMBER,
  CIRCLE_NO_MAIL,
  CIRCLE_PENDING,
  CIRCLE_REMOVE,
  CIRCLE_REMOVE_CONFIRM,
  CIRCLE_ROLE_ADMIN,
  CIRCLE_ROLE_MEMBER,
  CIRCLE_SECTION,
  FAMILY_SUB,
  FAMILY_TITLE,
  PARENTS_LABEL,
  PAUSED_SETUP,
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
  paused: PAUSED_SETUP,
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

/** What the seats list can do (spec 015 §6), each the App's thin wrapper
 *  over one 0025 function. A refusal rejects; the screen turns the codes a
 *  person can act on into §9's sentences and leaves the rest silent. */
export interface CircleActions {
  onAddSeat: (displayName: string, email: string) => Promise<void>;
  onRemoveSeat: (memberId: string) => Promise<void>;
  onSetRole: (memberId: string, role: "admin" | "member") => Promise<void>;
  onSetMail: (mail: boolean) => Promise<void>;
  onLeave: () => Promise<void>;
}

const ROW: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "0.75rem",
  flexWrap: "wrap",
  padding: "0.9375rem 1.25rem",
};

const SMALL_BTN: React.CSSProperties = {
  background: "none",
  border: "1px solid var(--hair)",
  borderRadius: "0.75rem",
  padding: "0.5rem 0.75rem",
  minHeight: "2.75rem",
  fontSize: "0.84375rem",
  fontWeight: 600,
  color: "var(--ink2)",
  cursor: "pointer",
};

const FIELD: React.CSSProperties = {
  boxSizing: "border-box",
  width: "100%",
  minHeight: "2.75rem",
  padding: "0.5rem 0.75rem",
  border: "1px solid var(--hair)",
  borderRadius: "0.75rem",
  background: "var(--paper)",
  color: "var(--ink)",
  fontSize: "0.9375rem",
};

export function FamilyScreen({
  parentStates,
  cities,
  members,
  viewerId,
  circle,
  setupEntries,
  onOpen,
  onPickCity,
  onClearCity,
}: {
  parentStates: ParentToday[];
  /** parentId → current city label ("" when unset), for the §1 picker. */
  cities: Record<string, string>;
  members: Member[];
  /** The signed-in auth user's id: which seat is "me" (own mail switch,
   *  own leave link), and whether the admin controls render at all. */
  viewerId: string | null;
  circle: CircleActions;
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

      <div style={KICKER}>{CIRCLE_SECTION}</div>
      <SeatsList members={members} viewerId={viewerId} circle={circle} />

      <p
        style={{ marginTop: "1.875rem", fontSize: "0.875rem", color: "var(--ink2)", lineHeight: 1.5 }}
        data-testid="privacy-footer"
      >
        {PRIVACY_FOOTER}
      </p>
    </div>
  );
}


/**
 * The seats list (spec 015 §8): one row per seat, "Name · Admin" or
 * "Name · Member", a claimed seat in full ink and an unclaimed one muted with
 * CIRCLE_PENDING. Admins see "Add someone" and the per-row controls;
 * everyone sees their own "Kettle emails me" switch and their own leave link.
 * Removing shows one confirm line in place of the row's controls, no dialog.
 */
function SeatsList({
  members,
  viewerId,
  circle,
}: {
  members: Member[];
  viewerId: string | null;
  circle: CircleActions;
}) {
  const admin = isAdmin(members, viewerId);
  const [note, setNote] = useState<string | null>(null);
  const [confirming, setConfirming] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  const attempt = async (action: () => Promise<void>, onOk?: () => void) => {
    setNote(null);
    try {
      await action();
      onOk?.();
    } catch (error) {
      setNote(circleRefusal(error));
    }
  };

  const submitAdd = async (event: React.FormEvent) => {
    event.preventDefault();
    await attempt(
      () => circle.onAddSeat(name.trim(), email.trim()),
      () => {
        setName("");
        setEmail("");
        setAdding(false);
        setNote(CIRCLE_ADDED);
      },
    );
  };

  return (
    <div style={CARD} data-testid="seats">
      {members.map((member, index) => {
        const mine = viewerId !== null && member.auth_user_id === viewerId;
        const pending = member.auth_user_id === null;
        const role = member.role === "admin" ? CIRCLE_ROLE_ADMIN : CIRCLE_ROLE_MEMBER;
        return (
          <div
            key={member.id}
            data-testid="roster-member"
            data-pending={pending ? "true" : undefined}
            style={{
              ...ROW,
              borderTop: index === 0 ? "1px solid rgba(0,0,0,0)" : "1px solid var(--hair)",
              color: pending ? "var(--mute)" : "var(--ink)",
            }}
          >
            <div style={{ minWidth: 0 }}>
              <span className="kt-serif" style={{ fontWeight: 500, fontSize: "1.1875rem" }}>
                {member.display_name ?? "—"}
              </span>
              <span style={{ fontSize: "0.84375rem", color: "var(--ink2)" }}> · {role}</span>
              {pending && (
                <span
                  style={{ display: "block", fontSize: "0.78125rem", color: "var(--mute)" }}
                  data-testid="seat-pending"
                >
                  {CIRCLE_PENDING}
                </span>
              )}
            </div>
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
              {mine && (
                <label style={{ display: "flex", gap: "0.5rem", alignItems: "center", fontSize: "0.84375rem", minHeight: "2.75rem" }}>
                  <input
                    type="checkbox"
                    checked={member.mail}
                    data-testid="mail-switch"
                    onChange={(event) => void attempt(() => circle.onSetMail(event.target.checked))}
                  />
                  {CIRCLE_MAIL_SWITCH}
                </label>
              )}
              {mine && (
                <button
                  type="button"
                  style={SMALL_BTN}
                  data-testid="seat-leave"
                  onClick={() => void attempt(circle.onLeave)}
                >
                  {CIRCLE_LEAVE}
                </button>
              )}
              {admin && !mine && confirming !== member.id && (
                <>
                  <button
                    type="button"
                    style={SMALL_BTN}
                    data-testid="seat-role"
                    onClick={() =>
                      void attempt(() =>
                        circle.onSetRole(member.id, member.role === "admin" ? "member" : "admin"),
                      )
                    }
                  >
                    {member.role === "admin" ? CIRCLE_MAKE_MEMBER : CIRCLE_MAKE_ADMIN}
                  </button>
                  <button
                    type="button"
                    style={SMALL_BTN}
                    data-testid="seat-remove"
                    onClick={() => setConfirming(member.id)}
                  >
                    {CIRCLE_REMOVE}
                  </button>
                </>
              )}
              {admin && !mine && confirming === member.id && (
                <span style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap", fontSize: "0.84375rem" }} data-testid="seat-confirm">
                  {CIRCLE_REMOVE_CONFIRM}
                  <button
                    type="button"
                    style={SMALL_BTN}
                    data-testid="seat-remove-confirm"
                    onClick={() =>
                      void attempt(() => circle.onRemoveSeat(member.id), () => setConfirming(null))
                    }
                  >
                    {CIRCLE_REMOVE}
                  </button>
                  <button type="button" style={SMALL_BTN} onClick={() => setConfirming(null)}>
                    {CIRCLE_KEEP}
                  </button>
                </span>
              )}
            </div>
          </div>
        );
      })}
      {nobodyListening(members) && (
        <p style={{ ...ROW, margin: 0, fontSize: "0.84375rem", color: "var(--ink2)" }} data-testid="circle-no-mail">
          {CIRCLE_NO_MAIL}
        </p>
      )}
      {admin && !adding && (
        <div style={ROW}>
          <button type="button" style={SMALL_BTN} data-testid="seat-add" onClick={() => setAdding(true)}>
            {CIRCLE_ADD}
          </button>
        </div>
      )}
      {admin && adding && (
        <form onSubmit={(event) => void submitAdd(event)} style={{ ...ROW, flexDirection: "column", alignItems: "stretch" }} data-testid="seat-add-form">
          <label style={{ fontSize: "0.84375rem", color: "var(--ink2)" }}>
            {CIRCLE_ADD_NAME}
            <input style={FIELD} value={name} onChange={(event) => setName(event.target.value)} required />
          </label>
          <label style={{ fontSize: "0.84375rem", color: "var(--ink2)" }}>
            {CIRCLE_ADD_EMAIL}
            <input style={FIELD} type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button type="submit" style={SMALL_BTN} data-testid="seat-add-submit">
              {CIRCLE_ADD_SUBMIT}
            </button>
            <button type="button" style={SMALL_BTN} onClick={() => setAdding(false)}>
              {CIRCLE_ADD_CANCEL}
            </button>
          </div>
        </form>
      )}
      {note && (
        <p style={{ ...ROW, margin: 0, fontSize: "0.84375rem", color: "var(--ink2)" }} data-testid="circle-note">
          {note}
        </p>
      )}
    </div>
  );
}
