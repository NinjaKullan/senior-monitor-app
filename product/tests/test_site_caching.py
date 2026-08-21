"""DECISIONS 112's caching contract, ported to the landing page (item 128).

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


def server_blocks() -> dict[str, str]:
    """The file's top-level `server { … }` blocks, keyed by their server_name.

    There are two since DECISIONS 142 — the one that serves the site and the one
    that 301s the retired Fly hostname away — and every rule below is about one
    of them specifically. Slicing the whole file would silently read whichever
    block happens to come first, which is exactly the mistake this helper stops:
    the redirect block owns a `location /` too, and before the split every
    caching assertion here would have started reading *its* body instead.
    """
    parts = re.split(r"^server \{", CONFIG, flags=re.MULTILINE)[1:]
    blocks = {}
    for part in parts:
        name = re.search(r"server_name\s+([^;]+);", part)
        assert name, "a server block with no server_name"
        blocks[name.group(1).strip()] = part
    return blocks


BLOCKS = server_blocks()
assert "_" in BLOCKS, "no default server block — nothing serves the site"
assert "kettle-site.fly.dev" in BLOCKS, (
    "the redirect block is gone: the retired Fly hostname would serve a second "
    "copy of the page instead of forwarding to heykettle.com (DECISIONS 142)"
)
SERVING = BLOCKS["_"]
REDIRECT = BLOCKS["kettle-site.fly.dev"]

#: The config with its comments stripped. Bans below are about what nginx does,
#: and this file explains itself at length — a rule spelled out in prose was
#: tripping the rule that forbids it.
DIRECTIVES = re.sub(r"#[^\n]*", "", CONFIG)


def block(prefix: str, within: str = SERVING) -> str:
    """One location block's body, sliced to the next location directive."""
    assert f"location {prefix}" in within, f"no `location {prefix}` block"
    return within.split(f"location {prefix}")[1].split("location ")[0]


def test_the_shell_always_revalidates():
    """The prerendered index names the hashed assets; a stale one mismatches."""
    assert 'add_header Cache-Control "no-cache"' in block("= /index.html")
    # The illustrations and privacy.html are unhashed too — the whole catch-all
    # revalidates. no-cache, not no-store: an unchanged illustration is a 304.
    assert 'add_header Cache-Control "no-cache"' in block("/ {")


def test_hashed_assets_are_immutable_for_a_year():
    body = block("/assets/")
    assert "max-age=31536000" in body
    assert "immutable" in body
    assert "public" in body


def test_no_other_block_reintroduces_a_lifetime_on_unhashed_files():
    """The webapp bug's second half, banned here from day one: no `expires`,
    and no regex location that would outrank both prefix rules silently."""
    assert "expires" not in DIRECTIVES
    assert not re.search(r"location\s+~", DIRECTIVES), "a regex location outranks the cache rules"


def test_the_illustrations_really_are_unhashed_stable_names():
    """The premise the catch-all rule rests on, checked against the tree.

    If imagery ever moves into the hashed pipeline this starts failing, which
    is the right moment to notice the contract's split no longer matches the
    files it was written for. The names are the illustration set that replaced
    the photographs wholesale (DECISIONS 136); a retired photograph left behind
    in public/ fails here, which is how this list stays a manifest rather than
    a comment.
    """
    webps = sorted(p.name for p in (SITE / "public").glob("*.webp"))
    assert webps == [
        "hero-two-cities.webp",
        "ill-her-afternoon.webp",
        "ill-her-morning.webp",
        "ill-somethings-off.webp",
        "ill-story-strip.webp",
        "ill-what-you-see.webp",
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


# ---------------------------------------------------------------------------
# DECISIONS 142 — the retired Fly hostname forwards instead of duplicating.
# ---------------------------------------------------------------------------


def test_the_old_fly_hostname_301s_to_the_canonical_domain():
    """One page, one address. The canonical link is a hint; this is the answer."""
    assert "return 301 https://heykettle.com$request_uri;" in block("/ {", REDIRECT)
    # $request_uri, not $uri: it carries the query string and the original
    # encoding, so a deep link keeps its path instead of landing on the home page.
    assert "$request_uri" in REDIRECT
    assert "$uri;" not in REDIRECT


def test_the_redirect_is_scoped_to_that_one_host():
    """Host-scoped by server_name, not by an `if` inside the serving block.

    The distinction is the whole safety of this change: requests arriving on
    heykettle.com never enter the redirect block, so the caching contract cannot
    be affected by anything written in it. An `if ($host = ...)` would put the
    two concerns in one block and make that reasoning a matter of reading order.
    """
    assert "server_name kettle-site.fly.dev;" in REDIRECT
    assert "server_name _;" in SERVING
    assert "if (" not in DIRECTIVES, "host routing belongs in server_name, not in `if`"
    # The serving block must not have grown a redirect of its own.
    assert "return 301" not in SERVING


def test_the_serving_block_still_owns_the_whole_caching_contract():
    """The contract on the real domain is untouched — asserted, not assumed."""
    assert "Cache-Control" not in REDIRECT
    for prefix in ("/assets/", "= /index.html", "/ {"):
        assert f"location {prefix}" in SERVING


def test_healthz_answers_on_both_hosts_rather_than_redirecting():
    """A machine asked whether it is alive answers for itself.

    fly.toml configures no HTTP check today, so nothing breaks either way right
    now. This is about the check somebody adds later: a health endpoint that
    301s to a different host reports on that host, and a machine that is
    actually down would still look fine.
    """
    assert "return 200 '{\"ok\":true}';" in block("/healthz", REDIRECT)
    assert "return 200 '{\"ok\":true}';" in block("/healthz", SERVING)


def test_the_canonical_link_names_the_domain_the_redirect_points_at():
    """The two halves of the same claim, which are edited in different files.

    A canonical pointing one way while the 301 points another is the failure
    mode worth a test: each is individually plausible and the pair is incoherent.
    """
    head = (SITE / "index.html").read_text()
    assert '<link rel="canonical" href="https://heykettle.com/" />' in head
    assert "heykettle.com" in REDIRECT
    assert "getkettle" not in head

    # privacy.html gets NO canonical, deliberately (DECISIONS 142). It is held to
    # a stricter standing law — it stands alone, with no <link> and no absolute
    # URL of any kind, so that the page a privacy-minded reader studies hardest
    # provably fetches nothing. A canonical link fetches nothing either, but the
    # law is written bluntly on purpose, and trading a plain guarantee for an SEO
    # hint is not a swap to make quietly. The 301 already stops that page being
    # reachable at two addresses.
    privacy = (SITE / "public" / "privacy.html").read_text()
    assert "<link" not in privacy
    assert "getkettle" not in privacy
