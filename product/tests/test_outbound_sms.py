"""Spec 011 Amendment A — the SMS transport for +1 parents (A.9).

Routing (A.2): WhatsApp wins; a +1 phone with consent and no STOP goes by
text; anything else is a recorded skip that names the failed condition, and
the two Twilio routes never stand in for each other. The transport (A.3):
one call naming the Messaging Service, a bare To, the body byte for byte,
never a From. The welcome (A.4): once per parent ever. Inbound (A.5): STOP,
START and HELP are never replies; a bare sender is the SMS channel, a
prefixed one is WhatsApp. The consent function (A.7): admins only, refused
for a parent with a WhatsApp number or a non-+1 phone.
"""

from __future__ import annotations

from datetime import datetime
from urllib.parse import parse_qs, urlencode
from zoneinfo import ZoneInfo

import httpx
import psycopg
import pytest

from kettle import db
from kettle.outbound import (
    ROUTE_SMS,
    ROUTE_WHATSAPP,
    LogTransport,
    TransportRoster,
    ask_route,
    record_inbound,
    run_outbound,
)
from kettle.outbound_sms import TwilioSMSTransport
from kettle.outbound_templates import OWNER_FALLBACK, owner_first_name, render
from kettle.provisioning import provision_family
from testsupport import BASE_URL, add_child_email, add_member, as_user, set_parent_whatsapp

IST = ZoneInfo("Asia/Kolkata")
ADMIN = "11111111-1111-1111-1111-111111111111"
MEMBER = "22222222-2222-2222-2222-222222222222"
US_PHONE = "+14155550123"
UK_PHONE = "+442079460123"
WHATSAPP = "+919845550001"
SERVICE = "MG_test_service"
SID = "AC_test_sid"
TOKEN = "auth_test_token"
OWNER = {"owner_name": "Priya"}


def at(hour: int, minute: int = 0, day: int = 21) -> datetime:
    return datetime(2026, 8, day, hour, minute, tzinfo=IST)


def set_parent_phone(conn, parent_id, number: str | None) -> None:
    conn.execute("update parents set phone_e164 = %s where id = %s", (number, parent_id))


def consent(conn, parent_id, when: datetime | None = None) -> None:
    conn.execute(
        "update parents set sms_consent_utc = %s where id = %s",
        (when or at(9, 0, day=20), parent_id),
    )


def opt_out(conn, parent_id, when: datetime | None = None) -> None:
    conn.execute(
        "update parents set sms_opted_out_utc = %s where id = %s",
        (when or at(9, 30, day=20), parent_id),
    )


@pytest.fixture
def family(conn):
    """One parent with no numbers at all; each test gives the ones it needs."""
    provisioned = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    add_child_email(conn, provisioned.family_id)
    add_member(conn, provisioned.family_id, ADMIN, role="admin")
    add_member(conn, provisioned.family_id, MEMBER, role="member")
    return provisioned


@pytest.fixture
def parent_id(family):
    return family.parents[0].parent_id


def parent_row(conn, parent_id):
    [row] = [p for p in db.parents_with_tz(conn) if p["parent_id"] == parent_id]
    return row


class WhatsAppLeaf(LogTransport):
    name = ROUTE_WHATSAPP
    kinds = ("ask",)
    requires_address = True


class SMSLeaf(LogTransport):
    name = ROUTE_SMS
    kinds = ("ask", "sms_welcome")
    requires_address = True


class ChildLeaf(LogTransport):
    name = "child-channels"
    kinds = ("digest_morning", "digest_evening", "follow_on", "all_clear")


def both_routes() -> TransportRoster:
    return TransportRoster([WhatsAppLeaf(), SMSLeaf(), ChildLeaf()])


def rows(conn, parent_id) -> list[tuple[str, str, str, str]]:
    found = conn.execute(
        "select kind, template_id, status, transport from sent_messages "
        "where parent_id = %s order by id",
        (parent_id,),
    ).fetchall()
    return [(r["kind"], r["template_id"], r["status"], r["transport"]) for r in found]


def skip_reasons(conn, parent_id) -> list[str]:
    return [
        r["detail"]
        for r in conn.execute(
            "select detail from ops_alerts where parent_id = %s and kind = 'outbound_skipped' "
            "order by id",
            (parent_id,),
        ).fetchall()
    ]


