"""Spec 014 §6 items 1, 2, 4, 5 — the Android server side (DECISIONS 329).

The vocabulary (unlock alarm-grade, motion corroborating, one grade per key
on every platform); provisioning by platform with no shortcuts faked for
Android; the claim route's life, limits and reinstall shape; the two claim
columns written and never read; and the ingest route unchanged, an Android
unlock counting in the engine's morning window and a motion never.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from kettle import db
from kettle.provisioning import provision_family, render_summary, select_signals
from kettle.setup_page import CLAIM_LIMIT
from kettle.signals import (
    ALARM_GRADE,
    ANDROID_SIGNALS,
    PLATFORM_SIGNALS,
    SHORTCUT_SIGNALS,
    SIGNAL_LABELS,
    STANDARD_SIGNALS,
)
from scripts.provision import main as provision_main
from testsupport import BASE_URL

KETTLE = Path(__file__).resolve().parents[1] / "kettle"
IST = ZoneInfo("Asia/Kolkata")


def android_family(conn, name: str = "Redmi", signals=None):
    return provision_family(
        conn,
        name,
        "Asia/Kolkata",
        [("Amma", None, "Mom")],
        base_url=BASE_URL,
        platform="android",
        signals=signals,
        owner_email="hema@example.test",
        owner_name="Hema",
    )


def slug_of(parent) -> str:
    return parent.setup_url.rsplit("/", 1)[-1]


def claim(client, slug: str, **over):
    body = {"platform": "android", "app_version": "0.1.0", "sdk": 35, "oem": "Xiaomi", **over}
    return client.post(f"/s/{slug}/claim", json=body)


# --- §6.1 the vocabulary ---------------------------------------------------------


def test_the_android_keys_carry_the_ruled_grades_and_labels():
    assert ALARM_GRADE["unlock"] is True
    assert ALARM_GRADE["motion"] is False
    assert SIGNAL_LABELS["unlock"] == "Phone unlocked"
    assert SIGNAL_LABELS["motion"] == "Phone moved"
    assert PLATFORM_SIGNALS["ios_shortcuts"] == STANDARD_SIGNALS
    assert PLATFORM_SIGNALS["android"] == ANDROID_SIGNALS
    assert [k for k, _ in ANDROID_SIGNALS] == ["unlock", "charger", "motion", "device_alive"]
    # ALARM_GRADE covers the whole vocabulary, both seeds and the merged pair.
    for platform, seed in PLATFORM_SIGNALS.items():
        for key, _grade in seed:
            assert key in ALARM_GRADE, (platform, key)
    assert {"routine", "charger"} <= set(ALARM_GRADE)


def test_no_key_is_alarm_grade_on_one_platform_and_corroborating_on_another():
    """Pinned (DECISIONS 329): one grade per key, wherever it is seeded."""
    seen: dict[str, bool] = {}
    for platform, seed in PLATFORM_SIGNALS.items():
        for key, grade in seed:
            assert grade == ALARM_GRADE[key], (platform, key)
            assert seen.setdefault(key, grade) == grade, f"{key} differs on {platform}"
    # And the Android keys are the app's own: no shortcut, no iCloud link.
    assert not ({"unlock", "motion"} & SHORTCUT_SIGNALS)


# --- §6.2 provisioning -----------------------------------------------------------


def test_platform_android_selects_the_android_set_and_fakes_no_shortcut(conn):
    family = android_family(conn)
    [parent] = family.parents
    rows = conn.execute(
        "select signal, alarm_grade, active from parent_signals where parent_id = %s "
        "order by signal",
        (parent.parent_id,),
    ).fetchall()
    assert [(r["signal"], r["alarm_grade"], r["active"]) for r in rows] == [
        ("charger", False, True),
        ("device_alive", False, True),
        ("motion", False, True),
        ("unlock", True, True),
    ]
    device = conn.execute(
        "select platform from devices where id = %s", (parent.device_id,)
    ).fetchone()
    assert device["platform"] == "android"
    assert all(sig.shortcut is None for sig in parent.signals)
    assert all(sig.url.endswith(f"/p/{parent.device_token}/{sig.signal}") for sig in parent.signals)
    summary = render_summary(family)
    assert "Kettle —" not in summary
    assert "- unlock  (alarm)" in summary
    assert "no shortcuts and no iCloud links" in summary


def test_ios_provisioning_is_unchanged(conn):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    [parent] = family.parents
    assert {(s.signal, s.alarm_grade) for s in parent.signals} == set(STANDARD_SIGNALS)
    assert all(sig.shortcut == f"Kettle — {SIGNAL_LABELS[sig.signal]}" for sig in parent.signals)
    assert select_signals(None) == STANDARD_SIGNALS
    assert select_signals(None, "ios_shortcuts") == STANDARD_SIGNALS


def test_signals_still_override_and_the_grade_is_never_the_callers(conn):
    family = android_family(conn, signals=["unlock", "device_alive"])
    rows = conn.execute(
        "select signal, alarm_grade from parent_signals where parent_id = %s order by signal",
        (family.parents[0].parent_id,),
    ).fetchall()
    assert [(r["signal"], r["alarm_grade"]) for r in rows] == [
        ("device_alive", False),
        ("unlock", True),
    ]
    with pytest.raises(ValueError, match="unknown platform"):
        select_signals(None, "blackberry")


def test_the_cli_takes_platform_android(conn, database_url, capsys):
    code = provision_main(
        [
            "--database-url",
            database_url,
            "--base-url",
            BASE_URL,
            "--family",
            "Redmi",
            "--parent",
            "Amma::Mom",
            "--platform",
            "android",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "- unlock  (alarm)" in out and "- motion  (corroborating)" in out
    assert "Kettle —" not in out
    keys = {
        r["signal"]
        for r in conn.execute(
            "select ps.signal from parent_signals ps join parents p on p.id = ps.parent_id "
            "join families f on f.id = p.family_id where f.name = 'Redmi'"
        ).fetchall()
    }
    assert keys == {"unlock", "charger", "motion", "device_alive"}


# --- §6.4 the claim -------------------------------------------------------------


def test_a_live_link_hands_the_app_its_token_base_and_allowlist(conn, client, settings):
    family = android_family(conn)
    [parent] = family.parents
    answer = claim(client, slug_of(parent))
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert body["device_token"] == parent.device_token
    assert body["api_base"] == settings.public_base_url.rstrip("/")
    assert body["signals"] == ["unlock", "charger", "device_alive", "motion"]
    assert answer.headers["cache-control"] == "no-store"
    row = conn.execute(
        "select platform, oem, app_version, active from devices where id = %s", (parent.device_id,)
    ).fetchone()
    assert (row["platform"], row["oem"], row["app_version"], row["active"]) == (
        "android",
        "Xiaomi",
        "0.1.0",
        True,
    )
    # The link stays claimable (a reinstall), and the token it handed out pings.
    assert claim(client, slug_of(parent)).status_code == 200
    assert client.get(f"/p/{body['device_token']}/unlock").status_code == 200


def test_a_reinstall_claims_again_and_gets_a_fresh_device_leaving_the_old_one_active(conn, client):
    """The app sends no stable identity (OEM plus version is not one), so a
    second claim cannot be told apart from a second phone: a new row, a
    fresh token, the earlier row untouched until the founder revokes it."""
    family = android_family(conn)
    [parent] = family.parents
    first = claim(client, slug_of(parent)).json()
    second = claim(client, slug_of(parent), app_version="0.1.1").json()
    assert second["device_token"] != first["device_token"]
    assert second["signals"] == first["signals"]
    rows = conn.execute(
        "select device_token, platform, active, app_version from devices where parent_id = %s",
        (parent.parent_id,),
    ).fetchall()
    by_token = {r["device_token"]: (r["platform"], r["active"], r["app_version"]) for r in rows}
    assert by_token == {
        first["device_token"]: ("android", True, "0.1.0"),
        second["device_token"]: ("android", True, "0.1.1"),
    }
    assert parent.device_token == first["device_token"]
    for token in (first["device_token"], second["device_token"]):
        assert client.get(f"/p/{token}/unlock").status_code == 200


def test_a_claim_on_a_link_that_is_not_android_is_refused_and_creates_nothing(conn, client):
    """DECISIONS 331: the link's platform is the parent's platform. An iOS
    link claimed by the Android app used to mint an Android row that
    inherited the iOS allowlist, which the app's every ping would then
    fail; it is refused instead, and the parent's devices are as they were."""
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    [parent] = family.parents
    refused = claim(client, slug_of(parent))
    assert refused.status_code == 400, refused.text
    assert refused.text == "platform"
    assert "device_token" not in refused.text
    rows = conn.execute(
        "select device_token, platform, app_version, oem, active from devices where parent_id = %s",
        (parent.parent_id,),
    ).fetchall()
    assert [tuple(r.values()) for r in rows] == [
        (parent.device_token, "ios_shortcuts", None, None, True)
    ]
    # The iOS token still pings; nothing about the parent's setup moved.
    assert client.get(f"/p/{parent.device_token}/whatsapp").status_code == 200
    # A dead link is dead on any platform: the dead end comes before the
    # platform is looked at, so the app never learns anything from a link
    # that has expired.
    conn.execute("update setup_links set expires_utc = now() - interval '1 hour'")
    expired = claim(client, slug_of(parent))
    assert (expired.status_code, expired.json()) == (410, {"status": "expired"})


