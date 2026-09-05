"""Postgres access. Plain SQL, no ORM (spec 002 §1).

Every write in this module names its columns explicitly. There is no
pass-through of caller-supplied fields anywhere: the schema is the privacy
promise, and it is enforced here by there being no code that could store
anything else.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from hashlib import sha256
from typing import Any

import psycopg
from psycopg.rows import dict_row

Row = dict[str, Any]


def connect(database_url: str) -> psycopg.Connection:
    """Open a connection that returns dict rows and commits each statement."""
    return psycopg.connect(database_url, row_factory=dict_row, autocommit=True)


def healthy(conn: psycopg.Connection) -> bool:
    """Cheap liveness probe for /healthz."""
    try:
        conn.execute("select 1 from pings limit 1").fetchall()
        return True
    except psycopg.Error:
        return False


def hash_ip(ip: str | None, salt: str) -> str | None:
    """Salted, truncated SHA-256 of the caller IP. Ops/debug only, never shown."""
    if not ip:
        return None
    return sha256(f"{salt}:{ip}".encode()).hexdigest()[:16]


# --- ingestion lookups ------------------------------------------------------


def device_by_token(conn: psycopg.Connection, token: str) -> Row | None:
    """Resolve a device token to its device, parent and family in one hop."""
    return conn.execute(
        """
        select d.id as device_id, d.active, d.revoked_utc, d.platform,
               p.id as parent_id, p.display_name as parent_name, p.tz as parent_tz,
               f.id as family_id, f.name as family_name, f.tz as family_tz
        from devices d
        join parents p on p.id = d.parent_id
        join families f on f.id = p.family_id
        where d.device_token = %s
        """,
        (token,),
    ).fetchone()


def active_signal(conn: psycopg.Connection, parent_id: Any, signal: str) -> Row | None:
    """Look the signal up in *this* parent's allowlist. None means reject."""
    return conn.execute(
        """
        select signal, alarm_grade
        from parent_signals
        where parent_id = %s and signal = %s and active
        """,
        (parent_id, signal),
    ).fetchone()


def insert_ping(
    conn: psycopg.Connection,
    parent_id: Any,
    signal: str,
    ts_utc: datetime,
    ip_hash: str | None,
    dedupe_window_s: int = 60,
) -> bool:
    """Insert a ping unless an identical (parent, signal) landed within the window.

    Shortcuts automations sometimes double-fire. The guard is inside the INSERT
    so two concurrent fires cannot both pass a separate check first.
    """
    cutoff = ts_utc - timedelta(seconds=dedupe_window_s)
    row = conn.execute(
        """
        insert into pings (parent_id, signal, ts_utc, ip_hash)
        select %(parent_id)s, %(signal)s, %(ts)s, %(ip_hash)s
        where not exists (
            select 1 from pings
            where parent_id = %(parent_id)s
              and signal = %(signal)s
              and ts_utc > %(cutoff)s
        )
        returning id
        """,
        {
            "parent_id": parent_id,
            "signal": signal,
            "ts": ts_utc,
            "ip_hash": ip_hash,
            "cutoff": cutoff,
        },
    ).fetchone()
    return row is not None


def revoke_device(conn: psycopg.Connection, device_id: Any, when: datetime) -> None:
    """Kill one device. Every other device in the family keeps working."""
    conn.execute(
        "update devices set active = false, revoked_utc = %s where id = %s",
        (when, device_id),
    )


# --- setup page lookups (spec 005b) -----------------------------------------


def setup_link_by_slug(conn: psycopg.Connection, slug: str) -> Row | None:
    """Resolve a setup slug to its link, device, parent and family in one hop.

    The device columns ride along because the link lives and dies with its
    device: a revoked token must kill the URL (spec 005b §4.2), and that rule
    is enforced by whoever reads this row, not by a second bookkeeping write.
    """
    return conn.execute(
        """
        select l.id as link_id, l.created_utc, l.expires_utc, l.revoked_utc,
               d.active as device_active, d.revoked_utc as device_revoked_utc,
               d.platform,
               p.id as parent_id, p.display_name as parent_name, p.tz as parent_tz,
               f.id as family_id, f.name as family_name, f.tz as family_tz
        from setup_links l
        join devices d on d.id = l.device_id
        join parents p on p.id = l.parent_id
        join families f on f.id = p.family_id
        where l.slug = %s
        """,
        (slug,),
    ).fetchone()


