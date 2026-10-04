"""DECISIONS 358, docs/chatgpt-plugin-brief.md: the ChatGPT plugin package in
tools/chatgpt-plugin/ and the domain-challenge route on the API."""

from __future__ import annotations

import json
import re
import subprocess
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from kettle.config import settings_from_env
from kettle.main import create_app

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "tools" / "chatgpt-plugin"
ROOT = PACKAGE / "kettle"
BRIEF = REPO / "docs" / "chatgpt-plugin-brief.md"
COPY_BANS = REPO / "site" / "src" / "tests" / "copyBans.ts"

INTERFACE = "com.openai.interface"
#: Brief §2: the manifest's own keys, and the interface block's, in order.
MANIFEST_KEYS = ("$schema", "name", "version", "description", "author", "homepage", "extensions")
INTERFACE_FIELDS = (
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
    "capabilities",
    "websiteURL",
    "supportURL",
    "privacyPolicyURL",
    "termsOfServiceURL",
    "defaultPrompt",
    "logo",
    "composerIcon",
)


def plugin() -> dict:
    return json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))


def interface() -> dict:
    return plugin()["extensions"][INTERFACE]


def readable_strings() -> dict[str, str]:
    """Every string in the manifest a person reads in the directory listing,
    keyed by where it sits. URLs, paths, the schema and the slug are not read.
    The two key tuples above are pinned, so a new string cannot arrive
    anywhere this list does not know about."""
    manifest = plugin()
    block = interface()
    out = {
        "description": manifest["description"],
        "author.name": manifest["author"]["name"],
        "displayName": block["displayName"],
        "shortDescription": block["shortDescription"],
        "longDescription": block["longDescription"],
        "developerName": block["developerName"],
        "category": block["category"],
    }
    out.update({f"capabilities[{i}]": s for i, s in enumerate(block["capabilities"])})
    out.update({f"defaultPrompt[{i}]": s for i, s in enumerate(block["defaultPrompt"])})
    return out


# --- §2: the two files ------------------------------------------------------------


def test_both_files_parse_and_carry_every_required_field():
    manifest = plugin()
    # Exactly the brief's keys, verbatim and in order: nothing missing, and
    # nothing extra that the scan below would never read.
    assert tuple(manifest) == MANIFEST_KEYS
    assert manifest["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert manifest["name"] == "heykettle"
    assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])
    assert manifest["description"]
    assert manifest["author"] == {"name": "HeyKettle", "url": "https://heykettle.com"}
    assert manifest["homepage"] == "https://heykettle.com/connect/"
    assert set(manifest["extensions"]) == {INTERFACE}
    block = interface()
    assert tuple(block) == INTERFACE_FIELDS
    assert block["displayName"] == "Kettle"
    assert block["shortDescription"] == "A caregiving log for family"
    assert block["developerName"] == "HeyKettle"
    assert block["category"] == "Productivity"
    assert block["websiteURL"] == "https://heykettle.com"
    assert block["supportURL"] == "https://heykettle.com/connect/"
    assert block["privacyPolicyURL"] == "https://heykettle.com/privacy.html"
    assert block["termsOfServiceURL"] == "https://heykettle.com/terms.html"
    assert len(block["capabilities"]) == 4 and len(block["defaultPrompt"]) == 3
    assert block["logo"] == "./assets/logo.png" == block["composerIcon"]

    servers = json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))
    assert tuple(servers) == ("$schema", "mcpServers")
    assert servers["$schema"] == "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
    assert servers["mcpServers"] == {
        "kettle": {"type": "streamable-http", "url": "https://api.heykettle.com/mcp"}
    }


def pm_copy() -> dict[str, object]:
    """Brief §3, read from the brief: the four long strings are verbatim and
    not to be edited, so the manifest is held to the document rather than to
    a second copy of the words here."""
    text = BRIEF.read_text(encoding="utf-8")
    section = text[text.index("## 3. PM copy") : text.index("## 4. Report")]

    def one(label: str) -> str:
        return re.search(rf"^{re.escape(label)}\n`(.*?)`$", section, re.M | re.S)[1]

    def many(label: str) -> list[str]:
        block = re.search(rf"^{re.escape(label)}\n((?:- `.*`\n)+)", section, re.M)[1]
        return re.findall(r"^- `(.*)`$", block, re.M)

    return {
        "description": one("description (package):"),
        "longDescription": one("longDescription:"),
        "capabilities": many("capabilities:"),
        "defaultPrompt": many("defaultPrompt:"),
    }


def test_the_pm_copy_is_verbatim_from_the_brief():
    copy = pm_copy()
    assert len(copy["capabilities"]) == 4 and len(copy["defaultPrompt"]) == 3
    manifest = plugin()
    block = interface()
    assert manifest["description"] == copy["description"]
    assert block["longDescription"] == copy["longDescription"]
    assert block["capabilities"] == copy["capabilities"]
    assert block["defaultPrompt"] == copy["defaultPrompt"]


