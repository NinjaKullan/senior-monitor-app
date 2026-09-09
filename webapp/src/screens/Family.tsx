/**
 * Family (spec 009, slimmed by spec 012 §2): the parents list with the city
 * picker, the spec-005b setup card (the DECISIONS 122 CTA pin), the member
 * roster, and the privacy footer. The consolidated notes feed moved to the
 * Memory tab — this screen is the household's SETTINGS now, and the record
 * lives where the record lives.
 */
import { useState } from "react";
import { Action } from "@/components/ui/action";
import { CityPicker } from "@/components/CityPicker";
import type { CityEntry } from "@/lib/cities";
import { circleRefusal, isAdmin, nobodyListening } from "@/lib/circle";
import { MCP_URL } from "@/lib/data";
import { localDay, monthDay } from "@/lib/journal";
import {
  ASSISTANTS_COPIED,
  ASSISTANTS_COPY,
  ASSISTANTS_DISCONNECT,
  ASSISTANTS_DISCONNECT_CONFIRM,
  ASSISTANTS_DISCONNECT_NO,
  ASSISTANTS_DISCONNECT_YES,
  ASSISTANTS_INTRO,
  ASSISTANTS_NONE,
  ASSISTANTS_SECTION,
  ASSISTANTS_SINCE,
  ASSISTANTS_SINCE_WRITE,
  ASSISTANT_FALLBACK,
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
  COMPOSER_FAILED,
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
  SMS_CONSENT_BUTTON,
  SMS_CONSENT_SCRIPT,
  SMS_ROW_ON,
  SMS_ROW_STOPPED,
  SMS_SCRIPT_LABEL,
  DEVICES_INTRO,
  DEVICE_ADD,
  DEVICE_ADD_CANCEL,
  DEVICE_ADD_DONE,
  DEVICE_ADD_KIND,
  DEVICE_ADD_PLATFORM,
  DEVICE_ADDRESS,
  DEVICE_COPIED,
  DEVICE_LIMIT,
  DEVICE_REMOVE,
  DEVICE_REMOVE_CONFIRM,
  DEVICE_REMOVE_NO,
  DEVICE_REMOVE_YES,
  DEVICE_ROW,
  DEVICE_NOTHING_YET,
  DEVICE_TELL,
  KIND_LABEL,
  PLATFORM_LABEL,
  RECIPE,
} from "@/lib/copy";
import { DEVICE_LIMIT_PER_PARENT, kindLabel, type DeviceSetupRow } from "@/lib/household";
import type { ParentToday } from "@/lib/parentState";
import type { SetupEntry } from "@/lib/setupLinks";
import type { AssistantGrant, Member } from "@/lib/types";

const SETUP_STATUS_LABEL = {
  reporting: SETUP_REPORTING,
  ready: SETUP_READY,
  needs_link: SETUP_NEEDS_LINK,
  paused: PAUSED_SETUP,
} as const;

/** The row's state line (Amendment A.6): Paused wins; then the texting
 *  state stands in for the link state; else the link state. */
