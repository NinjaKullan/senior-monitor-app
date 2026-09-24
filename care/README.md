# Care Compare by HeyKettle (kettle-care)

Spec `specs/021-care-compare.md`, ruled in DECISIONS 341 to 343; the build is
DECISIONS 344. A free, public, read-only MCP server at
`https://care.heykettle.com/mcp` that reads Medicare's own Care Compare
figures for nursing homes and home health agencies near a US ZIP code and
answers in sentences. It ranks nothing and recommends nothing, and every
answer ends with where the numbers came from, how old they are, and "call
the provider". Its public page is `heykettle.com/care` (in `site/`), and that
page is the link target for everything. The MCP address is never the link
target.

Amendment A (DECISIONS 347, built at 348) adds `https://care.heykettle.com/search`,
a plain form for people with no assistant. It gives the same sentences the
tools give, because it calls the same code, and the same limit applies:
a web search counts as a tool call. The page has no script, no cookie and
no image, and it sends no referrer.
Amendment B (DECISIONS 351) keeps result pages out of search engines: the
bare form may be indexed, every page with a query and every details page
answers `X-Robots-Tag: noindex` with the matching meta tag, and
`/robots.txt` disallows `/search/details`.

It is its own app. It shares no process, database, secret, table or code
with kettle-api. The MCP wiring is kettle-api's pattern, copied: the SDK's
`MCPServer` with one `instructions` line, read-only `ToolAnnotations`, and
stateless Streamable HTTP on an exact `/mcp` route.

## What it stores

Nothing, anywhere but this process's memory. CMS rows are cut to the §5
columns on arrival and held for 24 hours per (dataset, state). No database,
no disk, no account, no token. The log is one line per tool call, like
`find_care ok 8`: the tool, a status word (`ok`, `none`, `refused`,
`cms_down`) and a count. The log never holds an argument or an IP. The
uvicorn access log is off, and the SDK's and httpx's loggers are held at
WARNING, because a CMS URL carries the state.

## The files

| File | What it does |
|---|---|
| `app.py` | FastAPI; `Care`, the three answers that the tools and the web page share; the per-IP limit (60 an hour, `Fly-Client-IP`, shared by `/mcp` and `/search`); `/search`, `/search/details`, `/robots.txt`, `/`, and `/healthz` |
| `web.py` | The `/search` pages: one template string, one inlined stylesheet, every value escaped |
| `cms.py` | Fetch, page (1000 a page), cache, stale copy, `CmsDown`, and the `data.cms.gov`-only allowlist in the transport |
| `geo.py` | Centroids, great-circle miles, ZIP prefix to state, and which states a radius reaches |
| `answers.py` | CMS rows into the §4 sentences, as pure functions |
| `copy.py` | The §10 and A.5 strings, verbatim, and the §4 shapes |
| `data/zcta.csv` | Census 2020 ZCTA centroids: `zcta,lat,lon` |
| `scripts/make_zcta.py` | Builds `data/zcta.csv` from the Census Gazetteer |

## The centroid file

`data/zcta.csv` holds the Census 2020 national file, 33,144 rows, built on
2026-09-24 by `scripts/make_zcta.py` (6c97cfb). To rebuild it from a machine
that can reach census.gov:

```bash
python care/scripts/make_zcta.py          # downloads 2020_Gaz_zcta_national.zip
cd care && pytest
```

The Dockerfile refuses to build while `data/zcta.SAMPLE` exists. That marker
flagged the 200-row hand-placed sample the first build shipped with, and the
script deletes it.

## Running the tests

```bash
cd care
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest          # the entry point, not `python -m pytest`
.venv/bin/ruff check .
```

Use the `pytest` entry point. `python -m pytest` run from `care/` puts
`care/` itself on `sys.path`, where `copy.py` shadows the standard library's
`copy`, and pytest fails before it collects anything (DECISIONS 344). Add
`-P` if you must use `-m`.

CI runs the same two commands in its `care` job. The suite needs no
network. CMS answers come from `tests/fixtures/`, and an
autouse guard fails any test that opens a socket. The fixtures were built by
hand in the exact §5 column shape, because data.cms.gov was unreachable from
the build box.

## Deploy (founder, after the PM's review)

The app, its certificate and its DNS records exist (DECISIONS 346). A new
release needs only:

```bash
cd care && pytest && fly deploy
```

Keep it at one machine (`fly scale count 1`): a second machine doubles the
bill and splits the cache. There are no secrets to set.
