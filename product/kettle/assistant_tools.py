"""The five read-only tools an assistant can call (spec 019 §7).

Every answer is one to three of Kettle's sentences, because it may be read
aloud: what Kettle already said (the ledger, rendered through the template
registry), the heard line, and where the parent is. Nothing here judges a
day; the engine is the only thing that decides what a day means.

The MCP server is the official SDK's `MCPServer`, mounted by main.py under
/mcp behind a bearer check that resolves a token to one auth_user_id and
puts it in `CURRENT_USER`. Each tool looks that person's circles up at call
time from `members` — never from the grant — so removing someone from a
circle removes it from their assistant in the same instant.
"""

from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar
from datetime import date, datetime, timedelta
from typing import Any

import anyio
import psycopg
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from kettle import assistant_copy as copy
from kettle import db
from kettle.assistant_auth import can_write
from kettle.outbound import MORNING_WINDOW_START
from kettle.outbound_templates import owner_first_name, render, template
from kettle.timeutil import effective_tz, local_day, now_utc, to_local

#: Spec 020 follows the day clock (299): the engine's morning window start,
#: the app's DAY_START_HOUR.
DAY_START_HOUR = MORNING_WINDOW_START.hour

#: The auth_user_id the current /mcp request stands for (set by main.py).
CURRENT_USER: ContextVar[str | None] = ContextVar("kettle_assistant_user", default=None)
#: The grant itself (Amendment A): its scope decides the write tools, its
#: client_name is the mark a dictated line carries.
CURRENT_GRANT: ContextVar[dict[str, Any] | None] = ContextVar(
    "kettle_assistant_grant", default=None
)
#: Amendment A.4: writes an hour per grant, counted from the table.
WRITE_LIMIT_PER_HOUR = 20
BODY_CAP = 2000

KIND_WORDS = {
    "digest_morning": copy.MORNING_NOTE,
    "digest_evening": copy.EVENING_NOTE,
    "ask": copy.ASK_SENT,
    "follow_on": copy.FOLLOW_ON_SENT,
    "all_clear": copy.ALL_CLEAR_SENT,
}
MEMORY_CAP = 40
#: Every tool reads and nothing else (spec 019 §1; DECISIONS 286): said in the
#: annotations, so the assistant does not ask permission on every question.
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
#: The two write tools (Amendment A.2): not read-only, so the assistant asks
#: before each; not destructive; not idempotent (two calls are two notes).
WRITES = ToolAnnotations(
    read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False
)
DAY_FLOOR = timedelta(days=60)


# --- who is asking, and what they can see ----------------------------------------


def circles_for(conn: psycopg.Connection, auth_user_id: str) -> list[dict[str, Any]]:
    """The circles this person belongs to, oldest first — the same set
    app_current_family_ids() yields, read at call time."""
    return conn.execute(
        """
        select f.id, f.name, f.tz, f.demo
        from families f
        where f.id in (select m.family_id from members m where m.auth_user_id = %s)
        order by f.created_utc, f.id
        """,
        (auth_user_id,),
    ).fetchall()


def parents_in(conn: psycopg.Connection, family_ids: list[Any]) -> list[dict[str, Any]]:
    if not family_ids:
        return []
    return conn.execute(
        """
        select p.id, p.family_id, p.display_name, p.tz, p.relationship, p.city_label,
               p.phone_e164, p.whatsapp_e164,
               case when p.paused_until is null then null
                    else least(p.paused_until, timestamptz '9999-12-31 00:00:00+00') end
                    as paused_until,
               p.paused_until = 'infinity' as open_ended,
               f.name as family_name, f.tz as family_tz
        from parents p join families f on f.id = p.family_id
        where p.family_id = any(%s)
        order by f.created_utc, p.display_name
        """,
        (family_ids,),
    ).fetchall()


