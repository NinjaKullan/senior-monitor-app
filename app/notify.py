"""Founder-only notification transport (ntfy.sh).

Product law #3: there is no code path here that can reach a parent or any
other family member. One topic, owned by the founder, from an env var.
"""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

log = logging.getLogger("kettle.notify")

NTFY_BASE_URL = "https://ntfy.sh"


class Notifier(Protocol):
    """Anything that can deliver a founder alert."""

    def send(self, message: str) -> bool:
        """Deliver the message; return True if an HTTP POST was attempted."""
        ...


class NtfyNotifier:
    """Posts alert text to https://ntfy.sh/{topic}.

    The topic string is the only authentication ntfy has, so it is treated as
    a secret: env-supplied, never logged, never rendered in a page.
    """

    def __init__(
        self,
        topic: str,
        client: httpx.Client | None = None,
        base_url: str = NTFY_BASE_URL,
    ) -> None:
        self._topic = topic
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=5.0)

    def send(self, message: str) -> bool:
        """POST the message to the founder's topic. Never raises."""
        if not self._topic:
            log.info("ntfy topic unset, log-only alert: %s", message)
            return False
        try:
            self._client.post(
                f"{self._base_url}/{self._topic}",
                content=message.encode("utf-8"),
                headers={"Title": "Kettle pilot"},
            )
        except httpx.HTTPError as exc:  # network flake must never kill the loop
            log.warning("ntfy delivery failed: %s", type(exc).__name__)
        return True


class LogOnlyNotifier:
    """Fallback used when no topic is configured."""

    def send(self, message: str) -> bool:
        """Log the alert and report that nothing was sent."""
        log.info("log-only alert: %s", message)
        return False
