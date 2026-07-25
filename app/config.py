"""Environment-driven configuration. Secrets never have defaults."""

from __future__ import annotations

import os
import secrets
from collections.abc import Mapping
from dataclasses import dataclass

# Product law: the only people we know about in the pilot are the founder's parents.
PEOPLE: tuple[str, ...] = ("mom", "dad")

# The only signal names accepted. Anything else is a 400 and is not stored.
SIGNALS: tuple[str, ...] = (
    "whatsapp",
    "youtube",
    "news",
    "charge_on",
    "charge_off",
)

# Alarm-grade signals: deliberate app opens. Charger events only corroborate.
ALARM_GRADE: tuple[str, ...] = ("whatsapp", "youtube", "news")


@dataclass(frozen=True)
class Settings:
    """Resolved runtime configuration."""

    ping_token: str
    ntfy_topic: str
    db_path: str
    tz_display: str
    ip_hash_salt: str
    heartbeat_loop: bool


def settings_from_env(env: Mapping[str, str] | None = None) -> Settings:
    """Build settings from the process environment (or a supplied mapping)."""
    src: Mapping[str, str] = os.environ if env is None else env

    token = src.get("PING_TOKEN", "").strip()
    if not token:
        raise RuntimeError("PING_TOKEN is required and has no default")

    # No salt configured means a fresh random one per boot: ip_hash stays a
    # one-way ops breadcrumb and simply stops correlating across restarts.
    salt = src.get("IP_HASH_SALT", "").strip() or secrets.token_hex(16)

    return Settings(
        ping_token=token,
        ntfy_topic=src.get("NTFY_TOPIC", "").strip(),
        db_path=src.get("DB_PATH", "/data/pilot.db").strip(),
        tz_display=src.get("TZ_DISPLAY", "Asia/Kolkata").strip() or "Asia/Kolkata",
        ip_hash_salt=salt,
        heartbeat_loop=src.get("HEARTBEAT_LOOP", "1").strip() not in ("0", "false", "no"),
    )
