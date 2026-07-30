"""Acceptance criteria 1, 2, 3, 5, 6 — the digest scheduler.

Idempotency is the load-bearing property here, so the restart cases get the same
weight as the happy path: the scheduler must ask the database what it has sent,
never its own memory.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import psycopg
import pytest

from kettle import db
from kettle.channels import DigestChannel
from kettle.digest import (
    KIND_EVENING,
    KIND_MORNING,
    OPS_CHANNEL_UNAVAILABLE,
    OPS_SKIPPED,
    OPS_UNROUTABLE,
    STATUS_SENT,
    run_digests,
)
from kettle.provisioning import provision_family
from testsupport import BASE_URL, enable_digests

IST = ZoneInfo("Asia/Kolkata")
CHICAGO = ZoneInfo("America/Chicago")

MORNING_PING = datetime(2026, 8, 3, 8, 12, tzinfo=IST)
MID_MORNING = datetime(2026, 8, 3, 9, 0, tzinfo=IST)
EVENING = datetime(2026, 8, 3, 20, 30, tzinfo=IST)
LATE_EVENING = datetime(2026, 8, 3, 22, 0, tzinfo=IST)


class RecordingChannel:
    """A DigestChannel that records instead of sending."""

    name = "sms"
    available = True

    def __init__(self, succeed: bool = True) -> None:
        self.succeed = succeed
        self.sent: list[tuple[str, str]] = []

    def send(self, to_e164: str, message: str) -> bool:
        self.sent.append((to_e164, message))
        return self.succeed


@pytest.fixture
def channel() -> RecordingChannel:
    return RecordingChannel()


@pytest.fixture
def channels(channel: RecordingChannel) -> dict[str, DigestChannel]:
    return {"sms": channel, "whatsapp": channel}


def _family(conn: psycopg.Connection, parents, tz: str = "Asia/Kolkata", name="Sharma"):
    return provision_family(conn, name, tz, parents, base_url=BASE_URL)


def _ping(conn, parent_id, signal: str, when: datetime) -> None:
    db.insert_ping(conn, parent_id, signal, when, None)


def _rows(conn) -> list[dict]:
    return conn.execute(
        "select * from digest_sends order by kind, local_date, id"
    ).fetchall()


# --- AC1: morning, and the idempotency that survives restarts ---------------


def test_morning_sends_once_per_recipient(conn, settings, channels, channel, notifier):
    """AC1: first ping at 08:12 local produces exactly one message per recipient."""
    family = _family(conn, [("Amma", None)])
    enable_digests(
        conn,
        family.family_id,
        [("Child", "+15125550100"), ("Sister", "+15125550101")],
    )
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    sent = run_digests(conn, settings, channels, notifier, MID_MORNING)

    assert len(sent) == 2
    assert {s.kind for s in sent} == {KIND_MORNING}
    assert len(channel.sent) == 2
    assert {to for to, _ in channel.sent} == {"+15125550100", "+15125550101"}
    for _, message in channel.sent:
        assert "Amma" in message
        assert "day started normally" in message
    assert [r["status"] for r in _rows(conn)] == [STATUS_SENT, STATUS_SENT]


def test_second_ping_and_repeat_pass_do_not_resend(
    conn, settings, channels, channel, notifier
):
    """AC1: more pings and more passes are not more messages."""
    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id)
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    run_digests(conn, settings, channels, notifier, MID_MORNING)
    _ping(conn, family.parents[0].parent_id, "youtube", MID_MORNING)
    assert run_digests(conn, settings, channels, notifier, MID_MORNING) == []
    assert (
        run_digests(conn, settings, channels, notifier, MID_MORNING + timedelta(hours=1))
        == []
    )

    assert len(channel.sent) == 1
    assert len(_rows(conn)) == 1


def test_restart_does_not_double_send(conn, settings, channels, notifier, database_url):
    """AC1: idempotency is in the database, not in process memory.

    Simulated by running the second pass on a brand-new connection with no shared
    state — the same thing a redeploy does.
    """
    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id)
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    first_channel = RecordingChannel()
    run_digests(
        conn, settings, {"sms": first_channel, "whatsapp": first_channel}, notifier,
        MID_MORNING,
    )
    assert len(first_channel.sent) == 1

    with db.connect(database_url) as reborn:
        after_restart = RecordingChannel()
        sent = run_digests(
            reborn,
            settings,
            {"sms": after_restart, "whatsapp": after_restart},
            notifier,
            MID_MORNING + timedelta(minutes=1),
        )
        assert sent == []
        assert after_restart.sent == []

    assert len(_rows(conn)) == 1


def test_recording_the_send_is_what_blocks_a_duplicate(conn, settings, notifier):
    """The unique index is the guard, not a check-then-send window.

    A channel that crashes the process after delivering would leave no row — so
    the row is claimed with `on conflict do nothing`, and this asserts a second
    attempt at the same slot cannot insert.
    """
    family = _family(conn, [("Amma", None)])
    members = enable_digests(conn, family.family_id)
    local_date = MORNING_PING.date()

    assert db.record_digest_send(
        conn, family.family_id, family.parents[0].parent_id, KIND_MORNING,
        local_date, members[0]["member_id"], "sms", STATUS_SENT, MID_MORNING,
    )
    assert not db.record_digest_send(
        conn, family.family_id, family.parents[0].parent_id, KIND_MORNING,
        local_date, members[0]["member_id"], "sms", STATUS_SENT, MID_MORNING,
    )


# --- AC2: no evidence, no message ------------------------------------------


def test_no_ping_means_no_morning_message_ever(conn, settings, channels, channel, notifier):
    """AC2: a silent morning produces silence, not a manufactured reassurance."""
    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id)

    for hour in (6, 8, 10, 12, 13):
        moment = datetime(2026, 8, 3, hour, 0, tzinfo=IST)
        assert run_digests(conn, settings, channels, notifier, moment) == []
    assert channel.sent == []
    assert _rows(conn) == []


def test_first_ping_after_cutoff_gets_no_morning_but_still_counts_at_night(
    conn, settings, channels, channel, notifier
):
    """AC2: a 15:00 start is not a 'good morning'; the evening still counts it."""
    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id)
    _ping(conn, family.parents[0].parent_id, "whatsapp", datetime(2026, 8, 3, 15, 0, tzinfo=IST))

    just_after = datetime(2026, 8, 3, 15, 5, tzinfo=IST)
    assert run_digests(conn, settings, channels, notifier, just_after) == []
    assert channel.sent == []

    evening = run_digests(conn, settings, channels, notifier, EVENING)
    assert [s.kind for s in evening] == [KIND_EVENING]
    assert "Amma had a normal, active day." in channel.sent[-1][1]


def test_morning_is_not_sent_late_even_when_the_ping_was_early(
    conn, settings, channels, channel, notifier
):
    """A server down until dinnertime must not deliver a stale 'good morning'."""
    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id)
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    late = datetime(2026, 8, 3, 18, 0, tzinfo=IST)
    mornings = [
        s
        for s in run_digests(conn, settings, channels, notifier, late)
        if s.kind == KIND_MORNING
    ]
    assert mornings == []


def test_only_alarm_grade_pings_start_the_day(conn, settings, channels, channel, notifier):
    """A timer ping is plumbing; it cannot vouch that someone's day started."""
    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id)
    _ping(conn, family.parents[0].parent_id, "device_alive", datetime(2026, 8, 3, 7, 0, tzinfo=IST))
    _ping(conn, family.parents[0].parent_id, "charge_off", datetime(2026, 8, 3, 7, 30, tzinfo=IST))

    assert run_digests(conn, settings, channels, notifier, MID_MORNING) == []
    assert channel.sent == []


