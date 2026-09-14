#!/usr/bin/env python3
"""Turn a week folder (posts.json + PNGs) into one phone-friendly page, index.html.

Usage: python tools/social/build_week.py social/weeks/2026-W38

posts.json:
{"week": "2026-W38", "theme": "...",
 "posts": [{"day": "Mon", "channel": "x|pinterest|tiktok", "title": "...", "text": "...",
            "image": "mon-x.png", "alt": "...", "destination": "", "cta": false,
            "script": [{"t": "0:00-0:05", "say": "...", "overlay": "...", "broll": "..."}],
            "note": "..."}]}

The page is a fragment (title + style + body content, no doctype) so it can be published
as a Claude artifact as-is; browsers open it fine too. Images are embedded, so the one
file is all you need on your phone.
"""
from __future__ import annotations

import base64
import html
import json
import sys
from pathlib import Path

STYLE = """
<style>
:root{--paper:#F7F1E8;--ink:#403C36;--green:#297A5C;--line:#DDD5C8;--card:#FFFDF9}
body{background:var(--paper);color:var(--ink);font:16px/1.5 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;padding:16px;max-width:720px;margin:0 auto}
h1{font-size:22px;margin:8px 0 2px}h1 small{font-weight:400;color:#7a7268}
.theme{margin:0 0 18px;color:#5c564d}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:0 0 18px}
.top{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px}
.chip{font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--green);border:1px solid var(--green);border-radius:999px;padding:2px 9px}
.day{font-weight:600}
img{display:block;width:100%;max-width:100%;border-radius:10px;border:1px solid var(--line);margin:8px 0}
pre{white-space:pre-wrap;word-wrap:break-word;font:inherit;background:var(--paper);border-radius:10px;padding:12px;margin:8px 0}
button{background:var(--green);color:#fff;border:0;border-radius:10px;padding:10px 14px;font:600 15px inherit;cursor:pointer}
button.done{background:#6c9a86}
.meta{font-size:13px;color:#7a7268;margin-top:8px}
.meta b{color:var(--ink)}
table{width:100%;border-collapse:collapse;font-size:14px;margin:8px 0}
td,th{text-align:left;vertical-align:top;padding:6px 6px;border-top:1px solid var(--line)}
th{font-weight:600;color:#7a7268;border:0;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
details{margin-top:6px}summary{cursor:pointer;color:#7a7268;font-size:14px}
.hint{font-size:13px;color:#7a7268;margin:-4px 0 12px}
</style>
"""

SCRIPT = """
<script>
function cp(btn){const t=btn.parentElement.querySelector('pre').innerText;
 const ok=()=>{btn.textContent='Copied';btn.classList.add('done');setTimeout(()=>{btn.textContent='Copy text';btn.classList.remove('done')},1500)};
 if(navigator.clipboard){navigator.clipboard.writeText(t).then(ok).catch(()=>fallback(t,ok))}else{fallback(t,ok)}}
function fallback(t,ok){const ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();
 try{document.execCommand('copy');ok()}catch(e){}document.body.removeChild(ta)}
</script>
"""

CHANNEL = {"x": "X", "pinterest": "Pinterest", "tiktok": "TikTok"}


def img_tag(folder: Path, name: str, alt: str) -> str:
    p = folder / name
    if not name or not p.exists():
        return '<p class="meta"><b>Image:</b> pending</p>'
    data = base64.b64encode(p.read_bytes()).decode()
    return f'<img src="data:image/png;base64,{data}" alt="{html.escape(alt)}">'


def card(folder: Path, post: dict) -> str:
    e = html.escape
    ch = post.get("channel", "x")
    out = [f'<div class="card"><div class="top"><span class="day">{e(post.get("day", ""))}</span>'
           f'<span class="chip">{CHANNEL.get(ch, ch)}</span></div>']
    if post.get("title"):
        out.append(f'<div><b>{e(post["title"])}</b></div>')
    out.append(img_tag(folder, post.get("image", ""), post.get("alt", "")))
    if post.get("image"):
        out.append('<p class="hint">Long-press the image to save it to your phone.</p>')
    if post.get("text"):
        out.append(f'<div><pre>{e(post["text"])}</pre><button onclick="cp(this)">Copy text</button></div>')
    if ch == "tiktok" and post.get("script"):
        rows = "".join(
            f"<tr><td>{e(s.get('t', ''))}</td><td>{e(s.get('say', ''))}</td>"
            f"<td>{e(s.get('overlay', ''))}</td><td>{e(s.get('broll', ''))}</td></tr>"
            for s in post["script"])
        out.append(f"<table><tr><th>Time</th><th>Say</th><th>Overlay</th><th>Shot</th></tr>{rows}</table>")
    meta = []
    if post.get("destination"):
        meta.append(f'<b>Link:</b> {e(post["destination"])}')
    if post.get("alt"):
        meta.append(f'<b>Alt text (provisional):</b> {e(post["alt"])}')
    meta.append(f'<b>CTA:</b> {"yes" if post.get("cta") else "none"}')
    out.append(f'<div class="meta">{"<br>".join(meta)}</div>')
    if post.get("note"):
        out.append(f'<details><summary>Note from the writer</summary><p class="meta">{e(post["note"])}</p></details>')
    out.append("</div>")
    return "\n".join(out)


def build(folder: Path) -> Path:
    spec = json.loads((folder / "posts.json").read_text(encoding="utf-8"))
    e = html.escape
    parts = [f"<title>Kettle posts {e(spec.get('week', ''))}</title>", STYLE,
             f"<h1>This week's posts <small>{e(spec.get('week', ''))}</small></h1>",
             f"<p class=\"theme\">{e(spec.get('theme', ''))}</p>"]
    parts += [card(folder, p) for p in spec.get("posts", [])]
    parts.append(SCRIPT)
    out = folder / "index.html"
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: build_week.py social/weeks/<week>")
    build(Path(sys.argv[1]))