def family_owner_name(conn: psycopg.Connection, family_id: Any) -> str | None:
    """The family's first admin (spec 015: `owner` became `admin`), by display
    name — the setup page's "From {name}" and the ask's "{owner_name}"."""
    row = conn.execute(
        """
        select display_name from members
        where family_id = %s and role = 'admin'
        order by created_utc, id limit 1
        """,
        (family_id,),
    ).fetchone()
    return row["display_name"] if row else None


def parent_active_signals(conn: psycopg.Connection, parent_id: Any) -> list[Row]:
    """One parent's active allowlist, alarm-grade first.

    This is what the setup page renders steps from: the database stays
    authoritative about which signals a parent has, exactly as the forge's
    token path does (DECISIONS 97).
    """
    return conn.execute(
        """
        select signal, alarm_grade
        from parent_signals
        where parent_id = %s and active
        order by alarm_grade desc, signal
        """,
        (parent_id,),
    ).fetchall()


# --- heartbeat queries ------------------------------------------------------


def parents_with_tz(conn: psycopg.Connection) -> list[Row]:
    """Every monitored person, with the family context needed to pick a clock.

    `relationship` rides along for the outbound channel: it is the only thing
    `{relationship}` ever renders (DECISIONS 149), and None means the parent is
    skipped by relationship-bearing templates until the label is set.

    `family_demo` rides along too (0023): the engine drops those parents before
    it decides anything, and reading the flag here rather than filtering it out
    in SQL keeps this one query the single description of what a parent IS,
    with the decision about what to do with one staying in the engine. The
    pause columns (0027) ride for the same reason.
    """
    return conn.execute(
        """
        select p.id as parent_id, p.display_name as parent_name, p.tz as parent_tz,
               p.relationship as relationship,
               p.city_label as city_label, p.tz_changed_utc as tz_changed_utc,
               -- 'infinity' is what the open-ended pause stores (spec 017 §3)
               -- and what psycopg refuses to load; clamped to a year-9999
               -- instant here, which the engine's "paused_until > now" reads
               -- identically. Nothing writes this value back. The CASE is
               -- load-bearing: least() ignores NULLs, so without it every
               -- unpaused parent would read as paused until the year 9999.
               case when p.paused_until is null then null
                    else least(p.paused_until, timestamptz '9999-12-31 00:00:00+00')
               end as paused_until,
               p.paused_since as paused_since,
               f.id as family_id, f.name as family_name, f.tz as family_tz,
               f.demo as family_demo
        from parents p
        join families f on f.id = p.family_id
        order by f.name, p.display_name
        """
    ).fetchall()


def clear_pause(conn: psycopg.Connection, parent_id: Any) -> None:
    """The pause is over and its day is done (spec 017 §4): both fields null."""
    conn.execute(
        "update parents set paused_until = null, paused_since = null where id = %s",
        (parent_id,),
    )


def families_with_tz(conn: psycopg.Connection) -> list[Row]:
    """Every family, for the per-family infra check."""
    return conn.execute(
        "select id as family_id, name as family_name, tz as family_tz "
        "from families order by name"
    ).fetchall()


def count_alarm_pings_between(
    conn: psycopg.Connection, parent_id: Any, start: datetime, end: datetime
) -> int:
    """Count alarm-grade pings for one parent in [start, end).

    Alarm grade is read from that parent's own allowlist, so a family that turns
    a signal off for one person does not change anyone else's checks.
    """
    row = conn.execute(
        """
        select count(*) as n
        from pings p
        join parent_signals ps
          on ps.parent_id = p.parent_id and ps.signal = p.signal
        where p.parent_id = %s
          and ps.alarm_grade and ps.active
          and p.ts_utc >= %s and p.ts_utc < %s
        """,
        (parent_id, start, end),
    ).fetchone()
    return int(row["n"])