def quiet_morning_ask(conn, transport, notifier=None) -> None:
    """The morning slot, then two passes at the ask slot: the second must
    decide nothing new."""
    run_outbound(conn, transport, at(8, 30), notifier=notifier)
    run_outbound(conn, transport, at(11, 0), notifier=notifier)
    assert run_outbound(conn, transport, at(11, 0), notifier=notifier) == []


# --- A.2 routing ---------------------------------------------------------------


def test_a_whatsapp_number_wins_even_with_a_consented_us_phone(conn, parent_id):
    set_parent_whatsapp(conn, parent_id, WHATSAPP)
    set_parent_phone(conn, parent_id, US_PHONE)
    consent(conn, parent_id)
    route = ask_route(parent_row(conn, parent_id))
    assert (route.carrier_name, route.to, route.template_id) == (
        ROUTE_WHATSAPP,
        WHATSAPP,
        "ask_parent",
    )

    quiet_morning_ask(conn, both_routes())
    asks = [r for r in rows(conn, parent_id) if r[0] == "ask"]
    assert asks == [("ask", "ask_parent", "sent", ROUTE_WHATSAPP)]
    assert not db.sms_welcome_sent(conn, parent_id)


def test_a_consented_us_phone_with_no_whatsapp_goes_by_sms(conn, parent_id):
    set_parent_phone(conn, parent_id, US_PHONE)
    consent(conn, parent_id)
    route = ask_route(parent_row(conn, parent_id))
    assert (route.carrier_name, route.to, route.template_id) == (
        ROUTE_SMS,
        US_PHONE,
        "ask_parent_sms",
    )

    transport = both_routes()
    quiet_morning_ask(conn, transport)
    assert [r for r in rows(conn, parent_id) if r[0] in ("ask", "sms_welcome")] == [
        ("sms_welcome", "sms_welcome", "sent", ROUTE_SMS),
        ("ask", "ask_parent_sms", "sent", ROUTE_SMS),
    ]


@pytest.mark.parametrize(
    ("phone", "consented", "reason"),
    [
        (None, False, "no WhatsApp number and no phone number on file"),
        (UK_PHONE, True, "no WhatsApp number and the phone is not a +1 number"),
        (US_PHONE, False, "no WhatsApp number and no SMS consent recorded"),
    ],
)
def test_a_parent_who_qualifies_for_neither_is_a_recorded_skip_naming_the_condition(
    conn, parent_id, notifier, phone, consented, reason
):
    set_parent_phone(conn, parent_id, phone)
    if consented:
        consent(conn, parent_id)
    route = ask_route(parent_row(conn, parent_id))
    assert route.carrier_name is None
    assert route.reason == reason

    quiet_morning_ask(conn, both_routes(), notifier)
    assert [r for r in rows(conn, parent_id) if r[0] == "ask"] == [
        ("ask", "ask_parent", "skipped", "roster")
    ]
    assert not [r for r in rows(conn, parent_id) if r[0] == "sms_welcome"]
    assert [m for m in notifier.messages if reason in m]
    assert any(reason in d for d in skip_reasons(conn, parent_id))


def test_a_stopped_parent_is_skipped_quietly(conn, parent_id, notifier):
    """STOP is the parent's decision, not a fault: no founder alert per slot."""
    set_parent_phone(conn, parent_id, US_PHONE)
    consent(conn, parent_id)
    opt_out(conn, parent_id)
    route = ask_route(parent_row(conn, parent_id))
    assert route.carrier_name is None and route.quiet is True

    quiet_morning_ask(conn, both_routes(), notifier)
    assert [r for r in rows(conn, parent_id) if r[0] == "ask"] == [
        ("ask", "ask_parent", "skipped", "roster")
    ]
    assert notifier.messages == []
    assert skip_reasons(conn, parent_id) == []


