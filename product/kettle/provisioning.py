"""Family provisioning (spec 002 §5).

Until the PWA exists (spec 005) this is how a beta family gets onboarded: create
the family, its monitored loved ones, one device each, and each person's own
seeded signal allowlist, then hand back the ready-to-use ping URLs and the
shortcut names those URLs belong in.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import psycopg

from kettle import db
from kettle.signals import ALARM_GRADE, STANDARD_SIGNALS, shortcut_name
from kettle.timeutil import now_utc
from kettle.tokens import new_device_token, new_setup_slug

#: How long a freshly issued setup link answers (spec 005b §4.2). Seven days
#: covers "I'll call Amma on the weekend" without leaving a live credential
#: parked in a WhatsApp thread for a month. Re-issuing is one command.
SETUP_LINK_TTL_DAYS = 7

DEMO_FAMILY_NAME = "Kettle Demo Family"
DEMO_TZ = "Asia/Kolkata"
DEMO_PARENTS: tuple[tuple[str, str | None], ...] = (
    ("Demo Amma", None),
    ("Demo Appa", None),
)


def select_signals(keys: list[str] | None) -> tuple[tuple[str, bool], ...]:
    """The (signal, alarm_grade) rows a chosen key list provisions.

    None means the standard seed, unchanged. A key outside the vocabulary is a
    loud error before anything is written: a typo here would otherwise provision
    a signal no shortcut will ever ping and no label map can render.
    """
    if keys is None:
        return STANDARD_SIGNALS
    unknown = [k for k in keys if k not in ALARM_GRADE]
    if unknown:
        known = ", ".join(sorted(ALARM_GRADE))
        raise ValueError(f"unknown signal(s) {unknown!r} — the vocabulary is: {known}")
    if not keys:
        raise ValueError("--signals given but empty; a parent with no signals has no tripwires")
    return tuple((k, ALARM_GRADE[k]) for k in dict.fromkeys(keys))


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
    setup_url: str
    setup_expires_utc: datetime


@dataclass(frozen=True)
class ProvisionedFamily:
    """The result of one provisioning run."""

    family_id: Any
    name: str
    tz: str
    parents: list[ProvisionedParent]


def setup_url_for(base_url: str, slug: str) -> str:
    """The public address of one parent's setup page."""
    return f"{base_url.rstrip('/')}/s/{slug}"


def issue_setup_link(
    conn: psycopg.Connection, device_id: Any, parent_id: Any, when: datetime
) -> tuple[str, datetime]:
    """Mint the one live setup link for a device, retiring any predecessor.

    Issuance is rotation: a device has at most one answering link, so a
    re-issued URL quietly kills the copy still sitting in last week's WhatsApp
    thread. Returns (slug, expires_utc).
    """
    conn.execute(
        "update setup_links set revoked_utc = %s "
        "where device_id = %s and revoked_utc is null",
        (when, device_id),
    )
    slug = new_setup_slug()
    expires = when + timedelta(days=SETUP_LINK_TTL_DAYS)
    conn.execute(
        """
        insert into setup_links (device_id, parent_id, slug, created_utc, expires_utc)
        values (%s, %s, %s, %s, %s)
        """,
        (device_id, parent_id, slug, when, expires),
    )
    return slug, expires


@dataclass(frozen=True)
class IssuedSetupLink:
    """A re-issued setup link, with the context the operator reads back."""

    parent_name: str
    family_name: str
    url: str
    expires_utc: datetime


def issue_setup_link_by_token(
    conn: psycopg.Connection, device_token: str, base_url: str, when: datetime
) -> IssuedSetupLink | None:
    """Issue (or rotate) the setup link for an existing parent's device.

    The Appa case: provisioned weeks ago, setup happening now — the original
    link has expired and nothing should have to be re-provisioned to get a
    fresh one. None when the token is unknown or the device is revoked; a dead
    device gets no new doors (QUESTIONS 95's one-way door, unchanged).
    """
    device = db.device_by_token(conn, device_token)
    if device is None or not device["active"] or device["revoked_utc"]:
        return None
    slug, expires = issue_setup_link(conn, device["device_id"], device["parent_id"], when)
    return IssuedSetupLink(
        parent_name=device["parent_name"],
        family_name=device["family_name"],
        url=setup_url_for(base_url, slug),
        expires_utc=expires,
    )


