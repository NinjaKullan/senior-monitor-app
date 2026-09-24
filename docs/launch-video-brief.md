# Kettle launch video: background for the video session

Paste this whole file as the first message of the session that writes and
builds the launch video. It is background, not a script. Written by the PM
2026-09-24 from the live product and the ledger; where it says "true" it is
true today. Everything the session produces is a draft the founder approves.

## 1. What to make

A launch video for heykettle.com, LinkedIn and YouTube: 75 to 90 seconds,
16:9, 1920x1080, 30 fps, H.264, with a 9:16 cut for TikTok and Reels made
from the same scenes afterwards. Calm voice-over recorded by the founder
(write the words; do not synthesize a voice) plus on-screen words. Music
optional, quiet, no vocals, licensed or none.

It is a different piece from the 30-second explainer already on branch
`video-explainer` (`marketing/explainer-video/`). That one shows no app and
no faces and sells the feeling. This one shows the product and the AI side
and sells the company. Reuse its look, palette, painted backdrops, font and
render pipeline (canvas frames stepped headless, ffmpeg) wherever they fit;
read its `BRIEF.md` first. Do not change that folder.

Deliverables, in this order, each for the founder's approval before the
next: (1) the script with timings and the exact on-screen words; (2) a
storyboard, one line per shot, naming which app screen or painted scene
each shot uses; (3) the build. Nothing outside `marketing/launch-video/`
changes.

## 2. What Kettle is (say it this way)

Kettle is a small, quiet service for adults who live far from their
parents. It notices whether a parent's normal day happened, using the
phone the parent already owns, and tells the family twice a day in a
short note. If a morning doesn't look like her morning, Kettle asks the
parent first, quietly, before anyone else hears a thing. Nothing to
install in the home, nothing to wear, nothing to charge, nothing to learn.
Founding families pay $10 a month per parent, honoured for as long as they
stay. The founder's own mother and father were the first two people on it
and are on it still: one in Austin, one in Chennai.

The name: in Japan, a tea kettle once told faraway families that their
parents had started the day as usual. Kettle does the same with the phone
your parents already own.

The one line: "For checking in, not checking up."

## 3. What the video must show, in this order

1. **The day.** A parent's phone does what it always does (unlocks in the
   morning, goes on the charger at night). Kettle turns that into two short
   notes to the family, morning and evening, in plain sentences: "Mom's
   morning looked like a normal morning." When a morning is not like her
   morning, Kettle sends the parent one short message on WhatsApp or by
   text and she taps a thumbs up. The family hears only if she doesn't.
   The app's Today card says "Heard from 54 minutes ago", never a verdict.
2. **Memory.** The family's own notes and replies, kept with the parent:
   "Dad's cataract appointment is Thursday." "Called Mom, she sounded
   great." Dated, in the family's own words, nothing Kettle invents.
3. **Who to call.** The parent's number and the people the family listed
   to call if they can't reach her: the neighbour, the cousin, the
   building manager. One screen, no hunting through group chats.
4. **The family circle.** Siblings in one circle, each seeing the same
   notes; two circles for someone with parents in two homes; invite by
   email; admins can add a device or pause a parent while she travels.
5. **AI first.** Kettle is a connector for Claude, ChatGPT and other
   assistants. In the video, a real Claude conversation: "How was Mom's
   morning?" and Kettle's own sentence comes back. Then "Add a note: her
   cataract appointment is Thursday" and the note appears in the app.
   Show, don't claim: the connector was live on 2026-09-05 (read) and
   2026-09-11 (notes and replies). Also Care Compare by HeyKettle, a free
   public tool at care.heykettle.com that reads Medicare's own ratings for
   nursing homes and home health agencies near a ZIP code, in sentences,
   from any assistant or the web (live 2026-09-24). One shot: "Nursing
   homes within 15 miles of 43215 rated 4 or more" and the plain answer.
