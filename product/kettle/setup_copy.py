"""Every string on the parent setup page (spec 005b).

One module, flat constants, because the page's copy is product law made
visible and it must be testable as text: the consent facts, the pre-empted
Apple warning, Run Immediately on every automation row, the kill switch. The
flat structure is also requirement §4.4's future — a family-language variant
is another module shaped exactly like this one, not a rewrite.

Copy discipline (QUESTIONS 106): nobody reads. One short paragraph per step,
speech bubbles over prose, and every screen answers "what do I tap next".

`{child}` is the family's owner display name, `{parent}` the monitored
person's, `{host}` the API host the Apple warning will really name. Rendering
escapes the values, never the templates.
"""

from __future__ import annotations

#: Apple's own store page for the Shortcuts app — step zero's one button
#: (QUESTIONS 103: the app may have been deleted; never assume it exists).
APP_STORE_SHORTCUTS_URL = "https://apps.apple.com/app/shortcuts/id915249334"

#: Signal keys that watch a browser. Empty until QUESTIONS 100 adds one
#: (`safari` is the candidate); the consent screen adds CONSENT_BROWSER
#: whenever a parent's active set intersects this. The sentence exists now
#: because requirement §4.5 says the copy structure must not preclude it —
#: people hear "browsing" even though we only ever see that an app opened.
BROWSER_SIGNALS: tuple[str, ...] = ()

HEADER_SUB = "From {child} · takes about 10 minutes"
HEADER_SUB_NO_CHILD = "Takes about 10 minutes"
PAGE_TITLE = "Kettle — {parent}'s setup"
HELPER_TOGGLE = "Helping someone?"

# --- consent (screen 1; spec §2.7 — carried by the product, not the call) ----

CONSENT_TITLE = "Before anything: what this is"
CONSENT_SAY = (
    "A tripwire, not a camera. When you open an app you use every day, your "
    'phone tells your family’s Kettle page: “a normal thing happened.” '
    "That’s all."
)
CONSENT_SENT_HEADING = "SENT — 3 THINGS"
#: The merged method stores `routine`, so "never which app" is literally true.
CONSENT_SENT_MERGED = (
    "Who · “a normal thing happened” · date & time. "
    "Never which app. Never what you did in it."
)
#: Per-app setups store the app's own key, and the consent says so plainly —
#: claiming "never which app" here would be a lie in the product's mouth.
CONSENT_SENT_PER_APP = (
    "Who · which app opened · date & time. "
    "Never what you did inside it."
)
CONSENT_BROWSER = (
    "One of the buttons watches the internet app. It only ever says the app "
    "opened — never what you read or searched."
)
CONSENT_NEVER_HEADING = "NEVER COLLECTED"
CONSENT_NEVER = "No messages. No calls. No location. No listening. Ever."
KILL_SWITCH = (
    "You are always in charge. Delete the automations in the Shortcuts app "
    "any time — everything stops instantly, and nobody has to be asked."
)
CONSENT_CTA = "I understand — let’s set it up"
CONSENT_STOP = (
    "Not comfortable? Stop here and tell your family. That’s a fine answer."
)
HELPER_NOTE_CONSENT = (
    "Helper: read this screen aloud before anything else, in the words you’d "
    "use at the kitchen table. If they’re not comfortable, stop — that’s a "
    "fine answer."
)

# --- step zero: the Shortcuts app (screen 2; QUESTIONS 103) ------------------

STEP_ZERO_TITLE = "Do you see this app on your phone?"
STEP_ZERO_CAP = (
    "Shortcuts — it comes with every iPhone, but it may have been removed."
)
STEP_ZERO_BUBBLE = (
    "Swipe down on your home screen and type Shortcuts. Found it? Great. "
    "Not there? Tap the button below to get it back — it’s free and made by "
    "Apple."
)
STEP_ZERO_STORE_CTA = "⬇ Get Shortcuts from the App Store"
STEP_ZERO_CTA = "I found it"

# --- add the buttons (screen 3; delivery is WhatsApp documents, Q117) --------

ADD_TITLE_TWO = "Add your two Kettle buttons"
ADD_TITLE_MANY = "Add your {count} Kettle buttons"
ADD_SAY = (
    "In WhatsApp, find the files {child} sent you. Tap each one, then tap "
    "Add Shortcut. That’s the whole step."
)
ADD_SAY_NO_CHILD = (
    "In WhatsApp, find the files your family sent you. Tap each one, then "
    "tap Add Shortcut. That’s the whole step."
)
ADD_CAP = "These are yours alone — they only work on this phone."
ADD_CTA = "I added them all"

# --- first run + the pre-empted warning (screen 4; QUESTIONS 92/99) ----------

FIRSTRUN_TITLE = "Now run each one once — and expect a warning"
FIRSTRUN_SAY = (
    "Open Shortcuts and tap each Kettle button once. Your phone will show "
    "something like this. It’s expected, and it’s safe — it’s just asking "
    "permission to reach your family’s Kettle page."
)
APPLEWARN_TITLE = "“{shortcut}” wants to connect to {host}"
APPLEWARN_BODY = "This shortcut will be allowed to send data to this server."
APPLEWARN_ALLOW = "Allow"
APPLEWARN_DENY = "Don’t Allow"
FIRSTRUN_CAP = "Tap Allow — once for each button."
FIRSTRUN_CTA = "Done — I ran each one and tapped Allow"
HELPER_NOTE_FIRSTRUN = (
    "\U0001f4f7 Helper: keep the camera on the phone screen for this step — "
    "this is the one where people stop."
)

