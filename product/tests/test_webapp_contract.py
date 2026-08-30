"""The webapp's contract with the backend, checked from the Python side.

Two things a JS test cannot check for itself:

* that the copy it renders is still the copy the backend sends (AC3's templates
  live in two languages now, and drift would be silent);
* that every table the app reads is RLS-protected and returns only the caller's
  family (AC1's isolation proof, at the app's actual read surface);
* that the humanised signal names in `signalNames.ts` are still the names of
  the shortcuts sitting on the parent's phone (005d; since spec 008 the app
  renders none of them, but the module still keys tripwire logic and a drift
  would resurface the moment any repair surface names a shortcut again).
"""

from __future__ import annotations

import re
from pathlib import Path

import psycopg
import pytest

from kettle import db, signals
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


def test_the_digest_screen_is_retired_and_its_copy_is_gone():
    """DECISIONS 156: the Digests screen goes, and its copy goes with it.

    The five retired-spec-003 template strings must NOT reappear in `copy.ts`,
    and `digest_sends` must stay out of the app's declared read surface — from
    Wave B the digest IS the email, and a message-history screen, if families
    ever ask for one, reads a purpose-built view, never the raw ledger. Dead
    strings kept "just in case" are how retired copy leaks back onto a screen
    (the `never` precedent, DECISIONS 68).
    """
    ts = _ts_consts(COPY_TS)
    assert ts, "no exported string constants found in copy.ts"
    for name in ("MORNING_TEMPLATE", "EVENING_ONE", "EVENING_TWO", "EVENING_MANY", "CLOCK_NEUTRAL"):
        assert name not in ts, f"retired digest copy came back: {name}"
    assert "digest_sends" not in _read_surface(), (
        "digest_sends returned to the app's read surface (DECISIONS 156)"
    )


# The state sentence is the one string a family reads at an anxious moment
# (spec 008 §4: it is the card AND the hero), so it is the one the floor law
# governs. Three states, pinned verbatim: two about a person's day, and a
# third that is a sentence about a phone — see the law-#6 test below.
STATE_SENTENCES = {
    # Spec 009 §1: "normal", never "ordinary", in every rendered string.
    "STATE_ORDINARY": "Today looks like a normal day.",
    "STATE_QUIET": "Quiet so far today.",
    "STATE_UNREACHABLE": "Kettle can't hear from {name}'s phone right now.",
}


def test_webapp_state_copy_is_never_darker_than_quiet():
    """005a §3.1's floor, carried through 005c into spec 008's three states.

    `Quiet so far` is still as dark as this app ever gets about a *person*.
    The glance vocabulary this test used to pin retired with its screen
    (DECISIONS 169/170) and must stay gone — a dead constant is how retired
    copy leaks back (the `never` precedent, DECISIONS 68).
    """
    ts = _ts_consts(COPY_TS)

    assert {k: ts[k] for k in STATE_SENTENCES} == STATE_SENTENCES
    assert not {name for name in ts if name.startswith("GLANCE_")}, (
        "retired glance copy came back"
    )

    # A newly added STATE_ constant has to be classified rather than quietly
    # escaping the scan below — that is how a floor rots.
    unclassified = {
        name for name in ts if name.startswith("STATE_") and name not in STATE_SENTENCES
    }
    assert not unclassified, f"classify these against the floor: {unclassified}"

    for name in ("STATE_ORDINARY", "STATE_QUIET"):
        lowered = STATE_SENTENCES[name].lower()
        for worrying in ("no ", "not ", "unreachable", "silent", "concern", "alert"):
            assert worrying not in lowered, f"{name} is darker than the floor"
    assert STATE_SENTENCES["STATE_QUIET"].startswith("Quiet so far")


def test_webapp_fix_copy_names_no_mechanism_and_stays_gentle():
    """005d's chips retired with the rows (170); "tripwire" itself with 172.

    The word is internal vocabulary and never customer-facing, so no rendered
    string may carry it and no TRIPWIRE_ constant may exist in the copy
    module at all — identifiers elsewhere (lib/tripwires.ts, test names) keep
    it, because those are not strings a family reads. The fix card's body is
    pinned verbatim, and it still names a person only as the owner of a phone
    that needs two minutes.
    """
    ts = _ts_consts(COPY_TS)

    assert not {name for name in ts if name.startswith("TRIPWIRE_")}, (
        "retired tripwire copy came back"
    )
    for name, value in ts.items():
        assert "tripwire" not in value.lower(), f"{name} leaks mechanism vocabulary: {value}"
    assert ts["FIX_BODY"] == (
        "Something on {name}'s phone may need a quick fix. "
        "It's a two-minute FaceTime."
    )
    for worrying in ("urgent", "emergency", "alarm", "danger", "unwell", "ill", "wrong"):
        # Whole words: "still" and "will" are not "ill".
        assert not re.search(rf"\b{worrying}\b", ts["FIX_BODY"].lower())


