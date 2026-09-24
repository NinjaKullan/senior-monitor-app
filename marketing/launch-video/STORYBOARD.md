# Kettle launch video: storyboard (phase 2 draft)

Words and timings are in SCRIPT.md. There are five painted sets and one plain paper table
(the "plate") that every screen shot sits on. Each Gemini layer is painted flat on a clean
background and cut out to a transparent PNG. Blender stands it up as a paper card.
Anything that moves or glows (steam, the lit phone screen, the message slip) is a Blender
card or a light, not a painting.

## Shots

| # | Picture | Source |
|---|---|---|
| 1 | Paper map on a table. The camera drifts from the city apartment toward Mom and Dad's house as a paper sun comes up behind it. | Set MAP. Layers: map sheet with a faint dotted path (no text, no labels), city apartment block, parents' house (green roof, kitchen window), dawn sun disc, two paper trees, one cloud. |
| 2 | Mom's kitchen in morning light. The kettle steams, the phone on the counter lights up. Slow push-in. | Set KITCHEN. Layers: back wall with window, counter and stove, green kettle (painted to match assets/kettle.png), phone body (screen is a Blender emissive card), mug, small plant. |
| 3 | Two paper phones lie side by side on the table, both screens plainly lit. Gentle orbit. | Set PHONES. Layers: phone A (one rounded body, single lens), phone B (a different body and lens cluster, so they read as two makes without any logo), a folded napkin for scale. |
| 4 | The morning note, as the family gets it. | Screen R1 on the plate, right third. Caption left. |
| 5 | Today card: "Heard from N minutes ago". | Screen R2 on the plate. |
| 6 | The same kitchen, bright and tidy. The kettle is cold, the phone is on the table. The camera holds low and still, calm, not ominous. | Set KITCHEN restaged. No new layers: the phone moves to the table, no steam. |
| 7a/7b | Close on the phone. A blank paper slip settles on its screen, then a paper thumbs up rises beside it. The camera drifts slowly. | Set KITCHEN close-up, plus 1 new layer: paper thumbs-up cutout (a symbol, no hand or arm). The slip is a plain Blender card. |
| 8 | Memory with notes and a reply. | Screen R3 on the plate. |
| 9 | Who to call. | Screen R4. |
| 10 | Family circle. | Screen R5. |
| 11a/b | Claude: "How was Mom's morning?", then Kettle's sentence. | Screen R6. |
| 12 | Claude: add a note, read back, saved. | Screen R7. |
| 13 | Memory, the new note at the top. | Screen R8. |
| 14 | Claude with Care Compare, home health near 43215. | Screen R9. |
| 15 | Painted kettle on the paper table, a wisp of steam, the words. | Set CLOSE: assets/kettle.png as a card, Blender steam. No new layers. |
| plate | Empty cream table, soft top-left light, faint paper grain: the ground for every screen shot. | 1 layer: paper tabletop texture. |

About 20 Gemini layers in all. With redos that should fit inside the 60-image phase 4 budget.

Screen shots: the recording goes on the plate flat and square-on, about 880 px tall, in a paper
phone frame with a soft shadow. The caption sits on the plate to its left, never over the
screen. For the 9:16 cut, the screen fills the frame and the caption sits in the top band.

## Names on screen

The brief says to rename by CSS or overlay. Overlays hold on a still screen but not on a
scrolling Claude chat, where "TestMom" appears inside sentences. For that reason:

- Hold every recording still once the content is on screen, with no scrolling unless a step says so.
- The app screens R2 to R5 and R8: I cover "TestMom" and "TestDad" with a paper-coloured patch
  and "Mom" or "Dad" in the app's own font. I also crop out the circle switcher, which shows
  real family names.
- Claude R6 and R7: see decision 2 below.

## Screen recordings you must make

All on one iPhone, portrait, light mode, default text size. Before you start: Do Not Disturb on,
no notifications, battery charged. Start each recording 2 s before the first tap and stop 3 s after
the last thing appears. Signed in to kettle-app with the Rehearsal circle chosen.

Set up once in the Rehearsal circle first, in the app:
- Memory: a note "Called Mom, she sounded great." with a reply "Same. She told me all about the garden.",
  and an upcoming note tagged TestDad, "Dad's birthday dinner is Saturday." dated this Saturday.
  (Changed from the script's shot 8 example: the cataract note is added live in R7, so it can't
  already be there in R3.)
- Who to call, tagged TestMom: "A neighbor", Linda, (555) 010 2201, "Next door, has a key";
  "Someone in the family nearby", Cousin Ravi, (555) 010 3302; "Building or front desk",
  Front desk, (555) 010 4403, "Open 7am to 10pm". Use 555 numbers only.
- Family circle: at least two people (add a second seat if there is only one).
- Claude: Kettle's tools set to Always allow, so no permission prompt breaks the shot.
  Care Compare added as a connector (https://care.heykettle.com/mcp).

| Rec | For shot | Steps |
|---|---|---|
| R1 | 4 | Open the mail app, open a Rehearsal morning note email ("...'s morning looked like a normal morning. Next note this evening."). Hold 8 s. |
| R2 | 5 | kettle-app, Today. TestMom's card showing "Heard from N minutes ago", any N under 60. Hold 8 s. |
| R3 | 8 | Memory tab. The note, its reply and the upcoming note all visible without scrolling. Hold 8 s. |
| R4 | 9 | Who to call tab, filtered to TestMom: her Call line and the three contacts. Hold 7 s. |
| R5 | 10 | Family tab, scrolled so "Family circle" and its people fill the screen. Hold 4 s, tap "Add someone", hold 3 s, tap "Not now". |
| R6 | 11a/b | Claude app, new chat. Type "How was Mom's morning?" (see decision 2) at a calm pace, send, wait for the full answer, hold 5 s. |
| R7 | 12 | Same chat. Type "Add a note: her cataract appointment is Thursday", send. Claude reads it back and asks. Type "Yes", send, wait for "Saved. The family will see it in Memory.", hold 4 s. |
| R8 | 13 | kettle-app, Memory. The new note at the top, with "via Claude". Hold 6 s. |
| R9 | 14 | Claude app, new chat. Type "Home health agencies within 15 miles of 43215 rated 4 or more", send, wait for the full answer, hold 3 s, scroll slowly to the Source line, hold 3 s. |

Drop the files into `marketing/launch-video/recordings/` as R1.mp4 to R9.mp4 (gitignored, not committed).
Until they arrive, phases 3 and 4 use labelled grey cards.

## Decisions for the founder

1. Which account records. Your account is in two circles, and the switcher names the real one.
   Recommended: add a second seat to Rehearsal with another email of yours and record the app from
   that login, so nothing real can appear on screen.
2. "TestMom" in the Claude chat. Kettle matches names, so the question has to say "TestMom", and
   the answer says it back several times inside sentences. Overlays on a chat are fragile.
   Recommended: for the recording session, change the Rehearsal parents' display names to "Mom"
   and "Dad" (their data, not the app), record R2 to R8, then change them back. The fallback is
   to type "TestMom" and let me patch each occurrence frame by frame.