6. **Close.** The kettle, "Kettle", "heykettle.com", the one line.

Keep each part short; the whole thing is under 90 seconds. Part 5 may be
the longest because it is the differentiator.

## 4. True today (use freely), and what is not

True: iPhone parents by two pre-built Shortcuts sent as a link; WhatsApp
or US text to the parent; Claude connector with read and write; family
web app on any phone; two notes a day; the quiet ask; Memory with notes
and replies; Who to call; circles with admins; pause; a family's own
smart plug or sensor can be added and its last time shown ("Plug, 8:05
this morning") with no judgement drawn from it; Care Compare live.

Not yet, do not show or promise: the Android app (in a seven-day soak on
a test phone; a screen of it may appear only as "coming soon" with the
founder's yes); the ChatGPT directory listing (submitted, not accepted);
any customer, testimonial, statistic, or count of families. There are no
customer quotes. Do not invent one.

## 5. Laws (every one is a hard rule; a test on the site enforces most)

- Never say or show: monitor, monitoring, track, tracking, alert, alarm,
  surveillance, elderly, senior, seniors, sensor, detect, dashboard,
  score, safe, fine, okay as a verdict about a person. "Heard from",
  never "checked in". "Normal", never "ordinary". "Mom" and "Dad" in copy,
  never "your loved one".
- What, never how: say what the family gets, never the mechanism. No
  "signals", "pings", "shortcuts", "automation", "API", "MCP" on screen
  or in the voice-over. "Connector" is allowed because Claude calls it
  that.
- No verdicts, ever. Kettle reports; the family reads. No red or amber
  states, no exclamation marks, no sirens, no hospital, pills, walkers.
- Straight apostrophes; no em dashes anywhere, including on-screen words.
- Parents are capable and busy, never frail, confused, sad or waiting at
  a window. Adult children are not anxious wrecks; they are relieved.
- No real parent's data on screen. Every app screen comes from the
  Rehearsal family (TestDad, TestMom, Raleigh); rename on screen to
  "Mom" and "Dad" or "Priya's mom" by CSS or overlay, never by editing
  the app. The founder logs the recording device into the Rehearsal
  circle himself.
- No faces in painted scenes (the explainer's rule; keep it so the two
  videos match). Real screen recordings of the app are fine.
- Palette: paper #F7F1E8, ink #403C36, Kettle green #297A5C, warm yellow
  #E8C77A for light, copper #B26D3F only where the app itself uses it.
  No pure black, pure white, red, orange, neon, glossy gradients.
- Font for on-screen words: `tools/social/fonts/PatrickHand-Regular.ttf`,
  large, ink, centred, never over a face or a screen's text.
- Only logo: the word "Kettle" and the painted kettle
  (`marketing/explainer-video/assets/kettle.png`).

## 6. Sources in the repo (read before writing)

- `docs/kettle-brief-for-ai-writers.md`: voice, the self-check list.
- `site/src/copy.ts`: every sentence the site says; quote it, do not
  paraphrase it into something new.
- `marketing/explainer-video/BRIEF.md` and `index.html`: the look and the
  render pipeline.
- `specs/019-mcp.md` (the connector, and its exact answer strings in
  `product/kettle/assistant_copy.py`), `specs/012-*` and `016-*`
  (Memory, replies), `specs/015-*` (circles), `specs/017-*` (pause),
  `specs/020-*` (a family's own devices), `specs/021-care-compare.md`.
- `webapp/src/` for what the screens actually say; the video quotes the
  app, the app does not bend to the video.
- `docs/feature-backlog.md` §5 for LAW-1 to LAW-10 in full.

## 7. What to ask the founder before starting

Only these: (1) confirm 75 to 90 seconds landscape first; (2) whether he
records the voice-over or the video runs on on-screen words alone; (3)
whether the Android "coming soon" frame is in or out; (4) the release
date, so the close can say "Founding families, now" or a date.