def last_alarm_ping(conn: psycopg.Connection, parent_id: Any) -> datetime | None:
    """When this person last did something deliberate, ever."""
    row = conn.execute(
        """
        select max(p.ts_utc) as ts
        from pings p
        join parent_signals ps
          on ps.parent_id = p.parent_id and ps.signal = p.signal
        where p.parent_id = %s and ps.alarm_grade and ps.active
        """,
        (parent_id,),
    ).fetchone()
    return row["ts"] if row else None


def family_last_ping(conn: psycopg.Connection, family_id: Any) -> datetime | None:
    """Last ping from any device in the family. None means none ever."""
    row = conn.execute(
        """
        select max(p.ts_utc) as ts
        from pings p
        join parents pa on pa.id = p.parent_id
        where pa.family_id = %s
        """,
        (family_id,),
    ).fetchone()
    return row["ts"] if row else None


def first_alarm_ping_between(
    conn: psycopg.Connection, parent_id: Any, start: datetime, end: datetime
) -> datetime | None:
    """The earliest alarm-grade ping for one parent in [start, end).

    This is the evidence the morning digest is built from — there is no path
    that renders "day started normally" without a row coming back from here.
    """
    row = conn.execute(
        """
        select min(p.ts_utc) as ts
        from pings p
        join parent_signals ps
          on ps.parent_id = p.parent_id and ps.signal = p.signal
        where p.parent_id = %s
          and ps.alarm_grade and ps.active
          and p.ts_utc >= %s and p.ts_utc < %s
        """,
        (parent_id, start, end),
    ).fetchone()
    return row["ts"] if row else None


# --- digest (family-facing, spec 003) ---------------------------------------


def families_for_digest(conn: psycopg.Connection) -> list[Row]:
    """Families that have explicitly opted in. Defaults to none."""
    return conn.execute(
        "select id as family_id, name as family_name, tz as family_tz "
        "from families where digest_enabled order by name"
    ).fetchall()


def parents_for_family(conn: psycopg.Connection, family_id: Any) -> list[Row]:
    """The monitored people in one family."""
    return conn.execute(
        "select id as parent_id, display_name as parent_name, tz as parent_tz "
        "from parents where family_id = %s order by display_name",
        (family_id,),
    ).fetchall()


def digest_recipients(conn: psycopg.Connection, family_id: Any) -> list[Row]:
    """Members who have a channel and a number to reach it on."""
    return conn.execute(
        """
        select id as member_id, display_name as member_name,
               phone_e164, digest_channel
        from members
        where family_id = %s
          and digest_channel <> 'none'
          and phone_e164 is not null and phone_e164 <> ''
        order by created_utc, id
        """,
        (family_id,),
    ).fetchall()


def digest_send_exists(
    conn: psycopg.Connection,
    family_id: Any,
    parent_id: Any | None,
    kind: str,
    local_date: date,
    member_id: Any,
) -> bool:
    """Has this exact message already gone to this recipient today?

    The idempotency question is asked of the database, never of process memory,
    so a restart mid-pass cannot produce a second send.
    """
    row = conn.execute(
        """
        select 1 from digest_sends
        where family_id = %s
          and parent_id is not distinct from %s
          and kind = %s and local_date = %s and member_id = %s
        limit 1
        """,
        (family_id, parent_id, kind, local_date, member_id),
    ).fetchone()
    return row is not None


def record_digest_send(
    conn: psycopg.Connection,
    family_id: Any,
    parent_id: Any | None,
    kind: str,
    local_date: date,
    member_id: Any,
    channel: str,
    status: str,
    ts_utc: datetime,
) -> bool:
    """Record one delivery attempt. False when the unique index already had it.

    `on conflict do nothing` makes the write itself the race guard: two passes
    overlapping across a restart cannot both insert.
    """
    row = conn.execute(
        """
        insert into digest_sends
            (family_id, parent_id, kind, local_date, member_id, channel, status, ts_utc)
        values (%s, %s, %s, %s, %s, %s, %s, %s)
        on conflict do nothing
        returning id
        """,
        (family_id, parent_id, kind, local_date, member_id, channel, status, ts_utc),
    ).fetchone()
    return row is not None


