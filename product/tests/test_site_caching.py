"""QUESTIONS 112's caching contract, ported to the landing page (item 128).

The webapp's version of this bug white-screened returning browsers; the site's
version is quieter and therefore longer-lived — the six photographs and the
prerendered shell live at stable names, so any cached lifetime would pin old
imagery and old copy to returning visitors until it expired, invisibly. Same
rules, asserted the same way: nothing unhashed caches without revalidation,
everything hashed is immutable for a year, and no later block may outrank
either rule.
"""

from __future__ import annotations

import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent.parent / "site"
CONFIG = (SITE / "nginx.conf").read_text()


def block(prefix: str) -> str:
    """One location block's body, sliced to the next location directive."""
    assert f"location {prefix}" in CONFIG, f"no `location {prefix}` block"
    return CONFIG.split(f"location {prefix}")[1].split("location ")[0]


def test_the_shell_always_revalidates():
    """The prerendered index names the hashed assets; a stale one mismatches."""
    assert 'add_header Cache-Control "no-cache"' in block("= /index.html")
    # The photographs and privacy.html are unhashed too — the whole catch-all
    # revalidates. no-cache, not no-store: an unchanged photograph is a 304.
    assert 'add_header Cache-Control "no-cache"' in block("/ {")


def test_hashed_assets_are_immutable_for_a_year():
    body = block("/assets/")
    assert "max-age=31536000" in body
    assert "immutable" in body
    assert "public" in body


def test_no_other_block_reintroduces_a_lifetime_on_unhashed_files():
    """The webapp bug's second half, banned here from day one: no `expires`,
    and no regex location that would outrank both prefix rules silently."""
    assert "expires" not in CONFIG
    assert not re.search(r"location\s+~", CONFIG), "a regex location outranks the cache rules"


def test_the_photographs_really_are_unhashed_stable_names():
    """The premise the catch-all rule rests on, checked against the tree.

    If imagery ever moves into the hashed pipeline this starts failing, which
    is the right moment to notice the contract's split no longer matches the
    files it was written for.
    """
    webps = sorted(p.name for p in (SITE / "public").glob("*.webp"))
    assert webps == [
        "hero-evening.webp",
        "hero-morning.webp",
        "section-her-afternoon.webp",
        "section-her-morning.webp",
        "section-somethings-off.webp",
        "section-what-you-see.webp",
    ]
    for name in webps:
        assert not re.search(r"[.-][0-9a-f]{8,}\.webp$", name), f"{name} looks hashed"


def test_the_image_serves_from_this_config_not_gostatic():
    """The conf is only a contract if the container actually loads it.

    The site used to ship on gostatic, which can set none of these headers; a
    revert would leave nginx.conf as dead ornament while every response went
    out header-less. The Dockerfile is part of the contract.
    """
    dockerfile = (SITE / "Dockerfile").read_text()
    assert "nginx" in dockerfile
    assert "COPY nginx.conf" in dockerfile
    assert "gostatic" not in dockerfile
    # fly.toml routes to 8080; the conf must listen where fly points.
    assert "listen 8080" in CONFIG
    assert 'internal_port = 8080' in (SITE / "fly.toml").read_text()


def test_no_service_worker_exists_to_outlive_this_contract():
    """HTTP caching is the whole update story here too (webapp precedent)."""
    for path in (SITE / "src").rglob("*"):
        if path.is_file() and path.suffix in (".ts", ".tsx", ".js", ".html"):
            assert "serviceWorker" not in path.read_text(), path
    assert not (SITE / "public" / "sw.js").exists()
    assert "serviceWorker" not in (SITE / "index.html").read_text()
