# Kettle explainer video: brief

## Done means
- `out/kettle-explainer.mp4` exists: 1080x1920, 30 fps, H.264, yuv420p, no audio, 28 to 32 seconds.
- It plays the five scenes below in order, with exactly the on-screen words below and nothing else.
- `out/still-1.png`, `out/still-3.png`, `out/still-5.png` exist (one frame from scenes 1, 3, 5).
- `npm run render` (inside this folder) rebuilds all of the above from scratch, same result every time.
- Source committed on branch `video-explainer` and pushed. Nothing outside `marketing/explainer-video/`
  changed except one line in the root `.gitignore` for `marketing/explainer-video/out/` and `node_modules/`.

## What it is
One `index.html` + JS. Every shape drawn in code on a canvas: no image files, no AI images, no stock,
no icon fonts. Frame N is a pure function of N (no Math.random without a fixed seed, no wall clock),
so rendering is repeatable. Render by stepping frames headless and encoding with ffmpeg.

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
  a plain lit rectangle.
- Hospital, medicine, pills, walkers, alarms, sirens, warning triangles, exclamation marks.
- The mother looking frail, confused, sad or waiting at a window. She is busy and capable.
- Text touching a figure's face, text cut off at the edge, two text lines overlapping.
- Any logo other than the word "Kettle".

## Characters (paper figures)
- SAM: adult son, about 45. Short dark hair, round glasses, cream crew-neck sweater.
- MOM: about 74. Short silver hair, reading glasses pushed up on her head, green cardigan over a collared shirt.
- THE KETTLE: small stovetop kettle in Kettle green, curved spout, black handle. Never has a face.

## Story (on-screen words exactly as written, straight apostrophes)
1. 0 to 6 s. Night, dark blue-green paper sky. Sam at a table, far away, looking at his phone.
   Words: "Is Mom's day starting okay?"
2. 6 to 12 s. A simple paper map; the camera slides from Sam's side to Mom's house as morning light
   comes up there. Inside, the kettle lets out a little steam; Mom's phone glows in her hand. No words.
3. 12 to 19 s. A small folded paper note travels along a dotted line across the map to Sam's phone.
   Words: "Mom's normal morning happened."
4. 19 to 25 s. Sam sets the phone down and smiles.
   Words: "No call needed. Just a short note, twice a day."
5. 25 to 30 s. The green kettle centre screen, then "Kettle" and "heykettle.com" under it.
   Words: "For checking in, not checking up."

## Copy rules
Read `docs/kettle-brief-for-ai-writers.md`. Only the words above appear. Never: monitor, tracking,
alert, surveillance, elderly, senior, sensor, detect, dashboard. No em dashes.
