"""Wave C's WhatsApp transport: the ask to the parent, via the Twilio sandbox.

Same posture as the email transport (spec 007 §3, DECISIONS 159): its own
module because the decision core carries no network client; asks only, because
the sandbox is a parent-side channel and everything child-facing travels by
email (the Wave C channel ruling); every failure is a `delivered=False` result
that lands in the ledger as retryable 'failed' with a founder alert, never an
exception that kills a pass; logs carry a masked number and no body.

The sandbox constraint worth remembering at flip time: a parent must have
joined the sandbox (sent the join code once) before Twilio will deliver to
them. An unjoined number surfaces here as a failed send and an ops alert,
which is the correct loudness — Wave D's registered sender removes the step.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping

import httpx

from kettle.outbound import DeliveryResult
from kettle.outbound_templates import KIND_ASK, render, template

log = logging.getLogger("kettle.outbound")

TWILIO_API_BASE = "https://api.twilio.com"


def _mask(number: str) -> str:
    return f"…{number[-4:]}" if len(number) > 4 else "…"


class TwilioWhatsAppTransport:
    """POST one rendered ask to Twilio's Messages endpoint."""

    name = "twilio_whatsapp"
    kinds = (KIND_ASK,)
    requires_address = True

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_address: str,
        client: httpx.Client | None = None,
        api_base: str = TWILIO_API_BASE,
    ) -> None:
        missing = [
            name
            for name, value in (
                ("TWILIO_ACCOUNT_SID", account_sid),
                ("TWILIO_AUTH_TOKEN", auth_token),
                ("TWILIO_WHATSAPP_FROM", from_address),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"{', '.join(missing)} required when OUTBOUND_TRANSPORT selects "
                "twilio_whatsapp and have no default — set the Fly secrets "
                "before selecting this transport"
            )
        self._sid = account_sid
        self._auth = (account_sid, auth_token)
        self._from = from_address
        self._api_base = api_base.rstrip("/")
        self._client = client or httpx.Client(timeout=10.0)

    def send(
        self, to: str, template_id: str, variables: Mapping[str, str]
    ) -> DeliveryResult:
        found = template(template_id)
        if found.kind not in self.kinds:  # pragma: no cover - engine routes first
            return DeliveryResult(
                delivered=False, transport=self.name, detail=f"no route for {found.kind}"
            )
        body = render(template_id, variables)
        try:
            response = self._client.post(
                f"{self._api_base}/2010-04-01/Accounts/{self._sid}/Messages.json",
                auth=self._auth,
                data={"From": self._from, "To": f"whatsapp:{to}", "Body": body},
            )
        except httpx.HTTPError as exc:
            log.warning(
                "outbound: twilio %s to %s did not complete: %s",
                template_id,
                _mask(to),
                type(exc).__name__,
            )
            return DeliveryResult(
                delivered=False, transport=self.name, detail=type(exc).__name__
            )
        if response.status_code // 100 != 2:
            log.warning(
                "outbound: twilio %s to %s refused: HTTP %s",
                template_id,
                _mask(to),
                response.status_code,
            )
            return DeliveryResult(
                delivered=False,
                transport=self.name,
                detail=f"HTTP {response.status_code}",
            )
        log.info("outbound: twilio %s -> %s delivered", template_id, _mask(to))
        return DeliveryResult(delivered=True, transport=self.name)