def test_webapp_recency_copy_has_no_clock_variant_and_no_never():
    """Day-or-coarser granularity is a property of the vocabulary, not a caller.

    The RECENCY_ vocabulary retired whole with the tripwire rows (spec 009);
    the relative forms live in the HEARD_ family now, and none of them can
    carry a clock time — the constraint holds because the words to break it
    do not exist. `never` stays gone the same way (DECISIONS 68), and so does
    the "since ... ago" duration shape (spec 009 §1).
    """
    ts = _ts_consts(COPY_TS)
    assert not {name for name in ts if name.startswith("RECENCY_")}, (
        "retired recency copy came back"
    )
    heard = {name: value for name, value in ts.items() if name.startswith("HEARD_")}
    assert heard, "the relative-time vocabulary is missing"
    for name, value in heard.items():
        assert ":" not in value, f"{name} looks like it carries a clock: {value}"
    lowered = {v.lower() for v in ts.values()}
    assert "never" not in lowered
    assert not any("since" in v and "ago" in v for v in lowered), (
        "the retired since-ago duration shape came back"
    )


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


def test_webapp_unreachable_copy_describes_the_handset_not_the_person():
    """Law #6 at the pixel: a mechanism signal may never anchor a person claim.

    The beacon and its `phone` label retired with the glance (spec 008); the
    law now rides on the third state's sentences, which must stay about the
    phone. The aside is pinned verbatim — it is the string that talks a
    family down at the exact moment the temptation to say something darker
    is strongest.
    """
    ts = _ts_consts(COPY_TS)
    assert "BEACON_LABEL" not in ts, "the retired beacon's label came back"
    assert "phone" in ts["STATE_UNREACHABLE"]
    assert ts["UNREACHABLE_ASIDE"] == (
        "A call still works fine — this is only about the phone."
    )
    worrying_words = ("urgent", "emergency", "alarm", "danger", "unwell", "ill", "wrong", "silent")
    for name in ("STATE_UNREACHABLE", "UNREACHABLE_ASIDE"):
        for worrying in worrying_words:
            assert not re.search(rf"\b{worrying}\b", ts[name].lower()), (
                f"{name} reaches past the phone: {ts[name]}"
            )


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


