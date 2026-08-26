/**
 * Family notes (spec 009 §4): the panel both screens share. The parent page
 * passes its own scoped entries and a fixed parent tag; the Family screen
 * passes the consolidated list, shows each entry's tag, and lets the composer
 * pick one (Mom / Dad / Family).
 *
 * Bodies are family-authored text and render INERT: every segment is a React
 * text node or an anchor built by linkify() — never markup from the body.
 * Nothing here asks anything of a parent, and nothing turns into a chore.
 */

import { useState } from "react";
import {
  ADDED_BY,
  AUTHOR_FALLBACK,
  DATE_CHIP_LABEL,
  EVENT_FOR,
  NOTES_SUB,
  NOTES_TITLE,
  NOTE_PLACEHOLDER,
  NOTE_SUBMIT_LABEL,
  NOTE_TAG_LABEL,
  SIGNED_AS_LABEL,
  UPCOMING_LABEL,
  UPCOMING_ON,
} from "@/lib/copy";
import {
  firstLine,
  linkify,
  monthDay,
  pastEntries,
  upcomingEntries,
  weekdayMonthDay,
} from "@/lib/journal";
import type { JournalEntry } from "@/lib/types";

const SIGNED_AS_KEY = "kettle-signed-as";

function storedAuthor(): string {
  try {
    return localStorage.getItem(SIGNED_AS_KEY) ?? "";
  } catch {
    return "";
  }
}

function rememberAuthor(value: string): void {
  try {
    localStorage.setItem(SIGNED_AS_KEY, value);
  } catch {
    // A private window forgets; the note still posts.
  }
}

export interface NoteDraft {
  parentId: string | null;
  body: string;
  authorLabel: string;
  eventDate: string | null;
}

export interface TagOption {
  parentId: string | null;
  label: string;
}

function Body({ body }: { body: string }) {
  return (
    <p style={{ fontSize: "0.875rem", lineHeight: 1.5, marginTop: "0.1875rem", margin: 0, overflowWrap: "anywhere" }}>
      {linkify(body).map((segment, index) =>
        segment.kind === "text" ? (
          <span key={index}>{segment.text}</span>
        ) : (
          <a
            key={index}
            href={segment.href}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: "var(--copperdeep)",
              textDecoration: "underline",
              textUnderlineOffset: "0.1875rem",
            }}
          >
            {segment.label}
          </a>
        ),
      )}
    </p>
  );
}

