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

import { useRef, useState } from "react";
import {
  ADDED_BY,
  AUTHOR_FALLBACK,
  COMPOSER_FAILED,
  DATE_CHIP_LABEL,
  DELETE_CANCEL,
  DELETE_CONFIRM_YES,
  DELETE_LINK,
  DELETE_NOTE_CONFIRM,
  DELETE_REPLY_CONFIRM,
  EDITED_MARK,
  EDIT_CANCEL,
  EDIT_LINK,
  EVENT_FOR,
  NOTES_SUB,
  NOTES_TITLE,
  NOTE_PLACEHOLDER,
  NOTE_SUBMIT_LABEL,
  NOTE_TAG_LABEL,
  REPLY_CANCEL,
  REPLY_LINK,
  REPLY_PLACEHOLDER,
  REPLY_SUBMIT,
  SAVE,
  SIGNED_AS_LABEL,
  UPCOMING_LABEL,
  UPCOMING_ON,
} from "@/lib/copy";
import {
  canDelete,
  canEdit,
  canReply,
  firstLine,
  linkify,
  monthDay,
  localDay,
  monthYear,
  pastEntries,
  splitThreads,
  upcomingEntries,
  weekdayMonthDay,
  type Viewer,
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

/** Spec 016: a reply is a body and an author, on one note. The tag and the
 *  date are the note's; the server writes the tag, there is no date. */
export interface ReplyDraft {
  parentEntryId: number;
  body: string;
  authorLabel: string;
}

export interface TagOption {
  parentId: string | null;
  label: string;
}

const PILL_INPUT: React.CSSProperties = {
  flex: "1 1 10rem",
  background: "var(--paper)",
  border: "1px solid var(--hair)",
  borderRadius: "999px",
  padding: "0.5rem 0.875rem",
  fontSize: "0.8125rem",
  color: "var(--ink)",
  minHeight: "2.75rem",
  boxSizing: "border-box",
};
const PILL_BUTTON: React.CSSProperties = {
  border: "1px solid var(--hair)",
  borderRadius: "999px",
  padding: "0.5rem 0.875rem",
  fontSize: "0.8125rem",
  color: "var(--inkmid)",
  background: "var(--card)",
  cursor: "pointer",
  minHeight: "2.75rem",
};
const PILL_PRIMARY: React.CSSProperties = {
  ...PILL_BUTTON,
  border: "1px solid var(--copperbd)",
  fontWeight: 600,
  color: "var(--copperdeep)",
  background: "var(--coppertint)",
};
const LINK_BUTTON: React.CSSProperties = {
  background: "none",
  border: "none",
  padding: 0,
  fontSize: "0.71875rem",
  fontWeight: 600,
  letterSpacing: ".03em",
  color: "var(--copperdeep)",
  cursor: "pointer",
};

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
  tz,
  onAdd,
  onReply,
  viewer,
  onEdit,
  onDelete,
  /** Fixed tag (the parent page) or a picker over these options (Family). */
  tagOptions,
  fixedParentId,
  /** Family view prefixes each entry with its tag. */
  tagLabelFor,
  monthSeparators,
  emptyLine,
  showSubtitle = true,
  filters,
  scrollList = false,
}: {
  entries: JournalEntry[];
  todayDate: string;
  /** The family's timezone: a note is dated by the day it was written where
   *  it was written, not by UTC's day (DECISIONS 251). */
  tz: string;
  onAdd: (draft: NoteDraft) => Promise<void>;
  /** Spec 016 §4: the Reply link renders only when this is given. */
  onReply?: (draft: ReplyDraft) => Promise<void>;
  /** Spec 018: who is looking decides which Edit and Delete links render;
   *  without a viewer, none do. */
  viewer?: Viewer;
  onEdit?: (entryId: number, body: string) => Promise<void>;
  onDelete?: (entryId: number) => Promise<void>;
  tagOptions?: TagOption[];
  fixedParentId?: string | null;
  tagLabelFor?: (entry: JournalEntry) => string;
  /** Spec 012 §2, Memory only: month separators in the past feed, and the
   *  ruled empty-state line when there is nothing yet. ParentDetail keeps
   *  its scoped panel exactly as it was. */
  monthSeparators?: boolean;
  emptyLine?: string;
  /** Spec 012 §9.4: the Memory page already carries this sentence as its
   *  subtitle, so the card drops its copy rather than printing it twice. The
   *  parent page, which has no such subtitle, keeps it. */
  showSubtitle?: boolean;
  /** Spec 012 §9.1: the filter chips, rendered above the scroll region so
   *  they stay put while the list moves under them. */
  filters?: React.ReactNode;
  /** Spec 012 §9.2: the list grows without bound, so on Memory it scrolls
   *  inside the card. Month dividers ride INSIDE the scroll region and the
   *  composer stays outside it, pinned and always reachable. */
  scrollList?: boolean;
}) {
  const [body, setBody] = useState("");
  const [author, setAuthor] = useState(storedAuthor);
  const [eventDate, setEventDate] = useState<string>("");
  const [showDate, setShowDate] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [tag, setTag] = useState<string>("");
  /** The note whose reply composer is open, and what is typed in it. */
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const [replyBody, setReplyBody] = useState("");
  /**
   * Spec 018 §2, the optimistic composer. A sent note or reply appears in
   * the list at once as a PENDING row (a negative id nothing on the server
   * can collide with); the composer clears and LOCKS until the server
   * answers, so Enter and Add are one action that cannot fire twice; on
   * failure the row is removed and the text returns with COMPOSER_FAILED.
   * A ref, not only state, guards the lock: two events in one tick see the
   * same state and would both pass a state check.
   */
  const [pending, setPending] = useState<JournalEntry[]>([]);
  const [sending, setSending] = useState(false);
  const sendingRef = useRef(false);
  const [failed, setFailed] = useState<string | null>(null);
  const [replyFailed, setReplyFailed] = useState<string | null>(null);
  /** Spec 018 §4: the entry being edited inline, and the confirm line's target. */
  const [editing, setEditing] = useState<{ id: number; body: string } | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);

  // Spec 016: the strip and the feed are NOTES; replies hang under theirs.
  // Pending rows ride in front, where a just-written note belongs.
  const { notes, repliesByNote } = splitThreads([...pending, ...entries]);
  const upcoming = upcomingEntries(notes, todayDate);
  const past = pastEntries(notes, todayDate);

  function optimistic(fields: Partial<JournalEntry>): JournalEntry {
    return {
      id: -Date.now() - Math.floor(Math.random() * 1000),
      family_id: entries[0]?.family_id ?? "",
      parent_id: null,
      author_label: author.trim(),
      body: "",
      event_date: null,
      created_utc: new Date().toISOString(),
      kind: "note",
      parent_entry_id: null,
      author_member_id: viewer?.memberId ?? null,
      edited_utc: null,
      ...fields,
    };
  }

  async function submitReply(parentEntryId: number) {
    const trimmed = replyBody.trim();
    if (!trimmed || !onReply || sendingRef.current) return;
    sendingRef.current = true;
    setSending(true);
    setReplyFailed(null);
    rememberAuthor(author);
    const row = optimistic({ body: trimmed, parent_entry_id: parentEntryId });
    setPending((rows) => [row, ...rows]);
    setReplyBody("");
    setReplyingTo(null);
    try {
      await onReply({ parentEntryId, body: trimmed, authorLabel: author.trim() });
    } catch {
      setReplyBody(trimmed);
      setReplyingTo(parentEntryId);
      setReplyFailed(COMPOSER_FAILED);
    } finally {
      setPending((rows) => rows.filter((r) => r.id !== row.id));
      sendingRef.current = false;
      setSending(false);
    }
  }

  async function submit() {
    const trimmed = body.trim();
    if (!trimmed || sendingRef.current) return;
    sendingRef.current = true;
    setSending(true);
    setFailed(null);
    rememberAuthor(author);
    const parentId = fixedParentId !== undefined ? fixedParentId : tag === "" ? null : tag;
    const draft: NoteDraft = {
      parentId,
      body: trimmed,
      authorLabel: author.trim(),
      eventDate: eventDate || null,
    };
    const row = optimistic({ body: trimmed, parent_id: parentId, event_date: draft.eventDate });
    setPending((rows) => [row, ...rows]);
    setBody("");
    setEventDate("");
    setShowDate(false);
    setExpanded(false);
    try {
      await onAdd(draft);
    } catch {
      setBody(trimmed);
      setEventDate(draft.eventDate ?? "");
      setFailed(COMPOSER_FAILED);
    } finally {
      setPending((rows) => rows.filter((r) => r.id !== row.id));
      sendingRef.current = false;
      setSending(false);
    }
  }

  async function saveEdit() {
    if (!editing || !onEdit) return;
    const trimmed = editing.body.trim();
    if (!trimmed) return;
    await onEdit(editing.id, trimmed);
    setEditing(null);
  }

  async function confirmDelete(entryId: number) {
    if (!onDelete) return;
    await onDelete(entryId);
    setDeleting(null);
  }

  /** "Aug 22 · edited · Priya": the date, the mark when edited, the author. */
  function metaFor(entry: JournalEntry): string {
    const date = monthDay(localDay(entry.created_utc, tz));
    const mark = entry.edited_utc ? ` · ${EDITED_MARK}` : "";
    return `${date}${mark} · ${entry.author_label || AUTHOR_FALLBACK}`;
  }

  /** The Edit and Delete links, the inline editor and the confirm line, for
   *  a note or a reply (spec 018 §4). Nothing renders on a pending row. */
  function renderControls(entry: JournalEntry, isReply: boolean) {
    if (!viewer || entry.id < 0) return null;
    const editable = Boolean(onEdit) && canEdit(entry, viewer);
    const deletable = Boolean(onDelete) && canDelete(entry, viewer);
    if (!editable && !deletable) return null;
    if (editing?.id === entry.id) {
      return (
        <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.375rem", flexWrap: "wrap" }} data-testid="edit-composer">
          <input
            type="text"
            value={editing.body}
            autoFocus
            maxLength={2000}
            onChange={(event) => setEditing({ id: entry.id, body: event.target.value })}
            onKeyDown={(event) => {
              if (event.key === "Enter") void saveEdit();
              if (event.key === "Escape") setEditing(null);
            }}
            style={PILL_INPUT}
            data-testid="edit-input"
          />
          <button type="button" onClick={() => void saveEdit()} style={PILL_PRIMARY} data-testid="edit-save">
            {SAVE}
          </button>
          <button type="button" onClick={() => setEditing(null)} style={PILL_BUTTON} data-testid="edit-cancel">
            {EDIT_CANCEL}
          </button>
        </div>
      );
    }
    if (deleting === entry.id) {
      return (
        <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.375rem", alignItems: "center", flexWrap: "wrap", fontSize: "0.8125rem" }} data-testid="delete-confirm">
          {isReply ? DELETE_REPLY_CONFIRM : DELETE_NOTE_CONFIRM}
          <button type="button" onClick={() => void confirmDelete(entry.id)} style={PILL_BUTTON} data-testid="delete-yes">
            {DELETE_CONFIRM_YES}
          </button>
          <button type="button" onClick={() => setDeleting(null)} style={PILL_BUTTON} data-testid="delete-cancel">
            {DELETE_CANCEL}
          </button>
        </div>
      );
    }
    return (
      <span style={{ display: "inline-flex", gap: "0.75rem", marginLeft: "0.75rem" }}>
        {editable && (
          <button type="button" style={LINK_BUTTON} data-testid="edit-link" onClick={() => setEditing({ id: entry.id, body: entry.body })}>
            {EDIT_LINK}
          </button>
        )}
        {deletable && (
          <button type="button" style={LINK_BUTTON} data-testid="delete-link" onClick={() => setDeleting(entry.id)}>
            {DELETE_LINK}
          </button>
        )}
      </span>
    );
  }

  /** A note's replies, indented beneath it (spec 016 §4; DECISIONS 277: in
   *  the upcoming strip as well as the list). */
  function renderReplies(noteId: number) {
    return (repliesByNote.get(noteId) ?? []).map((reply) => (
      <div
        key={reply.id}
        data-testid="note-reply"
        data-pending={reply.id < 0 ? "true" : undefined}
        style={{ marginTop: "0.5rem", marginLeft: "1rem", paddingLeft: "0.75rem", borderLeft: "2px solid var(--hair)" }}
      >
        <div style={{ fontSize: "0.71875rem", color: "var(--mute)", letterSpacing: ".03em", fontWeight: 600 }} data-testid="reply-meta">
          {metaFor(reply)}
          {renderControls(reply, true)}
        </div>
        {editing?.id === reply.id ? null : <Body body={reply.body} />}
      </div>
    ));
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
      {showSubtitle && (
        <div style={{ fontSize: "0.78125rem", color: "var(--mute)", marginBottom: "0.625rem" }}>
          {NOTES_SUB}
        </div>
      )}

      {filters}

      {/* Spec 012 §9.2. The scroll region holds the upcoming strip, the empty
          line and the whole past feed WITH its month dividers; the composer
          below is deliberately outside it, so it stays pinned and reachable
          no matter how far the family has scrolled back. maxHeight is in rem
          so it tracks the reader's own text size, and overscroll-behavior
          keeps a flick at the end of the list from scrolling the page. */}
      <div
        style={
          scrollList
            ? { maxHeight: "32rem", overflowY: "auto", overscrollBehavior: "contain" }
            : undefined
        }
        data-testid={scrollList ? "notes-scroll" : undefined}
      >
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
          {renderReplies(entry.id)}
        </div>
      ))}

      {emptyLine && upcoming.length === 0 && past.length === 0 && (
        <div
          style={{ fontSize: "0.84375rem", color: "var(--ink2)", lineHeight: 1.5, padding: "0.375rem 0 0.5rem" }}
          data-testid="memory-empty"
        >
          {emptyLine}
        </div>
      )}

      {past.map((entry, index) => (
        <div key={entry.id}>
          {monthSeparators &&
            (index === 0 ||
              monthYear(localDay(past[index - 1].created_utc, tz)) !==
                monthYear(localDay(entry.created_utc, tz))) && (
              <div
                style={{
                  marginTop: index === 0 ? "0.25rem" : "0.875rem",
                  fontSize: "0.6875rem",
                  letterSpacing: ".14em",
                  textTransform: "uppercase",
                  color: "var(--mute)",
                  fontWeight: 700,
                }}
                data-testid="month-separator"
              >
                {monthYear(localDay(entry.created_utc, tz))}
              </div>
            )}
          <div
            style={{
              padding: "0.625rem 0",
              borderTop: index === 0 || monthSeparators ? "none" : "1px solid var(--hair)",
            }}
            data-testid="note-entry"
            data-pending={entry.id < 0 ? "true" : undefined}
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
            {metaFor(entry)}
            {entry.event_date ? ` · ${EVENT_FOR.replace("{date}", monthDay(entry.event_date))}` : ""}
            {renderControls(entry, false)}
          </div>
            {editing?.id === entry.id ? null : <Body body={entry.body} />}
            {renderReplies(entry.id)}
            {onReply && canReply(entry) && replyingTo !== entry.id && (
              <button
                type="button"
                className="kt-link"
                onClick={() => {
                  setReplyingTo(entry.id);
                  setReplyBody("");
                }}
                style={{
                  background: "none",
                  border: "none",
                  padding: "0.5rem 0 0",
                  fontSize: "0.78125rem",
                  fontWeight: 600,
                  color: "var(--copperdeep)",
                  cursor: "pointer",
                  minHeight: "2.75rem",
                }}
                data-testid="reply-link"
              >
                {REPLY_LINK}
              </button>
            )}
            {onReply && replyingTo === entry.id && (
              <div
                style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", marginLeft: "1rem", flexWrap: "wrap" }}
                data-testid="reply-composer"
              >
                <input
                  type="text"
                  value={replyBody}
                  placeholder={REPLY_PLACEHOLDER}
                  autoFocus
                  onChange={(event) => setReplyBody(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") void submitReply(entry.id);
                    if (event.key === "Escape") setReplyingTo(null);
                  }}
                  maxLength={2000}
                  style={{
                    flex: "1 1 10rem",
                    background: "var(--paper)",
                    border: "1px solid var(--hair)",
                    borderRadius: "999px",
                    padding: "0.5rem 0.875rem",
                    fontSize: "0.8125rem",
                    color: "var(--ink)",
                    minHeight: "2.75rem",
                    boxSizing: "border-box",
                  }}
                  data-testid="reply-input"
                  disabled={sending}
                />
                <button
                  type="button"
                  onClick={() => void submitReply(entry.id)}
                  style={{
                    border: "1px solid var(--copperbd)",
                    borderRadius: "999px",
                    padding: "0.5rem 0.875rem",
                    fontSize: "0.8125rem",
                    fontWeight: 600,
                    color: "var(--copperdeep)",
                    background: "var(--coppertint)",
                    cursor: "pointer",
                    minHeight: "2.75rem",
                  }}
                  data-testid="reply-submit"
                  disabled={sending}
                >
                  {REPLY_SUBMIT}
                </button>
                {replyFailed && (
                  <span style={{ flexBasis: "100%", fontSize: "0.78125rem", color: "var(--ink2)" }} data-testid="reply-failed">
                    {replyFailed}
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => setReplyingTo(null)}
                  style={{
                    border: "1px solid var(--hair)",
                    borderRadius: "999px",
                    padding: "0.5rem 0.875rem",
                    fontSize: "0.8125rem",
                    color: "var(--inkmid)",
                    background: "var(--card)",
                    cursor: "pointer",
                    minHeight: "2.75rem",
                  }}
                  data-testid="reply-cancel"
                >
                  {REPLY_CANCEL}
                </button>
              </div>
            )}
          </div>
        </div>
      ))}

      </div>

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
          disabled={sending}
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
          disabled={sending}
        >
          {NOTE_SUBMIT_LABEL}
        </button>
      </div>
      {failed && (
        <div style={{ marginTop: "0.375rem", fontSize: "0.78125rem", color: "var(--ink2)" }} data-testid="composer-failed">
          {failed}
        </div>
      )}
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
