"""What the site served, and the founder's Monday note about it.

DECISIONS 201 is the standing law this serves: the site measures itself with
server logs and Search Console and nothing else, ever — no client-side
anything. DECISIONS 211 ruled the delivery: Monday 9:00am ET, founder-only,
plain text, server counts only. docs/log-summary-job-design.md is the design
(option C, count-at-the-edge); the counter that feeds this lives in the site
container at site/counter/kettle_counter.py.

What this module holds is deliberately small: an idempotent write for a day's
counts, a week's worth of reading, and the words. What it does NOT hold is any
notion of a person. Nothing here joins to a family, a parent or a member; there
is no code path from a page count to a human being, which is why the table it
reads has three columns and no fourth.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import psycopg

log = logging.getLogger("kettle.site_metrics")

#: DECISIONS 211: the email lands Monday 9:00am ET. Eastern rather than the
#: parents' IST because this one is the founder's own working clock, and it is
#: the only surface in the system that is.
EMAIL_TZ = ZoneInfo("America/New_York")
EMAIL_HOUR = 9
EMAIL_MINUTE = 0

#: The bucket every off-allowlist path collapses into at the counter.
OTHER = "other"

#: A ceiling on how many distinct paths one POST may carry. The allowlist is
#: about thirty entries today; this is well clear of it and still refuses a
#: body that is trying to make the table grow a column's worth of rows.
MAX_PATHS_PER_POST = 500

#: Longest path string the table will hold, matching the migration's check.
MAX_PATH_LEN = 200


def valid_path(path: str) -> bool:
    """Shape check at the door, not an allowlist.

    The authoritative allowlist lives in the counter, which anonymises anything
    off it to `other` BEFORE shipping — so by the time a path arrives here it
    has already been vetted by the process that saw the request. What this
    endpoint owes is that nothing malformed reaches the table: a bounded,
    printable, query-free path, or the literal bucket name.
    """
    if path == OTHER:
        return True
    if not path.startswith("/") or len(path) > MAX_PATH_LEN:
        return False
    if any(ch in path for ch in "?#\n\r\t "):
        return False
    return path.isprintable() and path.isascii()


def record_daily(
    conn: psycopg.Connection, day: date, counts: dict[str, int]
) -> int:
    """Upsert one day's counts. Returns the number of paths written.

    **The upsert keeps a HIGH-WATER MARK, not the latest value.** The counter
    ships the day's running total repeatedly rather than once at midnight,
    because the site app runs with `auto_stop_machines` and a machine that
    stops at 11pm never reaches a midnight flush. Two properties follow, and
    both are wanted: re-POSTing an identical body changes nothing (the design's
    idempotency requirement), and a counter that restarted mid-day and is
    counting up from zero again cannot ERASE the morning it never saw. What is
    lost in that case is the requests during the gap, which is exactly the
    "a restart can cost a partial day" the design doc accepts and the email
    footer states out loud.
    """
    rows = [
        (day, path, count)
        for path, count in counts.items()
        if valid_path(path) and isinstance(count, int) and count >= 0
    ]
    if not rows:
        return 0
    with conn.cursor() as cur:
        cur.executemany(
            """
            insert into site_daily_counts (day, path, count)
            values (%s, %s, %s)
            on conflict (day, path) do update
                set count = greatest(site_daily_counts.count, excluded.count)
            """,
            rows,
        )
    conn.commit()
    return len(rows)


@dataclass(frozen=True)
class WeekRow:
    """One path's counts across the reported week and the week before it."""

    path: str
    this_week: int
    last_week: int


def week_start_for(moment: datetime) -> date:
    """The Monday that begins the week `moment` falls in, in Eastern terms."""
    local = moment.astimezone(EMAIL_TZ).date()
    return local - timedelta(days=local.weekday())


