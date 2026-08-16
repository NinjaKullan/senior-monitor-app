"""The parent setup page (spec 005b §4.3) — consent to verified, and the walls.

The load-bearing assertions here are the negative ones. The page travels
through WhatsApp threads and screenshots, so what it must never contain —
the device token, a ping URL, a `.shortcut` — is tested harder than what it
must. The verify check is law #6 at its sharpest point: only an alarm-grade,
person-attributed ping may turn the named card green.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import psycopg
import pytest

from kettle import setup_copy
from kettle.provisioning import issue_setup_link_by_token, provision_family
from kettle.setup_page import automation_row, verify_app_label
from kettle.signals import ALARM_GRADE
from kettle.timeutil import now_utc
from testsupport import BASE_URL


def _family(conn, signals=None, owner="Hema", parents=(("Amma", None),)):
    return provision_family(
        conn,
        "Suryaprakasam",
        "Asia/Kolkata",
        list(parents),
        base_url=BASE_URL,
        signals=signals,
        owner_email="hema@example.test" if owner else None,
        owner_name=owner,
    )


def _slug(parent) -> str:
    return parent.setup_url.rsplit("/", 1)[-1]


# --- the live page -----------------------------------------------------------


def test_merged_page_renders_the_whole_sequence(conn: psycopg.Connection, client):
    family = _family(conn, signals=["routine", "charger"])
    page = client.get(f"/s/{_slug(family.parents[0])}")
    assert page.status_code == 200
    body = page.text

    assert "Amma’s setup" in body
    assert "From Hema" in body

    # The sequence, in §4.3's order: consent → step zero → add → first run →
    # automations → verify → done.
    order = [
        setup_copy.CONSENT_TITLE,
        setup_copy.STEP_ZERO_TITLE,
        setup_copy.ADD_TITLE_TWO,
        setup_copy.FIRSTRUN_TITLE,
        setup_copy.AUTO_TITLE,
        setup_copy.VERIFY_TITLE,
        "That’s everything, Amma",
    ]
    positions = [body.index(text) for text in order]
    assert positions == sorted(positions), "screens out of order"

    # Consent facts (§2.7): what is sent, what never, and the kill switch —
    # which appears again on the done screen (shown, not described).
    assert setup_copy.CONSENT_SENT_MERGED in body
    assert setup_copy.CONSENT_NEVER in body
    assert body.count(setup_copy.KILL_SWITCH[:30]) >= 1
    assert setup_copy.DONE_KILL in body
    assert setup_copy.CONSENT_STOP in body

    # Two tiles, named what the phone will name them (ruling 61).
    assert "Kettle — Daily routine" in body
    assert "Kettle — Charger" in body

    # Step zero's App Store path (QUESTIONS 103).
    assert setup_copy.APP_STORE_SHORTCUTS_URL in body

    # The pre-empted warning names the real host (QUESTIONS 99).
    assert "wants to connect to kettle-api.test" in body

    # Q107's two field gotchas: Run Immediately on every automation row, and
    # both charger edges ticked in one automation.
    assert "Tick both" in body
    assert "Is Connected" in body and "Is Disconnected" in body

    # The helper path (QUESTIONS 104) is present but off by default.
    assert setup_copy.HELPER_TOGGLE in body
    assert setup_copy.HELPER_NOTE_FIRSTRUN in body


def test_every_automation_row_says_run_immediately(conn: psycopg.Connection, client):
    """Q107: Run After Confirmation is a dead automation on a parent's phone."""
    for keys in (["routine", "charger"], None):  # merged and the standard seed
        conn.execute("delete from families")
        family = _family(conn, signals=keys)
        body = client.get(f"/s/{_slug(family.parents[0])}").text
        rows = [
            automation_row(row["signal"], "Amma")
            for row in conn.execute(
                "select signal, alarm_grade from parent_signals where active "
                "order by alarm_grade desc, signal"
            ).fetchall()
        ]
        for rendered in rows:
            assert "Run Immediately" in rendered
            assert rendered.replace("&amp;", "&") in body.replace("&amp;", "&")


def test_per_app_page_tells_the_truth_about_which_app(conn: psycopg.Connection, client):
    """A per-app setup stores the app's key; its consent must not claim otherwise."""
    family = _family(conn)  # standard six-signal seed
    body = client.get(f"/s/{_slug(family.parents[0])}").text
    assert setup_copy.CONSENT_SENT_PER_APP in body
    assert setup_copy.CONSENT_SENT_MERGED not in body
    assert "Kettle — WhatsApp" in body
    assert "Kettle — Daily Check" in body


def test_the_page_never_carries_token_slug_or_file(conn: psycopg.Connection, client):
    """The wall: the page travels; the credentials and the files must not."""
    family = _family(conn, signals=["routine", "charger"])
    parent = family.parents[0]
    slug = _slug(parent)
    body = client.get(f"/s/{slug}").text

    assert parent.device_token not in body
    assert slug not in body, "the secret lives in the address bar alone"
    assert f"/p/{parent.device_token}" not in body
    assert ".shortcut" not in body, "the page never serves or names a file (Q117)"
    assert "download" not in body.lower()

    # And the page keeps itself out of caches, indexes and referrers.
    assert '<meta name="referrer" content="no-referrer">' in body
    assert '<meta name="robots" content="noindex">' in body


