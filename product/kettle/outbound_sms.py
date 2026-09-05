"""The SMS transport (spec 011 Amendment A): the ask to a +1 parent by text.

Same posture as the WhatsApp transport: its own module because the decision
core carries no network client; parent-side kinds only (the ask and the
once-only welcome); every failure is a `delivered=False` result that lands in
the ledger as retryable 'failed' with a founder alert, never an exception;
logs carry a masked number and no body.

The request names the Messaging Service the 10DLC campaign is bound to and
NEVER a bare From: the registration lives on the service, and a From would
route around it. No ContentSid — SMS has no templates — so the body is the
registry's, rendered here, byte for byte the filed sample (A.4). Twilio's
error 21610 (the recipient has opted out) is carried back as `opted_out` so
the engine can record STOP as if it had arrived (A.5).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping

import httpx

from kettle.outbound import DeliveryResult
from kettle.outbound_templates import KIND_ASK, KIND_SMS_WELCOME, render, template
from kettle.outbound_whatsapp import TWILIO_API_BASE, _mask, _refusal

log = logging.getLogger("kettle.outbound")

#: Twilio: "Attempt to send to unsubscribed recipient".
OPTED_OUT_CODE = 21610


class TwilioSMSTransport:
    """POST one rendered text to Twilio's Messages endpoint via the service."""

    name = "twilio_sms"
    kinds = (KIND_ASK, KIND_SMS_WELCOME)
    requires_address = True

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        messaging_service_sid: str,
        client: httpx.Client | None = None,
        api_base: str = TWILIO_API_BASE,
    ) -> None:
        missing = [
            name
            for name, value in (
                ("TWILIO_ACCOUNT_SID", account_sid),
                ("TWILIO_AUTH_TOKEN", auth_token),
                ("TWILIO_MESSAGING_SERVICE_SID", messaging_service_sid),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"{', '.join(missing)} required when OUTBOUND_TRANSPORT selects "
                "twilio_sms and have no default — set the Fly secrets before "
                "selecting this transport"
            )
        self._sid = account_sid
        self._auth = (account_sid, auth_token)
        self._service = messaging_service_sid
        self._api_base = api_base.rstrip("/")
        self._client = client or httpx.Client(timeout=10.0)

    def send(
        self,
        to: str,
        template_id: str,
        variables: Mapping[str, str],
        relationship: str | None = None,
    ) -> DeliveryResult:
        found = template(template_id)
        if found.kind not in self.kinds:  # pragma: no cover - engine routes first
            return DeliveryResult(
                delivered=False, transport=self.name, detail=f"no route for {found.kind}"
            )
        payload = {
            "MessagingServiceSid": self._service,
            "To": to,
            "Body": render(template_id, variables),
        }
        try:
            response = self._client.post(
                f"{self._api_base}/2010-04-01/Accounts/{self._sid}/Messages.json",
                auth=self._auth,
                data=payload,
            )
        except httpx.HTTPError as exc:
            log.warning(
                "outbound: sms %s to %s did not complete: %s",
                template_id,
                _mask(to),
                type(exc).__name__,
            )
            return DeliveryResult(delivered=False, transport=self.name, detail=type(exc).__name__)
        if response.status_code // 100 != 2:
            detail = f"HTTP {response.status_code}{_refusal(response)}"
            log.warning("outbound: sms %s to %s refused: %s", template_id, _mask(to), detail)
            return DeliveryResult(
                delivered=False,
                transport=self.name,
                detail=detail,
                opted_out=_error_code(response) == OPTED_OUT_CODE,
            )
        log.info("outbound: sms %s -> %s delivered", template_id, _mask(to))
        return DeliveryResult(delivered=True, transport=self.name)


def _error_code(response: httpx.Response) -> int | None:
    try:
        payload = response.json()
    except ValueError:
        return None
    code = payload.get("code") if isinstance(payload, dict) else None
    return code if isinstance(code, int) else None
