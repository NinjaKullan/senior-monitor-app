"""The shortcut forge (spec 005e): everything that can be proved without a Mac.

The signature cannot be produced here — `shortcuts sign` is macOS-only — so the
line this file draws is deliberate: *structure* is proved on every push, and the
signature is the only step that waits for the founder's laptop. That makes the
plant tests the load-bearing part. A generator that emits a plausible plist is
worth nothing; what matters is that a plist with a second action, or an extra
key, or someone else's URL, is rejected rather than signed and sent to a parent.
"""

from __future__ import annotations

import base64
import json
import plistlib
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest

from kettle.provisioning import provision_family
from kettle.signals import SIGNAL_LABELS, STANDARD_SIGNALS
from scripts import forge
from testsupport import BASE_URL

REPO = Path(__file__).resolve().parent.parent.parent
TOKEN = "TESTt0ken_TESTt0ken_TEST"  # 24 url-safe chars, the shape tokens.py emits
PARENT = "Demo Amma"


def one(signal: str = "whatsapp", token: str = TOKEN) -> bytes:
    """One generated file's bytes."""
    return forge.generate(PARENT, token, [signal], BASE_URL)[forge.file_name(PARENT, signal)]


# ---------------------------------------------------------------------------
# §2.1 — what comes out
# ---------------------------------------------------------------------------


def test_a_generated_shortcut_round_trips_through_plistlib():
    """AC1/AC2: parse it back and find exactly the fetch we put in."""
    plist = plistlib.loads(one())

    assert list(plist["WFWorkflowActions"]) == [
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
            "WFWorkflowActionParameters": {
                "WFURL": f"{BASE_URL}/p/{TOKEN}/whatsapp",
            },
        }
    ]
    assert plist["WFWorkflowHasOutputParameters"] is False
    assert plist["WFWorkflowHasShortcutInputVariables"] is False
    assert forge.validate(one(), expected_signal="whatsapp") == []


def test_the_file_is_named_the_way_the_repair_surface_names_it():
    """One vocabulary: the app, the shortcut on the phone, and this filename."""
    assert forge.file_name(PARENT, "whatsapp") == "Kettle — Demo Amma WhatsApp.shortcut"
    assert forge.file_name(PARENT, "charge_on") == "Kettle — Demo Amma Charger On.shortcut"

    # And the name survives the round trip back to a signal, for every signal a
    # parent can be provisioned with — that is what lets validate() cross-check
    # a file's name against the URL inside it.
    for signal, _ in STANDARD_SIGNALS:
        assert forge.signal_from_name(forge.file_name(PARENT, signal)) == signal


def test_one_file_per_signal_each_pointed_at_its_own_url():
    files = forge.generate(PARENT, TOKEN, ["whatsapp", "device_alive"], BASE_URL)

    assert sorted(files) == [
        "Kettle — Demo Amma Daily Check.shortcut",
        "Kettle — Demo Amma WhatsApp.shortcut",
    ]
    for name, raw in files.items():
        assert forge.validate(raw, expected_signal=forge.signal_from_name(name)) == []


def test_output_is_byte_identical_across_runs(tmp_path: Path):
    """AC3: two runs diff clean, so a regenerated file is reviewable."""
    first, second = tmp_path / "a", tmp_path / "b"
    signals = [s for s, _ in STANDARD_SIGNALS]
    forge.write(forge.generate(PARENT, TOKEN, signals, BASE_URL), first)
    forge.write(forge.generate(PARENT, TOKEN, signals, BASE_URL), second)

    for path in sorted(first.iterdir()):
        assert path.read_bytes() == (second / path.name).read_bytes(), path.name
    assert subprocess.run(["diff", "-r", first, second], check=False).returncode == 0


def test_written_files_are_owner_only(tmp_path: Path):
    """The token is inside. The filesystem should say so."""
    written = forge.write(forge.generate(PARENT, TOKEN, ["whatsapp"], BASE_URL), tmp_path / "o")
    assert written
    for path in written:
        assert path.stat().st_mode & 0o077 == 0, f"{path.name} is readable by others"


# ---------------------------------------------------------------------------
# §2.2 — the plants: what validation must reject
# ---------------------------------------------------------------------------


def _mutated(mutate) -> bytes:
    plist = plistlib.loads(one())
    mutate(plist)
    return forge.dump_plist(plist)


def test_a_second_action_fails_validation():
    """The one that matters. A shortcut is only as safe as its shortest list."""

    def add_action(plist):
        plist["WFWorkflowActions"].append(
            {
                "WFWorkflowActionIdentifier": "is.workflow.actions.getclipboard",
                "WFWorkflowActionParameters": {},
            }
        )

    problems = forge.validate(_mutated(add_action))
    assert problems, "a second action passed validation"
    assert "exactly one action" in problems[0]