# --- AC3: evening -----------------------------------------------------------


def test_evening_aggregates_active_parents(conn, settings, channels, channel, notifier):
    """AC3: two active parents, one message per recipient."""
    family = _family(conn, [("Amma", None), ("Appa", None)])
    enable_digests(conn, family.family_id)
    for parent in family.parents:
        _ping(conn, parent.parent_id, "whatsapp", MORNING_PING)

    run_digests(conn, settings, channels, notifier, MID_MORNING)  # mornings first
    channel.sent.clear()

    evening = run_digests(conn, settings, channels, notifier, EVENING)

    # One message delivered, one row per parent it vouched for (PM ruling on
    # item 27) — so the audit says who a given send covered.
    assert len(channel.sent) == 1
    assert channel.sent[0][1] == "Amma and Appa both had normal, active days."
    assert {s.kind for s in evening} == {KIND_EVENING}
    assert {s.parent_id for s in evening} == {p.parent_id for p in family.parents}

    rows = conn.execute(
        "select * from digest_sends where kind = 'evening'"
    ).fetchall()
    assert len(rows) == 2
    assert all(r["parent_id"] is not None for r in rows)
    assert {r["parent_id"] for r in rows} == {p.parent_id for p in family.parents}


def test_quiet_parent_is_omitted_and_reported_to_the_founder(
    conn, settings, channels, channel, notifier
):
    """AC3: the family hears about the active parent only; the founder hears the rest."""
    family = _family(conn, [("Amma", None), ("Appa", None)])
    enable_digests(conn, family.family_id)
    amma, appa = family.parents
    _ping(conn, amma.parent_id, "whatsapp", MORNING_PING)

    run_digests(conn, settings, channels, notifier, EVENING)

    family_message = channel.sent[-1][1]
    assert family_message == "Amma had a normal, active day."
    assert "Appa" not in family_message

    skipped = conn.execute(
        "select * from ops_alerts where kind = %s", (OPS_SKIPPED,)
    ).fetchall()
    assert len(skipped) == 1
    assert skipped[0]["parent_id"] == appa.parent_id
    assert "Family was not told" in skipped[0]["detail"]


