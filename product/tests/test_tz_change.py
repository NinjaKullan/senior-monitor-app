"""Spec 010 §3/§5 — the moved parent, seen from the engine's side.

The webapp writes three columns in one statement; everything here is about
what the scheduler does with them on its next pass. Two properties carry the
weight:

* **A shifted clock is not evidence.** From the change until the first local
  midnight in the NEW zone, absence under the moved clock proves nothing, so
  the ask ladder holds its tongue and the morning-quiet body is never chosen —
  while data actually seen still speaks at full volume.
* **A move is never silent, and never noisy twice.** One founder alert per
  change, deduped through `ops_alerts` rather than loop memory so a restart
  between the webapp write and the next cycle cannot swallow it — and the
  alert's own message is the next move's "old zone", so the parse of it is
  round-tripped here on purpose.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
from test_outbound import (
    CountingTransport,
    at,
    family,  # noqa: F401 - fixture
    ledger,
    ping,
    run_twice,
    statuses,
)

from kettle import db
from kettle.outbound import first_new_zone_midnight, run_outbound
from kettle.provisioning import provision_family
from testsupport import BASE_URL, add_child_email, set_parent_whatsapp

REPO = Path(__file__).resolve().parents[2]
CHICAGO = ZoneInfo("America/Chicago")


def move(
    conn: psycopg.Connection,
    parent_id,
    city: str | None,
    tz: str,
    changed: datetime,
) -> None:
    """What the webapp's one-statement write leaves behind (spec 010 §1)."""
    conn.execute(
        "update parents set city_label = %s, tz = %s, tz_changed_utc = %s "
        "where id = %s",
        (city, tz, changed, parent_id),
    )


# --- the city list itself -----------------------------------------------------


def test_every_city_zone_is_accepted_by_python_and_postgres(conn):
    """Spec 010 §5: the sweep that keeps a typo in cities.json from becoming a
    parent whose digests silently stop. Every zone the picker can commit must
    load in stdlib zoneinfo (the engine's clock) AND be recognised by
    Postgres (`at time zone` in any future SQL) — an entry failing either
    would ship a city nobody can safely pick."""
    entries = json.loads((REPO / "webapp" / "src" / "data" / "cities.json").read_text())
    zones = sorted({e["iana"] for e in entries})
    assert len(zones) > 0
    for zone in zones:
        ZoneInfo(zone)  # raises on an unknown key
        conn.execute("select now() at time zone %s", (zone,))


# --- the window's edge --------------------------------------------------------


def test_the_window_ends_at_the_new_zones_first_midnight():
    changed = at(10, 0, CHICAGO)
    end = first_new_zone_midnight(changed, "America/Chicago")
    assert end == datetime(2026, 8, 22, 0, 0, tzinfo=CHICAGO)
    # The instant is compared in the NEW zone: a change late in UTC terms is
    # still "today" where the parent now is, and the window runs to the next
    # local midnight there, not to a UTC one.
    late = datetime(2026, 8, 22, 3, 0, tzinfo=ZoneInfo("UTC"))  # 21st, 22:00 Chicago
    assert first_new_zone_midnight(late, "America/Chicago") == datetime(
        2026, 8, 22, 0, 0, tzinfo=CHICAGO
    )


# --- the founder alert --------------------------------------------------------


def test_a_move_alerts_the_founder_once_in_the_pinned_format(
    conn, family, notifier  # noqa: F811
):
    """One exact message per change — and the format is load-bearing, because
    the next move's old zone is parsed back out of it."""
    parent_id = family.parents[0].parent_id
    transport = CountingTransport()

    move(conn, parent_id, "Dallas", "America/Chicago", at(10, 0, CHICAGO))
    first = "Amma: timezone changed Asia/Kolkata → America/Chicago (city Dallas) via webapp."
    run_outbound(conn, transport, at(10, 5, CHICAGO), notifier=notifier)
    run_outbound(conn, transport, at(10, 10, CHICAGO), notifier=notifier)
    assert notifier.messages.count(first) == 1

    # The second move's old zone comes from the engine's own previous alert —
    # the round trip of _previous_zone's parse.
    move(conn, parent_id, "London", "Europe/London", at(11, 0, CHICAGO))
    second = "Amma: timezone changed America/Chicago → Europe/London (city London) via webapp."
    run_outbound(conn, transport, at(11, 5, CHICAGO), notifier=notifier)
    run_outbound(conn, transport, at(11, 10, CHICAGO), notifier=notifier)
    assert notifier.messages.count(second) == 1
    assert notifier.messages.count(first) == 1

    # A cleared label reads "unset", never a blank inside the parentheses.
    move(conn, parent_id, None, "Asia/Tokyo", at(12, 0, CHICAGO))
    third = "Amma: timezone changed Europe/London → Asia/Tokyo (city unset) via webapp."
    run_outbound(conn, transport, at(12, 5, CHICAGO), notifier=notifier)
    assert notifier.messages.count(third) == 1

    # The durable copy of each announcement is the ops_alerts trail.
    last = db.latest_ops_alert(conn, parent_id, "tz_changed")
    assert last["detail"] == third