def counts_between(
    conn: psycopg.Connection, start: date, end: date
) -> dict[str, int]:
    """Per-path totals for [start, end). Absent paths are simply absent."""
    with conn.cursor() as cur:
        cur.execute(
            """
            select path, sum(count)::int as total
            from site_daily_counts
            where day >= %s and day < %s
            group by path
            """,
            (start, end),
        )
        # The app's connections carry psycopg's dict_row factory (kettle/db.py),
        # so rows are mappings and the column has to be named to be read.
        return {row["path"]: row["total"] for row in cur.fetchall()}


def week_rows(conn: psycopg.Connection, week_start: date) -> list[WeekRow]:
    """The reported week beside the one before it, busiest path first."""
    this_week = counts_between(conn, week_start, week_start + timedelta(days=7))
    last_week = counts_between(conn, week_start - timedelta(days=7), week_start)
    paths = set(this_week) | set(last_week)
    rows = [
        WeekRow(path, this_week.get(path, 0), last_week.get(path, 0))
        for path in paths
    ]
    # Busiest first, then alphabetical so the order is stable week to week and
    # a diff of two emails is readable.
    rows.sort(key=lambda row: (-row.this_week, row.path))
    return rows


def _is_pdf(path: str) -> bool:
    return path.endswith(".pdf")


def _day_phrase(day: date) -> str:
    """"March 3", without leaning on a platform-specific strftime flag."""
    return f"{day:%B} {day.day}"


def _was(count: int) -> str:
    """The week-over-week half of a line, in the plainest words available."""
    return f"(was {count})"


def _table(rows: list[WeekRow]) -> list[str]:
    """Aligned `path count (was n)` lines, widest path setting the column."""
    if not rows:
        return []
    width = min(max(len(row.path) for row in rows), 52)
    return [
        f"  {row.path.ljust(width)}  {str(row.this_week).rjust(6)}  {_was(row.last_week)}"
        for row in rows
    ]


#: The footer DECISIONS 211 asked for out loud: the number can be short, and
#: the email says so every week rather than in a runbook nobody rereads.
FOOTER = (
    "These are server counts, taken as the site answers each request. "
    "Nothing about a visitor is recorded or kept. If the site restarted "
    "during the week, a count can be short by part of a day."
)

SEARCH_CONSOLE_NOTE = (
    "Search terms and positions are not in here by design (DECISIONS 211); "
    "they stay a Search Console visit."
)


def render_weekly_email(rows: list[WeekRow], week_start: date) -> tuple[str, str]:
    """Subject and plain-text body for the Monday note. Founder-only.

    Every string in here is scanned by test_site_metrics_copy. The family copy
    law cannot apply verbatim to a page-counts email whose whole subject IS
    counts, so the scan that binds this one is the founder-ops subset: no
    medical or diagnostic vocabulary, no urgency, no claim about any person,
    and no name, address or number belonging to a family. DECISIONS 212 records
    the distinction and why it is not a loophole.
    """
    week_end = week_start + timedelta(days=6)
    subject = f"Kettle site, week of {_day_phrase(week_start)}"

    pages = [row for row in rows if not _is_pdf(row.path)]
    pdfs = [row for row in rows if _is_pdf(row.path)]

    lines = [
        f"Week of {_day_phrase(week_start)} to {_day_phrase(week_end)}.",
        "",
    ]

    if not rows:
        # The first week runs before the counter has shipped anything, and a
        # week with no traffic reads the same way. Say so plainly rather than
        # sending an empty shape that looks like a broken job.
        lines += ["Nothing was counted this week.", ""]
    else:
        if pages:
            lines += ["PAGES", *_table(pages), ""]
        if pdfs:
            # Called out separately per the design: the resources strategy is
            # judged on downloads, and a PDF buried in a page list is not an
            # answer to that question.
            lines += ["PDF DOWNLOADS", *_table(pdfs), ""]
        lines += [
            f"Pages {sum(r.this_week for r in pages)} "
            f"{_was(sum(r.last_week for r in pages))}. "
            f"PDF downloads {sum(r.this_week for r in pdfs)} "
            f"{_was(sum(r.last_week for r in pdfs))}.",
            "",
        ]

    lines += [FOOTER, "", SEARCH_CONSOLE_NOTE]
    return subject, "\n".join(lines)


