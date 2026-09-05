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
  REPLY_CANCEL,
  REPLY_LINK,
  REPLY_PLACEHOLDER,
  REPLY_SUBMIT,
  SIGNED_AS_LABEL,
  UPCOMING_LABEL,
  UPCOMING_ON,
} from "@/lib/copy";
import {
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

  // Spec 016: the strip and the feed are NOTES; replies hang under theirs.
  const { notes, repliesByNote } = splitThreads(entries);
  const upcoming = upcomingEntries(notes, todayDate);
  const past = pastEntries(notes, todayDate);

  async function submitReply(parentEntryId: number) {
    const trimmed = replyBody.trim();
    if (!trimmed || !onReply) return;
    rememberAuthor(author);
    await onReply({ parentEntryId, body: trimmed, authorLabel: author.trim() });
    setReplyBody("");
    setReplyingTo(null);
  }

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
            {monthDay(localDay(entry.created_utc, tz))} ·{" "}
            {entry.author_label || AUTHOR_FALLBACK}
            {entry.event_date ? ` · ${EVENT_FOR.replace("{date}", monthDay(entry.event_date))}` : ""}
          </div>
            <Body body={entry.body} />
            {(repliesByNote.get(entry.id) ?? []).map((reply) => (
              <div
                key={reply.id}
                data-testid="note-reply"
                style={{
                  marginTop: "0.5rem",
                  marginLeft: "1rem",
                  paddingLeft: "0.75rem",
                  borderLeft: "2px solid var(--hair)",
                }}
              >
                <div
                  style={{ fontSize: "0.71875rem", color: "var(--mute)", letterSpacing: ".03em", fontWeight: 600 }}
                  data-testid="reply-meta"
                >
                  {monthDay(localDay(reply.created_utc, tz))} · {reply.author_label || AUTHOR_FALLBACK}
                </div>
                <Body body={reply.body} />
              </div>
            ))}
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
                >
                  {REPLY_SUBMIT}
                </button>
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
