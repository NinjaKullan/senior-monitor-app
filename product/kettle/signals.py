"""The standard signal set new parents are seeded with.

This is a *seed*, not an allowlist: the allowlist is per parent and lives in
`parent_signals`. One parent enabling a signal never enables it for anyone else.

Alarm-grade means a human deliberately did something. device_alive comes from a
time-of-day automation with zero human involvement and charger events are
household plumbing, so neither may ever stand in for a person (product law #6).
"""

from __future__ import annotations

# (signal, alarm_grade)
STANDARD_SIGNALS: tuple[tuple[str, bool], ...] = (
    ("whatsapp", True),
    ("youtube", True),
    ("news", True),
    ("charge_on", False),
    ("charge_off", False),
    ("device_alive", False),
)

# Human-facing names for the pre-built shortcuts a family receives. Nobody types
# a URL: each signal ships as a named shortcut behind a tapped iCloud link.
SIGNAL_LABELS: dict[str, str] = {
    "whatsapp": "WhatsApp",
    "youtube": "YouTube",
    "news": "News",
    "charge_on": "Charger On",
    "charge_off": "Charger Off",
    "device_alive": "Daily Check",
}


def shortcut_name(signal: str) -> str:
    """The shortcut's name on the phone, e.g. `Kettle — WhatsApp`.

    No parent name (QUESTIONS 96a, founder on-device). An iPhone tile truncates
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