def test_all_parents_quiet_sends_the_family_nothing(
    conn, settings, channels, channel, notifier
):
    """AC3: absence never reaches a family. That is spec 004's, and it is unbuilt."""
    family = _family(conn, [("Amma", None), ("Appa", None)])
    enable_digests(conn, family.family_id)

    assert run_digests(conn, settings, channels, notifier, EVENING) == []
    assert channel.sent == []
    assert _rows(conn) == []
    assert conn.execute(
        "select count(*) as n from ops_alerts where kind = %s", (OPS_SKIPPED,)
    ).fetchone()["n"] == 2


def test_skipped_ops_alert_is_once_per_local_day(conn, settings, channels, notifier):
    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id)

    run_digests(conn, settings, channels, notifier, EVENING)
    run_digests(conn, settings, channels, notifier, LATE_EVENING)
    assert conn.execute(
        "select count(*) as n from ops_alerts where kind = %s", (OPS_SKIPPED,)
    ).fetchone()["n"] == 1


def test_evening_does_not_fire_before_its_hour(conn, settings, channels, channel, notifier):
    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id)
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    just_early = datetime(2026, 8, 3, 20, 29, tzinfo=IST)
    evening = [
        s
        for s in run_digests(conn, settings, channels, notifier, just_early)
        if s.kind == KIND_EVENING
    ]
    assert evening == []


def test_evening_is_idempotent_across_passes_and_restarts(
    conn, settings, channels, channel, notifier, database_url
):
    """AC1 again, for the evening message."""
    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id)
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    run_digests(conn, settings, channels, notifier, EVENING)
    before = len(channel.sent)
    run_digests(conn, settings, channels, notifier, LATE_EVENING)

    with db.connect(database_url) as reborn:
        assert [
            s
            for s in run_digests(reborn, settings, channels, notifier, LATE_EVENING)
            if s.kind == KIND_EVENING
        ] == []

    assert len(channel.sent) == before
    assert (
        conn.execute("select count(*) as n from digest_sends where kind = 'evening'")
        .fetchone()["n"]
        == 1
    )


# --- AC5: timezones ---------------------------------------------------------


def test_parent_tz_override_gets_its_own_clock(conn, settings, channels, channel, notifier):
    """AC5: Chicago parent and IST parent, one family, two schedules."""
    family = _family(conn, [("Amma", "America/Chicago"), ("Appa", None)])
    enable_digests(conn, family.family_id)
    amma, appa = family.parents

    # 08:12 in each parent's own local morning.
    _ping(conn, amma.parent_id, "whatsapp", datetime(2026, 8, 3, 8, 12, tzinfo=CHICAGO))
    _ping(conn, appa.parent_id, "whatsapp", datetime(2026, 8, 3, 8, 12, tzinfo=IST))

    # 09:00 IST — morning for Appa, the middle of the night for Amma.
    sent = run_digests(conn, settings, channels, notifier, MID_MORNING)
    assert [s.parent_id for s in sent] == [appa.parent_id]

    # 09:00 Chicago — now Amma's morning.
    sent = run_digests(
        conn, settings, channels, notifier, datetime(2026, 8, 3, 9, 0, tzinfo=CHICAGO)
    )
    assert [s.parent_id for s in sent] == [amma.parent_id]


