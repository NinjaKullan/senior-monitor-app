"""The webapp's contract with the backend, checked from the Python side.

Two things a JS test cannot check for itself:

* that the copy it renders is still the copy the backend sends (AC3's templates
  live in two languages now, and drift would be silent);
* that every table the app reads is RLS-protected and returns only the caller's
  family (AC1's isolation proof, at the app's actual read surface);
* that the humanised signal names the tripwire view renders are still the names
  of the shortcuts sitting on the parent's phone (005d, and the reason those
  names are allowed to render at all).
"""

from __future__ import annotations

import re
from pathlib import Path

import psycopg
import pytest

from kettle import db, messages, signals
from kettle.provisioning import provision_family
from kettle.timeutil import now_utc
from testsupport import BASE_URL, add_member, as_user

WEBAPP = Path(__file__).resolve().parent.parent.parent / "webapp"
COPY_TS = WEBAPP / "src" / "lib" / "copy.ts"
QUERIES_TS = WEBAPP / "src" / "lib" / "queries.ts"
SIGNAL_NAMES_TS = WEBAPP / "src" / "lib" / "signalNames.ts"

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


def _ts_consts(path: Path) -> dict[str, str]:
    """Pull `export const NAME = "value";` (single- or multi-line) out of a module."""
    source = path.read_text()
    found = {}
    for match in re.finditer(
        r'export const ([A-Z_]+)\s*=\s*((?:"[^"]*"\s*\+?\s*)+);', source
    ):
        name, raw = match.group(1), match.group(2)
        found[name] = "".join(re.findall(r'"([^"]*)"', raw))
    return found


def test_webapp_copy_matches_the_backend_templates():
    """The digest list recomposes messages, so its templates must not drift."""
    ts = _ts_consts(COPY_TS)
    assert ts, "no exported string constants found in copy.ts"

    assert ts["MORNING_TEMPLATE"] == messages.MORNING_TEMPLATE
    assert ts["EVENING_ONE"] == messages.EVENING_ONE
    assert ts["EVENING_TWO"] == messages.EVENING_TWO
    assert ts["EVENING_MANY"] == messages.EVENING_MANY
    assert ts["CLOCK_NEUTRAL"] == messages.CLOCK_NEUTRAL


# The headline is the one string a family reads at an anxious moment, so it is
# the one the floor law governs. Sublines are captions on it and may state a
# plain absence ("No routine seen yet"); a headline may not.
GLANCE_HEADLINES = {
    "GLANCE_SEEN_MORNING": "{name}'s morning started the usual way",
    "GLANCE_SEEN_AFTERNOON": "A normal day so far",
    "GLANCE_SEEN_EVENING": "A normal, gentle day",
    "GLANCE_QUIET_MORNING": "Quiet so far this morning",
    "GLANCE_QUIET_TODAY": "Quiet so far today",
}
GLANCE_SUBLINES = {"GLANCE_NO_ROUTINE_YET"}


def test_webapp_glance_copy_is_never_darker_than_quiet():
    """005a §3.1, carried into 005c: `Quiet so far` is still the floor."""
    ts = _ts_consts(COPY_TS)

    assert {k: ts[k] for k in GLANCE_HEADLINES} == GLANCE_HEADLINES

    # A newly added GLANCE_ constant has to be classified rather than quietly
    # escaping the scan below — that is how a floor rots.
    unclassified = {
        name
        for name in ts
        if name.startswith("GLANCE_")
        and name not in GLANCE_HEADLINES
        and name not in GLANCE_SUBLINES
    }
    assert not unclassified, f"classify these as headline or subline: {unclassified}"

    for name, value in GLANCE_HEADLINES.items():
        lowered = value.lower()
        for worrying in ("no ", "not ", "unreachable", "silent", "concern", "alert"):
            assert worrying not in lowered, f"{name} is darker than the floor: {value}"
        if name.startswith("GLANCE_QUIET"):
            assert value.startswith("Quiet so far"), f"{name} left the floor: {value}"


# Spec 005d's copy, classified the way GLANCE_* is: chips are the two health
# states, and everything else on that view is chrome. An unclassified TRIPWIRE_
# constant fails below rather than quietly escaping the tone scan.
TRIPWIRE_CHIPS = {
    "TRIPWIRE_CONNECTED": "Connected",
    "TRIPWIRE_STALE": "Not heard in a while",
    # Never heard from is its own state, not the amber one: absence of *ever*
    # means not-yet-configured (PM ruling on DECISIONS 60, the same principle as
    # 001 item 4's "suppress the infra alert until the first ping arrives").
    "TRIPWIRE_UNSET": "Not set up yet",
}
TRIPWIRE_CHROME = {
    "TRIPWIRE_TITLE",
    "TRIPWIRE_REPAIR",
    "TRIPWIRE_BACK",
    "TRIPWIRE_OPEN_LABEL",
}