# --- automations (screen 5; Run Immediately always, spec §2.5) ---------------

AUTO_TITLE = "Teach your phone when to use them"
AUTO_SAY = "One short line each — go slowly, there’s no timer."
#: Every row ends "… → Run Immediately → pick {shortcut}". The templates are
#: per signal key; a key must appear in exactly one of the three trigger
#: families below or rendering refuses (a silent default would invent an
#: instruction for a signal nobody thought about).
AUTO_ROW_ROUTINE = (
    "In Shortcuts, tap Automation → + → App. Pick all the apps "
    "{parent} opens every day (WhatsApp, YouTube…). Choose Is Opened and "
    "Run Immediately → pick {shortcut}."
)
AUTO_ROW_APP = (
    "Automation → + → App → {label} → Is Opened → "
    "Run Immediately → pick {shortcut}."
)
AUTO_ROW_CHARGER_BOTH = (
    "Automation → + → Charger. Tick both “Is Connected” and "
    "“Is Disconnected”. Choose Run Immediately → pick {shortcut}."
)
AUTO_ROW_CHARGE_ON = (
    "Automation → + → Charger → Is Connected → "
    "Run Immediately → pick {shortcut}."
)
AUTO_ROW_CHARGE_OFF = (
    "Automation → + → Charger → Is Disconnected → "
    "Run Immediately → pick {shortcut}."
)
AUTO_ROW_TIME_OF_DAY = (
    "Automation → + → Time of Day → pick a morning time, Daily "
    "→ Run Immediately → pick {shortcut}."
)
AUTO_HONESTY = (
    "Your phone may sometimes say “{count} automations ran.” That’s "
    "not an error — it’s your phone being honest about what it’s doing."
)
AUTO_CTA = "The automations are built"

# --- verify by prediction (screen 6; runbook §8, QUESTIONS 92) ---------------

VERIFY_TITLE = "The proof: watch it work"
VERIFY_SAY = "Open {app} right now, then come back here."
#: The merged routine automation watches apps chosen on the phone, so the page
#: names the near-universal one rather than pretending to know the list.
VERIFY_APP_ROUTINE = "WhatsApp — or any app you picked just now"
VERIFY_WAITING = "Waiting for the signal from your phone…"
VERIFY_CHECKING = "Watching…"
VERIFY_GREEN = "{parent}’s card just turned green. It works."
VERIFY_RETRY = "Still quiet. Open {app} once more, then give it a few seconds."
VERIFY_CROSSED = (
    "Nothing has arrived on {parent}’s card. If a different name’s card "
    "changed instead, stop here — two links may have been swapped. Check with "
    "{child} before going on."
)
VERIFY_CROSSED_NO_CHILD = (
    "Nothing has arrived on {parent}’s card. If a different name’s card "
    "changed instead, stop here — two links may have been swapped. Check with "
    "your family before going on."
)
VERIFY_BUTTON = "I opened {app}"
VERIFY_FINISH = "Finish"
VERIFY_LINK_DIED = (
    "This link stopped working mid-way. Ask {child} to send a fresh one."
)
#: A set with no alarm-grade signal has no card the verify step may honestly
#: promise: household- and device-grade signals never speak for a person
#: (product law #6), so there is no green check here to give.
VERIFY_NO_ROUTINE = (
    "This setup has no routine button, so there is no card to watch from "
    "here. Check with {child} that everything looks right on their side."
)

# --- done (screen 7) ---------------------------------------------------------

DONE_TITLE = "That’s everything, {parent} \U0001f389"
DONE_SAY = (
    "From now on, just live your day. Open your apps like always, charge "
    "your phone like always. Your family sees “all’s well” — nothing more."
)
DONE_SEES_HEADING = "WHAT YOUR FAMILY SEES"
DONE_SEES = "A green card that says your routine happened today."
DONE_NOT_HEADING = "WHAT THEY DON’T"
DONE_NOT = "Which apps. What you did. Where you are."
DONE_KILL = (
    "Change your mind any time: Shortcuts → Automation → delete the "
    "automations. It all stops, instantly."
)

# --- dead ends (spec acceptance 3: plain language, never a file) -------------

DEAD_EXPIRED_TITLE = "This link has expired"
DEAD_EXPIRED_BODY = (
    "Setup links only live for a week. Ask {child} to send a fresh one — it "
    "takes them a minute."
)
DEAD_REVOKED_TITLE = "This link has been replaced"
DEAD_REVOKED_BODY = (
    "A newer link exists for this setup. Ask {child} for the latest one."
)
DEAD_NO_CHILD = "your family"
DEAD_UNKNOWN_TITLE = "This isn’t a live setup link"
DEAD_UNKNOWN_BODY = (
    "Check with the person who sent it that you have the whole link, or ask "
    "them to send a fresh one."
)

HELPER_NOTE_GENERAL = (
    "\U0001f4f7 On a video call? Point the camera at the phone screen — "
    "seeing it is most of the help."
)