def test_evening_follows_each_parents_clock(conn, settings, channels, channel, notifier):
    """AC5: the IST parent's summary lands hours before the Chicago parent's."""
    family = _family(conn, [("Amma", "America/Chicago"), ("Appa", None)])
    enable_digests(conn, family.family_id)
    amma, appa = family.parents
    _ping(conn, amma.parent_id, "whatsapp", datetime(2026, 8, 3, 8, 12, tzinfo=CHICAGO))
    _ping(conn, appa.parent_id, "whatsapp", datetime(2026, 8, 3, 8, 12, tzinfo=IST))

    ist_evening = [
        s
        for s in run_digests(conn, settings, channels, notifier, EVENING)
        if s.kind == KIND_EVENING
    ]
    assert [s.parent_id for s in ist_evening] == [appa.parent_id]
    assert channel.sent[-1][1] == "Appa had a normal, active day."

    chicago_evening = [
        s
        for s in run_digests(
            conn, settings, channels, notifier, datetime(2026, 8, 3, 20, 30, tzinfo=CHICAGO)
        )
        if s.kind == KIND_EVENING
    ]
    assert [s.parent_id for s in chicago_evening] == [amma.parent_id]
    assert channel.sent[-1][1] == "Amma had a normal, active day."


# --- AC6: the two kill-switches --------------------------------------------


def test_family_not_opted_in_gets_nothing(conn, settings, channels, channel, notifier):
    """AC6: digest_enabled defaults false and a full day of activity does not change it."""
    family = _family(conn, [("Amma", None)])
    # Members exist, activity exists — the flag does not.
    conn.execute(
        "insert into members (family_id, display_name, role, phone_e164) "
        "values (%s, 'Child', 'owner', '+15125550100')",
        (family.family_id,),
    )
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    assert conn.execute("select digest_enabled from families").fetchone()["digest_enabled"] is False
    assert run_digests(conn, settings, channels, notifier, MID_MORNING) == []
    assert run_digests(conn, settings, channels, notifier, EVENING) == []
    assert channel.sent == []


def test_global_kill_switch_overrides_everything(conn, settings, channels, channel, notifier):
    """AC6: DIGEST_ENABLED=0 silences even an opted-in, fully active family."""
    from dataclasses import replace

    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id)
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    off = replace(settings, digest_enabled=False)
    assert run_digests(conn, off, channels, notifier, MID_MORNING) == []
    assert run_digests(conn, off, channels, notifier, EVENING) == []
    assert channel.sent == []
    assert _rows(conn) == []


def test_members_opted_out_of_the_channel_are_not_recipients(
    conn, settings, channels, channel, notifier
):
    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id, [("Child", "+15125550100")], channel="none")
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    assert run_digests(conn, settings, channels, notifier, MID_MORNING) == []
    assert channel.sent == []


def test_members_without_a_phone_are_not_recipients(
    conn, settings, channels, channel, notifier
):
    family = _family(conn, [("Amma", None)])
    conn.execute("update families set digest_enabled = true where id = %s", (family.family_id,))
    conn.execute(
        "insert into members (family_id, display_name, role) values (%s, 'Child', 'owner')",
        (family.family_id,),
    )
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    assert run_digests(conn, settings, channels, notifier, MID_MORNING) == []
    assert channel.sent == []


# --- PM rulings on items 27, 29 and 31 -------------------------------------


def test_two_timezone_groups_both_get_their_evening(
    conn, settings, channels, channel, notifier
):
    """Item 27: the collision the coalesce index used to cause is gone.

    Four monitored people, two timezone groups, two active parents in each. Under
    the 0005 shape both groups recorded a null parent_id on the same local_date
    and the second message was silently blocked.
    """
    family = _family(
        conn,
        [
            ("Amma", None),
            ("Appa", None),
            ("Patti", "America/Chicago"),
            ("Thatha", "America/Chicago"),
        ],
    )
    enable_digests(conn, family.family_id)
    for parent in family.parents[:2]:  # the IST pair
        _ping(conn, parent.parent_id, "whatsapp", MORNING_PING)
    for parent in family.parents[2:]:  # the Chicago pair
        _ping(
            conn, parent.parent_id, "whatsapp", datetime(2026, 8, 3, 8, 12, tzinfo=CHICAGO)
        )

    def summaries() -> list[str]:
        # Mornings also fire in this window; the evening copy is what is asserted.
        return [m for _, m in channel.sent if "active day" in m]

    ist_group = [
        s
        for s in run_digests(conn, settings, channels, notifier, EVENING)
        if s.kind == KIND_EVENING
    ]
    assert summaries() == ["Amma and Appa both had normal, active days."]

    chicago_group = [
        s
        for s in run_digests(
            conn, settings, channels, notifier, datetime(2026, 8, 3, 20, 30, tzinfo=CHICAGO)
        )
        if s.kind == KIND_EVENING
    ]
    assert summaries() == [
        "Amma and Appa both had normal, active days.",
        "Patti and Thatha both had normal, active days.",
    ]

    # Four rows, same local_date, all distinct — no sentinel, no collision.
    rows = conn.execute(
        "select parent_id, local_date from digest_sends where kind = 'evening'"
    ).fetchall()
    assert len(rows) == 4
    assert len({r["parent_id"] for r in rows}) == 4
    assert len({r["local_date"] for r in rows}) == 1
    assert len(ist_group) == 2 and len(chicago_group) == 2