def test_an_extra_top_level_key_fails_validation():
    problems = forge.validate(_mutated(lambda p: p.update({"WFWorkflowIcon": {}})))
    assert any("unexpected top-level keys" in p for p in problems), problems


def test_a_missing_top_level_key_fails_validation():
    problems = forge.validate(_mutated(lambda p: p.pop("WFWorkflowTypes")))
    assert any("missing top-level keys" in p for p in problems), problems


def test_an_extra_action_parameter_fails_validation():
    """A header or a POST body would arrive exactly this way."""

    def add_parameter(plist):
        plist["WFWorkflowActions"][0]["WFWorkflowActionParameters"]["WFHTTPMethod"] = "POST"

    problems = forge.validate(_mutated(add_parameter))
    assert any("unexpected action parameters" in p for p in problems), problems


def test_a_different_action_fails_validation():
    def swap(plist):
        plist["WFWorkflowActions"][0]["WFWorkflowActionIdentifier"] = "is.workflow.actions.gettext"

    problems = forge.validate(_mutated(swap))
    assert any("expected 'is.workflow.actions.downloadurl'" in p for p in problems), problems


@pytest.mark.parametrize(
    "url",
    [
        "http://kettle-api.test/p/" + TOKEN + "/whatsapp",  # not https
        "https://kettle-api.test/p/short/whatsapp",  # token too short to be one
        "https://kettle-api.test/pings/" + TOKEN + "/whatsapp",  # not the ping route
        "https://evil.test/collect?u=" + TOKEN,  # somewhere else entirely
    ],
)
def test_a_url_that_is_not_a_ping_url_fails_validation(url: str):
    problems = forge.validate(_mutated(lambda p: _set_url(p, url)))
    assert any("not a ping URL" in p for p in problems), (url, problems)


def _set_url(plist, url: str) -> None:
    plist["WFWorkflowActions"][0]["WFWorkflowActionParameters"]["WFURL"] = url


def test_a_file_whose_name_disagrees_with_its_url_fails_validation():
    """The mismatch every other assertion here would happily sign and send."""
    whatsapp_bytes = one("whatsapp")
    named_youtube = forge.file_name(PARENT, "youtube")

    problems = forge.validate(whatsapp_bytes, expected_signal=forge.signal_from_name(named_youtube))
    assert any("URL signal is" in p for p in problems), problems


def test_garbage_is_reported_rather_than_raised():
    """`--verify` on a directory should name the bad file, not stack-trace."""
    problems = forge.validate(b"not a plist at all")
    assert len(problems) == 1
    assert problems[0].startswith("not a readable plist:")


# ---------------------------------------------------------------------------
# §2.3 — the secrets discipline
# ---------------------------------------------------------------------------


def test_a_generated_file_carries_the_token_and_nothing_else_secret():
    raw = one()
    assert TOKEN.encode() in raw, "the token is the payload; it belongs here"
    assert forge.scan_for_secrets(raw) == []


@pytest.mark.parametrize(
    "planted",
    [
        "postgresql://kettle:hunter2@db.internal:5432/kettle",
        "DATABASE_URL",
        "https://ntfy.sh/kettle-founder-alerts",
        "sb_secret_deadbeefdeadbeef",
        "-----BEGIN PRIVATE KEY-----",
    ],
)
def test_planted_credentials_are_caught(planted: str):
    """Each of these has a real home in this repo's env, and none is a URL."""
    assert forge.scan_for_secrets(_mutated(lambda p: p.update({"WFWorkflowTypes": [planted]})))


def test_a_jwt_is_caught_by_decoding_it_not_by_matching_its_shape():
    """Item 44's pattern: a service key and a safe key differ only inside.

    Stricter here than in the webapp — no JWT of any role belongs in a shortcut
    — so this plants the *anon* one, the key a shape-matcher would most happily
    wave through, and requires it to be caught anyway.
    """
    def jwt(role: str) -> str:
        claims = json.dumps({"role": role}).encode()
        payload = base64.urlsafe_b64encode(claims).decode().rstrip("=")
        return f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{payload}.c2lnbmF0dXJlc2lnbmF0dXJl"

    for role in ("service_role", "anon"):
        token = jwt(role)
        planted = _mutated(lambda p: p.update({"WFWorkflowTypes": [token]}))  # noqa: B023
        found = forge.scan_for_secrets(planted)
        assert any(f"role={role!r}" in problem for problem in found), (role, found)

    # And a merely JWT-shaped string that decodes to nothing is not a finding —
    # the check reads the claims rather than the punctuation.
    assert forge.scan_for_secrets(b"eyJnotreallyajwt.notbase64json.sig") == []


