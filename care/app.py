"""Care Compare by HeyKettle: a free, public, read-only MCP server (spec 021).

Its own small app, `kettle-care`. It shares no process, database, secret or
code with kettle-api; the MCP wiring is copied from kettle-api's pattern
(the official SDK's `MCPServer` with one `instructions` line, read-only
`ToolAnnotations`, stateless Streamable HTTP on an exact `/mcp` route), not
imported from it.

No accounts and no OAuth: the server advertises no authorization metadata
and a client that asks for any gets a 404. The one thing between the
internet and the tools is a per-IP limit of 60 tool calls an hour, in
memory, and a refusal is an ordinary tool answer (RATE_LIMITED).

Nothing about a question is logged. One line per tool call: the tool, a
status word (ok, none, refused, cms_down) and a count. Never an argument,
never the IP; the uvicorn access log is off (Dockerfile), and the SDK's and
httpx's own loggers are held at WARNING so a request URL, which carries the
state, is never written either.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.routing import Route

from care import answers as a
from care import cms, web
from care import copy as text
from care.geo import Centroids

log = logging.getLogger("care")

#: §6: every tool reads and nothing else, and reads only CMS.
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
RATE_PER_HOUR = 60
HOUR = 3600.0

#: The caller's address for the length of one /mcp request (set by the route).
CLIENT_IP: ContextVar[str] = ContextVar("care_client_ip", default="unknown")


class RateLimiter:
    """Tool calls per IP in a sliding hour, in process memory (§6)."""

    def __init__(self, limit: int = RATE_PER_HOUR, clock: Callable[[], float] = time.monotonic):
        self.limit = limit
        self.clock = clock
        self.calls: dict[str, deque[float]] = {}

    def allow(self, ip: str) -> bool:
        now = self.clock()
        for key in [k for k, q in self.calls.items() if q and now - q[-1] >= HOUR]:
            del self.calls[key]
        window = self.calls.setdefault(ip, deque())
        while window and now - window[0] >= HOUR:
            window.popleft()
        if len(window) >= self.limit:
            return False
        window.append(now)
        return True


def _said(tool: str, status: str, count: int) -> None:
    log.info("%s %s %d", tool, status, count)


def _footer(read: cms.Read, shown: list[a.Placed]) -> list[str]:
    """Every answer that read CMS ends with the source and the call (§3)."""
    lines = []
    if read.stale_since is not None:
        lines.append(text.STALE_LINE.format(date=a.date_words(read.stale_since.date().isoformat())))
    as_of = read.as_of({p.row["_dataset"] for p in shown})
    lines.append(text.SOURCE_LINE.format(date=a.date_words(as_of)))
    lines.append(text.CALL_LINE)
    return lines


def _answer(blocks: list[str], read: cms.Read, shown: list[a.Placed]) -> str:
    return "\n\n".join([*blocks, "\n".join(_footer(read, shown))])


def _zip(value: object, centroids: Centroids) -> tuple[str, tuple[float, float]] | None:
    zip5 = str(value if value is not None else "").strip()
    if len(zip5) != 5 or not zip5.isdigit():
        return None
    point = centroids.point(zip5)
    return (zip5, point) if point is not None else None


def _clamp(value: float | None, low: float, high: float, default: float | None) -> float | None:
    if value is None:
        return default
    return min(max(float(value), low), high)


@dataclass(frozen=True)
class Said:
    """One answer: the text the tool returns, and the providers it names,
    nearest first, so the web page can link each name (Amendment A.3)."""

    text: str
    shown: tuple[a.Placed, ...] = ()


class Care:
    """The three answers, shared by the MCP tools and the web page.

    One implementation, so /search says byte for byte what find_care says,
    and one limiter, so a web search and a tool call count against the same
    60 an hour (Amendment A.4). `label` is the word the log line starts
    with: the tool's name, or `search` on the web."""

    def __init__(self, data: cms.CmsData, centroids: Centroids, limiter: RateLimiter) -> None:
        self.data = data
        self.centroids = centroids
        self.limiter = limiter

    async def _read(self, datasets: list[str], zip5: str, miles: float) -> cms.Read:
        return await self.data.read(datasets, self.centroids.states_within(zip5, miles))

    async def find_care(
        self,
        label: str,
        ip: str,
        kind: str,
        zip: str,
        miles: float | None = None,
        min_rating: float | None = None,
    ) -> Said:
        if not self.limiter.allow(ip):
            _said(label, "refused", 0)
            return Said(text.RATE_LIMITED)
        chosen = a.parse_kind(kind)
        if chosen is None:
            _said(label, "refused", 0)
            return Said(text.KIND_UNKNOWN)
        asked = _zip(zip, self.centroids)
        if asked is None:
            _said(label, "refused", 0)
            return Said(text.ZIP_UNKNOWN)
        zip5, here = asked
        radius = _clamp(miles, 1, a.MAX_MILES, a.DEFAULT_MILES)
        floor = _clamp(min_rating, 1, 5, None)
        assert radius is not None
        try:
            got = await self._read([a.DATASET[chosen]], zip5, radius)
        except cms.CmsDown:
            _said(label, "cms_down", 0)
            return Said(text.CMS_DOWN)

        def keep(p: a.Placed) -> bool:
            return floor is None or (p.score is not None and p.score >= floor)

        placed = [p for p in a.place(got.rows, here, self.centroids) if keep(p)]
        within = [p for p in placed if p.miles <= radius]
        radius_words = f"{radius:g}"
        if within:
            listed = within[: a.LIST_CAP]
            blocks = ["\n".join(a.list_sentence(p) for p in listed)]
            if len(within) > a.LIST_CAP:
                blocks.append(
                    a.one_mile(
                        text.MORE_LINE.format(more=len(within) - a.LIST_CAP, miles=radius_words)
                    )
                )
            _said(label, "ok", len(listed))
            return Said(_answer(blocks, got, listed), tuple(listed))

        none = a.one_mile(
            text.NONE_NEAR.format(kind_plural=a.PLURAL[chosen], miles=radius_words, zip=zip5)
        )
        blocks = [none]
        shown: list[a.Placed] = []
        if radius < a.MAX_MILES:
            try:
                wider = await self._read([a.DATASET[chosen]], zip5, a.MAX_MILES)
            except cms.CmsDown:
                _said(label, "cms_down", 0)
                return Said(text.CMS_DOWN)
            beyond = [
                p
                for p in a.place(wider.rows, here, self.centroids)
                if keep(p) and p.miles <= a.MAX_MILES
            ]
            if beyond:
                nearest = beyond[0]
                blocks = [
                    none
                    + " "
                    + a.one_mile(
                        text.NEAREST_BEYOND.format(
                            name=nearest.name, city=nearest.city, miles=int(nearest.miles + 0.5)
                        )
                    )
                ]
                got, shown = wider, [nearest]
        _said(label, "none", 0)
        return Said(_answer(blocks, got, shown), tuple(shown))

    async def _resolve_all(
        self, names: list[str], zip5: str, here: tuple[float, float]
    ) -> tuple[list[a.Placed | None], list[a.Placed], cms.Read]:
        got = await self._read([cms.NURSING_HOMES, cms.HOME_HEALTH], zip5, a.MATCH_MILES)
        placed = a.place(got.rows, here, self.centroids)
        return [a.resolve(n, placed) for n in names], placed, got

    @staticmethod
    def _no_match(asked: str, zip5: str, placed: list[a.Placed]) -> str:
        return text.NO_MATCH.format(
            zip=zip5, asked=" ".join(asked.split()), names=a.nearest_names(placed)
        )

    async def care_details(self, label: str, ip: str, name: str, zip: str) -> Said:
        if not self.limiter.allow(ip):
            _said(label, "refused", 0)
            return Said(text.RATE_LIMITED)
        asked = _zip(zip, self.centroids)
        if asked is None:
            _said(label, "refused", 0)
            return Said(text.ZIP_UNKNOWN)
        zip5, here = asked
        try:
            (found,), placed, got = await self._resolve_all([name], zip5, here)
        except cms.CmsDown:
            _said(label, "cms_down", 0)
            return Said(text.CMS_DOWN)
        if found is None:
            _said(label, "none", 0)
            return Said(_answer([self._no_match(name, zip5, placed)], got, []))
        _said(label, "ok", 1)
        return Said(_answer(["\n".join(a.details(found, zip5))], got, [found]), (found,))

    async def compare_care(self, label: str, ip: str, names: list[str], zip: str) -> Said:
        if not self.limiter.allow(ip):
            _said(label, "refused", 0)
            return Said(text.RATE_LIMITED)
        asked_names = [n for n in names if str(n).strip()][:4]
        if len(asked_names) < 2:
            _said(label, "refused", 0)
            return Said(text.COMPARE_NEED_TWO)
        asked = _zip(zip, self.centroids)
        if asked is None:
            _said(label, "refused", 0)
            return Said(text.ZIP_UNKNOWN)
        zip5, here = asked
        try:
            found, placed, got = await self._resolve_all(asked_names, zip5, here)
        except cms.CmsDown:
            _said(label, "cms_down", 0)
            return Said(text.CMS_DOWN)
        distinct = {id(p.row) for p in found if p is not None}
        if len(distinct) < 2:
            _said(label, "refused", len(distinct))
            return Said(text.COMPARE_NEED_TWO)
        blocks = []
        seen: set[int] = set()
        for index, p in enumerate(found):
            if p is None:
                blocks.append(self._no_match(asked_names[index], zip5, placed))
            elif id(p.row) not in seen:
                seen.add(id(p.row))
                blocks.append("\n".join(a.details(p, zip5)))
        blocks.append(text.COMPARE_CLOSE)
        _said(label, "ok", len(distinct))
        named = [p for p in found if p is not None]
        return Said(_answer(blocks, got, named), tuple(named))


