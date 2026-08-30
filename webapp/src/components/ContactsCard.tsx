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
  CONTACTS_TITLE,
  CONTACT_ADD_LABEL,
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
  onSave,
}: {
  initial: ContactDraft;
  suggestedLabel: string;
  onSave: (draft: ContactDraft) => Promise<void>;
}) {
  const [label, setLabel] = useState(initial.label);
  const [name, setName] = useState(initial.name);
  const [phone, setPhone] = useState(initial.phone_display);
  const [note, setNote] = useState(initial.note);
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
      <button type="button" style={{ ...CHIP, color: "var(--copperdeep)", fontWeight: 600 }}
        onClick={() =>
          void onSave({
            label: label.trim(),
            name: name.trim(),
            phone_display: phone.trim(),
            phone_e164: telHrefNumber(phone),
            note: note.trim(),
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
  onAdd,
  onUpdate,
  onRemove,
}: {
  contacts: FamilyContact[];
  onAdd: (draft: ContactDraft) => Promise<void>;
  onUpdate: (id: number, draft: ContactDraft) => Promise<void>;
  onRemove: (id: number) => Promise<void>;
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
      <h3
        style={{
          fontSize: "0.6875rem",
          letterSpacing: ".14em",
          textTransform: "uppercase",
          color: "var(--mute)",
          fontWeight: 700,
          margin: 0,
          marginBottom: "0.375rem",
        }}
      >
        {CONTACTS_TITLE}
      </h3>

      {contacts.map((contact) =>
        editing === contact.id ? (
          <Editor
            key={contact.id}
            initial={contact}
            suggestedLabel={nextSuggestion}
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
          initial={{ label: "", name: "", phone_e164: "", phone_display: "", note: "" }}
          suggestedLabel={nextSuggestion}
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
