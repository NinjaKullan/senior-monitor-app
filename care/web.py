"""The web search page (spec 021 Amendment A): /search and /search/details.

A person with no assistant types a ZIP code and reads the same sentences the
tools give. This module only renders: the words come from `app.Care`, the
same methods the MCP tools call, so the text on the page is the tool's
answer byte for byte. Each line of the answer is a paragraph, and each named
provider's name links to its details.

Plain HTML from one template string, with one inlined stylesheet and no
script, cookie, image, font file or request to anywhere. Every value is
escaped on the way in. The form is GET, so a result has an address someone
can share, and the page sends no referrer, so that address (it carries the
ZIP) never leaves in a Referer header.
"""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
from urllib.parse import urlencode

from care import answers as a
from care import copy as text

MILES_CHOICES = (5, 10, 15, 25, 50)
RATING_CHOICES = (3, 4, 5)
KIND_CHOICES = (("nursing home", text.SEARCH_KIND_NURSING), ("home health", text.SEARCH_KIND_HH))

#: Sent with every page (Amendment A.1, A.6.4): nothing may load, nothing may
#: be framed, the form posts only here, and the address never leaves.
HEADERS = {
    "Cache-Control": "no-store",
    "Content-Security-Policy": (
        "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; "
        "base-uri 'none'; frame-ancestors 'none'"
    ),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}
#: Amendment B.2 (DECISIONS 349): the bare form may be indexed; every page
#: with a query, and every details page, is not. Thousands of thin result
#: pages would cost the site's standing and spend crawlers' hourly limits.
NOINDEX_HEADERS = {**HEADERS, "X-Robots-Tag": "noindex"}
NOINDEX_META = '<meta name="robots" content="noindex">\n'

#: Amendment B.2, byte for byte. /mcp needs nothing: it answers JSON.
ROBOTS_TXT = "User-agent: *\nDisallow: /search/details\nAllow: /\n"