def test_whatsapp_members_are_skipped_without_taking_the_slot(
    conn, settings, notifier
):
    """Item 29: no attempt, no failed row, one deduped ops row.

    A failed row would hold the day's slot and eat the first real WhatsApp
    digest on the day the channel goes live.
    """
    from kettle.channels import build_channels

    family = _family(conn, [("Amma", None)])
    enable_digests(
        conn, family.family_id, [("Child", "+919845550100")], channel="whatsapp"
    )
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    assert run_digests(conn, settings, build_channels(settings), notifier, MID_MORNING) == []
    assert _rows(conn) == []  # the slot is still free

    alerts = conn.execute(
        "select * from ops_alerts where kind = %s", (OPS_CHANNEL_UNAVAILABLE,)
    ).fetchall()
    assert len(alerts) == 1
    assert "not live yet" in alerts[0]["detail"]
    assert "no slot" in alerts[0]["detail"]

    # Deduped: once per member per local day, across passes.
    run_digests(conn, settings, build_channels(settings), notifier, EVENING)
    assert (
        conn.execute(
            "select count(*) as n from ops_alerts where kind = %s",
            (OPS_CHANNEL_UNAVAILABLE,),
        ).fetchone()["n"]
        == 1
    )


def test_channel_unavailable_is_per_member(conn, settings, notifier):
    """Two whatsapp members are two distinct ops rows, not one."""
    from kettle.channels import build_channels

    family = _family(conn, [("Amma", None)])
    enable_digests(
        conn,
        family.family_id,
        [("Child", "+919845550100"), ("Sister", "+919845550101")],
        channel="whatsapp",
    )
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    run_digests(conn, settings, build_channels(settings), notifier, MID_MORNING)
    alerts = conn.execute(
        "select detail from ops_alerts where kind = %s order by id",
        (OPS_CHANNEL_UNAVAILABLE,),
    ).fetchall()
    assert len(alerts) == 2
    assert {"Child", "Sister"} == {
        "Child" if "Child" in a["detail"] else "Sister" for a in alerts
    }


def test_enabled_family_with_nowhere_to_send_is_reported(
    conn, settings, channels, channel, notifier
):
    """Item 31: enabled but unreachable is a misconfiguration, not a quiet day."""
    family = _family(conn, [("Amma", None)])
    conn.execute(
        "update families set digest_enabled = true where id = %s", (family.family_id,)
    )
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    assert run_digests(conn, settings, channels, notifier, MID_MORNING) == []
    assert channel.sent == []

    alerts = conn.execute(
        "select * from ops_alerts where kind = %s", (OPS_UNROUTABLE,)
    ).fetchall()
    assert len(alerts) == 1
    assert "no member has both a channel and a phone number" in alerts[0]["detail"]

    # Once per family per local day.
    run_digests(conn, settings, channels, notifier, EVENING)
    assert (
        conn.execute(
            "select count(*) as n from ops_alerts where kind = %s", (OPS_UNROUTABLE,)
        ).fetchone()["n"]
        == 1
    )


def test_a_routable_family_produces_no_unroutable_alert(
    conn, settings, channels, notifier
):
    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id)
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)

    run_digests(conn, settings, channels, notifier, MID_MORNING)
    assert (
        conn.execute(
            "select count(*) as n from ops_alerts where kind = %s", (OPS_UNROUTABLE,)
        ).fetchone()["n"]
        == 0
    )


# --- the senior is never a recipient ---------------------------------------


def test_nothing_is_ever_sent_to_a_parent(conn, settings, channels, channel, notifier):
    """Spec 003 §0: nothing in this spec messages the senior.

    Parents have no contact column at all, so this asserts the structural fact:
    the recipient list comes from `members`, and every number dialled belongs to
    one of them.
    """
    family = _family(conn, [("Amma", None)])
    members = enable_digests(conn, family.family_id)
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING_PING)
    run_digests(conn, settings, channels, notifier, EVENING)

    member_phones = {m["phone_e164"] for m in members}
    assert {to for to, _ in channel.sent} <= member_phones

    parent_columns = {
        r["column_name"]
        for r in conn.execute(
            "select column_name from information_schema.columns "
            "where table_name = 'parents'"
        ).fetchall()
    }
    assert "phone_e164" not in parent_columns
    assert "email" not in parent_columns
