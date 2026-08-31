/**
 * Memory (spec 012): the journal, promoted to a place. The consolidated
 * cross-parent feed moved here from the Family screen — upcoming strip,
 * composer, tag picker, entries newest-first under month separators — with
 * the family's contacts sheet above it (placement per the build report:
 * family-wide, at the top, where the printable's block sits on its page).
 * A companion to the daily note, never a care-coordination suite; it asks
 * nothing of the parent, ever.
 */
import { useState } from "react";
import { FilterChips } from "@/components/FilterChips";
import { NotesPanel, type NoteDraft, type TagOption } from "@/components/NotesPanel";
import {
  AUTHOR_FALLBACK,
  FILTER_ALL_PARENTS,
  FILTER_EMPTY,
  FILTER_PARENT_LABEL,
  FILTER_TIME_LABEL,
  MEMORY_EMPTY,
  MEMORY_TITLE,
  NOTES_SUB,
  TIMEFRAME_3_MONTHS,
  TIMEFRAME_6_MONTHS,
  TIMEFRAME_ALL,
  TIMEFRAME_THIS_MONTH,
} from "@/lib/copy";
import {
  DEFAULT_PARENT_FILTER,
  DEFAULT_TIMEFRAME,
  filterEntries,
  type TimeframeId,
} from "@/lib/journal";
import type { JournalEntry } from "@/lib/types";

/** The four timeframes, chip id to the words DECISIONS 211 ruled the view
 *  opens on ("3 months"). Ids are the journal lib's, labels are copy. */
const TIMEFRAME_OPTIONS = [
  { id: "month", label: TIMEFRAME_THIS_MONTH },
  { id: "3m", label: TIMEFRAME_3_MONTHS },
  { id: "6m", label: TIMEFRAME_6_MONTHS },
  { id: "all", label: TIMEFRAME_ALL },
];

export function MemoryScreen({
  parentLabels,
  journal,
  todayDate,
  onAddNote,
}: {
  /** parentId → display name, for tags, filters and the composer's picker. */
  parentLabels: { parentId: string; label: string }[];
  journal: JournalEntry[];
  todayDate: string;
  onAddNote: (draft: NoteDraft) => Promise<void>;
}) {
  // DECISIONS 211: All parents over three months, All-time one tap away.
  const [parentFilter, setParentFilter] = useState<string | null>(DEFAULT_PARENT_FILTER);
  const [timeframe, setTimeframe] = useState<TimeframeId>(DEFAULT_TIMEFRAME);
  const labelById = new Map(parentLabels.map((p) => [p.parentId, p.label]));
  const shown = filterEntries(journal, todayDate, parentFilter, timeframe);
  // Two different silences, and they must not read the same. Nothing written
  // yet is the ruled MEMORY_EMPTY line; nothing in THIS window is a filter
  // that went too narrow, and saying "the first ones arrive on their own" to
  // a family with a year of notes would be false.
  const emptyLine = journal.length === 0 ? MEMORY_EMPTY : FILTER_EMPTY;
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

      {/* Spec 012 §9.3: the contacts sheet left this page for its own tab. */}

      <NotesPanel
        entries={shown}
        todayDate={todayDate}
        onAdd={onAddNote}
        tagOptions={tagOptions}
        tagLabelFor={(entry: JournalEntry) =>
          entry.parent_id === null
            ? AUTHOR_FALLBACK
            : (labelById.get(entry.parent_id) ?? AUTHOR_FALLBACK)
        }
        monthSeparators
        emptyLine={emptyLine}
        // Spec 012 §9.4: the page above already carries this sentence, so the
        // card no longer prints a second copy of it.
        showSubtitle={false}
        scrollList
        filters={
          <div style={{ display: "grid", gap: "0.375rem", marginBottom: "0.75rem" }}>
            {parentLabels.length > 1 && (
              <FilterChips
                groupLabel={FILTER_PARENT_LABEL}
                options={[
                  { id: "", label: FILTER_ALL_PARENTS },
                  ...parentLabels.map((p) => ({ id: p.parentId, label: p.label })),
                ]}
                selected={parentFilter ?? ""}
                onSelect={(id) => setParentFilter(id === "" ? null : id)}
                testId="notes-parent-filter"
              />
            )}
            <FilterChips
              groupLabel={FILTER_TIME_LABEL}
              options={TIMEFRAME_OPTIONS}
              selected={timeframe}
              onSelect={(id) => setTimeframe(id as TimeframeId)}
              testId="notes-time-filter"
            />
          </div>
        }
      />
    </div>
  );
}
