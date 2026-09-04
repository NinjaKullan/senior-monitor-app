# Spec 014 — Android senior app (the phone's voice)

Status: APPROVED by Hema, 2026-09-04 (DECISIONS 258). Drafted 2026-09-03. Written from `docs/android-signals-brief.md`
option B, DECISIONS 100, 107, 108, 138, and spec 005b. Asana: W2 "Android senior
app + Xiaomi soak test" (1216997773231871). All three founder decisions from the
brief are taken (DECISIONS 257): §2 and §5.5. Not scheduled before Wave D sunset
+ Memory v1.1. Owned by the Android session, whose lane is specs/014-*, android/,
and new DECISIONS entries; everything in §6 belongs to the PM session.

## 1. What it is, and the law it lives under

A small Android app whose only job is to be the parent's phone's voice. It sends
the same kind of pings the iOS Shortcuts send, to the same route
(`/p/{device_token}/{signal}`), and does nothing else. The kid installs it and
connects it through the existing setup link; the parent is asked nothing, ever
after. Elder-proof here means invisible: no screen the parent needs, no question
the parent answers, no notification that asks for a tap.

Why it exists: an Android parent is today a phone Kettle never hears from. Every
morning reads as quiet, the ask fires daily, and the product's promise (the ask is
the exception) inverts. This is beta-gating: no Android-parent family can join
honestly until it ships (brief, "The gap").

Laws that bind it, unchanged from the rest of Kettle:

1. Three fields stored per ping (who, which signal, when). The app sends nothing
   else. The route ignores everything but the path and that stays true.
2. Content-free, what-never-how. The phone was unlocked, the charger went in or
   out, the phone moved. Never which apps, never where, never a count shown to
   anyone.
3. App-usage tracking is surveillance-shaped and stays out, whatever it would buy
   (brief, option B). `PACKAGE_USAGE_STATS` is never requested.
4. No location permission is requested, ever. The word "location" appears nowhere
   in the app, the Play listing, or any permission rationale.
5. Per-person consent with a visible kill switch. Consent is carried by the setup
   page's first screen as in 005b law 7; the kill switch is a real button on the
   app's one screen (§5.4) plus plain uninstall.
