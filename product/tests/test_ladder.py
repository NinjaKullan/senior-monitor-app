"""Acceptance criteria 1, 3, 4, 5 — the escalation ladder.

AC4 is the one that matters most: in shadow mode the full ladder runs, records
and reports, and the channel abstraction is never invoked. Every test here uses
a channel that counts its own calls, so "zero sends" is asserted against the
object that would have done the sending rather than against a log line.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import psycopg
import pytest

from kettle import db
from kettle.ladder import (
    RESOLVED_BY_ACTIVITY,
    STAGE_ASK,
    STAGE_ASK_SKIPPED,
    STAGE_CANDIDATE,
    STAGE_FAMILY_1,
    STAGE_FAMILY_ALL,
    STAGE_RESOLVED,
    TRIGGER_DEADLINE,
    TRIGGER_MAX_GAP,
    run_ladder,
)
from kettle.provisioning import provision_family
from scripts.ladder import main as ladder_cli
from testsupport import BASE_URL, enable_digests, enable_ladder, set_senior_phone

IST = ZoneInfo("Asia/Kolkata")
CHICAGO = ZoneInfo("America/Chicago")

SENIOR_PHONE = "+919845550001"
MORNING = datetime(2026, 8, 3, 8, 0, tzinfo=IST)
NOON = datetime(2026, 8, 3, 12, 0, tzinfo=IST)
AFTERNOON = datetime(2026, 8, 3, 14, 0, tzinfo=IST)


class CountingChannel:
    """Counts every invocation. Shadow mode must never reach this object."""

    name = "sms"
    available = True

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send(self, to_e164: str, message: str) -> bool:
        self.sent.append((to_e164, message))
        return True


@pytest.fixture
def channel() -> CountingChannel:
    return CountingChannel()


@pytest.fixture
def channels(channel: CountingChannel) -> dict:
    return {"sms": channel, "whatsapp": channel}


def _family(conn, parents, tz="Asia/Kolkata", name="Sharma"):
    return provision_family(conn, name, tz, parents, base_url=BASE_URL)


def _ping(conn, parent_id, signal, when) -> None:
    db.insert_ping(conn, parent_id, signal, when, None)


def _events(conn) -> list[str]:
    return [
        r["stage"]
        for r in conn.execute(
            "select stage from ladder_events order by id"
        ).fetchall()
    ]


def _candidate(conn) -> dict:
    return conn.execute("select * from ladder_candidates").fetchone()


def _armed(
    conn, mode="shadow", parents=(("Amma", None),), with_phone=True, phone_alive=True
):
    """A family with the ladder on and a parent who has done nothing today.

    `phone_alive` inserts a timer ping, which is the ordinary case: the handset
    is fine and reporting, the person simply has not opened anything. Pass False
    for the genuinely-unreachable case, where mechanism_ok goes to False and the
    ask is skipped.
    """
    family = _family(conn, list(parents))
    # No members here: each test adds exactly the recipients it means to have,
    # so the escalation order under test is the one the test wrote down.
    enable_ladder(conn, family.family_id, mode)
    if with_phone:
        set_senior_phone(conn, family.parents[0].parent_id, SENIOR_PHONE)
    if phone_alive:
        for parent in family.parents:
            _ping(conn, parent.parent_id, "device_alive", MORNING)
    return family


# --- AC4: the mode gates ----------------------------------------------------


def test_shadow_never_touches_a_channel(conn, settings, channels, channel, notifier):
    """AC4, the one that matters: a full ladder walk with zero channel calls.

    Candidate → ask → family_1 → family_all, every stage recorded, the founder
    told at each one, and `CountingChannel` never invoked once.
    """
    family = _armed(conn, "shadow")
    parent = family.parents[0]
    enable_digests(conn, family.family_id, [("Child", "+15125550100"), ("Sis", "+15125550101")])

    run_ladder(conn, settings, channels, notifier, NOON)  # candidate + ask
    run_ladder(conn, settings, channels, notifier, NOON + timedelta(minutes=95))
    run_ladder(conn, settings, channels, notifier, NOON + timedelta(minutes=160))

    assert _events(conn) == [
        STAGE_CANDIDATE, STAGE_ASK, STAGE_FAMILY_1, STAGE_FAMILY_ALL,
    ]
    # The whole point.
    assert channel.sent == []
    assert all(r["mode"] == "shadow" for r in conn.execute(
        "select mode from ladder_events").fetchall())

    # The founder heard about every one of them.
    assert len(notifier.messages) == 4
    assert all(m.startswith("[SHADOW Sharma]") for m in notifier.messages)
    assert parent.display_name in notifier.messages[0]


def test_off_evaluates_nothing(conn, settings, channels, channel, notifier):
    """AC4: `off` is the default and it means no evaluation at all."""
    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id)
    set_senior_phone(conn, family.parents[0].parent_id, SENIOR_PHONE)

    assert conn.execute("select ladder_mode from families").fetchone()["ladder_mode"] == "off"
    assert run_ladder(conn, settings, channels, notifier, NOON) == []
    assert _candidate(conn) is None
    assert channel.sent == []
    assert notifier.messages == []


def test_global_kill_switch_overrides_every_family(conn, settings, channels, channel, notifier):
    """AC4: LADDER_ENABLED=0 silences even a live family."""
    from dataclasses import replace

    _armed(conn, "live")
    off = replace(settings, ladder_enabled=False)
    assert run_ladder(conn, off, channels, notifier, NOON) == []
    assert _candidate(conn) is None
    assert channel.sent == []


def test_live_requires_digests_at_the_database_level(conn):
    """AC4: the precondition is a CHECK, not a habit of whoever runs the CLI."""
    family = _family(conn, [("Amma", None)])
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "update families set ladder_mode = 'live' where id = %s", (family.family_id,)
        )


def test_live_sends_for_real(conn, settings, channels, channel, notifier):
    """The other side of AC4: live mode does reach the channel."""
    family = _armed(conn, "live")
    enable_digests(conn, family.family_id, [("Child", "+15125550100")])

    run_ladder(conn, settings, channels, notifier, NOON)
    assert len(channel.sent) == 1
    to, message = channel.sent[0]
    assert to == SENIOR_PHONE  # the ask goes to the senior, and only the ask
    assert "All good? Reply YES." in message


# --- AC1: rule v1 -----------------------------------------------------------


def test_deadline_branch_fires_at_the_parents_deadline(conn, settings, channels, notifier):
    """AC1: nothing alarm-grade since 05:00 and the personal deadline has passed."""
    family = _armed(conn, "shadow")
    enable_digests(conn, family.family_id)

    # 11:59 — one minute early, nothing yet.
    assert run_ladder(
        conn, settings, channels, notifier, datetime(2026, 8, 3, 11, 59, tzinfo=IST)
    ) == []
    assert _candidate(conn) is None

    run_ladder(conn, settings, channels, notifier, NOON)
    candidate = _candidate(conn)
    assert candidate["trigger"] == TRIGGER_DEADLINE
    assert candidate["parent_id"] == family.parents[0].parent_id


def test_deadline_branch_respects_a_custom_deadline(conn, settings, channels, notifier):
    """The thresholds are per-parent columns — analysis updates rows, not code."""
    family = _armed(conn, "shadow")
    conn.execute(
        "update parents set alarm_deadline = '10:00' where id = %s",
        (family.parents[0].parent_id,),
    )
    run_ladder(conn, settings, channels, notifier, datetime(2026, 8, 3, 10, 1, tzinfo=IST))
    assert _candidate(conn)["trigger"] == TRIGGER_DEADLINE


def test_morning_activity_stands_the_deadline_branch_down(conn, settings, channels, notifier):
    family = _armed(conn, "shadow")
    _ping(conn, family.parents[0].parent_id, "whatsapp", MORNING)
    assert run_ladder(conn, settings, channels, notifier, NOON) == []
    assert _candidate(conn) is None


def test_max_gap_branch_fires_on_a_long_silence(conn, settings, channels, notifier):
    """AC1: the second branch — active this morning, then silent past the gap."""
    family = _armed(conn, "shadow")
    parent = family.parents[0]
    conn.execute(
        "update parents set alarm_deadline = '23:00', max_gap_minutes = 240 "
        "where id = %s",
        (parent.parent_id,),
    )
    _ping(conn, parent.parent_id, "whatsapp", datetime(2026, 8, 3, 6, 0, tzinfo=IST))

    # 3h later: inside the gap.
    assert run_ladder(
        conn, settings, channels, notifier, datetime(2026, 8, 3, 9, 0, tzinfo=IST)
    ) == []
    # 5h later: past it.
    run_ladder(conn, settings, channels, notifier, datetime(2026, 8, 3, 11, 30, tzinfo=IST))
    assert _candidate(conn)["trigger"] == TRIGGER_MAX_GAP


def test_nothing_fires_outside_the_daytime_window(conn, settings, channels, notifier):
    """AC1: candidates open between 05:00 and 21:00 local, and not otherwise."""
    _armed(conn, "shadow")
    for hour in (0, 3, 4, 21, 22, 23):
        moment = datetime(2026, 8, 3, hour, 30, tzinfo=IST)
        assert run_ladder(conn, settings, channels, notifier, moment) == []
    assert _candidate(conn) is None


def test_one_candidate_per_parent_per_local_day(conn, settings, channels, notifier):
    """AC1: a resolved candidate does not re-arm the same day in v1."""
    family = _armed(conn, "shadow")
    parent = family.parents[0]

    run_ladder(conn, settings, channels, notifier, NOON)
    _ping(conn, parent.parent_id, "whatsapp", datetime(2026, 8, 3, 12, 30, tzinfo=IST))
    run_ladder(conn, settings, channels, notifier, datetime(2026, 8, 3, 12, 35, tzinfo=IST))
    assert _candidate(conn)["resolution"] == RESOLVED_BY_ACTIVITY

    # Silent again all afternoon: still no second candidate today.
    run_ladder(conn, settings, channels, notifier, datetime(2026, 8, 3, 20, 0, tzinfo=IST))
    assert conn.execute(
        "select count(*) as n from ladder_candidates"
    ).fetchone()["n"] == 1

    # Tomorrow is a new day.
    run_ladder(conn, settings, channels, notifier, datetime(2026, 8, 4, 12, 0, tzinfo=IST))
    assert conn.execute(
        "select count(*) as n from ladder_candidates"
    ).fetchone()["n"] == 2


def test_each_parent_is_evaluated_on_their_own_clock(conn, settings, channels, notifier):
    """A parent visiting Chicago gets their deadline on Chicago's noon."""
    family = _family(conn, [("Amma", "America/Chicago"), ("Appa", None)])
    enable_digests(conn, family.family_id)
    enable_ladder(conn, family.family_id, "shadow")
    amma, appa = family.parents

    run_ladder(conn, settings, channels, notifier, NOON)  # noon IST
    assert [r["parent_id"] for r in conn.execute(
        "select parent_id from ladder_candidates").fetchall()] == [appa.parent_id]

    run_ladder(conn, settings, channels, notifier, datetime(2026, 8, 3, 12, 0, tzinfo=CHICAGO))
    assert {r["parent_id"] for r in conn.execute(
        "select parent_id from ladder_candidates").fetchall()} == {
        amma.parent_id, appa.parent_id
    }