function setupRowLabel(entry: SetupEntry): string {
  if (entry.status === "paused") return PAUSED_SETUP;
  if (entry.sms === "on") return SMS_ROW_ON;
  if (entry.sms === "stopped") return SMS_ROW_STOPPED.replace("{name}", entry.parentName);
  return SETUP_STATUS_LABEL[entry.status];
}

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
  onSmsConsent,
  deviceRows = [],
  household,
  assistants = [],
  onRevokeAssistant,
  viewerTz = "UTC",
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
  /** Amendment A.6: present for admins only (App decides, as for the
   *  pause); a member's row carries the state and never the button. */
  onSmsConsent?: (parentId: string) => Promise<void>;
  /** Spec 020 §5: every live device's setup row, by parent. */
  deviceRows?: DeviceSetupRow[];
  /** Spec 020: admins only (App decides, the pause and consent gate); a
   *  member's rows carry the state and neither the address nor a control. */
  household?: HouseholdActions;
  /** Spec 019 §6: the viewer's own assistant connections and the disconnect. */
  assistants?: AssistantGrant[];
  onRevokeAssistant?: (grantId: string) => Promise<void>;
  /** The viewer's browser zone, for "since {date}" (279). */
  viewerTz?: string;
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
              flexDirection: "column",
              alignItems: "stretch",
              gap: "0.5rem",
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
                {setupRowLabel(entry)}
              </span>
            </div>
            {entry.sms === "offer" && onSmsConsent && entry.status !== "paused" && (
              <SmsConsent entry={entry} onConsent={onSmsConsent} />
            )}
            <HouseholdDevices
              parentId={entry.parentId}
              parentName={entry.parentName}
              rows={deviceRows.filter((row) => row.parentId === entry.parentId)}
              household={household}
            />
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

      <div style={KICKER}>{ASSISTANTS_SECTION}</div>
      <Assistants grants={assistants} onRevoke={onRevokeAssistant} viewerTz={viewerTz} />

      <p
        style={{ marginTop: "1.875rem", fontSize: "0.875rem", color: "var(--ink2)", lineHeight: 1.5 }}
        data-testid="privacy-footer"
      >
        {PRIVACY_FOOTER}
      </p>
    </div>
  );
}


export interface HouseholdActions {
  /** Returns the new device's id, so its recipe can sit under its row. */
  onAdd: (parentId: string, kind: string, platform: string | null) => Promise<string>;
  onRemove: (deviceId: string) => Promise<void>;
  /** The full address, for the clipboard only; never rendered. */
  onAddress: (deviceId: string) => Promise<string>;
}

/**
 * Spec 020 §5: the parent's devices under the phone row. The intro and the
 * parent-told line always; each device as "{kind} · {heard}"; for admins the
 * address copy, Remove with a confirm, and Add (a two-pick sheet) until the
 * limit. The recipe appears under a row the moment it is added, and again
 * whenever its address is copied, so the plumbing words sit next to the
 * thing they are for.
 */