# ---------------------------------------------------------------------------
# §2.4 — the gitignore guarantee
# ---------------------------------------------------------------------------


def _ignored(path: str) -> bool:
    """Ask git itself. Reading .gitignore and matching by hand would only test
    this file's idea of gitignore syntax, which is not the thing that decides."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", path], cwd=REPO, check=False, capture_output=True
    )
    assert result.returncode in (0, 1), result.stderr.decode()
    return result.returncode == 0


def test_the_output_directory_cannot_be_committed():
    """AC5: emitted files are credentials; git must refuse them by default."""
    assert _ignored(f"product/{forge.DEFAULT_OUT}/{forge.file_name(PARENT, 'whatsapp')}")
    assert _ignored("out/anything.shortcut")


def test_a_shortcut_written_anywhere_else_is_still_ignored():
    """The founder will one day pass --out ~/Desktop, or into the repo root.

    The directory rule alone would not cover that, so `*.shortcut` is ignored
    tree-wide as well — belt and braces on a file that carries a live token.
    """
    assert _ignored("product/kettle/Kettle — Demo Amma WhatsApp.shortcut")
    assert _ignored("webapp/src/whatever.shortcut")


def test_the_ignore_test_can_actually_fail():
    """A check-ignore assertion that always passes would be worse than none."""
    assert not _ignored("product/scripts/forge.py")
    assert not _ignored("README.md")


# ---------------------------------------------------------------------------
# §2 — the signing wrapper, from the side that cannot run it
# ---------------------------------------------------------------------------


def test_the_signing_wrapper_refuses_to_run_off_macos():
    """AC4, tested rather than asserted-by-comment.

    Running it here would fail regardless — there is no `shortcuts` binary — but
    it would fail as "command not found", which reads like a missing package and
    sends someone looking for one. The guard makes the boundary legible, so the
    guard is what gets tested.
    """
    script = REPO / "product" / "scripts" / "forge-sign.sh"
    assert script.exists()
    assert script.stat().st_mode & 0o111, "forge-sign.sh is not executable"

    result = subprocess.run(["bash", str(script), "irrelevant"], check=False, capture_output=True)
    assert result.returncode == 2
    assert "macOS only" in result.stderr.decode()


# ---------------------------------------------------------------------------
# QUESTIONS 77 — the bare-Mac path
# ---------------------------------------------------------------------------

#: Makes `import psycopg` fail the way it fails on a laptop that never installed
#: the backend. Monkeypatching the module object would not do: the bug was an
#: import at module scope, so the test has to run a real interpreter in which
#: the driver genuinely cannot be imported.
NO_PSYCOPG = """
import sys

class Absent:
    def find_module(self, name, path=None):
        return self.find_spec(name, path)

    def find_spec(self, name, path=None, target=None):
        if name == "psycopg" or name.startswith("psycopg."):
            raise ModuleNotFoundError("No module named 'psycopg'")
        return None

sys.meta_path.insert(0, Absent())
"""


def _forge_without_psycopg(tmp_path: Path, *args: str, **env_extra: str):
    blocker = tmp_path / "sitecustomize.py"
    blocker.write_text(NO_PSYCOPG)
    env = {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": f"{tmp_path}:{REPO / 'product'}",
        "PUBLIC_BASE_URL": "https://kettle-api.test",
        **env_extra,
    }
    return subprocess.run(
        [sys.executable, "-m", "scripts.forge", *args],
        cwd=REPO / "product",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_the_blocker_really_blocks_psycopg(tmp_path: Path):
    """Otherwise every test below would pass on a machine that simply has it.

    Drives the *database* path — a parent lookup with a DATABASE_URL set — which
    is the one path that must still import the driver. It has to fail, and fail
    for the right reason.
    """
    result = _forge_without_psycopg(
        tmp_path,
        "--parent",
        "Amma",
        "--out",
        str(tmp_path / "x"),
        DATABASE_URL="postgresql://unused.invalid/db",
    )

    assert result.returncode != 0
    assert "No module named 'psycopg'" in (result.stderr + result.stdout)


def test_device_token_mode_runs_with_psycopg_absent(tmp_path: Path):
    """QUESTIONS 77: the founder's laptop has a token and no backend installed.

    `--device-token --name` needs nothing from the database — the token and the
    name are both on the command line — so it must not import a driver to prove
    it. This failed in the field with ModuleNotFoundError before the import
    moved inside the query path.
    """
    out = tmp_path / "shortcuts"
    result = _forge_without_psycopg(
        tmp_path, "--device-token", TOKEN, "--name", "Amma", "--out", str(out)
    )

    assert result.returncode == 0, result.stderr
    assert "offline: no database consulted" in result.stdout
    written = sorted(p.name for p in out.iterdir())
    assert written == sorted(forge.file_name("Amma", s) for s, _ in STANDARD_SIGNALS)
    for path in out.iterdir():
        assert forge.validate(path.read_bytes(), forge.signal_from_name(path.name)) == []


def test_offline_mode_takes_an_explicit_signal_list(tmp_path: Path):
    """A parent who turned one off is a `--signals` away, still with no database."""
    out = tmp_path / "shortcuts"
    result = _forge_without_psycopg(
        tmp_path,
        "--device-token",
        TOKEN,
        "--name",
        "Amma",
        "--signals",
        "whatsapp,device_alive",
        "--out",
        str(out),
    )

    assert result.returncode == 0, result.stderr
    assert sorted(p.name for p in out.iterdir()) == [
        "Kettle — Amma Daily Check.shortcut",
        "Kettle — Amma WhatsApp.shortcut",
    ]


def test_verify_and_inspect_are_offline_too(tmp_path: Path):
    """Both run on the founder's Mac after signing; neither needs a database."""
    out = tmp_path / "shortcuts"
    forge.write(forge.generate("Amma", TOKEN, ["whatsapp"], BASE_URL), out)

    assert _forge_without_psycopg(tmp_path, "--verify", str(out)).returncode == 0
    inspected = _forge_without_psycopg(
        tmp_path, "--inspect", str(out / forge.file_name("Amma", "whatsapp"))
    )
    assert inspected.returncode == 0
    assert "differences from what forge generates" in inspected.stdout


