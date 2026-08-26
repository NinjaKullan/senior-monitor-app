# Spec 009 — Glance redesign: Today, Parent detail, Family notes

Status: approved by Hema 2026-08-26. Design source of truth:
`docs/mockups/glance-redesign-mockup-v2.html` (v2; the copper Call button is
the locked choice, the green variant on Dad's card is rejected). Tokens,
fonts, and the three-state glyph come from `docs/Kettle-Design.html` and the
shipped `KettleGlyph.tsx`; geometry is never redrawn by eye. Webapp only;
the outbound engine and site are untouched by this spec.

Authority for copy: every user-visible string in this spec is final unless
marked (ruling). All copy laws apply: what Kettle does, never how; no
verdicts, counts, signal names, gendered pronouns, or em dashes; "heard
from", never "checked in"; "normal", never "ordinary".

## 1. The word "normal" replaces "ordinary" everywhere

- `STATE_ORDINARY` copy becomes "Today looks like a normal day." Day rows
  and any other webapp string using "ordinary" switch to "normal". The
  state's internal name may stay `ordinary`; only rendered copy changes.
- The unreachable duration line "Nothing has reached Kettle since 9 days
  ago" becomes "Nothing has reached Kettle in 9 days." (n days, singular
  "1 day").

## 2. Today screen

Order: kicker date, family rollup, one card per parent, footer line.

- Kicker: weekday and date, e.g. "Wednesday · August 26" (middot, no em
  dash).
- Family rollup (Newsreader, large), by precedence unreachable > quiet >
  normal:
  - all parents normal: "Everything looks normal today."
  - any quiet (none unreachable): "Quiet so far for {Name}." (two quiet:
    "Quiet so far for {Name} and {Name}.")
  - any unreachable: "Kettle can't hear from {Name}'s phone right now."
  - Sub-line under the rollup: "Next note this evening." before the
    evening digest hour, "Next note in the morning." after it.
- Parent card, exactly the mockup layout:
  - 44px glyph in the parent's current state.
  - Name label (relationship label, e.g. MOM) and a second line
    "{city label} · {local time} there now" when a city label exists,
    otherwise "{local time} {Name}'s time".
  - State line (Newsreader): normal "Today looks like a normal day.";
    quiet "Quiet so far today."; unreachable "Kettle can't hear from
    {Name}'s phone right now."
  - Time, relative first: "Heard from {relative} ago" with buckets:
    under 2 min "moments ago"; minutes to 59; then hours ("2 hours ago");
    then days; beyond the 14-day window use the existing DECISIONS 166
    wording. Second line, small: "{time} in {city label or '{Name}'s
    time'} · {time} your time".
  - Actions row: copper pill "Call {Name} ↗" as `tel:{phone_e164}` (or
    `wa.me/{whatsapp_e164}` when phone_e164 is absent; hide the button if
    neither exists), and quiet link "View {Name}'s day →".
- Footer, only when every parent is normal: "Nothing needs you today.
  Kettle will write if that changes." When any parent is quiet or
  unreachable the footer is omitted (the rollup already carries it).

## 3. Parent detail screen

Order: back link, hero, time block, Call button, The day, Recent days,
What this means, fix card (conditional), Family notes.

- Hero: 44px glyph, "{NAME} · {city label}" kicker, state line as on the
  card.
