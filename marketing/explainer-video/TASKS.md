# Explainer video: tasks

- [x] Branch `video-explainer`; `package.json` with pinned `puppeteer-core`
- [x] `index.html`: paper-cutout scenes 1 to 5, seeded tears and grain, words guard (size, width, safe zone)
- [x] `render.mjs`: headless Chrome frames piped to ffmpeg; stills at 4 s, 15.5 s, 29 s
- [x] Render; check stills and every-2-second frames against "Do not produce" and story timings; fix; re-render
      (fixed: Sam's arm, muddy dim phone screen, cardigan below counter, kettle spout and handle,
      road through caption, caption widows, window popping to yellow, empty paper beat at 25 s)
- [x] Verify: 1080x1920, 30 fps, H.264, yuv420p, one stream, 900 frames, 30.0 s; two renders byte-identical
- [x] Self-review as a blocking merge review; fixed: failed frame left a short valid-looking MP4
- [x] `.gitignore`: nothing to add, root already ignores `out/` and `node_modules/` tree-wide
- [x] Commit (animation) and commit (render script, TASKS.md); push branch

## Render
    cd marketing/explainer-video && npm install && npm run render
Needs Google Chrome (or `CHROME=/path/to/chrome`) and `ffmpeg` on PATH. Output in `out/`.

## Open interpretations for Hema
- Scene 5 shows "Kettle", "heykettle.com" and the tagline together (brief lists all three under scene 5).
- Sweater and house walls use a cream (#EFE6D6) one step off paper so they read as separate cut pieces.
