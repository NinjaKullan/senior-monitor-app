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


def shortcut_name(parent_name: str, signal: str) -> str:
    """The iCloud shortcut name for one parent's signal, e.g. 'Kettle — Amma WhatsApp'."""
    return f"Kettle — {parent_name} {SIGNAL_LABELS.get(signal, signal)}"