def match_parents(parents: list[dict[str, Any]], asked: str | None) -> list[dict[str, Any]]:
    """Case-insensitive on display_name; every parent when nothing is asked."""
    if not asked or not asked.strip():
        return parents
    wanted = asked.strip().casefold()
    return [p for p in parents if p["display_name"].casefold() == wanted]


def no_such_parent(asked: str, parents: list[dict[str, Any]]) -> str:
    names = sorted({p["display_name"] for p in parents})
    return copy.NO_SUCH_PARENT.replace("{asked}", asked.strip()).replace(
        "{names}", join_names(names)
    )


def join_names(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} and {names[-1]}"


def prefix_for(parent: dict[str, Any], parents: list[dict[str, Any]]) -> str:
    """The name, and the circle's name too when the same name sits in two circles."""
    same = [p for p in parents if p["display_name"].casefold() == parent["display_name"].casefold()]
    if len({p["family_id"] for p in same}) > 1:
        return f"{parent['family_name']} · {parent['display_name']}"
    return parent["display_name"]


# --- rendering the ledger -------------------------------------------------------


def render_row(conn: psycopg.Connection, parent: dict[str, Any], row: dict[str, Any]) -> str:
    """One sent ledger row, through the registry, with the variables the
    engine would have used."""
    found = template(row["template_id"])
    available = {
        "relationship": parent["relationship"] or parent["display_name"],
        "owner_name": owner_first_name(db.family_owner_name(conn, parent["family_id"])),
        "name": parent["display_name"],
    }
    return render(row["template_id"], {name: available[name] for name in found.variables})


def sent_rows(conn: psycopg.Connection, parent_id: Any, day: str) -> list[dict[str, Any]]:
    return conn.execute(
        """
        select kind, template_id, sent_utc from sent_messages
        where parent_id = %s and local_date = %s and status = 'sent'
        order by sent_utc, id
        """,
        (parent_id, day),
    ).fetchall()


def clock_words(instant: datetime, tz_name: str) -> str:
    """'8:04 pm' — copy.ts's formatLocalTime."""
    local = to_local(instant, tz_name)
    hour = local.hour % 12 or 12
    return f"{hour}:{local.minute:02d} {'am' if local.hour < 12 else 'pm'}"


def join_sentences(parts: list[str]) -> str:
    """One answer from several sentences: a full stop and a space between
    them (DECISIONS 287 backlog b). The heard line and the city line carry no
    stop of their own on the app's screen; read aloud by an assistant they
    are sentences, and a sentence that runs on from the one before it reads
    as a fault."""
    ended = []
    for part in parts:
        text = part.strip()
        if text and text[-1] not in ".!?":
            text += "."
        ended.append(text)
    return " ".join(ended)


def heard_line(conn: psycopg.Connection, parent_id: Any, now: datetime) -> str:
    last = db.last_alarm_ping(conn, parent_id)
    if last is None:
        return copy.META_NOTHING_YET
    return copy.render_heard((now - last).total_seconds())


def paused_lines(parent: dict[str, Any], now: datetime) -> list[str] | None:
    until = parent["paused_until"]
    if until is None or until <= now:
        return None
    tz_name = effective_tz(parent["tz"], parent["family_tz"])
    if parent["open_ended"]:
        second = copy.PAUSED_OPEN_ENDED
    else:
        local = to_local(until, tz_name)
        second = copy.PAUSED_UNTIL.replace("{date}", f"{local.strftime('%b')} {local.day}")
    return [copy.PAUSED_CARD.replace("{name}", parent["display_name"]), second]


def place_of(parent: dict[str, Any], tz_name: str) -> str:
    """The city label, or the zone's own city when no label was picked
    ("Phoenix" from America/Phoenix) — a sentence with a blank is worse."""
    return parent["city_label"] or tz_name.split("/")[-1].replace("_", " ")


