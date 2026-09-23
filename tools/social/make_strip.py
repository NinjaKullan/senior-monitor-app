#!/usr/bin/env python3
"""Draw a Kettle cartoon strip: the image model draws each panel WITHOUT text, then this
script composes the panels and letters the speech bubbles, captions and signature
itself, so the words are always exactly the words in the spec.

Stdlib + Pillow. The API key is never in this file or the repo: in Claude cloud sessions
the environment's API credential adds the x-goog-api-key header on the way out; for a
local run, export GEMINI_API_KEY.

Usage
  python tools/social/make_strip.py --sheet --cast B --out tools/social/characters/sheet-b.png
  python tools/social/make_strip.py --panels x.panels.json --out x.png --layout row
  python tools/social/make_strip.py --panels p.panels.json --out p.png --layout stack
  python tools/social/make_strip.py --panels c.panels.json --out c.png --layout single

Layouts: row = panels side by side (X), stack = panels top to bottom (Pinterest),
single = one panel with a caption (TikTok cover). --cast A|B|auto (auto = even ISO week
is A, odd is B).

panels.json: {"panels": [{"scene": "...", "dialogue": [["JUNE", "..."]], "caption": ""}, ...]}
Every character named in dialogue must be in the active cast in characters.md.
Each panel's drawing is cached next to the output as <out stem>.p<N>.png; delete one to
redraw only that panel.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
HOST = "https://generativelanguage.googleapis.com/v1beta/models"
MODELS = [m for m in os.environ.get("KETTLE_IMAGE_MODELS", "gemini-3.1-flash-image,gemini-2.5-flash-image").split(",") if m]
STYLE_FILE = HERE / "characters.md"
FONT_FILE = HERE / "fonts" / "PatrickHand-Regular.ttf"
COUNTER = Path.home() / ".kettle_image_count.json"
CAP = int(os.environ.get("KETTLE_IMAGE_CAP", "30"))

PAPER, INK, GREEN = (247, 241, 232), (64, 60, 54), (41, 122, 92)
BANNED = ["monitor", "track", "alert", "surveillance", "elderly", "senior", "aging parent",
          "dashboard", "sensor", "detect", "safety device", "ordinary"]

# ----------------------------------------------------------------------------- casts

def pick_cast(arg: str) -> str:
    if arg.upper() in ("A", "B"):
        return arg.upper()
    return "A" if dt.date.today().isocalendar()[1] % 2 == 0 else "B"


def style_bible(cast: str) -> str:
    """characters.md with the other cast's section removed."""
    text = STYLE_FILE.read_text(encoding="utf-8")
    other = "B" if cast == "A" else "A"
    return re.sub(rf"## Cast {other}.*?(?=\n## )", "", text, flags=re.S)


def sheet_files(cast: str) -> list[Path]:
    d = HERE / "characters"
    for name in (f"sheet-{cast.lower()}.png", "sheet.png" if cast == "A" else ""):
        if name and (d / name).exists():
            return [d / name]
    return []

# ----------------------------------------------------------------------------- api

def _count_call() -> None:
    today = dt.date.today().isoformat()
    try:
        data = json.loads(COUNTER.read_text())
    except (OSError, ValueError):
        data = {}
    if data.get("date") != today:
        data = {"date": today, "count": 0}
    if data["count"] >= CAP:
        sys.exit(f"daily image cap reached ({CAP}); set KETTLE_IMAGE_CAP to raise it")
    data["count"] += 1
    COUNTER.write_text(json.dumps(data))


def _b64_image(path: Path) -> dict:
    return {"inline_data": {"mime_type": "image/png", "data": base64.b64encode(path.read_bytes()).decode()}}


