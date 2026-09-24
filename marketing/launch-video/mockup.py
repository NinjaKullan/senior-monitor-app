#!/usr/bin/env python3
"""Phase 3 mockups: one flat 1920x1080 still per shot, a contact sheet, and a silent rough cut.

Stdlib, headless Chrome (text) and ffmpeg (sheet, cut). Painted shots use the picked Gemini mockup in assets/mock/; screen shots are
grey cards named for the recording that replaces them. Words come from SHOTS, in Patrick Hand.
Usage (in this folder): python3 mockup.py [shot-id ...]   -> out/mock/<id>.png, out/contact-sheet.png,
out/rough-cut.mp4. With shot ids, only those stills are redrawn; the sheet and the cut always rebuild.
"""
from __future__ import annotations

import html
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT = HERE.parents[1] / "tools/social/fonts/PatrickHand-Regular.ttf"
OUT = HERE / "out/mock"
PAPER, INK, GREY, TABLE = "0xF7F1E8", "0x403C36", "0xC9C4BC", "0xECE3D5"
W, H = 1920, 1080

# (id, seconds, picture, words). picture: "paint:<asset>", "screen:<label>" or "close".
# Words: "\n" is a line break the caption keeps; screen captions sit in the left column.
SHOTS = [
    ("01", 4.2, "paint:map", "Mom and Dad live far away."),
    ("02", 4.7, "paint:kitchen", "Mom's phone does what it always does."),
    ("03", 5.2, "paint:phones", "iPhone or Android. The phone she already owns."),
    ("04", 5.7, "screen:R1  Morning note email", "Twice a day,\nthe family gets\na short note."),
    ("05", 5.7, "screen:R2  Today card", "The app shows when\nKettle last heard\nfrom her."),
    ("06", 4.7, "paint:quiet", "If a morning doesn't look like hers,"),
    ("07a", 3.7, "paint:thumbs", "Kettle asks her first, quietly."),
    ("07b", 5.2, "paint:thumbs", "The family hears only if she doesn't answer."),
    ("08", 5.2, "screen:R3  Memory", "Notes and replies,\nin the family's\nown words."),
    ("09", 5.2, "screen:R4  Who to call", "Who to call,\nif you can't\nreach her."),
    ("10", 5.0, "screen:R5  Family circle", "Brothers and sisters\nsee the same notes."),
    ("11a", 3.7, "screen:R6  Claude: the question", "Kettle works\ninside Claude, too."),
    ("11b", 3.7, "screen:R6  Claude: Kettle's answer", "Ask how Mom's\nmorning went."),
    ("12", 5.0, "screen:R7  Claude: add a note", "Or tell it something\nfor the family."),
    ("13", 4.2, "screen:R8  Memory: the new note", "It lands in the\nfamily's notes."),
    ("14a", 3.8, "screen:R9  Claude: Care Compare|Care Compare by HeyKettle", "Looking for\nhome health care?"),
    ("14b", 4.2, "screen:R9  Claude: Care Compare|Care Compare by HeyKettle", "Medicare's ratings,\nin plain words. Free."),
    ("15a", 1.0, "close", ""),
    ("15b", 4.7, "close", "For checking in, not checking up."),
    ("15c", 3.7, "close", "Now open to founding families."),
]
BANNED = ["monitor", "track", "alert", "alarm", "surveil", "elderly", "senior", "sensor", "detect",
          "dashboard", "score", "safe", "fine", "okay", "checked in", "ordinary", "signal", "ping",
          "shortcut", "automat", "api", "mcp", "loved one"]


def check(words: str) -> None:
    low = words.lower()
    bad = [b for b in BANNED if b in low] + [c for c in "—!’“”" if c in words]
    if bad:
        sys.exit(f"copy law: {bad} in {words!r}")


CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def still(i: int, sid: str, picture: str, words: str) -> None:
    """Lay the still out as HTML (Patrick Hand via @font-face) and screenshot it with headless Chrome."""
    check(words)
    OUT.mkdir(parents=True, exist_ok=True)
    cap = html.escape(words).replace("\n", "<br>")
    if picture.startswith("paint:"):
        body = (f'<img class="bg" src="{HERE}/assets/mock/{picture[6:]}.png">'
                + (f'<div class="w" style="top:150px">{cap}</div>' if words else ""))
    elif picture.startswith("screen:"):
        label, _, under = picture[7:].partition("|")
        label = html.escape(label).replace("  ", "<br>")
        body = (f'<div class="table"></div><div class="card">{label}</div>'
                + (f'<div class="w" style="top:1045px;left:1410px;font-size:44px">{html.escape(under)}</div>' if under else "")
                + f'<div class="w" style="top:500px;left:560px">{cap}</div>')
    else:  # the close: painted kettle, the name, the address, then one line at a time
        body = (f'<img class="k" src="{HERE}/assets/kettle.png">'
                '<div class="w" style="top:560px;font-size:130px">Kettle</div>'
                '<div class="w" style="top:670px;font-size:64px">heykettle.com</div>'
                + (f'<div class="w" style="top:860px">{cap}</div>' if words else ""))
    page = f"""<!doctype html><meta charset="utf-8"><style>
@font-face {{ font-family: P; src: url("file://{FONT}"); }}
html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: #{PAPER[2:]}; }}
.bg {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
.w {{ position: absolute; left: 50%; transform: translate(-50%, -50%); font: 80px/1.15 P; color: #{INK[2:]};
      text-align: center; white-space: nowrap; }}
.table {{ position: absolute; left: 0; right: 0; top: 820px; bottom: 0; background: #{TABLE[2:]}; }}
.card {{ position: absolute; left: 1150px; top: 70px; width: 520px; height: 940px; border-radius: 48px;
         background: #{GREY[2:]}; display: flex; align-items: center; justify-content: center;
         text-align: center; font: 48px/1.3 P; color: #6E6860; box-shadow: 8px 14px 24px rgba(64,60,54,.18); }}
.k {{ position: absolute; left: 50%; top: 90px; height: 360px; transform: translateX(-50%); }}
</style>{body}"""
    src = OUT / f".{sid}.html"
    src.write_text(page, encoding="utf-8")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    f"--window-size={W},{H}", "--virtual-time-budget=3000", f"--screenshot={OUT / f'{sid}.png'}",
                    f"file://{src}"], check=True, capture_output=True)
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
    graph = ";".join(parts) + ";" + "".join(f"[s{k}]" for k in range(cols * rows)) + f"xstack=inputs={cols * rows}:layout={layout}"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", graph, "-frames:v", "1",
                    str(HERE / "out/contact-sheet.png")], check=True)


def rough_cut() -> float:
    lst = OUT / "cut.txt"
    lines = [f"file '{sid}.png'\nduration {sec}" for sid, sec, *_ in SHOTS]
    lst.write_text("\n".join(lines) + f"\nfile '{SHOTS[-1][0]}.png'\n")
    total = sum(s[1] for s in SHOTS)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-i", str(lst),
                    "-vf", f"fps=30,format=yuv420p,fade=in:d=0.5,fade=out:st={total - 0.8}:d=0.8",
                    "-t", str(total), "-c:v", "libx264", "-crf", "20", "-an", "-movflags", "+faststart",
                    str(HERE / "out/rough-cut.mp4")], check=True)
    return total


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for i, (sid, _sec, picture, words) in enumerate(SHOTS):
        if not only or sid in only:
            still(i, sid, picture, words)
    sheet()
    print(f"rough cut {rough_cut():.1f} s -> out/rough-cut.mp4; sheet -> out/contact-sheet.png")
