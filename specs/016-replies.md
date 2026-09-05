# Spec 016 — Replies on a note

Status: RATIFIED by Hema, 2026-09-04 (DECISIONS 274); strings verbatim. Founder ask, same day
(Asana 1218017356495916 comment). Builds on spec 012 (journal), 251
(dates in family time), 015 (any member writes).

## 1. What this is

A family member replies to a note, and the reply stays under the
note. "Dr. Reed, Thursday 2pm" and the sibling who took her writing
"Took her, all fine, next visit Oct 2" become one thing on the Memory
tab, not two notes a month apart. Same laws as every note: plain
words, straight characters, no verdicts, what-never-how.

## 2. Rules (founder, Sep 4)

- One level only. A note can have replies; a reply cannot.
- Any member replies (015: full write for everyone).
- A reply has an author label and a written-at instant like a note;
  it has no event date and no parent tag of its own (it inherits
  both from the note it belongs to).
- Kettle-authored lines (city_change, started, first_reply,
  clean_month) do not take replies. They are the house speaking, not
  a conversation.

## 3. Data

Migration numbered at build time (268).

- `journal_entries.parent_entry_id bigint null references
  journal_entries(id) on delete cascade`.
- Check: a row with parent_entry_id set has kind 'note', event_date
  null, and its parent row has parent_entry_id null and kind 'note'
  (enforced in the insert function or a trigger; CC's call, tested
  either way).
- RLS unchanged: a reply is a journal row in the same family; the
  existing insert policy already refuses a foreign family, and the
  parent_entry_id must belong to the same family (checked with the
  parent_id rule 0017 already applies).
- Deleting a note deletes its replies (cascade). No UI for deleting
  exists today; unchanged.

## 4. Webapp

- Under every note (kind 'note', top level): a "Reply" text link.
  Tapping it opens a one-line composer beneath the note with
  REPLY_PLACEHOLDER and REPLY_SUBMIT; Esc or REPLY_CANCEL closes it.
- Replies render indented under their note, oldest first, each with
  author label and date (family-timezone day, 251), in the smaller
  metadata type. A note with replies shows its replies always; no
  collapse in v1.
- Filters (spec 012 §9.1) apply to the note; replies travel with it.
  Timeframe filters key on the note's written-at, not the replies'.
- The upcoming-appointments strip shows the note only; replies
  appear when the note is opened in the list below, as now.
- MCP constraint (263 direction): the reads stay circle-scoped
  functions; a thread is the note plus its replies from the same
  read.

## 5. Strings (VERBATIM; copy laws)

- REPLY_LINK = "Reply"
- REPLY_PLACEHOLDER = "Add to this note"
- REPLY_SUBMIT = "Add"
- REPLY_CANCEL = "Not now"
- REPLY_COUNT_ONE = "1 reply"  (not shown in v1; reserved)

## 6. Tests

Function or trigger refuses: a reply to a reply; a reply to a Kettle
line; a reply with an event_date; a reply across families. Cascade
on delete. Webapp: Reply link only on top-level notes; composer
opens and closes; a reply renders under its note with the family-
timezone date; filters carry replies with their note; copy-law walk.

## 7. Out of scope

Editing or deleting notes and replies; reply counts; notifications
on reply; reactions.
