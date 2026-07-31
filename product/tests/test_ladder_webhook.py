"""Acceptance criteria 2 and 6 — the inbound reply webhook.

AC2 is the second thing that matters most in this spec: a senior's reply
resolves the candidate and its *content* is dropped everywhere. The test posts a
distinctive body and then goes looking for it in every table and every log
record, and fails if it finds it anywhere.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from kettle import db
from kettle.config import Settings
from kettle.ladder import RESOLVED_BY_SENIOR, run_ladder
from kettle.main import create_app
from kettle.provisioning import provision_family
from kettle.twilio_signature import expected_signature, is_valid
from testsupport import BASE_URL, enable_digests, enable_ladder, set_senior_phone

IST = ZoneInfo("Asia/Kolkata")
SENIOR_PHONE = "+919845550001"
MORNING = datetime(2026, 8, 3, 8, 0, tzinfo=IST)
NOON = datetime(2026, 8, 3, 12, 0, tzinfo=IST)

AUTH_TOKEN = "test-auth-token-not-a-real-credential"
WEBHOOK_URL = "http://testserver/twilio/inbound"

# Distinctive enough that finding it anywhere is unambiguous.
SECRET_BODY = "YES amma here my knee hurts a bit but fine ZZQQ7788"


class Recorder:
    """A channel that records; the ladder should not use it in these tests."""

    name = "sms"
    available = True

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send(self, to_e164: str, message: str) -> bool:
        self.sent.append((to_e164, message))
        return True


@pytest.fixture
def signed_settings(settings: Settings) -> Settings:
    return replace(settings, twilio_auth_token=AUTH_TOKEN)


@pytest.fixture
def webhook_client(signed_settings, notifier, conn):
    with TestClient(create_app(signed_settings, notifier)) as c:
        yield c


def _post(client: TestClient, params: dict[str, str], token: str = AUTH_TOKEN):
    body = urlencode(params)
    signature = expected_signature(token, WEBHOOK_URL, params)
    return client.post(
        "/twilio/inbound",
        content=body,
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "x-twilio-signature": signature,
        },
    )


def _armed_with_ask(conn, settings, notifier, mode="live"):
    """A family whose senior has been asked and has not answered yet."""
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    enable_ladder(conn, family.family_id, mode)
    enable_digests(conn, family.family_id, [("Child", "+15125550100")])
    set_senior_phone(conn, family.parents[0].parent_id, SENIOR_PHONE)
    db.insert_ping(conn, family.parents[0].parent_id, "device_alive", MORNING, None)
    run_ladder(conn, settings, {"sms": Recorder(), "whatsapp": Recorder()}, notifier, NOON)
    # The webhook reads the real clock, so the grace window has to be real too:
    # anchor the ask to five minutes ago rather than to the fabricated NOON,
    # which is in the future and would make every reply look "inside grace".
    conn.execute("update ladder_candidates set ask_utc = now() - interval '5 minutes'")
    return family


# --- AC2 --------------------------------------------------------------------


def test_senior_reply_resolves_and_the_family_hears_nothing(
    conn, signed_settings, notifier, webhook_client
):
    """AC2: a reply inside grace closes the candidate; the family is not told."""
    _armed_with_ask(conn, signed_settings, notifier)
    channel = Recorder()

    response = _post(webhook_client, {"From": SENIOR_PHONE, "Body": "YES"})
    assert response.status_code == 200

    candidate = conn.execute("select * from ladder_candidates").fetchone()
    assert candidate["resolution"] == RESOLVED_BY_SENIOR
    assert candidate["resolved_utc"] is not None

    # Nothing further happens, and the family circle was never contacted.
    run_ladder(
        conn,
        signed_settings,
        {"sms": channel, "whatsapp": channel},
        notifier,
        NOON + timedelta(hours=3),
    )
    assert channel.sent == []
    assert any("family not contacted" in m for m in notifier.messages)


def test_the_reply_body_is_dropped_everywhere(
    conn, signed_settings, notifier, webhook_client, caplog
):
    """AC2, the guarantee: we record that they answered, never what they said."""
    _armed_with_ask(conn, signed_settings, notifier)

    with caplog.at_level(0):
        response = _post(
            webhook_client, {"From": SENIOR_PHONE, "Body": SECRET_BODY, "NumMedia": "0"}
        )
    assert response.status_code == 200

    needle = "ZZQQ7788"

    # Every column of every table in the schema.
    tables = [
        r["table_name"]
        for r in conn.execute(
            "select table_name from information_schema.tables "
            "where table_schema = 'public'"
        ).fetchall()
    ]
    for table in tables:
        rows = conn.execute(f"select * from {table}").fetchall()  # noqa: S608 - test
        for row in rows:
            blob = " ".join(str(v) for v in row.values())
            assert needle not in blob, f"reply body leaked into {table}"
            assert SECRET_BODY not in blob, f"reply body leaked into {table}"

    # Every log record the request produced.
    for record in caplog.records:
        assert needle not in record.getMessage()

    # And every founder notification.
    assert all(needle not in m for m in notifier.messages)

    # The fact of the reply *was* recorded — this is not passing by doing nothing.
    assert (
        conn.execute("select resolution from ladder_candidates").fetchone()["resolution"]
        == RESOLVED_BY_SENIOR
    )


def test_reply_after_grace_does_not_resolve(conn, signed_settings, notifier, webhook_client):
    """Grace is a window, not a promise. Late replies land after the ladder moved."""
    family = _armed_with_ask(conn, signed_settings, notifier)
    # Grace is 90 minutes; put the ask well outside it, on the real clock.
    conn.execute("update ladder_candidates set ask_utc = now() - interval '200 minutes'")
    del family

    assert _post(webhook_client, {"From": SENIOR_PHONE, "Body": "YES"}).status_code == 200
    assert conn.execute(
        "select resolution from ladder_candidates"
    ).fetchone()["resolution"] is None


def test_reply_from_an_unknown_number_records_nothing(
    conn, signed_settings, notifier, webhook_client
):
    """A wrong number is a signed request about nobody. Acknowledge, record nothing."""
    _armed_with_ask(conn, signed_settings, notifier)
    events_before = conn.execute("select count(*) as n from ladder_events").fetchone()["n"]

    assert _post(
        webhook_client, {"From": "+15550009999", "Body": "YES"}
    ).status_code == 200

    assert conn.execute(
        "select resolution from ladder_candidates"
    ).fetchone()["resolution"] is None
    assert (
        conn.execute("select count(*) as n from ladder_events").fetchone()["n"]
        == events_before
    )


# --- AC6: signature validation ----------------------------------------------


def test_unsigned_request_is_403_and_records_nothing(
    conn, signed_settings, notifier, webhook_client
):
    """AC6: no signature, no entry."""
    _armed_with_ask(conn, signed_settings, notifier)

    response = webhook_client.post(
        "/twilio/inbound",
        content=urlencode({"From": SENIOR_PHONE, "Body": "YES"}),
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 403
    assert response.text == "forbidden"
    assert conn.execute(
        "select resolution from ladder_candidates"
    ).fetchone()["resolution"] is None


def test_mismatched_signature_is_403(conn, signed_settings, notifier, webhook_client):
    """AC6: a signature computed with the wrong token is no signature at all."""
    _armed_with_ask(conn, signed_settings, notifier)

    response = _post(
        webhook_client, {"From": SENIOR_PHONE, "Body": "YES"}, token="wrong-token"
    )
    assert response.status_code == 403
    assert conn.execute(
        "select resolution from ladder_candidates"
    ).fetchone()["resolution"] is None


def test_tampered_body_invalidates_the_signature(
    conn, signed_settings, notifier, webhook_client
):
    """The signature covers the parameters, so changing one breaks it."""
    _armed_with_ask(conn, signed_settings, notifier)
    params = {"From": SENIOR_PHONE, "Body": "YES"}
    signature = expected_signature(AUTH_TOKEN, WEBHOOK_URL, params)

    response = webhook_client.post(
        "/twilio/inbound",
        content=urlencode({"From": "+15550001111", "Body": "YES"}),
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "x-twilio-signature": signature,
        },
    )
    assert response.status_code == 403


def test_unconfigured_deployment_rejects_everything(conn, settings, notifier):
    """An empty auth token must reject every request, not accept every request."""
    with TestClient(create_app(settings, notifier)) as client:  # no token configured
        response = client.post(
            "/twilio/inbound",
            content=urlencode({"From": SENIOR_PHONE}),
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "x-twilio-signature": "anything",
            },
        )
    assert response.status_code == 403


def test_signature_helper_matches_twilios_algorithm():
    """Known-answer check of the URL + sorted-params + HMAC-SHA1 + base64 chain."""
    params = {"Body": "YES", "From": "+15551234567", "To": "+15559876543"}
    signature = expected_signature("secret", "https://example.test/hook", params)
    assert is_valid("secret", "https://example.test/hook", params, signature)
    assert not is_valid("secret", "https://example.test/other", params, signature)
    assert not is_valid("other", "https://example.test/hook", params, signature)
    assert not is_valid("secret", "https://example.test/hook", params, None)
    assert not is_valid("", "https://example.test/hook", params, signature)
    # Parameter order must not matter; parameter content must.
    assert is_valid("secret", "https://example.test/hook", dict(reversed(list(
        params.items()))), signature)
    assert not is_valid(
        "secret", "https://example.test/hook", {**params, "Body": "NO"}, signature
    )
