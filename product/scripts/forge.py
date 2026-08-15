"""Shortcut forge — generate real `.shortcut` files for a device (spec 005e).

    python -m scripts.forge --device-token <token> --out out/shortcuts
    python -m scripts.forge --parent "Amma" --out out/shortcuts
    python -m scripts.forge --verify out/shortcuts
    python -m scripts.forge --inspect ~/Downloads/HandBuilt.shortcut

The iCloud-link plan still asked a family to assemble shortcuts by hand in an
app they have never opened. A `.shortcut` file is a plist, and Apple's own
`shortcuts sign` will sign one for distribution, so the assembly step is
removable: this emits one file per active signal, each holding a single
`Get Contents of URL` action pointed at that signal's ping URL, named exactly as
the repair surface names it.

Signing is macOS-only and lives in `forge-sign.sh`. Everything up to the
signature runs anywhere, which is why validation lives here rather than in the
wrapper: the structure can be proved on Linux, in CI, on every push.

**The files this emits are credentials.** The device token is in the URL, and
whoever holds the token can post pings as that phone. Treat an emitted file
exactly like the token: the default output directory is gitignored, and
`--verify` refuses a file carrying anything else secret.

## On the plist format

The schema is stable but under-documented; `specs/QUESTIONS.md` item 69 records
what was known by construction versus inferred, and is now closed — the field
test proved import and ping end-to-end, and the icon values are measured from a
real signed shortcut (item 96b). `--inspect` remains for the next format
question: it prints a real file's shape beside this module's.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import plistlib
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from kettle.signals import SIGNAL_LABELS, STANDARD_SIGNALS, shortcut_name

if TYPE_CHECKING:  # pragma: no cover - typing only, never imported at runtime
    import psycopg

# psycopg and kettle.db are imported *inside* the two functions that query, not
# here. This is a founder tool: `--device-token` alone forges a set of shortcuts
# from a provisioning printout with no database in the picture, and it has to
# run on a bare Mac that has never installed the backend. Importing a
# database driver at module scope made that mode fail with ModuleNotFoundError
# on a laptop in the field (QUESTIONS 77). --verify and --inspect are offline
# for the same reason.

# ---------------------------------------------------------------------------
# The plist
# ---------------------------------------------------------------------------

#: `Get Contents of URL`. The one action a Kettle tripwire performs.
URL_ACTION = "is.workflow.actions.downloadurl"

#: The only parameter that action needs: where to fetch. A bare GET is the
#: default, so no method, no body, no headers — every one of those would be a
#: key an importing Shortcuts build could disagree with us about.
URL_PARAMETER = "WFURL"

#: Client-version keys. Shortcuts writes these on export and uses them to decide
#: whether the running build is new enough to open the file. The values below
#: are deliberately old: they claim little, so nothing modern is required of a
#: parent's phone. See QUESTIONS 69 — these are the least-verified values here.
CLIENT_VERSION = "900"
MINIMUM_CLIENT_VERSION = 900

#: The tile's look (QUESTIONS 96b). Both values are *measured*, not guessed —
#: the founder set the icon by hand in Shortcuts and the iCloud record for the
#: shared shortcut exposed them (`…/shortcuts/api/records/<share-id>` returns
#: `icon_color` and `icon_glyph` directly). That closes item 69's inference:
#: colour is RGBA packed into one integer — 0xFD6631FF, rgb(253, 102, 49) — and
#: the glyph is an id from Apple's built-in set, 0xF259, the chain link.
#: Five unlabelled beige tiles in a library full of Amazon and airline shortcuts
#: was exactly the not-findable case the earlier omission created.
ICON_COLOR = 4251333119
ICON_GLYPH = 62041

#: Every top-level key this module writes, and nothing else. `--verify` requires
#: an exact match rather than a superset: an unexpected key is either a Shortcuts
#: build adding something we do not understand, or an edit nobody meant to make,
#: and on a file that carries a credential both deserve a failed build.
TOP_LEVEL_KEYS = frozenset(
    {
        "WFWorkflowActions",
        "WFWorkflowClientVersion",
        "WFWorkflowHasOutputParameters",
        "WFWorkflowHasShortcutInputVariables",
        "WFWorkflowIcon",
        "WFWorkflowImportQuestions",
        "WFWorkflowInputContentItemClasses",
        "WFWorkflowMinimumClientVersion",
        "WFWorkflowMinimumClientVersionString",
        "WFWorkflowTypes",
    }
)


def build_plist(url: str) -> dict[str, Any]:
    """The whole shortcut, as a plist object. One action, no input, no output.

    Deliberately minimal. Anything that is not the fetch is a thing that can
    break on a phone we cannot see, and a tripwire that silently stopped firing
    is worse for this product than one that never installed.
    """
    return {
        "WFWorkflowActions": [
            {
                "WFWorkflowActionIdentifier": URL_ACTION,
                "WFWorkflowActionParameters": {URL_PARAMETER: url},
            }
        ],
        "WFWorkflowClientVersion": CLIENT_VERSION,
        # Takes nothing, returns nothing. An automation runs it; no one reads it.
        "WFWorkflowHasOutputParameters": False,
        "WFWorkflowHasShortcutInputVariables": False,
        "WFWorkflowImportQuestions": [],
        "WFWorkflowInputContentItemClasses": [],
        "WFWorkflowMinimumClientVersion": MINIMUM_CLIENT_VERSION,
        "WFWorkflowMinimumClientVersionString": CLIENT_VERSION,
        "WFWorkflowTypes": [],
        # Present since QUESTIONS 96b. The key was omitted while the values
        # would have been guesses; these are read from a real signed shortcut,
        # so the "visible oddity on someone's home screen" risk is gone and the
        # unlabelled-beige-tile problem it left behind is what gets fixed.
        "WFWorkflowIcon": {
            "WFWorkflowIconGlyphNumber": ICON_GLYPH,
            "WFWorkflowIconStartColor": ICON_COLOR,
        },
    }


def dump_plist(plist: dict[str, Any]) -> bytes:
    """Serialise deterministically: same inputs, same bytes, diffable output.

    XML rather than binary, and sorted, because these files get regenerated and
    compared. A format whose bytes move on their own would make every diff a
    question about the format instead of about the URL.
    """
    return plistlib.dumps(plist, fmt=plistlib.FMT_XML, sort_keys=True)


def ping_url(base_url: str, token: str, signal: str) -> str:
    """The same URL provisioning prints — one shape, defined in one place."""
    return f"{base_url.rstrip('/')}/p/{token}/{signal}"


def file_name(signal: str) -> str:
    """`Kettle — WhatsApp.shortcut`.

    The name a `.shortcut` imports under is its filename, so this is not
    cosmetic: it is the string the tripwire health view shows when that signal
    needs repair, and the string the founder says on the phone. One source
    (`kettle.signals`) keeps all three in step — and per QUESTIONS 96a the
    parent's name is not in it, so two parents' files are identical by design.
    """
    return f"{shortcut_name(signal)}.shortcut"


# ---------------------------------------------------------------------------
# Secrets discipline
# ---------------------------------------------------------------------------

#: Literal markers for credentials that have no business in a shortcut. The
#: device token is expected — it is the payload — and is not listed.
SECRET_PATTERNS = (
    "DATABASE_URL",
    "postgres://",
    "postgresql://",
    "ntfy.sh",
    "NTFY_TOPIC",
    "TWILIO_",
    "AUTH_TOKEN",
    "SUPABASE_SERVICE",
    "SERVICE_ROLE",
    "sb_secret_",
    "-----BEGIN",
)

_JWT = re.compile(rb"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*")


def _jwt_claims(token: bytes) -> dict[str, Any] | None:
    """The claims inside a JWT-shaped string, or None if it is not really one."""
    try:
        payload = token.split(b".")[1]
        padded = payload + b"=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, binascii.Error, UnicodeDecodeError):
        return None
    return claims if isinstance(claims, dict) else None


def scan_for_secrets(raw: bytes) -> list[str]:
    """Anything credential-shaped in the emitted file, other than the token.

    Decode, do not grep, where JWTs are concerned (adopted as the pattern in
    QUESTIONS 44): a publishable key and a service key are both `eyJ…` and
    differ only in an interior claim, so a pattern match would pass on exactly
    the string it was written to catch.

    Stricter than the webapp's version of the same check, deliberately. There it
    decides whether a key is the *safe* one; here no JWT of any role belongs in
    the file at all, so any that decodes is a finding.
    """
    problems = [f"contains {p!r}" for p in SECRET_PATTERNS if p.encode() in raw]
    problems += [
        f"contains a JWT (role={claims.get('role', 'none')!r})"
        for claims in (_jwt_claims(m) for m in _JWT.findall(raw))
        if claims is not None
    ]
    return problems


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

#: `https://host/p/<token>/<signal>` and nothing else on the end.
_PING_URL = re.compile(r"^https://[^/\s]+(?:/[^/\s]+)*?/p/([A-Za-z0-9_-]{20,})/([a-z_]+)$")


def validate(raw: bytes, expected_signal: str | None = None) -> list[str]:
    """Everything provable about a generated file without a signature.

    Returns a list of problems; empty means valid. Exactness is the point
    throughout — one action, one parameter, one known key set — because the
    failure this guards against is not a typo but an extra action nobody
    noticed, on a file that is about to be sent to someone's mother.
    """
    try:
        plist = plistlib.loads(raw)
    except Exception as exc:  # noqa: BLE001 - any parse failure is one problem
        return [f"not a readable plist: {type(exc).__name__}"]

    if not isinstance(plist, dict):
        return ["top level is not a dictionary"]

    problems: list[str] = []

    keys = set(plist)
    if extra := keys - TOP_LEVEL_KEYS:
        problems.append(f"unexpected top-level keys: {sorted(extra)}")
    if missing := TOP_LEVEL_KEYS - keys:
        problems.append(f"missing top-level keys: {sorted(missing)}")

    actions = plist.get("WFWorkflowActions")
    if not isinstance(actions, list):
        problems.append("WFWorkflowActions is not an array")
        return problems
    if len(actions) != 1:
        problems.append(f"expected exactly one action, found {len(actions)}")
        return problems

    action = actions[0]
    if not isinstance(action, dict):
        problems.append("the action is not a dictionary")
        return problems
    if set(action) != {"WFWorkflowActionIdentifier", "WFWorkflowActionParameters"}:
        problems.append(f"unexpected action keys: {sorted(action)}")

    identifier = action.get("WFWorkflowActionIdentifier")
    if identifier != URL_ACTION:
        problems.append(f"action is {identifier!r}, expected {URL_ACTION!r}")

    parameters = action.get("WFWorkflowActionParameters")
    if not isinstance(parameters, dict):
        problems.append("action parameters are not a dictionary")
        return problems
    if set(parameters) != {URL_PARAMETER}:
        problems.append(f"unexpected action parameters: {sorted(parameters)}")

    # The icon is validated as exactly as the action: a wrong glyph or colour
    # is not corruption, but it is a file that will not look like the other
    # five on the phone, and these get signed and sent.
    icon = plist.get("WFWorkflowIcon")
    if not isinstance(icon, dict):
        problems.append("WFWorkflowIcon is not a dictionary")
    else:
        expected_icon = {
            "WFWorkflowIconGlyphNumber": ICON_GLYPH,
            "WFWorkflowIconStartColor": ICON_COLOR,
        }
        if icon != expected_icon:
            problems.append(f"unexpected icon: {icon!r}")

    url = parameters.get(URL_PARAMETER)
    if not isinstance(url, str):
        problems.append("the URL is not a string")
        return problems

    match = _PING_URL.match(url)
    if match is None:
        problems.append(f"URL is not a ping URL: {url!r}")
    elif expected_signal is not None and match.group(2) != expected_signal:
        problems.append(f"URL signal is {match.group(2)!r}, expected {expected_signal!r}")

    problems += scan_for_secrets(raw)
    return problems


def signal_from_name(name: str) -> str | None:
    """Recover the signal from `Kettle — WhatsApp.shortcut`, or None.

    Used to cross-check a file's name against the URL inside it — the one
    mismatch that would survive every other assertion here and still send a
    family the wrong tripwire.
    """
    stem = name[: -len(".shortcut")] if name.endswith(".shortcut") else name
    for signal, label in SIGNAL_LABELS.items():
        if stem.endswith(f" {label}"):
            return signal
    return None


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def generate(token: str, signals: list[str], base_url: str) -> dict[str, bytes]:
    """{filename: file bytes} for one device. Pure — no filesystem, no clock."""
    return {
        file_name(signal): dump_plist(build_plist(ping_url(base_url, token, signal)))
        for signal in signals
    }


#: Where generated files land unless told otherwise, relative to `product/`.
#: `.gitignore` covers both this directory and `*.shortcut` anywhere in the
#: tree, so the safe path is also the default one and a stray file elsewhere is
#: still not committable. `test_forge.py` proves both with `git check-ignore`.
DEFAULT_OUT = Path("out/shortcuts")


def write(files: dict[str, bytes], out: Path) -> list[Path]:
    """Write the emitted files, owner-readable only.

    0600 because the token is inside: a shortcut sitting in a shared Downloads
    folder is a live credential, and the filesystem should say so.
    """
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for name, raw in sorted(files.items()):
        path = out / name
        path.write_bytes(raw)
        path.chmod(0o600)
        written.append(path)
    return written


DEVICE_SQL = """
select p.display_name, d.device_token, s.signal
from devices d
join parents p on p.id = d.parent_id
join parent_signals s on s.parent_id = p.id
where d.revoked_utc is null and s.active and {where}
order by s.signal
"""


def _lookup(conn: psycopg.Connection, where: str, value: str) -> tuple[str, str, list[str]]:
    rows = conn.execute(DEVICE_SQL.format(where=where), (value,)).fetchall()
    if not rows:
        raise LookupError(f"no active device and signals found for {value!r}")
    tokens = {r["device_token"] for r in rows}
    if len(tokens) > 1:
        raise LookupError(f"{value!r} matches {len(tokens)} devices; use --device-token")
    return rows[0]["display_name"], rows[0]["device_token"], [r["signal"] for r in rows]


def lookup_by_token(conn: psycopg.Connection, token: str) -> tuple[str, str, list[str]]:
    return _lookup(conn, "d.device_token = %s", token)


def lookup_by_parent(conn: psycopg.Connection, name: str) -> tuple[str, str, list[str]]:
    return _lookup(conn, "p.display_name = %s", name)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _inspect(path: Path) -> int:
    """Print a real `.shortcut`'s shape beside this module's.

    The container has no macOS and no Shortcuts app, so the plist schema here is
    asserted from documentation rather than confirmed against an export. This is
    how that gets closed: build one tripwire by hand on a Mac, export it, run
    this, and the two shapes are side by side. Differences are the answer.
    """
    try:
        plist = plistlib.loads(path.read_bytes())
    except Exception as exc:  # noqa: BLE001 - reporting, not handling
        print(f"could not read {path}: {exc}", file=sys.stderr)
        return 1

    mine = build_plist("https://example.test/p/" + "x" * 24 + "/whatsapp")
    theirs = plist if isinstance(plist, dict) else {}

    print(f"--- {path.name}")
    for key in sorted(theirs):
        value = theirs[key]
        shown = value if not isinstance(value, (list, dict)) else f"<{type(value).__name__}>"
        print(f"  {key}: {shown}")
    for index, action in enumerate(theirs.get("WFWorkflowActions", []) or []):
        if isinstance(action, dict):
            print(f"  action[{index}]: {action.get('WFWorkflowActionIdentifier')}")
            print(f"    parameters: {sorted(action.get('WFWorkflowActionParameters', {}))}")

    print("\n--- differences from what forge generates")
    only_theirs = sorted(set(theirs) - set(mine))
    only_mine = sorted(set(mine) - set(theirs))
    print(f"  keys only in {path.name}: {only_theirs or 'none'}")
    print(f"  keys only in forge output: {only_mine or 'none'}")
    print("\nRecord anything surprising in specs/QUESTIONS.md item 69.")
    return 0


def _verify(out: Path) -> int:
    files = sorted(out.glob("*.shortcut"))
    if not files:
        print(f"no .shortcut files in {out}", file=sys.stderr)
        return 1

    failed = 0
    for path in files:
        problems = validate(path.read_bytes(), expected_signal=signal_from_name(path.name))
        if problems:
            failed += 1
            print(f"FAIL {path.name}")
            for problem in problems:
                print(f"     {problem}")
        else:
            print(f"ok   {path.name}")
    print(f"\n{len(files) - failed}/{len(files)} valid")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Kettle .shortcut files.")
    parser.add_argument("--device-token", help="the device to forge shortcuts for")
    parser.add_argument("--parent", help="look the device up by the person's display name")
    parser.add_argument(
        "--name",
        help="optional label for offline output (names left files since QUESTIONS 96a)",
    )
    parser.add_argument(
        "--signals",
        help="comma-separated signals for offline mode (default: the standard set)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="output directory (default %(default)s, which .gitignore covers)",
    )
    parser.add_argument("--verify", type=Path, metavar="DIR", help="validate an output directory")
    parser.add_argument(
        "--inspect",
        type=Path,
        metavar="FILE",
        help="print a real .shortcut's shape beside forge's (run this on a Mac)",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("PUBLIC_BASE_URL", ""),
        help="API base URL for the ping links (default $PUBLIC_BASE_URL)",
    )
    args = parser.parse_args(argv)

    if args.inspect:
        return _inspect(args.inspect)
    if args.verify:
        return _verify(args.verify)

    if not (args.device_token or args.parent):
        parser.error("one of --device-token, --parent, --verify or --inspect is required")
    if not args.base_url:
        parser.error("--base-url (or PUBLIC_BASE_URL) is required when generating")
    if args.name and not args.device_token:
        parser.error("--name labels offline output for --device-token; --parent looks names up")

    database_url = os.environ.get("DATABASE_URL")
    # Offline: the token alone is enough now that filenames carry no parent name
    # (QUESTIONS 96a retired the one thing the database was still needed for on
    # this path). Taken when the command line says so (--name/--signals) or when
    # there is simply no database to ask — the bare-Mac case QUESTIONS 77/78
    # exist for. With a DATABASE_URL and no override, the database stays
    # authoritative about which signals are active.
    if args.device_token and (args.name or args.signals or not database_url):
        # No driver is imported on this path (QUESTIONS 77). The signal list is
        # the standard set unless given, which is what a provisioning printout
        # in the founder's hand actually lists — and it is printed back below
        # so an unexpected sixth file is noticed at the terminal, not on a
        # parent's phone.
        parent_name = args.name
        token = args.device_token
        signals = (
            [s.strip() for s in args.signals.split(",") if s.strip()]
            if args.signals
            else [signal for signal, _ in STANDARD_SIGNALS]
        )
        whose = f" for {parent_name}" if parent_name else ""
        print(f"offline: no database consulted, forging {', '.join(signals)}{whose}")
    else:
        if not database_url:
            print(
                "DATABASE_URL is not set, and --parent needs a database to look a name up. "
                "A device token forges offline without one.",
                file=sys.stderr,
            )
            return 2

        # Imported here, not at module scope: the offline path above must run on
        # a laptop that has never installed psycopg.
        from kettle import db

        with db.connect(database_url) as conn:
            try:
                if args.device_token:
                    parent_name, token, signals = lookup_by_token(conn, args.device_token)
                else:
                    parent_name, token, signals = lookup_by_parent(conn, args.parent)
            except LookupError as exc:
                print(str(exc), file=sys.stderr)
                return 2

    written = write(generate(token, signals, args.base_url), args.out)
    for path in written:
        print(f"wrote {path}")
    label = f" for {parent_name}" if parent_name else ""
    print(
        f"\n{len(written)} unsigned shortcut(s){label}."
        "\nThese files contain the device token — treat them like the token itself."
        "\nNext: ./product/scripts/forge-sign.sh (macOS), then send the signed files."
    )
    return _verify(args.out)


if __name__ == "__main__":
    raise SystemExit(main())