def test_page_response_headers_are_locked_down(conn: psycopg.Connection, client):
    family = _family(conn, signals=["routine", "charger"])
    response = client.get(f"/s/{_slug(family.parents[0])}")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-robots-tag"] == "noindex"
    assert "connect-src 'self'" in response.headers["content-security-policy"]


def test_names_are_escaped(conn: psycopg.Connection, client):
    family = provision_family(
        conn,
        "Sharma",
        "Asia/Kolkata",
        [('<script>alert("x")</script>', None)],
        base_url=BASE_URL,
        signals=["routine", "charger"],
        owner_email="child@example.test",
        owner_name="<b>Child</b>",
    )
    body = client.get(f"/s/{_slug(family.parents[0])}").text
    assert '<script>alert("x")</script>' not in body
    assert "<b>Child</b>" not in body
    assert "&lt;script&gt;" in body


def test_family_without_an_owner_still_reads(conn: psycopg.Connection, client):
    family = _family(conn, signals=["routine", "charger"], owner=None)
    body = client.get(f"/s/{_slug(family.parents[0])}").text
    assert setup_copy.HEADER_SUB_NO_CHILD in body
    assert "From " not in body.split("<main>")[0]


# --- dead ends (acceptance 3) ------------------------------------------------


def test_expired_link_is_a_dead_end_with_a_person_to_ask(conn: psycopg.Connection, client):
    family = _family(conn, signals=["routine", "charger"])
    slug = _slug(family.parents[0])
    conn.execute("update setup_links set expires_utc = now() - interval '1 hour'")

    page = client.get(f"/s/{slug}")
    assert page.status_code == 410
    assert setup_copy.DEAD_EXPIRED_TITLE in page.text
    assert "Hema" in page.text, "the child contact path"
    for leaked in (
        setup_copy.AUTO_TITLE,
        setup_copy.VERIFY_TITLE,
        "Kettle — Daily routine",
        ".shortcut",
        family.parents[0].device_token,
    ):
        assert leaked not in page.text
    assert page.headers["cache-control"] == "no-store"


def test_rotated_link_is_dead_and_the_new_one_lives(conn: psycopg.Connection, client):
    family = _family(conn, signals=["routine", "charger"])
    old_slug = _slug(family.parents[0])
    issued = issue_setup_link_by_token(
        conn, family.parents[0].device_token, BASE_URL, now_utc()
    )

    old = client.get(f"/s/{old_slug}")
    assert old.status_code == 410
    assert setup_copy.DEAD_REVOKED_TITLE in old.text

    new = client.get(f"/s/{issued.url.rsplit('/', 1)[-1]}")
    assert new.status_code == 200


def test_revoking_the_device_kills_the_url(conn: psycopg.Connection, client):
    """§4.2: the URL is the token in transit and dies with it."""
    family = _family(conn, signals=["routine", "charger"])
    slug = _slug(family.parents[0])
    assert client.get(f"/s/{slug}").status_code == 200

    conn.execute("update devices set active = false, revoked_utc = now()")
    dead = client.get(f"/s/{slug}")
    assert dead.status_code == 410
    assert setup_copy.DEAD_REVOKED_TITLE in dead.text


def test_unknown_slug_is_a_generic_dead_end(conn: psycopg.Connection, client):
    page = client.get("/s/nosuchslug0000000000000000")
    assert page.status_code == 404
    assert setup_copy.DEAD_UNKNOWN_TITLE in page.text
    # No row, so no family: the generic dead end names nobody.
    assert "Hema" not in page.text


# --- the live state check (verify by prediction) -----------------------------


def test_state_reports_live_and_holds_the_server_clock(conn: psycopg.Connection, client):
    family = _family(conn, signals=["routine", "charger"])
    state = client.get(f"/s/{_slug(family.parents[0])}/state").json()
    assert state["status"] == "live"
    assert state["parent_name"] == "Amma"
    assert state["seen"] is None
    assert state["now"].endswith("+00:00")


def _second_before(now_iso: str) -> str:
    """A baseline strictly older than any ping the test sends afterwards.

    Server timestamps are second-resolution, so a test that pings within the
    same second as its baseline would sit exactly on the boundary; stepping
    the baseline back one second makes "after the screen" unambiguous.
    """
    return (datetime.fromisoformat(now_iso) - timedelta(seconds=1)).isoformat()


def test_verify_greens_on_an_alarm_ping_and_only_then(conn: psycopg.Connection, client):
    family = _family(conn, signals=["routine", "charger"])
    parent = family.parents[0]
    path = f"/s/{_slug(parent)}/state"
    since = _second_before(client.get(path).json()["now"])

    assert client.get(path, params={"since": since}).json()["seen"] is False

    # A charger edge is household plumbing (law #6): it must never be what
    # turns the named card green, even though it is a real, active signal.
    assert client.get(f"/p/{parent.device_token}/charger").status_code == 200
    assert client.get(path, params={"since": since}).json()["seen"] is False

    assert client.get(f"/p/{parent.device_token}/routine").status_code == 200
    assert client.get(path, params={"since": since}).json()["seen"] is True


