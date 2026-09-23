"""CMS reading (spec 021 §5, §6; acceptance §8.7, §8.8, §8.10)."""

from __future__ import annotations

import asyncio
import socket
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from care import cms
from care import copy as text
from care.app import RateLimiter, create_app
from conftest import FakeCms, call

CARE = Path(__file__).resolve().parent.parent


# --- §8.7 the cache --------------------------------------------------------------


def test_second_call_within_a_day_asks_cms_nothing(ask, fake, clock):
    ask("find_care", kind="nursing home", zip="27502")
    first = len(fake.requests)
    assert first == 2  # one page of NC, one metastore read
    clock.advance(hours=23, minutes=59)
    ask("find_care", kind="nursing home", zip="27502")
    assert len(fake.requests) == first
    # care_details reads both kinds within 50 miles (NC and SC): only the
    # three copies it did not already hold are new.
    ask("care_details", name="Pine Hollow", zip="27502")
    nc_homes = [
        r for r in fake.data_requests()
        if "4pq5-n9py" in r.url.path and r.url.params["conditions[0][value]"] == "NC"
    ]
    assert len(nc_homes) == 1, "the NC nursing-home copy was fetched again inside 24 hours"
    assert len(fake.requests) == first + 3 * 2


def test_a_day_later_it_reads_cms_again(ask, fake, clock):
    ask("find_care", kind="nursing home", zip="27502")
    clock.advance(hours=24)
    ask("find_care", kind="nursing home", zip="27502")
    assert len(fake.requests) == 4


def test_cms_down_with_a_warm_copy_answers_from_the_copy(ask, fake, clock):
    fresh = ask("find_care", kind="nursing home", zip="27502")
    clock.advance(hours=30)
    fake.down = True
    stale = ask("find_care", kind="nursing home", zip="27502")
    body, footer = fresh.rsplit("\n\n", 1)
    assert stale == body + "\n\n" + "\n".join(
        [
            "Medicare's site did not answer just now, so these figures are from our copy of "
            "September 23, 2026.",
            footer,
        ]
    )
    # One try, no retries inside a request.
    assert sum(r.url.path.endswith("/0") for r in fake.requests) == 2


def test_cms_down_with_no_copy_answers_cms_down(ask, fake):
    fake.down = True
    assert ask("find_care", kind="nursing home", zip="27502") == text.CMS_DOWN
    assert ask("care_details", name="Pine Hollow", zip="27502") == text.CMS_DOWN
    assert ask("compare_care", names=["a", "b"], zip="27502") == text.CMS_DOWN


def test_a_timeout_is_a_failure_like_any_other(fake, clock, centroids):
    class Slow(FakeCms):
        async def handle_async_request(self, request):
            raise httpx.ReadTimeout("slow", request=request)

    app = create_app(cms.make_client(Slow()), centroids, clock, RateLimiter())
    with TestClient(app) as c:
        assert call(c, "find_care", kind="nursing home", zip="27502") == text.CMS_DOWN


def test_one_state_down_with_no_copy_is_cms_down_not_half_an_answer(ask, fake):
    """Charlotte reads NC and SC. An answer that silently left out SC would
    look complete and be wrong."""
    ask("find_care", kind="nursing home", zip="27502")  # NC is warm, SC is not
    fake.down = True
    assert ask("find_care", kind="nursing home", zip="28273") == text.CMS_DOWN


def test_the_timeout_is_ten_seconds_a_page():
    client = cms.make_client()
    assert client.timeout == httpx.Timeout(10.0)


# --- §8.8 pagination -------------------------------------------------------------


def _synthetic(n: int) -> list[dict]:
    return [
        {"provider_name": f"HOME {i}", "state": "TX", "zip_code": "75201",
         "cms_certification_number_ccn": f"67{i:04d}"}
        for i in range(n)
    ]


def test_a_state_of_2300_rows_is_three_pages_of_1000(fake, clock):
    fake.extra[(cms.NURSING_HOMES, "TX")] = _synthetic(2300)
    data = cms.CmsData(cms.make_client(fake), clock)
    held, stale = asyncio.run(data.copy_for(cms.NURSING_HOMES, "TX"))
    assert not stale
    assert len(held.rows) == 2300
    pages = fake.data_requests()
    assert [int(r.url.params["offset"]) for r in pages] == [0, 1000, 2000]
    assert {r.url.params["limit"] for r in pages} == {"1000"}
    assert {r.url.host for r in fake.requests} == {"data.cms.gov"}
    assert pages[0].url.path == "/provider-data/api/1/datastore/query/4pq5-n9py/0"
    assert held.modified == "2026-08-01"


