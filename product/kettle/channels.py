"""Delivery channels for family-facing digests.

One protocol, three implementations: Twilio SMS (live), WhatsApp template (a
stub until Meta business verification lands), and a log-only fallback for when
no credentials are configured — the same shape as the ntfy notifier.

A channel only ever carries text this codebase generated from `messages.py`.
"""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

from kettle.config import Settings

log = logging.getLogger("kettle.channels")

TWILIO_BASE_URL = "https://api.twilio.com"


class DigestChannel(Protocol):
    """Anything that can deliver one digest message to one recipient."""

    name: str

    def send(self, to_e164: str, message: str) -> bool:
        """Deliver the message; return True when it was accepted."""
        ...


class TwilioSmsChannel:
    """SMS via Twilio. The launch channel — WhatsApp replaces it when approved."""

    name = "sms"

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_e164: str,
        client: httpx.Client | None = None,
        base_url: str = TWILIO_BASE_URL,
    ) -> None:
        self._sid = account_sid
        self._token = auth_token
        self._from = from_e164
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=10.0)

    def send(self, to_e164: str, message: str) -> bool:
        """POST to the Messages API. Never raises — a flake is a failed send."""
        url = f"{self._base_url}/2010-04-01/Accounts/{self._sid}/Messages.json"
        try:
            response = self._client.post(
                url,
                data={"To": to_e164, "From": self._from, "Body": message},
                auth=(self._sid, self._token),
            )
        except httpx.HTTPError as exc:
            log.warning("twilio delivery failed: %s", type(exc).__name__)
            return False
        if not response.is_success:
            # Status only: the body can echo the recipient number.
            log.warning("twilio rejected the message: HTTP %s", response.status_code)
            return False
        return True


class WhatsAppTemplateChannel:
    """Stub for the WhatsApp Business template send.

    Deliberately inert. Meta business verification is on the critical path
    (roadmap §6 risk 1) and the API shape is not settled until it lands, so this
    reports "not delivered" rather than pretending. A member set to `whatsapp`
    before then gets one recorded failure per message, which is exactly the
    signal the founder needs, and SMS remains the working default.
    """

    name = "whatsapp"

    def send(self, to_e164: str, message: str) -> bool:
        """Always False: not wired yet."""
        log.warning("whatsapp channel is not configured yet; message not sent")
        return False


class LogOnlyChannel:
    """Used when no provider credentials are configured.

    Reports success so local runs and tests exercise the same idempotency path
    they would in production; the recorded channel is `log`, so a `digest_sends`
    row never claims an SMS that nobody sent.
    """

    name = "log"

    def send(self, to_e164: str, message: str) -> bool:
        """Log the message and report it handled."""
        log.info("log-only digest to %s: %s", _mask(to_e164), message)
        return True


def _mask(to_e164: str) -> str:
    """Last four digits only — logs do not need a family's phone number."""
    return f"…{to_e164[-4:]}" if len(to_e164) > 4 else "…"


def build_channels(
    settings: Settings, client: httpx.Client | None = None
) -> dict[str, DigestChannel]:
    """Map a member's `digest_channel` value to the object that delivers it."""
    sms: DigestChannel
    if settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_from:
        sms = TwilioSmsChannel(
            settings.twilio_account_sid,
            settings.twilio_auth_token,
            settings.twilio_from,
            client=client,
        )
    else:
        sms = LogOnlyChannel()
    return {"sms": sms, "whatsapp": WhatsAppTemplateChannel()}