def test_webapp_tripwire_copy_describes_equipment_not_the_person():
    """005d §2: amber is the ceiling, and it refers to a tripwire, never a parent.

    The health chips are the strings a family reads next to a signal name, which
    makes them the place a person-claim would sneak in ("Amma may be unwell").
    They are pinned exactly, and the rest of the view's copy is scanned for the
    vocabulary of alarm — this screen escalates to `Not heard in a while` and no
    further, because anything further belongs to the ladder.
    """
    ts = _ts_consts(COPY_TS)

    assert {k: ts[k] for k in TRIPWIRE_CHIPS} == TRIPWIRE_CHIPS

    unclassified = {
        name
        for name in ts
        if name.startswith("TRIPWIRE_")
        and name not in TRIPWIRE_CHIPS
        and name not in TRIPWIRE_CHROME
    }
    assert not unclassified, f"classify these as chip or chrome: {unclassified}"

    for name in list(TRIPWIRE_CHIPS) + sorted(TRIPWIRE_CHROME):
        lowered = ts[name].lower()
        for worrying in ("urgent", "emergency", "alarm", "danger", "unwell", "ill", "wrong"):
            # Whole words: "still" and "will" are not "ill".
            assert not re.search(rf"\b{worrying}\b", lowered), (
                f"{name} is darker than amber: {ts[name]}"
            )

    # The nudge is the only string here that names a person, and it names them as
    # the owner of a phone that needs two minutes.
    assert ts["TRIPWIRE_REPAIR"] == (
        "A tripwire may need a quick fix on {name}'s phone. "
        "It's a two-minute FaceTime."
    )


def test_webapp_recency_copy_has_no_clock_variant_and_no_never():
    """005d §1: day granularity is a property of the vocabulary, not of a caller.

    There is no template here a future caller could pass a time into, which is
    the point — the constraint holds because the words to break it do not exist.
    `never` was deleted the same way (founder's on-device round, DECISIONS 68):
    a tripwire that has never reported renders its chip and no recency at all,
    and the word is gone from the module rather than merely uncalled.
    """
    ts = _ts_consts(COPY_TS)
    recency = {name: value for name, value in ts.items() if name.startswith("RECENCY_")}

    assert recency == {
        "RECENCY_TODAY": "today",
        "RECENCY_YESTERDAY": "yesterday",
        "RECENCY_DAYS": "{days} days ago",
    }
    for name, value in recency.items():
        assert ":" not in value, f"{name} looks like it carries a clock: {value}"
    assert "never" not in {v.lower() for v in ts.values()}


def test_webapp_signal_names_match_the_shortcuts_on_the_phone():
    """005d §1: the one view that renders signal names must name them correctly.

    These are the shortcut names a family sees in the Shortcuts app
    (`Kettle — Charger On`), so a drift here sends someone hunting for a
    shortcut that does not exist — on the screen whose entire job is repair.
    """
    source = SIGNAL_NAMES_TS.read_text()
    block = re.search(r"SIGNAL_DISPLAY_NAMES: Record<string, string> = \{(.*?)\n\}", source, re.S)
    assert block, "SIGNAL_DISPLAY_NAMES not found in signalNames.ts"
    rendered = dict(re.findall(r'(\w+):\s*"([^"]+)"', block.group(1)))

    assert rendered == signals.SIGNAL_LABELS
    # Every signal a parent can actually be provisioned with has a name here, so
    # the app's title-case fallback never runs for the standard set.
    assert {signal for signal, _ in signals.STANDARD_SIGNALS} <= set(rendered)


def test_webapp_beacon_describes_the_handset_not_the_person():
    """Law #6 at the pixel: a mechanism signal may never anchor a person claim."""
    assert _ts_consts(COPY_TS)["BEACON_LABEL"] == "phone"


def test_privacy_footer_is_verbatim():
    """§3.3 specifies this sentence exactly."""
    assert _ts_consts(COPY_TS)["PRIVACY_FOOTER"] == (
        "Kettle stores three things: who, which routine, when. "
        "Nothing else exists to show you."
    )


def _read_surface() -> dict[str, list[str]]:
    """Parse the app's declared table/column reads out of queries.ts."""
    source = QUERIES_TS.read_text()
    block = re.search(r"READ_SURFACE = \{(.*?)\n\}", source, re.S).group(1)
    surface = {}
    for table, columns in re.findall(r'(\w+):\s*"([^"]+)"', block):
        surface[table] = [c.strip() for c in columns.split(",")]
    return surface