def test_no_cross_transport_fallback_in_either_direction(conn, parent_id, notifier):
    """A WhatsApp parent on an SMS-only stack, and an SMS parent on a
    WhatsApp-only stack, are both skips: the other route never stands in."""
    set_parent_whatsapp(conn, parent_id, WHATSAPP)
    quiet_morning_ask(conn, TransportRoster([SMSLeaf(), ChildLeaf()]), notifier)
    assert [r for r in rows(conn, parent_id) if r[0] == "ask"] == [
        ("ask", "ask_parent", "skipped", "roster")
    ]
    assert [m for m in notifier.messages if f"on the {ROUTE_WHATSAPP} channel" in m]

    conn.execute("delete from sent_messages; delete from ops_alerts")
    notifier.messages.clear()
    set_parent_whatsapp(conn, parent_id, "")
    conn.execute("update parents set whatsapp_e164 = null where id = %s", (parent_id,))
    set_parent_phone(conn, parent_id, US_PHONE)
    consent(conn, parent_id)
    quiet_morning_ask(conn, TransportRoster([WhatsAppLeaf(), ChildLeaf()]), notifier)
    assert [r for r in rows(conn, parent_id) if r[0] in ("ask", "sms_welcome")] == [
        ("sms_welcome", "sms_welcome", "skipped", "roster"),
        ("ask", "ask_parent", "skipped", "roster"),
    ]
    assert [m for m in notifier.messages if f"on the {ROUTE_SMS} channel" in m]


def test_the_dark_console_stands_in_for_either_route(conn, family, parent_id):
    """A dark run records the decision — welcome then ask, the SMS body — so
    the ledger review can see what a real stack would have sent."""
    set_parent_phone(conn, parent_id, US_PHONE)
    consent(conn, parent_id)
    transport = LogTransport()
    quiet_morning_ask(conn, transport)
    assert [r for r in rows(conn, parent_id) if r[0] in ("ask", "sms_welcome")] == [
        ("sms_welcome", "sms_welcome", "sent", "log"),
        ("ask", "ask_parent_sms", "sent", "log"),
    ]
    owner = {"owner_name": owner_first_name(db.family_owner_name(conn, family.family_id))}
    assert ("ask_parent_sms", render("ask_parent_sms", owner)) in transport.sent


def test_paused_and_demo_parents_never_reach_routing(conn, parent_id, notifier):
    set_parent_phone(conn, parent_id, US_PHONE)
    consent(conn, parent_id)
    conn.execute(
        "update parents set paused_until = 'infinity', paused_since = %s where id = %s",
        (at(9, 0, day=20), parent_id),
    )
    quiet_morning_ask(conn, both_routes(), notifier)
    assert [r for r in rows(conn, parent_id) if r[0] in ("ask", "sms_welcome")] == []


# --- A.3 / A.4 the transport and the bodies -------------------------------------


