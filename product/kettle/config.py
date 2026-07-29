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
        heartbeat_loop=src.get("HEARTBEAT_LOOP", "1").strip()
        not in ("0", "false", "no"),
    )
