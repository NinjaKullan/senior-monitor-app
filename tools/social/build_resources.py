#!/usr/bin/env python3
"""Turn social/resources/<date>/resources.json into index.html (phone page with copy
buttons) and roundup.md. Usage: python tools/social/build_resources.py social/resources/<date>
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

from build_week import SCRIPT, STYLE  # same look as the posts page


def card(it: dict) -> str:
    e = html.escape
    meta = f"<b>Who:</b> {e(it.get('who', ''))}<br><b>Cost:</b> {e(it.get('cost', ''))}<br><b>Why now:</b> {e(it.get('why_now', ''))}"
    pin = f"{it.get('pin_title', '')}\n\n{it.get('pin_description', '')}\n\n{it.get('url', '')}"
    return f"""<div class="card"><div class="top"><span class="day">{e(it.get('name', ''))}</span><span class="chip">{e(it.get('lane', ''))}</span></div>
<div>{e(it.get('what', ''))}</div>
<div class="meta">{meta}<br><b>Link:</b> <a href="{e(it.get('url', ''))}">{e(it.get('url', ''))}</a></div>
<p class="meta"><b>Pinterest</b></p><div><pre>{e(pin)}</pre><button onclick="cp(this)">Copy text</button></div>
<p class="meta"><b>X</b></p><div><pre>{e(it.get('x_line', ''))}</pre><button onclick="cp(this)">Copy text</button></div>
</div>"""


def build(folder: Path) -> None:
    spec = json.loads((folder / "resources.json").read_text(encoding="utf-8"))
    e = html.escape
    parts = [f"<title>Kettle resources {e(spec.get('date', ''))}</title>", STYLE,
             f"<h1>Useful resources <small>{e(spec.get('date', ''))}</small></h1>",
             '<p class="theme">Five things worth passing on. Pick what to post; the roundup at the end is for the blog.</p>']
    parts += [card(it) for it in spec.get("items", [])]
    roundup = spec.get("roundup_md", "")
    parts.append(f'<div class="card"><div class="top"><span class="day">Blog roundup</span><span class="chip">heykettle.com</span></div><div><pre>{e(roundup)}</pre><button onclick="cp(this)">Copy text</button></div></div>')
    parts.append(SCRIPT)
    (folder / "index.html").write_text("\n".join(parts), encoding="utf-8")
    (folder / "roundup.md").write_text(roundup, encoding="utf-8")
    print(f"wrote {folder / 'index.html'} and roundup.md")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: build_resources.py social/resources/<date>")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    build(Path(sys.argv[1]))