def build_server(care: Care) -> MCPServer:
    """The MCP server: three read-only tools over CMS's own figures."""
    server = MCPServer(text.SERVER_NAME, instructions=text.SERVER_INSTRUCTIONS)

    @server.tool(name="find_care", description=text.TOOL_FIND, annotations=READ_ONLY)
    async def find_care(
        kind: str, zip: str, miles: float | None = None, min_rating: float | None = None
    ) -> str:
        said = await care.find_care("find_care", CLIENT_IP.get(), kind, zip, miles, min_rating)
        return said.text

    @server.tool(name="care_details", description=text.TOOL_DETAILS, annotations=READ_ONLY)
    async def care_details(name: str, zip: str) -> str:
        return (await care.care_details("care_details", CLIENT_IP.get(), name, zip)).text

    @server.tool(name="compare_care", description=text.TOOL_COMPARE, annotations=READ_ONLY)
    async def compare_care(names: list[str], zip: str) -> str:
        return (await care.compare_care("compare_care", CLIENT_IP.get(), names, zip)).text

    return server


def _quiet_loggers() -> None:
    """The SDK and httpx log request lines that can carry an argument or a
    CMS URL with the state in it, and httpx2 (the SDK's) logs a /search URL
    with the ZIP in it. None of that is ours to write (§6). Our own
    lines go to stderr at INFO; basicConfig is a no-op when something (a
    test's log capture) already holds the root logger."""
    for name in ("mcp", "httpx", "httpcore", "httpx2", "httpcore2", "uvicorn.access"):
        logging.getLogger(name).setLevel(logging.WARNING)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log.setLevel(logging.INFO)


