"""Provision a beta family, or revoke a lost phone (spec 002 §5).

    python -m scripts.provision --family "Sharma" --parent "Amma" \
        --parent "Appa:America/Chicago" --owner-email child@example.com

    python -m scripts.provision --demo

    python -m scripts.provision --revoke <device_token>

Provisioning prints each person's device token, the ready-to-use ping URLs, and
the name of the shortcut each URL belongs in. This is the onboarding path until
the wizard exists (spec 005).

Revocation exists because a lost phone is an operational emergency and the
operator should not be hand-writing SQL at midnight. It kills exactly one
device; every other phone in the family keeps working.
"""

from __future__ import annotations

import argparse
import os
import sys

from kettle import db
from kettle.provisioning import (
    provision_demo_family,
    provision_family,
    render_revocation,
    render_summary,
    revoke_by_token,
)
from kettle.timeutil import now_utc


def _parse_parent(value: str) -> tuple[str, str | None]:
    """'Amma' or 'Amma:America/Chicago' -> (name, tz or None)."""
    name, _, tz = value.partition(":")
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError("parent name cannot be empty")
    return name, (tz.strip() or None)


def main(argv: list[str] | None = None) -> int:
    """Provision one family; returns a process exit code."""
    parser = argparse.ArgumentParser(description="Provision a Kettle family.")
    parser.add_argument("--family", help="family name")
    parser.add_argument(
        "--tz",
        default=os.environ.get("DEFAULT_TZ", "Asia/Kolkata"),
        help="family timezone (default %(default)s)",
    )
    parser.add_argument(
        "--parent",
        action="append",
        default=[],
        metavar="NAME[:TZ]",
        help="a monitored loved one; repeat per person. TZ overrides family tz",
    )
    parser.add_argument(
        "--platform",
        default="ios_shortcuts",
        choices=("ios_shortcuts", "android"),
    )
    parser.add_argument("--owner-email", default=None)
    parser.add_argument("--owner-name", default=None)
    parser.add_argument(
        "--demo", action="store_true", help="provision the standard demo family"
    )
    parser.add_argument(
        "--revoke",
        metavar="DEVICE_TOKEN",
        default=None,
        help="revoke one lost/replaced device; leaves every other device working",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("PUBLIC_BASE_URL", "https://kettle-api.fly.dev"),
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="defaults to $DATABASE_URL",
    )
    args = parser.parse_args(argv)

    if not args.database_url:
        parser.error("DATABASE_URL is not set and --database-url was not given")
    if args.revoke and (args.demo or args.family or args.parent):
        parser.error("--revoke cannot be combined with provisioning arguments")
    if not args.revoke and not args.demo and not (args.family and args.parent):
        parser.error(
            "--family and at least one --parent are required (or --demo, or --revoke)"
        )

    if args.revoke:
        with db.connect(args.database_url) as conn:
            revoked = revoke_by_token(conn, args.revoke, now_utc())
        if revoked is None:
            print(
                "No device matches that token — nothing revoked. "
                "Check the token (it is the segment after /p/ in the ping URL) "
                "and try again.",
                file=sys.stderr,
            )
            return 1
        print(render_revocation(revoked, args.revoke))
        return 0

    with db.connect(args.database_url) as conn:
        if args.demo:
            family = provision_demo_family(conn, base_url=args.base_url)
        else:
            family = provision_family(
                conn,
                name=args.family,
                tz=args.tz,
                parents=[_parse_parent(p) for p in args.parent],
                base_url=args.base_url,
                platform=args.platform,
                owner_email=args.owner_email,
                owner_name=args.owner_name,
            )
    print(render_summary(family))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
