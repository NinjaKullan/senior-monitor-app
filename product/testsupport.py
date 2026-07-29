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
