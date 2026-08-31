"""The weekly site summary (DECISIONS 201/211/212).

The four properties the design doc named as tests, plus the ones that turned
out to carry weight once the thing was built: that the endpoint is a write and
not a read, that the high-water upsert survives a counter restart without
erasing the morning, and that no path off the allowlist can become a row.

Every assertion about what is STORED is really an assertion about DECISIONS
201: counts, and nothing that was ever a request line.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import psycopg
import pytest
from fastapi.testclient import TestClient

from kettle import site_metrics
from kettle.main import create_app
from kettle.site_metrics import (
    WeekRow,
    claim_week,
    due_week,
    maybe_send_weekly,
    record_daily,
    render_weekly_email,
    valid_path,
    week_rows,
    week_start_for,
)

TOKEN = "metrics-token-for-tests"
DAY = date(2026, 8, 31)


@pytest.fixture
def metrics_client(settings, notifier, conn):
    """An app with the metrics token configured."""
    configured = replace(settings, site_metrics_token=TOKEN)
    with TestClient(create_app(configured, notifier)) as c:
        yield c


def stored(conn: psycopg.Connection) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute("select path, count from site_daily_counts order by path")
        return {row["path"]: row["count"] for row in cur.fetchall()}


# --- the endpoint's door ------------------------------------------------------


def test_without_a_token_configured_the_endpoint_does_not_exist(client):
    """Fail-closed, the shape /outbound/reply already uses.

    An unauthenticated counts endpoint is a way to write junk into the only
    numbers the founder has, so it is a 404 rather than an open door.
    """
    response = client.post("/site-metrics/daily", json={"day": "2026-08-31", "counts": {}})
    assert response.status_code == 404


def test_a_wrong_or_missing_token_is_401(metrics_client, conn):
    wrong = [{}, {"x-kettle-metrics-token": "not-the-token"}, {"x-kettle-metrics-token": ""}]
    for headers in wrong:
        response = metrics_client.post(
            "/site-metrics/daily",
            json={"day": "2026-08-31", "counts": {"/": 5}},
            headers=headers,
        )
        assert response.status_code == 401, headers
    assert stored(conn) == {}


def test_the_right_token_writes_and_reports_only_how_many(metrics_client, conn):
    response = metrics_client.post(
        "/site-metrics/daily",
        json={"day": "2026-08-31", "counts": {"/": 12, "other": 3}},
        headers={"x-kettle-metrics-token": TOKEN},
    )
    assert response.status_code == 200
    # A count of rows written, never the counts themselves: this route holds a
    # write token, and echoing the numbers back would make it a read too.
    assert response.text == "2"
    assert stored(conn) == {"/": 12, "other": 3}


@pytest.mark.parametrize(
    "payload",
    [
        {"day": "not-a-date", "counts": {}},
        {"day": "2026-08-31"},
        {"counts": {}},
        {"day": "2026-08-31", "counts": "twelve"},
        ["not", "a", "dict"],
    ],
)
def test_a_malformed_body_is_a_400_and_writes_nothing(metrics_client, conn, payload):
    response = metrics_client.post(
        "/site-metrics/daily", json=payload, headers={"x-kettle-metrics-token": TOKEN}
    )
    assert response.status_code == 400
    assert stored(conn) == {}


def test_an_oversized_body_is_refused(metrics_client, conn):
    counts = {f"/p{n}": 1 for n in range(site_metrics.MAX_PATHS_PER_POST + 1)}
    response = metrics_client.post(
        "/site-metrics/daily",
        json={"day": "2026-08-31", "counts": counts},
        headers={"x-kettle-metrics-token": TOKEN},
    )
    assert response.status_code == 400
    assert stored(conn) == {}


# --- idempotency, and the restart it is really about --------------------------


def test_re_posting_the_same_day_never_doubles(conn):
    """The design's idempotency requirement, stated as its own test."""
    for _ in range(3):
        record_daily(conn, DAY, {"/": 10, "/blog/": 4})
    assert stored(conn) == {"/": 10, "/blog/": 4}


def test_a_later_post_raises_a_count_but_a_smaller_one_cannot_lower_it(conn):
    """The high-water mark, which is what makes a restart survivable.

    The site app runs with `auto_stop_machines`, so the counter is stopped and
    restarted freely through the day and comes back counting from zero. Under a
    plain last-write-wins upsert that second process would ERASE the morning it
    never saw. The maximum is kept instead: what is lost is only the requests
    during the gap, which is exactly the partial day the design doc accepts and
    the email footer states out loud.
    """
    record_daily(conn, DAY, {"/": 40})
    record_daily(conn, DAY, {"/": 55})
    assert stored(conn) == {"/": 55}
    record_daily(conn, DAY, {"/": 3})
    assert stored(conn) == {"/": 55}