def member_send_sent(
    conn: psycopg.Connection,
    family_id: Any,
    parent_id: Any,
    kind: str,
    local_date: Any,
    member_id: Any,
) -> bool:
    """Has this member already RECEIVED this slot (spec 015 §7)? Sent rows
    only: a failed row keeps the member due, the way the ledger's statuses
    work (0015)."""
    row = conn.execute(
        """
        select 1 from digest_sends
        where family_id = %s and parent_id = %s and kind = %s
          and local_date = %s and member_id = %s and status = 'sent'
        limit 1
        """,
        (family_id, parent_id, kind, local_date, member_id),
    ).fetchone()
    return row is not None


def record_member_send(
    conn: psycopg.Connection,
    family_id: Any,
    parent_id: Any,
    kind: str,
    local_date: Any,
    member_id: Any,
    channel: str,
    status: str,
    ts_utc: datetime,
) -> None:
    """One member's outcome for one slot. A failed row is overwritten by the
    retry that reaches them; a sent row is final."""
    conn.execute(
        """
        insert into digest_sends
            (family_id, parent_id, kind, local_date, member_id, channel, status, ts_utc)
        values (%s, %s, %s, %s, %s, %s, %s, %s)
        on conflict (family_id, parent_id, kind, local_date, member_id) do update
            set channel = excluded.channel, status = excluded.status, ts_utc = excluded.ts_utc
            where digest_sends.status <> 'sent'
        """,
        (family_id, parent_id, kind, local_date, member_id, channel, status, ts_utc),
    )


def count_any_pings_between(
    conn: psycopg.Connection, parent_id: Any, start: datetime, end: datetime
) -> int:
    """Every ping in the window, whatever its grade.

    Alarm-grade answers "did a person do something"; this answers "is the phone
    and the pipeline alive at all", which is a different question and the one
    that decides whether asking the senior is even possible.
    """
    row = conn.execute(
        "select count(*) as n from pings "
        "where parent_id = %s and ts_utc >= %s and ts_utc < %s",
        (parent_id, start, end),
    ).fetchone()
    return int(row["n"])


# --- ladder (spec 004) ------------------------------------------------------


def families_for_ladder(conn: psycopg.Connection) -> list[Row]:
    """Families with the ladder switched on at all. Defaults to none."""
    return conn.execute(
        "select id as family_id, name as family_name, tz as family_tz, "
        "       ladder_mode, digest_enabled "
        "from families where ladder_mode <> 'off' order by name"
    ).fetchall()


def ladder_parents(conn: psycopg.Connection, family_id: Any) -> list[Row]:
    """Monitored people with their rule-v1 thresholds and timings."""
    return conn.execute(
        """
        select id as parent_id, display_name as parent_name, tz as parent_tz,
               phone_e164, alarm_deadline, max_gap_minutes, grace_minutes,
               family_gap_minutes
        from parents where family_id = %s order by display_name
        """,
        (family_id,),
    ).fetchall()


def ladder_recipients(conn: psycopg.Connection, family_id: Any) -> list[Row]:
    """The family circle in escalation order: owner first, then by created order."""
    return conn.execute(
        """
        select id as member_id, display_name as member_name, phone_e164,
               digest_channel, role
        from members
        where family_id = %s
          and digest_channel <> 'none'
          and phone_e164 is not null and phone_e164 <> ''
        order by (role = 'admin') desc, created_utc, id
        """,
        (family_id,),
    ).fetchall()


def family_contact(conn: psycopg.Connection, family_id: Any) -> Row | None:
    """The family's named local contact, if the wizard has captured one."""
    return conn.execute(
        "select name, phone_e164, relation from family_contacts "
        "where family_id = %s order by created_utc, id limit 1",
        (family_id,),
    ).fetchone()


def candidate_for_day(
    conn: psycopg.Connection, parent_id: Any, local_date: date
) -> Row | None:
    """The one candidate this parent may have today, resolved or not."""
    return conn.execute(
        "select * from ladder_candidates where parent_id = %s and local_date = %s",
        (parent_id, local_date),
    ).fetchone()


def open_candidate_for_parent(conn: psycopg.Connection, parent_id: Any) -> Row | None:
    """The parent's unresolved candidate, if one is running."""
    return conn.execute(
        "select * from ladder_candidates "
        "where parent_id = %s and resolved_utc is null "
        "order by opened_utc desc limit 1",
        (parent_id,),
    ).fetchone()


