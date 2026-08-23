"""Wave B's email transport (spec 007 §3), against a mocked Resend API.

No test here opens a socket: `httpx.MockTransport` answers every request, so
what is asserted is the exact HTTP contract — and, through `run_outbound`,
that a real delivery result lands in the ledger as 'sent' or 'failed' exactly
like the console transport's does.
"""

from __future__ import annotations

import json
import logging

import httpx
import pytest

from kettle.outbound import run_outbound
from kettle.outbound_email import REPLY_TO, ResendTransport
from kettle.outbound_templates import EMAIL_SUBJECT, render
from kettle.provisioning import provision_family
from testsupport import BASE_URL, add_child_email

FROM = "Kettle <notes@send.heykettle.com>"
CHILD_EMAIL = "child@example.test"


def transport_answering(handler) -> tuple[ResendTransport, list[httpx.Request]]:
    """A ResendTransport wired to a mock API; returns it plus the request log."""
    seen: list[httpx.Request] = []

    def record_then(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    client = httpx.Client(transport=httpx.MockTransport(record_then))
    return ResendTransport("re_test_key", FROM, client=client), seen


def ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"id": "email_123"})


def test_a_digest_becomes_one_resend_call_with_the_rendered_body():
    transport, seen = transport_answering(ok)
    result = transport.send(CHILD_EMAIL, "digest_morning_normal", {"relationship": "Mom"})

    assert result.delivered is True
    assert result.transport == "resend"
    [request] = seen
    assert str(request.url) == "https://api.resend.com/emails"
    assert request.headers["authorization"] == "Bearer re_test_key"
    payload = json.loads(request.content)
    assert payload == {
        "from": FROM,
        "to": [CHILD_EMAIL],
        "reply_to": REPLY_TO,
        "subject": EMAIL_SUBJECT,
        "text": render("digest_morning_normal", {"relationship": "Mom"}),
    }


def test_a_refusal_is_a_failed_result_with_the_status_code():
    transport, _ = transport_answering(lambda request: httpx.Response(500))
    result = transport.send(CHILD_EMAIL, "digest_evening_normal", {})
    assert result.delivered is False
    assert result.detail == "HTTP 500"


def test_a_network_error_is_a_failed_result_never_an_exception():
    def explode(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    transport, _ = transport_answering(explode)
    result = transport.send(CHILD_EMAIL, "digest_evening_normal", {})
    assert result.delivered is False
    assert result.detail == "ConnectError"


def test_the_key_is_required_to_construct_at_all():
    with pytest.raises(RuntimeError, match="RESEND_API_KEY"):
        ResendTransport("", FROM)


def test_logs_carry_a_masked_address_and_no_body(caplog):
    transport, _ = transport_answering(ok)
    with caplog.at_level(logging.DEBUG, logger="kettle.outbound"):
        transport.send(CHILD_EMAIL, "digest_morning_normal", {"relationship": "Mom"})
    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert CHILD_EMAIL not in logged
    assert "ch…@example.test" in logged
    assert "Mom's morning" not in logged


def test_through_the_engine_a_delivery_lands_in_the_ledger_as_sent(conn, notifier):
    """The seam end to end: the engine hands a digest to resend, the mock
    delivers, the ledger says sent-by-resend — and the ask, which resend does
    not carry, records skipped with a founder alert instead of vanishing."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    provisioned = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    add_child_email(conn, provisioned.family_id)
    transport, seen = transport_answering(ok)

    at_digest = datetime(2026, 8, 21, 8, 30, tzinfo=ZoneInfo("Asia/Kolkata"))
    run_outbound(conn, transport, at_digest, notifier=notifier)
    row = conn.execute(
        "select transport, status from sent_messages where kind = 'digest_morning'"
    ).fetchone()
    assert (row["transport"], row["status"]) == ("resend", "sent")
    assert len(seen) == 1

    at_ask = datetime(2026, 8, 21, 11, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    run_outbound(conn, transport, at_ask, notifier=notifier)
    row = conn.execute(
        "select status from sent_messages where kind = 'ask'"
    ).fetchone()
    assert row["status"] == "skipped"
    assert any("does not carry" in m for m in notifier.messages)
    assert len(seen) == 1  # the ask never became an HTTP call


def test_a_failed_resend_day_is_retryable_in_the_ledger(conn, notifier):
    """500 today, 200 on the retry: the same slot upgrades failed -> sent."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    provisioned = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    add_child_email(conn, provisioned.family_id)
    at_digest = datetime(2026, 8, 21, 8, 30, tzinfo=ZoneInfo("Asia/Kolkata"))

    failing, _ = transport_answering(lambda request: httpx.Response(500))
    run_outbound(conn, failing, at_digest, notifier=notifier)
    assert conn.execute(
        "select status from sent_messages where kind = 'digest_morning'"
    ).fetchone()["status"] == "failed"
    assert any("HTTP 500" in m for m in notifier.messages)

    recovered, _ = transport_answering(ok)
    run_outbound(conn, recovered, at_digest + timedelta(minutes=1), notifier=notifier)
    assert conn.execute(
        "select status from sent_messages where kind = 'digest_morning'"
    ).fetchone()["status"] == "sent"