# --- AC3: the stage walk ----------------------------------------------------


def test_grace_expiry_walks_family_1_then_family_all(conn, settings, channels, channel, notifier):
    """AC3: the stages fire in order, at the configured gaps, to the right people."""
    family = _armed(conn, "live")
    enable_digests(
        conn,
        family.family_id,
        [("Child", "+15125550100"), ("Sis", "+15125550101"), ("Bro", "+15125550102")],
    )

    run_ladder(conn, settings, channels, notifier, NOON)
    assert [to for to, _ in channel.sent] == [SENIOR_PHONE]

    # 89 minutes: still inside grace.
    run_ladder(conn, settings, channels, notifier, NOON + timedelta(minutes=89))
    assert len(channel.sent) == 1

    # 91 minutes: FAMILY-1, the owner only.
    run_ladder(conn, settings, channels, notifier, NOON + timedelta(minutes=91))
    assert [to for to, _ in channel.sent][1:] == ["+15125550100"]

    # +59 more: still inside the family gap.
    run_ladder(conn, settings, channels, notifier, NOON + timedelta(minutes=150))
    assert len(channel.sent) == 2

    # +61: FAMILY-ALL, the remaining members.
    run_ladder(conn, settings, channels, notifier, NOON + timedelta(minutes=152))
    assert [to for to, _ in channel.sent][2:] == ["+15125550101", "+15125550102"]
    assert _events(conn) == [
        STAGE_CANDIDATE, STAGE_ASK, STAGE_FAMILY_1, STAGE_FAMILY_ALL,
    ]