def insert_candidate(
    conn: psycopg.Connection,
    family_id: Any,
    parent_id: Any,
    local_date: date,
    mode: str,
    trigger: str,
    mechanism_ok: bool,
    stage: str,
    opened_utc: datetime,
) -> Row | None:
    """Open a candidate. None when today's already exists (unique index)."""
    return conn.execute(
        """
        insert into ladder_candidates
            (family_id, parent_id, local_date, mode, trigger, mechanism_ok,
             stage, opened_utc)
        values (%s, %s, %s, %s, %s, %s, %s, %s)
        on conflict do nothing
        returning *
        """,
        (family_id, parent_id, local_date, mode, trigger, mechanism_ok, stage, opened_utc),
    ).fetchone()


def set_candidate_stage(
    conn: psycopg.Connection,
    candidate_id: int,
    stage: str,
    column: str | None,
    when: datetime,
) -> Row:
    """Move a candidate to a stage, stamping that stage's timestamp column."""
    allowed = {"ask_utc", "family_1_utc", "family_all_utc", None}
    if column not in allowed:
        raise ValueError(f"unknown stage column: {column}")
    if column is None:
        sql = "update ladder_candidates set stage = %s where id = %s returning *"
        params: tuple[Any, ...] = (stage, candidate_id)
    else:
        sql = (
            f"update ladder_candidates set stage = %s, {column} = %s "
            "where id = %s returning *"
        )
        params = (stage, when, candidate_id)
    return conn.execute(sql, params).fetchone()


def resolve_candidate(
    conn: psycopg.Connection, candidate_id: int, resolution: str, when: datetime
) -> Row | None:
    """Close a candidate. None if it was already closed — first resolution wins."""
    return conn.execute(
        """
        update ladder_candidates
        set stage = 'resolved', resolution = %s, resolved_utc = %s
        where id = %s and resolved_utc is null
        returning *
        """,
        (resolution, when, candidate_id),
    ).fetchone()


def insert_ladder_event(
    conn: psycopg.Connection,
    candidate_id: int,
    family_id: Any,
    parent_id: Any,
    stage: str,
    mode: str,
    detail: str,
    ts_utc: datetime,
) -> None:
    """Append one transition to the ledger."""
    conn.execute(
        """
        insert into ladder_events
            (candidate_id, family_id, parent_id, stage, mode, detail, ts_utc)
        values (%s, %s, %s, %s, %s, %s, %s)
        """,
        (candidate_id, family_id, parent_id, stage, mode, detail, ts_utc),
    )


def parent_by_phone(conn: psycopg.Connection, phone_e164: str) -> Row | None:
    """Resolve an inbound sender to a monitored person, for the ASK reply."""
    return conn.execute(
        """
        select p.id as parent_id, p.display_name as parent_name, p.tz as parent_tz,
               p.grace_minutes,
               f.id as family_id, f.name as family_name, f.tz as family_tz,
               f.ladder_mode
        from parents p
        join families f on f.id = p.family_id
        where p.phone_e164 = %s
        limit 1
        """,
        (phone_e164,),
    ).fetchone()


# --- ops alerts (founder-only) ----------------------------------------------


def insert_ops_alert(
    conn: psycopg.Connection,
    family_id: Any,
    parent_id: Any | None,
    kind: str,
    detail: str,
    ts_utc: datetime,
) -> None:
    """Record an ops alert. Nothing here is ever shown to a family or a parent."""
    conn.execute(
        """
        insert into ops_alerts (family_id, parent_id, kind, detail, ts_utc)
        values (%s, %s, %s, %s, %s)
        """,
        (family_id, parent_id, kind, detail, ts_utc),
    )


def latest_ops_alert(
    conn: psycopg.Connection, parent_id: Any, kind: str
) -> Row | None:
    """The newest ops alert of one kind for one parent, or None.

    Spec 010 §3's move alert reads this twice over: whether the change at
    `tz_changed_utc` has already been announced (dedupe that survives a
    restart, unlike loop memory), and what the previous announcement said the
    zone became (the old zone of the next move).
    """
    return conn.execute(
        """
        select kind, detail, ts_utc from ops_alerts
        where parent_id = %s and kind = %s
        order by ts_utc desc, id desc
        limit 1
        """,
        (parent_id, kind),
    ).fetchone()


