/**
 * The family contacts sheet, "If you can't reach them" (spec 012 §4): the
 * digital twin of the emergency printable. Family-entered ONLY — never
 * auto-populated, no directory, no lookup; a stale emergency number we
 * suggested is worse than a blank line the family owns (DECISIONS 200).
 *
 * UNLIKE notes, contacts are editable and deletable: reference data, not
 * record. Numbers obey the elder-proofing law the rest of the app lives by,
 * with the one spec-012 amendment: the tel: href carries E.164 and the
 * VISIBLE text is phone_display — the single place this app shows a phone
 * number as text, scoped to data-testid="contact-phone" and exempted by name
 * in the copy scan.
 */

import { useState } from "react";
import {
  CONTACT_ADD_LABEL,
  CONTACT_MOVE_DOWN,
  CONTACT_MOVE_UP,
  CONTACT_TAG_EVERYONE,
  CONTACT_TAG_LABEL,
  CONTACT_EDIT_LABEL,
  CONTACT_NAME_PLACEHOLDER,
  CONTACT_NOTE_PLACEHOLDER,
  CONTACT_PHONE_PLACEHOLDER,
  CONTACT_REMOVE_LABEL,
  CONTACT_SAVE_LABEL,
  CONTACT_SUGGESTED_LABELS,
} from "@/lib/copy";
import { telHrefNumber, type ContactDraft } from "@/lib/data";
import type { FamilyContact } from "@/lib/types";

const FIELD: React.CSSProperties = {
  border: "1px solid var(--hair)",
  borderRadius: "999px",
  padding: "0.4375rem 0.75rem",
  fontSize: "0.8125rem",
  color: "var(--ink)",
  background: "var(--paper)",
  minHeight: "2.25rem",
  boxSizing: "border-box",
};

const CHIP: React.CSSProperties = {
  border: "1px solid var(--hair)",
  borderRadius: "999px",
  padding: "0.375rem 0.75rem",
  fontSize: "0.78125rem",
  color: "var(--inkmid)",
  background: "var(--card)",
  cursor: "pointer",
  minHeight: "2.25rem",
};

function Editor({
  initial,
  suggestedLabel,
  parentOptions,
  onSave,
}: {
  initial: ContactDraft;
  suggestedLabel: string;
  /** Spec 012 §9.3: who this number is for. Everyone, or one parent. */
  parentOptions: { parentId: string; label: string }[];
  onSave: (draft: ContactDraft) => Promise<void>;
}) {
  const [label, setLabel] = useState(initial.label);
  const [name, setName] = useState(initial.name);
  const [phone, setPhone] = useState(initial.phone_display);
  const [note, setNote] = useState(initial.note);
  const [tag, setTag] = useState(initial.parent_id ?? "");
  return (
    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", padding: "0.5rem 0" }} data-testid="contact-editor">
      <input type="text" value={label} placeholder={suggestedLabel} maxLength={60}
        onChange={(event) => setLabel(event.target.value)}
        style={{ ...FIELD, flex: "1 1 10rem" }} data-testid="contact-label-input" />
      <input type="text" value={name} placeholder={CONTACT_NAME_PLACEHOLDER} maxLength={80}
        onChange={(event) => setName(event.target.value)}
        style={{ ...FIELD, flex: "1 1 8rem" }} data-testid="contact-name-input" />
      <input type="tel" value={phone} placeholder={CONTACT_PHONE_PLACEHOLDER} maxLength={30}
        onChange={(event) => setPhone(event.target.value)}
        style={{ ...FIELD, flex: "1 1 8rem" }} data-testid="contact-phone-input" />
      <input type="text" value={note} placeholder={CONTACT_NOTE_PLACEHOLDER} maxLength={200}
        onChange={(event) => setNote(event.target.value)}
        style={{ ...FIELD, flex: "2 1 12rem" }} data-testid="contact-note-input" />
      <select
        value={tag}
        onChange={(event) => setTag(event.target.value)}
        aria-label={CONTACT_TAG_LABEL}
        style={{ ...FIELD, flex: "1 1 8rem" }}
        data-testid="contact-tag"
      >
        <option value="">{CONTACT_TAG_EVERYONE}</option>
        {parentOptions.map((option) => (
          <option key={option.parentId} value={option.parentId}>
            {option.label}
          </option>
        ))}
      </select>
      <button type="button" style={{ ...CHIP, color: "var(--copperdeep)", fontWeight: 600 }}
        onClick={() =>
          void onSave({
            label: label.trim(),
            name: name.trim(),
            phone_display: phone.trim(),
            phone_e164: telHrefNumber(phone),
            note: note.trim(),
            parent_id: tag === "" ? null : tag,
          })
        }
        data-testid="contact-save"
      >
        {CONTACT_SAVE_LABEL}
      </button>
    </div>
  );
}