def test_every_relative_path_exists_inside_the_root():
    def walk(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for inner in value.values():
                yield from walk(inner)
        elif isinstance(value, list):
            for inner in value:
                yield from walk(inner)

    paths = [s for s in walk(plugin()) if s.startswith("./")]
    assert paths, "the manifest names no file, which cannot be right for a logo"
    for rel in paths:
        target = (ROOT / rel).resolve()
        assert target.is_file(), rel
        assert target.is_relative_to(ROOT.resolve()), f"{rel} escapes the root folder"


def test_the_package_holds_nothing_the_brief_rules_out():
    """No skills/, no .app.json, no hooks, no screenshots: the server has no UI."""
    names = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
    assert names == {"plugin.json", "mcp.json", "assets/logo.png"}
    assert "skills" not in {p.name for p in ROOT.iterdir()}


def test_the_logo_is_the_apps_icon():
    icon = (REPO / "webapp" / "public" / "icon-512.png").read_bytes()
    assert (ROOT / "assets" / "logo.png").read_bytes() == icon
    assert icon[:8] == b"\x89PNG\r\n\x1a\n"


def test_the_limits_hold():
    manifest = plugin()
    block = interface()
    assert len(manifest["description"]) <= 1024
    assert len(block["displayName"]) <= 30
    assert len(block["shortDescription"]) <= 30
    assert len(block["longDescription"]) <= 4000
    assert len(block["developerName"]) <= 80
    assert all(len(p) <= 128 for p in block["defaultPrompt"])
    assert len(block["capabilities"]) <= 20
    assert all(len(c) <= 120 for c in block["capabilities"])
    for where, text in readable_strings().items():
        assert text == text.strip() and text, where


# --- §2: the copy law, under the site's own lists ---------------------------------


def site_ban_lists() -> dict[str, list[str]]:
    """The arrays exported by site/src/tests/copyBans.ts, read from the file
    rather than copied: a second copy of the lists would drift from the first
    the day someone widened one, which is the drift that file exists to stop."""
    # Line comments go first: a quoted word inside one is not an entry.
    source = re.sub(r"//[^\n]*", "", COPY_BANS.read_text(encoding="utf-8"))
    lists: dict[str, list[str]] = {}
    bodies: dict[str, str] = {}
    for name, body in re.findall(r"export const (\w+)(?::[^=]+)? = \[(.*?)\];", source, re.S):
        bodies[name] = body
        # Double- or single-quoted entries; an apostrophe inside one is kept.
        lists[name] = [a or b for a, b in re.findall(r"\"([^\"]*)\"|'([^']*)'", body)]
    # BANNED is the spread of the groups plus any literal written beside them.
    spread = re.findall(r"\.\.\.(\w+)", bodies["BANNED"])
    lists["BANNED"] = [word for group in spread for word in lists[group]] + lists["BANNED"]
    lists["BANNED_GROUPS"] = spread
    return lists


def assert_site_copy_law(text: str, lists: dict[str, list[str]]) -> None:
    """copyLaw.test.tsx's three scans over one string, in Python: no em dash,
    no banned word (word-bounded, dots escaped, either apostrophe), no
    culture-coded term, no exclamation mark, and no app name anywhere (the
    site's "names no app" test). ASCII word boundaries, as a JavaScript
    RegExp without the u flag has. No allowlist: nothing here is exempt."""
    assert "—" not in text, f"an em dash in: {text}"
    lowered = text.lower()
    for word in lists["BANNED"]:
        pattern = r"\b" + re.escape(word).replace("'", "['’]") + r"\b"
        assert not re.search(pattern, lowered, re.ASCII), f"{word!r} appeared in: {text}"
    for word in lists["CULTURE_CODED"]:
        assert not re.search(rf"\b{word}\b", lowered, re.ASCII), (
            f"culture-coded {word!r} in: {text}"
        )
    for app in lists["APP_NAMES"]:
        assert not re.search(rf"\b{app}\b", lowered, re.ASCII), f"app name {app!r} in: {text}"
    assert "!" not in text, f"an exclamation mark in: {text}"


#: One sentence per group the site spreads into BANNED, as copyLaw.test.tsx
#: plants them: a group the parser lost would let its sentence through.
PLANTS = {
    "URGENCY": "Join now, limited places",
    "DIAGNOSIS": "A dementia tracker",
    "MEDICAL": "She may be unwell",
    "ALARM": "Kettle sends an alert when something is wrong",
    "SURVEILLANCE": "Kettle is not tracking messages",
    "VERDICTS": "Know she's fine today",
    "INFERENCE": "Kettle learns her routine over time",
    "MECHANISM": "runs on kettle-api.fly.dev",
}


def test_the_site_lists_are_read_and_each_group_still_bans():
    """The parser is load-bearing: a group that parsed to nothing would pass
    every string, so each group the site spreads into BANNED is named here
    and planted, and the groups outside BANNED are planted too."""
    lists = site_ban_lists()
    assert set(lists["BANNED_GROUPS"]) == set(PLANTS), lists["BANNED_GROUPS"]
    for group, sentence in PLANTS.items():
        assert lists[group], f"{group} parsed to nothing"
        assert all(w in lists["BANNED"] for w in lists[group]), group
        with pytest.raises(AssertionError, match="appeared in"):
            assert_site_copy_law(sentence, lists)
    assert lists["CULTURE_CODED"], "CULTURE_CODED parsed to nothing"
    assert lists["APP_NAMES"], "APP_NAMES parsed to nothing"
    with pytest.raises(AssertionError, match="culture-coded"):
        assert_site_copy_law("Call Amma first", lists)
    with pytest.raises(AssertionError, match="app name"):
        assert_site_copy_law("Ask on WhatsApp how the day went", lists)
    with pytest.raises(AssertionError, match="em dash"):
        assert_site_copy_law("Mom—and Dad", lists)
    with pytest.raises(AssertionError, match="exclamation"):
        assert_site_copy_law("Add a note!", lists)
    # Dots are escaped (the "a.i." lesson): "fly.dev" must not match "flyXdev".
    assert_site_copy_law("a flyXdev word", lists)
    # Either apostrophe, as the site matches.
    with pytest.raises(AssertionError, match="appeared in"):
        assert_site_copy_law("Know she’s fine", lists)


def test_every_string_a_person_reads_passes_the_site_copy_law():
    lists = site_ban_lists()
    for where, text in readable_strings().items():
        try:
            assert_site_copy_law(text, lists)
        except AssertionError as failure:
            raise AssertionError(f"{where}: {failure}") from None


# --- §2: the zip ------------------------------------------------------------------


def test_make_zip_builds_the_root_folder_and_nothing_beside_it(tmp_path: Path):
    result = subprocess.run(
        [str(PACKAGE / "make-zip.sh"), str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    version = plugin()["version"]
    out = tmp_path / f"kettle-plugin-{version}.zip"
    assert Path(result.stdout.strip()) == out.resolve()
    assert out.is_file()
    with zipfile.ZipFile(out) as archive:
        files = [n for n in archive.namelist() if not n.endswith("/")]
        assert sorted(files) == ["kettle/assets/logo.png", "kettle/mcp.json", "kettle/plugin.json"]
        assert all(n.startswith("kettle/") for n in archive.namelist())
        assert json.loads(archive.read("kettle/plugin.json")) == plugin()
        assert archive.testzip() is None


def _ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", path], cwd=REPO, check=False, capture_output=True
    )
    assert result.returncode in (0, 1), result.stderr.decode()
    return result.returncode == 0


def test_make_zip_defaults_to_dist_beside_the_package():
    """Brief §2: `dist/kettle-plugin-<version>.zip`, and dist/ is gitignored."""
    out = PACKAGE / "dist" / f"kettle-plugin-{plugin()['version']}.zip"
    out.unlink(missing_ok=True)
    result = subprocess.run(
        [str(PACKAGE / "make-zip.sh")], check=False, capture_output=True, text=True, cwd=REPO
    )
    assert result.returncode == 0, result.stderr
    assert out.is_file()
    assert Path(result.stdout.strip()) == out.resolve()
    assert _ignored(out.relative_to(REPO).as_posix())
    out.unlink()


def test_dist_is_ignored_and_the_package_is_not():
    assert _ignored("tools/chatgpt-plugin/dist/kettle-plugin-1.0.0.zip")
    # The assertion can fail: the package itself is source.
    assert not _ignored("tools/chatgpt-plugin/kettle/plugin.json")
    assert not _ignored("tools/chatgpt-plugin/make-zip.sh")


# --- §1: the domain challenge -----------------------------------------------------


@pytest.fixture
def challenged(settings, notifier):
    with TestClient(
        create_app(replace(settings, openai_apps_challenge="openai-verify-abc123"), notifier)
    ) as client:
        yield client


def test_the_challenge_is_the_bare_token_as_text_on_every_host(challenged):
    for host in ("api.heykettle.com", "kettle-api.fly.dev", "testserver"):
        response = challenged.get("/.well-known/openai-apps-challenge", headers={"host": host})
        assert response.status_code == 200, host
        assert response.headers["content-type"].startswith("text/plain")
        # Bare: no JSON, no quotes, no trailing newline.
        assert response.content == b"openai-verify-abc123"


def test_the_challenge_is_a_404_while_the_secret_is_unset(settings, notifier):
    assert settings.openai_apps_challenge == ""
    with TestClient(create_app(settings, notifier)) as client:
        response = client.get("/.well-known/openai-apps-challenge")
        assert response.status_code == 404
        assert b"openai" not in response.content


def test_the_setting_is_read_from_the_environment_and_stripped():
    base = {"DATABASE_URL": "postgresql:///x"}
    assert settings_from_env(base).openai_apps_challenge == ""
    token = settings_from_env({**base, "OPENAI_APPS_CHALLENGE": " tok-1 \n"})
    assert token.openai_apps_challenge == "tok-1"