def test_days_do_not_bleed_into_each_other(conn):
    record_daily(conn, DAY, {"/": 5})
    record_daily(conn, date(2026, 9, 1), {"/": 9})
    with conn.cursor() as cur:
        cur.execute("select day, count from site_daily_counts where path = '/' order by day")
        assert [(r["day"], r["count"]) for r in cur.fetchall()] == [
            (DAY, 5),
            (date(2026, 9, 1), 9),
        ]


# --- what may become a row ----------------------------------------------------


@pytest.mark.parametrize(
    "path",
    ["/", "/blog/", "/resources/normal-day/normal-day-print.pdf", "other"],
)
def test_well_formed_paths_are_accepted(path):
    assert valid_path(path)


@pytest.mark.parametrize(
    "path",
    [
        "/search?q=secret",          # a query string is content, never a bucket
        "/page#fragment",
        "relative/path",
        "/with space",
        "/with\nnewline",
        "/" + "x" * 300,             # past the column's own check
        "/café",                # non-ascii: the site serves none
    ],
)
def test_malformed_paths_never_reach_the_table(conn, path):
    assert not valid_path(path)
    # And the writer drops them rather than trusting the caller.
    record_daily(conn, DAY, {path: 4, "/": 1})
    assert stored(conn) == {"/": 1}


# --- the week's arithmetic ----------------------------------------------------


def test_week_rows_pair_each_path_with_the_week_before(conn):
    monday = date(2026, 8, 31)
    record_daily(conn, monday, {"/": 10})
    record_daily(conn, monday + timedelta(days=2), {"/": 5, "/blog/": 2})
    record_daily(conn, monday - timedelta(days=3), {"/": 40})

    rows = {row.path: row for row in week_rows(conn, monday)}
    assert rows["/"].this_week == 15
    assert rows["/"].last_week == 40
    assert rows["/blog/"].this_week == 2
    assert rows["/blog/"].last_week == 0


def test_week_start_is_the_monday_in_eastern_terms():
    # A Monday 00:30 ET moment is 04:30 UTC the same day.
    assert week_start_for(datetime(2026, 8, 31, 4, 30, tzinfo=UTC)) == date(2026, 8, 31)
    # A Sunday belongs to the week that began the previous Monday.
    assert week_start_for(datetime(2026, 9, 6, 12, 0, tzinfo=UTC)) == date(2026, 8, 31)


# --- the Monday note ----------------------------------------------------------


def test_the_first_week_renders_with_no_data_at_all():
    """The design's zero-data case: the job runs before anything is counted.

    An empty shape would read as a broken job, so the email says in words that
    nothing was counted, and still carries the footer that explains why a
    number can be short.
    """
    subject, body = render_weekly_email([], date(2026, 8, 31))
    assert subject == "Kettle site, week of August 31"
    assert "Nothing was counted this week." in body
    assert site_metrics.FOOTER in body
    # No empty table headings left stranded above nothing.
    assert "PAGES" not in body
    assert "PDF DOWNLOADS" not in body


def test_pdf_downloads_are_called_out_separately():
    """The resources strategy is judged on downloads (the design's words).

    A PDF buried in a page list is not an answer to that question, so the two
    get their own sections and their own totals.
    """
    rows = [
        WeekRow("/", 100, 90),
        WeekRow("/resources/normal-day/normal-day-print.pdf", 12, 4),
    ]
    _, body = render_weekly_email(rows, date(2026, 8, 31))
    pages, _, pdfs = body.partition("PDF DOWNLOADS")
    assert "PAGES" in pages
    assert "/" in pages
    assert "normal-day-print.pdf" in pdfs
    assert "normal-day-print.pdf" not in pages
    assert "Pages 100 (was 90). PDF downloads 12 (was 4)." in body


def test_every_row_carries_its_week_over_week_number():
    rows = [WeekRow("/blog/", 7, 3)]
    _, body = render_weekly_email(rows, date(2026, 8, 31))
    assert "/blog/" in body
    assert "7" in body
    assert "(was 3)" in body


def test_the_footer_says_a_restart_can_cost_part_of_a_day():
    """DECISIONS 211 asked for the caveat out loud, every week.

    A limitation recorded only in a runbook is a limitation nobody rereads.
    """
    _, body = render_weekly_email([WeekRow("/", 1, 0)], date(2026, 8, 31))
    assert "short by part of a day" in body


