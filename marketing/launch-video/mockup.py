#!/usr/bin/env python3
"""Phase 3 mockups: one flat 1920x1080 still per shot, a contact sheet, and a silent rough cut.

Stdlib, headless Chrome (text) and ffmpeg (sheet, cut). Painted shots use the picked Gemini
mockup in assets/mock/; screen shots are
grey cards named for the recording that replaces them. Words come from SHOTS, in Patrick Hand.
Usage (in this folder): python3 mockup.py [shot-id ...]
  -> out/mock/<id>.png, out/contact-sheet.png, out/rough-cut.mp4.
With shot ids, only those stills are redrawn; the sheet and the cut always rebuild.
"""

from __future__ import annotations

import html
import subprocess
import sys
from pathlib import Path

from shots import SHOTS, check

HERE = Path(__file__).resolve().parent
FONT = HERE.parents[1] / "tools/social/fonts/PatrickHand-Regular.ttf"
OUT = HERE / "out/mock"
PAPER, INK, GREY, TABLE = "0xF7F1E8", "0x403C36", "0xC9C4BC", "0xECE3D5"
W, H = 1920, 1080

MOCK = {
    "01": "map",
    "02": "kitchen",
    "03": "phones",
    "06": "quiet",
    "07": "thumbs",
}  # set shot -> assets/mock


def mock_picture(picture: str) -> str:
    """shots.py's picture -> this tool's: paint:<mock asset>, screen:<label>|<under>, or close."""
    kind, *rest = picture.split("|")
    if kind == "blender":
        return f"paint:{MOCK[rest[0]]}"
    if kind == "screen":
        return f"screen:{rest[0]}  {rest[1]}" + (f"|{rest[2]}" if len(rest) > 2 else "")
    return "close"


SHOTS = [(sid, sec, mock_picture(pic), words) for sid, sec, pic, words in SHOTS]


CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def still(i: int, sid: str, picture: str, words: str) -> None:
    """Lay the still out as HTML in Patrick Hand; screenshot it with headless Chrome."""
    check(words)
    OUT.mkdir(parents=True, exist_ok=True)
    cap = html.escape(words).replace("\n", "<br>")
    if picture.startswith("paint:"):
        body = f'<img class="bg" src="{HERE}/assets/mock/{picture[6:]}.png">' + (
            f'<div class="w" style="top:150px">{cap}</div>' if words else ""
        )
    elif picture.startswith("screen:"):
        label, _, under = picture[7:].partition("|")
        label = html.escape(label).replace("  ", "<br>")
        body = (
            f'<div class="table"></div><div class="card">{label}</div>'
            + (
                f'<div class="w" style="top:1045px;left:1410px;font-size:44px">'
                f"{html.escape(under)}</div>"
                if under
                else ""
            )
            + f'<div class="w" style="top:500px;left:560px">{cap}</div>'
        )
    else:  # the close: painted kettle, the name, the address, then one line at a time
        body = (
            f'<img class="k" src="{HERE}/assets/kettle.png">'
            '<div class="w" style="top:560px;font-size:130px">Kettle</div>'
            '<div class="w" style="top:670px;font-size:64px">heykettle.com</div>'
            + (f'<div class="w" style="top:860px">{cap}</div>' if words else "")
        )
    page = f"""<!doctype html><meta charset="utf-8"><style>
@font-face {{ font-family: P; src: url("file://{FONT}"); }}
html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: #{PAPER[2:]}; }}
.bg {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
.w {{ position: absolute; left: 50%; transform: translate(-50%, -50%);
      font: 80px/1.15 P; color: #{INK[2:]};
      text-align: center; white-space: nowrap; }}
.table {{ position: absolute; left: 0; right: 0; top: 820px; bottom: 0; background: #{TABLE[2:]}; }}
.card {{ position: absolute; left: 1150px; top: 70px; width: 520px; height: 940px;
         border-radius: 48px;
         background: #{GREY[2:]}; display: flex; align-items: center; justify-content: center;
         text-align: center; font: 48px/1.3 P; color: #6E6860;
         box-shadow: 8px 14px 24px rgba(64,60,54,.18); }}
.k {{ position: absolute; left: 50%; top: 90px; height: 360px; transform: translateX(-50%); }}
</style>{body}"""
    src = OUT / f".{sid}.html"
    src.write_text(page, encoding="utf-8")
    subprocess.run(
        [
            CHROME,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--allow-file-access-from-files",
            f"--window-size={W},{H}",
            "--virtual-time-budget=3000",
            f"--screenshot={OUT / f'{sid}.png'}",
            f"file://{src}",
        ],
        check=True,
        capture_output=True,
    )
    src.unlink()


def sheet() -> None:
    ins, parts = [], []
    for n, (sid, *_rest) in enumerate(SHOTS):
        ins += ["-i", str(OUT / f"{sid}.png")]
        parts.append(f"[{n}]scale=480:270,pad=490:280:5:5:color={PAPER}[s{n}]")
    cols, n = 4, len(SHOTS)
    rows = -(-n // cols)
    for k in range(n, cols * rows):  # pad the grid with paper
        ins += ["-f", "lavfi", "-i", f"color=c={PAPER}:s=490x280"]
        parts.append(f"[{k}]null[s{k}]")
    layout = "|".join(f"{(k % cols) * 490}_{(k // cols) * 280}" for k in range(cols * rows))
    graph = (
        ";".join(parts)
        + ";"
        + "".join(f"[s{k}]" for k in range(cols * rows))
        + f"xstack=inputs={cols * rows}:layout={layout}"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            *ins,
            "-filter_complex",
            graph,
            "-frames:v",
            "1",
            str(HERE / "out/contact-sheet.png"),
        ],
        check=True,
    )


def rough_cut() -> float:
    lst = OUT / "cut.txt"
    lines = [f"file '{sid}.png'\nduration {sec}" for sid, sec, *_ in SHOTS]
    lst.write_text("\n".join(lines) + f"\nfile '{SHOTS[-1][0]}.png'\n")
    total = sum(s[1] for s in SHOTS)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-i",
            str(lst),
            "-vf",
            f"fps=30,format=yuv420p,fade=in:d=0.5,fade=out:st={total - 0.8}:d=0.8",
            "-t",
            str(total),
            "-c:v",
            "libx264",
            "-crf",
            "20",
            "-an",
            "-movflags",
            "+faststart",
            str(HERE / "out/rough-cut.mp4"),
        ],
        check=True,
    )
    return total


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for i, (sid, _sec, picture, words) in enumerate(SHOTS):
        if not only or sid in only:
            still(i, sid, picture, words)
    sheet()
    print(f"rough cut {rough_cut():.1f} s -> out/rough-cut.mp4; sheet -> out/contact-sheet.png")
