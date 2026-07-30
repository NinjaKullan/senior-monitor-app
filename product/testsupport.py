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
)


# Everything except ops_alerts, which is service-only in every sense: no policy
# and, after migration 0004, no privilege either.
FAMILY_TABLES = tuple(t for t in TABLES if t != "ops_alerts")

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


def as_user(authed_conn: psycopg.Connection, auth_user_id: str) -> None:
    """Present a Supabase Auth user on an `authenticated` connection."""
    authed_conn.execute(
        "select set_config('request.jwt.claims', %s, false)",
        (f'{{"sub": "{auth_user_id}"}}',),
    )


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
