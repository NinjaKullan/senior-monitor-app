"""Server-rendered HTML. Inline CSS, no JavaScript, no external assets.

Product law #4: nothing on these pages loads a third-party script, font, or
pixel. Everything is same-origin plain HTML so the pages work on a phone on a
bad Chennai connection and observe nobody.
"""

from __future__ import annotations

from html import escape
from urllib.parse import quote

CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
       margin: 0; padding: 1rem; max-width: 46rem; }
h1 { font-size: 1.3rem; margin: 0 0 .25rem; }
h2 { font-size: 1.05rem; margin: 1.5rem 0 .4rem; }
p.sub { margin: 0 0 1rem; opacity: .7; font-size: .85rem; }
table { border-collapse: collapse; width: 100%; font-size: .9rem; }
th, td { text-align: left; padding: .35rem .5rem; border-bottom: 1px solid #8883; }
th { font-weight: 600; opacity: .75; }
.card { border: 1px solid #8884; border-radius: .6rem; padding: .75rem 1rem;
        margin-bottom: .9rem; }
.big { font-size: 1.05rem; font-weight: 600; }
.muted { opacity: .6; }
nav a { display: inline-block; margin-right: .9rem; font-size: .9rem; }
form.label { border: 1px solid #8884; border-radius: .6rem; padding: .75rem 1rem;
             margin-bottom: .9rem; }
input[type=text] { width: 100%; padding: .55rem; font-size: 1rem;
                   border: 1px solid #8886; border-radius: .4rem; background: transparent;
                   color: inherit; }
button { margin-top: .5rem; margin-right: .5rem; padding: .6rem 1rem; font-size: 1rem;
         border-radius: .4rem; border: 1px solid #8886; background: #8882; color: inherit; }
.note { font-size: .85rem; opacity: .75; }
"""


def page(title: str, body: str) -> str:
    """Wrap body markup in the shared page shell."""
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{escape(title)}</title><style>{CSS}</style></head>"
        f"<body>{body}</body></html>"
    )


def _q(token: str) -> str:
    return f"?token={quote(token, safe='')}"


def nav(token: str) -> str:
    """Shared navigation strip."""
    t = _q(token)
    return (
        "<nav>"
        f"<a href='/status{t}'>Status</a>"
        f"<a href='/labels{t}'>Labels</a>"
        f"<a href='/pings/mom{t}'>Mom pings</a>"
        f"<a href='/pings/dad{t}'>Dad pings</a>"
        f"<a href='/export.csv{t}'>Export CSV</a>"
        "</nav>"
    )


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "<p class='muted'>Nothing yet.</p>"
    head = "".join(f"<th>{escape(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{escape(c)}</td>" for c in row) + "</tr>" for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def label_form(token: str, who: str, next_path: str) -> str:
    """One person's blinded-label form: free-text note or a one-tap 'nothing unusual'."""
    action = f"/labels{_q(token)}"
    return (
        f"<form class='label' method='post' action='{escape(action, quote=True)}'>"
        f"<input type='hidden' name='who' value='{escape(who, quote=True)}'>"
        f"<input type='hidden' name='next' value='{escape(next_path, quote=True)}'>"
        f"<div class='big'>{escape(who.title())}</div>"
        "<input type='text' name='note' autocomplete='off' "
        "placeholder='Anything unusual today? (travel, visitors, illness…)'>"
        "<div>"
        "<button type='submit' name='quick' value='1'>Nothing unusual</button>"
        "<button type='submit' name='save' value='1'>Save note</button>"
        "</div></form>"
    )


def interstitial(
    token: str, today_ist: str, missing: list[str], done: list[tuple[str, str]]
) -> str:
    """The blinding gate: labels first, data second."""
    forms = "".join(label_form(token, who, "/status") for who in missing)
    already = ""
    if done:
        rows = [[who.title(), note] for who, note in done]
        already = "<h2>Already logged today</h2>" + _table(["Who", "Note"], rows)
    body = (
        "<h1>Log today's labels before viewing data</h1>"
        f"<p class='sub'>{escape(today_ist)} IST — pilot protocol: write the label log "
        "before opening the dashboard, so the labels stay blind to the data.</p>"
        f"{forms}{already}"
    )
    return page("Labels first", body)


def status(
    token: str,
    now_ist: str,
    today_ist: str,
    people: list[dict],
    heartbeat: dict,
    recent: list[list[str]],
) -> str:
    """The founder dashboard."""
    blocks = []
    for person in people:
        rows = [
            [s["signal"], s["last_seen"], s["gap"]] for s in person["signals"]
        ]
        blocks.append(
            f"<h2>{escape(person['who'].title())}</h2>"
            "<div class='card'>"
            f"<div class='big'>{escape(person['alarm_gap'])}</div>"
            "<div class='muted'>since last alarm-grade ping "
            "(whatsapp / youtube / news)</div>"
            f"<div style='margin-top:.4rem'>Today: {person['today_count']} "
            "routine pings</div>"
            "</div>"
            + _table(["Signal", "Last seen (IST)", "Gap"], rows)
        )

    hb = (
        "<h2>Heartbeat</h2><div class='card'>"
        f"<div>Last check: {escape(heartbeat['last_check'])}</div>"
        f"<div>Last alert: {escape(heartbeat['last_alert'])}</div>"
        "<div class='note'>Founder-only. Nothing here is ever sent to family "
        "or to the parents' phones.</div></div>"
    )

    body = (
        "<h1>Kettle — pilot status</h1>"
        f"<p class='sub'>{escape(now_ist)} IST · labels logged for {escape(today_ist)}</p>"
        + nav(token)
        + "".join(blocks)
        + hb
        + "<h2>Recent pings</h2>"
        + _table(["Time (IST)", "Who", "Signal"], recent)
    )
    return page("Kettle status", body)


def labels_page(token: str, today_ist: str, rows: list[list[str]]) -> str:
    """Add/view the blinded ground-truth label log."""
    forms = "".join(label_form(token, who, "/labels") for who in ("mom", "dad"))
    body = (
        "<h1>Labels</h1>"
        f"<p class='sub'>Today is {escape(today_ist)} IST. "
        "Labels default to today.</p>"
        + nav(token)
        + forms
        + f"<p><a href='/labels.csv{_q(token)}'>Download labels.csv</a></p>"
        + "<h2>All labels</h2>"
        + _table(["Date (IST)", "Who", "Note", "Logged (IST)"], rows)
    )
    return page("Labels", body)


def pings_page(token: str, who: str, rows: list[list[str]]) -> str:
    """Full transparency view for one person: timestamps and signal names only."""
    body = (
        f"<h1>Every ping — {escape(who.title())}</h1>"
        f"<p class='sub'>{len(rows)} pings. This is the complete record: a time and "
        "the name of an app that was opened. No content, no location, nothing else "
        "is stored.</p>" + nav(token) + _table(["Time (IST)", "Signal"], rows)
    )
    return page(f"Pings — {who}", body)
