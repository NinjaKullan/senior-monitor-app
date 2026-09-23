"""Reading CMS's Care Compare data: fetch, page, cache (spec 021 §5).

One whole state at a time, from the provider-data datastore, 1000 rows a page
until a page comes back short. The dataset's `modified` date is read from the
metastore in the same fetch and cached with the rows, because every answer
says how old its figures are.

The cache is this process's memory and nothing else: per (dataset, state),
24 hours. A miss fetches. A CMS failure with a copy in hand serves the copy
and says so (STALE_LINE); with no copy it is `CmsDown`, and the tool answers
CMS_DOWN. Ten seconds a page, no retries inside a request.

Rows are cut to the §5 columns the moment they arrive. The datastore hands
back eighty-odd columns, the CCN among them; the ones no answer uses are not
kept, so they cannot leak into one.

The outbound allowlist is enforced at the transport, under the client, so a
request to any other host raises before a socket is opened (§6, §8.10: the
F1 lesson on day one). Redirects are requests too and meet the same check.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

CMS_HOST = "data.cms.gov"
ALLOWED_HOSTS = frozenset({CMS_HOST})
BASE = f"https://{CMS_HOST}/provider-data/api/1"

NURSING_HOMES = "4pq5-n9py"
HOME_HEALTH = "6jpm-sxkc"

NH_COLUMNS = (
    "provider_name", "provider_address", "citytown", "state", "zip_code",
    "telephone_number", "ownership_type", "number_of_certified_beds",
    "overall_rating", "health_inspection_rating", "staffing_rating", "qm_rating",
    "abuse_icon", "special_focus_status", "latitude", "longitude",
)
HH_SERVICE_COLUMNS = (
    "offers_nursing_care_services",
    "offers_physical_therapy_services",
    "offers_occupational_therapy_services",
    "offers_speech_pathology_services",
    "offers_medical_social_services",
    "offers_home_health_aide_services",
)
HH_COLUMNS = (
    "provider_name", "address", "citytown", "state", "zip_code", "telephone_number",
    "type_of_ownership", "quality_of_patient_care_star_rating", "certification_date",
    *HH_SERVICE_COLUMNS,
)
COLUMNS = {NURSING_HOMES: NH_COLUMNS, HOME_HEALTH: HH_COLUMNS}

PAGE = 1000
TIMEOUT_SECONDS = 10.0
TTL = timedelta(hours=24)


class OutboundRefused(RuntimeError):
    """A request to a host outside ALLOWED_HOSTS. Raised before any socket."""


class CmsDown(RuntimeError):
    """CMS did not answer and there is no copy to answer from."""


class AllowlistTransport(httpx.AsyncBaseTransport):
    """Refuses every host but data.cms.gov, then hands the request on."""

    def __init__(self, inner: httpx.AsyncBaseTransport | None = None) -> None:
        self.inner = inner or httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if request.url.scheme != "https" or request.url.host not in ALLOWED_HOSTS:
            raise OutboundRefused(f"outbound request refused: {request.url.host}")
        return await self.inner.handle_async_request(request)

    async def aclose(self) -> None:
        await self.inner.aclose()


def make_client(inner: httpx.AsyncBaseTransport | None = None) -> httpx.AsyncClient:
    """The one HTTP client this app has. `inner` is for tests (a recorded
    fixture transport); the allowlist wraps it either way."""
    return httpx.AsyncClient(
        transport=AllowlistTransport(inner),
        timeout=httpx.Timeout(TIMEOUT_SECONDS),
        follow_redirects=False,
    )


@dataclass(frozen=True)
class Copy:
    """One (dataset, state): its rows, CMS's `modified` date, when we read it."""

    rows: tuple[dict[str, Any], ...]
    modified: str
    fetched_at: datetime


@dataclass(frozen=True)
class Read:
    """What a tool gets back: the rows, and whether any of them is stale."""

    rows: list[dict[str, Any]]
    modified: dict[str, str]  # per dataset, the oldest `modified` among its copies
    stale_since: datetime | None  # the oldest stale copy's fetch time, if any

    def as_of(self, datasets: set[str] | None = None) -> str:
        """The date an answer carries: the oldest `modified` of the datasets
        its providers came from, or of everything read when it names none."""
        chosen = [m for d, m in self.modified.items() if not datasets or d in datasets]
        return min(chosen or self.modified.values())


def _project(row: dict[str, Any], columns: tuple[str, ...]) -> dict[str, Any]:
    return {column: row.get(column) for column in columns}


class CmsData:
    """The per-process cache in front of CMS."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.client = client
        self.clock = clock
        self.cache: dict[tuple[str, str], Copy] = {}
        self._locks: dict[tuple[str, str], asyncio.Lock] = {}

    async def _fetch(self, dataset: str, state: str) -> Copy:
        rows: list[dict[str, Any]] = []
        offset = 0
        while True:
            response = await self.client.get(
                f"{BASE}/datastore/query/{dataset}/0",
                params={
                    "limit": PAGE,
                    "offset": offset,
                    "conditions[0][property]": "state",
                    "conditions[0][value]": state,
                },
            )
            response.raise_for_status()
            page = response.json()["results"]
            rows.extend(_project(row, COLUMNS[dataset]) for row in page)
            if len(page) < PAGE:
                break
            offset += PAGE
        meta = await self.client.get(f"{BASE}/metastore/schemas/dataset/items/{dataset}")
        meta.raise_for_status()
        modified = str(meta.json()["modified"])
        return Copy(tuple(rows), modified, self.clock())

    async def copy_for(self, dataset: str, state: str) -> tuple[Copy, bool]:
        """The copy for one (dataset, state), and whether it is stale."""
        key = (dataset, state)
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            held = self.cache.get(key)
            if held is not None and self.clock() - held.fetched_at < TTL:
                return held, False
            try:
                fresh = await self._fetch(dataset, state)
            except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:
                if held is not None:
                    return held, True
                raise CmsDown(dataset) from error
            self.cache[key] = fresh
            return fresh, False

    async def read(self, datasets: list[str], states: list[str]) -> Read:
        """Every row for these datasets across these states. Any one of them
        with no copy to fall back on makes the whole read `CmsDown`: an answer
        that silently left out the state across the line would be a wrong
        answer that looks complete."""
        rows: list[dict[str, Any]] = []
        modified: dict[str, str] = {}
        stale: list[datetime] = []
        for dataset in datasets:
            for state in states:
                copy, is_stale = await self.copy_for(dataset, state)
                rows.extend({**row, "_dataset": dataset} for row in copy.rows)
                modified[dataset] = min(modified.get(dataset, copy.modified), copy.modified)
                if is_stale:
                    stale.append(copy.fetched_at)
        return Read(rows, modified, min(stale) if stale else None)
