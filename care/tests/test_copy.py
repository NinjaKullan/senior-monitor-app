"""Every §10 string, verbatim (spec 021 acceptance §8.12, §8.13).

The expected values are read out of specs/021-care-compare.md §10 itself, so
there is one copy of the ruling and a drift on either side fails here. The
PAGE_* strings are the site's and are pinned by site/src/tests/care.test.ts
against the same section.
"""

from __future__ import annotations

import re
from pathlib import Path

from care import copy as text

SPEC = Path(__file__).resolve().parents[2] / "specs" / "021-care-compare.md"


def strings_between(start: str, stop: str) -> dict[str, str]:
    body = SPEC.read_text().split(start, 1)[1].split(stop, 1)[0]
    return dict(re.findall(r"\b([A-Z][A-Z0-9_]+) = \"([^\"]*)\"", body))


def section_10() -> dict[str, str]:
    found = strings_between("\n## 10.", "\n## Amendment A")
    assert len(found) == 39, f"§10 changed shape: {len(found)} strings"
    return found


def test_every_server_string_is_verbatim():
    strings = {k: v for k, v in section_10().items() if not k.startswith("PAGE_")}
    assert len(strings) == 26
    for name, value in strings.items():
        assert hasattr(text, name), f"{name} is missing from care/copy.py"
        assert getattr(text, name) == value, name


def test_the_server_is_named_as_the_page_is():
    assert section_10()["PAGE_TITLE"] == text.SERVER_NAME


def test_the_page_strings_are_not_duplicated_here():
    """One home each: the page's strings live in the page."""
    assert not [n for n in dir(text) if n.startswith("PAGE_")]


VERDICTS = ("good", "best", "better", "worse", "safe", "avoid", "top", "recommend", "excellent",
            "poor", "bad")


def test_no_string_the_tools_say_carries_a_dash_or_a_verdict():
    """§4: Kettle never says good, best, safe, avoid, or any verdict. The
    instructions line alone names 'recommend', to say it does not."""
    for name in dir(text):
        value = getattr(text, name)
        if not name.isupper() or not isinstance(value, str):
            continue
        assert "—" not in value and "–" not in value, name
        if name == "SERVER_INSTRUCTIONS":
            value = value.replace("does not rank, recommend, or give", "")
        for word in VERDICTS:
            assert not re.search(rf"\b{word}\b", value, re.IGNORECASE), (name, word)