def test_every_table_the_app_reads_is_rls_protected(conn: psycopg.Connection):
    """AC1, structurally: the app's whole read surface is behind a policy."""
    surface = _read_surface()
    assert surface, "no read surface declared"

    for table in surface:
        row = conn.execute(
            """
            select c.relrowsecurity as rls,
                   (select count(*) from pg_policies p
                    where p.schemaname = 'public' and p.tablename = c.relname) as policies
            from pg_class c join pg_namespace n on n.oid = c.relnamespace
            where n.nspname = 'public' and c.relname = %s
            """,
            (table,),
        ).fetchone()
        assert row is not None, f"{table} does not exist"
        assert row["rls"] is True, f"{table} has RLS off"
        assert row["policies"] > 0, f"{table} has no policy"

    # The app must never reach for the founder's ops log.
    assert "ops_alerts" not in surface
    assert "ladder_events" not in surface
    assert "ladder_candidates" not in surface


def test_the_columns_the_app_asks_for_exist(conn: psycopg.Connection):
    """A typo in queries.ts should fail here, not in a demo."""
    for table, columns in _read_surface().items():
        actual = {
            r["column_name"]
            for r in conn.execute(
                "select column_name from information_schema.columns "
                "where table_schema = 'public' and table_name = %s",
                (table,),
            ).fetchall()
        }
        assert set(columns) <= actual, f"{table}: {set(columns) - actual}"


@pytest.fixture
def two_families(conn: psycopg.Connection) -> dict:
    a = provision_family(conn, "Sharma", "Asia/Kolkata", [("Amma", None)], base_url=BASE_URL)
    b = provision_family(conn, "Iyer", "America/Chicago", [("Patti", None)], base_url=BASE_URL)
    add_member(conn, a.family_id, USER_A)
    add_member(conn, b.family_id, USER_B)
    now = now_utc()
    db.insert_ping(conn, a.parents[0].parent_id, "whatsapp", now, None)
    db.insert_ping(conn, b.parents[0].parent_id, "whatsapp", now, None)
    return {"a": a, "b": b}


def test_the_apps_own_queries_return_one_family_only(two_families, authed):
    """AC1: run exactly what the app runs, as the role the app runs as.

    The app never filters by family — RLS does. So these selects carry no WHERE
    clause, which is the point: if a policy were wrong, this would return the
    other family's rows.

    Spec 005d raised the stakes on two of these tables without adding a column to
    either (item 58). `parent_signals` used to decide a beacon's shade; it now
    prints a named list of one parent's apps, and `pings` now decides what that
    list says about each of them. A leak that was a wrong tint is now a
    neighbour's tripwire inventory, so both are asserted by row rather than left
    to the loop's `families`/`parents` spot-checks.
    """
    surface = _read_surface()

    as_user(authed, USER_A)
    amma = two_families["a"].parents[0].parent_id
    for table, columns in surface.items():
        rows = authed.execute(f"select {', '.join(columns)} from {table}").fetchall()  # noqa: S608
        if table == "families":
            assert [r["name"] for r in rows] == ["Sharma"]
        if table == "parents":
            assert [r["display_name"] for r in rows] == ["Amma"]
        if table == "pings":
            assert len(rows) == 1
            assert {r["parent_id"] for r in rows} == {amma}
        if table == "parent_signals":
            # Every signal this family provisioned, and not one belonging to the
            # neighbour's parent — this is the list the detail view renders.
            assert {r["parent_id"] for r in rows} == {amma}
            assert {r["signal"] for r in rows} == {s for s, _ in signals.STANDARD_SIGNALS}
        if table == "setup_links":
            # The slug is a credential the app is allowed to *forward* (spec
            # 005b): one row, this family's parent, and never the neighbour's.
            assert {r["parent_id"] for r in rows} == {amma}
            assert len(rows) == 1

    as_user(authed, USER_B)
    patti = two_families["b"].parents[0].parent_id
    assert [
        r["name"] for r in authed.execute("select name from families").fetchall()
    ] == ["Iyer"]
    assert [
        r["display_name"] for r in authed.execute("select display_name from parents").fetchall()
    ] == ["Patti"]
    assert {
        r["parent_id"]
        for r in authed.execute("select parent_id from parent_signals").fetchall()
    } == {patti}


def test_the_app_never_writes(two_families, authed):
    """Read-only means read-only, and the grants say so."""
    as_user(authed, USER_A)
    for statement in (
        "insert into pings (parent_id, signal, ts_utc) "
        "select id, 'whatsapp', now() from parents limit 1",
        "update parents set display_name = 'x'",
        "delete from digest_sends",
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            authed.execute(statement)