# The site's locked palette (site/src/tokens.css), as /care uses it. Sizes are
# rem so the page grows with the reader's font size; every control is at
# least 2.75rem (44px at the default size) tall.
PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
{robots}<title>{title}</title>
<style>
body {{ margin: 0 auto; padding: 2.5rem 1rem 4rem; max-width: 42rem; background: #f6f2ec;
  color: #403c36; font: 1rem/1.5 system-ui, sans-serif; }}
a {{ color: inherit; text-underline-offset: 0.2em; }}
h1 {{ font: 500 2rem/1.2 "Newsreader", Georgia, serif; letter-spacing: -0.02em; margin: 0; }}
h2 {{ font: 500 1.375rem/1.3 "Newsreader", Georgia, serif; margin: 2.5rem 0 0; }}
.lede, .answer p {{ font: 1.1875rem/1.6 "Newsreader", Georgia, serif; max-width: 66ch; }}
.lede {{ margin: 0.75rem 0 0; }}
form {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
  gap: 1rem; margin: 2rem 0 0; }}
label {{ display: block; font-weight: 600; margin: 0 0 0.375rem; }}
select, input, button {{ box-sizing: border-box; width: 100%; min-height: 2.75rem;
  font: inherit; color: inherit; border-radius: 8px; }}
select, input {{ padding: 0.5rem 0.75rem; border: 1px solid #6c665d; background: #fffdf9; }}
button {{ align-self: end; padding: 0.5rem 1.25rem; border: 1px solid #403c36;
  background: #403c36; color: #f6f2ec; font-weight: 600; cursor: pointer; }}
button:hover {{ background: #2b2824; }}
select:focus-visible, input:focus-visible, button:focus-visible, a:focus-visible {{
  outline: 2px solid #403c36; outline-offset: 2px; }}
.answer {{ margin: 0.5rem 0 0; }}
.answer .block {{ margin: 1.25rem 0 0; }}
.answer p {{ margin: 0 0 0.75rem; }}
.assistant {{ margin: 2rem 0 0; padding: 1rem 0 0; border-top: 1px solid rgba(64, 60, 54, 0.2); }}
code {{ font: 600 1rem/1.4 ui-monospace, Menlo, Consolas, monospace; overflow-wrap: anywhere; }}
.back {{ margin: 1.5rem 0 0; }}
</style>
</head>
<body>
<main>
<h1>{title}</h1>
<p class="lede">{lede}</p>
{body}
</main>
</body>
</html>
"""


def _option(value: str, label: str, chosen: str) -> str:
    selected = " selected" if value == chosen else ""
    return f'<option value="{escape(value)}"{selected}>{escape(label)}</option>'


def _form(query: Mapping[str, str]) -> str:
    kind = query.get("kind", "nursing home")
    miles = query.get("miles", "15")
    rating = query.get("min_rating", "")
    kinds = "".join(_option(v, label, kind) for v, label in KIND_CHOICES)
    miles_options = "".join(
        _option(str(n), text.SEARCH_MILES_UNIT.format(n=n), miles) for n in MILES_CHOICES
    )
    ratings = _option("", text.SEARCH_RATING_ANY, rating) + "".join(
        _option(str(n), text.SEARCH_RATING_N.format(n=n), rating) for n in RATING_CHOICES
    )
    return (
        '<form method="get" action="/search">'
        f'<div><label for="kind">{escape(text.SEARCH_LABEL_KIND)}</label>'
        f'<select id="kind" name="kind">{kinds}</select></div>'
        f'<div><label for="zip">{escape(text.SEARCH_LABEL_ZIP)}</label>'
        '<input id="zip" name="zip" type="text" inputmode="numeric" autocomplete="postal-code"'
        f' maxlength="5" value="{escape(query.get("zip", ""))}"></div>'
        f'<div><label for="miles">{escape(text.SEARCH_LABEL_MILES)}</label>'
        f'<select id="miles" name="miles">{miles_options}</select></div>'
        f'<div><label for="min_rating">{escape(text.SEARCH_LABEL_RATING)}</label>'
        f'<select id="min_rating" name="min_rating">{ratings}</select></div>'
        f'<button type="submit">{escape(text.SEARCH_BUTTON)}</button>'
        "</form>"
    )


def search_query(query: Mapping[str, str]) -> dict[str, str]:
    """The four search fields, as given: what the details link carries and
    SEARCH_BACK returns to."""
    return {k: query[k] for k in ("kind", "zip", "miles", "min_rating") if k in query}


def _answer(said_text: str, links: list[tuple[str, str]]) -> str:
    """The tool's answer: a block per paragraph, a <p> per line, and each
    (name, href) in `links` linked at its first appearance, in order."""
    pending = list(links)
    blocks = []
    for block in said_text.split("\n\n"):
        lines = []
        for line in block.split("\n"):
            html = escape(line, quote=False)
            if pending:
                name, href = pending[0]
                marked = escape(name, quote=False)
                if marked in html:
                    html = html.replace(marked, f'<a href="{escape(href)}">{marked}</a>', 1)
                    pending.pop(0)
            lines.append(f"<p>{html}</p>")
        blocks.append(f'<div class="block">{"".join(lines)}</div>')
    return f'<div class="answer">{"".join(blocks)}</div>'


def _section(zip_value: str, inner: str) -> str:
    """The results, headed SEARCH_RESULTS_HEAD when the ZIP is five digits
    (a heading of "Near abc" over ZIP_UNKNOWN would repeat the mistake)."""
    zip5 = zip_value.strip()
    if len(zip5) == 5 and zip5.isdigit():
        head = escape(text.SEARCH_RESULTS_HEAD.format(zip=zip5))
        return f'<section aria-labelledby="results"><h2 id="results">{head}</h2>{inner}</section>'
    return f"<section>{inner}</section>"


def _assistant() -> str:
    return (
        f'<p class="assistant">{escape(text.SEARCH_ASSISTANT_LINE)} '
        f"<code>{escape(text.CONNECTOR_ADDRESS)}</code> "
        f'<a href="{escape(text.SITE_CARE_URL)}">{escape(text.SEARCH_ASSISTANT_LINK)}</a></p>'
    )


def _page(body: str, noindex: bool) -> str:
    return PAGE.format(
        title=escape(text.SEARCH_TITLE),
        lede=escape(text.SEARCH_LEDE),
        body=body,
        robots=NOINDEX_META if noindex else "",
    )


def render_search(
    query: Mapping[str, str],
    said_text: str | None,
    shown: tuple[a.Placed, ...] = (),
    noindex: bool = True,
) -> str:
    """/search: the form, and under it the answer when a search ran.
    `noindex` is False only for the bare form (Amendment B.2)."""
    body = _form(query)
    if said_text is not None:
        carried = search_query(query)
        zip_value = query.get("zip", "").strip()
        links = [
            (p.name, "/search/details?" + urlencode({"name": p.name, **carried, "zip": zip_value}))
            for p in shown
            # care_details matches within 50 miles; a name beyond that
            # (NEAREST_BEYOND reaches 100) would link to a NO_MATCH.
            if p.miles <= a.MATCH_MILES
        ]
        body += _section(zip_value, _answer(said_text, links) + _assistant())
    return _page(body, noindex)


def render_details(query: Mapping[str, str], said_text: str) -> str:
    """/search/details: care_details's answer and the way back."""
    back = "/search?" + urlencode(search_query(query))
    body = f'<p class="back"><a href="{escape(back)}">{escape(text.SEARCH_BACK)}</a></p>'
    body += _section(query.get("zip", ""), _answer(said_text, []) + _assistant())
    return _page(body, noindex=True)