def ops_alert_exists(
    conn: psycopg.Connection,
    kind: str,
    family_id: Any,
    parent_id: Any | None,
    start: datetime,
    end: datetime,
) -> bool:
    """Has this (kind, parent-or-family) alert already fired in the window?"""
    row = conn.execute(
        """
        select 1 from ops_alerts
        where kind = %s
          and family_id = %s
          and parent_id is not distinct from %s
          and ts_utc >= %s and ts_utc < %s
        limit 1
        """,
        (kind, family_id, parent_id, start, end),
    ).fetchone()
    return row is not None


def ops_alert_exists_with_detail(
    conn: psycopg.Connection,
    kind: str,
    family_id: Any,
    parent_id: Any | None,
    detail: str,
    start: datetime,
    end: datetime,
) -> bool:
    """Dedupe on the message text as well as the kind.

    `ops_alerts` has no member column, so per-member dedupe keys on the detail
    string, which is deterministic for a given member on a given day.
    """
    row = conn.execute(
        """
        select 1 from ops_alerts
        where kind = %s
          and family_id = %s
          and parent_id is not distinct from %s
          and detail = %s
          and ts_utc >= %s and ts_utc < %s
        limit 1
        """,
        (kind, family_id, parent_id, detail, start, end),
    ).fetchone()
    return row is not None


# --- the outbound channel's ledger (spec 007) --------------------------------


def outbound_contacts(conn: psycopg.Connection, family_id: Any) -> list[Row]:
    """Everyone in the circle Kettle's mail goes to (spec 015 §7).

    Every member with `mail` on and an email on file, admins first, then by
    created order. Digests, follow-ons and all-clears go to all of them; the
    per-member idempotency rides `digest_sends`. Empty means nobody is
    listening — the engine sends nothing and raises `circle_unreachable`
    once a day.
    """
    return conn.execute(
        """
        select m.id as member_id, m.email
        from members m
        where m.family_id = %s and m.mail and m.email is not null and m.email <> ''
        order by (m.role = 'admin') desc, m.created_utc, m.id
        """,
        (family_id,),
    ).fetchall()


def parent_whatsapp(conn: psycopg.Connection, parent_id: Any) -> str | None:
    """The parent's WhatsApp number, or None when the founder has not entered it."""
    row = conn.execute(
        "select whatsapp_e164 from parents where id = %s", (parent_id,)
    ).fetchone()
    return (row or {}).get("whatsapp_e164")


def sent_message(
    conn: psycopg.Connection, family_id: Any, parent_id: Any, local_date: str, kind: str
) -> Row | None:
    """The SENT ledger row for one family, parent, local day and kind — or None.

    Status-blind reads would make a skipped ask look sent to the follow-on's
    precondition and a failed digest look done to the scheduler. Only 'sent'
    rows are messages (0015); 'failed' and 'skipped' claim the slot but leave
    the decision open for a later pass to retry.
    """
    return conn.execute(
        """
        select id, template_id, transport, sent_utc, replied_utc
        from sent_messages
        where family_id = %s and parent_id = %s and local_date = %s and kind = %s
          and status = 'sent'
        """,
        (family_id, parent_id, local_date, kind),
    ).fetchone()


def message_row(
    conn: psycopg.Connection, family_id: Any, parent_id: Any, local_date: str, kind: str
) -> Row | None:
    """The ledger row for one slot, ANY status — the escalation-clock read.

    `sent_message` above answers "did Kettle actually say this"; this answers
    "did the engine decide this today". The follow-on's precondition uses it
    (DECISIONS 163): an ask that recorded skipped or failed still starts the
    grace clock, because a missing phone number must never silently disable
    the ladder. For a non-sent row `sent_utc` is when the outcome was
    recorded — the moment the ask was due — and `replied_utc` is null by
    construction, since only sent asks are answerable.
    """
    return conn.execute(
        """
        select id, template_id, transport, status, sent_utc, replied_utc
        from sent_messages
        where family_id = %s and parent_id = %s and local_date = %s and kind = %s
        """,
        (family_id, parent_id, local_date, kind),
    ).fetchone()


