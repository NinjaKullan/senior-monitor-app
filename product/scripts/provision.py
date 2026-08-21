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
    issue_setup_link_by_token,
    provision_demo_family,
    provision_family,
    render_revocation,
    render_setup_link,
    render_summary,
    revoke_by_token,
    set_parent_signals,
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
        "--signals",
        default=None,
        metavar="KEY,KEY",
        help="signal set for every parent in this run (default: the standard seed); "
        "e.g. routine,charger,device_alive",
    )
    parser.add_argument(
        "--set-signals",
        metavar="DEVICE_TOKEN",
        default=None,
        help="re-point an existing parent's allowlist to --signals (DECISIONS 107)",
    )
    parser.add_argument(
        "--revoke",
        metavar="DEVICE_TOKEN",
        default=None,
        help="revoke one lost/replaced device; leaves every other device working",
    )
    parser.add_argument(
        "--setup-link",
        metavar="DEVICE_TOKEN",
        default=None,
        help="issue a fresh setup-page link for an existing parent's device; "
        "any earlier link for that device stops answering (spec 005b)",
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
    if args.set_signals and (args.demo or args.family or args.parent or args.revoke):
        parser.error("--set-signals takes only --signals and a device token")
    if args.set_signals and not args.signals:
        parser.error("--set-signals needs --signals to say what the new set is")
    if args.setup_link and (
        args.demo or args.family or args.parent or args.revoke or args.set_signals
    ):
        parser.error("--setup-link takes only a device token")
    if (
        not args.revoke
        and not args.set_signals
        and not args.setup_link
        and not args.demo
        and not (args.family and args.parent)
    ):
        parser.error(
            "--family and at least one --parent are required "
            "(or --demo, --revoke, --set-signals, --setup-link)"
        )

    chosen = (
        [k.strip() for k in args.signals.split(",") if k.strip()] if args.signals else None
    )

    if args.set_signals:
        with db.connect(args.database_url) as conn:
            try:
                result = set_parent_signals(conn, args.set_signals, chosen or [])
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
        if result is None:
            print("No active device matches that token — nothing changed.", file=sys.stderr)
            return 1
        display_name, active = result
        print(f"{display_name} now has exactly: {', '.join(active)}")
        base = args.base_url.rstrip("/")
        for signal in active:
            print(f"  {base}/p/{args.set_signals}/{signal}")
        print("Everything else is inactive (kept, not deleted). Re-forge before delivering.")
        return 0

    if args.setup_link:
        with db.connect(args.database_url) as conn:
            issued = issue_setup_link_by_token(
                conn, args.setup_link, args.base_url, now_utc()
            )
        if issued is None:
            print(
                "No active device matches that token — no link issued. "
                "A revoked device gets no new doors (DECISIONS 95: re-issue "
                "for a replacement phone is still an open tooling gap).",
                file=sys.stderr,
            )
            return 1
        print(render_setup_link(issued, args.setup_link))
        return 0

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
                signals=chosen,
                platform=args.platform,
                owner_email=args.owner_email,
                owner_name=args.owner_name,
            )
    print(render_summary(family))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