6. Corroborating signals never alarm on their own (law #6). Grade comes from the
   vocabulary, never from the sender.

## 2. Sequencing (founder decisions 1 and 2, 2026-09-03)

**Decision 1, adopted as written.** The brief's ordering stands. Item 1 of the
brief (phone-gone-silent surfacing in the kid app) has already shipped as
`STATE_UNREACHABLE` (DECISIONS 161/163, live-tested 243/254), so the sequence
that remains is: Wave D sunset, then Memory v1.1, then this spec, then
Android-parent beta families. Option A (MacroDroid, hand-held) stays in the back
pocket for a single pilot family that arrives before B ships; it is never the
product answer.

**Decision 2, wait.** The beta recruiting message stays iPhone-parent only until
this app ships. No promise is made that this month cannot keep. An Android-parent
family that asks joins the waitlist; `parent_phone` on the waitlist (DECISIONS
138) keeps deciding how loudly Android demand is calling. The message wording is
not changed by this spec.

**Decision 3** (name and strings) is ruled in §5.5.

## 3. Signals: the Android vocabulary

The iOS vocabulary is `routine` (habit apps opened, alarm-grade) and `charger`
(corroborating), with `device_alive` off the Shortcuts surface (DECISIONS 107).
DECISIONS 100 already said `STANDARD_SIGNALS` must become platform-aware, keyed
off `devices.platform`, which exists with values `ios_shortcuts` and `android`
(migration 0001). This spec cashes that in.

| key            | source on Android                                                | grade         | app-side cap             | kid-app label   |
|----------------|------------------------------------------------------------------|---------------|--------------------------|-----------------|
| `unlock`       | `ACTION_USER_PRESENT` (the phone was unlocked by a person); if the phone has no lock screen at all, `ACTION_SCREEN_ON` | alarm | one ping per 30 min | Phone unlocked |
| `charger`      | `ACTION_POWER_CONNECTED` / `ACTION_POWER_DISCONNECTED`            | corroborating | one ping per 60 s (server dedupe) | Charger  |
| `motion`       | step-counter delta > 0 since last read, or significant-motion trigger | corroborating | one ping per 60 min  | Phone moved     |
| `device_alive` | first successful worker run each local calendar day               | corroborating | one per day              | Daily Check     |

Rulings inside the table (the vocabulary ones are asked of the PM session in §9):

- **`unlock` is a new key, not `routine` overloaded.** The kid app labels a
  signal by key. "Daily routine" over an unlock event would be a label that lies,
  and `Not set up yet` never lies about a signal (DECISIONS 110). New key, honest
  label. `routine` stays iOS-only.
- **No lock screen is common on a parent's phone.** Swipe-to-unlock still fires
  `USER_PRESENT`; a lock set to None never does. The app checks
  `KeyguardManager.isDeviceSecure`/`isKeyguardLocked` at setup and each worker
  run and falls back to `SCREEN_ON` (the phone woke) when there is no keyguard.
  Same key, same grade; a screen that came on is still a person.
- **`unlock` is alarm-grade.** It is a deliberate human act on a personal device,
  the same class as opening WhatsApp. It is the Android answer to "which app do
  they open every day without thinking": every parent who uses the phone at all
  unlocks it. The 005b wizard's habit-apps question is therefore skipped for an
  Android parent (§6).
- **`motion` is corroborating and rate-limited to once an hour.** A signal, not a
  metric: the app never stores or sends a step count, only the fact that the
  delta was non-zero. Three independent voices where iOS has one (brief, motion
  section (a)).
- **`device_alive` finds its intended home** (DECISIONS 107): a daily heartbeat
  from a parent-side native app, honest on Android because background work is
  (DECISIONS 138, "the Android wave").

Server-side vocabulary change (built later, §6): `ALARM_GRADE` gains
`"unlock": True, "motion": False`; `SIGNAL_LABELS` gains the two labels above;
the default Android signal set at provisioning is `unlock, charger, motion,
device_alive`. Per-parent allowlist semantics are unchanged: the server still
answers 400 to a signal the parent is not provisioned for, and the app ignores
that answer.

## 4. The app: engineering posture

Kotlin, minimum SDK 26 (Android 8), target current. One activity (the setup
screen, §5.4), one foreground service, one periodic worker, three receivers. No
account, no analytics SDK, no crash reporter that phones home with content, no
third-party network library beyond what the platform ships.

**4.1 Foreground service, because that is what Android honestly requires.**
Since Android 8, `ACTION_POWER_CONNECTED`, `ACTION_POWER_DISCONNECTED` and
`ACTION_USER_PRESENT` cannot be received by a manifest-declared receiver; a
process must be alive and register them at runtime. A foreground service is the
only durable way to be that process. Its notification is the price: one line,
`MIN` importance, silent channel, no action buttons, collapses to nothing on most
launchers. Android 14+ requires a declared foreground service type; the honest
fit is `health` (the service reads the step sensor and holds
`ACTIVITY_RECOGNITION`); if Play review rejects that reading, `specialUse` with
the declaration text from §5.6. The implementer picks; the choice is recorded in
DECISIONS at build time.

**4.2 The belt: a periodic worker.** WorkManager, every 15 minutes (the platform
minimum), `requiresBatteryNotLow` off, no network constraint. Each run: restart
the service if the OEM killed it; read the step counter once (no continuous
listener) and emit `motion` if the delta since the last read is positive and the
hourly cap allows; emit `device_alive` if today has none; flush the retry queue
(4.4). `RECEIVE_BOOT_COMPLETED` restarts both after reboot. This is the layer the
Xiaomi soak test (§8) exists to prove.

**4.3 Permissions, all of them, at setup only.** `INTERNET`;
`FOREGROUND_SERVICE` (+ the typed variant); `RECEIVE_BOOT_COMPLETED`;
`ACTIVITY_RECOGNITION` (runtime dialog, for the step sensor);
`REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` (system dialog, once);
`POST_NOTIFICATIONS` on Android 13+ (needed so the service notification exists;
if the kid declines, the service still runs, the notification is simply hidden,
which is fine). Nothing else. No location, no usage stats, no contacts, no SMS.

**4.4 Network and honesty of timing.** A ping is one HTTPS GET to
`{api_base}/p/{token}/{signal}`, no body, no headers beyond a `User-Agent` of
`kettle-android/{version}`. If it fails, it retries with backoff for at most 60
minutes and is then dropped. A ping is never replayed later than that: the server
records arrival time, and a morning unlock delivered at dinner would say the
wrong thing about the morning. Late is dropped; the phone-gone-silent surfacing
already covers a phone that cannot reach the server.

**4.5 Token handling.** The device token arrives once at claim (§5.3), is stored
in `EncryptedSharedPreferences`, and is never displayed, logged, or exported. A
`403` from the server means revoked: the app stops the service, clears the
token, and shows the revoked state (§5.4). It never retries a revoked token.

**4.6 What the app never does.** Runs in the foreground for the parent. Shows a
dialog after setup. Reads the screen, notifications, apps, contacts, or
location. Sends a count. Updates itself outside Play. Speaks any language but
English (standing ruling).

## 5. Setup: the kid's path

The measured finding behind 005b holds here in reverse: on iOS the automation
builder is ~16 Apple-UI taps we cannot remove; on Android the app replaces all of
them. The target is ≤ 10 taps from opening the setup link to "Kettle heard it",
Play already installed on the phone.

**5.1 The wizard.** One new question per parent: "Which phone does Mom have?"
with two picture answers, iPhone and Android. Android skips the habit-apps
question and the per-app opt-in (both are iOS concepts) and provisions the
Android signal set. The setup link it emits is the same `/s/{slug}` link,
labelled the same way ("Mom's setup"), forwarded the same way (WhatsApp share).

**5.2 The setup page branches on platform.** For an Android device the page is:
consent (unchanged, 005b law 7) → **Install** (a Play button whose URL carries
the slug in the install referrer) → **Open Kettle** (an Android App Link on the
same setup URL, which opens the app directly when installed) → verify → done.
No shortcuts, no automations, no Files app, no warning to pre-empt. The page
never shows a token; the slug is the token in transit exactly as in 005b.

**5.3 Claim.** On first launch the app reads the slug from the Play Install
Referrer; if that is empty (sideload, or Play stripped it), the App Link supplies
it when the kid taps "Open Kettle" on the setup page. The app then calls
`POST /s/{slug}/claim` with `{platform: "android", app_version, sdk, oem}` and
receives `{device_token, api_base, signals}`. Claim works while the link is live
(7 days, revocable with the token, 005b §4.2); a claimed link stays claimable so
a reinstall on the same phone works without a new link; an expired or revoked
slug answers the same plain-language dead end the page shows. `oem` is stored on
the device row for the soak-test record and for the per-OEM step in 5.4, and
for nothing else.

**5.4 The one screen and its states.** One activity, one state at a time, one
full-width button per state, high contrast, and the app honours Android's
font-size setting all the way to its maximum without clipping (elder eyes;
tested at the largest setting as part of §8). Who reads it: per 005b the median
install is remote, so the reader is the parent holding the phone with the kid
narrating on a call. The strings are written for that reader. The parent, if
they ever open the app afterwards, sees only `ON`.

1. `NO_LINK` (opened from the launcher before setup): title, one line, no
   button.
2. `CONNECTING`: spinner, one line.
3. `PERMISSIONS`: one line and one button; the button fires the system dialogs
   in sequence (activity recognition, then battery). On OEMs with a known
   autostart or battery page (Xiaomi, Samsung, Oppo, OnePlus, Vivo, Huawei) a
   second button opens that page directly with one line of guidance. The guidance
   per OEM lives in a strings table the implementer fills from the soak test;
   each line is DECISIONS-recorded when written.
4. `VERIFY`: "lock it, unlock it". The app waits for its own `unlock` ping to be
   accepted (a 2xx), then flips to `HEARD`. This is verification by prediction
   exactly as 005b law 8: the alarm-grade signal, the permission grant and the
   crossed-files check in one step. The setup page shows the same green check.
5. `HEARD` → `ON`: the steady state. One line, and the kill switch: a text button
   that opens a two-button confirm. Confirming stops the service, clears the
   token, and shows `OFF`. The server sees silence and the kid sees unreachable;
   the kid revokes or re-provisions from the wizard as they would for an iPhone.
6. `REVOKED`: reached on a 403. One line, no button.
7. `OFF`: after the kill switch. One line, one button to reconnect, which needs a
   fresh setup link and says so.

**5.5 Name and strings, RULED (DECISIONS 257), VERBATIM.** Copy laws apply:
straight apostrophes, no em dashes, no "we", plain English. These are v1 and are
expected to change during the Xiaomi soak; every change is a new DECISIONS
entry.

App name (under the icon, in the Play listing): **Kettle**

Notification (persistent, silent): `NOTIFICATION = "Kettle is on"`

Screen strings:

- `BEFORE_SETUP = "Ask your family to send you the Kettle setup link, then open it on this phone."`
- `CONNECTING = "Connecting this phone to Kettle."`
- `PERMISSIONS = "Your phone will ask two questions. Tap Allow on both."` Button: `"Continue"`
- `RATIONALE_MOTION = "Kettle only notices that the phone moved today. It never knows where you are."`
- `RATIONALE_BATTERY = "This lets Kettle keep working every day."`
- `OEM_SETTING = "One more setting so this phone does not switch Kettle off."` Button: `"Show me"`
- `VERIFY = "Turn the screen off, then unlock the phone the way you usually do."`
- `HEARD = "Kettle heard it. This phone is connected. You can close this."`
- `ON = "Kettle is on. There is nothing you need to do."`
- `OFF_LINK = "Turn Kettle off"` (small, at the bottom of `ON`)
- `OFF_CONFIRM = "Turn Kettle off on this phone? Your family will stop hearing that your day has started."` Buttons: `"Turn off"` / `"Keep on"`
- `OFF = "Kettle is off on this phone."` Button: `"Reconnect"` Note: `"Ask your family for a new setup link."`
- `REVOKED = "Your family has turned Kettle off on this phone."`

Android's own dialogs (activity recognition, battery, notifications) are not
ours to write; `PERMISSIONS` pre-empts them the way 005b law 6 pre-empts Apple's
warning, by saying which button to tap.

**5.6 Play listing, draft (not parent-facing until the listing goes live; ruled then).** Title "Kettle". Short description: "For a
parent's phone. Kettle lets family know the day has started, without asking
anything of them." Full description and the data-safety form say exactly what
§1 says: three fields, no location, no app usage, no content. Foreground-service
declaration text (only if `specialUse` is needed): "Receives charger and unlock
system broadcasts to send a content-free daily signal to the user's family;
cannot function without a live process."

## 6. Needs the PM session (out of the Android session's lane)

The Android session edits only specs/014-*, android/, and new DECISIONS
entries. Everything below lives in product/ or webapp/ and is flagged, not made.
Until items 1 to 4 exist the app can still be built and soak-tested: the ping
route accepts any client today, a rehearsal parent is provisioned with the
existing keys (`routine` stands in for `unlock` during the soak only), and the
token reaches the phone by founder hand in a debug build.

1. `product/kettle/signals.py`: `ALARM_GRADE` and `SIGNAL_LABELS` gain `unlock`
   and `motion`; a `PLATFORM_SIGNALS` map replaces the single `STANDARD_SIGNALS`
   default (DECISIONS 100), `ios_shortcuts` unchanged, `android` = `unlock,
   charger, motion, device_alive`. Pinned test: no key is alarm-grade on one
   platform and corroborating on another.
2. `provisioning.py` / `scripts/provision.py`: `--platform android` selects the
   Android default set; `--signals` still overrides; grade still never
   caller-supplied (DECISIONS 110).
3. `setup_page.py`: platform branch (§5.2) with a step zero before the Play
   button, in 005b's "do you see this icon" shape: "Does the Play Store open on
   this phone?" A parent's phone is often set up by someone else and Play asks
   for a Google password nobody remembers; the kid's recovery path goes here.
   `verify_app_label` for Android is the unlock instruction, not an app name;
   Play URL with install referrer; App Link association file served at
   `/.well-known/assetlinks.json` on the setup host.
4. New route `POST /s/{slug}/claim` (§5.3), rate-limited per slug, logged like a
   setup-link resolve, 403/410 semantics identical to the page.
5. `db.py` / migration: `devices.oem text null`, `devices.app_version text
   null`, written at claim, read by nothing in the product. No new ping fields.
6. Webapp: the wizard's phone question (§5.1); the two new labels; nothing else.
   `STATE_UNREACHABLE` already covers the silent-phone case on both platforms.
7. Runbook: an Android install section, written from the first real install, in
   the same shape as the Amma log.

## 7. Privacy (binding)

- Three fields per ping, forever. `oem` and `app_version` live on the device
  row, not on pings, and exist for the soak-test record only.
- Never a count. The app compares step readings and discards them. No number
  leaves the phone.
- Never a location permission, never the word. Acceptance §8.6 audits this.
- Never app usage. `PACKAGE_USAGE_STATS` is not in the manifest; acceptance
  §8.6 audits this too.
- Consent lives in the product: the setup page's first screen and the kill
  switch on the app's screen. No form, no signature, no one-pager (standing
  ruling).