def test_verify_ignores_pings_from_before_the_screen(conn: psycopg.Connection, client):
    """First-run pings predate the verify screen; they must not pre-green it.

    The boundary is strict: a ping in the same second as the baseline counts
    as before the screen, because greening on a stale ping is the exact
    failure the crossed-pair check exists to catch.
    """
    family = _family(conn, signals=["routine", "charger"])
    parent = family.parents[0]
    path = f"/s/{_slug(parent)}/state"

    assert client.get(f"/p/{parent.device_token}/routine").status_code == 200
    since = client.get(path).json()["now"]
    assert client.get(path, params={"since": since}).json()["seen"] is False


def test_crossed_urls_fail_loudly_not_silently(conn: psycopg.Connection, client):
    """Acceptance 4: swap two parents' URLs and the named-card check must fail.

    Amma's phone, Appa's URL: the page waits for *Appa's* card, Amma's ping
    arrives, and the check stays red. The page's own copy then says what to
    suspect — that is the loud half, asserted from the embedded script copy.
    """
    family = _family(
        conn,
        signals=["routine", "charger"],
        parents=(("Amma", None), ("Appa", None)),
    )
    amma, appa = family.parents

    appa_state = f"/s/{_slug(appa)}/state"
    since = _second_before(client.get(appa_state).json()["now"])

    # The crossed install: Amma's token pings while Appa's page watches.
    assert client.get(f"/p/{amma.device_token}/routine").status_code == 200
    assert client.get(appa_state, params={"since": since}).json()["seen"] is False

    body = client.get(f"/s/{_slug(appa)}").text
    assert "two links may have been swapped" in body
    assert "Appa" in body


def test_state_dead_ends_mirror_the_page(conn: psycopg.Connection, client):
    family = _family(conn, signals=["routine", "charger"])
    slug = _slug(family.parents[0])

    conn.execute("update setup_links set expires_utc = now() - interval '1 hour'")
    gone = client.get(f"/s/{slug}/state")
    assert gone.status_code == 410
    assert gone.json() == {"status": "expired"}

    assert client.get("/s/nosuchslug0000000000000000/state").status_code == 404


def test_malformed_since_is_refused(conn: psycopg.Connection, client):
    family = _family(conn, signals=["routine", "charger"])
    path = f"/s/{_slug(family.parents[0])}/state"
    assert client.get(path, params={"since": "yesterdayish"}).status_code == 400
    # A naive timestamp has no timezone to compare in; refuse rather than guess.
    assert client.get(path, params={"since": "2026-08-16T10:00:00"}).status_code == 400


# --- the instruction map stays total -----------------------------------------


def test_every_vocabulary_signal_has_an_automation_instruction():
    """A new signal key must get a real instruction, not inherit a default."""
    for signal in ALARM_GRADE:
        rendered = automation_row(signal, "Amma")
        assert "Run Immediately" in rendered

    with pytest.raises(ValueError, match="no automation instruction"):
        automation_row("pigeon", "Amma")


def test_verify_app_prefers_the_first_alarm_signal():
    assert verify_app_label([{"signal": "routine", "alarm_grade": True}]).startswith("WhatsApp")
    assert verify_app_label([{"signal": "whatsapp", "alarm_grade": True}]) == "WhatsApp"
    assert (
        verify_app_label(
            [
                {"signal": "charger", "alarm_grade": False},
                {"signal": "youtube", "alarm_grade": True},
            ]
        )
        == "YouTube"
    )
    assert verify_app_label([{"signal": "charger", "alarm_grade": False}]) is None


def test_all_corroborating_set_gets_no_green_check(conn: psycopg.Connection, client):
    """Law #6 at the page: no alarm signal, no card promise, no polling UI."""
    family = _family(conn, signals=["charger", "device_alive"])
    body = client.get(f"/s/{_slug(family.parents[0])}").text
    assert setup_copy.VERIFY_NO_ROUTINE.format(child="Hema") in body
    assert 'id="verifyBtn"' not in body
    assert '"hasVerify": false' in body


def test_browser_signal_consent_sentence_is_wired(
    conn: psycopg.Connection, client, monkeypatch
):
    """Q100's future browser signal must surface its own consent sentence.

    The vocabulary has no browser key yet, so today's pages never show it —
    asserted on a real page. The wiring is then proven by patching
    BROWSER_SIGNALS over an existing key, so the day `safari` joins the list
    the sentence appears with no second change to remember.
    """
    family = _family(conn, signals=["routine", "charger"])
    path = f"/s/{_slug(family.parents[0])}"
    assert setup_copy.CONSENT_BROWSER not in client.get(path).text

    monkeypatch.setattr(setup_copy, "BROWSER_SIGNALS", ("routine",))
    assert setup_copy.CONSENT_BROWSER in client.get(path).text