def transport_answering(handler) -> tuple[TwilioSMSTransport, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def record_then(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    client = httpx.Client(transport=httpx.MockTransport(record_then))
    return TwilioSMSTransport(SID, TOKEN, SERVICE, client=client), seen


def ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(201, json={"sid": "SM123"})


def form_of(request: httpx.Request) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(request.content.decode(), keep_blank_values=True).items()}


def test_the_ask_names_the_service_a_bare_to_and_the_body_byte_for_byte():
    transport, seen = transport_answering(ok)
    result = transport.send(US_PHONE, "ask_parent_sms", OWNER)
    assert result.delivered is True
    assert result.transport == ROUTE_SMS
    [request] = seen
    assert str(request.url) == f"https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages.json"
    assert request.headers["authorization"].startswith("Basic ")
    form = form_of(request)
    assert "From" not in form
    assert form == {
        "MessagingServiceSid": SERVICE,
        "To": US_PHONE,
        "Body": render("ask_parent", OWNER) + "\nReply STOP to end these texts.",
    }


def test_the_ask_body_is_the_v7_ask_plus_the_stop_line(conn, parent_id):
    """Named owner and the fallback form, both byte for byte (A.4)."""
    whatsapp_ask = render("ask_parent", OWNER)
    assert render("ask_parent_sms", OWNER) == whatsapp_ask + "\nReply STOP to end these texts."
    fallback = {"owner_name": OWNER_FALLBACK}
    assert render("ask_parent_sms", fallback) == (
        render("ask_parent", fallback) + "\nReply STOP to end these texts."
    )


def test_the_welcome_body_is_the_filed_sample():
    transport, seen = transport_answering(ok)
    transport.send(US_PHONE, "sms_welcome", OWNER)
    [request] = seen
    assert form_of(request)["Body"] == (
        "HeyKettle: Priya set you up to get a short text from Kettle when your "
        "morning is not as usual. At most one question a day, and one reminder. "
        "Message and data rates may apply. Reply HELP for help or STOP to end "
        "these texts. heykettle.com"
    )
    assert "From" not in form_of(request)


def test_a_refusal_is_a_failed_result_and_21610_is_an_opt_out():
    transport, _ = transport_answering(lambda request: httpx.Response(401))
    result = transport.send(US_PHONE, "ask_parent_sms", OWNER)
    assert result.delivered is False
    assert result.detail == "HTTP 401"
    assert result.opted_out is False

    transport, _ = transport_answering(
        lambda request: httpx.Response(
            400, json={"code": 21610, "message": "Attempt to send to unsubscribed recipient"}
        )
    )
    result = transport.send(US_PHONE, "ask_parent_sms", OWNER)
    assert result.delivered is False
    assert result.opted_out is True


def test_a_network_error_is_a_failed_result_never_an_exception():
    def explode(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("slow", request=request)

    transport, _ = transport_answering(explode)
    result = transport.send(US_PHONE, "ask_parent_sms", OWNER)
    assert result.delivered is False
    assert result.detail == "ConnectTimeout"


def test_the_transport_fails_closed_without_the_service_sid(settings, notifier):
    from dataclasses import replace

    from kettle.outbound import transport_from_name

    with pytest.raises(RuntimeError, match="TWILIO_MESSAGING_SERVICE_SID"):
        TwilioSMSTransport(SID, TOKEN, "")
    cfg = replace(
        settings,
        outbound_transport="twilio_sms",
        twilio_account_sid=SID,
        twilio_auth_token=TOKEN,
        twilio_messaging_service_sid="",
    )
    with pytest.raises(RuntimeError, match="TWILIO_MESSAGING_SERVICE_SID"):
        transport_from_name("twilio_sms", cfg)
    built = transport_from_name("twilio_sms", replace(cfg, twilio_messaging_service_sid=SERVICE))
    assert built.name == ROUTE_SMS
    roster = transport_from_name(
        "resend,twilio_sms",
        replace(cfg, resend_api_key="re_x", twilio_messaging_service_sid=SERVICE),
    )
    assert {leaf.name for leaf in roster._transports} == {"resend", ROUTE_SMS}
    with pytest.raises(RuntimeError):
        transport_from_name("twilio_sms,carrier_pigeon", cfg)


def test_the_transport_logs_a_masked_number_and_no_body(caplog):
    import logging

    transport, _ = transport_answering(ok)
    with caplog.at_level(logging.INFO, logger="kettle.outbound"):
        transport.send(US_PHONE, "ask_parent_sms", OWNER)
    text = caplog.text
    assert US_PHONE not in text
    assert "STOP" not in text and "Priya" not in text


def test_a_21610_through_the_engine_records_stop_once_and_stops_texting(conn, parent_id, notifier):
    set_parent_phone(conn, parent_id, US_PHONE)
    consent(conn, parent_id)
    conn.execute(
        "insert into sent_messages (family_id, parent_id, local_date, kind, template_id, "
        "transport, status, sent_utc) values ((select family_id from parents where id = %s), "
        "%s, '2026-08-20', 'sms_welcome', 'sms_welcome', 'twilio_sms', 'sent', %s)",
        (parent_id, parent_id, at(9, 0, day=20)),
    )

    class Unsubscribed(SMSLeaf):
        def send(self, to, template_id, variables, relationship=None):
            from kettle.outbound import DeliveryResult

            return DeliveryResult(
                delivered=False, transport=self.name, detail="HTTP 400 21610", opted_out=True
            )

    roster = TransportRoster([Unsubscribed(), ChildLeaf()])
    run_outbound(conn, roster, at(8, 30), notifier=notifier)
    notifier.messages.clear()
    run_outbound(conn, roster, at(11, 0), notifier=notifier)
    assert [r for r in rows(conn, parent_id) if r[0] == "ask"] == [
        ("ask", "ask_parent_sms", "failed", ROUTE_SMS)
    ]
    stopped = conn.execute(
        "select sms_opted_out_utc from parents where id = %s", (parent_id,)
    ).fetchone()["sms_opted_out_utc"]
    assert stopped is not None
    assert [m for m in notifier.messages if "21610" in m and "stopped" in m] == notifier.messages
    assert len(notifier.messages) == 1

    # The next slot is the quiet skip, and the opt-out timestamp is not moved.
    notifier.messages.clear()
    run_outbound(conn, roster, at(11, 15), notifier=notifier)
    assert notifier.messages == []
    again = conn.execute(
        "select sms_opted_out_utc from parents where id = %s", (parent_id,)
    ).fetchone()["sms_opted_out_utc"]
    assert again == stopped


# --- A.4 the welcome, once ------------------------------------------------------


def test_the_welcome_goes_once_ever_then_only_the_ask(conn, parent_id):
    set_parent_phone(conn, parent_id, US_PHONE)
    consent(conn, parent_id)
    transport = both_routes()
    quiet_morning_ask(conn, transport)
    assert [r for r in rows(conn, parent_id) if r[0] == "sms_welcome"] == [
        ("sms_welcome", "sms_welcome", "sent", ROUTE_SMS)
    ]
    # Next day, quiet again: the ask goes, the welcome does not.
    run_outbound(conn, transport, at(11, 0, day=22))
    assert [r[0] for r in rows(conn, parent_id) if r[0] in ("ask", "sms_welcome")] == [
        "sms_welcome",
        "ask",
        "ask",
    ]


def test_the_welcome_needs_no_quiet_morning(conn, parent_id):
    """Enrollment day: the parent's phone reported, so no ask — the welcome
    still goes at the first pass after consent, and only once."""
    set_parent_phone(conn, parent_id, US_PHONE)
    consent(conn, parent_id)
    db.insert_ping(conn, parent_id, "whatsapp", at(7, 0), None)
    transport = both_routes()
    run_outbound(conn, transport, at(8, 30))
    run_outbound(conn, transport, at(11, 0))
    assert [r for r in rows(conn, parent_id) if r[0] in ("ask", "sms_welcome")] == [
        ("sms_welcome", "sms_welcome", "sent", ROUTE_SMS)
    ]


def test_the_welcome_takes_the_fallback_owner_name(conn):
    """No admin with a display name: `your family`, the ask's own fallback."""
    provisioned = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    parent_id = provisioned.parents[0].parent_id
    set_parent_phone(conn, parent_id, US_PHONE)
    consent(conn, parent_id)
    sms = SMSLeaf()
    run_outbound(conn, TransportRoster([sms, ChildLeaf()]), at(11, 0))
    welcome = sms.sent[0]
    assert welcome[0] == "sms_welcome"
    assert welcome[1].startswith("HeyKettle: Your family set you up")


# --- A.5 inbound -----------------------------------------------------------------


def pending_sms_ask(conn, parent_id) -> None:
    set_parent_phone(conn, parent_id, US_PHONE)
    consent(conn, parent_id)
    quiet_morning_ask(conn, both_routes())
    assert ("ask", "ask_parent_sms", "sent", ROUTE_SMS) in rows(conn, parent_id)


def replied(conn, parent_id) -> bool:
    row = conn.execute(
        "select replied_utc from sent_messages where parent_id = %s and kind = 'ask'",
        (parent_id,),
    ).fetchone()
    return row["replied_utc"] is not None


def sms_state(conn, parent_id):
    return conn.execute(
        "select sms_opted_out_utc from parents where id = %s", (parent_id,)
    ).fetchone()["sms_opted_out_utc"]


def test_stop_records_the_opt_out_alerts_once_and_is_never_a_reply(conn, parent_id, notifier):
    pending_sms_ask(conn, parent_id)
    assert record_inbound(conn, US_PHONE, "STOP", at(11, 30), notifier=notifier) is False
    assert replied(conn, parent_id) is False
    assert sms_state(conn, parent_id) == at(11, 30)
    assert len(notifier.messages) == 1 and "STOP" in notifier.messages[0]
    kinds = [r["kind"] for r in conn.execute("select kind from ops_alerts").fetchall()]
    assert kinds == ["sms_opt_out"]

    # A second STOP changes nothing and says nothing.
    assert record_inbound(conn, US_PHONE, "STOP", at(11, 45), notifier=notifier) is False
    assert sms_state(conn, parent_id) == at(11, 30)
    assert len(notifier.messages) == 1


def test_start_clears_the_opt_out_and_is_never_a_reply(conn, parent_id, notifier):
    pending_sms_ask(conn, parent_id)
    opt_out(conn, parent_id)
    assert record_inbound(conn, US_PHONE, "START", at(11, 30), notifier=notifier) is False
    assert replied(conn, parent_id) is False
    assert sms_state(conn, parent_id) is None
    assert len(notifier.messages) == 1 and "START" in notifier.messages[0]
    kinds = [r["kind"] for r in conn.execute("select kind from ops_alerts").fetchall()]
    assert kinds == ["sms_opt_in"]
    # START while not stopped: nothing to record, no alert.
    assert record_inbound(conn, US_PHONE, "START", at(11, 40), notifier=notifier) is False
    assert len(notifier.messages) == 1


def test_help_records_nothing_and_is_never_a_reply(conn, parent_id, notifier):
    pending_sms_ask(conn, parent_id)
    assert record_inbound(conn, US_PHONE, "HELP", at(11, 30), notifier=notifier) is False
    assert replied(conn, parent_id) is False
    assert sms_state(conn, parent_id) is None
    assert notifier.messages == []
    assert conn.execute("select count(*) as n from ops_alerts").fetchone()["n"] == 0


def test_a_keyword_from_an_unknown_number_changes_nothing(conn, parent_id, notifier):
    pending_sms_ask(conn, parent_id)
    assert record_inbound(conn, "+14155550999", "STOP", at(11, 30), notifier=notifier) is False
    assert sms_state(conn, parent_id) is None
    assert notifier.messages == []


def test_a_plain_reply_from_a_phone_only_parent_matches_by_phone(conn, parent_id):
    pending_sms_ask(conn, parent_id)
    assert record_inbound(conn, US_PHONE, None, at(11, 30)) is True
    assert replied(conn, parent_id) is True


def test_a_whatsapp_reply_still_matches_by_whatsapp_number(conn, parent_id):
    set_parent_whatsapp(conn, parent_id, WHATSAPP)
    run_outbound(conn, both_routes(), at(11, 0))
    assert record_inbound(conn, f"whatsapp:{WHATSAPP}", "", at(11, 30)) is True
    assert replied(conn, parent_id) is True


def test_the_same_digits_in_both_columns_resolve_by_channel(conn):
    """Two parents: one has the number as phone, the other as WhatsApp. A
    bare sender is the phone parent; a prefixed one is the WhatsApp parent."""
    provisioned = provision_family(
        conn,
        "Sharma",
        "Asia/Kolkata",
        [("Amma", None, "Mom"), ("Appa", None, "Dad")],
        base_url=BASE_URL,
    )
    add_child_email(conn, provisioned.family_id)
    amma, appa = (p.parent_id for p in provisioned.parents)
    set_parent_phone(conn, amma, US_PHONE)
    consent(conn, amma)
    set_parent_whatsapp(conn, appa, US_PHONE)
    run_outbound(conn, both_routes(), at(11, 0))

    assert record_inbound(conn, f"whatsapp:{US_PHONE}", None, at(11, 30)) is True
    assert replied(conn, appa) is True and replied(conn, amma) is False
    assert record_inbound(conn, US_PHONE, None, at(11, 31)) is True
    assert replied(conn, amma) is True


def test_the_endpoint_passes_the_opt_out_type_through_content_blind(
    settings, notifier, conn, parent_id, caplog
):
    """A Twilio-signed STOP, the Wave C production shape: the body is
    verified as part of the signature and then discarded; the keyword is
    read from OptOutType, never from the body."""
    import logging
    from dataclasses import replace

    from fastapi.testclient import TestClient

    from kettle.main import create_app
    from kettle.twilio_signature import expected_signature

    pending_sms_ask(conn, parent_id)
    url = f"{settings.public_base_url}/outbound/reply"
    cfg = replace(settings, outbound_reply_token="", twilio_auth_token=TOKEN)
    params = {
        "From": US_PHONE,
        "Body": "STOP please, my knee hurts",
        "OptOutType": "STOP",
        "SmsSid": "SM1",
    }
    with (
        TestClient(create_app(cfg, notifier, clock=lambda: at(11, 30))) as c,
        caplog.at_level(logging.INFO),
    ):
        response = c.post(
            "/outbound/reply",
            content=urlencode(params),
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "X-Twilio-Signature": expected_signature(TOKEN, url, params),
            },
        )
    assert response.status_code == 204
    assert replied(conn, parent_id) is False
    assert sms_state(conn, parent_id) is not None
    assert "knee" not in caplog.text
    assert "knee" not in " ".join(notifier.messages)


def test_the_signature_still_covers_sms_shaped_params(settings, notifier, conn, parent_id):
    """OptOutType is inside the signed form like any other field: a tampered
    keyword fails the check and changes nothing."""
    from dataclasses import replace

    from fastapi.testclient import TestClient

    from kettle.main import create_app
    from kettle.twilio_signature import expected_signature

    pending_sms_ask(conn, parent_id)
    url = f"{settings.public_base_url}/outbound/reply"
    cfg = replace(settings, outbound_reply_token="", twilio_auth_token=TOKEN)
    signed = {"From": US_PHONE, "Body": "ok", "SmsSid": "SM1"}
    sent = {**signed, "OptOutType": "STOP"}
    with TestClient(create_app(cfg, notifier, clock=lambda: at(11, 30))) as c:
        response = c.post(
            "/outbound/reply",
            content=urlencode(sent),
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "X-Twilio-Signature": expected_signature(TOKEN, url, signed),
            },
        )
    assert response.status_code == 403
    assert sms_state(conn, parent_id) is None
    assert replied(conn, parent_id) is False


