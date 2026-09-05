# Spec 018 — Notes: edit, delete, and a composer that never keeps you waiting

Status: RATIFIED by Hema, 2026-09-04 (DECISIONS 280). Builds on 012,
016 (replies), 015 (roles), 251/279 (dates).

## 1. What this is

Three things a family found in the first hour of using replies:
a typo is a permanent record; pressing Enter and then Add posts
twice; and a reply written at 11:30pm in Raleigh is dated tomorrow
because the family row says Kolkata. Fix all three.

## 2. Rules (founder, Sep 4)

- Delete: the author deletes their own notes and replies; an admin
  deletes anyone's. Deleting a note deletes its replies (0026
  cascade). Kettle-authored lines (city_change, started,
  first_reply, clean_month) cannot be edited or deleted by anyone.
- Edit: only the author, only their own text. Admins do not rewrite
  other people's words. An edited entry shows EDITED_MARK beside
  its date.
- Authorship: every new note and reply records the author's member
  id, set server-side from the JWT, never from the client. Rows
  written before this spec have no author id; on those, only an
  admin may edit or delete.
- Composer: optimistic. A note or reply appears in the list the
  instant it is sent; the composer clears and locks until the server
  answers; Enter and Add are the same action and cannot fire twice.
  On failure the optimistic row is removed and the text returns to
  the composer with COMPOSER_FAILED beneath it.
- Dates and times on notes and replies render in the VIEWER's
  browser timezone (279). The family zone stays for the parents'
  clocks only. `event_date` (a calendar date) is unchanged.

## 3. Data

Migration numbered at build time.

- `journal_entries.author_member_id uuid null references members(id)
  on delete set null`.
- `journal_entries.edited_utc timestamptz null`.
- Trigger on insert (extend 0026's): when auth.uid() is present,
  set author_member_id to the caller's member row in that family.
- Functions, SECURITY DEFINER, authenticated only, 0004 grants:
  - `app_edit_entry(entry_id, body)`: caller must be the author
    (member id match) and kind must be 'note'; sets body and
    edited_utc; body length rule as 0017.
  - `app_delete_entry(entry_id)`: caller must be the author, or an
    admin of the entry's family; kind must be 'note'. Cascade handles
    replies.
  No client UPDATE or DELETE policy on journal_entries.

## 4. Webapp

- Each note and reply the viewer may edit shows EDIT_LINK; each the
  viewer may delete shows DELETE_LINK. Both hidden otherwise.
- Edit: inline, same composer, prefilled; SAVE / EDIT_CANCEL.
- Delete: one confirm line, DELETE_NOTE_CONFIRM or
  DELETE_REPLY_CONFIRM, with DELETE_CONFIRM_YES / DELETE_CANCEL.
- EDITED_MARK after the date on edited entries.
- Composer per §2: optimistic row, lock, single-fire, failure path.
- Dates and times per §2: viewer zone. `localDay` (256) takes the
  browser zone for journal metadata; the family-zone path stays for
  parent clocks.

## 5. Strings (VERBATIM; copy laws)

- EDIT_LINK = "Edit"
- DELETE_LINK = "Delete"
- SAVE = "Save"
- EDIT_CANCEL = "Not now"
- DELETE_NOTE_CONFIRM = "Delete this note? Its replies go with it."
- DELETE_REPLY_CONFIRM = "Delete this reply?"
- DELETE_CONFIRM_YES = "Delete"
- DELETE_CANCEL = "Keep it"
- EDITED_MARK = "edited"
- COMPOSER_FAILED = "That didn't save. Try again."

## 6. Tests

Functions: non-author edit refused; admin edit refused; non-author
non-admin delete refused; admin delete of another's note allowed;
Kettle lines refused for both; legacy rows (null author) editable
and deletable by admin only; cascade on note delete. Trigger sets
author_member_id from the JWT and ignores a client-supplied value.
Webapp: links shown only where allowed; optimistic row appears
before the response and is removed on failure; a double Enter/Add
produces one row; edited mark renders; a reply written at 03:30Z
renders as the previous day for a viewer in America/New_York and as
the same day for one in Asia/Kolkata.

## 7. Data fix (PM, prod)

Suryaprakasam family row: tz America/New_York (was Asia/Kolkata from
July provisioning; the parents carry their own zones).

## 8. Out of scope

Edit history; deleting Kettle lines; notifications; MCP (spec 019).
