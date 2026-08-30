/**
 * Memory (spec 012): the journal, promoted to a place. The consolidated
 * cross-parent feed moved here from the Family screen — upcoming strip,
 * composer, tag picker, entries newest-first under month separators — with
 * the family's contacts sheet above it (placement per the build report:
 * family-wide, at the top, where the printable's block sits on its page).
 * A companion to the daily note, never a care-coordination suite; it asks
 * nothing of the parent, ever.
 */
import { ContactsCard } from "@/components/ContactsCard";
import { NotesPanel, type NoteDraft, type TagOption } from "@/components/NotesPanel";
import { AUTHOR_FALLBACK, MEMORY_EMPTY, MEMORY_TITLE, NOTES_SUB } from "@/lib/copy";
import type { ContactDraft } from "@/lib/data";
import type { FamilyContact, JournalEntry } from "@/lib/types";

export function MemoryScreen({
  parentLabels,
  journal,
  contacts,
  todayDate,
  onAddNote,
  onAddContact,
  onUpdateContact,
  onRemoveContact,
}: {
  /** parentId → display name, for tags and the composer's picker. */
  parentLabels: { parentId: string; label: string }[];
  journal: JournalEntry[];
  contacts: FamilyContact[];
  todayDate: string;
  onAddNote: (draft: NoteDraft) => Promise<void>;
  onAddContact: (draft: ContactDraft) => Promise<void>;
  onUpdateContact: (id: number, draft: ContactDraft) => Promise<void>;
  onRemoveContact: (id: number) => Promise<void>;
}) {
  const labelById = new Map(parentLabels.map((p) => [p.parentId, p.label]));
  const tagOptions: TagOption[] = [
    ...parentLabels.map((p) => ({ parentId: p.parentId, label: p.label })),
    { parentId: null, label: AUTHOR_FALLBACK },
  ];
  return (
    <div className="kt-view" style={{ maxWidth: "43.75rem", margin: "0 auto" }} data-testid="memory-screen">
      <h1
        className="kt-serif"
        style={{ margin: 0, fontWeight: 500, fontSize: "2.375rem", letterSpacing: "-.01em" }}
      >
        {MEMORY_TITLE}
      </h1>
      <div style={{ marginTop: "0.4375rem", fontSize: "0.9375rem", color: "var(--ink2)", lineHeight: 1.5 }}>
        {NOTES_SUB}
      </div>

      <div style={{ marginTop: "1.25rem" }}>
        <ContactsCard
          contacts={contacts}
          onAdd={onAddContact}
          onUpdate={onUpdateContact}
          onRemove={onRemoveContact}
        />
      </div>

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
        monthSeparators
        emptyLine={MEMORY_EMPTY}
      />
    </div>
  );
}