def provision_family(
    conn: psycopg.Connection,
    name: str,
    tz: str,
    parents: list[tuple[str, str | None]],
    base_url: str,
    platform: str = "ios_shortcuts",
    owner_email: str | None = None,
    owner_name: str | None = None,
    signals: list[str] | None = None,
) -> ProvisionedFamily:
    """Create a family, its people, their devices and their signal allowlists.

    `parents` is a list of (display_name, tz_or_None); a per-parent tz overrides
    the family tz. An owner member is created only when an email is supplied —
    the row's `auth_user_id` stays null until that person actually signs up
    through Supabase Auth.

    `signals` chooses the allowlist at provisioning time (QUESTIONS 94) instead
    of seeding the standard set and editing afterwards. Keys must be in the
    vocabulary — alarm grade comes from `kettle.signals.ALARM_GRADE`, never from
    the caller, so a merged `routine` cannot arrive corroborating or a `charger`
    alarm-grade by typo. The set applies to every parent in this invocation.
    """
    chosen = select_signals(signals)
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
        for signal, alarm_grade in chosen:
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
                    shortcut=shortcut_name(signal),
                )
            )

        slug, link_expires = issue_setup_link(conn, device["id"], parent_id, created)

        provisioned.append(
            ProvisionedParent(
                parent_id=parent_id,
                display_name=display_name,
                tz=parent_tz,
                device_id=device["id"],
                device_token=token,
                signals=signals,
                setup_url=setup_url_for(base_url, slug),
                setup_expires_utc=link_expires,
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


@dataclass(frozen=True)
class RevokedDevice:
    """What a revocation actually killed, for the operator to read back."""

    device_id: Any
    platform: str
    parent_name: str
    family_name: str
    already_revoked: bool


def set_parent_signals(
    conn: psycopg.Connection, device_token: str, keys: list[str]
) -> tuple[str, list[str]] | None:
    """Re-point an existing parent's allowlist at a chosen signal set.

    The Appa case (QUESTIONS 107): a live parent moving from per-app keys to the
    merged pair, without hand-written SQL. Chosen keys are upserted active with
    the vocabulary's alarm grade; everything else the parent had goes inactive
    rather than away, so history keeps its rows and `Not set up yet` never lies.
    Returns (display_name, active_signals) or None when no device matches.
    """
    chosen = select_signals(keys)
    row = conn.execute(
        """
        select p.id as parent_id, p.display_name
        from devices d join parents p on p.id = d.parent_id
        where d.device_token = %s and d.revoked_utc is null
        """,
        (device_token,),
    ).fetchone()
    if row is None:
        return None

    for signal, alarm_grade in chosen:
        conn.execute(
            """
            insert into parent_signals (parent_id, signal, alarm_grade, active)
            values (%s, %s, %s, true)
            on conflict (parent_id, signal)
            do update set active = true, alarm_grade = excluded.alarm_grade
            """,
            (row["parent_id"], signal, alarm_grade),
        )
    conn.execute(
        "update parent_signals set active = false where parent_id = %s "
        "and signal != all(%s)",
        (row["parent_id"], [signal for signal, _ in chosen]),
    )
    return row["display_name"], [signal for signal, _ in chosen]


def revoke_by_token(
    conn: psycopg.Connection, device_token: str, when: datetime
) -> RevokedDevice | None:
    """Revoke one device by its token. Returns None when the token is unknown.

    A lost phone is an operational emergency, so this is idempotent: revoking an
    already-revoked device reports that fact rather than failing.
    """
    device = db.device_by_token(conn, device_token)
    if device is None:
        return None

    already = not device["active"] or device["revoked_utc"] is not None
    if not already:
        db.revoke_device(conn, device["device_id"], when)

    return RevokedDevice(
        device_id=device["device_id"],
        platform=device["platform"],
        parent_name=device["parent_name"],
        family_name=device["family_name"],
        already_revoked=bool(already),
    )


def mask_token(device_token: str) -> str:
    """Show just enough of a token to confirm which one it was."""
    return f"…{device_token[-6:]}" if len(device_token) > 6 else "…"


def render_revocation(revoked: RevokedDevice, device_token: str) -> str:
    """The operator-facing printout for a revocation."""
    verb = "Already revoked" if revoked.already_revoked else "Revoked"
    return "\n".join(
        [
            f"{verb} device {mask_token(device_token)}",
            f"  family:   {revoked.family_name}",
            f"  parent:   {revoked.parent_name}",
            f"  platform: {revoked.platform}",
            "",
            "That phone's pings are now rejected. Every other device in the "
            "family is unaffected.",
        ]
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
        lines.append(
            f"    setup page:   {parent.setup_url}"
            f"  (expires {parent.setup_expires_utc.date().isoformat()})"
        )
        for sig in parent.signals:
            grade = "alarm" if sig.alarm_grade else "corroborating"
            lines.append(f"    - {sig.shortcut}  ({grade})")
            lines.append(f"      {sig.url}")
        lines.append("")
    lines.append(
        "Tokens are per device: revoking one phone leaves the rest working. "
        "Nobody types these URLs — they ship inside pre-built shortcuts."
    )
    lines.append(
        "The setup page is the one link a family forwards. It shows steps and "
        "the live check, never a file and never a token."
    )
    return "\n".join(lines)


def render_setup_link(issued: IssuedSetupLink, device_token: str) -> str:
    """The operator-facing printout for a re-issued setup link."""
    return "\n".join(
        [
            f"Setup link for {issued.parent_name} ({issued.family_name}), "
            f"device {mask_token(device_token)}:",
            f"  {issued.url}",
            f"  expires {issued.expires_utc.date().isoformat()}",
            "",
            "Any earlier link for this device is now dead, including copies "
            "already sitting in a chat.",
        ]
    )