- Household signals never speak for a person: the app is on one phone for one
  parent; a shared tablet is not a supported install.

## 8. Acceptance criteria

1. **Xiaomi soak test, the gate.** On a Xiaomi phone running current MIUI or
   HyperOS with factory defaults, after the one-time setup in §5 and no further
   human touch: `unlock`, `charger`, `motion` and `device_alive` each arrive on
   every one of 7 consecutive days. Same pass on one Samsung. A phone the OEM
   battery manager force-stops recovers within 30 minutes with nobody touching it.
   The soak log is the artifact and lands in DECISIONS.
2. **Tap count.** ≤ 10 taps from opening the setup link to `HEARD`, Play already
   on the phone, enumerated honestly in a test script in the shape of
   `docs/005b-test-script.md`. Per-OEM extra settings are counted when the phone
   needs them.
3. **Crossed pair.** Swap two rehearsal setup links; the named-card check on the
   setup page fails loudly (005b §5.4 holds).
4. **Revoke.** `--revoke` on the token: the app reaches `REVOKED` within one
   worker cycle and sends nothing afterwards.
5. **Kill switch.** The parent-side "Turn off" needs a confirm; no single tap on
   the screen costs the family coverage.
6. **String and manifest audit.** "location" appears nowhere in the app, the
   listing, or the rationales; `PACKAGE_USAGE_STATS` and every location
   permission are absent from the manifest. Pinned by a test over the strings
   file and the merged manifest.
