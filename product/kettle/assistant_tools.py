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

from kettle import assistant_copy as copy
from kettle import db
from kettle.outbound_templates import owner_first_name, render, template
from kettle.timeutil import effective_tz, local_day, now_utc, to_local

#: The auth_user_id the current /mcp request stands for (set by main.py).
CURRENT_USER: ContextVar[str | None] = ContextVar("kettle_assistant_user", default=None)

KIND_WORDS = {
    "digest_morning": copy.MORNING_NOTE,
    "digest_evening": copy.EVENING_NOTE,
    "ask": copy.ASK_SENT,
    "follow_on": copy.FOLLOW_ON_SENT,
    "all_clear": copy.ALL_CLEAR_SENT,
}
MEMORY_CAP = 40
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


def today_for(conn: psycopg.Connection, parent: dict[str, Any], now: datetime) -> str:
    lines = paused_lines(parent, now)
    if lines is None:
        tz_name = effective_tz(parent["tz"], parent["family_tz"])
        rows = sent_rows(conn, parent["id"], local_day(now, tz_name))
        lines = [
            render_row(conn, parent, rows[-1])
            if rows
            else copy.TODAY_NOTHING_YET.replace("{name}", parent["display_name"])
        ]
    lines.append(heard_line(conn, parent["id"], now))
    city = city_now(parent, now)
    if city:
        lines.append(city)
    return " ".join(lines)


def parent_day_for(conn: psycopg.Connection, parent: dict[str, Any], day: str) -> str:
    rows = sent_rows(conn, parent["id"], day)
    if not rows:
        return copy.DAY_NOTHING.replace("{name}", parent["display_name"])
    parts = []
    for row in rows:
        word = KIND_WORDS.get(row["kind"], row["kind"]).replace("{name}", parent["display_name"])
        parts.append(f"{word}: {render_row(conn, parent, row)}")
    return " ".join(parts)


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
               j.created_utc, j.kind, j.parent_entry_id, j.edited_utc, f.tz as family_tz
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


# --- the server ------------------------------------------------------------------


def build_server(connect: Callable[[], Any], clock: Callable[[], datetime] = now_utc) -> MCPServer:
    """The MCP server with the five tools. `connect()` is a context manager
    yielding a pooled connection; tools run their SQL in a worker thread."""
    server = MCPServer(
        "Kettle", instructions="Kettle answers in its own sentences about a parent's day."
    )

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

    @server.tool(name="today", description=copy.TOOL_TODAY)
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

    @server.tool(name="parent_day", description=copy.TOOL_PARENT_DAY)
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

    @server.tool(name="memory", description=copy.TOOL_MEMORY)
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

    @server.tool(name="who_to_call", description=copy.TOOL_WHO_TO_CALL)
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

    @server.tool(name="circles", description=copy.TOOL_CIRCLES)
    async def circles() -> str:
        def go(conn: psycopg.Connection, user: str, now: datetime) -> str:
            found = circles_for(conn, user)
            if not found:
                return "This person is not in any circle yet."
            return circles_text(conn, found, now)

        return await anyio.to_thread.run_sync(run(go))

    return server