def due_week(now: datetime) -> date | None:
    """The week to report if `now` is inside a Monday 9am ET send window.

    Returns the week that just ENDED (the previous Monday's week), because a
    Monday morning note is about the week behind it. Outside the window this is
    None and the loop does nothing. The window is an hour wide rather than a
    minute so that a restart, a slow pass or a clock that drifts by seconds
    cannot skip a week outright; sending only once inside it is the ledger's
    job, not the window's.
    """
    local = now.astimezone(EMAIL_TZ)
    if local.weekday() != 0:
        return None
    if not (EMAIL_HOUR <= local.hour < EMAIL_HOUR + 1):
        return None
    if local.hour == EMAIL_HOUR and local.minute < EMAIL_MINUTE:
        return None
    return week_start_for(now) - timedelta(days=7)


def claim_week(conn: psycopg.Connection, week_start: date) -> bool:
    """Claim the right to send this week's email, exactly once.

    The insert IS the lock: whoever writes the row sends, everyone else gets
    False and stops. The ops loop runs every minute inside an hour-wide window,
    so without this the founder would get sixty copies of the same note.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into site_weekly_sends (week_start)
            values (%s)
            on conflict (week_start) do nothing
            """,
            (week_start,),
        )
        claimed = cur.rowcount == 1
    conn.commit()
    return claimed


def send_weekly_email(
    api_key: str,
    from_address: str,
    to_address: str,
    subject: str,
    body: str,
    client: object | None = None,
    api_url: str = "https://api.resend.com/emails",
) -> bool:
    """POST the note to Resend. Founder-only, plain text, no template.

    Deliberately NOT routed through `ResendTransport`. That class is the
    family channel: it renders from the template registry, it carries the
    child-facing kinds, and it sends multipart HTML. This message is none of
    those things and shares none of that machinery, which keeps product law #3
    structural rather than careful — there is no code path from this function
    to a family address, because the only address it can reach is the one env
    var the founder set.
    """
    import httpx

    http = client or httpx.Client(timeout=10.0)
    try:
        response = http.post(
            api_url,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "from": from_address,
                "to": [to_address],
                "subject": subject,
                # Text only. An ops note about page counts has nothing to gain
                # from a rendered wrapper, and the plain part is the message.
                "text": body,
            },
        )
    except Exception as exc:  # noqa: BLE001 - a failed note never kills the loop
        log.warning("site metrics email did not complete: %s", type(exc).__name__)
        return False
    ok = response.status_code // 100 == 2
    if not ok:
        log.warning("site metrics email refused: HTTP %s", response.status_code)
    return ok


def maybe_send_weekly(
    conn: psycopg.Connection,
    settings: object,
    now: datetime,
    client: object | None = None,
) -> date | None:
    """One pass of the weekly job. Returns the week sent, or None.

    Called from the ops loop every minute (kettle/heartbeat.py). Everything
    that would make this a nuisance is handled before anything is sent: outside
    the Monday window it returns immediately, an unconfigured deploy returns
    immediately, and the week is claimed in the database before the send so
    sixty passes inside the window produce one email.
    """
    week = due_week(now)
    if week is None:
        return None
    api_key = getattr(settings, "resend_api_key", "")
    to_address = getattr(settings, "site_metrics_email", "")
    if not api_key or not to_address:
        return None
    if not claim_week(conn, week):
        return None
    subject, body = render_weekly_email(week_rows(conn, week), week)
    if not send_weekly_email(
        api_key,
        getattr(settings, "resend_from", ""),
        to_address,
        subject,
        body,
        client=client,
    ):
        # The claim stands even on a failed send. A retry loop here would mean
        # a flapping Resend sends the same note repeatedly, and a weekly trend
        # read is not worth that: the failure is in the logs, and next Monday
        # carries the week-over-week column anyway.
        log.warning("site metrics email for %s was claimed but not sent", week)
        return None
    return week
