"""Provision a beta family, or revoke a lost phone (spec 002 §5).

    python -m scripts.provision --family "Sharma" --parent "Amma::Mom" \
        --parent "Appa:America/Chicago:Dad" --owner-email child@example.com

    python -m scripts.provision --demo

    python -m scripts.provision --revoke <device_token>
    python -m scripts.provision --revoke=<device_token>   # equivalent

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
    set_parent_relationship,
    set_parent_signals,
)
from kettle.timeutil import now_utc


def _parse_parent(value: str) -> tuple[str, str | None, str | None]:
    """'Amma', 'Amma:America/Chicago', 'Amma:America/Chicago:Mom' or 'Amma::Mom'.

    Returns (name, tz or None, relationship or None). The second field is
    always the timezone — a label with no tz needs the empty field ('Amma::Mom')
    so that a mistyped position fails loudly in `check_relationship` instead of
    being stored as a timezone.
    """
    name, _, rest = value.partition(":")
    tz, _, relationship = rest.partition(":")
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError("parent name cannot be empty")
    return name, (tz.strip() or None), (relationship.strip() or None)


#: Options whose value is a device token, and therefore may begin with a dash.
TOKEN_OPTIONS = ("--revoke", "--setup-link", "--set-signals", "--set-relationship")


def join_token_values(argv: list[str], known_options: set[str]) -> list[str]:
    """Rewrite `--revoke <token>` as `--revoke=<token>` when the token needs it.

    Device tokens are `secrets.token_urlsafe`, whose alphabet is `A-Za-z0-9-_`,
    so about one token in sixty-four starts with a dash — and argparse reads a
    dashed value as another flag ("expected one argument"). That turned
    revoking a *lost phone* into a confusing failure roughly every sixty-fourth
    time it mattered (DECISIONS 136).

    The `=` form has always worked and stays documented; this makes the bare
    form work too, by joining the pair before argparse ever sees them. A value
    that is a real option string is left alone, so `--revoke --demo` still
    fails the way it should rather than being swallowed as a token.
    """
    joined: list[str] = []
    index = 0
    while index < len(argv):
        argument = argv[index]
        following = argv[index + 1] if index + 1 < len(argv) else None
        if (
            argument in TOKEN_OPTIONS
            and following is not None
            and following.startswith("-")
            and following not in known_options
        ):
            joined.append(f"{argument}={following}")
            index += 2
            continue
        joined.append(argument)
        index += 1
    return joined


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
        metavar="NAME[:TZ][:REL]",
        help="a monitored loved one; repeat per person. TZ overrides family tz; "
        "REL is the relationship label outbound copy renders (DECISIONS 149), "
        "e.g. 'Amma::Mom'",
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
        "--set-relationship",
        metavar="DEVICE_TOKEN",
        default=None,
        help="set an existing parent's relationship label to --relationship "
        "(DECISIONS 149); until set, relationship-bearing messages skip them",
    )
    parser.add_argument(
        "--relationship",
        default=None,
        metavar="LABEL",
        help="the label for --set-relationship, from the standard set "
        "(Mom, Dad, Grandma, Grandpa, Aunt, Uncle)",
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
    known_options = {
        option for action in parser._actions for option in action.option_strings
    }
    args = parser.parse_args(
        join_token_values(list(sys.argv[1:] if argv is None else argv), known_options)
    )

    if not args.database_url:
        parser.error("DATABASE_URL is not set and --database-url was not given")
    if args.revoke and (args.demo or args.family or args.parent):
        parser.error("--revoke cannot be combined with provisioning arguments")
    if args.set_signals and (args.demo or args.family or args.parent or args.revoke):
        parser.error("--set-signals takes only --signals and a device token")
    if args.set_signals and not args.signals:
        parser.error("--set-signals needs --signals to say what the new set is")
    if args.set_relationship and (
        args.demo or args.family or args.parent or args.revoke or args.set_signals
    ):
        parser.error("--set-relationship takes only --relationship and a device token")
    if args.set_relationship and not args.relationship:
        parser.error("--set-relationship needs --relationship to say what the label is")
    if args.setup_link and (
        args.demo
        or args.family
        or args.parent
        or args.revoke
        or args.set_signals
        or args.set_relationship
    ):
        parser.error("--setup-link takes only a device token")
    if (
        not args.revoke
        and not args.set_signals
        and not args.set_relationship
        and not args.setup_link
        and not args.demo
        and not (args.family and args.parent)
    ):
        parser.error(
            "--family and at least one --parent are required "
            "(or --demo, --revoke, --set-signals, --set-relationship, --setup-link)"
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

    if args.set_relationship:
        with db.connect(args.database_url) as conn:
            try:
                name = set_parent_relationship(conn, args.set_relationship, args.relationship)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
        if name is None:
            print("No active device matches that token — nothing changed.", file=sys.stderr)
            return 1
        print(f"{name} is now [{args.relationship}] in every message that names them.")
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