def test_expired_and_revoked_links_answer_the_dead_end_and_hand_out_nothing(conn, client):
    family = android_family(conn)
    [parent] = family.parents
    conn.execute("update setup_links set expires_utc = now() - interval '1 hour'")
    expired = claim(client, slug_of(parent))
    assert (expired.status_code, expired.json()) == (410, {"status": "expired"})
    conn.execute("update setup_links set expires_utc = now() + interval '6 days'")
    conn.execute("update devices set active = false, revoked_utc = now()")
    revoked = claim(client, slug_of(parent))
    assert (revoked.status_code, revoked.json()) == (410, {"status": "revoked"})
    assert "device_token" not in expired.text and "device_token" not in revoked.text
    assert conn.execute("select count(*) as n from devices").fetchone()["n"] == 1
    assert conn.execute("select oem from devices").fetchone()["oem"] is None
    assert claim(client, "nosuchslug0000000000000000").status_code == 404


def test_a_platform_other_than_android_is_refused(conn, client):
    family = android_family(conn)
    slug = slug_of(family.parents[0])
    for body in (
        {"platform": "ios_shortcuts"},
        {"platform": "ios"},
        {},
        [],
    ):
        refused = client.post(f"/s/{slug}/claim", json=body)
        assert refused.status_code == 400, body
    assert (
        client.post(
            f"/s/{slug}/claim", content="not json", headers={"content-type": "application/json"}
        ).status_code
        == 400
    )
    assert conn.execute("select app_version from devices").fetchone()["app_version"] is None


