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
    # Specs 003 and 004 were retired by 007 (DECISIONS 141), and their settings
    # went with them: DIGEST_ENABLED, the digest hours, LADDER_ENABLED and the
    # three TWILIO_* values, which existed for the SMS channel and the inbound
    # webhook those engines used. Wave C re-adds a Twilio credential when it has
    # a transport to spend it on; a setting with nothing reading it is a
    # deployment that looks configured and is not.
    # Spec 007's outbound channel. Off by default like every other sending
    # path, and in Wave A "on" still reaches nothing: the only transport that
    # exists writes a log line. Two switches rather than one because the wave
    # after this adds a transport that does not.
    outbound_enabled: bool
    # Runs the scheduler as an in-process background task, same pattern as
    # HEARTBEAT_LOOP (DECISIONS 154). The loop is the machinery; OUTBOUND_ENABLED
    # stays the kill switch on the decisions themselves, so production can stop
    # the engine deciding without restarting the process.
    outbound_loop: bool
    # Which registered transport the loop hands its messages to. "console" —
    # the dark transport, a log line and a ledger row — is the only registered
    # name until a wave adds another; anything else refuses to boot
    # (`transport_from_name`), so a typo cannot fail open into a real sender.
    outbound_transport: str
    # Wave B's email transport (spec 007 §3). The key is read only when
    # OUTBOUND_TRANSPORT=resend is selected — and then it must exist, or the
    # app refuses to boot (fail closed, DECISIONS 154's rule extended to
    # credentials). The from address defaults to the verified sending
    # subdomain (docs/auth-smtp-plan.md); reply-to goes to a human.
    resend_api_key: str
    resend_from: str
    # The shared secret the reply webhook requires. Empty — the default — means
    # the endpoint does not exist: an unauthenticated route that can cancel a
    # follow-on would let anyone who knows a number suppress an escalation.
    outbound_reply_token: str
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
        outbound_enabled=_flag(src, "OUTBOUND_ENABLED", default=False),
        outbound_loop=_flag(src, "OUTBOUND_LOOP", default=False),
        outbound_transport=src.get("OUTBOUND_TRANSPORT", "").strip() or "console",
        resend_api_key=src.get("RESEND_API_KEY", "").strip(),
        resend_from=(
            src.get("RESEND_FROM", "").strip()
            or "Kettle <notes@send.heykettle.com>"
        ),
        outbound_reply_token=src.get("OUTBOUND_REPLY_TOKEN", "").strip(),
        waitlist_origins=_origins(src, "WAITLIST_ORIGINS"),
    )


#: heykettle.com is the live domain (DECISIONS 142), plus the Vite dev server.
#: Further origins are an env var at deploy, not a code change — which is how the
#: transition works: `kettle-site.fly.dev` is deliberately NOT in this default,
#: because the default is what the system should settle on, and the old origin is
#: a temporary grant the founder sets and later removes.
DEFAULT_WAITLIST_ORIGINS = (
    "https://heykettle.com",
    "https://www.heykettle.com",
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
