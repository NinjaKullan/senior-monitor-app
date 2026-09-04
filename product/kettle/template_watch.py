"""The ask template's category, watched daily (DECISIONS 262, item 1 of 263).

v7 is the only approved-and-Utility WhatsApp template, and a Utility category
is what lets it reach a US number at all (216). Meta re-reviews templates on
its own schedule; if v7 ever comes back Marketing, US delivery stops with no
error on our side — the send is accepted and never arrives. So once a day the
ops loop asks Twilio's Content API what the live template's WhatsApp approval
status and category are, and anything other than approved/Utility raises one
founder-only ops alert per UTC day.

Founder-only by construction (product law #3): the alert goes to ops_alerts
and ntfy, nothing family- or parent-facing. Nothing here decides whether to
send; it only reports what Meta currently thinks of the words we send.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import httpx
import psycopg

from kettle import db
from kettle.notify import Notifier

log = logging.getLogger("kettle.template_watch")

KIND_TEMPLATE_CATEGORY = "template_category"
CONTENT_API = "https://content.twilio.com/v1/Content"
EXPECTED_STATUS = "approved"
EXPECTED_CATEGORY = "utility"
# A failed fetch is logged and skipped, then tried again after this long —
# often enough that a Twilio blip does not lose the day's check, rarely enough
# that an outage is one log line an hour rather than one a minute.
RETRY_AFTER = timedelta(hours=1)


@dataclass(frozen=True)
class TemplateStanding:
    """What Meta currently says about the template."""

    sid: str
    status: str
    category: str

    @property
    def is_utility(self) -> bool:
        return (
            self.status.lower() == EXPECTED_STATUS
            and self.category.lower() == EXPECTED_CATEGORY
        )


@dataclass
class WatchState:
    """In-process memory of the watch: which UTC day was last checked, and
    when the last attempt was made. A restart re-checks, which is harmless —
    the alert itself dedupes in the database, not here."""

    checked_day: date | None = None
    last_attempt_utc: datetime | None = None


def fetch_standing(
    sid: str, account_sid: str, auth_token: str, client: httpx.Client
) -> TemplateStanding:
    """One GET to the Content API's approval endpoint.

    Raises httpx.HTTPError (transport or non-2xx) or ValueError (a body that
    is not the shape documented) — the caller treats both as "could not
    check today", never as "the template is bad".
    """
    response = client.get(
        f"{CONTENT_API}/{sid}/ApprovalRequests", auth=(account_sid, auth_token)
    )
    response.raise_for_status()
    body = response.json()
    whatsapp = body.get("whatsapp") if isinstance(body, dict) else None
    if not isinstance(whatsapp, dict):
        raise ValueError("approval response carries no whatsapp block")
    return TemplateStanding(
        sid=sid,
        status=str(whatsapp.get("status") or "unknown"),
        category=str(whatsapp.get("category") or "unknown"),
    )


def alert_detail(standing: TemplateStanding) -> str:
    return (
        f"⚠️ Ask template {standing.sid} is {standing.status}/{standing.category}, "
        "not approved/utility. US delivery stops silently on a non-Utility "
        "template (DECISIONS 216/262) — read the template page in Twilio."
    )


def _alerted_today(conn: psycopg.Connection, now: datetime) -> bool:
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    row = conn.execute(
        """
        select 1 from ops_alerts
        where kind = %s and family_id is null
          and ts_utc >= %s and ts_utc < %s
        limit 1
        """,
        (KIND_TEMPLATE_CATEGORY, start, start + timedelta(days=1)),
    ).fetchone()
    return row is not None


def check_once(
    conn: psycopg.Connection,
    settings: Any,
    notifier: Notifier,
    now: datetime,
    client: httpx.Client | None = None,
) -> TemplateStanding | None:
    """Fetch the standing and alert if it is not Utility. Returns the standing,
    or None when the fetch failed (logged, nothing raised, nothing written).

    Idempotent per UTC day: a second call on the same day with the same bad
    answer adds no row and sends nothing.
    """
    sid = getattr(settings, "twilio_ask_content_sid", "")
    account_sid = getattr(settings, "twilio_account_sid", "")
    auth_token = getattr(settings, "twilio_auth_token", "")
    if not (sid and account_sid and auth_token):
        return None
    http = client or httpx.Client(timeout=10.0)
    try:
        standing = fetch_standing(sid, account_sid, auth_token, http)
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("template watch: could not fetch %s (%s); skipping", sid, exc)
        return None
    if standing.is_utility:
        return standing
    if _alerted_today(conn, now):
        return standing
    detail = alert_detail(standing)
    db.insert_ops_alert(conn, None, None, KIND_TEMPLATE_CATEGORY, detail, now)
    notifier.send(detail)
    log.info("ops alert kind=%s sid=%s", KIND_TEMPLATE_CATEGORY, sid)
    return standing


def maybe_check(
    conn: psycopg.Connection,
    settings: Any,
    notifier: Notifier,
    state: WatchState,
    now: datetime,
    client: httpx.Client | None = None,
) -> TemplateStanding | None:
    """The once-a-day gate in front of check_once, for a loop that runs every
    minute. A day counts as checked only when the fetch succeeded; a failure
    is retried after RETRY_AFTER, and never more often than that."""
    today = now.date()
    if state.checked_day == today:
        return None
    if state.last_attempt_utc is not None and now - state.last_attempt_utc < RETRY_AFTER:
        return None
    state.last_attempt_utc = now
    standing = check_once(conn, settings, notifier, now, client)
    if standing is not None:
        state.checked_day = today
    return standing
