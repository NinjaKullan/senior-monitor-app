# Kettle resource finder

Followed by the scheduled Claude task "Kettle useful resources" every other Monday (odd
ISO weeks). Standalone: assume no memory of any earlier conversation. It finds five
services, programs or tools that help families with a parent who lives on their own, and
hands Hema ready-to-post lines. Hema decides what to post; nothing here publishes.

## 0. Ground rules

- Read `docs/kettle-brief-for-ai-writers.md`. The lines written for posting follow it
  (banned words, no verdicts, straight apostrophes, no em dashes, no invented numbers).
  The searching itself may use any words ("elderly", "caregiver", "seniors").
- US resources first (standing founder ruling); a national or state-run program beats a
  local one; free beats paid; a public body, non-profit, library or utility beats a
  company. Never a product that competes with Kettle (check-in apps, sensors, cameras,
  medical alert devices). Never anything medical or diagnostic.
- Never `git commit` to main. Never post anything.
- Model economy: delegate the searching and link checks to a sonnet subagent; keep the
  choice of the five and the wording in the main session.

## 1. Get the files and the memory

`git clone https://github.com/NinjaKullan/senior-monitor-app`. Then `git fetch origin
social-drafts` and read every `social/resources/*/resources.json` on that branch (past
picks: do not repeat one), plus `docs/adult_children_aging_parent_resource_research.md`
and `docs/aging_in_place_free_resources_strategy.md` (things already known; prefer new
ones, but a known one may be included once if it has a clear reason now).

## 2. Search

Run 8 to 12 WebSearch queries across these lanes and keep a longlist of 12 or more:
government programs (Medicare and benefits deadlines, Area Agencies on Aging, Eldercare
Locator, state property-tax or utility relief, SHIP counselling, LIHEAP), free or
low-cost services (library home delivery and tech help, meal programs, transport and
paratransit, friendly-call programs, mail-hold and package options), practical tools for
families (shared calendars, medication list templates from public bodies, document
checklists, power of attorney explainers from bar associations), and timely items (open
enrollment windows, tax-season help, weather-season programs).

## 3. Vet

For each candidate on the shortlist, WebFetch the page and confirm: it is live, it says
what the resource does, who qualifies, and what it costs. Keep the exact URL that loaded.
Drop anything that fails to load, is a listicle rather than the service itself, is
behind a paywall or an email wall, or is a competitor. Pick the five most useful,
varied across the lanes, at least one with a date attached ("why now").

## 4. Write

For each of the five write, obeying the brief:
- `name`, `url`, `what` (one sentence), `who` (one sentence), `cost`, `why_now` (one
  sentence, may be "evergreen"), `lane`.
- `pin_title` (under 60 characters), `pin_description` (two or three plain sentences, no
  CTA, the link is the destination).
- `x_line` (under 240 characters including the URL, no hashtag).
Then `roundup_md`: a 250 to 400 word blog roundup "Five useful things this fortnight" in
the voice of `docs/blog-post-1-draft.md` (plain, warm, no em dashes, Kettle mentioned only
in the last line if at all), listing the five with links.
Run the brief's self-check on every line. No Kettle CTA anywhere in this deliverable.

## 5. Package and deliver

1. Write `social/resources/<YYYY-MM-DD>/resources.json`:
   `{"date": "...", "items": [ {fields above} ], "roundup_md": "..."}`
2. `python3 tools/social/build_resources.py social/resources/<YYYY-MM-DD>`
3. Publish `index.html` with the Artifact tool, title `Kettle resources <YYYY-MM-DD>`,
   favicon 🔗. Send `resources.json` and `roundup.md` with SendUserFile.
4. Commit `social/resources/<date>/` on branch `social-drafts` (create from `origin/main`
   if missing, otherwise check out and rebase on `origin/main`) and push that branch.
5. Final message, under 150 words: the five names with one line each and the URL, which
   one has a date attached, and anything you could not verify.
