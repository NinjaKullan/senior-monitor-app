"""Acceptance criterion 7 — delivery channels.

Twilio is asserted against real HTTP over a mocked transport, so "one POST per
recipient with the right E.164" is a fact about the request, not about a stub.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
import psycopg

from kettle import db
from kettle.channels import (
    LogOnlyChannel,
    TwilioSmsChannel,
    WhatsAppTemplateChannel,
    build_channels,
)
from kettle.digest import OPS_FAILED, STATUS_FAILED, run_digests
from kettle.provisioning import provision_family
from testsupport import BASE_URL, enable_digests

IST = ZoneInfo("Asia/Kolkata")
MORNING_PING = datetime(2026, 8, 3, 8, 12, tzinfo=IST)
MID_MORNING = datetime(2026, 8, 3, 9, 0, tzinfo=IST)

SID = "ACtestsidnotarealcredential"
TOKEN = "testtokennotarealcredential"
FROM = "+15125550999"


class MockTwilio:
    """A real TwilioSmsChannel over a transport that records requests."""

    def __init__(self, status: int = 201) -> None:
        self.requests: list[httpx.Request] = []
        self.status = status

        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return httpx.Response(self.status, json={"sid": "SMtest"})

        self.channel = TwilioSmsChannel(
            SID,
            TOKEN,
            FROM,
            client=httpx.Client(transport=httpx.MockTransport(handler)),
            base_url="https://api.twilio.test",
        )

    def bodies(self) -> list[dict[str, str]]:
        return [dict(httpx.QueryParams(r.content.decode())) for r in self.requests]


def test_twilio_posts_once_per_recipient(conn: psycopg.Connection, settings, notifier):
    """AC7: one POST per recipient, correct E.164 in To and From."""
    twilio = MockTwilio()
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    enable_digests(
        conn,
        family.family_id,
        [("Child", "+15125550100"), ("Sister", "+919845550100")],
    )
    db.insert_ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING, None)

    run_digests(
        conn,
        settings,
        {"sms": twilio.channel, "whatsapp": twilio.channel},
        notifier,
        MID_MORNING,
    )

    assert len(twilio.requests) == 2
    assert twilio.requests[0].url.path == f"/2010-04-01/Accounts/{SID}/Messages.json"
    assert "authorization" in twilio.requests[0].headers

    bodies = twilio.bodies()
    assert {b["To"] for b in bodies} == {"+15125550100", "+919845550100"}
    assert {b["From"] for b in bodies} == {FROM}
    for body in bodies:
        assert "day started normally" in body["Body"]


def test_twilio_failure_records_an_ops_row_and_does_not_crash(
    conn: psycopg.Connection, settings, notifier
):
    """AC7: a rejected send is a failed row plus an ops alert, never an exception."""
    twilio = MockTwilio(status=400)
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    enable_digests(conn, family.family_id)
    db.insert_ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING, None)

    sent = run_digests(
        conn,
        settings,
        {"sms": twilio.channel, "whatsapp": twilio.channel},
        notifier,
        MID_MORNING,
    )

    assert [s.status for s in sent] == [STATUS_FAILED]
    # One retry, then give up: two attempts, not a storm.
    assert len(twilio.requests) == 2

    failures = conn.execute(
        "select * from ops_alerts where kind = %s", (OPS_FAILED,)
    ).fetchall()
    assert len(failures) == 1
    assert "could not be delivered" in failures[0]["detail"]
    # The founder gets told; the phone number does not go in the log.
    assert "+1512" not in failures[0]["detail"]
    assert notifier.messages


def test_a_failed_send_is_not_retried_until_the_next_message(
    conn: psycopg.Connection, settings, notifier
):
    """The failed row holds the slot, so the next pass does not re-dial."""
    twilio = MockTwilio(status=500)
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    enable_digests(conn, family.family_id)
    db.insert_ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING, None)
    channels = {"sms": twilio.channel, "whatsapp": twilio.channel}

    run_digests(conn, settings, channels, notifier, MID_MORNING)
    attempts = len(twilio.requests)
    run_digests(conn, settings, channels, notifier, MID_MORNING)
    assert len(twilio.requests) == attempts


def test_network_error_is_a_failed_send_not_an_exception():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route to host")

    channel = TwilioSmsChannel(
        SID, TOKEN, FROM, client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    assert channel.send("+15125550100", "hello") is False


def test_unset_credentials_fall_back_to_log_only(settings):
    """AC7: no creds, no HTTP — and the row says `log`, not `sms`."""
    channels = build_channels(settings)
    assert isinstance(channels["sms"], LogOnlyChannel)
    assert channels["sms"].name == "log"
    assert channels["sms"].send("+15125550100", "hello") is True


def test_configured_credentials_select_twilio(settings):
    configured = replace(
        settings, twilio_account_sid=SID, twilio_auth_token=TOKEN, twilio_from=FROM
    )
    channels = build_channels(configured)
    assert isinstance(channels["sms"], TwilioSmsChannel)
    assert channels["sms"].name == "sms"


def test_whatsapp_is_an_honest_stub(settings):
    """AC7: the stub reports 'not sent' rather than pretending it delivered."""
    channels = build_channels(settings)
    assert isinstance(channels["whatsapp"], WhatsAppTemplateChannel)
    assert channels["whatsapp"].send("+919845550100", "hello") is False


def test_log_only_channel_records_a_log_channel_row(
    conn: psycopg.Connection, settings, notifier
):
    """A digest_sends row must never claim an SMS that nobody sent."""
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL
    )
    enable_digests(conn, family.family_id)
    db.insert_ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING, None)

    run_digests(conn, settings, build_channels(settings), notifier, MID_MORNING)
    row = conn.execute("select * from digest_sends").fetchone()
    assert row["channel"] == "log"
    assert row["status"] == "sent"
