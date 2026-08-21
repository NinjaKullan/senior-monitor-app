# 005b — setup page copy deck

*PM: Fable, 2026-08-16. Every string the parent setup page shows, keyed for implementation.
Register per DECISIONS 106: one visual + one short paragraph per screen, speech bubbles over
prose, no alarm vocabulary anywhere (the copy-law test should extend to every key here).
`{parent}` = display name ("Appa"), `{child}` = the child's name ("Hema"), `{apps}` = the
chosen habit apps. Helper mode (DECISIONS 104) adds the `helper_` strings; it never replaces
the parent-facing ones. The page never says "error", "fail", "warning", or "wrong".*

## Screen 0 — consent

- `consent_title` — **Before anything: what this is**
- `consent_body` — A tripwire, not a camera. When you open an app you use every day, your
  phone tells your family's Kettle page one thing: "a normal thing happened." That's all.
- `consent_sent_label` — SENT — 3 THINGS
- `consent_sent_body` — Who · "routine" · date & time. Never which app. Never what you did.
- `consent_never_label` — NEVER COLLECTED
- `consent_never_body` — No messages. No calls. No location. No listening. Ever.
- `consent_kill` — You are always in charge. Delete the automations in the Shortcuts app any
  time — everything stops instantly, and nobody has to be asked.
- `consent_cta` — I understand — let's set it up
- `consent_decline` — Not comfortable? Stop here and tell {child}. That's a fine answer.
- `helper_consent` — Read this screen out loud to {parent}, in the language you two actually
  speak. Then ask them to tell you what they think it does. If they're uneasy, stop — really.

## Screen 1 — step zero: the Shortcuts app (DECISIONS 103)

- `shortcuts_title` — Do you see this app on your phone?
- `shortcuts_body` — Swipe down on your home screen and type **Shortcuts**. It comes with
  every iPhone, but it may have been removed.
- `shortcuts_found_cta` — I found it
- `shortcuts_missing_cta` — ⬇ Get Shortcuts from the App Store — it's free, made by Apple
- `helper_shortcuts` — If it needs installing, this is the hardest step of the day. Camera on
  the screen, and go one tap at a time.

## Screen 2 — add the buttons

- `add_title` — Add your two Kettle buttons
- `add_body` — {child} sent them to you on WhatsApp. Tap each one, then tap **Add Shortcut**.
  That's the whole step.
- `add_tile_routine` — Kettle — Daily routine
- `add_tile_charger` — Kettle — Charger
- `add_caption` — These are yours alone — they only work on this phone.
- `add_cta` — I added both
- `helper_add` — Send one person's files only, from that person's chat. Two files, two taps
  each.

## Screen 3 — first run, and the message your phone will show (DECISIONS 92/99)

- `firstrun_title` — Now run each one once — and expect a question
- `firstrun_body` — Open Shortcuts, tap **Kettle — Daily routine**. Your phone will ask
  something like this. It's expected, and it's safe — it's your phone checking that *you*
  approve before it ever talks to your family's page.
- `firstrun_prompt_replica` — *(render Apple's dialog verbatim, Allow highlighted)*
- `firstrun_caption` — Tap **Allow**. Then the same for **Kettle — Charger**.
- `firstrun_cta` — Done — I ran both and tapped Allow
- `helper_firstrun` — The phone must be unlocked for this. If {parent} hesitates at the
  question, that's normal — it's worded sternly. It is safe, and you can say so.

## Screen 4 — the automations

- `auto_title` — Teach your phone when to use them
- `auto_step1` — In Shortcuts, tap **Automation** → **+** → **App**. Pick all the apps you
  open every day ({apps}). Choose **Is Opened** and **Run Immediately** → pick
  **Kettle — Daily routine**.
- `auto_step2` — Again: **+** → **Charger**. Tick **both** "Is Connected" and
  "Is Disconnected". Choose **Run Immediately** → pick **Kettle — Charger**.
- `auto_notice` — Your phone may sometimes say "2 automations ran." That's not a problem —
  it's your phone being honest about what it's doing.
- `auto_cta` — Both automations are built
- `helper_auto` — Two things people miss: **Run Immediately** (not "Run After Confirmation" —
  that one asks permission at every plug-in and never gets tapped), and picking the Kettle
  button at the end of each.

## Screen 5 — verify by prediction (DECISIONS 92, runbook §8)

- `verify_title` — The proof: watch it work
- `verify_body` — Open **WhatsApp** right now, then come back here.
- `verify_waiting` — Waiting for your phone's first signal…
- `verify_green` — {parent}'s card just turned green. It works.
- `verify_cta` — I opened WhatsApp
- `verify_next` — Finish
- `verify_stuck_body` — Nothing yet — that's usually the first run from the last step. Open
  Shortcuts, tap **Kettle — Daily routine** once, tap Allow if asked, then try again.
- `helper_verify` — Say out loud which card should change *before* they open the app. If a
  different person's card changes, stop and tell {child} — ten seconds now saves a month.

## Screen 6 — done

- `done_title` — That's everything, {parent} 🎉
- `done_body` — From now on, just live your day. Open your apps like always, charge your
  phone like always. Your family sees "all's well" — nothing more.
- `done_sees_label` — WHAT YOUR FAMILY SEES
- `done_sees_body` — A green card that says your routine happened today.
- `done_not_label` — WHAT THEY DON'T
- `done_not_body` — Which apps. What you did. Where you are.
- `done_kill` — Change your mind any time: Shortcuts → Automation → delete both. It all
  stops, instantly.

## Dead ends (requirement §4.3 — never a file, never a shrug)

- `expired_title` — This link has done its job
- `expired_body` — Setup links only live for a little while. Ask {child} to send a fresh
  one — it takes them a minute.
- `revoked_title` — This link was turned off
- `revoked_body` — {child} can send a new one if that's a surprise.

## Global

- `helper_toggle` — Helping someone?
- `helper_banner` — 📷 On a video call? Point the camera at {parent}'s phone — seeing the
  screen is most of the help.
- `progress_labels` — Consent · Shortcuts app · Add · First run · Automations · Verify · Done
