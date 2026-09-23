# Explainer video: tasks

## v1 (code-drawn figures) — superseded
- [x] Paper-cutout scenes, render pipeline, byte-identical renders. Figures judged creepy; replaced below.

## v2: "Two houses, one light" (no people)
- [x] BRIEF.md: picture descriptions rewritten for the no-faces story; words unchanged; do-not-produce
      adds no faces or bodies, no lonely darkness, no text in backdrops
- [x] `paint.mjs`: Gemini call pattern from tools/social/make_strip.py (3.1-flash-image, fallback
      2.5-flash-image, x-goog-api-key, shared daily cap); prompts read from `assets/PROMPTS.md`
- [x] Backdrops painted once, best picked, 1080x1920 PNG in `assets/`: apartment-night, apartment-dawn,
      mom-house, kitchen, map (9 Gemini calls, 5 used; rejects in ignored `candidates/`)
- [x] `index.html`: code draws only what moves (kitchen light, glow, steam, dotted path and warm light,
      phones lighting, blank card, words); figures and map drawing removed
- [x] Review stills and every-2-second frames; fixed captions touching the curtain rod, invisible steam,
      path ending inside the building, dark phone reading as an empty frame, olive mid-fade kitchen phone
- [x] 1080x1920, 30 fps, H.264, yuv420p, one stream, 900 frames, 30.0 s; two renders byte-identical
- [x] Commit and push `video-explainer`

## v3: painted end-card kettle
- [x] `assets/kettle.png`: Gemini paper-cutout of the X avatar kettle (2 calls, 1 kept), paper keyed to
      transparent; prompt in PROMPTS.md. Scene 5 draws it; steam stays in code from the spout tip
- [x] still-5 checked; two renders byte-identical; pushed

## Render
    cd marketing/explainer-video && npm install && npm run render
Needs Google Chrome (or `CHROME=/path/to/chrome`) and `ffmpeg`. Output in `out/`. Never calls Gemini.
Repaint a backdrop: `GEMINI_API_KEY=... node paint.mjs <name> [ref.png]`, then pick from `candidates/`.
