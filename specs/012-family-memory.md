# Spec 012 — Family Memory: the journal becomes a place

Status: RATIFIED by Hema, 2026-08-30 (DECISIONS 200) — all §8
rulings approved as drafted: tab name Memory, the four auto-note
strings, the empty-state line, the contacts heading. Scope rulings already made by Hema in session
(Aug 30): third tab YES; gentle-whats auto-notes YES; contacts
in-spec YES; photos DEFERRED. Asana: 1217867436034126 (family
journal backlog task — its PM review and phase plan are incorporated
here and remain binding).

## 1. What this is, and the law it lives under

The journal already exists (migration 0017, NotesPanel, auto-note on
city change). Today it is a sidebar embedded in two screens. This
spec promotes it to a first-class tab named **Memory** and adds the
two things that make it compound: Kettle writing a few warm lines of
its own, and the family's own contacts sheet living beside it.

Why: retention. Daily notes are ephemeral; a memory is an asset. A
family three months in owns a record they cannot take elsewhere and
would feel the loss of. It also widens the multi-sibling pitch
(the $12.99 competitor story in the Asana task) without chasing the
caretaker-log market.

GUARDRAILS (unchanged from the task's PM review): companion to the
daily note, never a care-coordination suite. No task assignments, no
schedules, no medication-dose tracking, in this spec or its
follow-ons under this number. Asks nothing of the parent, ever.

## 2. The Memory tab

- Nav becomes Today / Memory / Family. (ruling: the tab name —
  "Memory" recommended; alternatives "Journal", "Notebook".)
- The consolidated cross-parent feed (currently on the Family screen)
  MOVES to Memory: upcoming-dated strip on top, then entries
  newest-first, tag picker (Mom / Dad / Family), composer at top.
  ParentDetail keeps its scoped panel unchanged. Family screen slims
  to members + city/timezone + setup links.
- Month separators in the feed ("August 2026") — cheap, and they turn
  a list into a record.
- Empty state (verbatim, ruling): "Notes from your family and from
  Kettle live here. The first ones arrive on their own."
- Reads stay capped and paginate by month boundary rather than a hard
  row limit.

## 3. Kettle-authored lines (the gentle whats set)

Principles: whats never hows; no verdicts; NO escalation or ladder
events EVER — memory is a warm record, not an incident log. Absence
speaks, exactly like the product.

v1 auto-note kinds, strings to be ratified VERBATIM (ruling), with
the existing city note unchanged:

1. city_change (exists): "{Parent}'s city changed to {city}."
2. started: "Kettle's first morning with {Parent}." — written when a
   parent's first daily note goes out.
3. first_reply: "Heard from {Parent} with a 👍." — written once, on a
   parent's first-ever WhatsApp reply on the real number (Wave D).
   "Heard from" is the sanctioned verb; this is its natural home.
4. clean_month: "A normal {month}, start to finish." — written on the
   1st, ONLY when the previous month had no silent-day escalation for
   that parent. A month that wasn't clean gets NOTHING — no entry, no
   qualifier. Echoes the evening digest's ruled copy.

Mechanics: the product backend (kettle/) gains a small journal writer
(insert-only, author_label "Kettle") — today only the webapp writes.
Idempotency keys per (kind, parent, period) so reruns never
double-write. Each string lands in DECISIONS verbatim at ship, per
standing law.

## 4. The family contacts sheet ("If you can't reach them")

The digital twin of the emergency printable (asset #6 / the block on
asset #1 page 3), and the same four rows to start: a neighbor,
someone in the family who lives nearby, their building or front
desk, their doctor.

- New table family_contacts: id, family_id, parent_id (nullable =
  family-wide), label, name, phone_e164, phone_display, note (short),
  position, created/updated, author_label. RLS family-scoped like
  journal. UNLIKE the journal, contacts are editable and deletable —
  they are reference data, not record.
- UI: a calm card at the top of Memory (or per-parent on
  ParentDetail; CC proposes, PM reviews), labels free-text with the
  four suggested rows pre-offered as placeholders. Phone numbers
  render as tap-to-call links (elder-proofing law: E.164 stored,
  human-readable shown).
- NEVER auto-populated. Family-entered only. No lookup of "services
  near them", no directory — a stale emergency number we suggested is
  worse than a blank line the family owns. (This closes the "local
  emergency numbers" idea: the family's OWN numbers yes, our
  directory no.)

## 5. Schema and build shape

- Migration 0020: journal_entries ADD COLUMN kind text NOT NULL
  DEFAULT 'note' (auto kinds: city_change, started, first_reply,
  clean_month); backfill existing "Kettle"-authored rows to
  city_change. Insert-only posture UNCHANGED for journal v1;
  correction path is a new entry.
- Migration 0021: family_contacts as above, with update/delete
  grants and RLS.
- API-first: data functions shaped so phase 3 (MCP read access for
  the family's AI agents) is a thin layer later — per the task, gated
  on token scoping + privacy counsel, not in this spec.
- Tests: RLS isolation both tables; auto-note idempotency (rerun a
  period, one row); clean_month suppression (a month with an
  escalation writes nothing); copy scan over every new string;
  webapp render tests for the new tab.
- Size: Phase-1-shaped, roughly one to two CC days. No cost impact.

## 6. Privacy (binding, from the task's PM review)

A journal invites health-adjacent content into a database that today
stores almost nothing — that stays a family-authored-content story,
never a Kettle-inference story. Before any STRANGER family joins:
privacy.html updated to name family notes and contacts; a deletion
path for journal content exists (family-level export/delete is
acceptable v1 — row editing stays out); privacy counsel pass. For
the pilot family, ship without ceremony.

## 7. Out of scope (recorded so they stay out)

Photos/media (fast-follow AFTER privacy counsel; needs bucket +
upload UX). Multi-account family circle (phase 2, sized when a real
sibling family asks). MCP read access (phase 3). Reactions, threads,
comments. Any digest/notification hook from journal entries. Native
mobile app (PWA ruling stands). Local-services directories of any
kind.

## 8. Rulings requested from Hema

(a) Tab name "Memory". (b) The four auto-note strings in §3,
verbatim. (c) Empty-state line in §2. (d) Contacts card heading "If
you can't reach them" (mirrors the printable). Once ratified: file
the DECISIONS entry, then CC builds from pushed git after Wave D
Phase 2 — Wave D keeps priority for CC's queue.
