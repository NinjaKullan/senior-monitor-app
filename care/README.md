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
| `app.py` | FastAPI plus the three tools, the per-IP limit (60 tool calls an hour, `Fly-Client-IP`), `/`, and `/healthz` |
| `cms.py` | Fetch, page (1000 a page), cache, stale copy, `CmsDown`, and the `data.cms.gov`-only allowlist in the transport |
| `geo.py` | Centroids, great-circle miles, ZIP prefix to state, and which states a radius reaches |
| `answers.py` | CMS rows into the §4 sentences, as pure functions |
| `copy.py` | The §10 strings, verbatim, and the §4 shapes |
| `data/zcta.csv` | Census 2020 ZCTA centroids: `zcta,lat,lon` |
| `scripts/make_zcta.py` | Builds `data/zcta.csv` from the Census Gazetteer |

## The centroid file: run the script once before the first deploy

The checked-in `data/zcta.csv` is a 200-row sample, hand-placed near real ZIP
centroids, because census.gov was unreachable from the build box.
`data/zcta.SAMPLE` says so, and the Dockerfile refuses to build while that
marker exists. From a machine that can reach census.gov:

```bash
python care/scripts/make_zcta.py          # downloads 2020_Gaz_zcta_national.zip
# or, with the file already downloaded:
python care/scripts/make_zcta.py ~/Downloads/2020_Gaz_zcta_national.zip
cd care && pytest                         # the shipped-file test now expects ~33,000 rows
```

The script writes the national file (about 33,000 rows) and deletes the
marker. Commit both changes.

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

The suite needs no network. CMS answers come from `tests/fixtures/`, and an
autouse guard fails any test that opens a socket. The fixtures were built by
hand in the exact §5 column shape, because data.cms.gov was unreachable from
the build box.

## Deploy (founder, after the PM's review)

```bash
python care/scripts/make_zcta.py          # once, see above
cd care
fly launch --no-deploy --copy-config --name kettle-care
fly deploy
```

Then add a `care` CNAME on heykettle.com in Cloudflare, proxied, pointing to
`kettle-care.fly.dev`, and run `fly certs add care.heykettle.com`. There are
no secrets to set.