def test_the_app_never_writes_outside_its_two_granted_paths(two_families, authed):
    """Spec 009 opened two write paths (journal inserts, the city label
    column), spec 010 widened the second to the place columns (tz,
    tz_changed_utc), and spec 012 added a third: full CRUD on
    family_contacts, RLS-bounded (tested below). Everything else the
    read-only contract used to refuse it still refuses, display_name on the
    very table the column grant touches included — and the journal itself
    stays insert-only."""
    as_user(authed, USER_A)
    for statement in (
        "insert into pings (parent_id, signal, ts_utc) "
        "select id, 'whatsapp', now() from parents limit 1",
        "update parents set display_name = 'x'",
        "delete from digest_sends",
        # v1 notes are insert-only: no edit, no delete (spec 009 §4).
        "update journal_entries set body = 'x'",
        "delete from journal_entries",
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            authed.execute(statement)


def test_journal_writes_and_reads_stay_inside_the_family(two_families, authed):
    """Spec 009 §4: RLS mirrors the 0002 shape on the app's first own table.

    Verified live against the migration before this test existed (the
    2026-08-26 probe); pinned here so it stays true: a member inserts and
    reads their own family's notes, cannot write into the neighbour's family,
    and cannot tag the neighbour's parent onto their own family's note.
    """
    a = two_families["a"]
    b = two_families["b"]
    as_user(authed, USER_A)
    authed.execute(
        "insert into journal_entries (family_id, parent_id, author_label, body, event_date) "
        "values (%s, %s, 'Hema', 'hearing aid batteries', '2026-09-01')",
        (a.family_id, a.parents[0].parent_id),
    )
    authed.execute(
        "insert into journal_entries (family_id, body) values (%s, 'a family note')",
        (a.family_id,),
    )
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute(
            "insert into journal_entries (family_id, body) values (%s, 'sneak')",
            (b.family_id,),
        )
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute(
            "insert into journal_entries (family_id, parent_id, body) values (%s, %s, 'sneak')",
            (a.family_id, b.parents[0].parent_id),
        )
    rows = authed.execute(
        "select body from journal_entries order by created_utc desc limit 50"
    ).fetchall()
    assert {r["body"] for r in rows} == {"hearing aid batteries", "a family note"}

    # The neighbour sees none of it.
    as_user(authed, USER_B)
    assert authed.execute("select count(*) as n from journal_entries").fetchone()["n"] == 0


def test_city_label_is_a_writable_parents_column(two_families, authed, conn):
    """Spec 009 §5: the update grant is COLUMN-scoped and RLS-bounded."""
    a = two_families["a"]
    as_user(authed, USER_A)
    authed.execute(
        "update parents set city_label = 'Chennai' where id = %s",
        (a.parents[0].parent_id,),
    )
    # A blanket update only ever reaches the caller's own family's rows.
    authed.execute("update parents set city_label = 'Elsewhere'")
    labels = {
        r["display_name"]: r["city_label"]
        for r in conn.execute("select display_name, city_label from parents").fetchall()
    }
    assert labels == {"Amma": "Elsewhere", "Patti": None}
    # The 40-character bound holds at the schema.
    with pytest.raises(psycopg.errors.CheckViolation):
        authed.execute(
            "update parents set city_label = %s where id = %s",
            ("x" * 41, a.parents[0].parent_id),
        )


def test_the_place_columns_are_writable_together_and_nothing_else_opened(
    two_families, authed, conn
):
    """Spec 010 §2: 0019 widens the parents grant to (tz, tz_changed_utc).

    The picker's whole write is one statement — label, zone, and the change
    stamp land together or not at all. The same RLS policy that bounded 0018's
    city_label bounds these, so a blanket update still cannot reach the
    neighbour's rows, and display_name stays refused (asserted alongside the
    other refusals in test_the_app_never_writes_outside_its_two_granted_paths).
    """
    a = two_families["a"]
    as_user(authed, USER_A)
    authed.execute(
        "update parents set city_label = 'Dallas', tz = 'America/Chicago', "
        "tz_changed_utc = now() where id = %s",
        (a.parents[0].parent_id,),
    )
    # RLS bounds a blanket update to the caller's own family.
    authed.execute("update parents set tz = 'America/Denver', tz_changed_utc = now()")
    zones = {
        r["display_name"]: (r["tz"], r["tz_changed_utc"] is not None)
        for r in conn.execute("select display_name, tz, tz_changed_utc from parents").fetchall()
    }
    assert zones == {"Amma": ("America/Denver", True), "Patti": (None, False)}


def test_contacts_are_editable_reference_data_bounded_to_the_family(
    two_families, authed, conn
):
    """Spec 012 §4: the one table the app may fully edit — and only its own
    family's rows. Contacts are reference data, not record, so unlike the
    journal every verb is granted; RLS is what keeps each verb honest."""
    a = two_families["a"]
    b = two_families["b"]
    as_user(authed, USER_A)
    authed.execute(
        "insert into family_contacts (family_id, label, name, phone_e164, phone_display) "
        "values (%s, 'A neighbor', 'Lakshmi', '+919845550111', '98455 50111')",
        (a.family_id,),
    )
    authed.execute(
        "update family_contacts set name = 'Lakshmi R' where family_id = %s",
        (a.family_id,),
    )
    # Writing into the neighbour family, or tagging their parent: refused.
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute(
            "insert into family_contacts (family_id, label) values (%s, 'sneak')",
            (b.family_id,),
        )
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute(
            "insert into family_contacts (family_id, parent_id, label) "
            "values (%s, %s, 'sneak')",
            (a.family_id, b.parents[0].parent_id),
        )

    # The neighbour sees nothing, and their blanket delete removes nothing —
    # RLS turns it into a no-op rather than an error, so the row count is the
    # assertion.
    as_user(authed, USER_B)
    assert authed.execute(
        "select count(*) as n from family_contacts"
    ).fetchone()["n"] == 0
    authed.execute("delete from family_contacts")
    assert conn.execute(
        "select count(*) as n from family_contacts"
    ).fetchone()["n"] == 1

    # The owner really can delete their own.
    as_user(authed, USER_A)
    authed.execute("delete from family_contacts where family_id = %s", (a.family_id,))
    assert conn.execute(
        "select count(*) as n from family_contacts"
    ).fetchone()["n"] == 0


def test_journal_kind_rides_the_app_write_and_stays_insert_only(
    two_families, authed, conn
):
    """Spec 012 §5: the webapp's city auto-note now names its kind; a plain
    note defaults to 'note'; an invented kind dies on the check constraint;
    and update/delete stay refused whatever the kind says."""
    a = two_families["a"]
    as_user(authed, USER_A)
    authed.execute(
        "insert into journal_entries (family_id, parent_id, author_label, body, kind) "
        "values (%s, %s, 'Kettle', 'Amma''s city changed to Austin.', 'city_change')",
        (a.family_id, a.parents[0].parent_id),
    )
    authed.execute(
        "insert into journal_entries (family_id, author_label, body) "
        "values (%s, 'Hema', 'a plain note')",
        (a.family_id,),
    )
    kinds = {
        r["body"]: r["kind"]
        for r in conn.execute("select body, kind from journal_entries").fetchall()
    }
    assert kinds == {
        "Amma's city changed to Austin.": "city_change",
        "a plain note": "note",
    }
    with pytest.raises(psycopg.errors.CheckViolation):
        authed.execute(
            "insert into journal_entries (family_id, body, kind) "
            "values (%s, 'x', 'medication_log')",
            (a.family_id,),
        )
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute("update journal_entries set kind = 'note'")
