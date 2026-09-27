# Kettle human video session: charter and background

Paste this whole file as the first message of a new session whose only job
is one film with AI-made people in it. Written by the PM 2026-09-26 from
the live product, the two earlier video briefs and the ledger. Where it
says "true" it is true today. The founder (Hema) pastes prompts into the
video tool, presses every button, and posts; this session writes, plans,
reviews and logs.

## 1. What to make

One 30-second film, real-looking people, about an adult child and a parent
who lives on her own, with Kettle as the quiet part. Two cuts from one
master: 16:9 for the product-release post and the site, 9:16 for social and
any paid placement later. AI-generated picture and AI-generated voice; no
actors, no stock, no founder on camera. The app appears only as the real
screen recordings from the launch shoot (R1 to R9 in
`marketing/launch-video/recordings/`, gitignored, on the founder's Mac),
composited onto a phone in shot.

This is the third Kettle film. The explainer (branch `video-explainer`) has
no faces and sells the feeling. The launch video (branch `launch-video`)
is painted paper and shows the product. This one shows people. Read both
briefs first (`docs/launch-video-brief.md`, `marketing/explainer-video/`)
so the three feel like one company.

## 2. Who it is for (founder ruling, 2026-09-26)

Adult children with a parent aging in place. Not daughters only: the GTM
research says employed adult daughters are the majority buyer, but the film
speaks to any son or daughter. Write the pair as "the adult child" and "the
parent"; do not pin gender in the script. If the tool makes a second cast
cheap, generate a son version and a daughter version of the same cut and
let the founder pick.

## 3. What Kettle is (say it this way)

Kettle is a small, quiet service for adults who live far from their
parents. It notices whether a parent's normal day happened, using the
phone the parent already owns, and tells the family twice a day in a
short note. If a morning doesn't look like her morning, Kettle asks the
parent first, quietly, before anyone else hears a thing. Nothing to
install in the home, nothing to wear, nothing to charge, nothing to learn.
The founder's own mother and father were the first two people on it.

The one line: "For checking in, not checking up."

## 4. The story shape (settled)

A day in the life, two people, three beats, no dialogue between them
needed:

1. Morning, the parent's kitchen. She is up, busy, herself: kettle on,
   phone on the counter, a normal morning. Not frail, not waiting.
2. Mid-morning, the adult child at work or on the move. The phone buzzes
   once; the note reads "Mom's morning looked like a normal morning." A
   small exhale, back to the day. That is the whole product moment.
3. Evening, a short call between them about nothing in particular. Warm
   and easy. End card: "Kettle. For checking in, not checking up."
   heykettle.com.

The voice-over is one calm voice, first person, the adult child, under 60
words. It says what changed for them, never how Kettle works. Draft three
versions of the script for the PM before any generation.

## 5. True today (use freely), and what is not

True: morning and evening notes by email; the parent is asked first, by
WhatsApp, on a quiet morning; the family shares Memory notes, a Who to
call list and a family circle; the family can ask Claude about a parent's
day; Care Compare reads Medicare ratings. Founding families are free
through the beta, then $10 a month per parent.

Not true, never imply: fall detection, cameras, location, health data,
counts of anything, a verdict that someone is safe or fine, an app the
parent has to use.

## 6. Laws (hard rules; the site's copy test enforces most)

- Never say or show: monitor, monitoring, track, tracking, alert, alarm,
  surveillance, elderly, senior, seniors, sensor, detect, dashboard,
  score, safe, fine, okay as a verdict about a person. "Heard from", never
  "checked in". "Normal", never "ordinary". "Mom" and "Dad", never "your
  loved one".
- What, never how. No "signals", "pings", "shortcuts", "automation",
  "AI" as a feature word in the voice-over. (The film is made with AI;
  the product is not sold as AI.)
- No verdicts, ever. No red or amber, no exclamation marks, no sirens,
  no hospital, pills, walkers, no fall, no empty chair.
- Parents are capable and busy. Adult children are relieved, not anxious
  wrecks. Nobody cries.
- Straight apostrophes; no em dashes anywhere, including end cards.
- No real parent's data on screen. Screens are R1 to R9 only, and only
  the frames where the names read Mom and Dad.
- The people are AI-made and must not resemble a real person. No
  celebrity or "looks like" prompts. No children.
- Palette and type for anything drawn on top (end card, captions): paper
  #F7F1E8, ink #403C36, Kettle green #297A5C; font
  `tools/social/fonts/PatrickHand-Regular.ttf`. Live-action frames keep
  their own light; no filters that fight the palette.
- Only logo: the word "Kettle" and the painted kettle
  (`marketing/explainer-video/assets/kettle.png`).

## 7. The tool (Higgsfield, or another if it does the same three things)

The founder chose Higgsfield. What matters, whichever tool: one trained
face per character that carries across every clip (Higgsfield calls it
Soul ID); voice generated in-tool and lip-synced (LipSync Studio; Veo 3 or
Kling for the human shots); clips of 5 to 10 seconds stitched, never one
long generation (gesture repeats past ~10 s). Plan the film as 6 to 9
clips plus the screen inserts. Budget: the Plus plan for one month, about
$49, is enough for a 30-second film with redos at roughly 15 to 20 Veo 3
clips; do not spend past $100 without asking. Commercial use terms: the
session reads the current terms and quotes the line to the founder before
the first paid generation.

## 8. How the session works

- Own log: `docs/human-video-log.md`. Every prompt that produced a kept
  clip, every clip's number, cost in credits, and what was rejected and
  why. Commit the log with each change.
- Never touches product code, `specs/`, `DECISIONS.md`, the site, or
  the other two video branches. Works on branch `human-video` under
  `marketing/human-video/`.
- Order: script (three versions) to the PM; PM picks one and rules on
  wording; then shot list with one prompt per clip; founder generates;
  session reviews stills and asks for redos; cut; PM reviews the cut
  against section 6 before anything is posted.
- The founder posts. The session never publishes anything.
- Stop and ask if: a generated face resembles a real person; a clip needs
  a claim not in section 5; the tool's terms limit commercial use; the
  cost passes $100; or the script wants a word from the banned list.

## 9. Sources in the repo (read before writing)

`docs/launch-video-brief.md` (laws and product order), `docs/feature-backlog.md`
section 5 (LAW-1 to LAW-10), `docs/gtm-market-research-2026-08.md`
(who buys and why), `marketing/launch-video/STORYBOARD.md` and `SCRIPT.md`
(the tone the three films share), `site/public/index.html` (the words the
site already uses).

## 10. Decisions for the founder (recommended defaults in bold)

1. An end-card line saying the people are AI-made. **Yes: "The people in
   this film are made with AI."** Small, ink, on the end card. Honest, and
   it stops the "is that a real customer" question before it is asked.
2. Length. **30 seconds master.** A 15-second cut for paid social comes
   from the same clips later if paid social happens.
3. Music. **None, or one held note under the voice.** Same rule as the
   launch video.