def test_activity_resolves_and_sends_one_all_clear(conn, settings, channels, channel, notifier):
    """AC3: a ping at any stage resolves; a told family gets exactly one all-clear."""
    family = _armed(conn, "live")
    enable_digests(conn, family.family_id, [("Child", "+15125550100")])
    parent = family.parents[0]

    run_ladder(conn, settings, channels, notifier, NOON)
    run_ladder(conn, settings, channels, notifier, NOON + timedelta(minutes=95))
    sends_before = len(channel.sent)

    _ping(conn, parent.parent_id, "whatsapp", NOON + timedelta(minutes=100))
    run_ladder(conn, settings, channels, notifier, NOON + timedelta(minutes=101))

    assert _candidate(conn)["resolution"] == RESOLVED_BY_ACTIVITY
    assert len(channel.sent) == sends_before + 1
    assert channel.sent[-1][1] == "Kettle: Amma's routine has resumed. All normal."

    # And nothing further, ever.
    run_ladder(conn, settings, channels, notifier, NOON + timedelta(minutes=200))
    assert len(channel.sent) == sends_before + 1
    assert _events(conn)[-1] == STAGE_RESOLVED


def test_resolution_before_the_family_knew_sends_no_all_clear(
    conn, settings, channels, channel, notifier
):
    """Nobody gets an all-clear for an alarm they were never told about."""
    family = _armed(conn, "live")
    enable_digests(conn, family.family_id, [("Child", "+15125550100")])
    parent = family.parents[0]

    run_ladder(conn, settings, channels, notifier, NOON)  # ask only
    _ping(conn, parent.parent_id, "whatsapp", NOON + timedelta(minutes=10))
    run_ladder(conn, settings, channels, notifier, NOON + timedelta(minutes=11))

    assert [to for to, _ in channel.sent] == [SENIOR_PHONE]
    assert _candidate(conn)["resolution"] == RESOLVED_BY_ACTIVITY


