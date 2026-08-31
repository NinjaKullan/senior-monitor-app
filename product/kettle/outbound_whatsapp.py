"""The WhatsApp transport: the ask to the parent, by sandbox or by template.

Same posture as the email transport (spec 007 §3, DECISIONS 159): its own
module because the decision core carries no network client; asks only, because
this is a parent-side channel and everything child-facing travels by email (the
Wave C channel ruling); every failure is a `delivered=False` result that lands
in the ledger as retryable 'failed' with a founder alert, never an exception
that kills a pass; logs carry a masked number and no body.

**Two send shapes, chosen by config, never by code** (spec 011 §4, Wave D
Phase 2). A registered number may only START a conversation with a
Meta-approved template, so when `TWILIO_ASK_CONTENT_SID` is set the ask goes
as `ContentSid` and the words come from Meta's approved copy rather than from
this process. Unset — the sandbox — and the request is byte-for-byte what it
has always been: `Body`, rendered from the registry. The registry keeps the
same words either way (DECISIONS 206), so the two paths say one thing.

The approved template carries NO buttons (DECISIONS 205: Meta forbids emoji in
template buttons) and zero variables, so a template send names the SID and
nothing else — no `ContentVariables`, no button payload to parse. A parent's
👍 arrives as an ordinary inbound message, which is what the reply path has
always read.

The sandbox constraint worth remembering until Phase 3's sunset: a parent must
have joined the sandbox (sent the join code once) before Twilio will deliver.
An unjoined number surfaces here as a failed send and an ops alert, which is
the correct loudness — the registered sender removes the step.
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


def _refusal(response: httpx.Response) -> str:
    """Twilio's own words for a refusal, appended to the HTTP status.

    Failure honesty (spec 011 §4): a parent silently not asked is the one
    failure Kettle must never absorb quietly, and "HTTP 400" alone does not
    tell the founder whether the number is wrong, the template is paused, or
    Meta disabled it overnight. Twilio answers errors with `code` and
    `message`, so both are carried into the ops alert VERBATIM rather than
    translated through a table of error numbers this code would have to keep
    current — whatever Twilio and Meta say arrives unedited.

    Defensive by construction: a refusal that is not JSON, or is JSON of an
    unexpected shape, must still produce an alert rather than an exception on
    the failure path.
    """
    try:
        payload = response.json()
    except ValueError:
        return ""
    if not isinstance(payload, dict):
        return ""
    code = payload.get("code")
    message = payload.get("message")
    parts = [str(part) for part in (code, message) if part not in (None, "")]
    return f" ({'; '.join(parts)})" if parts else ""


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
        ask_content_sid: str = "",
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
        # Empty is the sandbox: no SID, no template, the body send unchanged.
        self._ask_content_sid = ask_content_sid.strip()

    def send(
        self,
        to: str,
        template_id: str,
        variables: Mapping[str, str],
        relationship: str | None = None,
    ) -> DeliveryResult:
        # `relationship` is the email transport's subject/chip concern; a
        # WhatsApp message has no subject line, so it is accepted and unused.
        found = template(template_id)
        if found.kind not in self.kinds:  # pragma: no cover - engine routes first
            return DeliveryResult(
                delivered=False, transport=self.name, detail=f"no route for {found.kind}"
            )
        payload: dict[str, str] = {"From": self._from, "To": f"whatsapp:{to}"}
        if self._ask_content_sid:
            # The business-initiated shape: the SID names Meta-approved copy,
            # so no body travels from here. Zero variables (DECISIONS 206/207),
            # so no ContentVariables either — an empty one is a field Twilio
            # would have to parse for nothing.
            payload["ContentSid"] = self._ask_content_sid
        else:
            payload["Body"] = render(template_id, variables)
        try:
            response = self._client.post(
                f"{self._api_base}/2010-04-01/Accounts/{self._sid}/Messages.json",
                auth=self._auth,
                data=payload,
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
            detail = f"HTTP {response.status_code}{_refusal(response)}"
            log.warning(
                "outbound: twilio %s to %s refused: %s",
                template_id,
                _mask(to),
                detail,
            )
            return DeliveryResult(
                delivered=False,
                transport=self.name,
                detail=detail,
            )
        log.info(
            "outbound: twilio %s -> %s delivered (%s)",
            template_id,
            _mask(to),
            "template" if self._ask_content_sid else "body",
        )
        return DeliveryResult(delivered=True, transport=self.name)
