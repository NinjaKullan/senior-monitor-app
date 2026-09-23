# Kettle explainer video: brief

## Done means
- `out/kettle-explainer.mp4` exists: 1080x1920, 30 fps, H.264, yuv420p, no audio, 28 to 32 seconds.
- It plays the five scenes below in order, with exactly the on-screen words below and nothing else.
- `out/still-1.png`, `out/still-3.png`, `out/still-5.png` exist (one frame from scenes 1, 3, 5).
- `npm run render` (inside this folder) rebuilds all of the above from scratch, same result every time.
- Source committed on branch `video-explainer` and pushed. Nothing outside `marketing/explainer-video/`
  changed except one line in the root `.gitignore` for `marketing/explainer-video/out/` and `node_modules/`.

## What it is
One `index.html` + JS on a canvas. The still backdrops are paper-cutout paintings made ONCE with
Gemini (`paint.mjs`, prompts in `assets/PROMPTS.md`) and committed in `assets/`. Everything that
moves is drawn in code on top: lights switching on, window glow, steam, the travelling light and its
dotted path, the phone lighting up, all words. No stock, no icon fonts. Render never calls Gemini.
Frame N is a pure function of N (no Math.random without a fixed seed, no wall clock), so rendering
is repeatable. Render by stepping frames headless and encoding with ffmpeg.

## Look
Paper cutout. Flat shapes with slightly torn, uneven edges, a faint paper grain, a soft drop shadow
under each cut piece, gentle eased motion (nothing snaps, nothing bounces).
Palette: paper #F7F1E8, ink #403C36, Kettle green #297A5C, pale grey-green #C9D3C6 for shadows,
warm yellow #E8C77A for window light and morning sun only.
Font for all words: `tools/social/fonts/PatrickHand-Regular.ttf` (load it with @font-face).
Words: large (at least 72px), ink colour, centred, inside the middle 76% of the height (the top and
bottom 12% are covered by app buttons on TikTok and Reels). One line of words on screen at a time.

## Do not produce
- Pure black or pure white anywhere; red or orange; neon; gradients that look glossy or 3D.
- Any phone screen showing an app, chart, graph, number, notification badge or UI. Phones show only
  a plain lit rectangle; the kid's phone may add one blank paper card (no words, lines or icons).
- Hospital, medicine, pills, walkers, alarms, sirens, warning triangles, exclamation marks.
- The mother looking frail, confused, sad or waiting at a window. She is busy and capable.
- Text touching a figure's face, text cut off at the edge, two text lines overlapping.
- Any logo other than the word "Kettle".
- No human faces or bodies. No hands, silhouettes or figures, and no glow around a figure.
- Lonely or empty darkness. Night scenes are cozy: a lamp on, lit windows, things on the table.
- Text inside a painted backdrop. All words come from code, in the font above.

## Places and things (no people are shown)
- MOM'S HOUSE: small cream house, Kettle-green roof, one kitchen window, on a green hill.
- MOM'S KITCHEN: counter, stove, the kettle, her phone standing on the counter.
- THE KID'S APARTMENT: city window with curtains, a table with a lamp, mug, plant and the phone.
- THE KETTLE: small stovetop kettle in Kettle green, curved spout, black handle. Never has a face.

## Story (on-screen words exactly as written, straight apostrophes)
1. 0 to 6 s. Night at the kid's city apartment: dark blue-green sky and lit windows outside, the
   lamp on, the phone resting dark on the table.
   Words: "Is Mom's day starting okay?"
2. 6 to 12 s. Mom's house at dawn; the camera eases in as morning comes up and her kitchen window
   lights. Inside, the kettle lets out a little steam and her phone on the counter lights up. No words.
3. 12 to 19 s. A paper map: a small warm light travels along a dotted path from Mom's house to the
   kid's city, which glows as it arrives.
   Words: "Mom's normal morning happened."
4. 19 to 25 s. The kid's apartment at dawn; the phone on the table lights up with a calm, blank card.
   Words: "No call needed. Just a short note, twice a day."
5. 25 to 30 s. The green kettle centre screen, then "Kettle" and "heykettle.com" under it.
   Words: "For checking in, not checking up."

## Copy rules
Read `docs/kettle-brief-for-ai-writers.md`. Only the words above appear. Never: monitor, tracking,
alert, surveillance, elderly, senior, sensor, detect, dashboard. No em dashes.
