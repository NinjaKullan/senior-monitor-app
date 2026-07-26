# Spec 001a — device_alive timer signal (amendment to 001)

*Small, urgent: deploy before the parents' phones are set up (today). PM: Fable.*

## What

A new allowlisted signal name: `device_alive`. Sent by a Shortcuts **time-of-day** automation (e.g. daily 07:00 IST) from each parent's phone. It fires with zero human involvement, so it proves only "phone on + network up + Shortcuts engine alive" — a plumbing diagnostic, never a person signal.

## Changes

1. `config.py`: add `"device_alive"` to `SIGNALS`. It must **NOT** be added to `ALARM_GRADE` — it says nothing about a human.
2. That's the only functional change. Verify (add/adjust tests):
   - `/ping?...&signal=device_alive` → 200, stored.
   - Noon/evening heartbeat checks ignore it (they already filter on `ALARM_GRADE` — assert a day with only `device_alive` pings still fires the noon alert for that person).
   - Infra check counts it as pipeline liveness (it already uses any-ping — assert this): timer pings flowing while app pings are silent must NOT fire the 🔧 infra alert. That is precisely the diagnostic value: apps silent + device_alive flowing = person quiet or app automations dead, pipeline fine.
   - `/status` renders the new row (no template change should be needed; signal list is driven by `SIGNALS`).
3. README: add the Shortcuts recipe — Automation → Time of Day → 7:00 AM, daily → Run Immediately → Get Contents of URL → `.../ping?token=<T>&who=<who>&signal=device_alive`.

## Definition of done

pytest green (including the three assertions above), ruff clean, pushed to main.
