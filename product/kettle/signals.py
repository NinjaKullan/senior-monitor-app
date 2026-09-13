"""The standard signal set new parents are seeded with.

This is a *seed*, not an allowlist: the allowlist is per parent and lives in
`parent_signals`. One parent enabling a signal never enables it for anyone else.

Alarm-grade means a human deliberately did something. device_alive comes from a
time-of-day automation with zero human involvement and charger events are
household plumbing, so neither may ever stand in for a person (product law #6).
"""

from __future__ import annotations

# (signal, alarm_grade): the iOS Shortcuts seed, unchanged since 0001.
STANDARD_SIGNALS: tuple[tuple[str, bool], ...] = (
    ("whatsapp", True),
    ("youtube", True),
    ("news", True),
    ("charge_on", False),
    ("charge_off", False),
    ("device_alive", False),
)

#: Spec 014 §3 (DECISIONS 329): the Android senior app's voice. `unlock` is a
#: deliberate human act on a personal device, the same class as opening
#: WhatsApp; `motion` is a fact about the phone (a non-zero step delta, once
#: an hour, never a count) and corroborates only; `device_alive` finds its
#: intended home as a daily heartbeat from a native app.
ANDROID_SIGNALS: tuple[tuple[str, bool], ...] = (
    ("unlock", True),
    ("charger", False),
    ("motion", False),
    ("device_alive", False),
)

#: The default seed per `devices.platform` (DECISIONS 100, cashed in by 014):
#: what a parent is provisioned with when no `--signals` is given.
PLATFORM_SIGNALS: dict[str, tuple[tuple[str, bool], ...]] = {
    "ios_shortcuts": STANDARD_SIGNALS,
    "android": ANDROID_SIGNALS,
}

# Human-facing names for the pre-built shortcuts a family receives. Nobody types
# a URL: each signal ships as a named shortcut behind a tapped iCloud link.
SIGNAL_LABELS: dict[str, str] = {
    "whatsapp": "WhatsApp",
    "youtube": "YouTube",
    "news": "News",
    "charge_on": "Charger On",
    "charge_off": "Charger Off",
    "device_alive": "Daily Check",
    # The merged end-state pair (DECISIONS 107): one multi-app automation firing
    # `routine`, one charger automation with Connected and Disconnected both
    # checked firing `charger`. These replace the per-app and per-edge keys for
    # new setups; the old keys stay valid — Amma is live on them, and nothing is
    # rebuilt remotely for elegance.
    "routine": "Daily routine",
    "charger": "Charger",
    # Spec 014 §3: the Android keys. A label names what the phone did, never
    # an app: "Phone unlocked" over ACTION_USER_PRESENT (or SCREEN_ON when the
    # phone has no lock screen), "Phone moved" over a non-zero step delta.
    "unlock": "Phone unlocked",
    "motion": "Phone moved",
}

#: The keys that ship as iOS shortcuts (a `.shortcut` file behind an iCloud
#: link, an automation row on the setup page). The Android keys are the app's
#: own and never become a shortcut.
SHORTCUT_SIGNALS: frozenset[str] = frozenset(
    {"whatsapp", "youtube", "news", "charge_on", "charge_off", "device_alive", "routine", "charger"}
)

#: Alarm-grade for the whole vocabulary, seed set and merged pair alike, so a
#: caller choosing signals by name (provision --signals, DECISIONS 94) cannot
#: invent a grade. `routine` is alarm-grade — a human deliberately opened one of
#: their habit apps; *which* app never leaves the phone, the automation fires one
#: shortcut for any of them. `charger` stays corroborating: the on/off pair it
#: merges was household plumbing under law #6, and coarsening the two edges into
#: one event changes nothing about who it may speak for (DECISIONS 107 accepted
#: exactly that — session semantics were never load-bearing).
ALARM_GRADE: dict[str, bool] = {
    **dict(STANDARD_SIGNALS),
    "routine": True,
    "charger": False,
    **dict(ANDROID_SIGNALS),
}


def shortcut_name(signal: str) -> str:
    """The shortcut's name on the phone, e.g. `Kettle — WhatsApp`.

    No parent name (DECISIONS 96a, founder on-device). An iPhone tile truncates
    to `Kettle — TestDad C…` — the name consumes the line and the signal, the
    only token a reader needs, is what gets cut. Everyone who reads this string
    already knows whose phone it is on: the parent in their own library, the
    person building automations who must pick one of five *by signal*, and the
    app, which shows signals inside a per-parent view.

    The cost — identical names across two parents' phones make a crossed-files
    mix-up less visible — is accepted because the runbook's verify-by-prediction
    step catches that in ten seconds regardless of naming. Ruling 61 still
    holds: the repair surface names what the phone names, so the app's tripwire
    labels and this function move together, and the drift test keeps it so.
    """
    return f"Kettle — {SIGNAL_LABELS.get(signal, signal)}"