- Time block: "Heard from {relative} ago" bold; sub-line adds the offset
  sentence from the existing About block ("nine and a half hours ahead of
  you") joined with middots.
- Copper "Call {Name} ↗" pill.
- The day (panel "THE DAY"): one arc path drawn twice, background stroke
  `--hearthring`, progress stroke `--olive` revealed with
  `pathLength`/`stroke-dasharray` to the fraction of the parent's local
  day elapsed (midnight to midnight); dot sits at the reveal end,
  positioned on the same curve. Never two different curves. Below, three
  cells Morning (before noon local), Afternoon (noon to 6 pm), Evening
  (after 6 pm): caption "Heard from {last ping time in segment}" when one
  exists, "Quiet" for a past segment with none, "Still ahead" for a
  future segment.
- Recent days (panel "RECENT DAYS"): seven cells, oldest left, Today
  right, each a 16px state chip reusing the day classification the app
  already computes: normal day = filled `--hearthfill` with
  `--hearthring` ring; quiet start = `--copper` outline; no pings all
  day = `--mute` outline. Weekday abbreviations beneath. NO tally, NO
  checkmarks, NO count anywhere. Legend, always visible: "A normal day",
  "A quiet start", "Couldn't hear" with matching chips. States must
  remain distinguishable with color removed (fill vs outline + legend).
- What this means (card): normal: heading "No action needed." body
  "{Name}'s day looks like most days. Kettle will write if that
  changes."; quiet: heading "Nothing to do yet." body "Kettle will check
  in with {Name} first if the quiet continues."; unreachable: heading
  "Worth a look." body existing unreachable guidance copy, unchanged.
- Fix card: unchanged FIX_BODY copy and trigger, restyled to the mockup's
  tinted card with "See the simple steps →".

## 4. Family notes (the journal, v1)

Positioning inside the app: the panel is titled "FAMILY NOTES" with the
sub-line "The family's memory. Everyone in the family can read and add."
Never any copy about decline, care stages, or preparing for the worst.

- Migration (next number): table `journal_entries`:
  `id bigint identity pk`, `family_id uuid not null references families`,
  `parent_id uuid null references parents`, `author_label text not null
  default ''`, `body text not null check (char_length(body) <= 2000)`,
  `event_date date null`, `created_utc timestamptz not null default
  now()`. RLS mirrors the existing per-family policies exactly (deny
  all, family members read/insert their family's rows; no update/delete
  in v1).
- Scoping law: the parent detail panel shows only entries where
  `parent_id` = this parent. The Family screen gains a consolidated
  "Family notes" list: all entries for the family, newest first, each
  prefixed with the parent's relationship label or "Family" when
  `parent_id` is null. New entries created from a parent page default to
  that parent; from the Family screen the tag is selectable (Mom / Dad /
  Family).
- Upcoming strip: entries with `event_date` today or later render at the
  top of the panel as "Upcoming · {body, first line} on {Weekday, Mon D}
  · added by {author}". Past `event_date` renders inline in the entry
  metadata ("for Aug 20").
- Entry rendering: metadata line "{Mon D} · {author_label or 'Family'}",
  then body. Bodies are plain text, HTML-escaped, with URLs auto-linked
  at render (https/http and bare domains), `target="_blank"
  rel="noopener noreferrer"`, styled as underlined copper links. No rich
  text, no images, no attachments in v1.
- Composer: single-line field "Add a note for the family…" expanding on
  focus, a "+ date" chip opening a native date input, and a small
  "Signed as" input prefilled from the last used value (localStorage;
  empty is allowed and renders as "Family"). Reads are capped at the 50
  newest per scope with the existing bounded-read discipline (DECISIONS
  160); no unbounded queries.

## 5. City label (display only, this spec)

Migration adds `parents.city_label text null`. Family screen's parent row
gains an optional "City" text field the child edits (kid-entered, free
text, max 40 chars). Where present it renders as in the mockup; where
absent, fall back to "{Name}'s time". Timezone itself is NOT editable in
this spec (separate backlog task); the label is cosmetic.

## 6. Accessibility (law, tested)

- All typography in rem; layout verified unbroken at 200% browser zoom.
- Text contrast AA: 4.5:1 minimum for normal text, 3:1 for large; nothing
  smaller than the mockup's metadata sizes may use `--mute`.
- No state distinguishable by color alone anywhere (shape or fill
  difference plus visible text, per the glyph system).
- `prefers-reduced-motion` continues to gate all animation.

## 7. Tests and process

- Component tests pin: rollup precedence and all three rollup strings;
  card state lines; relative-time buckets incl. the 14-day boundary;
  dual-time line; Call button href logic and its absence without numbers;
  arc single-path rule (two path elements, identical `d`); dots carry no
  digits (regression against tallies); legend strings; what-this-means
  copy per state; journal scoping (parent page filters, Family page
  consolidates, null parent renders "Family"); URL linkification is
  escaped (an entry containing `<script>` renders inert); Upcoming
  ordering; bounded reads.
- The chrome copy scan (em dashes, banned words, "ordinary", "checked
  in", "since ... days ago") runs over all new strings.
- File one DECISIONS entry per numbered section actually built, with all
  new user-visible strings recorded verbatim. Migrations applied to prod
  by the PM via MCP after review, per standing practice.

## Out of scope (explicitly)

Editable timezone, consolidated/multi-recipient emails, family member
accounts and invites, MCP access to notes, entry edit/delete, email
template changes (separate pass), Digests screen.