def test_an_exact_multiple_ends_on_an_empty_page(fake, clock):
    fake.extra[(cms.NURSING_HOMES, "TX")] = _synthetic(2000)
    data = cms.CmsData(cms.make_client(fake), clock)
    held, _ = asyncio.run(data.copy_for(cms.NURSING_HOMES, "TX"))
    assert len(held.rows) == 2000
    assert len(fake.data_requests()) == 3


def test_rows_keep_the_section_5_columns_and_nothing_else(fake, clock):
    """The datastore sends the CCN and eighty-odd other columns; the copy
    keeps §5's, so no id can reach an answer."""
    data = cms.CmsData(cms.make_client(fake), clock)
    nh, _ = asyncio.run(data.copy_for(cms.NURSING_HOMES, "NC"))
    hh, _ = asyncio.run(data.copy_for(cms.HOME_HEALTH, "NC"))
    assert all(set(r) == set(cms.NH_COLUMNS) for r in nh.rows)
    assert all(set(r) == set(cms.HH_COLUMNS) for r in hh.rows)
    assert len(cms.NH_COLUMNS) == 16 and len(cms.HH_COLUMNS) == 15


def test_no_answer_carries_a_ccn(ask, fake):
    ccns = {r["cms_certification_number_ccn"] for r in fake.rows("4pq5-n9py", "NC")}
    answers = [
        ask("find_care", kind="nursing home", zip="27502", miles=100),
        ask("find_care", kind="home health", zip="27502", miles=100),
        ask("compare_care", names=["Pine Hollow", "Apex Home Care"], zip="27502"),
    ]
    for answer in answers:
        assert not any(ccn in answer for ccn in ccns)
        assert "Holdco" not in answer


# --- §8.10 the outbound allowlist --------------------------------------------------


class Recording(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self.seen: list[httpx.URL] = []

    async def handle_async_request(self, request):
        self.seen.append(request.url)
        return httpx.Response(200, json={"results": []})


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/",
        "https://www2.census.gov/geo/",
        "https://data.cms.gov.evil.example/provider-data/",
        "https://evil.example/?h=data.cms.gov",
        "http://data.cms.gov/provider-data/api/1/",  # not https
        "https://api.kettle-api.fly.dev/",
    ],
)
def test_any_host_but_data_cms_gov_raises_before_the_socket(url, monkeypatch):
    opened: list[object] = []
    monkeypatch.setattr(socket.socket, "connect", lambda self, addr: opened.append(addr))
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: opened.append(a))
    inner = Recording()

    async def go(client: httpx.AsyncClient) -> None:
        async with client:
            await client.get(url)

    with pytest.raises(cms.OutboundRefused):
        asyncio.run(go(cms.make_client(inner)))
    assert inner.seen == []
    # The production client, with the real transport under it, too.
    with pytest.raises(cms.OutboundRefused):
        asyncio.run(go(cms.make_client()))
    assert opened == []


def test_data_cms_gov_is_let_through():
    inner = Recording()

    async def go() -> None:
        async with cms.make_client(inner) as client:
            await client.get(f"{cms.BASE}/metastore/schemas/dataset/items/{cms.NURSING_HOMES}")

    asyncio.run(go())
    assert [u.host for u in inner.seen] == ["data.cms.gov"]


def test_the_allowlist_is_the_only_way_out():
    """Only cms.py talks to the network, and only through make_client."""
    for path in CARE.glob("*.py"):
        source = path.read_text()
        if path.name == "cms.py":
            assert source.count("httpx.AsyncClient(") == 1
            assert "transport=AllowlistTransport(inner)" in source
            continue
        for word in ("import httpx", "urllib", "requests", "socket", "http.client"):
            assert word not in source, f"{word} in {path.name}"
    assert frozenset({"data.cms.gov"}) == cms.ALLOWED_HOSTS
