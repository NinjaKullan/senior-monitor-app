"""Spec 020 — the family's own devices, product side (§8).

Ingest answers `ok` to everything token-shaped and records only a live
device's ping once a minute; no engine, heartbeat or roster module names
the table; the functions are admin-only and hold the limit of three; the
family reads the view without the token and the pings of its own circle;
the assistant's `today` carries the card's line as a closed sentence.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
import pytest
from fastapi.testclient import TestClient

from kettle import assistant_copy
from kettle.assistant_tools import device_line, parents_in, today_for
from kettle.main import DEDUPE_WINDOW_S, HOUSEHOLD_SWEEP_DAYS, create_app
from kettle.provisioning import provision_family
from testsupport import BASE_URL, add_child_email, add_member, as_user

ADMIN = "11111111-1111-1111-1111-111111111111"
MEMBER = "22222222-2222-2222-2222-222222222222"
STRANGER = "33333333-3333-3333-3333-333333333333"
IST = ZoneInfo("Asia/Kolkata")
KETTLE = Path(__file__).resolve().parents[1] / "kettle"


class Clock:
    def __init__(self, now: datetime | None = None) -> None:
        self.now = now or datetime(2026, 9, 8, 3, 5, tzinfo=UTC)  # 8:35 am IST

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def api(settings, notifier, conn, clock):
    with TestClient(create_app(settings, notifier, clock)) as c:
        yield c


@pytest.fixture
def family(conn):
    provisioned = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    add_child_email(conn, provisioned.family_id)
    add_member(conn, provisioned.family_id, ADMIN, role="admin")
    add_member(conn, provisioned.family_id, MEMBER, role="member")
    return provisioned


def add_device(conn, parent_id, kind: str = "plug", platform: str | None = "ifttt"):
    """The service role's shortcut to a device row; the function tests below
    go through app_add_household_device as the admin."""
    row = conn.execute(
        "insert into household_devices (parent_id, kind, platform, token) "
        "values (%s, %s, %s, %s) returning id, token",
        (parent_id, kind, platform, f"tok_{kind}_{parent_id.hex[:8]}_{'x' * 12}"),
    ).fetchone()
    return row["id"], row["token"]


def pings_of(conn, device_id) -> list[datetime]:
    return [
        r["ts_utc"]
        for r in conn.execute(
            "select ts_utc from household_pings where device_id = %s order by ts_utc",
            (device_id,),
        ).fetchall()
    ]


# --- ingest (§4) ------------------------------------------------------------------


def test_a_live_token_records_one_row_and_a_duplicate_inside_the_window_none(
    api, conn, family, clock
):
    device_id, token = add_device(conn, family.parents[0].parent_id)
    assert api.get(f"/d/{token}").text == "ok"
    assert pings_of(conn, device_id) == [clock.now]
    clock.now += timedelta(seconds=DEDUPE_WINDOW_S - 1)
    assert api.post(f"/d/{token}").status_code == 200
    assert len(pings_of(conn, device_id)) == 1
    clock.now += timedelta(seconds=2)
    assert api.get(f"/d/{token}?anything=ignored").text == "ok"
    assert len(pings_of(conn, device_id)) == 2


def test_removed_and_unknown_tokens_answer_ok_and_record_nothing(api, conn, family):
    device_id, token = add_device(conn, family.parents[0].parent_id)
    conn.execute("update household_devices set removed_utc = now() where id = %s", (device_id,))
    removed = api.get(f"/d/{token}")
    unknown = api.get(f"/d/{'n' * 32}")
    live_shape = api.get(f"/d/{token}")
    assert (removed.status_code, removed.text) == (200, "ok")
    assert (unknown.status_code, unknown.text) == (200, "ok")
    assert (live_shape.status_code, live_shape.text, dict(live_shape.headers)) == (
        removed.status_code,
        removed.text,
        dict(removed.headers),
    )
    assert conn.execute("select count(*) as n from household_pings").fetchone()["n"] == 0


def test_a_wrong_shaped_token_is_a_404_like_any_unknown_path(api):
    assert api.get("/d/short").status_code == 404
    assert api.get("/d/has%20space%20in%20it%20and%20is%20long").status_code == 404
    assert api.get("/d/").status_code == 404


def test_the_ping_table_has_no_ip_column_to_write(conn):
    columns = {
        r["column_name"]
        for r in conn.execute(
            "select column_name from information_schema.columns "
            "where table_schema = 'public' and table_name = 'household_pings'"
        ).fetchall()
    }
    assert columns == {"id", "device_id", "ts_utc"}


def test_the_route_sweeps_pings_older_than_thirty_days(api, conn, family, clock):
    device_id, token = add_device(conn, family.parents[0].parent_id)
    old = clock.now - timedelta(days=HOUSEHOLD_SWEEP_DAYS, hours=1)
    kept = clock.now - timedelta(days=HOUSEHOLD_SWEEP_DAYS - 1)
    for when in (old, kept):
        conn.execute(
            "insert into household_pings (device_id, ts_utc) values (%s, %s)", (device_id, when)
        )
    api.get(f"/d/{token}")
    assert pings_of(conn, device_id) == [kept, clock.now]


# --- engine isolation (§4, §8) -------------------------------------------------------


def test_no_engine_heartbeat_or_roster_module_names_the_household_table():
    """The ingest route (main.py) and the assistant's today are the only
    readers; a third name here is the engine learning about the house."""
    allowed = {"main.py", "assistant_tools.py"}
    naming = {
        path.name
        for path in KETTLE.glob("*.py")
        if re.search(r"\bhousehold_pings\b", path.read_text())
    }
    assert naming == allowed
    for name in ("outbound.py", "heartbeat.py", "db.py", "outbound_sms.py", "outbound_whatsapp.py"):
        assert "household_devices" not in (KETTLE / name).read_text()


# --- functions (§3) -----------------------------------------------------------------


def test_an_admin_adds_a_device_and_a_member_is_refused(family, authed, conn):
    amma = family.parents[0].parent_id
    as_user(authed, MEMBER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_admin"):
        authed.execute("select public.app_add_household_device(%s, 'plug', 'ifttt')", (amma,))
    as_user(authed, ADMIN)
    new_id = authed.execute(
        "select public.app_add_household_device(%s, 'plug', 'ifttt') as id", (amma,)
    ).fetchone()["id"]
    row = conn.execute("select * from household_devices where id = %s", (new_id,)).fetchone()
    assert (row["parent_id"], row["kind"], row["platform"], row["removed_utc"]) == (
        amma,
        "plug",
        "ifttt",
        None,
    )
    assert re.fullmatch(r"[A-Za-z0-9_-]{20,}", row["token"])
    # A platform is optional; a stranger is refused like a member.
    authed.execute("select public.app_add_household_device(%s, 'door', null)", (amma,))
    as_user(authed, STRANGER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_admin"):
        authed.execute("select public.app_add_household_device(%s, 'plug', 'ifttt')", (amma,))


def test_a_fourth_device_and_an_unknown_kind_are_refused(family, authed):
    amma = family.parents[0].parent_id
    as_user(authed, ADMIN)
    for kind in ("plug", "door", "motion"):
        authed.execute("select public.app_add_household_device(%s, %s, 'other')", (amma, kind))
    with pytest.raises(psycopg.errors.CheckViolation, match="device_limit"):
        authed.execute("select public.app_add_household_device(%s, 'light', 'other')", (amma,))
    with pytest.raises(psycopg.errors.CheckViolation, match="unknown_kind"):
        authed.execute("select public.app_add_household_device(%s, 'kettle', 'other')", (amma,))
    with pytest.raises(psycopg.errors.CheckViolation, match="unknown_platform"):
        authed.execute("select public.app_add_household_device(%s, 'plug', 'zigbee')", (amma,))


def test_remove_sets_removed_utc_and_the_address_answers_ok_recording_nothing(
    family, authed, conn, api
):
    amma = family.parents[0].parent_id
    as_user(authed, ADMIN)
    device_id = authed.execute(
        "select public.app_add_household_device(%s, 'plug', 'ifttt') as id", (amma,)
    ).fetchone()["id"]
    token = authed.execute(
        "select public.app_household_device_address(%s) as t", (device_id,)
    ).fetchone()["t"]
    assert api.get(f"/d/{token}").text == "ok"
    assert len(pings_of(conn, device_id)) == 1
    # A removed slot frees the limit and the token stops in the same instant.
    authed.execute("select public.app_remove_household_device(%s)", (device_id,))
    removed = conn.execute(
        "select removed_utc from household_devices where id = %s", (device_id,)
    ).fetchone()["removed_utc"]
    assert removed is not None
    assert api.get(f"/d/{token}").text == "ok"
    assert len(pings_of(conn, device_id)) == 1
    with pytest.raises(psycopg.errors.CheckViolation, match="removed"):
        authed.execute("select public.app_household_device_address(%s)", (device_id,))
    for kind in ("door", "motion", "light"):
        authed.execute("select public.app_add_household_device(%s, %s, null)", (amma, kind))


def test_the_address_function_refuses_members_and_strangers(family, authed, conn):
    amma = family.parents[0].parent_id
    device_id, token = add_device(conn, amma)
    as_user(authed, MEMBER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_admin"):
        authed.execute("select public.app_household_device_address(%s)", (device_id,))
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_admin"):
        authed.execute("select public.app_remove_household_device(%s)", (device_id,))
    as_user(authed, ADMIN)
    assert (
        authed.execute(
            "select public.app_household_device_address(%s) as t", (device_id,)
        ).fetchone()["t"]
        == token
    )


# --- RLS (§3) ---------------------------------------------------------------------


def test_the_circle_reads_the_view_without_the_token_and_its_own_pings(family, authed, conn, api):
    amma = family.parents[0].parent_id
    device_id, token = add_device(conn, amma)
    api.get(f"/d/{token}")
    other = provision_family(conn, "Iyer", "Asia/Kolkata", [("Patti", None)], base_url=BASE_URL)
    other_id, other_token = add_device(conn, other.parents[0].parent_id, kind="door")
    add_member(conn, other.family_id, STRANGER, role="admin")
    api.get(f"/d/{other_token}")

    for user in (ADMIN, MEMBER):
        as_user(authed, user)
        view = authed.execute("select * from household_devices_view").fetchall()
        assert [(r["id"], r["kind"]) for r in view] == [(device_id, "plug")]
        assert "token" not in view[0]
        pings = authed.execute("select device_id from household_pings").fetchall()
        assert [r["device_id"] for r in pings] == [device_id]
        # The table itself is not readable at all.
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            authed.execute("select token from household_devices")
        authed.rollback() if hasattr(authed, "rollback") else None
    # Another circle reads only its own.
    as_user(authed, STRANGER)
    assert [r["id"] for r in authed.execute("select id from household_devices_view")] == [other_id]
    assert [r["device_id"] for r in authed.execute("select device_id from household_pings")] == [
        other_id
    ]
    # No client write on either table.
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute(
            "insert into household_pings (device_id, ts_utc) values (%s, now())", (other_id,)
        )


def test_the_view_does_not_carry_the_token_column(conn):
    columns = {
        r["column_name"]
        for r in conn.execute(
            "select column_name from information_schema.columns "
            "where table_schema = 'public' and table_name = 'household_devices_view'"
        ).fetchall()
    }
    assert columns == {"id", "parent_id", "kind", "platform", "created_utc", "removed_utc"}


# --- assistant (§6) ----------------------------------------------------------------


def _parent(conn, family):
    [row] = parents_in(conn, [family.family_id])
    return row


def _ping_at(conn, device_id, when: datetime) -> None:
    conn.execute(
        "insert into household_pings (device_id, ts_utc) values (%s, %s)", (device_id, when)
    )


def test_today_carries_the_device_line_as_a_closed_sentence_before_the_city(conn, family):
    parent = dict(_parent(conn, family))
    parent["tz"] = "America/Chicago"  # away from the Chennai circle: a city line follows
    conn.execute("update parents set tz = 'America/Chicago' where id = %s", (parent["id"],))
    parent = dict(_parent(conn, family))
    device_id, _ = add_device(conn, parent["id"], kind="voice")
    now = datetime(2026, 9, 8, 15, 48, tzinfo=UTC)  # 10:48 am Chicago
    _ping_at(conn, device_id, datetime(2026, 9, 8, 13, 5, tzinfo=UTC))  # 8:05 am
    assert device_line(conn, parent, now) == "Voice routine, 8:05 am this morning"
    text = today_for(conn, parent, now)
    assert " yet. Voice routine, 8:05 am this morning. Chicago · " in text
    assert text.endswith(" there now.")


def test_the_line_takes_the_afternoon_and_evening_forms_and_the_latest_device(conn, family):
    parent = _parent(conn, family)
    plug, _ = add_device(conn, parent["id"], kind="plug")
    door, _ = add_device(conn, parent["id"], kind="door")
    _ping_at(conn, plug, datetime(2026, 9, 8, 3, 5, tzinfo=UTC))  # 8:35 am IST
    _ping_at(conn, door, datetime(2026, 9, 8, 8, 30, tzinfo=UTC))  # 2:00 pm IST
    assert device_line(conn, parent, datetime(2026, 9, 8, 9, 0, tzinfo=UTC)) == (
        "Door, 2:00 pm this afternoon"
    )
    _ping_at(conn, plug, datetime(2026, 9, 8, 13, 0, tzinfo=UTC))  # 6:30 pm IST
    assert device_line(conn, parent, datetime(2026, 9, 8, 14, 0, tzinfo=UTC)) == (
        "Plug, 6:30 pm this evening"
    )


def test_the_line_is_absent_at_night_before_six_paused_or_with_nothing_today(conn, family):
    parent = _parent(conn, family)
    plug, _ = add_device(conn, parent["id"], kind="plug")
    # 5:50 am IST ping, read at 5:55: night, and the ping is before six anyway.
    _ping_at(conn, plug, datetime(2026, 9, 8, 0, 20, tzinfo=UTC))
    assert device_line(conn, parent, datetime(2026, 9, 8, 0, 25, tzinfo=UTC)) is None
    # At 8:35 the 5:50 ping still belongs to no day: no line.
    assert device_line(conn, parent, datetime(2026, 9, 8, 3, 5, tzinfo=UTC)) is None
    assert "Plug" not in today_for(conn, parent, datetime(2026, 9, 8, 3, 5, tzinfo=UTC))
    # A 6:00 ping counts; a removed device's pings never show; paused hides it.
    _ping_at(conn, plug, datetime(2026, 9, 8, 0, 30, tzinfo=UTC))
    assert device_line(conn, parent, datetime(2026, 9, 8, 3, 5, tzinfo=UTC)) == (
        "Plug, 6:00 am this morning"
    )
    conn.execute(
        "update parents set paused_until = 'infinity', paused_since = now() where id = %s",
        (parent["id"],),
    )
    paused = dict(_parent(conn, family))
    assert "Plug" not in today_for(conn, paused, datetime(2026, 9, 8, 3, 5, tzinfo=UTC))
    conn.execute("update household_devices set removed_utc = now() where id = %s", (plug,))
    assert device_line(conn, parent, datetime(2026, 9, 8, 3, 5, tzinfo=UTC)) is None


def test_the_server_labels_and_line_forms_are_the_specs():
    assert assistant_copy.KIND_LABEL == {
        "plug": "Plug",
        "door": "Door",
        "motion": "Motion",
        "voice": "Voice routine",
        "fridge": "Fridge",
        "light": "Light",
    }
    assert assistant_copy.DEVICE_LINE_MORNING == "{kind}, {time} this morning"
    assert assistant_copy.DEVICE_LINE_AFTERNOON == "{kind}, {time} this afternoon"
    assert assistant_copy.DEVICE_LINE_EVENING == "{kind}, {time} this evening"
