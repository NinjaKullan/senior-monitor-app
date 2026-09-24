"""Robots on the care host (spec 021 Amendment B.2; acceptance B.4.2).

The bare search form may be indexed. Every page with a query, and every
details page, answers `X-Robots-Tag: noindex` and carries the meta tag, and
/robots.txt keeps crawlers off the details pages (DECISIONS 349).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from care import cms
from care.app import RateLimiter, create_app

META = '<meta name="robots" content="noindex">'
FULL = {"kind": "nursing home", "zip": "27502", "miles": "15", "min_rating": ""}


def assert_noindex(response) -> None:
    assert response.headers.get("x-robots-tag") == "noindex", response.url
    if response.status_code == 200:
        assert response.text.count(META) == 1, response.url
        head = response.text.split("</head>")[0]
        assert META in head


def assert_indexable(response) -> None:
    assert "x-robots-tag" not in {k.lower() for k in response.headers}, response.url
    assert "noindex" not in response.text


def test_the_bare_form_is_indexable(client, fake):
    assert_indexable(client.get("/search"))
    assert_indexable(client.get("/search?"))  # an empty query is no query
    assert fake.requests == []


def test_any_query_is_noindex(client):
    for query in (
        FULL,
        {"kind": "nursing home"},  # the form again, but with a query
        {"zip": ""},
        {**FULL, "zip": "abc"},  # ZIP_UNKNOWN
        {**FULL, "zip": "27936"},  # NONE_NEAR
        {**FULL, "kind": "home health", "min_rating": "4"},
        {"utm_source": "x"},  # a query that is not a search field still counts
    ):
        assert_noindex(client.get("/search", params=query))


def test_every_details_page_is_noindex(client):
    assert_noindex(client.get("/search/details", params={**FULL, "name": "Apex Ridge"}))
    assert_noindex(client.get("/search/details", params={**FULL, "name": "Sunny Acres"}))
    redirect = client.get("/search/details", params=FULL, follow_redirects=False)
    assert redirect.status_code == 303
    assert_noindex(redirect)


def test_refusals_are_noindex_too(fake, clock, centroids):
    app = create_app(cms.make_client(fake), centroids, clock, RateLimiter(limit=1))
    with TestClient(app) as c:
        c.get("/search", params=FULL)
        assert_noindex(c.get("/search", params=FULL))  # RATE_LIMITED
    fake.down = True
    app = create_app(cms.make_client(fake), centroids, clock, RateLimiter())
    with TestClient(app) as c:
        assert_noindex(c.get("/search", params=FULL))  # CMS_DOWN


def test_robots_txt_is_b2_byte_for_byte(client, fake):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert response.content == b"User-agent: *\nDisallow: /search/details\nAllow: /\n"
    assert response.headers["content-type"].startswith("text/plain")
    assert fake.requests == []


def test_nothing_else_changes(client):
    assert_indexable(client.get("/"))
    assert_indexable(client.get("/healthz"))