def create_app(
    client: Any = None,
    centroids: Centroids | None = None,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    limiter: RateLimiter | None = None,
) -> FastAPI:
    """The app. Tests pass a client over recorded fixtures, their own
    centroids, a clock and a limiter; production passes nothing."""
    _quiet_loggers()
    http = client or cms.make_client()
    data = cms.CmsData(http, clock)
    points = centroids or Centroids.load()
    care = Care(data, points, limiter or RateLimiter())
    mcp_server = build_server(care)
    mcp_asgi = mcp_server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        # As kettle-api: host checks belong to Fly's edge and the public URL.
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        host="0.0.0.0",  # noqa: S104 - the SDK's flag for "not loopback-only"
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            async with mcp_server.session_manager.run():
                yield
        finally:
            await http.aclose()

    app = FastAPI(
        title="Care Compare", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan
    )
    app.state.cms = data

    class Mcp:
        """An exact route rather than a Mount (kettle-api, DECISIONS 286): a
        Mount answers /mcp with a 307 first. It puts the caller's address in
        CLIENT_IP for the rate limit and nowhere else."""

        async def __call__(self, scope, receive, send):  # type: ignore[no-untyped-def]
            headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
            client_host = (scope.get("client") or ("unknown", 0))[0]
            token = CLIENT_IP.set(headers.get("fly-client-ip", "").strip() or client_host)
            try:
                await mcp_asgi(scope, receive, send)
            finally:
                CLIENT_IP.reset(token)

    app.router.routes.append(Route("/mcp", endpoint=Mcp(), methods=["GET", "POST", "DELETE"]))

    def caller(request: Request) -> str:
        """The address the limit counts, as /mcp reads it."""
        forwarded = request.headers.get("fly-client-ip", "").strip()
        return forwarded or (request.client.host if request.client else "unknown")

    def number(value: str | None) -> float | None:
        try:
            return float(value) if value not in (None, "") else None
        except ValueError:
            return None

    @app.get("/search")
    async def search(request: Request) -> HTMLResponse:
        """Amendment A: the form, and find_care's answer under it once a ZIP
        is given. No ZIP in the query is the empty form and reads nothing."""
        query = dict(request.query_params)
        if "zip" not in query:
            return HTMLResponse(web.render_search(query, None), headers=web.HEADERS)
        said = await care.find_care(
            "search",
            caller(request),
            query.get("kind", "nursing home"),
            query["zip"],
            number(query.get("miles")),
            number(query.get("min_rating")),
        )
        return HTMLResponse(web.render_search(query, said.text, said.shown), headers=web.HEADERS)

    @app.get("/search/details", response_model=None)
    async def search_details(request: Request) -> HTMLResponse | RedirectResponse:
        """care_details's answer for one name near one ZIP, and the way back."""
        query = dict(request.query_params)
        if not query.get("name", "").strip() or "zip" not in query:
            back = "/search?" + web.urlencode(web.search_query(query))
            return RedirectResponse(back, status_code=303, headers=web.HEADERS)
        said = await care.care_details(
            "search_details", caller(request), query["name"], query["zip"]
        )
        return HTMLResponse(web.render_details(query, said.text), headers=web.HEADERS)

    @app.get("/", response_class=PlainTextResponse)
    async def root() -> str:
        return "ok\n"

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        """Liveness for Fly. Reads nothing."""
        return JSONResponse({"ok": True})

    return app