function HouseholdDevices({
  parentId,
  parentName,
  rows,
  household,
}: {
  parentId: string;
  parentName: string;
  rows: DeviceSetupRow[];
  household?: HouseholdActions;
}) {
  const [adding, setAdding] = useState(false);
  const [kind, setKind] = useState<string>("plug");
  const [platform, setPlatform] = useState<string>("ifttt");
  const [recipeFor, setRecipeFor] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [removing, setRemoving] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  // DECISIONS 324 (315): the row is shown the moment the function returns
  // its id and the refetch reconciles; a removed row goes at once. A failed
  // add removes its row and shows nothing; a failed remove brings it back.
  const [pendingRows, setPendingRows] = useState<DeviceSetupRow[]>([]);
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  // The full address in view, admins only, fetched when a row is expanded
  // (added or copied); never rendered for members, who have no `household`.
  const [addresses, setAddresses] = useState<Record<string, string>>({});
  const small = { fontSize: "0.84375rem", color: "var(--ink2)" } as const;
  const known = new Set(rows.map((r) => r.id));
  const shown = [...rows, ...pendingRows.filter((r) => !known.has(r.id))].filter(
    (r) => !hidden.has(r.id),
  );

  const reveal = (id: string) => {
    if (!household) return Promise.resolve("");
    return household.onAddress(id).then((address) => {
      setAddresses((held) => ({ ...held, [id]: address }));
      return address;
    });
  };
  const add = () => {
    if (!household) return;
    setBusy(true);
    setFailed(false);
    const chosenKind = kind;
    const chosenPlatform = platform;
    household
      .onAdd(parentId, chosenKind, chosenPlatform)
      .then((id) => {
        setPendingRows((held) => [
          ...held,
          {
            id,
            parentId,
            kind: chosenKind,
            platform: chosenPlatform,
            text: DEVICE_ROW.replace("{kind}", kindLabel(chosenKind)).replace("{time}", DEVICE_NOTHING_YET),
          },
        ]);
        setRecipeFor(id);
        setAdding(false);
        void reveal(id).catch(() => undefined);
      })
      .catch(() => setFailed(true))
      .finally(() => setBusy(false));
  };
  const copy = (row: DeviceSetupRow) => {
    if (!household) return;
    reveal(row.id)
      .then(async (address) => {
        await navigator.clipboard.writeText(address);
        setCopied(row.id);
        setRecipeFor(row.id);
        window.setTimeout(() => setCopied((held) => (held === row.id ? null : held)), 2000);
      })
      .catch(() => setFailed(true));
  };
  const remove = (row: DeviceSetupRow) => {
    if (!household) return;
    setBusy(true);
    setHidden((held) => new Set([...held, row.id]));
    setRemoving(null);
    household
      .onRemove(row.id)
      .then(() => setPendingRows((held) => held.filter((r) => r.id !== row.id)))
      .catch(() => {
        setHidden((held) => {
          const next = new Set(held);
          next.delete(row.id);
          return next;
        });
        setFailed(true);
      })
      .finally(() => setBusy(false));
  };

  return (
    <div style={{ marginTop: "0.5rem" }} data-testid="household">
      <p style={{ margin: 0, ...small }}>{DEVICES_INTRO.split("{name}").join(parentName)}</p>
      <p style={{ margin: "0.25rem 0 0", ...small }} data-testid="device-tell">
        {DEVICE_TELL.replace("{name}", parentName)}
      </p>
      {shown.map((row) => (
        <div key={row.id} style={{ marginTop: "0.5rem" }} data-testid="device-setup-row">
          <div style={{ display: "flex", justifyContent: "space-between", gap: "0.5rem", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.9375rem" }} data-testid="device-setup-text">
              {row.text}
            </span>
            {household && removing !== row.id && (
              <span style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
                <Action variant="secondary" data-testid="device-address" onClick={() => copy(row)}>
                  {copied === row.id ? DEVICE_COPIED : DEVICE_ADDRESS}
                </Action>
                <Action variant="quiet" data-testid="device-remove" onClick={() => setRemoving(row.id)}>
                  {DEVICE_REMOVE}
                </Action>
              </span>
            )}
          </div>
          {household && addresses[row.id] && (
            <code
              style={{ display: "block", marginTop: "0.25rem", fontSize: "0.78125rem", overflowWrap: "anywhere" }}
              data-testid="device-address-line"
            >
              {addresses[row.id]}
            </code>
          )}
          {household && removing === row.id && (
            <div style={{ marginTop: "0.25rem", ...small }} data-testid="device-remove-confirm">
              {DEVICE_REMOVE_CONFIRM.replace("{kind}", kindLabel(row.kind).toLowerCase())}
              <span style={{ display: "inline-flex", gap: "0.75rem", marginLeft: "0.75rem" }}>
                <Action variant="secondary" disabled={busy} data-testid="device-remove-yes" onClick={() => remove(row)}>
                  {DEVICE_REMOVE_YES}
                </Action>
                <Action variant="quiet" data-testid="device-remove-no" onClick={() => setRemoving(null)}>
                  {DEVICE_REMOVE_NO}
                </Action>
              </span>
            </div>
          )}
          {household && recipeFor === row.id && (
            <p style={{ margin: "0.25rem 0 0", fontSize: "0.78125rem", color: "var(--mute)", lineHeight: 1.5 }} data-testid="device-recipe">
              {RECIPE[(row.platform ?? "other") as keyof typeof RECIPE] ?? RECIPE.other}
            </p>
          )}
        </div>
      ))}
      {household && shown.length >= DEVICE_LIMIT_PER_PARENT && (
        <p style={{ margin: "0.5rem 0 0", ...small }} data-testid="device-limit">
          {DEVICE_LIMIT.replace("{name}", parentName)}
        </p>
      )}
      {household && shown.length < DEVICE_LIMIT_PER_PARENT && !adding && (
        <div style={{ marginTop: "0.5rem" }}>
          <Action variant="secondary" data-testid="device-add" onClick={() => setAdding(true)}>
            {DEVICE_ADD}
          </Action>
        </div>
      )}
      {household && adding && (
        <div style={{ marginTop: "0.5rem", display: "grid", gap: "0.5rem" }} data-testid="device-add-sheet">
          <label style={small}>
            {DEVICE_ADD_KIND}
            <select style={FIELD} value={kind} onChange={(e) => setKind(e.target.value)} data-testid="device-kind">
              {Object.entries(KIND_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label style={small}>
            {DEVICE_ADD_PLATFORM}
            <select style={FIELD} value={platform} onChange={(e) => setPlatform(e.target.value)} data-testid="device-platform">
              {Object.entries(PLATFORM_LABEL).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <Action variant="primary" disabled={busy} data-testid="device-add-done" onClick={add}>
              {DEVICE_ADD_DONE}
            </Action>
            <Action variant="quiet" data-testid="device-add-cancel" onClick={() => setAdding(false)}>
              {DEVICE_ADD_CANCEL}
            </Action>
          </div>
        </div>
      )}
      {failed && (
        <p style={{ margin: "0.25rem 0 0", fontSize: "0.78125rem", color: "var(--mute)" }}>{COMPOSER_FAILED}</p>
      )}
    </div>
  );
}


/**
 * Amendment A.6 (DECISIONS 290): the consent script as words to say, then
 * the one control that enrols. No checkbox, no second screen — the button IS
 * the enrollment, and the server records the yes once.
 */
function SmsConsent({
  entry,
  onConsent,
}: {
  entry: SetupEntry;
  onConsent: (parentId: string) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  return (
    <div style={{ marginTop: "0.375rem" }} data-testid="sms-consent">
      <p style={{ margin: 0, fontSize: "0.84375rem", color: "var(--ink2)" }}>
        {SMS_SCRIPT_LABEL.replace("{name}", entry.parentName)}
      </p>
      <p
        className="kt-serif"
        style={{ margin: "0.375rem 0 0", fontSize: "0.9375rem", lineHeight: 1.55 }}
        data-testid="sms-consent-script"
      >
        {SMS_CONSENT_SCRIPT}
      </p>
      <Action
        variant="secondary"
        className="kt-mt2"
        disabled={busy}
        data-testid="sms-consent-button"
        onClick={() => {
          setBusy(true);
          setFailed(false);
          onConsent(entry.parentId)
            .catch(() => setFailed(true))
            .finally(() => setBusy(false));
        }}
      >
        {SMS_CONSENT_BUTTON}
      </Action>
      {failed && (
        <p style={{ margin: "0.25rem 0 0", fontSize: "0.78125rem", color: "var(--mute)" }}>
          {COMPOSER_FAILED}
        </p>
      )}
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
                <Action variant="quiet" data-testid="seat-leave" onClick={() => void attempt(circle.onLeave)}>
                  {CIRCLE_LEAVE}
                </Action>
              )}
              {admin && !mine && confirming !== member.id && (
                <>
                  <Action
                    variant="secondary"
                    data-testid="seat-role"
                    onClick={() =>
                      void attempt(() =>
                        circle.onSetRole(member.id, member.role === "admin" ? "member" : "admin"),
                      )
                    }
                  >
                    {member.role === "admin" ? CIRCLE_MAKE_MEMBER : CIRCLE_MAKE_ADMIN}
                  </Action>
                  <Action variant="quiet" data-testid="seat-remove" onClick={() => setConfirming(member.id)}>
                    {CIRCLE_REMOVE}
                  </Action>
                </>
              )}
              {admin && !mine && confirming === member.id && (
                <span style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap", fontSize: "0.84375rem" }} data-testid="seat-confirm">
                  {CIRCLE_REMOVE_CONFIRM}
                  <Action
                    variant="secondary"
                    data-testid="seat-remove-confirm"
                    onClick={() =>
                      void attempt(() => circle.onRemoveSeat(member.id), () => setConfirming(null))
                    }
                  >
                    {CIRCLE_REMOVE}
                  </Action>
                  <Action variant="quiet" onClick={() => setConfirming(null)}>
                    {CIRCLE_KEEP}
                  </Action>
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
          <Action variant="secondary" data-testid="seat-add" onClick={() => setAdding(true)}>
            {CIRCLE_ADD}
          </Action>
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
            <Action variant="primary" type="submit" data-testid="seat-add-submit">
              {CIRCLE_ADD_SUBMIT}
            </Action>
            <Action variant="quiet" onClick={() => setAdding(false)}>
              {CIRCLE_ADD_CANCEL}
            </Action>
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

/**
 * The Assistants section (spec 019 §6): how to add Kettle as a connector, the
 * address with Copy, and the viewer's own connections with Disconnect behind
 * one confirm line. The assistant's own Connectors screen is canonical; this
 * explains it and lists what is connected.
 */
function Assistants({
  grants,
  onRevoke,
  viewerTz,
}: {
  grants: AssistantGrant[];
  onRevoke?: (grantId: string) => Promise<void>;
  viewerTz: string;
}) {
  const [copied, setCopied] = useState(false);
  const [confirming, setConfirming] = useState<string | null>(null);
  const copyAddress = async () => {
    try {
      await navigator.clipboard.writeText(MCP_URL);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };
  return (
    <div style={CARD} data-testid="assistants">
      <p style={{ ...ROW, margin: 0, fontSize: "0.875rem", lineHeight: 1.5, color: "var(--ink2)" }}>
        {ASSISTANTS_INTRO}
      </p>
      <div style={ROW}>
        <code style={{ fontSize: "0.84375rem", overflowWrap: "anywhere" }} data-testid="mcp-url">
          {MCP_URL}
        </code>
        <Action variant="secondary" data-testid="mcp-copy" onClick={() => void copyAddress()}>
          {copied ? ASSISTANTS_COPIED : ASSISTANTS_COPY}
        </Action>
      </div>
      {grants.length === 0 && (
        <p style={{ ...ROW, margin: 0, fontSize: "0.84375rem", color: "var(--ink2)" }} data-testid="assistants-none">
          {ASSISTANTS_NONE}
        </p>
      )}
      {grants.map((grant) => {
        const client = grant.client_name ?? ASSISTANT_FALLBACK;
        return (
          <div key={grant.id} style={{ ...ROW, borderTop: "1px solid var(--hair)" }} data-testid="assistant-grant">
            <span style={{ fontSize: "0.9375rem" }}>
              {(grant.scope.split(" ").includes("kettle:write") ? ASSISTANTS_SINCE_WRITE : ASSISTANTS_SINCE).replace("{client}", client).replace(
                "{date}",
                monthDay(localDay(grant.created_utc, viewerTz)),
              )}
            </span>
            {onRevoke && confirming !== grant.id && (
              <Action variant="quiet" data-testid="assistant-disconnect" onClick={() => setConfirming(grant.id)}>
                {ASSISTANTS_DISCONNECT}
              </Action>
            )}
            {onRevoke && confirming === grant.id && (
              <span style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap", fontSize: "0.84375rem" }} data-testid="assistant-confirm">
                {ASSISTANTS_DISCONNECT_CONFIRM.replace("{client}", client)}
                <Action
                  variant="secondary"
                  data-testid="assistant-disconnect-yes"
                  onClick={() => void onRevoke(grant.id).then(() => setConfirming(null))}
                >
                  {ASSISTANTS_DISCONNECT_YES}
                </Action>
                <Action variant="quiet" onClick={() => setConfirming(null)}>
                  {ASSISTANTS_DISCONNECT_NO}
                </Action>
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