def test_claims_are_rate_limited_per_slug(conn, client):
    family = android_family(conn, name="One")
    other = android_family(conn, name="Two")
    slug = slug_of(family.parents[0])
    for _ in range(CLAIM_LIMIT):
        assert claim(client, slug).status_code == 200
    assert claim(client, slug).status_code == 429
    # Another slug in the same minute has its own budget.
    assert claim(client, slug_of(other.parents[0])).status_code == 200


def test_claim_fields_are_trimmed_capped_and_optional(conn, client):
    family = android_family(conn)
    [parent] = family.parents
    assert (
        claim(client, slug_of(parent), oem="  Samsung  ", app_version="x" * 500).status_code == 200
    )
    row = conn.execute(
        "select oem, app_version from devices where id = %s", (parent.device_id,)
    ).fetchone()
    assert (row["oem"], len(row["app_version"])) == ("Samsung", 120)
    again = client.post(f"/s/{slug_of(parent)}/claim", json={"platform": "android"})
    assert again.status_code == 200
    newest = conn.execute(
        "select oem, app_version from devices where device_token = %s",
        (again.json()["device_token"],),
    ).fetchone()
    assert (newest["oem"], newest["app_version"]) == (None, None)


def test_the_claim_log_names_the_platform_and_never_a_token(conn, client, caplog):
    import logging

    family = android_family(conn)
    [parent] = family.parents
    with caplog.at_level(logging.INFO, logger="kettle.setup"):
        body = claim(client, slug_of(parent)).json()
    assert "claim on …" in caplog.text and "android" in caplog.text
    assert body["device_token"] not in caplog.text
    assert slug_of(parent) not in caplog.text


