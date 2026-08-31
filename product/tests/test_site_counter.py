"""The counter sidecar that runs beside nginx in the site image.

It lives in site/ because that is where it is deployed, and it is tested from
here because this is the repo's Python suite and the properties that matter are
Python ones. Loaded by path rather than imported by name: site/ is not a
package and must not become one just to be tested.

The property this file exists for is the allowlist. Everything the counter has
not been told about collapses to one bucket BEFORE it is counted, which is what
keeps a URL somebody probed us with from ever being written down.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parent.parent.parent / "site"
COUNTER_PY = SITE / "counter" / "kettle_counter.py"


def _load():
    spec = importlib.util.spec_from_file_location("kettle_counter", COUNTER_PY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


counter = _load()


@pytest.fixture
def allowlist():
    """The REAL allowlist, derived from the sitemap the site actually ships."""
    return counter.allowlist_from_sitemap((SITE / "public" / "sitemap.xml").read_text())


# --- the allowlist ------------------------------------------------------------


def test_the_allowlist_is_derived_from_the_shipped_sitemap(allowlist):
    """Derived, never transcribed: two copies of a list drift.

    A page added to the sitemap is counted with no second edit, and the PDFs
    need no separate rule because the sitemap already carries them.
    """
    assert "/" in allowlist
    assert "/resources/" in allowlist
    assert "/resources/normal-day/normal-day-print.pdf" in allowlist
    # Every entry is a path, never a URL: nothing with a host in it.
    assert all(path.startswith("/") for path in allowlist)
    assert not any("heykettle.com" in path for path in allowlist)


def test_paths_off_the_allowlist_are_bucketed_as_other(allowlist):
    """The design's fourth test, and the privacy-carrying one.

    A probe, a typo, a scanner walking wp-admin: none of them becomes a row,
    and none of them is written down anywhere.
    """
    tally = counter.Tally()
    for path in (
        "/wp-admin/install.php",
        "/.env",
        "/nope",
        "/resources/not-a-real-thing.pdf",
    ):
        counter.consume(f"2026-08-31T10:00:00+00:00 200 {path}", tally, allowlist)
    day = tally.snapshot()["2026-08-31"]
    assert day == {"other": 4}
    assert "/wp-admin/install.php" not in str(day)


def test_an_allowlisted_path_is_counted_under_its_own_name(allowlist):
    tally = counter.Tally()
    for _ in range(3):
        counter.consume("2026-08-31T10:00:00+00:00 200 /", tally, allowlist)
    counter.consume("2026-08-31T10:00:00+00:00 200 /resources/", tally, allowlist)
    assert tally.snapshot()["2026-08-31"] == {"/": 3, "/resources/": 1}


def test_an_unparseable_sitemap_degrades_instead_of_crashing():
    """A broken sitemap must never be able to stop the site serving."""
    assert counter.allowlist_from_sitemap("<not xml") == frozenset()


# --- what counts as a view ----------------------------------------------------


@pytest.mark.parametrize("status", [200, 206, 299, 304])
def test_served_and_revalidated_responses_count(status):
    assert counter.counted(status)


@pytest.mark.parametrize("status", [301, 302, 400, 403, 404, 499, 500, 502])
def test_redirects_and_errors_are_not_views(status):
    assert not counter.counted(status)


# --- the shapes nginx actually logs -------------------------------------------


def test_the_index_suffix_is_folded_back_to_the_sitemap_form(allowlist):
    """nginx logs the post-rewrite $uri, so /blog/ arrives as /blog/index.html.

    Without this fold a sitemap-derived allowlist matches almost no real
    traffic, and every page read lands in `other`.
    """
    assert counter.normalise_path("/blog/index.html") == "/blog/"
    assert counter.normalise_path("/index.html") == "/"
    tally = counter.Tally()
    counter.consume("2026-08-31T10:00:00+00:00 200 /blog/index.html", tally, allowlist)
    assert tally.snapshot()["2026-08-31"] == {"/blog/": 1}


def test_a_query_string_can_never_become_part_of_a_bucket():
    """Defence in depth: the log format carries no query string at all.

    $uri rather than $request is what guarantees it upstream; this is the
    second line, in case a format is ever edited without reading why.
    """
    assert counter.normalise_path("/search?q=a-private-thing") == "/search"
    assert counter.normalise_path("/page#frag") == "/page"


def test_a_line_that_does_not_match_the_format_is_dropped(allowlist):
    """nginx's error log and anything else on the stream is not a count."""
    tally = counter.Tally()
    for line in (
        "",
        "2026/08/31 10:00:00 [error] 7#7: *1 open() failed",
        "garbage",
        "2026-08-31T10:00:00+00:00 200",
    ):
        counter.consume(line, tally, allowlist)
    assert tally.snapshot() == {}


def test_the_day_comes_from_the_line_not_the_clock(allowlist):
    """A line written just before midnight belongs to the day it happened."""
    tally = counter.Tally()
    counter.consume("2026-08-31T23:59:59+00:00 200 /", tally, allowlist)
    counter.consume("2026-09-01T00:00:01+00:00 200 /", tally, allowlist)
    assert sorted(tally.snapshot()) == ["2026-08-31", "2026-09-01"]


# --- what leaves the process --------------------------------------------------


def test_the_tally_holds_counts_and_nothing_else(allowlist):
    """The whole privacy claim, stated as a shape.

    Whatever is in this structure is what can be shipped; if it is only
    {day: {path: int}} then there is nothing else to ship.
    """
    tally = counter.Tally()
    counter.consume("2026-08-31T10:00:00+00:00 200 /", tally, allowlist)
    snapshot = tally.snapshot()
    assert all(isinstance(day, str) for day in snapshot)
    for counts in snapshot.values():
        assert all(isinstance(path, str) for path in counts)
        assert all(isinstance(value, int) for value in counts.values())


def test_a_shipped_day_is_forgotten_and_today_is_kept(allowlist):
    tally = counter.Tally()
    counter.consume("2026-08-30T10:00:00+00:00 200 /", tally, allowlist)
    counter.consume("2026-08-31T10:00:00+00:00 200 /", tally, allowlist)
    tally.forget_before("2026-08-31")
    assert sorted(tally.snapshot()) == ["2026-08-31"]