def city_now(parent: dict[str, Any], now: datetime) -> str | None:
    """CITY_NOW when the parent's clock differs from the circle's (§7)."""
    tz_name = effective_tz(parent["tz"], parent["family_tz"])
    if tz_name == parent["family_tz"]:
        return None
    return copy.CITY_NOW.replace("{city}", place_of(parent, tz_name)).replace(
        "{time}", clock_words(now, tz_name)
    )


# --- the tools ---------------------------------------------------------------------


def device_line(conn: psycopg.Connection, parent: dict[str, Any], now: datetime) -> str | None:
    """Spec 020 §5/§6: the most recent household device heard today, from
    06:00 in the parent's zone, as the card says it — a fact after the heard
    line, never a verdict. None before six (the card's night), or when no
    device has fired today. The one read of household_pings outside the
    ingest route (§4)."""
    tz_name = effective_tz(parent["tz"], parent["family_tz"])
    local = to_local(now, tz_name)
    if local.hour < DAY_START_HOUR:
        return None
    day_start = local.replace(hour=DAY_START_HOUR, minute=0, second=0, microsecond=0)
    row = conn.execute(
        """
        select d.kind, h.ts_utc from household_pings h
        join household_devices d on d.id = h.device_id
        where d.parent_id = %s and d.removed_utc is null and h.ts_utc >= %s and h.ts_utc <= %s
        order by h.ts_utc desc limit 1
        """,
        (parent["id"], day_start, now),
    ).fetchone()
    if row is None:
        return None
    hour = to_local(row["ts_utc"], tz_name).hour
    form = (
        copy.DEVICE_LINE_MORNING
        if hour < 12
        else copy.DEVICE_LINE_AFTERNOON
        if hour < 18
        else copy.DEVICE_LINE_EVENING
    )
    return form.replace("{kind}", copy.KIND_LABEL[row["kind"]]).replace(
        "{time}", clock_words(row["ts_utc"], tz_name)
    )


def today_for(conn: psycopg.Connection, parent: dict[str, Any], now: datetime) -> str:
    lines = paused_lines(parent, now)
    paused = lines is not None
    if lines is None:
        tz_name = effective_tz(parent["tz"], parent["family_tz"])
        rows = sent_rows(conn, parent["id"], local_day(now, tz_name))
        lines = [
            render_row(conn, parent, rows[-1])
            if rows
            else copy.TODAY_NOTHING_YET.replace("{name}", parent["display_name"])
        ]
    lines.append(heard_line(conn, parent["id"], now))
    device = None if paused else device_line(conn, parent, now)
    if device:
        lines.append(device)
    city = city_now(parent, now)
    if city:
        lines.append(city)
    return join_sentences(lines)


def parent_day_for(conn: psycopg.Connection, parent: dict[str, Any], day: str) -> str:
    rows = sent_rows(conn, parent["id"], day)
    if not rows:
        return copy.DAY_NOTHING.replace("{name}", parent["display_name"])
    parts = []
    for row in rows:
        word = KIND_WORDS.get(row["kind"], row["kind"]).replace("{name}", parent["display_name"])
        parts.append(f"{word}: {render_row(conn, parent, row)}")
    return join_sentences(parts)


