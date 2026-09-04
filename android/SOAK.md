# Spec 014 §8 acceptance: checklist and soak log

Fill this in on the phones, then copy the result into a DECISIONS entry (§8.1
says the soak log is the artifact). Two phones: the Xiaomi (MIUI or HyperOS,
factory defaults) and the Samsung. Debug build, token entered by hand, the
rehearsal parent provisioned with `routine`, `charger`, `motion`, `device_alive`
(server-side `motion` does not exist yet, so expect 400 on it until spec 014 §6
item 1 lands; the app ignores 400).

## Before day 1

- [ ] Rehearsal parent provisioned; token entered on the Xiaomi
- [ ] Rehearsal parent provisioned; token entered on the Samsung
- [ ] Both phones reached HEARD (the verify step)
- [ ] "Show me" done on both: Xiaomi autostart on, Samsung battery Unrestricted
- [ ] Both phones on a normal daily charge routine, nobody touching the app again

## Acceptance checklist (§8)

| # | Test | Xiaomi | Samsung | Notes |
|---|---|---|---|---|
| 8.1 | 7 consecutive days: unlock, charger, motion, device_alive each arrive every day (table below) | [ ] | [ ] | |
| 8.1 | Force-stop the app from the OEM battery manager; it recovers within 30 min untouched | [ ] | [ ] | time to recover: |
| 8.2 | Tap count, setup link to HEARD, ≤ 10 (needs the claim route; count the debug path for now and note it) | [ ] | [ ] | taps: |
| 8.3 | Crossed pair: two rehearsal links swapped, setup page fails loudly (needs the Android setup page, §6 item 3) | [ ] | [ ] | blocked on §6 |
| 8.4 | `--revoke` the token: REVOKED within one worker cycle, nothing sent afterwards | [ ] | [ ] | |
| 8.5 | Kill switch: "Turn Kettle off" needs the confirm; "Keep on" changes nothing | [ ] | [ ] | |
| 8.6 | `./gradlew check` passes (strings pin, manifest audit, merged-manifest audit) | [ ] | n/a | |
| 8.7 | Quiet: a week under 1 MB data; not in the phone's top battery consumers | [ ] | [ ] | data used: |
| 8.8 | Late pings dropped: airplane mode 2 hours over an unlock; nothing delivered for it afterwards | [ ] | [ ] | |
| 8.9 | Largest font size: every state readable and un-clipped (BEFORE_SETUP, PERMISSIONS, VERIFY, HEARD, ON, the confirm, OFF, REVOKED) | [ ] | [ ] | |
| 8.10 | First stranger family's install produces a DECISIONS block | [ ] | [ ] | later |

## Xiaomi, 7-day log

Model and OS version: ____________________

| Date | unlock | charger | motion | device_alive | Notes |
|---|---|---|---|---|---|
| Day 1 | | | | | |
| Day 2 | | | | | |
| Day 3 | | | | | |
| Day 4 | | | | | |
| Day 5 | | | | | |
| Day 6 | | | | | |
| Day 7 | | | | | |

## Samsung, 7-day log

Model and OS version: ____________________

| Date | unlock | charger | motion | device_alive | Notes |
|---|---|---|---|---|---|
| Day 1 | | | | | |
| Day 2 | | | | | |
| Day 3 | | | | | |
| Day 4 | | | | | |
| Day 5 | | | | | |
| Day 6 | | | | | |
| Day 7 | | | | | |

Mark a cell with the time of the first ping that day (IST), or `none`. A `none`
on any row fails 8.1 for that phone; note what the phone was doing (charging,
in a drawer, force-stopped by the battery manager) in Notes.
