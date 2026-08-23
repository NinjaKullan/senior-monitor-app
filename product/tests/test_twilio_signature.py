"""The reply webhook's Twilio-signature path (spec 007 §2.6, DECISIONS 163).

Half unit — the signature math against a hand-computed vector — and half
integration: a signed POST through the real route, with no shared-secret
header, must reach `record_parent_reply`; a tampered one must not.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import replace
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient

from kettle.main import create_app
from kettle.provisioning import provision_family
from kettle.twilio_signature import expected_signature, verify_signature
from testsupport import BASE_URL, add_child_email, set_parent_whatsapp

TOKEN = "twilio_auth_test_token"
URL = f"{BASE_URL}/outbound/reply"
WHATSAPP = "+919845550001"


def sign(url: str, params: dict[str, str], token: str = TOKEN) -> str:
    """An independent implementation of Twilio's signing, so the module under
    test is checked against the algorithm, not against itself."""
    payload = url + "".join(k + params[k] for k in sorted(params))
    return base64.b64encode(
        hmac.new(token.encode(), payload.encode(), hashlib.sha1).digest()
    ).decode()


def test_the_signature_math_matches_an_independent_implementation():
    params = {"From": "whatsapp:+919845550001", "Body": "👍", "SmsSid": "SM1"}
    assert expected_signature(TOKEN, URL, params) == sign(URL, params)
    assert verify_signature(TOKEN, URL, params, sign(URL, params)) is True


def test_any_tamper_fails() -> None:
    params = {"From": "whatsapp:+919845550001", "Body": "yes"}
    good = sign(URL, params)
    assert verify_signature(TOKEN, URL, {**params, "Body": "no"}, good) is False
    assert verify_signature(TOKEN, URL + "x", params, good) is False
    assert verify_signature("other_token", URL, params, good) is False
    assert verify_signature(TOKEN, URL, params, good[:-2] + "xx") is False


def test_missing_credentials_fail_closed_never_open():
    params = {"From": "x"}
    assert verify_signature("", URL, params, sign(URL, params)) is False
    assert verify_signature(TOKEN, URL, params, "") is False


@pytest.fixture
def twilio_client(settings, notifier, conn):
    """A client whose reply route accepts Twilio signatures and has no shared
    secret at all — the Wave C production shape."""
    cfg = replace(settings, outbound_reply_token="", twilio_auth_token=TOKEN)
    with TestClient(create_app(cfg, notifier, clock=lambda: _at(11, 30))) as c:
        yield c


def _at(hour: int, minute: int = 0):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    return datetime(2026, 8, 21, hour, minute, tzinfo=ZoneInfo("Asia/Kolkata"))


def _quiet_family_with_pending_ask(conn):
    provisioned = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    add_child_email(conn, provisioned.family_id)
    set_parent_whatsapp(conn, provisioned.parents[0].parent_id, WHATSAPP)

    from kettle.outbound import LogTransport, run_outbound

    run_outbound(conn, LogTransport(), _at(11, 0))
    return provisioned


def test_a_signed_whatsapp_reply_cancels_the_follow_on(twilio_client, conn):
    """End to end: Twilio's own signature is the credential, the whatsapp:
    prefix is stripped to find the parent, the body is verified then
    discarded, and the pending ask is marked answered."""
    _quiet_family_with_pending_ask(conn)
    params = {"From": f"whatsapp:{WHATSAPP}", "Body": "👍", "SmsSid": "SM1"}

    response = twilio_client.post(
        "/outbound/reply",
        content=urlencode(params),
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "X-Twilio-Signature": sign(URL, params),
        },
    )
    assert response.status_code == 204
    stored = conn.execute(
        "select replied_utc from sent_messages where kind = 'ask'"
    ).fetchone()
    assert stored["replied_utc"] is not None


def test_a_bad_signature_is_refused_and_cancels_nothing(twilio_client, conn):
    _quiet_family_with_pending_ask(conn)
    params = {"From": f"whatsapp:{WHATSAPP}", "Body": "👍"}

    response = twilio_client.post(
        "/outbound/reply",
        content=urlencode(params),
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "X-Twilio-Signature": sign(URL, params, token="wrong_token"),
        },
    )
    assert response.status_code == 403
    stored = conn.execute(
        "select replied_utc from sent_messages where kind = 'ask'"
    ).fetchone()
    assert stored["replied_utc"] is None


def test_the_body_is_verified_then_discarded(twilio_client, conn, caplog):
    """§2.6's content-blind rule survives the signature path: the reply text
    participates in verification and appears nowhere afterwards."""
    import logging

    _quiet_family_with_pending_ask(conn)
    secret = "yes all fine, forgot my phone at the temple"
    params = {"From": f"whatsapp:{WHATSAPP}", "Body": secret}

    with caplog.at_level(logging.DEBUG):
        twilio_client.post(
            "/outbound/reply",
            content=urlencode(params),
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "X-Twilio-Signature": sign(URL, params),
            },
        )
    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert secret not in logged and "temple" not in logged
    assert WHATSAPP not in logged
    stored = conn.execute("select * from sent_messages where kind = 'ask'").fetchone()
    assert "temple" not in str(stored)