def memory_for(
    conn: psycopg.Connection,
    circles: list[dict[str, Any]],
    parents: list[dict[str, Any]],
    parent_id: Any | None,
    since: str | None,
    today: date,
) -> str:
    family_ids = [c["id"] for c in circles]
    rows = conn.execute(
        """
        select j.id, j.family_id, j.parent_id, j.author_label, j.body, j.event_date,
               j.created_utc, j.kind, j.parent_entry_id, j.edited_utc, j.via_client,
               f.tz as family_tz
        from journal_entries j join families f on f.id = j.family_id
        where j.family_id = any(%s)
          and (%s::uuid is null or j.parent_id = %s)
          and (%s::date is null or (j.created_utc at time zone f.tz)::date >= %s)
        order by j.created_utc desc, j.id desc
        limit %s
        """,
        (family_ids, parent_id, parent_id, since, since, MEMORY_CAP * 3),
    ).fetchall()
    notes = [r for r in rows if r["parent_entry_id"] is None][:MEMORY_CAP]
    ids = {r["id"] for r in notes}
    replies: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        if r["parent_entry_id"] in ids:
            replies.setdefault(r["parent_entry_id"], []).append(r)

    def line(r: dict[str, Any], indent: str = "") -> str:
        day = to_local(r["created_utc"], r["family_tz"])
        author = r["author_label"] or (copy.AUTO_NOTE_AUTHOR if r["kind"] != "note" else "Family")
        if r.get("via_client"):
            author = copy.AUTHOR_VIA.replace("{name}", author).replace("{client}", r["via_client"])
        mark = f" · {copy.EDITED_MARK}" if r["edited_utc"] else ""
        return f"{indent}{day.strftime('%b')} {day.day}{mark} · {author}: {r['body']}"

    upcoming = [r for r in notes if r["event_date"] and r["event_date"] >= today]
    past = [r for r in notes if not (r["event_date"] and r["event_date"] >= today)]
    out: list[str] = []
    if upcoming:
        out.append(copy.UPCOMING_LABEL)
        for r in sorted(upcoming, key=lambda x: x["event_date"]):
            out.append(line(r))
            out.extend(
                line(x, "  ")
                for x in sorted(replies.get(r["id"], []), key=lambda x: x["created_utc"])
            )
    for r in past:
        out.append(line(r))
        out.extend(
            line(x, "  ") for x in sorted(replies.get(r["id"], []), key=lambda x: x["created_utc"])
        )
    return "\n".join(out) if out else "Nothing in the family's notes yet."


def who_to_call_for(conn: psycopg.Connection, parent: dict[str, Any]) -> str:
    lines: list[str] = []
    number = parent["phone_e164"] or parent["whatsapp_e164"]
    if number:
        lines.append(f"{copy.CALL_LABEL.replace('{name}', parent['display_name'])} {number}")
    contacts = conn.execute(
        """
        select name, label, phone_display, phone_e164, note from family_contacts
        where family_id = %s and (parent_id is null or parent_id = %s)
        order by position, id
        """,
        (parent["family_id"], parent["id"]),
    ).fetchall()
    for c in contacts:
        who = c["name"] or c["label"]
        phone = c["phone_display"] or c["phone_e164"]
        lines.append(" · ".join(part for part in (who, phone, c["note"]) if part))
    return "\n".join(lines) if lines else "The family has not listed anyone to call yet."


def circles_text(conn: psycopg.Connection, circles: list[dict[str, Any]], now: datetime) -> str:
    out: list[str] = []
    parents = parents_in(conn, [c["id"] for c in circles])
    for circle in circles:
        out.append(circle["name"])
        for p in [x for x in parents if x["family_id"] == circle["id"]]:
            tz_name = effective_tz(p["tz"], p["family_tz"])
            where = copy.CITY_NOW.replace("{city}", place_of(p, tz_name)).replace(
                "{time}", clock_words(now, tz_name)
            )
            out.append(f"  {p['display_name']} · {where}")
        members = conn.execute(
            "select display_name, role from members where family_id = %s order by created_utc, id",
            (circle["id"],),
        ).fetchall()
        for m in members:
            out.append(f"  {m['display_name'] or 'Someone'} ({m['role']})")
    return "\n".join(out)


# --- the writes (Amendment A) ------------------------------------------------------


def member_for(conn: psycopg.Connection, auth_user_id: str, family_id: Any) -> Any | None:
    """The person's seat in this family, read at call time (A.5): removed
    from the circle, there is no seat and nothing lands."""
    return conn.execute(
        """
        select id, display_name from members
        where family_id = %s and auth_user_id = %s
        order by created_utc, id limit 1
        """,
        (family_id, auth_user_id),
    ).fetchone()


