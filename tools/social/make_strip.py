#!/usr/bin/env python3
"""Draw a Kettle cartoon strip (or the character sheet) with Gemini's image model.

Stdlib only. The API key is never in this file or the repo: in Claude cloud
sessions the environment's API credential adds the x-goog-api-key header on the
way out; for a local run, export GEMINI_API_KEY.

Usage
  python tools/social/make_strip.py --sheet --out tools/social/characters/sheet.png
  python tools/social/make_strip.py --panels panels.json --out strip.png --aspect 2:3

panels.json: {"panels": [{"scene": "...", "dialogue": [["Priya", "..."]], "caption": ""}, ...]}
Every character named in dialogue must exist in characters.md.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOST = "https://generativelanguage.googleapis.com/v1beta/models"
MODELS = [m for m in os.environ.get("KETTLE_IMAGE_MODELS", "gemini-2.5-flash-image").split(",") if m]
STYLE_FILE = HERE / "characters.md"
SHEET_FILES = sorted((HERE / "characters").glob("*.png")) if (HERE / "characters").exists() else []


def _style_bible() -> str:
    return STYLE_FILE.read_text(encoding="utf-8")


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
                try:
                    with urllib.request.urlopen(req, timeout=180) as r:
                        data = json.load(r)
                    for part in data["candidates"][0]["content"]["parts"]:
                        if "inlineData" in part:
                            return base64.b64decode(part["inlineData"]["data"])
                        if "inline_data" in part:
                            return base64.b64decode(part["inline_data"]["data"])
                    last = f"{model}: no image in response: {json.dumps(data)[:300]}"
                    break
                except urllib.error.HTTPError as e:
                    msg = e.read().decode(errors="replace")[:300]
                    last = f"{model} HTTP {e.code}: {msg}"
                    if e.code in (429, 500, 503):
                        time.sleep(8 * (attempt + 1))
                        continue
                    break  # 400 etc: try next config/model
                except (urllib.error.URLError, TimeoutError) as e:
                    last = f"{model}: {e}"
                    time.sleep(5)
    raise SystemExit(f"image generation failed: {last}")


def sheet_prompt() -> str:
    return (
        "Draw a CHARACTER SHEET for a newspaper comic strip. Follow this style bible exactly:\n\n"
        + _style_bible()
        + "\n\nLayout: white background, each character shown three times (front view, three-quarter view, "
        "side view) at the same scale, with the character's name lettered under them in plain capitals. "
        "Add one small row of simple props: an iPhone, a kettle, a kitchen table. No speech bubbles, no scene, "
        "no other text. This sheet will be used as the reference for every future strip, so make each character "
        "distinctive and easy to redraw."
    )


def strip_prompt(spec: dict, aspect: str) -> str:
    n = len(spec["panels"])
    layout = {"2:3": "stacked vertically, one above the other", "1:1": "in a 2x2 grid" if n == 4 else "in a row",
              "16:9": "in a row"}.get(aspect, "in a row")
    lines = [
        f"Draw ONE newspaper comic strip of {n} panels {layout}, in the exact style and with the exact characters "
        "shown in the attached reference sheet. Follow this style bible:\n",
        _style_bible(),
        "\nLetter every word of dialogue EXACTLY as written below, in clean hand-lettered capitals inside simple "
        "speech bubbles. Do not add, drop or change any words. Use straight apostrophes. No other text anywhere "
        "in the image except an optional small caption under a panel where one is given.\n",
    ]
    for i, p in enumerate(spec["panels"], 1):
        lines.append(f"PANEL {i}: {p['scene']}")
        for who, said in p.get("dialogue", []):
            lines.append(f'  {who} says: "{said}"')
        if p.get("caption"):
            lines.append(f"  Caption under panel: \"{p['caption']}\"")
    if spec.get("signature", True):
        lines.append("\nIn the last panel's bottom-right corner, letter a tiny signature: heykettle.com")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", action="store_true", help="generate the character sheet")
    ap.add_argument("--panels", help="panels.json for a strip")
    ap.add_argument("--out", required=True)
    ap.add_argument("--aspect", default="2:3", choices=["2:3", "1:1", "16:9", "3:4", "4:5"])
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.sheet:
        png = call_gemini(sheet_prompt(), [], "16:9")
    elif args.panels:
        if not SHEET_FILES:
            sys.exit("no character sheet in tools/social/characters/ - run --sheet first and commit it")
        spec = json.loads(Path(args.panels).read_text(encoding="utf-8"))
        png = call_gemini(strip_prompt(spec, args.aspect), SHEET_FILES, args.aspect)
    else:
        sys.exit("give --sheet or --panels")
    out.write_bytes(png)
    print(f"wrote {out} ({len(png)//1024} KB)")


if __name__ == "__main__":
    main()