export function NotesPanel({
  entries,
  todayDate,
  onAdd,
  /** Fixed tag (the parent page) or a picker over these options (Family). */
  tagOptions,
  fixedParentId,
  /** Family view prefixes each entry with its tag. */
  tagLabelFor,
}: {
  entries: JournalEntry[];
  todayDate: string;
  onAdd: (draft: NoteDraft) => Promise<void>;
  tagOptions?: TagOption[];
  fixedParentId?: string | null;
  tagLabelFor?: (entry: JournalEntry) => string;
}) {
  const [body, setBody] = useState("");
  const [author, setAuthor] = useState(storedAuthor);
  const [eventDate, setEventDate] = useState<string>("");
  const [showDate, setShowDate] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [tag, setTag] = useState<string>("");

  const upcoming = upcomingEntries(entries, todayDate);
  const past = pastEntries(entries, todayDate);

  async function submit() {
    const trimmed = body.trim();
    if (!trimmed) return;
    rememberAuthor(author);
    await onAdd({
      parentId: fixedParentId !== undefined ? fixedParentId : tag === "" ? null : tag,
      body: trimmed,
      authorLabel: author.trim(),
      eventDate: eventDate || null,
    });
    setBody("");
    setEventDate("");
    setShowDate(false);
    setExpanded(false);
  }

  return (
    <section
      style={{
        background: "var(--card)",
        border: "1px solid var(--hair)",
        borderRadius: "1.125rem",
        padding: "1rem",
        marginBottom: "0.875rem",
      }}
      data-testid="notes-panel"
    >
      <h3
        style={{
          fontSize: "0.6875rem",
          letterSpacing: ".14em",
          textTransform: "uppercase",
          color: "var(--mute)",
          fontWeight: 700,
          margin: 0,
          marginBottom: "0.25rem",
        }}
      >
        {NOTES_TITLE}
      </h3>
      <div style={{ fontSize: "0.78125rem", color: "var(--mute)", marginBottom: "0.625rem" }}>
        {NOTES_SUB}
      </div>

      {upcoming.map((entry) => (
        <div
          key={`up-${entry.id}`}
          style={{
            background: "var(--coppertint)",
            borderRadius: "0.75rem",
            padding: "0.625rem 0.75rem",
            fontSize: "0.8125rem",
            marginBottom: "0.75rem",
          }}
          data-testid="upcoming-entry"
        >
          <b style={{ color: "var(--copperdeep)" }}>{UPCOMING_LABEL}</b>
          {" · "}
          {UPCOMING_ON.replace("{first}", firstLine(entry.body)).replace(
            "{date}",
            weekdayMonthDay(entry.event_date ?? todayDate),
          )}
          {" · "}
          {ADDED_BY.replace("{author}", entry.author_label || AUTHOR_FALLBACK)}
        </div>
      ))}

      {past.map((entry, index) => (
        <div
          key={entry.id}
          style={{
            padding: "0.625rem 0",
            borderTop: index === 0 ? "none" : "1px solid var(--hair)",
          }}
          data-testid="note-entry"
        >
          <div
            style={{
              fontSize: "0.71875rem",
              color: "var(--mute)",
              letterSpacing: ".03em",
              fontWeight: 600,
            }}
            data-testid="note-meta"
          >
            {tagLabelFor ? `${tagLabelFor(entry)} · ` : ""}
            {monthDay(entry.created_utc)} · {entry.author_label || AUTHOR_FALLBACK}
            {entry.event_date ? ` · ${EVENT_FOR.replace("{date}", monthDay(entry.event_date))}` : ""}
          </div>
          <Body body={entry.body} />
        </div>
      ))}

      <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem", flexWrap: "wrap" }}>
        <input
          type="text"
          value={body}
          placeholder={NOTE_PLACEHOLDER}
          onFocus={() => setExpanded(true)}
          onChange={(event) => setBody(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") void submit();
          }}
          maxLength={2000}
          style={{
            flex: "1 1 12rem",
            background: "var(--paper)",
            border: "1px solid var(--hair)",
            borderRadius: "999px",
            padding: "0.5625rem 0.875rem",
            fontSize: "0.84375rem",
            color: "var(--ink)",
            minHeight: "2.75rem",
            boxSizing: "border-box",
          }}
          data-testid="note-input"
        />
        {showDate ? (
          <input
            type="date"
            value={eventDate}
            onChange={(event) => setEventDate(event.target.value)}
            aria-label={DATE_CHIP_LABEL}
            style={{
              border: "1px solid var(--hair)",
              borderRadius: "999px",
              padding: "0.5625rem 0.75rem",
              fontSize: "0.8125rem",
              color: "var(--inkmid)",
              background: "var(--card)",
            }}
            data-testid="note-date"
          />
        ) : (
          <button
            type="button"
            onClick={() => setShowDate(true)}
            style={{
              border: "1px solid var(--hair)",
              borderRadius: "999px",
              padding: "0.5625rem 0.75rem",
              fontSize: "0.8125rem",
              color: "var(--inkmid)",
              background: "var(--card)",
              whiteSpace: "nowrap",
              cursor: "pointer",
              minHeight: "2.75rem",
            }}
            data-testid="note-date-chip"
          >
            {DATE_CHIP_LABEL}
          </button>
        )}
        <button
          type="button"
          onClick={() => void submit()}
          style={{
            border: "1px solid var(--copperbd)",
            borderRadius: "999px",
            padding: "0.5625rem 1rem",
            fontSize: "0.8125rem",
            fontWeight: 600,
            color: "var(--copperdeep)",
            background: "var(--coppertint)",
            cursor: "pointer",
            minHeight: "2.75rem",
          }}
          data-testid="note-submit"
        >
          {NOTE_SUBMIT_LABEL}
        </button>
      </div>
      {expanded && (
        <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
          {tagOptions && fixedParentId === undefined && (
            <select
              value={tag}
              onChange={(event) => setTag(event.target.value)}
              aria-label={NOTE_TAG_LABEL}
              style={{
                border: "1px solid var(--hair)",
                borderRadius: "999px",
                padding: "0.4375rem 0.75rem",
                fontSize: "0.8125rem",
                color: "var(--inkmid)",
                background: "var(--card)",
              }}
              data-testid="note-tag"
            >
              {tagOptions.map((option) => (
                <option key={option.parentId ?? "family"} value={option.parentId ?? ""}>
                  {option.label}
                </option>
              ))}
            </select>
          )}
          <label
            style={{ display: "inline-flex", alignItems: "center", gap: "0.375rem", fontSize: "0.8125rem", color: "var(--mute)" }}
          >
            {SIGNED_AS_LABEL}
            <input
              type="text"
              value={author}
              onChange={(event) => setAuthor(event.target.value)}
              style={{
                border: "1px solid var(--hair)",
                borderRadius: "999px",
                padding: "0.4375rem 0.75rem",
                fontSize: "0.8125rem",
                color: "var(--ink)",
                background: "var(--paper)",
                width: "8rem",
              }}
              data-testid="note-author"
            />
          </label>
        </div>
      )}
    </section>
  );
}