def writes_this_hour(conn: psycopg.Connection, auth_user_id: str, now: datetime) -> int:
    """A.4: rows with this person's author_member_id and a via_client mark
    in the last hour, on the injected clock."""
    row = conn.execute(
        """
        select count(*) as n from journal_entries j
        where j.via_client is not null and j.created_utc > %s
          and j.author_member_id in (select id from members where auth_user_id = %s)
        """,
        (now - timedelta(hours=1), auth_user_id),
    ).fetchone()
    return int(row["n"])


def _parse_date(value: str | None) -> date | None | bool:
    """None for no date, a date, or False for a date that is not YYYY-MM-DD."""
    if value is None or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return False


def _app(app_origin: str) -> str:
    return app_origin.rstrip("/")


def add_note_for(
    conn: psycopg.Connection,
    grant: dict[str, Any],
    text: str,
    parent: str | None,
    when: str | None,
    now: datetime,
    app_origin: str,
) -> str:
    """A.3.1: a note in the family's Memory, in the person's own words."""
    if not can_write(grant.get("scope")):
        return copy.NEED_WRITE
    user = grant["auth_user_id"]
    circles = circles_for(conn, user)
    parents = parents_in(conn, [c["id"] for c in circles])
    parent_id = None
    if parent and parent.strip():
        chosen = match_parents(parents, parent)
        if not chosen:
            return no_such_parent(parent, parents)
        if len({p["family_id"] for p in chosen}) > 1:
            return copy.WHICH_PARENT.replace("{names}", join_names(_circle_names(chosen)))
        family_id = chosen[0]["family_id"]
        parent_id = chosen[0]["id"]
    elif len(circles) == 1:
        family_id = circles[0]["id"]
    else:
        names = sorted({p["display_name"] for p in parents})
        return copy.WHICH_PARENT.replace("{names}", join_names(names))
    body = text.strip()
    event_date = _parse_date(when)
    if not body or len(body) > BODY_CAP or event_date is False:
        return copy.CANNOT_SAVE.replace("{app}", _app(app_origin))
    member = member_for(conn, user, family_id)
    if member is None:
        names = sorted({p["display_name"] for p in parents})
        return copy.WHICH_PARENT.replace("{names}", join_names(names))
    if writes_this_hour(conn, user, now) >= WRITE_LIMIT_PER_HOUR:
        return copy.WRITE_LIMIT.replace("{app}", _app(app_origin))
    conn.execute(
        """
        insert into journal_entries
            (family_id, parent_id, author_label, author_member_id, via_client, body,
             event_date, kind, created_utc)
        values (%s, %s, %s, %s, %s, %s, %s, 'note', %s)
        """,
        (
            family_id,
            parent_id,
            member["display_name"] or "",
            member["id"],
            grant.get("client_name") or copy.ASSISTANT_FALLBACK,
            body,
            event_date,
            now,
        ),
    )
    return copy.NOTE_SAVED


def _circle_names(chosen: list[dict[str, Any]]) -> list[str]:
    return [f"{p['family_name']} · {p['display_name']}" for p in chosen]