def call_gemini(prompt: str, refs: list[Path], aspect: str) -> bytes:
    """Return PNG bytes. Tries each model, with and without the aspect hint."""
    parts = [{"text": prompt}] + [_b64_image(p) for p in refs]
    headers = {"Content-Type": "application/json"}
    if os.environ.get("GEMINI_API_KEY"):
        headers["x-goog-api-key"] = os.environ["GEMINI_API_KEY"]
    last = ""
    for model in MODELS:
        for gen in ({"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}},
                    {"responseModalities": ["IMAGE"]}):
            body = json.dumps({"contents": [{"parts": parts}], "generationConfig": gen}).encode()
            req = urllib.request.Request(f"{HOST}/{model}:generateContent", data=body, headers=headers)
            for attempt in range(4):
                _count_call()
                try:
                    with urllib.request.urlopen(req, timeout=180) as r:
                        data = json.load(r)
                    for part in data["candidates"][0]["content"]["parts"]:
                        blob = part.get("inlineData") or part.get("inline_data")
                        if blob:
                            return base64.b64decode(blob["data"])
                    last = f"{model}: no image in response: {json.dumps(data)[:300]}"
                    break
                except urllib.error.HTTPError as e:
                    last = f"{model} HTTP {e.code}: {e.read().decode(errors='replace')[:300]}"
                    if e.code in (429, 500, 503):
                        time.sleep(8 * (attempt + 1))
                        continue
                    break
                except (urllib.error.URLError, TimeoutError) as e:
                    last = f"{model}: {e}"
                    time.sleep(5)
    raise SystemExit(f"image generation failed: {last}")

# ----------------------------------------------------------------------------- prompts

def sheet_prompt(cast: str) -> str:
    return (
        "Draw a CHARACTER SHEET for a newspaper comic strip. Follow this style bible exactly "
        "(ignore its rule about leaving the top third empty; a sheet is not a panel):\n\n"
        + style_bible(cast)
        + "\n\nLayout: plain paper background, each of the two characters shown three times (front "
        "view, three-quarter view, side view) at the same scale, plus the kettle, an iPhone and a "
        "kitchen table as small props. No words, no labels, no speech bubbles. This sheet is the "
        "reference for every future strip, so make each character distinctive and easy to redraw."
    )


def panel_prompt(cast: str, scene: str, aspect: str, n: int, i: int) -> str:
    return (
        f"Draw ONE single panel (panel {i} of {n}) of a newspaper comic strip, in the exact style and "
        "with the exact characters shown in the attached reference sheet. Follow this style bible:\n\n"
        + style_bible(cast)
        + f"\n\nTHE SCENE: {scene}\n\nAbsolutely no text, letters, numbers, signs or speech bubbles "
        f"anywhere in the image. Keep the top third plain. Image shape {aspect}. No panel border."
    )

# ----------------------------------------------------------------------------- lettering

def check_words(spec: dict) -> None:
    bad = []
    for p in spec["panels"]:
        for _, said in p.get("dialogue", []):
            bad += _check(said)
        if p.get("caption"):
            bad += _check(p["caption"])
    if bad:
        sys.exit("lettering breaks the copy laws: " + "; ".join(bad))


def _check(s: str) -> list[str]:
    out = []
    low = s.lower()
    for w in BANNED:
        if re.search(rf"\b{re.escape(w)}", low):
            out.append(f"'{w}' in: {s}")
    if "—" in s or "’" in s or "“" in s or "”" in s:
        out.append(f"em dash or curly quote in: {s}")
    if len(s.split()) > 12:
        out.append(f"more than 12 words: {s}")
    return out


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_FILE), size)


