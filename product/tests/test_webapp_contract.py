"""The webapp's contract with the backend, checked from the Python side.

Two things a JS test cannot check for itself:

* that the copy it renders is still the copy the backend sends (AC3's templates
  live in two languages now, and drift would be silent);
* that every table the app reads is RLS-protected and returns only the caller's
  family (AC1's isolation proof, at the app's actual read surface).
"""

from __future__ import annotations

import re
from pathlib import Path

import psycopg
import pytest

from kettle import db, messages
from kettle.provisioning import provision_family
from kettle.timeutil import now_utc
from testsupport import BASE_URL, add_member, as_user

WEBAPP = Path(__file__).resolve().parent.parent.parent / "webapp"
COPY_TS = WEBAPP / "src" / "lib" / "copy.ts"
QUERIES_TS = WEBAPP / "src" / "lib" / "queries.ts"

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
    """
    surface = _read_surface()

    as_user(authed, USER_A)
    for table, columns in surface.items():
        rows = authed.execute(f"select {', '.join(columns)} from {table}").fetchall()  # noqa: S608
        if table == "families":
            assert [r["name"] for r in rows] == ["Sharma"]
        if table == "parents":
            assert [r["display_name"] for r in rows] == ["Amma"]
        if table == "pings":
            assert len(rows) == 1

    as_user(authed, USER_B)
    assert [
        r["name"] for r in authed.execute("select name from families").fetchall()
    ] == ["Iyer"]
    assert [
        r["display_name"] for r in authed.execute("select display_name from parents").fetchall()
    ] == ["Patti"]


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
