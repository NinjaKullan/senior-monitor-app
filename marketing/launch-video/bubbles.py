#!/usr/bin/env python3
"""Paper props for the feature videos, drawn by headless Chrome as transparent PNGs that the
Blender sets lay down as paper cards.

python3 bubbles.py -> assets/bubbles/in.png (a cream bubble, tail left), out.png (a sage bubble,
tail right) and call.png (a missed-call chip: a green circle with a handset), for the family
video's "scattered" beat (phones.py sc); newspaper.png, Dad's folded paper (kitchen.py 10a-10c)
No words anywhere: soft grey bars stand where text would be, like the kitchen's message bubble, so
nothing reads as a real app screen, and the newspaper has no masthead or headline.
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


def newspaper() -> tuple[str, int, int]:
    """A newspaper folded in half: newsprint cream, four columns of fine grey lines, one grey
    picture block, and a soft shadow along the fold at the top edge."""
    lines = "repeating-linear-gradient(#CFC8BB 0 5px, transparent 5px 15px)"
    cols = "".join(
        f'<div style="position:absolute;left:{40 + k * 205}px;top:{70 if k != 1 else 250}px;'
        f'width:180px;bottom:40px;background:{lines}"></div>'
        for k in range(4)
    )
    body = f"""<div style="position:absolute;inset:6px;background:#EFEAE0;border:5px solid #B9B1A4;
        border-radius:6px;overflow:hidden;box-shadow:inset 0 26px 22px -18px rgba(90,80,64,.35)">
      {cols}<div style="position:absolute;left:245px;top:70px;width:180px;height:160px;
        background:#D8D1C5"></div></div>"""
    return body, 900, 620


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pieces = {
        "in": bubble("#FBF6EC", False, (0.9, 0.62)),
        "out": bubble("#DCE8D6", True, (0.8, 0.5)),
        "call": call(),
        "newspaper": newspaper(),
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
