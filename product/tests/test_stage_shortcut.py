"""The §5.1 staging harness (QUESTIONS 102): what can be proved before the tap.

The experiment itself — does iOS open a served `.shortcut` straight into the
Add Shortcut sheet? — happens on Hema's iPhone and cannot be tested here. What
can be proved is the discipline around it: the harness refuses files it cannot
vouch for, the slug carries token-grade entropy, the staged path can never be
committed, and nginx actually carries the content-type block the experiment
turns on.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from scripts import forge
from testsupport import BASE_URL

REPO = Path(__file__).resolve().parent.parent.parent
TOKEN = "REHEt0ken_REHEt0ken_REHE"


def _files(tmp_path: Path, signal: str = "whatsapp") -> tuple[Path, Path]:
    """An unsigned forge file and a stand-in 'signed' sibling (different bytes)."""
    name = forge.file_name(signal)
    unsigned = tmp_path / "unsigned" / name
    unsigned.parent.mkdir()
    unsigned.write_bytes(forge.generate(TOKEN, [signal], BASE_URL)[name])
    signed = tmp_path / "signed" / name
    signed.parent.mkdir()
    # A signed shortcut is an opaque Apple archive; any different bytes model it.
    signed.write_bytes(b"AEA1" + unsigned.read_bytes())
    return signed, unsigned


def run(*argv: str) -> subprocess.CompletedProcess[str]:
    import sys

    return subprocess.run(
        [sys.executable, "-m", "scripts.stage_shortcut", *argv],
        cwd=REPO / "product",
        capture_output=True,
        text=True,
        check=False,
    )


def test_stages_one_file_at_an_unguessable_path(tmp_path: Path):
    signed, unsigned = _files(tmp_path)
    dest = tmp_path / "x"

    result = run(
        "--signed", str(signed), "--unsigned", str(unsigned),
        "--dest", str(dest), "--base-url", "https://kettle-app.fly.dev",
    )

    assert result.returncode == 0, result.stderr
    staged = list(dest.rglob("*.shortcut"))
    assert len(staged) == 1
    assert staged[0].read_bytes() == signed.read_bytes()
    # World-readable (QUESTIONS 113): the mode travels into the Docker image,
    # and 0600 there means nginx's worker answers 403. The URL is the guard.
    assert staged[0].stat().st_mode & 0o777 == 0o644
    # Token-grade entropy in the slug: 18 url-safe bytes -> 24 characters.
    slug = staged[0].parent.name
    assert len(slug) >= 24
    # The printed URL names the slug and percent-encodes the filename.
    assert f"/x/{slug}/" in result.stdout
    assert "Kettle%20%E2%80%94%20WhatsApp.shortcut" in result.stdout
    # The token warning is loud and names the device.
    assert TOKEN in result.stdout
    assert "REHEARSAL TOKENS ONLY" in result.stdout


def test_two_stagings_never_share_a_slug(tmp_path: Path):
    signed, unsigned = _files(tmp_path)
    dest = tmp_path / "x"
    for _ in range(2):
        assert run(
            "--signed", str(signed), "--unsigned", str(unsigned), "--dest", str(dest)
        ).returncode == 0
    assert len({p.parent.name for p in dest.rglob("*.shortcut")}) == 2


def test_refuses_an_unsigned_copy_that_fails_validation(tmp_path: Path):
    """The gate is forge.validate — the same one that guards signing."""
    signed, unsigned = _files(tmp_path)
    import plistlib

    plist = plistlib.loads(unsigned.read_bytes())
    plist["WFWorkflowActions"].append(
        {"WFWorkflowActionIdentifier": "is.workflow.actions.getclipboard",
         "WFWorkflowActionParameters": {}}
    )
    unsigned.write_bytes(forge.dump_plist(plist))

    result = run(
        "--signed", str(signed), "--unsigned", str(unsigned), "--dest", str(tmp_path / "x")
    )
    assert result.returncode == 1
    assert "fails validation" in result.stderr
    assert not (tmp_path / "x").exists()


def test_refuses_a_token_that_disagrees_with_the_printout(tmp_path: Path):
    signed, unsigned = _files(tmp_path)
    result = run(
        "--signed", str(signed), "--unsigned", str(unsigned),
        "--dest", str(tmp_path / "x"), "--expect-token", "SOMEOTHERtokenSOMEOTHER1",
    )
    assert result.returncode == 1
    assert TOKEN in result.stderr
    assert not (tmp_path / "x").exists()


def test_refuses_an_unsigned_file_masquerading_as_signed(tmp_path: Path):
    """Byte-identical inputs mean nobody ran forge-sign.sh."""
    _, unsigned = _files(tmp_path)
    result = run(
        "--signed", str(unsigned), "--unsigned", str(unsigned), "--dest", str(tmp_path / "x")
    )
    assert result.returncode == 1
    assert "not signed" in result.stderr


def test_the_staging_area_can_never_be_committed():
    """The staged file is a live credential; git must refuse the whole directory."""
    check = subprocess.run(
        ["git", "check-ignore", "-q", "webapp/public/x/slug/anything.txt"],
        cwd=REPO,
        check=False,
    )
    assert check.returncode == 0
    # And a tracked path still is not ignored, so this test can actually fail.
    control = subprocess.run(
        ["git", "check-ignore", "-q", "webapp/nginx.conf"], cwd=REPO, check=False
    )
    assert control.returncode == 1


def test_nginx_serves_the_staging_path_with_the_experiment_content_type():
    """The config half of the experiment, asserted structurally.

    The content type is the experiment's variable, so the assertion is that the
    block exists, scopes to /x/, disables caching and suppresses the default
    type map — not which type is currently being tried.
    """
    config = (REPO / "webapp" / "nginx.conf").read_text()
    assert "location /x/" in config
    # Slice to the next location rather than the next brace: the inner
    # `types { }` block closes a brace of its own.
    block = config.split("location /x/")[1].split("location ")[0]
    assert "default_type" in block
    assert "no-store" in block
    assert "types { }" in block or "types {}" in block
    assert "try_files $uri =404" in block
