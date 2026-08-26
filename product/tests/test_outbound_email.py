"""Wave B's email transport (spec 007 §3), against a mocked Resend API.

No test here opens a socket: `httpx.MockTransport` answers every request, so
what is asserted is the exact HTTP contract — and, through `run_outbound`,
that a real delivery result lands in the ledger as 'sent' or 'failed' exactly
like the console transport's does.
"""

from __future__ import annotations

import json
import logging
import re

import httpx
import pytest
from test_outbound_copy import assert_outbound_copy_law

from kettle.outbound import run_outbound
from kettle.outbound_email import REPLY_TO, ResendTransport
from kettle.outbound_html import GLYPH_URL, render_email_html
from kettle.outbound_templates import EMAIL_SUBJECT, render
from kettle.provisioning import provision_family
from testsupport import BASE_URL, add_child_email

FROM = "Kettle <notes@send.heykettle.com>"
CHILD_EMAIL = "child@example.test"


def visible_text(html: str) -> str:
    """The words a reader sees: tags stripped, entities decoded, whitespace
    collapsed."""
    from html import unescape

    text = unescape(re.sub(r"<[^>]+>", " ", html))
    return re.sub(r"\s+", " ", text).strip()


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
    result = transport.send(
        CHILD_EMAIL, "digest_morning_normal", {"relationship": "Mom"}, relationship="Mom"
    )

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
        # Per-parent (email-polish pass): the subject names whose day it is.
        "subject": "A note about Mom's day",
        # Multipart, always: the registry body as text, the wrapper as HTML.
        "text": render("digest_morning_normal", {"relationship": "Mom"}),
        "html": render_email_html(
            "digest_morning_normal", {"relationship": "Mom"}, "Mom"
        ),
    }


def test_an_email_about_nobody_in_particular_keeps_the_plain_subject():
    transport, seen = transport_answering(ok)
    transport.send(CHILD_EMAIL, "digest_evening_normal", {})
    [request] = seen
    assert json.loads(request.content)["subject"] == EMAIL_SUBJECT


def test_the_html_part_carries_exactly_one_image_the_hosted_glyph():
    html = render_email_html("digest_evening_recovered", {}, "Mom")
    images = re.findall(r"<img\b[^>]*>", html)
    assert len(images) == 1
    [img] = images
    assert f'src="{GLYPH_URL}"' in img
    assert 'width="44"' in img and 'height="44"' in img
    assert 'alt="Kettle"' in img
    # The glyph lives on the site at an unhashed stable name; nothing else is
    # fetched from anywhere — no external CSS, no remote fonts.
    assert html.count("http") == html.count("https://heykettle.com")


def test_with_images_blocked_the_email_still_reads_complete():
    """No text may exist only inside an image: strip the <img> and every word
    of the message survives — chip, sentence, sub-line, footer."""
    html = render_email_html("digest_morning_normal", {"relationship": "Mom"}, "Mom")
    without_images = re.sub(r"<img\b[^>]*>", "", html)
    text = visible_text(without_images)
    assert "Mom" in text  # the chip
    assert "Mom's morning looked like a normal morning." in text
    assert "Next note this evening." in text
    assert EMAIL_SUBJECT in text  # the footer line
    assert "heykettle.com" in text  # the footer link text


def test_the_plain_text_part_carries_the_same_words_as_the_html():
    for template_id, variables, relationship in [
        ("digest_morning_normal", {"relationship": "Mom"}, "Mom"),
        ("digest_evening_normal", {}, "Mom"),
        ("digest_evening_recovered", {}, "Dad"),
        ("follow_on_family", {"relationship": "Mom"}, "Mom"),
        ("all_clear_family", {"relationship": "Grandma"}, "Grandma"),
    ]:
        body = render(template_id, variables)
        html = render_email_html(template_id, variables, relationship)
        assert body in visible_text(html), template_id


def test_the_html_obeys_the_copy_law_and_its_own_style_rules():
    for relationship in ("Mom", None):
        html = render_email_html("digest_evening_normal", {}, relationship)
        # The visible words go through the same scanner every body does; the
        # markup carries no em dash anywhere, visible or not, and no style
        # arrives from outside the message.
        assert_outbound_copy_law(visible_text(html))
        assert "—" not in html
        assert "<link" not in html and "@import" not in html
        assert "font-family:Georgia, 'Times New Roman', serif" in html
    # No chip renders when the engine has no label to put in it — and nothing
    # else changes.
    without = render_email_html("digest_evening_normal", {}, None)
    assert "border-radius:999px" not in without


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
    # The engine told the transport whose day this is: per-parent subject,
    # and the multipart body rode along.
    payload = json.loads(seen[0].content)
    assert payload["subject"] == "A note about Mom's day"
    assert "html" in payload and "text" in payload

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
