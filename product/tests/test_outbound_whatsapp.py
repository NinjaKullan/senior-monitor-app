"""Wave C's WhatsApp transport (spec 007 §3), against a mocked Twilio API.

Same shape as the Resend suite: no socket is opened, the HTTP contract is
asserted exactly, and failures become failed DeliveryResults, never
exceptions.
"""

from __future__ import annotations

import logging

import httpx
import pytest

from kettle.outbound_templates import render
from kettle.outbound_whatsapp import TwilioWhatsAppTransport

SID = "AC_test_sid"
TOKEN = "auth_test_token"
FROM = "whatsapp:+14155238886"
PARENT = "+919845550001"

#: The ask takes one variable since DECISIONS 217 — the first name of the
#: family member who set Kettle up. Every send in this file supplies it, the
#: way the engine does.
ASK_VARS = {"owner_name": "Priya"}


def transport_answering(handler) -> tuple[TwilioWhatsAppTransport, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def record_then(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    client = httpx.Client(transport=httpx.MockTransport(record_then))
    return TwilioWhatsAppTransport(SID, TOKEN, FROM, client=client), seen


def ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(201, json={"sid": "SM123"})


def test_the_ask_becomes_one_twilio_call_with_the_rendered_body():
    transport, seen = transport_answering(ok)
    result = transport.send(PARENT, "ask_parent", ASK_VARS)

    assert result.delivered is True
    assert result.transport == "twilio_whatsapp"
    [request] = seen
    assert str(request.url) == (
        f"https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages.json"
    )
    assert request.headers["authorization"].startswith("Basic ")
    form = dict(
        pair.split("=", 1) for pair in request.content.decode().split("&")
    )
    from urllib.parse import unquote_plus

    decoded = {k: unquote_plus(v) for k, v in form.items()}
    assert decoded == {
        "From": FROM,
        "To": f"whatsapp:{PARENT}",
        "Body": render("ask_parent", ASK_VARS),
    }


def test_a_refusal_is_a_failed_result_with_the_status_code():
    transport, _ = transport_answering(lambda request: httpx.Response(401))
    result = transport.send(PARENT, "ask_parent", ASK_VARS)
    assert result.delivered is False
    assert result.detail == "HTTP 401"


def test_a_network_error_is_a_failed_result_never_an_exception():
    def explode(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("slow", request=request)

    transport, _ = transport_answering(explode)
    result = transport.send(PARENT, "ask_parent", ASK_VARS)
    assert result.delivered is False
    assert result.detail == "ConnectTimeout"


def test_all_three_credentials_are_required_to_construct():
    with pytest.raises(RuntimeError, match="TWILIO_ACCOUNT_SID"):
        TwilioWhatsAppTransport("", TOKEN, FROM)
    with pytest.raises(RuntimeError, match="TWILIO_AUTH_TOKEN"):
        TwilioWhatsAppTransport(SID, "", FROM)
    with pytest.raises(RuntimeError, match="TWILIO_WHATSAPP_FROM"):
        TwilioWhatsAppTransport(SID, TOKEN, "")


def test_it_carries_the_ask_and_only_the_ask():
    """The sandbox is a parent-side channel (the Wave C channel ruling)."""
    transport, _ = transport_answering(ok)
    assert transport.kinds == ("ask",)
    assert transport.requires_address is True


def test_logs_carry_a_masked_number_and_no_body(caplog):
    transport, _ = transport_answering(ok)
    with caplog.at_level(logging.DEBUG, logger="kettle.outbound"):
        transport.send(PARENT, "ask_parent", ASK_VARS)
    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert PARENT not in logged
    assert "…0001" in logged
    assert "Everything okay today" not in logged
