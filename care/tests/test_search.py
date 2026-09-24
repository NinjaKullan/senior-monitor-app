"""The web search page (spec 021 Amendment A; acceptance A.6.1 to A.6.6)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient

from care import cms
from care import copy as text
from care.answers import title
from care.app import RateLimiter, create_app
from conftest import FIXTURES, call

SITE_BANS = Path(__file__).resolve().parents[2] / "site" / "src" / "tests" / "copyBans.ts"
FULL = {"kind": "nursing home", "zip": "27502", "miles": "15", "min_rating": ""}


@dataclass
class Answer:
    """The answer back out of the page: a block per div.block, a line per
    <p>, and every link inside it. The markup is web.py's own and regular."""

    blocks: list[list[str]]
    links: list[tuple[str, str]]

    def text(self) -> str:
        return "\n\n".join("\n".join(lines) for lines in self.blocks)


def _plain(html: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", html))


def read_answer(page: str) -> Answer:
    found = re.search(r'<div class="answer">(.*?)</div></div><p class="assistant">', page, re.S)
    assert found, "no answer on the page"
    inner = found.group(1) + "</div>"
    blocks = [
        [_plain(line) for line in re.findall(r"<p>(.*?)</p>", block, re.S)]
        for block in re.findall(r'<div class="block">(.*?)</div>', inner, re.S)
    ]
    links = [(_plain(t), unescape(h)) for h, t in re.findall(r'<a href="([^"]+)">(.*?)</a>', inner)]
    return Answer(blocks, links)


def search(client: TestClient, ip: str = "203.0.113.7", **query: str):
    return client.get("/search", params=query, headers={"fly-client-ip": ip})


# --- A.6.1 the form, and the tool's answer under it ---------------------------------


def test_no_query_is_the_form_and_reads_nothing(client, fake):
    page = client.get("/search").text
    assert '<form method="get" action="/search">' in page
    assert "<section" not in page and 'class="answer"' not in page
    assert fake.requests == []
    for label in (text.SEARCH_LABEL_KIND, text.SEARCH_LABEL_ZIP, text.SEARCH_LABEL_MILES,
                  text.SEARCH_LABEL_RATING, text.SEARCH_BUTTON, text.SEARCH_KIND_NURSING,
                  text.SEARCH_KIND_HH, text.SEARCH_RATING_ANY):
        assert f">{label}<" in page, label
    assert '<option value="15" selected>15 miles</option>' in page
    assert '<option value="" selected>Any rating</option>' in page
    assert re.search(r'<input id="zip" name="zip" type="text" inputmode="numeric"', page)
    assert re.findall(r'<option value="(\d+)">\1 miles', page) == [
        "5", "10", "25", "50"]  # and 15, selected
    assert re.findall(r'<option value="(\d)">\1 of 5', page) == ["3", "4", "5"]


def test_the_answer_is_find_cares_character_for_character(client):
    for query, tool in [
        (FULL, {"kind": "nursing home", "zip": "27502", "miles": 15}),
        ({**FULL, "kind": "home health", "min_rating": "4"},
         {"kind": "home health", "zip": "27502", "miles": 15, "min_rating": 4}),
        ({**FULL, "zip": "28273", "miles": "50", "min_rating": "3"},
         {"kind": "nursing home", "zip": "28273", "miles": 50, "min_rating": 3}),
        ({**FULL, "zip": "27936"}, {"kind": "nursing home", "zip": "27936", "miles": 15}),
    ]:
        page = search(client, **query).text
        assert read_answer(page).text() == call(client, "find_care", **tool), query


def test_each_provider_name_links_to_its_details(client):
    answer = read_answer(search(client, **FULL).text)
    names = [line.split(",")[0] for line in answer.blocks[0]]
    assert len(names) == 8
    assert [name for name, _ in answer.links] == names
    for name, href in answer.links:
        parts = urlsplit(href)
        assert parts.path == "/search/details"
        assert parse_qs(parts.query, keep_blank_values=True) == {
            "name": [name], "kind": ["nursing home"], "zip": ["27502"], "miles": ["15"],
            "min_rating": [""]}


def test_details_is_care_details_and_goes_back_with_the_same_query(client):
    name = "St. Mary's Care Center"
    page = client.get("/search/details", params={**FULL, "name": name}).text
    assert read_answer(page).text() == call(client, "care_details", name=name, zip="27502")
    back = re.search(r'<p class="back"><a href="([^"]+)">' + text.SEARCH_BACK + "</a>", page)
    assert back is not None
    parts = urlsplit(unescape(back.group(1)))
    assert parts.path == "/search"
    assert parse_qs(parts.query, keep_blank_values=True) == {
        "kind": ["nursing home"], "zip": ["27502"], "miles": ["15"], "min_rating": [""]}
    # Following a list link lands on the same answer.
    href = read_answer(search(client, **FULL).text).links[4][1]
    assert read_answer(client.get(unescape(href)).text).text() == read_answer(page).text()


def test_details_without_a_name_goes_back_to_the_search(client, fake):
    response = client.get("/search/details", params=FULL, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/search?kind=nursing+home&zip=27502")
    assert fake.requests == []


def test_results_close_with_the_source_the_call_then_the_assistant_line(client):
    page = search(client, **FULL).text
    head = f'<h2 id="results">{text.SEARCH_RESULTS_HEAD.format(zip="27502")}</h2>'
    assert head in page
    assert read_answer(page).blocks[-1][-1] == text.CALL_LINE
    assistant = (
        f'<p class="assistant">{text.SEARCH_ASSISTANT_LINE} <code>{text.CONNECTOR_ADDRESS}'
        f'</code> <a href="https://heykettle.com/care/">{text.SEARCH_ASSISTANT_LINK}</a></p>'
    )
    assert assistant in page
    assert page.index("</div></div>" + assistant) > page.index(head)


def test_the_form_keeps_what_was_asked(client):
    page = search(client, **{**FULL, "kind": "home health", "miles": "25", "min_rating": "4"}).text
    assert '<option value="home health" selected>' in page
    assert '<option value="25" selected>25 miles</option>' in page
    assert '<option value="4" selected>4 of 5</option>' in page
    assert 'value="27502"' in page


def test_what_is_typed_is_escaped(client):
    page = search(client, **{**FULL, "zip": '"><script>x</script>'}).text
    assert "<script" not in page
    assert "&quot;&gt;&lt;script&gt;" in page


# --- A.6.2 every refusal as the tool says it --------------------------------------


def test_zip_unknown_none_near_more_and_nearest_beyond(client):
    assert read_answer(search(client, **{**FULL, "zip": "abc"}).text).text() == text.ZIP_UNKNOWN
    none = read_answer(search(client, **{**FULL, "kind": "home health", "zip": "27936"}).text)
    assert none.blocks[0] == [
        "No home health agencies within 15 miles of 27936 in Medicare's list."]
    beyond = read_answer(search(client, **{**FULL, "zip": "27936"}).text)
    assert beyond.blocks[0] == [
        "No nursing homes within 15 miles of 27936 in Medicare's list. The nearest is Manteo "
        "Shores Care in Manteo, about 46 miles away."]
    assert [name for name, _ in beyond.links] == ["Manteo Shores Care"]
    more = read_answer(search(client, **FULL).text)
    assert more.blocks[1] == [text.MORE_LINE.format(more=2, miles=15)]


def test_cms_down_and_the_stale_line(client, fake, clock):
    fake.down = True
    assert read_answer(search(client, **FULL).text).text() == text.CMS_DOWN
    fake.down = False
    search(client, **FULL)
    clock.advance(hours=25)
    fake.down = True
    stale = read_answer(search(client, **FULL).text).blocks[-1]
    assert stale[0] == text.STALE_LINE.format(date="September 23, 2026")


# --- A.6.3 one limit for the web and /mcp ------------------------------------------


def test_the_61st_search_counting_tool_calls_is_rate_limited(fake, clock, centroids):
    now = [0.0]
    app = create_app(cms.make_client(fake), centroids, clock, RateLimiter(clock=lambda: now[0]))
    with TestClient(app) as c:
        for _ in range(30):
            assert call(c, "find_care", ip="198.51.100.9", kind="x", zip="1") == (
                text.KIND_UNKNOWN)
            assert read_answer(search(c, ip="198.51.100.9", zip="1").text).text() == (
                text.ZIP_UNKNOWN)
        assert read_answer(search(c, ip="198.51.100.9", **FULL).text).text() == (
            text.RATE_LIMITED)
        details = c.get("/search/details", params={**FULL, "name": "Apex Ridge"},
                        headers={"fly-client-ip": "198.51.100.9"})
        assert read_answer(details.text).text() == text.RATE_LIMITED
        assert call(c, "find_care", ip="198.51.100.9", kind="x", zip="1") == text.RATE_LIMITED
        assert read_answer(search(c, ip="198.51.100.10", zip="1").text).text() == (
            text.ZIP_UNKNOWN)
        assert fake.requests == []  # the refused search read nothing


# --- A.6.4 nothing runs, nothing is kept, nothing is fetched --------------------------


def test_no_script_no_cookie_no_request_to_anywhere(client):
    pages = [
        client.get("/search"),
        search(client, **FULL),
        search(client, **{**FULL, "zip": "27936"}),
        client.get("/search/details", params={**FULL, "name": "Apex Ridge"}),
    ]
    for response in pages:
        page = response.text
        assert "set-cookie" not in {k.lower() for k in response.headers}
        assert "<script" not in page.lower()
        assert not re.search(r"\bsrc\s*=", page, re.IGNORECASE)
        assert not re.search(r"<(img|link|iframe|object|embed|video|audio|source)\b", page)
        assert "url(" not in page and "@import" not in page
        for href in re.findall(r'href="([^"]*)"', page):
            assert href.startswith("/search") or href == "https://heykettle.com/care/", href
        for action in re.findall(r'action="([^"]*)"', page):
            assert action == "/search"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert '<meta name="referrer" content="no-referrer">' in page
        assert response.headers["content-security-policy"].startswith("default-src 'none';")
        assert response.headers["cache-control"] == "no-store"


def test_every_control_is_at_least_44px_and_the_form_fits_a_phone():
    from care.web import PAGE

    assert "select, input, button {{ box-sizing: border-box; width: 100%; min-height: 2.75rem;" in (
        PAGE)  # 2.75rem is 44px at the default size, and grows with the reader's font size
    assert "minmax(10rem, 1fr)" in PAGE  # 360px less 2rem of gutter holds one column
    assert "px" not in re.sub(r"\d+px solid|outline-offset: 2px|border-radius: 8px", "", PAGE)


def _site_bans() -> list[str]:
    """The site's copy-law lists, read out of site/src/tests/copyBans.ts, so
    this page is held to the same law rather than to a copy of it."""
    source = SITE_BANS.read_text()
    words: list[str] = []
    for name in ("URGENCY", "DIAGNOSIS", "MEDICAL", "ALARM", "SURVEILLANCE", "VERDICTS",
                 "INFERENCE", "MECHANISM", "CULTURE_CODED"):
        body = re.search(rf"export const {name} = \[(.*?)\];", source, re.S)
        assert body, name
        words += re.findall(r'"([^"]+)"', body.group(1))
    assert len(words) > 60
    return words


#: §10's ruled answers say "just now" (CMS_DOWN, STALE_LINE); the urgency ban
#: is about pressing a reader, and these say when Medicare's site failed.
RULED = ("just now",)


def test_the_copy_law_over_every_rendered_page(client, fake, clock):
    pages = [client.get("/search").text, search(client, **FULL).text,
             search(client, **{**FULL, "zip": "abc"}).text,
             client.get("/search/details", params={**FULL, "name": "Morrisville"}).text]
    search(client, **{**FULL, "kind": "home health"})
    clock.advance(hours=25)
    fake.down = True
    pages += [search(client, **{**FULL, "kind": "home health"}).text,
              search(client, **{**FULL, "zip": "28273"}).text]
    bans = _site_bans()
    for page in pages:
        body = unescape(re.sub(r"<[^>]+>", " ", page.split("</style>")[1])).lower()
        assert "—" not in body and "–" not in body
        for phrase in RULED:
            body = body.replace(phrase, " ")
        for word in bans:
            assert not re.search(rf"\b{re.escape(word)}\b", body), word


# --- A.6.5 logging --------------------------------------------------------------------


def test_a_search_logs_one_line_without_the_zip_or_a_name(client, caplog):
    caplog.set_level(logging.DEBUG)
    search(client, ip="192.0.2.80", **{**FULL, "zip": "28273"})
    client.get("/search/details", params={**FULL, "zip": "28273", "name": "Fort Mill Place"},
               headers={"fly-client-ip": "192.0.2.80"})
    client.get("/search")
    logged = "\n".join(f"{r.name} {r.getMessage()} {r.args!r}" for r in caplog.records).lower()
    for secret in ("28273", "fort mill", "queen city", "192.0.2.80", "nursing", "=sc", "=nc",
                   "/search"):
        assert secret not in logged, secret
    assert [r.getMessage() for r in caplog.records if r.name == "care"] == [
        "search ok 2", "search_details ok 1"]


# --- A.6.6 acronyms -------------------------------------------------------------------


def test_unc_rex(client, fake):
    rows = json.loads((FIXTURES / "datastore_4pq5-n9py_NC.json").read_text())["results"]
    unc = {**rows[0], "provider_name": "UNC REX REHAB & NURSING CARE CENTER OF APEX",
           "provider_address": "5 REX WAY", "latitude": "35.69", "longitude": "-78.90"}
    fake.extra[(cms.NURSING_HOMES, "NC")] = [*rows, unc]
    page = client.get("/search/details", params={**FULL, "name": "UNC Rex"}).text
    first = read_answer(page).blocks[0][0]
    assert first.startswith("UNC Rex Rehab & Nursing Care Center of Apex, 5 Rex Way, Apex, NC ")
    assert "Unc Rex" not in page
    listed = call(client, "find_care", kind="nursing home", zip="27502", miles=5)
    assert "UNC Rex Rehab & Nursing Care Center of Apex, Apex, about 3 miles away." in listed


def test_the_acronym_list():
    assert title("UNC REX REHAB & NURSING CARE CENTER OF APEX") == (
        "UNC Rex Rehab & Nursing Care Center of Apex")
    assert title("ACME HOME HEALTH, LLC") == "Acme Home Health, LLC"
    assert title("ACME CARE PLLC") == "Acme Care PLLC"
    assert title("ACME PARTNERS LLP") == "Acme Partners LLP"
    assert title("ACME CARE LP") == "Acme Care LP"
    assert title("BAYADA HOME HEALTH CARE, INC.") == "Bayada Home Health Care, Inc."
    assert title("ACME CARE INC") == "Acme Care Inc."
    assert title("CARE USA") == "Care USA"
    assert title("VA MEDICAL CENTER SNF") == "VA Medical Center SNF"
    assert title("TRIANGLE CARE OF NC") == "Triangle Care of NC"
    assert title("FORT MILL SC") == "Fort Mill SC"
    # State codes that are also words stay words.
    assert title("CARE IN THE PINES") == "Care in the Pines"
    assert title("LA GRANGE") == "La Grange"
    assert title("DE SOTO") == "De Soto"
    assert title("MT OLIVE") == "Mt Olive"
    assert title("ME AND MY HOUSE") == "Me and My House"
