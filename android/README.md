# Kettle for Android (spec 014)

The parent's phone's voice. It sends the same content-free pings the iPhone
Shortcuts send, to the same route, and does nothing else. Read
`specs/014-android-senior-app.md` for what it is and why; this file is only
how to build it and put it on a phone.

What is in here:

| Path | What |
|---|---|
| `app/src/main/kotlin/.../MainActivity.kt` | The one screen and its states (§5.4) |
| `app/src/main/kotlin/.../KettleService.kt` | The foreground service that hears unlock and charger (§4.1) |
| `app/src/main/kotlin/.../HeartbeatWorker.kt` | The 15-minute worker: restart, motion, device_alive, retry (§4.2) |
| `app/src/main/kotlin/.../Sender.kt`, `RetryQueue.kt` | Caps, one attempt, the 60-minute drop rule (§4.4) |
| `app/src/main/kotlin/.../OemSettings.kt` | The "Show me" table for Xiaomi, Samsung, Oppo, OnePlus, Vivo, Huawei |
| `app/src/main/res/values/strings.xml` | Every parent-facing string, verbatim from DECISIONS 257 |
| `app/src/test/kotlin/...` | Tests: strings pin, manifest audit, retry queue, caps |
| `app/src/debug/kotlin/.../DebugSetup.kt` | Debug-only token entry; not in release builds |
| `SOAK.md` | The §8 acceptance checklist and the 7-day soak log |

## 1. Install Android Studio

1. Download Android Studio from https://developer.android.com/studio and run the installer. Accept the defaults; it installs the Android SDK for you.
2. Open it once and let it finish "Downloading components". This takes a few minutes.

## 2. Open this folder

1. In Android Studio choose **Open** and pick the `android/` folder (this folder, not the repo root).
2. Wait for "Gradle sync" at the bottom to finish. The first sync downloads about a gigabyte. If it asks to install an SDK platform or build tools, say yes.
3. If sync fails with a message about a missing SDK, open **File > Settings > Languages & Frameworks > Android SDK** and install "Android 15 (API 35)".

## 3. Build the debug APK

1. **Build > Build App Bundle(s) / APK(s) > Build APK(s)**.
2. When the "APK(s) generated" popup appears, click **locate**. The file is `app/build/outputs/apk/debug/app-debug.apk`.

Or from a terminal inside the `android/` folder:

```
./gradlew assembleDebug
```

To run the tests and the manifest audit:

```
./gradlew check
```

## 4. Put the phone in developer mode

On the parent's phone:

1. **Settings > About phone**. Tap **Build number** seven times (on Xiaomi it is under **About phone > MIUI version** or **OS version**; on Samsung under **About phone > Software information > Build number**). The phone says you are now a developer.
2. **Settings > System > Developer options** (Xiaomi: **Additional settings > Developer options**). Turn on **USB debugging**. On Xiaomi also turn on **Install via USB** and **USB debugging (Security settings)**; it may ask you to sign in to a Mi account for those.
3. Plug the phone into the computer with a USB cable. When the phone asks "Allow USB debugging?", tick **Always allow** and tap **Allow**.

## 5. Install with adb

`adb` was installed with Android Studio, in `~/Library/Android/sdk/platform-tools` on a Mac or `%LOCALAPPDATA%\Android\Sdk\platform-tools` on Windows. From that folder, or with it on your PATH:

```
adb devices
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

`adb devices` should list the phone as `device`. If it says `unauthorized`, look at the phone and tap Allow. Android Studio's green **Run** button does the same install if the phone is selected in the device dropdown.

## 6. Enter the token (debug builds only)

The setup link and claim route do not exist yet (spec 014 §6), so the token goes in by hand:

1. Provision a rehearsal parent on the server with `--platform android` is not built yet; for now provision with the existing keys and note the device token it prints. `routine` stands in for `unlock` during the soak (spec 014 §9.1).
2. Open **Kettle** on the phone. It shows "Ask your family to send you the Kettle setup link...".
3. **Long-press the word "Kettle" at the top.** A box appears with two fields: api base (already `https://kettle-api.fly.dev`) and token. Paste the token, tap **Connect**.
4. The screen says "Your phone will ask two questions. Tap Allow on both." Tap **Continue**. Allow physical activity, allow notifications, then on the battery dialog tap **Allow**.
5. On a Xiaomi or Samsung there is a second button, **Show me**. Tap it and turn on autostart (Xiaomi) or set the app to Unrestricted (Samsung), then go back.

Release builds do not contain the long-press; there is no way to enter a token in one until the claim route ships.

## 7. Verify

1. The screen now says "Turn the screen off, then unlock the phone the way you usually do." Do that.
2. Within a few seconds it says "Kettle heard it. This phone is connected. You can close this." That was the app's own unlock ping being accepted by the server.
3. On the server side, check the ping arrived (the founder's ntfy or the family app for the rehearsal parent).
4. Start `SOAK.md`.

## Useful adb commands during the soak

```
adb logcat -s Kettle:* AndroidRuntime:E      # nothing is logged by design; errors would show here
adb shell dumpsys activity services com.heykettle.android.debug   # is the service alive?
adb shell cmd jobscheduler run -f com.heykettle.android.debug 0   # not the worker; use the next line
adb shell am broadcast -a android.intent.action.BOOT_COMPLETED -p com.heykettle.android.debug
```

To force the worker early, open the app in Android Studio's **App Inspection > Background Task Inspector** and run `kettle-heartbeat`.

## What the app never does

No location permission, no usage stats, no analytics, no crash reporter, no third-party libraries beyond AndroidX and WorkManager. A test fails the build if any of that changes (`app/src/test/.../ManifestAuditTest.kt` and the `auditDebugManifest` / `auditReleaseManifest` Gradle tasks).
