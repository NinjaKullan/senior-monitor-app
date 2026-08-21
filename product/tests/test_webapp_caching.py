"""DECISIONS 112: the caching contract that stops deploys white-screening.

Hit three times in one evening: nginx sent no Cache-Control on the SPA shell,
browsers heuristically cached it, a deploy renamed the hashed assets, and the
stale shell 404'd its own JavaScript — a blank white page with no error, which a
parent reads as "it broke". The rules are simple enough to assert structurally:
nothing without a content hash in its name may be cached without revalidation,
and everything with one is immutable for a year.
"""

from __future__ import annotations

import re
from pathlib import Path

CONFIG = (Path(__file__).resolve().parent.parent.parent / "webapp" / "nginx.conf").read_text()


def block(prefix: str) -> str:
    """One location block's body, sliced to the next location directive."""
    assert f"location {prefix}" in CONFIG, f"no `location {prefix}` block"
    return CONFIG.split(f"location {prefix}")[1].split("location ")[0]


def test_the_spa_shell_always_revalidates():
    """The shell names the hashed assets, so a stale shell is a broken app."""
    assert 'add_header Cache-Control "no-cache"' in block("= /index.html")
    # The SPA fallback serves the same shell for every route, and the manifest
    # and icons are unhashed too — the whole catch-all revalidates.
    assert 'add_header Cache-Control "no-cache"' in block("/ {")


def test_hashed_assets_are_immutable_for_a_year():
    body = block("/assets/")
    assert "max-age=31536000" in body
    assert "immutable" in body
    assert "public" in body


def test_no_other_block_reintroduces_a_lifetime_on_unhashed_files():
    """The original bug's second half: a regex block matched /assets/*.js with
    higher precedence than the prefix block and capped it at one hour — and gave
    unhashed files a lifetime with no revalidation. Neither may return."""
    assert "expires" not in CONFIG
    # Regex locations outrank prefix locations in nginx; a future one matching
    # by extension would silently override both cache rules above.
    assert not re.search(r"location\s+~", CONFIG), "a regex location outranks the cache rules"


def test_the_experiment_path_stays_uncached():
    """/x/ serves a revocable credential; a cached copy outlives revocation."""
    assert "no-store" in block("/x/")


def test_no_service_worker_exists_to_outlive_this_contract():
    """HTTP caching is the whole update story, and that is load-bearing.

    A service worker would reintroduce DECISIONS 112's failure class with worse
    persistence — a cached app that survives even a fixed server. If one is ever
    added deliberately, it must bring its own update flow, and this test is the
    reminder to design that rather than a ban on doing so.
    """
    webapp = Path(__file__).resolve().parent.parent.parent / "webapp"
    for path in (webapp / "src").rglob("*"):
        if path.is_file() and path.suffix in (".ts", ".tsx", ".js", ".html"):
            assert "serviceWorker" not in path.read_text(), path
    assert not (webapp / "public" / "sw.js").exists()
    index = (webapp / "index.html").read_text()
    assert "serviceWorker" not in index