def wrap(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit(draw, text, max_w, start, min_size=18, max_lines=3):
    size = start
    while size > min_size:
        f = font(size)
        lines = wrap(draw, text, f, max_w)
        if len(lines) <= max_lines:
            return f, lines
        size -= 2
    f = font(min_size)
    return f, wrap(draw, text, f, max_w)


def draw_bubble(img: Image.Image, text: str, y_top: int, tail_x_frac: float) -> int:
    """Draw a speech bubble near the top of a panel. Returns the y below the bubble."""
    w = img.width
    draw = ImageDraw.Draw(img)
    f, lines = fit(draw, text.upper(), int(w * 0.66), max(28, w // 28))
    line_h = int(f.size * 1.18)
    tw = max(draw.textlength(ln, font=f) for ln in lines)
    pad = int(f.size * 0.7)
    bw, bh = int(tw + 2 * pad), int(len(lines) * line_h + 2 * pad)
    x0 = (w - bw) // 2
    y0 = y_top
    draw.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=int(pad * 1.2), fill=(255, 253, 249), outline=INK, width=3)
    tx = int(x0 + bw * tail_x_frac)
    tail = [(tx - pad // 2, y0 + bh - 2), (tx + pad // 2, y0 + bh - 2), (tx - pad // 3, y0 + bh + int(pad * 1.1))]
    draw.polygon(tail, fill=(255, 253, 249), outline=INK)
    draw.line([tail[0], tail[2]], fill=INK, width=3)
    draw.line([tail[1], tail[2]], fill=INK, width=3)
    draw.line([tail[0], tail[1]], fill=(255, 253, 249), width=4)
    y = y0 + pad
    for ln in lines:
        lw = draw.textlength(ln, font=f)
        draw.text(((w - lw) // 2, y), ln, font=f, fill=INK)
        y += line_h
    return y0 + bh + pad


def caption_band(width: int, text: str) -> Image.Image:
    tmp = Image.new("RGB", (width, 10), PAPER)
    draw = ImageDraw.Draw(tmp)
    f, lines = fit(draw, text.upper(), int(width * 0.86), max(26, width // 30), max_lines=2)
    line_h = int(f.size * 1.2)
    band = Image.new("RGB", (width, int(len(lines) * line_h + f.size * 1.1)), PAPER)
    d = ImageDraw.Draw(band)
    y = int(f.size * 0.5)
    for ln in lines:
        d.text(((width - d.textlength(ln, font=f)) // 2, y), ln, font=f, fill=INK)
        y += line_h
    return band


def frame(panel: Image.Image, border: int = 4) -> Image.Image:
    out = Image.new("RGB", (panel.width + 2 * border, panel.height + 2 * border), INK)
    out.paste(panel, (border, border))
    return out


def compose(panels: list[Image.Image], spec: dict, layout: str) -> Image.Image:
    gutter, margin = 28, 44
    units = []
    for img, p in zip(panels, spec["panels"]):
        y = int(img.height * 0.035)
        for k, (_, said) in enumerate(p.get("dialogue", [])):
            y = draw_bubble(img, said, y, 0.35 if k % 2 == 0 else 0.65)
        unit = frame(img)
        if p.get("caption"):
            band = caption_band(unit.width, p["caption"])
            u = Image.new("RGB", (unit.width, unit.height + band.height), PAPER)
            u.paste(unit, (0, 0))
            u.paste(band, (0, unit.height))
            unit = u
        units.append(unit)
    if layout == "row":
        h = max(u.height for u in units)
        W = sum(u.width for u in units) + gutter * (len(units) - 1) + 2 * margin
        canvas = Image.new("RGB", (W, h + 2 * margin + 40), PAPER)
        x = margin
        for u in units:
            canvas.paste(u, (x, margin))
            x += u.width + gutter
    else:  # stack or single
        w = max(u.width for u in units)
        H = sum(u.height for u in units) + gutter * (len(units) - 1) + 2 * margin + 40
        canvas = Image.new("RGB", (w + 2 * margin, H), PAPER)
        y = margin
        for u in units:
            canvas.paste(u, (margin + (w - u.width) // 2, y))
            y += u.height + gutter
    d = ImageDraw.Draw(canvas)
    f = font(max(22, canvas.width // 45))
    sig = "heykettle.com"
    d.text((canvas.width - margin - d.textlength(sig, font=f), canvas.height - margin - f.size + 6), sig, font=f, fill=(122, 114, 104))
    return canvas

# ----------------------------------------------------------------------------- main

PANEL_SHAPE = {"row": ("3:4", (900, 1200)), "stack": ("4:3", (1200, 900)), "single": ("3:4", (1200, 1600))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--panels")
    ap.add_argument("--out", required=True)
    ap.add_argument("--layout", default="stack", choices=list(PANEL_SHAPE))
    ap.add_argument("--cast", default="auto")
    args = ap.parse_args()
    cast = pick_cast(args.cast)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.sheet:
        out.write_bytes(call_gemini(sheet_prompt(cast), [], "16:9"))
        print(f"wrote {out} (cast {cast})")
        return
    if not args.panels:
        sys.exit("give --sheet or --panels")
    refs = sheet_files(cast)
    if not refs:
        sys.exit(f"no character sheet for cast {cast} in tools/social/characters/ (run --sheet --cast {cast})")
    spec = json.loads(Path(args.panels).read_text(encoding="utf-8"))
    check_words(spec)
    aspect, size = PANEL_SHAPE[args.layout]
    n = len(spec["panels"])
    if args.layout == "single" and n != 1:
        sys.exit("single layout takes exactly one panel")
    panels = []
    for i, p in enumerate(spec["panels"], 1):
        cache = out.with_name(f"{out.stem}.p{i}.png")
        if not cache.exists():
            cache.write_bytes(call_gemini(panel_prompt(cast, p["scene"], aspect, n, i), refs + panels_as_refs(out, i), aspect))
            print(f"drew panel {i}")
        img = Image.open(cache).convert("RGB")
        panels.append(img.resize(size, Image.LANCZOS))
    strip = compose(panels, spec, args.layout)
    strip.save(out, optimize=True)
    print(f"wrote {out} {strip.size} (cast {cast})")


def panels_as_refs(out: Path, i: int) -> list[Path]:
    """The previous panel, as a continuity reference."""
    prev = out.with_name(f"{out.stem}.p{i - 1}.png")
    return [prev] if i > 1 and prev.exists() else []


if __name__ == "__main__":
    main()