def count_pings_between(
    conn: psycopg.Connection, parent_id: Any, start: datetime, end: datetime
) -> int:
    """Pings of ANY signal in [start, end) — the unreachable-phone read.

    Deliberately not joined to the allowlist and not filtered by grade: the
    question is "has this device said anything at all today", and a charger or
    device_alive row answers it. This never anchors reassurance or alarm about
    a person (law #6) — it only chooses which follow-on body reports the
    silence honestly.
    """
    return conn.execute(
        "select count(*) as n from pings "
        "where parent_id = %s and ts_utc >= %s and ts_utc < %s",
        (parent_id, start, end),
    ).fetchone()["n"]


def record_sent_message(
    conn: psycopg.Connection,
    family_id: Any,
    parent_id: Any,
    local_date: str,
    kind: str,
    template_id: str,
    transport: str,
    sent_utc: datetime,
    status: str = "sent",
) -> bool:
    """Write the ledger row. False means nothing new was recorded.

    `on conflict` rather than a check-then-insert: two schedulers racing on the
    same day is exactly what the unique index exists for, and a read followed
    by a write leaves a window between them.

    The transition rule (0015): 'sent' is final and is never overwritten — a
    racing pass cannot downgrade a delivered message to 'failed'. 'failed' and
    'skipped' rows may be upgraded by a later pass (a retry that succeeds, a
    label set after a skip), and re-recording the *same* non-sent status is a
    no-op — which is what keeps the minutely loop from re-alerting a standing
    skip sixty times an hour. True means this call changed the ledger: a fresh
    row, or a status transition. `replied_utc` is never touched here.
    """
    row = conn.execute(
        """
        insert into sent_messages
            (family_id, parent_id, local_date, kind, template_id, transport,
             sent_utc, status)
        values (%s, %s, %s, %s, %s, %s, %s, %s)
        on conflict (family_id, parent_id, local_date, kind) do update
            set status = excluded.status,
                template_id = excluded.template_id,
                transport = excluded.transport,
                sent_utc = excluded.sent_utc
            where sent_messages.status != 'sent'
              and sent_messages.status is distinct from excluded.status
        returning id
        """,
        (family_id, parent_id, local_date, kind, template_id, transport, sent_utc, status),
    ).fetchone()
    return row is not None


def record_reply(conn: psycopg.Connection, parent_id: Any, when: datetime) -> bool:
    """Mark the parent's pending ask answered. Timestamp only.

    The pending ask is the most recent one that was sent, is unanswered, and
    whose follow-on has not gone yet, bounded to asks sent within the last 24
    hours (spec 007 §2.6, DECISIONS 153). No calendar day in the match: keying
    on the parent's local date is the DECISIONS 145 defect, where an answer
    just after midnight matched nothing and the family was escalated to anyway.
    The follow-on condition is per the ask's own ledger day — once the family
    has been told, a late reply cannot un-tell them, so there is nothing left
    for it to cancel.

    Never the content: what the parent said is content, and this product does
    not hold content. The first reply wins — a second one changes nothing, so a
    duplicate webhook delivery cannot move the timestamp around.
    """
    row = conn.execute(
        """
        update sent_messages
        set replied_utc = %s
        where id = (
            select a.id
            from sent_messages a
            where a.parent_id = %s
              and a.kind = 'ask'
              and a.status = 'sent'
              and a.replied_utc is null
              and a.sent_utc > %s - interval '24 hours'
              and not exists (
                  -- Only a follow-on that actually reached the family closes
                  -- the question; a skipped or failed one told them nothing.
                  select 1 from sent_messages f
                  where f.parent_id = a.parent_id
                    and f.local_date = a.local_date
                    and f.kind = 'follow_on'
                    and f.status = 'sent'
              )
            order by a.sent_utc desc
            limit 1
        )
        returning id
        """,
        (when, parent_id, when),
    ).fetchone()
    return row is not None


def parent_by_whatsapp(conn: psycopg.Connection, number: str) -> Row | None:
    """Find a parent by the WhatsApp number the reply arrived from."""
    return conn.execute(
        """
        select p.id as parent_id, p.display_name as parent_name, p.tz as parent_tz,
               f.id as family_id, f.tz as family_tz
        from parents p
        join families f on f.id = p.family_id
        where p.whatsapp_e164 = %s
        """,
        (number,),
    ).fetchone()
