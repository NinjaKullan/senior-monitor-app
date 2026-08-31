"""Wave D Phase 2 (spec 011 §4): the ask goes out as an approved template.

A registered WhatsApp number may only START a conversation with a
Meta-approved template, so the one thing that changes on the flip is the
shape of the ask's HTTP request: `ContentSid` instead of `Body`. Everything
else in this system — the decision core, the ledger, idempotency, the reply
webhook, the parsing — is untouched, and the tests here are largely about
proving that untouchedness rather than the new line of code.

Three claims carry the weight:

* **Config chooses, never code.** The Content SID's presence is the whole
  switch, so the sandbox path stays available and byte-identical until the
  Phase 3 sunset, and rolling the real number back is emptying one variable.
* **No buttons anywhere** (DECISIONS 205: Meta forbids emoji in template
  buttons). Nothing sends one, nothing parses one, and a parent's 👍 arrives
  as the ordinary inbound message the reply path has always read.
* **A refusal says why.** A parent silently not asked is the one failure
  Kettle must never absorb quietly, so Twilio's own code and message reach
  the ops alert verbatim — including the day Meta pauses the template.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote_plus

import httpx
import pytest
from test_outbound import (
    CountingTransport,
    at,
    family,  # noqa: F401 - fixture
    ledger,
    run_twice,
    statuses,
)

from kettle import db
from kettle.config import settings_from_env
from kettle.outbound import record_parent_reply, transport_from_name
from kettle.outbound_templates import render
from kettle.outbound_whatsapp import TwilioWhatsAppTransport

SID = "AC_test_sid"
TOKEN = "auth_test_token"
#: The real sender and the approved template, per the Phase 2 order.
REAL_FROM = "whatsapp:+19843704452"
CONTENT_SID = "HXdb4e38c90d0ccc51bbcd264a002d0a8a"
SANDBOX_FROM = "whatsapp:+14155238886"
PARENT = "+919845550001"


def transport_answering(handler, **kwargs) -> tuple[TwilioWhatsAppTransport, list]:
    seen: list[httpx.Request] = []

    def record_then(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    client = httpx.Client(transport=httpx.MockTransport(record_then))
    return TwilioWhatsAppTransport(SID, TOKEN, kwargs.pop("from_address", REAL_FROM),
                                   client=client, **kwargs), seen


def ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(201, json={"sid": "SM123"})


def form_of(request: httpx.Request) -> dict[str, str]:
    pairs = dict(pair.split("=", 1) for pair in request.content.decode().split("&"))
    return {key: unquote_plus(value) for key, value in pairs.items()}


# --- the template send --------------------------------------------------------


def test_the_ask_goes_as_a_content_sid_with_no_body_and_no_variables():
    """The business-initiated shape. The approved template has zero variables
    (DECISIONS 206/207), so the request names the SID and nothing else — an
    empty ContentVariables would be a field Twilio parses for nothing."""
    transport, seen = transport_answering(ok, ask_content_sid=CONTENT_SID)
    result = transport.send(PARENT, "ask_parent", {})

    assert result.delivered is True
    # The ledger names the transport that actually carried it (spec 011 §4).
    assert result.transport == "twilio_whatsapp"
    [request] = seen
    assert form_of(request) == {
        "From": REAL_FROM,
        "To": f"whatsapp:{PARENT}",
        "ContentSid": CONTENT_SID,
    }
    assert "Body" not in form_of(request)
    assert "ContentVariables" not in form_of(request)


def test_nothing_sends_or_expects_a_button(caplog):
    """DECISIONS 205: Meta forbids emoji in template buttons, so the approved
    template has none. Nothing in the send path may name one — a button
    payload built here would be a message Meta refuses, and a button payload
    PARSED here would be a reply path that only works for taps."""
    transport, seen = transport_answering(ok, ask_content_sid=CONTENT_SID)
    transport.send(PARENT, "ask_parent", {})
    [request] = seen
    body = request.content.decode().lower()
    for shape in ("button", "quick_reply", "payload", "action"):
        assert shape not in body, f"the send names {shape}"

    source = (Path(__file__).resolve().parents[1] / "kettle").rglob("*.py")
    for module in source:
        text = module.read_text().lower()
        for shape in ("buttonpayload", "quick_reply", "button_text"):
            assert shape not in text, f"{module.name} reaches for {shape}"


# --- the sandbox, unchanged ---------------------------------------------------


def test_without_a_content_sid_the_request_is_the_sandbox_one_byte_for_byte():
    """Phase 2 must not touch the sandbox path (spec 011 §4): with no SID
    configured the transport sends the registry's rendered body, exactly as
    Wave C has all along."""
    transport, seen = transport_answering(ok, from_address=SANDBOX_FROM)
    result = transport.send(PARENT, "ask_parent", {})

    assert result.delivered is True
    [request] = seen
    assert form_of(request) == {
        "From": SANDBOX_FROM,
        "To": f"whatsapp:{PARENT}",
        "Body": render("ask_parent", {}),
    }
    assert "ContentSid" not in form_of(request)


def test_the_switch_is_config_and_the_sandbox_is_still_reachable():
    """Config chooses, never code: the same env with and without one variable
    builds the same transport in its two shapes, so the Phase 3 sunset is a
    deletion and a rollback is emptying a variable."""
    base = {
        "DATABASE_URL": "postgresql://x/y",
        "TWILIO_ACCOUNT_SID": SID,
        "TWILIO_AUTH_TOKEN": TOKEN,
        "TWILIO_WHATSAPP_FROM": SANDBOX_FROM,
    }
    sandbox = settings_from_env(base)
    assert sandbox.twilio_ask_content_sid == ""
    real = settings_from_env(
        {**base, "TWILIO_WHATSAPP_FROM": REAL_FROM, "TWILIO_ASK_CONTENT_SID": CONTENT_SID}
    )
    assert real.twilio_ask_content_sid == CONTENT_SID
    assert real.twilio_whatsapp_from == REAL_FROM
    # And both boot a working transport through the registered factory.
    for settings in (sandbox, real):
        built = transport_from_name("twilio_whatsapp", settings)
        assert built.kinds == ("ask",)


# --- failure honesty ----------------------------------------------------------


def test_a_paused_template_is_a_loud_failure_carrying_metas_own_words():
    """The failure the spec names by hand: Meta pauses or disables the
    template and every ask stops. Twilio's code and message ride into the
    detail verbatim, so the ops alert says WHY rather than 'HTTP 400'."""
    def paused(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "code": 63016,
                "message": "Template is paused due to low quality",
            },
        )

    transport, _ = transport_answering(paused, ask_content_sid=CONTENT_SID)
    result = transport.send(PARENT, "ask_parent", {})
    assert result.delivered is False
    assert "63016" in result.detail
    assert "paused" in result.detail.lower()
    assert result.detail.startswith("HTTP 400")


def test_a_refusal_that_is_not_json_still_fails_loudly_rather_than_raising():
    """The alert path must never be the thing that breaks: an HTML error page
    or an empty body still produces a failed result with the status."""
    for response in (
        httpx.Response(502, text="<html>bad gateway</html>"),
        httpx.Response(500, text=""),
        httpx.Response(400, json=["unexpected", "shape"]),
    ):
        transport, _ = transport_answering(
            lambda request, r=response: r, ask_content_sid=CONTENT_SID
        )
        result = transport.send(PARENT, "ask_parent", {})
        assert result.delivered is False
        assert result.detail.startswith(f"HTTP {response.status_code}")


def test_a_rejected_template_send_reaches_the_founder_and_stays_retryable(
    conn, family, notifier  # noqa: F811
):
    """End to end through the engine: a refused ask is a 'failed' ledger row
    naming the transport, one ntfy, one ops_alert — never a silent absence."""
    class RefusingTemplate(CountingTransport):
        name = "twilio_whatsapp"

        def send(self, to, template_id, variables, relationship=None):
            from kettle.outbound import DeliveryResult

            return DeliveryResult(
                delivered=False,
                transport="twilio_whatsapp",
                detail="HTTP 400 (63016; Template is paused due to low quality)",
            )

    assert run_twice(conn, RefusingTemplate(), at(11, 0), notifier=notifier) == []
    assert ledger(conn) == []
    assert statuses(conn)["ask"] == "failed"
    alerts = [
        row["detail"]
        for row in conn.execute(
            "select detail from ops_alerts where kind = 'outbound_failed'"
        ).fetchall()
    ]
    assert len(alerts) == 1
    assert "63016" in alerts[0] and "paused" in alerts[0].lower()
    assert any("63016" in message for message in notifier.messages)

    # The slot stays retryable: the template comes back, the ask goes.
    run_twice(conn, CountingTransport(), at(11, 5), notifier=notifier)
    assert ("ask", "ask_parent") in ledger(conn)
    row = db.message_row(conn, family.family_id, family.parents[0].parent_id,
                         "2026-08-21", "ask")
    assert row["status"] == "sent"


# --- the reply, unchanged by any of this --------------------------------------


@pytest.mark.parametrize(
    ("label", "body"),
    [
        ("a typed thumbs up", "👍"),
        ("what a button tap would have sent", "👍"),
        ("a typed word", "ok"),
        ("something else entirely", "call you later"),
    ],
)
def test_every_inbound_reply_lands_the_same_way(
    conn, family, notifier, label, body  # noqa: F811
):
    """Intake is content-blind and always was, which is exactly why losing the
    button costs nothing (DECISIONS 205): a tap would have arrived as an
    ordinary inbound message, and so does everything else. The body never
    reaches this function — it is listed here only to say that it cannot
    matter."""
    run_twice(conn, CountingTransport(), at(11, 0), notifier=notifier)
    assert record_parent_reply(conn, "+919845550001", at(11, 30)) is True, label
    row = db.message_row(conn, family.family_id, family.parents[0].parent_id,
                         "2026-08-21", "ask")
    assert row["replied_utc"] is not None
    # And the follow-on never fires, whatever the parent typed.
    run_twice(conn, CountingTransport(), at(13, 30), notifier=notifier)
    assert "follow_on" not in statuses(conn)
