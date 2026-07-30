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
    OPS_SKIPPED,
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
    assert [s.kind for s in evening] == [KIND_EVENING]
    assert len(channel.sent) == 1
    assert channel.sent[0][1] == "Amma and Appa both had normal, active days."
    # Aggregated rows carry no parent_id, matching the unique index.
    row = conn.execute(
        "select * from digest_sends where kind = 'evening'"
    ).fetchone()
    assert row["parent_id"] is None


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