def reply_for(
    conn: psycopg.Connection,
    grant: dict[str, Any],
    text: str,
    author: str | None,
    when: str | None,
    now: datetime,
    app_origin: str,
) -> str:
    """A.3.2: a reply under the newest note in the person's circles, or the
    one an author or a date picks out. The 016 trigger still guards."""
    if not can_write(grant.get("scope")):
        return copy.NEED_WRITE
    user = grant["auth_user_id"]
    circles = circles_for(conn, user)
    family_ids = [c["id"] for c in circles]
    on_date = _parse_date(when)
    if on_date is False:
        return copy.NO_NOTE_TO_ANSWER
    wanted = (author or "").strip().casefold() or None
    target = conn.execute(
        """
        select j.id, j.family_id, j.author_label, j.author_member_id, j.created_utc,
               f.tz as family_tz, m.display_name as member_name
        from journal_entries j
        join families f on f.id = j.family_id
        left join members m on m.id = j.author_member_id
        where j.family_id = any(%s) and j.kind = 'note' and j.parent_entry_id is null
          and (%s::text is null or lower(coalesce(m.display_name, '')) = %s
               or lower(j.author_label) = %s)
          and (%s::date is null or (j.created_utc at time zone f.tz)::date = %s)
        order by j.created_utc desc, j.id desc
        limit 1
        """,
        (family_ids, wanted, wanted, wanted, on_date, on_date),
    ).fetchone()
    if target is None:
        return copy.NO_NOTE_TO_ANSWER
    body = text.strip()
    if not body or len(body) > BODY_CAP:
        return copy.CANNOT_SAVE.replace("{app}", _app(app_origin))
    member = member_for(conn, user, target["family_id"])
    if member is None:
        parents = parents_in(conn, family_ids)
        names = sorted({p["display_name"] for p in parents})
        return copy.WHICH_PARENT.replace("{names}", join_names(names))
    if writes_this_hour(conn, user, now) >= WRITE_LIMIT_PER_HOUR:
        return copy.WRITE_LIMIT.replace("{app}", _app(app_origin))
    try:
        with conn.transaction():
            conn.execute(
                """
                insert into journal_entries
                    (family_id, parent_entry_id, author_label, author_member_id, via_client,
                     body, kind, created_utc)
                values (%s, %s, %s, %s, %s, %s, 'note', %s)
                """,
                (
                    target["family_id"],
                    target["id"],
                    member["display_name"] or "",
                    member["id"],
                    grant.get("client_name") or copy.ASSISTANT_FALLBACK,
                    body,
                    now,
                ),
            )
    except psycopg.errors.CheckViolation:
        # The 016 rules, held by the trigger: never a reply to a reply or to
        # one of Kettle's own lines. The select above already excludes both;
        # the trigger is the guard if it ever does not.
        return copy.NO_NOTE_TO_ANSWER
    written_by = target["member_name"] or target["author_label"] or "Family"
    day = to_local(target["created_utc"], target["family_tz"])
    return copy.REPLY_SAVED.replace("{author}", written_by).replace(
        "{date}", f"{day.strftime('%b')} {day.day}"
    )


# --- the server ------------------------------------------------------------------