# --- §6.5 the columns -------------------------------------------------------------


def test_the_claim_columns_are_written_at_claim_and_read_by_nothing(conn, client):
    columns = {
        r["column_name"]
        for r in conn.execute(
            "select column_name from information_schema.columns "
            "where table_schema = 'public' and table_name = 'devices'"
        ).fetchall()
    }
    assert {"oem", "app_version"} <= columns
    ping_columns = {
        r["column_name"]
        for r in conn.execute(
            "select column_name from information_schema.columns "
            "where table_schema = 'public' and table_name = 'pings'"
        ).fetchall()
    }
    assert ping_columns == {"id", "parent_id", "signal", "ts_utc", "ip_hash"}
    # No SELECT in the product names either column; the one reader is the
    # claim-or-not check, which reads only whether app_version is set.
    for path in KETTLE.glob("*.py"):
        source = path.read_text()
        for statement in re.findall(r"select\b.*?\bfrom\b", source, re.S | re.I):
            assert "oem" not in statement.lower(), path.name
            assert "app_version" not in statement.lower() or "is not null" in statement, path.name


# --- item 5: ingest unchanged, the engine's window ---------------------------------


def test_an_android_unlock_lands_and_counts_in_the_morning_window_and_motion_never(conn, client):
    family = android_family(conn)
    [parent] = family.parents
    token = claim(client, slug_of(parent)).json()["device_token"]
    assert client.get(f"/p/{token}/motion").status_code == 200
    assert client.get(f"/p/{token}/unlock").status_code == 200
    # `routine` is the iOS key and stays refused on an Android allowlist.
    assert client.get(f"/p/{token}/routine").status_code == 400
    rows = conn.execute(
        "select signal from pings where parent_id = %s order by id", (parent.parent_id,)
    ).fetchall()
    assert [r["signal"] for r in rows] == ["motion", "unlock"]
    now = datetime.now(tz=UTC)
    counted = db.count_alarm_pings_between(
        conn, parent.parent_id, now - timedelta(minutes=5), now + timedelta(minutes=5)
    )
    assert counted == 1
    conn.execute("delete from pings where signal = 'unlock'")
    assert (
        db.count_alarm_pings_between(
            conn, parent.parent_id, now - timedelta(minutes=5), now + timedelta(minutes=5)
        )
        == 0
    )


def test_the_engine_reads_an_android_unlock_as_a_normal_morning(conn):
    from kettle.outbound import LogTransport, run_outbound
    from testsupport import add_child_email

    family = android_family(conn)
    add_child_email(conn, family.family_id)
    [parent] = family.parents
    day = datetime(2026, 9, 14, tzinfo=IST)
    db.insert_ping(conn, parent.parent_id, "motion", day.replace(hour=7), None)
    transport = LogTransport()
    run_outbound(conn, transport, day.replace(hour=8, minute=30))
    assert "digest_morning_quiet" in {t for t, _ in transport.sent}
    # Day two: an unlock before the digest — a normal morning. Same
    # allowlist, the grade decides.
    next_day = day + timedelta(days=1)
    db.insert_ping(conn, parent.parent_id, "unlock", next_day.replace(hour=7, minute=5), None)
    transport = LogTransport()
    run_outbound(conn, transport, next_day.replace(hour=8, minute=30))
    assert "digest_morning_normal" in {t for t, _ in transport.sent}
