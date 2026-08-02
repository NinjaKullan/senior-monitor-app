"""Environment-driven configuration. Secrets have no defaults."""

from __future__ import annotations

import os
import secrets
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Resolved runtime configuration."""

    database_url: str
    ntfy_topic: str
    ip_hash_salt: str
    default_tz: str
    public_base_url: str
    heartbeat_loop: bool
    # Global digest kill-switch. Off by default: family-facing sending is opt-in
    # at two levels, this one and families.digest_enabled (also false by default).
    digest_enabled: bool
    digest_morning_cutoff_hour: int
    digest_evening_hour: int
    digest_evening_minute: int
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from: str
    # Global ladder kill-switch, over and above each family's ladder_mode.
    # Off by default: this is the alert path.
    ladder_enabled: bool
    # Browser origins allowed to POST /waitlist. An explicit list, not a
    # wildcard: this is the only route a browser ever calls, and the landing
    # page is served from origins we control (spec 006 §7).
    waitlist_origins: tuple[str, ...]


def settings_from_env(env: Mapping[str, str] | None = None) -> Settings:
    """Build settings from the process environment (or a supplied mapping)."""
    src: Mapping[str, str] = os.environ if env is None else env

    database_url = src.get("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required and has no default")

    # Unset means a fresh random salt per boot: ip_hash stays a one-way ops
    # breadcrumb and simply stops correlating across restarts.
    salt = src.get("IP_HASH_SALT", "").strip() or secrets.token_hex(16)

    return Settings(
        database_url=database_url,
        ntfy_topic=src.get("NTFY_TOPIC", "").strip(),
        ip_hash_salt=salt,
        default_tz=src.get("DEFAULT_TZ", "").strip() or "Asia/Kolkata",
        public_base_url=(
            src.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
            or "https://kettle-api.fly.dev"
        ),
        heartbeat_loop=_flag(src, "HEARTBEAT_LOOP", default=True),
        digest_enabled=_flag(src, "DIGEST_ENABLED", default=False),
        digest_morning_cutoff_hour=_int(src, "DIGEST_MORNING_CUTOFF_HOUR", 14),
        digest_evening_hour=_int(src, "DIGEST_EVENING_HOUR", 20),
        digest_evening_minute=_int(src, "DIGEST_EVENING_MINUTE", 30),
        twilio_account_sid=src.get("TWILIO_ACCOUNT_SID", "").strip(),
        twilio_auth_token=src.get("TWILIO_AUTH_TOKEN", "").strip(),
        twilio_from=src.get("TWILIO_FROM", "").strip(),
        ladder_enabled=_flag(src, "LADDER_ENABLED", default=False),
        waitlist_origins=_origins(src, "WAITLIST_ORIGINS"),
    )


#: getkettle.* per the GTM roadmap, plus the Vite dev server. Further TLDs are an
#: env var at deploy, not a code change.
DEFAULT_WAITLIST_ORIGINS = (
    "https://getkettle.com",
    "https://www.getkettle.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _origins(src: Mapping[str, str], name: str) -> tuple[str, ...]:
    """Comma-separated origin allowlist, falling back to the shipped default."""
    raw = src.get(name, "").strip()
    if not raw:
        return DEFAULT_WAITLIST_ORIGINS
    return tuple(origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip())


def _flag(src: Mapping[str, str], name: str, default: bool) -> bool:
    """Read a boolean env var. Anything but 0/false/no is on."""
    raw = src.get(name, "").strip().lower()
    if not raw:
        return default
    return raw not in ("0", "false", "no")


def _int(src: Mapping[str, str], name: str, default: int) -> int:
    """Read an integer env var, falling back on anything unparseable."""
    raw = src.get(name, "").strip()
    try:
        return int(raw)
    except ValueError:
        return default