def build_server(
    connect: Callable[[], Any],
    clock: Callable[[], datetime] = now_utc,
    app_origin: str = "https://kettle-app.fly.dev",
) -> MCPServer:
    """The MCP server: five read tools and, since Amendment A, two writes.
    `connect()` is a context manager yielding a pooled connection; tools run
    their SQL in a worker thread."""
    server = MCPServer("Kettle", instructions=copy.SERVER_INSTRUCTIONS)

    def run(fn: Callable[[psycopg.Connection, str, datetime], str]) -> Callable[[], str]:
        def inner() -> str:
            user = CURRENT_USER.get()
            if user is None:  # pragma: no cover - the bearer check runs first
                return "Kettle does not know who is asking."
            with connect() as conn:
                return fn(conn, user, clock())

        return inner

    def visible(conn: psycopg.Connection, user: str):
        circles = circles_for(conn, user)
        return circles, parents_in(conn, [c["id"] for c in circles])

    def run_write(fn: Callable[[psycopg.Connection, dict[str, Any], datetime], str]):
        def inner() -> str:
            grant = CURRENT_GRANT.get()
            user = CURRENT_USER.get()
            if grant is None or user is None:  # pragma: no cover - the bearer check runs first
                return "Kettle does not know who is asking."
            with connect() as conn:
                return fn(conn, grant, clock())

        return inner

    @server.tool(name="add_note", description=copy.TOOL_ADD_NOTE, annotations=WRITES)
    async def add_note(text: str, parent: str | None = None, date: str | None = None) -> str:
        def go(conn: psycopg.Connection, grant: dict[str, Any], now: datetime) -> str:
            return add_note_for(conn, grant, text, parent, date, now, app_origin)

        return await anyio.to_thread.run_sync(run_write(go))

    @server.tool(name="reply", description=copy.TOOL_REPLY, annotations=WRITES)
    async def reply(text: str, author: str | None = None, date: str | None = None) -> str:
        def go(conn: psycopg.Connection, grant: dict[str, Any], now: datetime) -> str:
            return reply_for(conn, grant, text, author, date, now, app_origin)

        return await anyio.to_thread.run_sync(run_write(go))

    @server.tool(name="today", description=copy.TOOL_TODAY, annotations=READ_ONLY)
    async def today(parent: str | None = None) -> str:
        def go(conn: psycopg.Connection, user: str, now: datetime) -> str:
            circles, parents = visible(conn, user)
            chosen = match_parents(parents, parent)
            if not chosen:
                return no_such_parent(parent or "", parents)
            return "\n\n".join(
                f"{prefix_for(p, parents)}: {today_for(conn, p, now)}" for p in chosen
            )

        return await anyio.to_thread.run_sync(run(go))

    @server.tool(name="parent_day", description=copy.TOOL_PARENT_DAY, annotations=READ_ONLY)
    async def parent_day(parent: str, date: str | None = None) -> str:
        def go(conn: psycopg.Connection, user: str, now: datetime) -> str:
            _, parents = visible(conn, user)
            chosen = match_parents(parents, parent)
            if not chosen:
                return no_such_parent(parent, parents)
            out = []
            for p in chosen:
                tz_name = effective_tz(p["tz"], p["family_tz"])
                today_local = local_day(now, tz_name)
                day = date or today_local
                floor = (to_local(now, tz_name).date() - DAY_FLOOR).isoformat()
                if day < floor or day > today_local:
                    nothing = copy.DAY_NOTHING.replace("{name}", p["display_name"])
                    out.append(f"{prefix_for(p, parents)}: {nothing}")
                    continue
                out.append(f"{prefix_for(p, parents)}: {parent_day_for(conn, p, day)}")
            return "\n\n".join(out)

        return await anyio.to_thread.run_sync(run(go))

    @server.tool(name="memory", description=copy.TOOL_MEMORY, annotations=READ_ONLY)
    async def memory(parent: str | None = None, since: str | None = None) -> str:
        def go(conn: psycopg.Connection, user: str, now: datetime) -> str:
            circles, parents = visible(conn, user)
            parent_id = None
            if parent:
                chosen = match_parents(parents, parent)
                if not chosen:
                    return no_such_parent(parent, parents)
                parent_id = chosen[0]["id"]
            today = to_local(now, circles[0]["tz"]).date() if circles else now.date()
            return memory_for(conn, circles, parents, parent_id, since, today)

        return await anyio.to_thread.run_sync(run(go))

    @server.tool(name="who_to_call", description=copy.TOOL_WHO_TO_CALL, annotations=READ_ONLY)
    async def who_to_call(parent: str | None = None) -> str:
        def go(conn: psycopg.Connection, user: str, now: datetime) -> str:
            _, parents = visible(conn, user)
            chosen = match_parents(parents, parent)
            if not chosen:
                return no_such_parent(parent or "", parents)
            return "\n\n".join(
                f"{prefix_for(p, parents)}:\n{who_to_call_for(conn, p)}" for p in chosen
            )

        return await anyio.to_thread.run_sync(run(go))

    @server.tool(name="circles", description=copy.TOOL_CIRCLES, annotations=READ_ONLY)
    async def circles() -> str:
        def go(conn: psycopg.Connection, user: str, now: datetime) -> str:
            found = circles_for(conn, user)
            if not found:
                return "This person is not in any circle yet."
            return circles_text(conn, found, now)

        return await anyio.to_thread.run_sync(run(go))

    return server
