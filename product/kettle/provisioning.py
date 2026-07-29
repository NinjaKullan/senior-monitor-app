"""Family provisioning (spec 002 §5).

Until the PWA exists (spec 005) this is how a beta family gets onboarded: create
the family, its monitored loved ones, one device each, and each person's own
seeded signal allowlist, then hand back the ready-to-use ping URLs and the
shortcut names those URLs belong in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import psycopg

from kettle.signals import STANDARD_SIGNALS, shortcut_name
from kettle.timeutil import now_utc
from kettle.tokens import new_device_token

DEMO_FAMILY_NAME = "Kettle Demo Family"
DEMO_TZ = "Asia/Kolkata"
DEMO_PARENTS: tuple[tuple[str, str | None], ...] = (
    ("Demo Amma", None),
    ("Demo Appa", None),
)


@dataclass(frozen=True)
class ProvisionedSignal:
    """One signal, with everything needed to build its shortcut."""

    signal: str
    alarm_grade: bool
    url: str
    shortcut: str


@dataclass(frozen=True)
class ProvisionedParent:
    """One monitored person and their (single) provisioned device."""

    parent_id: Any
    display_name: str
    tz: str | None
    device_id: Any
    device_token: str
    signals: list[ProvisionedSignal]


@dataclass(frozen=True)
class ProvisionedFamily:
    """The result of one provisioning run."""

    family_id: Any
    name: str
    tz: str
    parents: list[ProvisionedParent]


def provision_family(
    conn: psycopg.Connection,
    name: str,
    tz: str,
    parents: list[tuple[str, str | None]],
    base_url: str,
    platform: str = "ios_shortcuts",
    owner_email: str | None = None,
    owner_name: str | None = None,
) -> ProvisionedFamily:
    """Create a family, its people, their devices and their signal allowlists.

    `parents` is a list of (display_name, tz_or_None); a per-parent tz overrides
    the family tz. An owner member is created only when an email is supplied —
    the row's `auth_user_id` stays null until that person actually signs up
    through Supabase Auth.
    """
    created = now_utc()
    family = conn.execute(
        "insert into families (name, tz, created_utc) values (%s, %s, %s) "
        "returning id",
        (name, tz, created),
    ).fetchone()
    family_id = family["id"]

    if owner_email:
        conn.execute(
            """
            insert into members (family_id, display_name, role, email, created_utc)
            values (%s, %s, 'owner', %s, %s)
            """,
            (family_id, owner_name or owner_email, owner_email, created),
        )

    provisioned: list[ProvisionedParent] = []
    for display_name, parent_tz in parents:
        parent = conn.execute(
            "insert into parents (family_id, display_name, tz, created_utc) "
            "values (%s, %s, %s, %s) returning id",
            (family_id, display_name, parent_tz, created),
        ).fetchone()
        parent_id = parent["id"]

        token = new_device_token()
        device = conn.execute(
            """
            insert into devices (parent_id, platform, device_token, created_utc)
            values (%s, %s, %s, %s)
            returning id
            """,
            (parent_id, platform, token, created),
        ).fetchone()

        signals: list[ProvisionedSignal] = []
        for signal, alarm_grade in STANDARD_SIGNALS:
            conn.execute(
                "insert into parent_signals (parent_id, signal, alarm_grade) "
                "values (%s, %s, %s)",
                (parent_id, signal, alarm_grade),
            )
            signals.append(
                ProvisionedSignal(
                    signal=signal,
                    alarm_grade=alarm_grade,
                    url=f"{base_url.rstrip('/')}/p/{token}/{signal}",
                    shortcut=shortcut_name(display_name, signal),
                )
            )

        provisioned.append(
            ProvisionedParent(
                parent_id=parent_id,
                display_name=display_name,
                tz=parent_tz,
                device_id=device["id"],
                device_token=token,
                signals=signals,
            )
        )

    return ProvisionedFamily(
        family_id=family_id, name=name, tz=tz, parents=provisioned
    )


def provision_demo_family(
    conn: psycopg.Connection, base_url: str
) -> ProvisionedFamily:
    """Provision the standard demo family used by tests and walkthroughs."""
    return provision_family(
        conn,
        name=DEMO_FAMILY_NAME,
        tz=DEMO_TZ,
        parents=list(DEMO_PARENTS),
        base_url=base_url,
    )


def render_summary(family: ProvisionedFamily) -> str:
    """The operator-facing printout: what to build, and the URL it points at."""
    lines = [
        f"Family: {family.name}  (id {family.family_id}, tz {family.tz})",
        "",
    ]
    for parent in family.parents:
        tz_note = f" [tz {parent.tz}]" if parent.tz else ""
        lines.append(f"  {parent.display_name}{tz_note}")
        lines.append(f"    device token: {parent.device_token}")
        for sig in parent.signals:
            grade = "alarm" if sig.alarm_grade else "corroborating"
            lines.append(f"    - {sig.shortcut}  ({grade})")
            lines.append(f"      {sig.url}")
        lines.append("")
    lines.append(
        "Tokens are per device: revoking one phone leaves the rest working. "
        "Nobody types these URLs — they ship inside pre-built shortcuts."
    )
    return "\n".join(lines)
