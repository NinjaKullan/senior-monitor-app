"""Wave B's email transport: digests to the child, via Resend (spec 007 §3).

Deliberately its own module: `kettle/outbound.py` is the decision core and
carries no network client — a test pins that — so the one place the outbound
channel can reach the internet is this file, and it can reach exactly one API.

What this transport will and will not do:

* **Digests only.** `kinds` names the two digest kinds and nothing else; the
  engine records an ask or follow-on as skipped (with a founder ops alert)
  rather than handing it here, because a message to a parent has no channel
  until Wave C.
* **No address, no attempt.** `requires_address` makes an empty recipient an
  unroutable skip upstream; this class never sees one.
* **Failure is a result, never an exception.** A non-2xx, a timeout, a DNS
  flake — each comes back as `delivered=False` with a short detail, lands in
  the ledger as 'failed' (retryable, 0015) and ops-alerts the founder. Nothing
  here can kill a scheduler pass.
* **Logs get a masked address and no body.** The body reaches the family's
  inbox and the ledger stores only the template id, same as every transport.

Tracking is off at the Resend domain level (docs/auth-smtp-plan.md) and this
sends plain text only, so there is nothing for a tracker to rewrite.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping

import httpx

from kettle.outbound import DeliveryResult
from kettle.outbound_templates import (
    EMAIL_SUBJECT,
    KIND_DIGEST_EVENING,
    KIND_DIGEST_MORNING,
    render,
    template,
)

log = logging.getLogger("kettle.outbound")

RESEND_API_URL = "https://api.resend.com/emails"

#: Reply-to a human, not the sending machinery (docs/auth-smtp-plan.md).
REPLY_TO = "hello@heykettle.com"


def _mask(address: str) -> str:
    """Enough to recognise the recipient in a log, never the whole address."""
    name, _, domain = address.partition("@")
    if not domain:
        return "…"
    return f"{name[:2]}…@{domain}"


class ResendTransport:
    """POST one rendered digest to Resend's send endpoint."""

    name = "resend"
    kinds = (KIND_DIGEST_MORNING, KIND_DIGEST_EVENING)
    requires_address = True

    def __init__(
        self,
        api_key: str,
        from_address: str,
        client: httpx.Client | None = None,
        api_url: str = RESEND_API_URL,
    ) -> None:
        if not api_key:
            raise RuntimeError(
                "RESEND_API_KEY is required when OUTBOUND_TRANSPORT=resend "
                "and has no default — set the Fly secret before selecting "
                "this transport"
            )
        self._api_key = api_key
        self._from = from_address
        self._api_url = api_url
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
                self._api_url,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "from": self._from,
                    "to": [to],
                    "reply_to": REPLY_TO,
                    "subject": EMAIL_SUBJECT,
                    "text": body,
                },
            )
        except httpx.HTTPError as exc:
            log.warning(
                "outbound: resend %s to %s did not complete: %s",
                template_id,
                _mask(to),
                type(exc).__name__,
            )
            return DeliveryResult(
                delivered=False, transport=self.name, detail=type(exc).__name__
            )
        if response.status_code // 100 != 2:
            log.warning(
                "outbound: resend %s to %s refused: HTTP %s",
                template_id,
                _mask(to),
                response.status_code,
            )
            return DeliveryResult(
                delivered=False,
                transport=self.name,
                detail=f"HTTP {response.status_code}",
            )
        log.info("outbound: resend %s -> %s delivered", template_id, _mask(to))
        return DeliveryResult(delivered=True, transport=self.name)