# --- changeover conservatism --------------------------------------------------


def test_the_ask_is_suppressed_in_the_window_and_resumes_after_midnight(
    conn, family, notifier  # noqa: F811
):
    """A quiet morning under a clock that moved this morning earns a skipped
    ledger row whose durable detail names the change — and the very next
    local day, the same quiet earns the ask again."""
    parent_id = family.parents[0].parent_id
    transport = CountingTransport()
    move(conn, parent_id, "Dallas", "America/Chicago", at(4, 0, CHICAGO))

    run_twice(conn, transport, at(11, 0, CHICAGO), notifier=notifier)
    assert ledger(conn) == []
    assert statuses(conn)["ask"] == "skipped"
    # The skip's detail (ops_alerts is where details live — sent_messages
    # carries no detail column) names the timezone change.
    suppressed = [
        m
        for m in notifier.messages
        if "suppressed until the first local midnight" in m
        and "America/Chicago" in m
    ]
    assert len(suppressed) == 1
    row = conn.execute(
        "select detail from ops_alerts where kind = 'outbound_skipped' "
        "and detail like %s",
        ("%first local midnight%",),
    ).fetchone()
    assert row is not None and "America/Chicago" in row["detail"]

    # First midnight in the new zone has passed: a quiet morning asks again.
    run_twice(conn, transport, at(11, 0, CHICAGO) + timedelta(days=1), notifier=notifier)
    assert ("ask", "ask_parent") in ledger(conn)


def test_a_quiet_morning_in_the_window_is_withheld_but_data_still_speaks(
    conn, family, notifier  # noqa: F811
):
    """The morning-quiet body is never chosen from moved-clock absence; a
    morning with actual signal sends the normal digest inside the window."""
    parent_id = family.parents[0].parent_id
    transport = CountingTransport()
    move(conn, parent_id, "Dallas", "America/Chicago", at(4, 0, CHICAGO))

    other = provision_family(
        conn, "Iyer", "Asia/Kolkata", [("Patti", None, "Mom")], base_url=BASE_URL
    )
    add_child_email(conn, other.family_id)
    set_parent_whatsapp(conn, other.parents[0].parent_id, "+919845550002")
    move(conn, other.parents[0].parent_id, "Dallas", "America/Chicago", at(4, 0, CHICAGO))
    ping(conn, other.parents[0].parent_id, "whatsapp", at(6, 30, CHICAGO))

    run_twice(conn, transport, at(8, 30, CHICAGO), notifier=notifier)
    # Amma was quiet: withheld, with the tz named in the alert. Patti had
    # data: the digest reports what was actually seen and sends on time.
    assert ledger(conn) == [("digest_morning", "digest_morning_normal")]
    withheld = [m for m in notifier.messages if "not evidence" in m]
    assert len(withheld) == 1
    assert "Sharma / Amma" in withheld[0]
    assert "America/Chicago" in withheld[0]


def test_digests_fire_on_the_new_zones_clock_from_the_next_cycle(
    conn, family, notifier  # noqa: F811
):
    """The zone is read fresh each cycle: after a move the evening digest
    belongs to the new zone's 20:30, and the old zone's 20:30 decides
    nothing for the evening slot."""
    parent_id = family.parents[0].parent_id
    transport = CountingTransport()
    move(conn, parent_id, "Dallas", "America/Chicago", at(4, 0, CHICAGO))
    ping(conn, parent_id, "whatsapp", at(6, 30, CHICAGO))

    # 20:30 IST — the zone the parent LEFT — is 10:00 in Chicago: morning
    # territory. The morning digest (with data) goes; no evening row exists.
    run_twice(conn, transport, at(20, 30), notifier=notifier)
    assert ledger(conn) == [("digest_morning", "digest_morning_normal")]
    assert "digest_evening" not in statuses(conn)

    # 20:30 in the new zone is when the evening note belongs to this parent.
    run_twice(conn, transport, at(20, 30, CHICAGO), notifier=notifier)
    assert ("digest_evening", "digest_evening_normal") in ledger(conn)
    # And the signal at 6:30 meant the day never reached the ask threshold.
    assert "ask" not in statuses(conn)