# --- AC5: mechanism_ok discrimination ---------------------------------------


def test_timer_flowing_means_the_ask_proceeds(conn, settings, channels, channel, notifier):
    """AC5: apps silent but the phone alive — ask the senior."""
    family = _armed(conn, "live")
    enable_digests(conn, family.family_id, [("Child", "+15125550100")])
    _ping(conn, family.parents[0].parent_id, "device_alive", MORNING)

    run_ladder(conn, settings, channels, notifier, NOON)
    candidate = _candidate(conn)
    assert candidate["mechanism_ok"] is True
    assert candidate["stage"] == STAGE_ASK
    assert channel.sent[0][0] == SENIOR_PHONE


def test_nothing_flowing_skips_the_ask_and_uses_the_unreachable_copy(
    conn, settings, channels, channel, notifier
):
    """AC5: you cannot ask a dead phone, and the family copy says what is known."""
    family = _armed(conn, "live", phone_alive=False)
    enable_digests(conn, family.family_id, [("Child", "+15125550100")])

    run_ladder(conn, settings, channels, notifier, NOON)
    candidate = _candidate(conn)
    assert candidate["mechanism_ok"] is False
    assert _events(conn) == [STAGE_CANDIDATE, STAGE_ASK_SKIPPED, STAGE_FAMILY_1]

    assert SENIOR_PHONE not in [to for to, _ in channel.sent]
    assert channel.sent[-1][0] == "+15125550100"
    assert "unreachable today" in channel.sent[-1][1]


def test_unreachable_in_shadow_still_tells_only_the_founder(
    conn, settings, channels, channel, notifier
):
    """AC5, shadow half: the founder is alerted, nobody else is."""
    family = _armed(conn, "shadow", phone_alive=False)
    enable_digests(conn, family.family_id, [("Child", "+15125550100")])

    run_ladder(conn, settings, channels, notifier, NOON)
    assert channel.sent == []
    assert any("check-in skipped" in m for m in notifier.messages)
    assert all(m.startswith("[SHADOW") for m in notifier.messages)


