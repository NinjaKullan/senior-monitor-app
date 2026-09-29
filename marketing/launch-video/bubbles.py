#!/usr/bin/env python3
"""Paper message bubbles for the family video's "scattered" beat, drawn by headless Chrome as
transparent PNGs that blender/features.py lays on the table as paper cards.

python3 bubbles.py -> assets/bubbles/in.png (a cream bubble, tail left), out.png (a sage bubble,
tail right) and call.png (a missed-call chip: a green circle with a handset)
No words: soft grey bars stand where text would be, like the kitchen's message bubble, so nothing
reads as a real app screen.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "assets" / "bubbles"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUTLINE, BAR = "#8A847B", "#C9C4BC"
HANDSET = (
    "M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 "
    "1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 "
    "1 0 0 1-.25 1z"
)


def bubble(fill: str, tail_right: bool, bars: tuple[float, ...]) -> tuple[str, int, int]:
    """A rounded bubble with a tail at the bottom corner: the tail is drawn outlined, then the body,
    then the tail again unoutlined so the join shows no line."""
    w, bh = 600, 70 + len(bars) * 60
    x0, x1, x2 = (w - 150, w - 80, w - 90) if tail_right else (150, 80, 90)
    tail = f"{x0},{bh} {x2},{bh + 66} {x1},{bh - 20}"
    rows = "".join(
        f'<rect x="64" y="{60 + i * 60}" width="{f * 472:.0f}" height="30" rx="15" fill="{BAR}"/>'
        for i, f in enumerate(bars)
    )
    body = f"""<svg width="{w}" height="{bh + 80}" style="position:absolute;left:0;top:0">
      <polygon points="{tail}" fill="{fill}" stroke="{OUTLINE}" stroke-width="7"
        stroke-linejoin="round"/>
      <rect x="10" y="10" width="{w - 20}" height="{bh}" rx="80" fill="{fill}"
        stroke="{OUTLINE}" stroke-width="7"/>
      <polygon points="{tail}" fill="{fill}" transform="translate(0,-8)"/>{rows}</svg>"""
    return body, w, bh + 80


def call() -> tuple[str, int, int]:
    body = f"""<div style="position:absolute;left:10px;top:10px;width:520px;height:160px;
        box-sizing:border-box;background:#FBF6EC;border:7px solid {OUTLINE};border-radius:80px">
      <div style="position:absolute;left:24px;top:22px;width:102px;height:102px;
        border-radius:50%;background:#297A5C;display:flex;align-items:center;
        justify-content:center"><svg width="60" height="60" viewBox="0 0 24 24">
        <path d="{HANDSET}" fill="#FBF6EC"/></svg></div>
      <div style="position:absolute;left:160px;top:44px;width:300px;height:28px;
        background:{BAR};border-radius:14px"></div>
      <div style="position:absolute;left:160px;top:92px;width:190px;height:24px;
        background:{BAR};border-radius:12px"></div></div>"""
    return body, 540, 180


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pieces = {
        "in": bubble("#FBF6EC", False, (0.9, 0.62)),
        "out": bubble("#DCE8D6", True, (0.8, 0.5)),
        "call": call(),
    }
    for name, (body, w, h) in pieces.items():
        src = OUT / f".{name}.html"
        src.write_text(f"""<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;
width:{w}px;height:{h}px;overflow:hidden;background:transparent}}</style>{body}""")
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                        "--default-background-color=00000000", f"--window-size={w},{h}",
                        f"--screenshot={OUT / f'{name}.png'}", f"file://{src}"],
                       check=True, capture_output=True)  # fmt: skip
        src.unlink()
        print(f"wrote assets/bubbles/{name}.png")


if __name__ == "__main__":
    main()
