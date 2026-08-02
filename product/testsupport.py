"""Helpers shared by the product tests.

Lives at the `product/` root rather than inside `tests/` so it can be imported
as `testsupport` — the repo already has a `tests` package (the pilot's), and two
`tests.conftest` modules on one path is a collision waiting to happen.
"""

from __future__ import annotations

import psycopg

BASE_URL = "https://kettle-api.test"

TABLES = (
    "families",
    "members",
    "parents",
    "devices",
    "parent_signals",
    "pings",
    "ops_alerts",
    "digest_sends",
    "family_contacts",
    "ladder_candidates",
    "ladder_events",
    "waitlist",
)


# Everything except the two service-only tables: no policy and, after migration
# 0004, no privilege either. `ops_alerts` is the founder's plumbing log (law #3);
# `waitlist` is strangers' email addresses that no client ever reads (spec 006).
SERVICE_ONLY_TABLES = ("ops_alerts", "waitlist")
FAMILY_TABLES = tuple(t for t in TABLES if t not in SERVICE_ONLY_TABLES)

# Actual granted privileges on public tables and sequences, straight from the
# catalog. information_schema.role_table_grants hides grants the caller cannot
# see; aclexplode does not, and it covers sequences too.
_PRIVILEGE_SQL = """
select r.rolname as grantee, c.relkind, c.relname,
       array_agg(a.privilege_type order by a.privilege_type) as privs
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
cross join lateral aclexplode(c.relacl) a
join pg_roles r on r.oid = a.grantee
where n.nspname = 'public'
  and c.relkind in ('r', 'S')
  and r.rolname = any(%s)
group by 1, 2, 3
"""


def object_privileges(
    conn: psycopg.Connection, roles: list[str]
) -> dict[tuple[str, str], set[str]]:
    """{(grantee, object_name): {privilege, ...}} for public tables and sequences.

    Objects with no explicit grants have a NULL acl and simply do not appear, so
    an empty dict means "this role holds nothing".
    """
    rows = conn.execute(_PRIVILEGE_SQL, (roles,)).fetchall()
    return {(r["grantee"], r["relname"]): set(r["privs"]) for r in rows}


class RecordingNotifier:
    """Stand-in for ntfy that records what the founder would have received."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, message: str) -> bool:
        self.messages.append(message)
        return True


def enable_digests(
    conn: psycopg.Connection,
    family_id: object,
    recipients: list[tuple[str, str]] | None = None,
    channel: str = "sms",
) -> list[dict]:
    """Opt a family in and give it recipients. Nothing sends without both."""
    conn.execute("update families set digest_enabled = true where id = %s", (family_id,))
    for name, phone in recipients or [("Child", "+15125550100")]:
        conn.execute(
            """
            insert into members (family_id, display_name, role, email, phone_e164,
                                 digest_channel)
            values (%s, %s, 'owner', %s, %s, %s)
            """,
            (family_id, name, f"{name.lower()}@example.test", phone, channel),
        )
    return conn.execute(
        "select id as member_id, display_name, phone_e164 from members "
        "where family_id = %s order by created_utc, id",
        (family_id,),
    ).fetchall()


def enable_ladder(
    conn: psycopg.Connection, family_id: object, mode: str = "shadow"
) -> None:
    """Put a family into a ladder mode. `live` needs digests on first (DB CHECK)."""
    if mode == "live":
        conn.execute(
            "update families set digest_enabled = true where id = %s", (family_id,)
        )
    conn.execute("update families set ladder_mode = %s where id = %s", (mode, family_id))


def set_senior_phone(
    conn: psycopg.Connection, parent_id: object, phone_e164: str
) -> None:
    """Give a monitored person a number the ASK stage can reach."""
    conn.execute(
        "update parents set phone_e164 = %s where id = %s", (phone_e164, parent_id)
    )


def as_user(authed_conn: psycopg.Connection, auth_user_id: str) -> None:
    """Present a Supabase Auth user on an `authenticated` connection."""
    authed_conn.execute(
        "select set_config('request.jwt.claims', %s, false)",
        (f'{{"sub": "{auth_user_id}"}}',),
    )


def as_user_with_email(
    authed_conn: psycopg.Connection, auth_user_id: str, email: str
) -> None:
    """Present a Supabase Auth user *and* their verified email, as Auth does."""
    authed_conn.execute(
        "select set_config('request.jwt.claims', %s, false)",
        (f'{{"sub": "{auth_user_id}", "email": "{email}"}}',),
    )


def invite_member(
    conn: psycopg.Connection, family_id: object, email: str, role: str = "owner"
) -> object:
    """A member row as provisioning leaves it: email known, auth_user_id null."""
    return conn.execute(
        """
        insert into members (family_id, display_name, role, email)
        values (%s, %s, %s, %s) returning id
        """,
        (family_id, email.split("@")[0], role, email),
    ).fetchone()["id"]


def add_member(
    conn: psycopg.Connection, family_id: object, auth_user_id: str, role: str = "owner"
) -> None:
    """Link an auth user to a family, the way signup will."""
    conn.execute(
        """
        insert into members (family_id, auth_user_id, display_name, role, email)
        values (%s, %s, %s, %s, %s)
        """,
        (family_id, auth_user_id, f"member-{role}", role, f"{role}@example.test"),
    )