def test_no_senior_phone_skips_the_ask(conn, settings, channels, channel, notifier):
    """No number on file is a skip to the family stage, not a dead end."""
    family = _armed(conn, "live", with_phone=False)
    enable_digests(conn, family.family_id, [("Child", "+15125550100")])
    _ping(conn, family.parents[0].parent_id, "device_alive", MORNING)

    run_ladder(conn, settings, channels, notifier, NOON)
    assert _events(conn) == [STAGE_CANDIDATE, STAGE_ASK_SKIPPED, STAGE_FAMILY_1]
    assert any("no phone number on file" in m for m in notifier.messages)
    assert [to for to, _ in channel.sent] == ["+15125550100"]


def test_named_contact_is_suggested_at_family_all_only(
    conn, settings, channels, channel, notifier
):
    """RESPONDER-INFO v1: a suggestion in the copy. No call, no SMS to them."""
    family = _armed(conn, "live")
    enable_digests(
        conn, family.family_id, [("Child", "+15125550100"), ("Sis", "+15125550101")]
    )
    conn.execute(
        "insert into family_contacts (family_id, name, phone_e164, relation) "
        "values (%s, 'Priya', '+919845557777', 'neighbour')",
        (family.family_id,),
    )

    run_ladder(conn, settings, channels, notifier, NOON)
    run_ladder(conn, settings, channels, notifier, NOON + timedelta(minutes=95))
    assert "Priya" not in channel.sent[-1][1]  # FAMILY-1 carries no contact line

    run_ladder(conn, settings, channels, notifier, NOON + timedelta(minutes=160))
    assert "Priya (neighbour)" in channel.sent[-1][1]

    # The contact themselves is never messaged.
    assert "+919845557777" not in [to for to, _ in channel.sent]


# --- the mode CLI: where privilege escalation actually happens ---------------


def test_cli_lists_and_sets_modes(conn, database_url, capsys):
    """Mode changes happen here, deliberately, one family at a time."""
    family = _family(conn, [("Amma", None)])
    assert ladder_cli(["--list", "--database-url", database_url]) == 0
    assert "Sharma" in capsys.readouterr().out

    assert ladder_cli(["--set-mode", "Sharma", "shadow", "--database-url", database_url]) == 0
    out = capsys.readouterr().out
    assert "off -> shadow" in out
    assert "No message reaches the senior or the family" in out
    assert conn.execute("select ladder_mode from families").fetchone()["ladder_mode"] == "shadow"
    del family


def test_cli_refuses_live_without_digests(conn, database_url, capsys):
    """AC4: the CLI reports the database's refusal rather than working around it."""
    _family(conn, [("Amma", None)])
    assert ladder_cli(["--set-mode", "Sharma", "live", "--database-url", database_url]) == 1
    assert "cannot go live while digests are off" in capsys.readouterr().err
    assert conn.execute("select ladder_mode from families").fetchone()["ladder_mode"] == "off"


def test_cli_allows_live_once_digests_are_on(conn, database_url, capsys):
    family = _family(conn, [("Amma", None)])
    enable_digests(conn, family.family_id)
    assert ladder_cli(["--set-mode", "Sharma", "live", "--database-url", database_url]) == 0
    assert "REAL SENDS ARE NOW ON" in capsys.readouterr().out


def test_cli_manual_resolve_requires_a_note(
    conn, settings, channels, notifier, database_url, capsys
):
    """The ledger is the point of the ladder, so a manual close explains itself."""
    family = _armed(conn, "shadow")
    enable_digests(conn, family.family_id)
    run_ladder(conn, settings, channels, notifier, NOON)
    candidate_id = _candidate(conn)["id"]

    with pytest.raises(SystemExit):
        ladder_cli(["--resolve", str(candidate_id), "--database-url", database_url])

    assert ladder_cli(
        ["--resolve", str(candidate_id), "--note", "called Amma, she is fine",
         "--database-url", database_url]
    ) == 0
    assert "resolved manually" in capsys.readouterr().out

    candidate = _candidate(conn)
    assert candidate["resolution"] == "resolved_manually"
    detail = conn.execute(
        "select detail from ladder_events order by id desc limit 1"
    ).fetchone()["detail"]
    assert "called Amma, she is fine" in detail

    # Already closed: refuse rather than double-resolve.
    assert ladder_cli(
        ["--resolve", str(candidate_id), "--note", "again", "--database-url", database_url]
    ) == 1