7. **Quiet.** A week of pings is under 1 MB of data and the app is never in the
   phone's top battery consumers.
8. **Late pings dropped.** Airplane mode for two hours over an unlock; nothing is
   delivered afterwards for that unlock.
9. **Large text.** Every state of the screen is readable and un-clipped at
   Android's maximum font size.
10. **Field note.** The first stranger Android family's install produces a
    numbered DECISIONS block, same as the founder's own.

## 9. Rulings still open

1. `unlock` as a new alarm-grade key with label "Phone unlocked" (not `routine`
   overloaded), and `motion` corroborating, once an hour, label "Phone moved".
   Vocabulary is the PM session's; this spec asks, it does not rule.
2. The 60-minute drop rule for undelivered pings (§4.4).
3. Play distribution for the first beta families. Google requires a new
   personal developer account to run a closed test (12 opted-in testers, 14
   days, under the policy as of late 2023; verify at account creation) before a
   production listing. Until production access exists the soak test and the
   first families run from the internal-testing track, which needs the parent's
   Google account added by email, or from a sideloaded build the kid installs
   hand-held. Recommendation: open the $25 account at spec approval so the
   clock runs during the Memory v1.1 build; internal track for the soak; no
   stranger family before the production listing.

## 10. Out of scope, recorded so it stays out

- **An iOS senior app.** A named future option (HealthKit background delivery as
  a supplementary voice, never a replacement for Shortcuts); not a v1 need
  (brief, motion section (b)).
- **Timezone from the phone.** DECISIONS 108's idea (a ping carries tz, the
  server notices drift and prompts the kid) is the right long-term answer and
  the app is the right sender. Not built here: the route ignores everything but
  the path and timezone is member configuration, not a ping field. Follow-up
  spec once spec 010's city picker has lived with a travelling parent.
- **Option A (MacroDroid).** Back pocket for one hand-held pilot family; never a
  documented path.
- **Option D (ask-anchored coverage).** Only after the kids-own-the-ask spec
  lands (the brief calls it 013; that number has since gone to email-code
  sign-in, so it is unnumbered here) and only as a family's explicit choice,
  never a silent default.
- **Per-app signals on Android.** App usage stays out, whatever it would buy.
- **Shared devices, tablets, Wear, a widget, any parent-facing feature.**
