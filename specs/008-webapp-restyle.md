# Spec 008 — The webapp wears Kettle v5

*PM: Fable, 2026-08-23. The family app is restyled to the locked v5 design
(docs/Kettle-Design.html — the extracted reference; open it in a browser to see
every screen and state). A RESTYLE, not a rewrite: every data read, guard, and
test from DECISIONS 160/166 stays; the visual layer changes over them.*

## 1. Scope

Phase 1 restyles exactly three surfaces: **Today**, **Parent detail**, and
**Family (parents list only)**. Explicitly OUT of phase 1 (DECISIONS 169):
the Digests screen (retired in 156; returns post-beta on a purpose-built read
surface with PER-PARENT notes only), per-member note toggles and invites (the
fan-out tier DECISIONS 157 ranked "later"), and the add-a-parent flow (parked
with onboarding, QUESTIONS 126). The v5 file shows these; the build omits them.
Nav renders Today and Family only.

## 2. Design source of truth

docs/Kettle-Design.html carries the tokens verbatim: the Day/Night custom
properties (--paper, --card, --ink*, --copper*, --hearthfill/-ring, --cup,
--steam, --mute, --hair, radii 22/20/16/14px), Newsreader for sentences and
titles (h1 38px/500, card sentence 23px/500, hero 31px/500), Source Sans 3 for
everything else. Lift values from the file; do not re-derive by eye. Fonts are
self-hosted or system-fallback — the app makes no third-party font requests if
that is its current posture; keep whatever the current build does.

## 3. The three-state glyph

One SVG component, two sizes (44px card, 200px detail hero), three states:
- ordinary: hearthfill disc + hearthring stroke, cup+handle in --cup, two steam
  rects in --steam
- quiet: unfilled disc + --copper stroke (thinner), cup in --copper, no steam
- unreachable: unfilled disc + --mute stroke, no cup, two --mute pause bars
The exact geometry (circle r=18, cup path, handle path, steam/pause rects) is
in the design file's icon markup — copy it, don't redraw. "The kettle's on"
text renders ONLY inside the ordinary-state hero. No animation at 44px; steam
may drift gently on the hero only, honoring prefers-reduced-motion.

## 4. Copy

All customer-facing strings come from the v5 file EXCEPT:
1. "She answered — all is well." renders as "She answered." (DECISIONS 169 —
   Kettle knows that she answered, never what she said).
2. Any string belonging to out-of-scope surfaces is not shipped.
State sentences map to the webapp's existing state model: ordinary-day, quiet
(the existing honest-absence path), unreachable (the >full-silence distinction
the tripwire ages already expose). Existing copy-law tests extend over every
new string; the pronoun rule applies (v5's she/her strings parameterize on the
relationship label's pronoun set or restructure — restructuring preferred).

## 5. Requirements & acceptance

1. Today: responsive card grid, one card per parent (glyph, name eyebrow,
   local-time meta, state sentence, last-heard line). Sidebar nav (wide) /
   bottom tabs (narrow) per the file. Dark ("Night") tokens included.
2. Parent detail: hero glyph + sentence + local-time line, Call button
   (tel: from a phone field only when one exists — else no button, never a
   dead one), the Morning/Afternoon/Evening day rows in words, the
   two-minute-fix card gated on the same condition that today drives the
   "small thing to fix" nudge, Recent days list from existing per-day data,
   About block from provisioning fields that exist (omit what doesn't).
3. Family: the parents list card only, honest sub-lines, no toggles/invites.
4. All existing tests stay green or are updated ONLY where a string/layout
   they pinned deliberately changed; the 160/166 pings-read discipline and
   audit tests unchanged. Copy-law scan green over the full new string set.
5. npm run ci clean; product/site/pilot untouched; nothing deployed (deploy
   is the founder's, after the Wave B flip settles).