# --- A.7 the consent function -----------------------------------------------------


def consent_utc(conn, parent_id):
    return conn.execute(
        "select sms_consent_utc from parents where id = %s", (parent_id,)
    ).fetchone()["sms_consent_utc"]


def test_a_member_cannot_record_consent(family, parent_id, authed, conn):
    set_parent_phone(conn, parent_id, US_PHONE)
    as_user(authed, MEMBER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_admin"):
        authed.execute("select public.app_sms_consent(%s)", (parent_id,))
    assert consent_utc(conn, parent_id) is None


def test_an_admin_records_consent_once(family, parent_id, authed, conn):
    set_parent_phone(conn, parent_id, US_PHONE)
    as_user(authed, ADMIN)
    authed.execute("select public.app_sms_consent(%s)", (parent_id,))
    first = consent_utc(conn, parent_id)
    assert first is not None
    authed.execute("select public.app_sms_consent(%s)", (parent_id,))
    assert consent_utc(conn, parent_id) == first


def test_consent_is_refused_for_a_parent_with_a_whatsapp_number(family, parent_id, authed, conn):
    set_parent_phone(conn, parent_id, US_PHONE)
    set_parent_whatsapp(conn, parent_id, WHATSAPP)
    as_user(authed, ADMIN)
    with pytest.raises(psycopg.errors.CheckViolation, match="has_whatsapp"):
        authed.execute("select public.app_sms_consent(%s)", (parent_id,))
    assert consent_utc(conn, parent_id) is None


def test_consent_is_refused_for_a_non_us_phone_or_no_phone(family, parent_id, authed, conn):
    as_user(authed, ADMIN)
    for phone in (None, UK_PHONE):
        set_parent_phone(conn, parent_id, phone)
        with pytest.raises(psycopg.errors.CheckViolation, match="not_a_us_number"):
            authed.execute("select public.app_sms_consent(%s)", (parent_id,))
    assert consent_utc(conn, parent_id) is None


def test_a_stranger_cannot_consent_for_someone_elses_parent(family, parent_id, authed, conn):
    set_parent_phone(conn, parent_id, US_PHONE)
    as_user(authed, "33333333-3333-3333-3333-333333333333")
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_admin"):
        authed.execute("select public.app_sms_consent(%s)", (parent_id,))


def test_the_sms_columns_are_not_client_writable(family, parent_id, authed):
    as_user(authed, ADMIN)
    for column in ("sms_consent_utc", "sms_opted_out_utc"):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            authed.execute(f"update parents set {column} = now() where id = %s", (parent_id,))


def test_anon_cannot_execute_the_consent_function(conn):
    row = conn.execute(
        "select has_function_privilege('anon', 'public.app_sms_consent(uuid)', 'execute') as a, "
        "has_function_privilege('authenticated', 'public.app_sms_consent(uuid)', 'execute') as u"
    ).fetchone()
    assert (row["a"], row["u"]) == (False, True)
