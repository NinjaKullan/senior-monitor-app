/**
 * Who to call (spec 012 §9.3): the contacts sheet, promoted off Memory into
 * its own tab.
 *
 * The founder's framing, recorded in the spec's own words: this is an
 * escalation ladder camouflaged as a contact list. So the order of the rows
 * is the point — call-first, then, then — and the family sets it by hand.
 * Parents living apart carry different numbers, which is why a contact
 * belongs to one parent or to the whole household, and why the list filters.
 *
 * The TAB is called "Who to call" (DECISIONS 211, verbatim). The PAGE keeps
 * the DECISIONS-200 heading "If you can't reach them", which was not
 * reopened. Two strings, two jobs: the rail needs a short name, the page
 * needs the sentence that says what the moment is.
 */
import { useState } from "react";
import { ContactsCard } from "@/components/ContactsCard";
import { FilterChips } from "@/components/FilterChips";
import {
  CONTACTS_TITLE,
  CONTACT_TAG_EVERYONE,
  FILTER_ALL_PARENTS,
  FILTER_PARENT_LABEL,
} from "@/lib/copy";
import type { ContactDraft } from "@/lib/data";
import type { FamilyContact } from "@/lib/types";

export function WhoToCallScreen({
  parentLabels,
  contacts,
  onAddContact,
  onUpdateContact,
  onRemoveContact,
  onMoveContact,
}: {
  parentLabels: { parentId: string; label: string }[];
  contacts: FamilyContact[];
  onAddContact: (draft: ContactDraft) => Promise<void>;
  onUpdateContact: (id: number, draft: ContactDraft) => Promise<void>;
  onRemoveContact: (id: number) => Promise<void>;
  onMoveContact: (id: number, direction: -1 | 1) => Promise<void>;
}) {
  const [parentFilter, setParentFilter] = useState<string | null>(null);
  const labelById = new Map(parentLabels.map((p) => [p.parentId, p.label]));

  // A household contact shows under every parent's filter as well as under
  // All: the neighbour with a key is who you call about either of them, and
  // hiding that row while filtered to one parent would be the list lying
  // about who is reachable.
  const shown = contacts
    .filter(
      (contact) =>
        parentFilter === null ||
        contact.parent_id === null ||
        contact.parent_id === parentFilter,
    )
    .slice()
    .sort((a, b) => a.position - b.position || a.id - b.id);

  return (
    <div
      className="kt-view"
      style={{ maxWidth: "43.75rem", margin: "0 auto" }}
      data-testid="who-to-call-screen"
    >
      <h1
        className="kt-serif"
        style={{ margin: 0, fontWeight: 500, fontSize: "2.375rem", letterSpacing: "-.01em" }}
      >
        {CONTACTS_TITLE}
      </h1>

      {parentLabels.length > 1 && (
        <div style={{ marginTop: "0.875rem" }}>
          <FilterChips
            groupLabel={FILTER_PARENT_LABEL}
            options={[
              { id: "", label: FILTER_ALL_PARENTS },
              ...parentLabels.map((p) => ({ id: p.parentId, label: p.label })),
            ]}
            selected={parentFilter ?? ""}
            onSelect={(id) => setParentFilter(id === "" ? null : id)}
            testId="contact-parent-filter"
          />
        </div>
      )}

      <div style={{ marginTop: "1rem" }}>
        <ContactsCard
          contacts={shown}
          parentOptions={parentLabels}
          parentLabelFor={(contact) =>
            contact.parent_id === null
              ? CONTACT_TAG_EVERYONE
              : (labelById.get(contact.parent_id) ?? CONTACT_TAG_EVERYONE)
          }
          onAdd={onAddContact}
          onUpdate={onUpdateContact}
          onRemove={onRemoveContact}
          onMove={onMoveContact}
        />
      </div>
    </div>
  );
}