export function ContactsCard({
  contacts,
  parentOptions,
  parentLabelFor,
  onAdd,
  onUpdate,
  onRemove,
  onMove,
}: {
  /** Already filtered and already in rank order by the screen above. */
  contacts: FamilyContact[];
  parentOptions: { parentId: string; label: string }[];
  parentLabelFor: (contact: FamilyContact) => string;
  onAdd: (draft: ContactDraft) => Promise<void>;
  onUpdate: (id: number, draft: ContactDraft) => Promise<void>;
  onRemove: (id: number) => Promise<void>;
  /** Spec 012 §9.3: the call-first order, moved one row at a time. */
  onMove: (id: number, direction: -1 | 1) => Promise<void>;
}) {
  const [editing, setEditing] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);
  const nextSuggestion =
    CONTACT_SUGGESTED_LABELS[
      Math.min(contacts.length, CONTACT_SUGGESTED_LABELS.length - 1)
    ];

  return (
    <section
      style={{
        background: "var(--card)",
        border: "1px solid var(--hair)",
        borderRadius: "1.125rem",
        padding: "1rem",
        marginBottom: "0.875rem",
      }}
      data-testid="contacts-card"
    >
      {/* No heading here. The page above carries the DECISIONS-200 line
          "If you can't reach them", and printing it twice is precisely the
          duplication spec 012 §9.4 exists to remove — the card must not
          reintroduce it one section down. */}

      {contacts.map((contact) =>
        editing === contact.id ? (
          <Editor
            key={contact.id}
            initial={contact}
            suggestedLabel={nextSuggestion}
            parentOptions={parentOptions}
            onSave={async (draft) => {
              await onUpdate(contact.id, draft);
              setEditing(null);
            }}
          />
        ) : (
          <div
            key={contact.id}
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: "0.625rem",
              flexWrap: "wrap",
              padding: "0.5rem 0",
              borderTop: "1px solid var(--hair)",
            }}
            data-testid="contact-row"
          >
            <span
              style={{ fontSize: "0.71875rem", color: "var(--mute)", fontWeight: 600, letterSpacing: ".03em" }}
              data-testid="contact-label"
            >
              {contact.label}
            </span>
            <span
              style={{ fontSize: "0.71875rem", color: "var(--mute)", letterSpacing: ".03em" }}
              data-testid="contact-tag-label"
            >
              {parentLabelFor(contact)}
            </span>
            <span className="kt-serif" style={{ fontWeight: 500, fontSize: "0.9375rem" }}>
              {contact.name}
            </span>
            {contact.phone_e164 && (
              <a
                href={`tel:${contact.phone_e164}`}
                className="kt-link"
                style={{ fontSize: "0.875rem", fontWeight: 600 }}
                data-testid="contact-phone"
              >
                {contact.phone_display}
              </a>
            )}
            {contact.note && (
              <span style={{ fontSize: "0.8125rem", color: "var(--ink2)" }}>{contact.note}</span>
            )}
            <span style={{ marginLeft: "auto", display: "flex", gap: "0.375rem" }}>
              <button type="button" style={CHIP} onClick={() => void onMove(contact.id, -1)}
                aria-label={CONTACT_MOVE_UP} data-testid="contact-up">
                {CONTACT_MOVE_UP}
              </button>
              <button type="button" style={CHIP} onClick={() => void onMove(contact.id, 1)}
                aria-label={CONTACT_MOVE_DOWN} data-testid="contact-down">
                {CONTACT_MOVE_DOWN}
              </button>
              <button type="button" style={CHIP} onClick={() => setEditing(contact.id)}
                data-testid="contact-edit">
                {CONTACT_EDIT_LABEL}
              </button>
              <button type="button" style={CHIP} onClick={() => void onRemove(contact.id)}
                data-testid="contact-remove">
                {CONTACT_REMOVE_LABEL}
              </button>
            </span>
          </div>
        ),
      )}

      {adding ? (
        <Editor
          initial={{ label: "", name: "", phone_e164: "", phone_display: "", note: "", parent_id: null }}
          suggestedLabel={nextSuggestion}
          parentOptions={parentOptions}
          onSave={async (draft) => {
            await onAdd(draft);
            setAdding(false);
          }}
        />
      ) : (
        <button type="button" style={{ ...CHIP, marginTop: "0.375rem" }}
          onClick={() => setAdding(true)} data-testid="contact-add">
          {CONTACT_ADD_LABEL}
        </button>
      )}
    </section>
  );
}
