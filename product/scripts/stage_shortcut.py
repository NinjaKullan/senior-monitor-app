"""Stage one signed .shortcut for the §5.1 delivery experiment (DECISIONS 102).

    python -m scripts.stage_shortcut \\
        --signed ~/kettle-files/rehearsal-signed/"Kettle — WhatsApp.shortcut" \\
        --unsigned ~/kettle-files/rehearsal-shortcuts/"Kettle — WhatsApp.shortcut" \\
        [--expect-token TOKEN]

The question this exists to answer: does iOS open a `.shortcut` served over
plain HTTPS straight into the Add Shortcut sheet? If yes, Apple's iCloud
sharing is unnecessary and 005b's whole delivery problem becomes a URL. The
harness stages exactly one file into `webapp/public/x/<unguessable>/` so the
next `kettle-app` deploy serves it; nginx gives it the content type (the
experiment's variable — see webapp/nginx.conf), and this prints the URL for
Hema to tap.

**Rehearsal tokens only.** A signed shortcut is an opaque Apple archive — this
tool cannot read a token out of it — so verification runs against the unsigned
sibling the forge wrote in the same run: it must pass `forge.validate`, and its
embedded token is printed loudly (and checked, when `--expect-token` is given)
so what goes on the wire is confirmed against the provisioning printout rather
than against a directory name. The staged path is gitignored; the file carries a
live credential and must never reach the repo.
"""

from __future__ import annotations

import argparse
import plistlib
import re
import secrets
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

from scripts import forge

REPO = Path(__file__).resolve().parent.parent.parent
DEFAULT_DEST = REPO / "webapp" / "public" / "x"
DEFAULT_BASE_URL = "https://kettle-app.fly.dev"

_TOKEN = re.compile(r"/p/([A-Za-z0-9_-]{20,})/[a-z_]+$")


def embedded_token(unsigned: bytes) -> str:
    """The device token inside an unsigned shortcut's ping URL."""
    plist = plistlib.loads(unsigned)
    url = plist["WFWorkflowActions"][0]["WFWorkflowActionParameters"][forge.URL_PARAMETER]
    match = _TOKEN.search(url)
    if match is None:  # pragma: no cover - validate() has already rejected this shape
        raise ValueError(f"no token in {url!r}")
    return match.group(1)


def stage(signed: Path, dest: Path, base_url: str) -> tuple[Path, str]:
    """Copy the signed file under an unguessable slug; return (path, URL).

    18 random bytes -> 24 url-safe characters, the same entropy as a device
    token, for the same reason: the URL *is* the credential while it is live.
    """
    slug = secrets.token_urlsafe(18)
    target = dest / slug / signed.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(signed, target)
    # 0644, not the forge's 0600 (DECISIONS 113): the mode travels into the
    # Docker image, where nginx's worker is not the owner and answered 403 on
    # the founder's first tap. This file exists to be served — the unguessable
    # URL is the credential, and on-disk restrictiveness here breaks the serving
    # while protecting nothing.
    target.chmod(0o644)
    url = f"{base_url.rstrip('/')}/x/{slug}/{quote(signed.name)}"
    return target, url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage one signed rehearsal shortcut.")
    parser.add_argument("--signed", type=Path, required=True, help="the signed .shortcut to serve")
    parser.add_argument(
        "--unsigned",
        type=Path,
        required=True,
        help="its unsigned sibling from the same forge run — the only readable copy",
    )
    parser.add_argument(
        "--expect-token",
        default=None,
        help="fail unless the unsigned file embeds exactly this token (from the printout)",
    )
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args(argv)

    if not args.signed.is_file():
        print(f"no such file: {args.signed}", file=sys.stderr)
        return 2
    raw = args.unsigned.read_bytes() if args.unsigned.is_file() else None
    if raw is None:
        print(f"no such file: {args.unsigned}", file=sys.stderr)
        return 2

    problems = forge.validate(raw, expected_signal=forge.signal_from_name(args.unsigned.name))
    if problems:
        print("refusing to stage: the unsigned copy fails validation —", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1

    token = embedded_token(raw)
    if args.expect_token and token != args.expect_token:
        print(
            f"refusing to stage — the file embeds token {token}, expected {args.expect_token}. "
            "Wrong file, or wrong printout.",
            file=sys.stderr,
        )
        return 1
    if args.signed.read_bytes() == raw:
        print(
            "refusing to stage — --signed and --unsigned are byte-identical, so the "
            "'signed' file is not signed. Run forge-sign.sh first.",
            file=sys.stderr,
        )
        return 1

    target, url = stage(args.signed, args.dest, args.base_url)
    print(f"staged {target}")
    print(f"\nThis file posts pings as device {token} — REHEARSAL TOKENS ONLY.")
    print("The path is unguessable, but the URL is the credential while it lives.\n")
    print(f"  {url}\n")
    print("Deploy so nginx serves it:  cd webapp && npm run ci && fly deploy")
    print("Then tap the URL on the iPhone. Success = Safari opens the Add Shortcut")
    print("sheet directly. Anything else (download, raw bytes, a share sheet):")
    print("change the content type in webapp/nginx.conf (the comment lists the")
    print("order to try) and redeploy. Delete the slug directory when done —")
    print("the experiment ends when the file does.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