# --- when it fires, and how often ---------------------------------------------


def test_the_window_is_monday_9am_eastern_and_reports_the_week_behind():
    # Monday 2026-09-07 09:15 ET is 13:15 UTC (EDT, UTC-4).
    inside = datetime(2026, 9, 7, 13, 15, tzinfo=UTC)
    assert due_week(inside) == date(2026, 8, 31)


@pytest.mark.parametrize(
    "moment",
    [
        datetime(2026, 9, 7, 12, 30, tzinfo=UTC),  # Monday 08:30 ET, too early
        datetime(2026, 9, 7, 14, 30, tzinfo=UTC),  # Monday 10:30 ET, too late
        datetime(2026, 9, 8, 13, 15, tzinfo=UTC),  # Tuesday
        datetime(2026, 9, 6, 13, 15, tzinfo=UTC),  # Sunday
    ],
)
def test_outside_the_window_nothing_is_due(moment):
    assert due_week(moment) is None


def test_a_week_can_be_claimed_exactly_once(conn):
    """The insert IS the lock.

    The ops loop runs every minute and the window is an hour wide, so without
    this the founder would get sixty copies of the same note.
    """
    week = date(2026, 8, 31)
    assert claim_week(conn, week) is True
    assert claim_week(conn, week) is False
    assert claim_week(conn, date(2026, 9, 7)) is True


class FakeResend:
    """Stands in for httpx.Client, recording what would have been sent."""

    def __init__(self, status: int = 200) -> None:
        self.status = status
        self.calls: list[dict] = []

    def post(self, url, headers=None, json=None):  # noqa: A002 - httpx's name
        self.calls.append({"url": url, "headers": headers or {}, "json": json or {}})
        return type("R", (), {"status_code": self.status})()


def test_the_weekly_pass_sends_once_and_only_inside_the_window(conn, settings):
    configured = replace(
        settings, resend_api_key="re_test", site_metrics_email="founder@example.com"
    )
    record_daily(conn, date(2026, 8, 31), {"/": 20})
    monday = datetime(2026, 9, 7, 13, 15, tzinfo=UTC)

    resend = FakeResend()
    assert maybe_send_weekly(conn, configured, monday, client=resend) == date(2026, 8, 31)
    assert len(resend.calls) == 1
    # A second pass a minute later inside the same window sends nothing.
    later = datetime(2026, 9, 7, 13, 16, tzinfo=UTC)
    assert maybe_send_weekly(conn, configured, later, client=resend) is None
    assert len(resend.calls) == 1


def test_the_note_goes_to_the_founder_address_and_nowhere_else(conn, settings):
    """Product law #3, made structural rather than careful.

    The only address this path can reach is the one env var the founder set:
    it does not touch the template registry, the family transports, or any
    table with a person in it.
    """
    configured = replace(
        settings, resend_api_key="re_test", site_metrics_email="founder@example.com"
    )
    resend = FakeResend()
    maybe_send_weekly(conn, configured, datetime(2026, 9, 7, 13, 15, tzinfo=UTC), client=resend)
    sent = resend.calls[0]["json"]
    assert sent["to"] == ["founder@example.com"]
    # Plain text only: an ops note about page counts has nothing to gain from
    # a rendered wrapper, and the plain part IS the message.
    assert "html" not in sent
    assert sent["text"]


def test_an_unconfigured_deploy_is_quiet_rather_than_broken(conn, settings):
    """No key or no address means no email, and no exception either."""
    monday = datetime(2026, 9, 7, 13, 15, tzinfo=UTC)
    assert maybe_send_weekly(conn, settings, monday, client=FakeResend()) is None
    assert maybe_send_weekly(
        conn, replace(settings, resend_api_key="re_test"), monday, client=FakeResend()
    ) is None


def test_a_refused_send_does_not_retry_the_same_note_forever(conn, settings):
    """A flapping Resend must not mean sixty copies once it recovers.

    The claim stands even on failure: the failure is in the logs, and next
    Monday carries the week-over-week column anyway.
    """
    configured = replace(
        settings, resend_api_key="re_test", site_metrics_email="founder@example.com"
    )
    monday = datetime(2026, 9, 7, 13, 15, tzinfo=UTC)
    refusing = FakeResend(status=500)
    assert maybe_send_weekly(conn, configured, monday, client=refusing) is None
    assert len(refusing.calls) == 1
    recovered = FakeResend()
    assert maybe_send_weekly(conn, configured, monday, client=recovered) is None
    assert recovered.calls == []
