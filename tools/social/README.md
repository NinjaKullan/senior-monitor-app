# tools/social

The free weekly social pipeline. A scheduled Claude task follows `weekly-task.md` every
Monday: it drafts the week's X, Pinterest and TikTok posts, draws a cartoon strip for
each with `make_strip.py`, and builds one phone page with `build_week.py`. Hema reads the
page and posts by hand. Nothing here publishes anywhere.

- `characters.md`: the style bible and two casts. Cast A (Sam, June) draws even ISO weeks,
  cast B (Dana, Walt) odd weeks. Change the strips by editing this file.
- `characters/`: one adopted character sheet per cast (`sheet-a.png`, `sheet-b.png`).
- `fonts/`: Patrick Hand (SIL Open Font License) for the lettering.
- `make_strip.py`: draws each panel with Gemini (no text), then letters bubbles, captions
  and the signature itself with Pillow, so the words are always exact. No key in code: the Claude cloud environment
  "CC-cloud" holds it as an API credential (host `generativelanguage.googleapis.com`,
  header `x-goog-api-key`). For a local run, `export GEMINI_API_KEY=...`.
- `build_week.py`: `social/weeks/<week>/posts.json` + PNGs -> `index.html`.
- `weekly-task.md`: what the scheduled task does, plus the two role prompts.

Outputs live in `social/weeks/<ISO week>/`. Committing them is optional; the task reads
the last two weeks, when present, to avoid repeating a theme.

- `resources-task.md` + `build_resources.py`: the fortnightly "Kettle useful resources" routine
  (odd ISO weeks): five vetted services or programs for families, with ready Pinterest and X
  lines and a blog roundup. Outputs in `social/resources/<date>/` on the `social-drafts` branch.