def test_a_token_with_no_name_and_no_database_says_what_to_do(tmp_path: Path):
    """The failure the founder actually hit, now with an instruction in it."""
    result = _forge_without_psycopg(tmp_path, "--device-token", TOKEN, "--out", str(tmp_path / "x"))

    assert result.returncode == 2
    assert "--name" in result.stderr


# ---------------------------------------------------------------------------
# AC1 — against a really provisioned device
# ---------------------------------------------------------------------------


@pytest.fixture
def provisioned(conn: psycopg.Connection):
    return provision_family(
        conn, "Forge", "Asia/Kolkata", [("Demo Amma", None)], base_url=BASE_URL
    )


def test_forging_for_a_provisioned_device_emits_every_active_signal(
    conn: psycopg.Connection, provisioned
):
    parent = provisioned.parents[0]
    name, token, signals = forge.lookup_by_token(conn, parent.device_token)

    assert name == "Demo Amma"
    assert token == parent.device_token
    assert sorted(signals) == sorted(s for s, _ in STANDARD_SIGNALS)

    files = forge.generate(name, token, signals, BASE_URL)
    assert len(files) == len(STANDARD_SIGNALS)
    for filename, raw in files.items():
        assert forge.validate(raw, expected_signal=forge.signal_from_name(filename)) == []
        # The URL provisioning printed and the URL in the file are the same URL.
        wanted = next(s.url for s in parent.signals if s.shortcut + ".shortcut" == filename)
        assert wanted.encode() in raw


def test_a_deactivated_signal_gets_no_shortcut(conn: psycopg.Connection, provisioned):
    parent = provisioned.parents[0]
    conn.execute(
        "update parent_signals set active = false where parent_id = %s and signal = 'youtube'",
        (parent.parent_id,),
    )

    _, _, signals = forge.lookup_by_token(conn, parent.device_token)
    assert "youtube" not in signals
    assert "whatsapp" in signals


def test_a_revoked_device_forges_nothing(conn: psycopg.Connection, provisioned):
    """A lost phone must not be re-armed by a stale command in someone's history."""
    parent = provisioned.parents[0]
    conn.execute(
        "update devices set revoked_utc = now() where device_token = %s", (parent.device_token,)
    )

    with pytest.raises(LookupError):
        forge.lookup_by_token(conn, parent.device_token)


def test_lookup_by_parent_name_finds_the_same_device(conn: psycopg.Connection, provisioned):
    by_name = forge.lookup_by_parent(conn, "Demo Amma")
    by_token = forge.lookup_by_token(conn, provisioned.parents[0].device_token)
    assert by_name == by_token


def test_an_unknown_parent_is_an_error_not_an_empty_directory(
    conn: psycopg.Connection, provisioned
):
    with pytest.raises(LookupError):
        forge.lookup_by_parent(conn, "Nobody")


def test_every_standard_signal_has_a_human_name_to_forge_under():
    """A signal with no label would emit `Kettle — Amma charge_on.shortcut`."""
    assert {s for s, _ in STANDARD_SIGNALS} <= set(SIGNAL_LABELS)
