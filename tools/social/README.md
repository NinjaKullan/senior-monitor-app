# tools/social

The free weekly social pipeline. A scheduled Claude task follows `weekly-task.md` every
Monday: it drafts the week's X, Pinterest and TikTok posts, draws a cartoon strip for
each with `make_strip.py`, and builds one phone page with `build_week.py`. Hema reads the
page and posts by hand. Nothing here publishes anywhere.

- `characters.md`: the cast (Sam, June, the kettle) and style bible. Change the strips by
  editing this file.
- `characters/`: the adopted character sheet PNG(s). Every strip is drawn from these.
- `make_strip.py`: Gemini image call. No key in code: the Claude cloud environment
  "CC-cloud" holds it as an API credential (host `generativelanguage.googleapis.com`,
  header `x-goog-api-key`). For a local run, `export GEMINI_API_KEY=...`.
- `build_week.py`: `social/weeks/<week>/posts.json` + PNGs -> `index.html`.
- `weekly-task.md`: what the scheduled task does, plus the two role prompts.

Outputs live in `social/weeks/<ISO week>/`. Committing them is optional; the task reads
the last two weeks, when present, to avoid repeating a theme.
