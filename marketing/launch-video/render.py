#!/usr/bin/env python3
"""Build the Kettle launch video from scratch: python3 render.py

1. Blender renders any painted shot whose frames are missing (out/frames/<shot>/), and the plate.
2. Headless Chrome draws every caption, the name and address, and the grey placeholder cards as
   transparent PNGs in Patrick Hand (this ffmpeg has no drawtext).
3. ffmpeg composes one segment per row of shots.py, in 16:9 and 9:16, and joins them.
Out: out/kettle-launch-16x9.mp4 (1920x1080) and out/kettle-launch-9x16.mp4 (1080x1920), 30 fps,
H.264 yuv420p, silent unless shots.MUSIC_TRACK exists; a still per shot in out/shots/.
A recording saved as recordings/<R>.mp4 replaces its grey card on the next run, cut per
shots.RECORDINGS.
Flags: --frames-only (Blender only), --no-blender (fail if frames are missing),
--preview <name> (16:9 only, to out/<name>), --vertical (the 9:16 cut only), --no-music (the
voice-only version).
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from pathlib import Path

from shots import (
    CAPTION_LAYOUT,
    CAPTION_OUT_EARLY,
    DISSOLVES,
    MUSIC_START,
    MUSIC_TRACK,
    MUSIC_UNDER,
    OUT_NAME,
    RECORDINGS,
    SFX,
    SHOTS,
    VOICE,
    VOICE_LEAD,
    VOICE_TAKE,
    ZOOM,
    check,
)

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
FONT = HERE.parents[1] / "tools/social/fonts/PatrickHand-Regular.ttf"
BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAPER, INK, MUTED, GREY = "#F7F1E8", "#403C36", "#6E6860", "#C9C4BC"
FPS = 30
READY: dict[str, Path | None] = {}  # recording -> its prepared file, filled by main()
FIRST_CLOSE = next((r[0] for r in SHOTS if r[2].startswith("close")), None)  # name fades in here
ICON = HERE.parents[1] / "webapp/public/icon-512.png"  # the Kettle app's home-screen icon
# 9:16 reframes each painted shot: a window of the 1920x1080 frame, keyed by set-shot frame as
# (frame, centre x, centre y, width), eased between keys, scaled to 1080 wide and feathered onto the
# paper under the caption. The window follows the subject (v7, founder: keep it fully in frame).
REFRAME_9X16: dict[str, list[tuple[int, int, int, int]]] = {
    "01": [(1, 970, 540, 1620)],  # the apartments and the house, both
    # The two phones through the arc, then the push-in's end: the green phone and its note.
    "03": [(1, 965, 540, 1080), (204, 965, 540, 1080), (234, 1350, 540, 1140)],
    # Wide: the phone, the thumbs up and the kettle; close: the phone and its message.
    "07c": [(20, 1240, 540, 1140), (50, 770, 540, 1080), (140, 770, 540, 1080),
            (172, 1240, 540, 1140)],
    # The feature videos: the phone and every bubble around it.
    "sc": [(1, 950, 620, 1480)],
}  # fmt: skip
SCENE_Y_9X16 = 1100  # the painted band's centre in 9:16, below the caption
SAFE_TOP_9X16 = 231  # 12% of 1920: TikTok, Reels and Shorts put their buttons above and below
SET_SCRIPT = {
    "10b": "kitchen.py",
    "01": "map.py",
    "02": "kitchen.py",
    "06": "kitchen.py",
    "07": "kitchen.py",
    "07c": "kitchen.py",
    "10a": "kitchen.py",
    "10c": "kitchen.py",
    "sc": "phones.py",
    "03": "phones.py",
    "15": "close.py",
}
X264 = [
    "-c:v",
    "libx264",
    "-crf",
    "18",
    "-preset",
    "medium",
    "-pix_fmt",
    "yuv420p",
    # Every segment tagged limited range: the iPhone recordings come in tagged full range, and a
    # cut that opens on one (Care Compare) would otherwise tag the whole film so. The launch
    # finals already played the recordings' values as limited range; this only makes it explicit.
    "-color_range",
    "tv",
    "-r",
    str(FPS),
    "-an",
    "-fflags",
    "+bitexact",
    "-flags",
    "+bitexact",
]
# Layout, per format: where the words, the screen and the close's name go.
FMT = {
    "16x9": {"W": 1920, "H": 1080, "paint_cap": 150, "screen_cap": (560, 500),
             "card": (1150, 70, 520, 940), "under": 1045, "brand": (620, 725), "close_cap": 880,
             "cap_px": 80, "wrap": False},
    "9x16": {"W": 1080, "H": 1920, "paint_cap": 340, "screen_cap": (540, 360),
             "card": (40, 500, 1000, 1180), "under": None, "brand": (1010, 1110), "close_cap": 1330,
             "cap_px": 76, "wrap": True},
}  # fmt: skip


def run(cmd: list[str], quiet: bool = False) -> None:
    subprocess.run(cmd, check=True, capture_output=quiet)


def frames_needed() -> dict[str, int]:
    """Set shot -> frames the cut plays from it (consecutive rows play on through its frames)."""
    need: dict[str, int] = {}
    for i, (sid, sec, pic, _w) in enumerate(SHOTS):
        kind, *rest = pic.split("|")
        if kind in ("blender", "close"):
            after = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else None
            run_on = DISSOLVES.get((sid, after), 0.0)  # it plays on under the next shot
            first = int(rest[1]) - 1 if len(rest) > 1 else 0
            need[rest[0]] = max(need.get(rest[0], first), first) + round((sec + run_on) * FPS)
    return need


def ensure_frames(allow: bool) -> None:
    for shot, n in frames_needed().items():
        folder = OUT / "frames" / shot
        have = len(list(folder.glob("*.png"))) if folder.exists() else 0
        if have >= n:
            continue
        if not allow:
            raise SystemExit(
                f"out/frames/{shot} has {have} of {n} frames; run without --no-blender"
            )
        print(f"blender: {shot} ({n} frames)")
        run([BLENDER, "-b", "-P", str(HERE / "blender" / SET_SCRIPT[shot]), "--", shot, "frames"])
    if not (OUT / "frames/plate.png").exists():
        if not allow:
            raise SystemExit("out/frames/plate.png is missing; run without --no-blender")
        run(
            [
                BLENDER,
                "-b",
                "-P",
                str(HERE / "blender/close.py"),
                "--",
                "plate",
                "still",
                "1",
                "out/frames/plate.png",
            ]
        )


# ---------------------------------------------------------------- overlays (headless Chrome)


def overlay_png(body: str, w: int, h: int, out: Path) -> Path:
    """A transparent w x h PNG of `body`. Every text element is Patrick Hand in ink."""
    page = f"""<!doctype html><meta charset="utf-8"><style>
@font-face {{ font-family: P; src: url("file://{FONT}"); }}
html, body {{ margin: 0; width: {w}px; height: {h}px; overflow: hidden; background: transparent; }}
.t {{ position: absolute; transform: translate(-50%, -50%); font-family: P; color: {INK};
      text-align: center; }}
.card {{ position: absolute; border-radius: 48px; background: {GREY};
         box-shadow: 8px 14px 26px rgba(64,60,54,.2);
         display: flex; align-items: center; justify-content: center; text-align: center;
         font: 46px/1.3 P; color: {MUTED}; }}
.shadow {{ position: absolute; border-radius: 44px; box-shadow: 8px 14px 26px rgba(64,60,54,.24); }}
</style>{body}"""
    src = out.with_suffix(".html")
    src.write_text(page, encoding="utf-8")
    run(
        [
            CHROME,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--allow-file-access-from-files",
            "--default-background-color=00000000",
            f"--window-size={w},{h}",
            "--virtual-time-budget=3000",
            f"--screenshot={out}",
            f"file://{src}",
        ],
        quiet=True,
    )  # Chrome chatters on stderr
    src.unlink()
    return out


def text(words: str, x: int, y: int, px: int, wrap: bool, max_w: int) -> str:
    lines = html.escape(words).replace("\n", " " if wrap else "<br>")
    flow = f"width: {max_w}px; text-wrap: balance;" if wrap else "white-space: nowrap;"
    style = f"left:{x}px;top:{y}px;font-size:{px}px;line-height:1.15;{flow}"
    return f'<div class="t" style="{style}">{lines}</div>'


def caption(sid: str, pic: str, words: str, f: dict, fmt: str) -> Path | None:
    if not words:
        return None
    kind = pic.split("|")[0]
    W, H, px, wrap = f["W"], f["H"], f["cap_px"], f["wrap"]
    if kind == "card":
        return None  # the title card lays out its own words (card_png)
    if CAPTION_LAYOUT.get(sid) == "brand":
        return overlay_png(
            brand_caption(words, f, fmt), W, H, OUT / "overlays" / f"{fmt}-cap-{sid}.png"
        )
    if kind == "screen":
        x, y = f["screen_cap"]
    elif kind == "close":
        x, y = W // 2, f["close_cap"]
    else:
        x, y = W // 2, f["paint_cap"]
    if wrap:  # a caption that wraps to three lines moves down, clear of the top 12% (9:16)
        lines = -(-int(0.42 * px * len(words)) // (W - 140))  # Patrick Hand, about 0.42 em a letter
        y = max(y, int(SAFE_TOP_9X16 + 10 + lines * px * 1.15 / 2))
    return overlay_png(
        text(words, x, y, px, wrap, W - 140), W, H, OUT / "overlays" / f"{fmt}-cap-{sid}.png"
    )


# The still cards (founder, 2026-09-27): the Kettle app icon, never the painted kettle; Patrick
# Hand in ink on paper; one centred stack. Each layout is (item, size in px, space above), where an
# item is "icon" or the index of a line of the row's words. 9:16 has its own sizes: lines wrap
# there, so they can be larger (v7, founder: readable on a phone).
CARDS = {
    "16x9": {
        "intro": [("icon", 250, 0), (0, 140, 44), (1, 72, 22)],
        "more": [(0, 100, 0), (1, 64, 44), (2, 64, 18)],
        "end": [("icon", 190, 0), (0, 120, 30), (1, 60, 6), (2, 78, 52), (3, 62, 20)],
    },
    "9x16": {
        "intro": [("icon", 225, 0), (0, 126, 40), (1, 72, 20)],
        "more": [(0, 104, 0), (1, 76, 64), (2, 76, 36)],
        "end": [("icon", 220, 0), (0, 140, 34), (1, 72, 8), (2, 84, 64), (3, 72, 28)],
    },
}


def card_png(f: dict, fmt: str, layout: str, words: str) -> Path:
    """A still card: the layout's items stacked and centred, the paper above equal to the paper
    below. Long lines wrap in 9:16. The icon is the app's own (webapp/public/icon-512.png), drawn
    as a home-screen icon: rounded corners and a soft shadow, so its square reads on the paper."""
    W, H = f["W"], f["H"]
    lines = words.split("\n")
    max_w = W - 160
    items = []  # (html maker, height)
    for item, size, gap in CARDS[fmt][layout]:
        if item == "icon":
            items.append(("icon", size, gap))
        else:
            n_lines = 1 if fmt == "16x9" else -(-int(0.36 * size * len(lines[item])) // max_w)
            items.append((lines[item], size * 1.15 * n_lines, gap, size))
    total = sum(it[1] + it[2] for it in items)
    y = (H - total) / 2
    body = f'<div style="position:absolute;inset:0;background:{PAPER}"></div>'
    for it in items:
        y += it[2]
        if it[0] == "icon":
            side = it[1]
            shadow = f"0 {side * 0.04}px {side * 0.12}px rgba(64,60,54,.22)"
            body += (f'<img src="file://{ICON}" style="position:absolute;left:{W / 2 - side / 2}px;'
                     f"top:{y}px;width:{side}px;height:{side}px;border-radius:{side * 0.2237}px;"
                     f'box-shadow:{shadow}">')  # fmt: skip
        else:
            body += text(it[0], W // 2, int(y + it[1] / 2), int(it[3]), fmt != "16x9", max_w)
        y += it[1]
    return overlay_png(body, W, H, OUT / "overlays" / f"{fmt}-card-{layout}.png")


def brand_caption(words: str, f: dict, fmt: str) -> str:
    """Shot 2's caption over the phones: the app icon and "Kettle" side by side, the line beneath,
    in the paper band above the phones."""
    W = f["W"]
    name, line = words.split("\n", 1)
    k = 1.0 if fmt == "16x9" else 0.9
    icon, name_px, line_px = 128 * k, 112 * k, 64 if fmt == "16x9" else 68
    row_y, line_y = (150, 282) if fmt == "16x9" else (330, 470)
    name_w = 0.42 * name_px * len(name)  # Patrick Hand runs about 0.42 em a letter
    gap = 28 * k
    left = W / 2 - (icon + gap + name_w) / 2
    shadow = f"0 {icon * 0.04}px {icon * 0.12}px rgba(64,60,54,.22)"
    return (
        f'<img src="file://{ICON}" style="position:absolute;left:{left}px;top:{row_y - icon / 2}px;'
        f'width:{icon}px;height:{icon}px;border-radius:{icon * 0.2237}px;box-shadow:{shadow}">'
        + text(name, int(left + icon + gap + name_w / 2), row_y, int(name_px), False, W)
        + text(line, W // 2, line_y, int(line_px), fmt != "16x9", W - 160)
    )


def brand(f: dict, fmt: str) -> Path:
    W, (y1, y2) = f["W"], f["brand"]
    body = text("Kettle", W // 2, y1, 130, False, W) + text(
        "heykettle.com", W // 2, y2, 64, False, W
    )
    return overlay_png(body, W, f["H"], OUT / "overlays" / f"{fmt}-brand.png")


def screen_dressing(
    rec: str,
    label: str,
    under: str,
    f: dict,
    fmt: str,
    live: tuple[int, int] | None,
    rect: tuple[int, int, int, int],
) -> Path:
    """The grey card (no recording yet) or the recording's shadow, and the line under the screen."""
    x, y, w, h = rect
    if live:  # the recording's own box, centred where the card sits
        rw, rh = live
        box = f"left:{x + (w - rw) // 2}px;top:{y + (h - rh) // 2}px;width:{rw}px;height:{rh}px"
        body = f'<div class="shadow" style="{box}"></div>'
    else:
        body = (
            f'<div class="card" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">'
            f"{html.escape(rec)}<br>{html.escape(label)}<br>placeholder</div>"
        )
    if under and f["under"]:  # 9:16 has no room under the screen, above the platforms' buttons
        body += text(under, x + w // 2, f["under"], 44, False, f["W"])
    return overlay_png(
        body,
        f["W"],
        f["H"],
        OUT / "overlays" / f"{fmt}-screen-{rec}-{'live' if live else 'card'}.png",
    )


# ---------------------------------------------------------------- segments (ffmpeg)


def source(rec: str) -> Path | None:
    """recordings/<rec>.mp4 or .mov, any case (the iPhone writes R2.MP4)."""
    for p in sorted((HERE / "recordings").glob(f"{rec}.*")):
        if p.suffix.lower() in (".mp4", ".mov"):
            return p
    return None


def prepared(rec: str) -> Path | None:
    """The recording as it plays: cut, sped and cropped per shots.RECORDINGS, at 30 fps H.264,
    written to out/rec/<rec>.mp4. None until the founder's file exists."""
    edit = RECORDINGS.get(rec, {})
    src = source(edit.get("src", rec))
    if not src:
        return None
    out = OUT / "rec" / f"{rec}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    top, bottom = edit.get("crop", (0, None))
    left, right = edit.get("xcrop", (0, None))
    width = f"{right}-{left}" if right else f"iw-{left}"
    crop = f"crop={width}:{f'{bottom}-{top}' if bottom else f'ih-{top}'}:{left}:{top}"
    if "hold" in edit:
        t = edit["hold"]
        graph = f"[0:v]trim=start={t}:duration=0.05,setpts=PTS-STARTPTS,{crop},fps={FPS}[v]"
        if "zoom" in edit:  # a slow push in on the held frame: a w x h detail around (cx, cy)
            sec, s0, s1, cx, cy, w, h = edit["zoom"]
            src_w, src_h = recording_size(src, edit)
            p = f"clip(t/{sec},0,1)"
            z = f"({s0}+{s1 - s0}*(3*pow({p},2)-2*pow({p},3)))"
            graph = graph.replace(
                "[v]",
                f",tpad=stop_mode=clone:stop_duration={sec},"
                f"scale=w='trunc({src_w}*{z}/2)*2':h='trunc({src_h}*{z}/2)*2':eval=frame,"
                f"crop={w}:{h}:x='clip({cx}*{z}-{w / 2},0,{src_w}*{z}-{w})'"
                f":y='clip({cy}*{z}-{h / 2},0,{src_h}*{z}-{h})'[v]",
            )
    else:
        pieces = edit.get("cuts", [(0, None, 1)])
        parts = []
        for k, (a, b, speed, *extra) in enumerate(pieces):
            end = f":end={b}" if b is not None else ""
            piece = f"[0:v]trim=start={a}{end},setpts=(PTS-STARTPTS)/{speed},fps={FPS}"
            if extra and "mask" in extra[0]:  # cover rows m0..m1 with blank page from `sample`
                m0, m1, sample = extra[0]["mask"]
                parts.append(f"{piece},split[b{k}][c{k}]")
                parts.append(f"[c{k}]crop=iw:50:0:{sample},scale=iw:{m1 - m0}[patch{k}]")
                parts.append(f"[b{k}][patch{k}]overlay=0:{m0}[p{k}]")
            else:
                parts.append(f"{piece}[p{k}]")
        joined = "".join(f"[p{k}]" for k in range(len(pieces)))
        hold = "tpad=stop_mode=clone:stop_duration=30"  # a later shot may start past the end
        graph = ";".join(parts) + f";{joined}concat=n={len(pieces)}:v=1:a=0,{crop},{hold}[v]"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-filter_complex", graph,
         "-map", "[v]", *X264, str(out)])  # fmt: skip
    return out


def recording_size(src: Path, edit: dict) -> tuple[int, int]:
    """The recording's size after its shots.RECORDINGS crop and xcrop."""
    info = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "json", str(src)],
        check=True, capture_output=True, text=True).stdout)["streams"][0]  # fmt: skip
    top, bottom = edit.get("crop", (0, None))
    left, right = edit.get("xcrop", (0, None))
    return (right or info["width"]) - left, (bottom or info["height"]) - top


HOME_SCREEN_Y = (
    190  # mean brightness: Kettle and Claude screens sit at 219+, the home screen at 113
)


def refuse_home_screen(rec: str, path: Path, seconds: float) -> None:
    """Stop the build if any frame the cut uses from `rec` is dark enough to be the iPhone home
    screen or the app switcher (founder: no personal apps anywhere in either cut)."""
    probe_out = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-t", f"{seconds:.3f}", "-i", str(path), "-vf",
         "scale=120:-2,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
         "-f", "null", "-"],
        check=True, capture_output=True, text=True,
    ).stdout  # fmt: skip
    dark = [i for i, y in enumerate(re.findall(r"YAVG=([0-9.]+)", probe_out))
            if float(y) < HOME_SCREEN_Y]  # fmt: skip
    if dark:
        raise SystemExit(
            f"{rec}: {len(dark)} frame(s) look like the home screen or app switcher, first at "
            f"{dark[0] / FPS:.2f} s of the cut; trim it in shots.RECORDINGS"
        )


def screen_rect(rec: str, f: dict, fmt: str) -> tuple[int, int, int, int]:
    """Where a recording sits: its own box in 16:9 when shots.RECORDINGS gives one (a zoom),
    otherwise the phone-sized card."""
    box = RECORDINGS.get(rec, {}).get("box")
    return tuple(box) if box and fmt == "16x9" else f["card"]


def recording_box(path: Path, rect: tuple[int, int, int, int]) -> tuple[int, int]:
    info = json.loads(
        subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "json",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )["streams"][0]
    _, _, bw, bh = rect
    scale = min(bw / info["width"], bh / info["height"])
    return int(info["width"] * scale) // 2 * 2, int(info["height"] * scale) // 2 * 2


def fade(
    label_in: str, label_out: str, dur: float, fade_in: bool = True, fade_out: bool = True
) -> str:
    """Caption fades in over 0.4 s and out over the last 0.3 s of its beat."""
    parts = ["format=rgba"]
    if fade_in:
        parts.append("fade=in:st=0:d=0.4:alpha=1")
    if fade_out:
        parts.append(f"fade=out:st={dur - 0.3:.2f}:d=0.3:alpha=1")
    return f"[{label_in}]{','.join(parts)}[{label_out}]"


def reframe(shot: str, start: int) -> tuple[str, int]:
    """The 9:16 window for a set shot whose segment starts at frame `start`: scale and crop filters
    and the band's height. Width and centre ease between keys (REFRAME_9X16); the crop offset comes
    from the scale expression, since crop reads the frame's size only once."""
    keys = REFRAME_9X16.get(shot, [(1, 960, 540, 1080)])

    def eased(i: int) -> str:
        expr = str(keys[0][i])
        for j in range(1, len(keys)):
            a, b = keys[j - 1], keys[j]
            if b[i] != a[i]:
                p = f"clip((n+{start}-{a[0]})/{b[0] - a[0]},0,1)"
                expr += f"+{b[i] - a[i]}*(3*pow({p},2)-2*pow({p},3))"
        return f"({expr})"

    k = f"(1080/{eased(3)})"
    band = min(1080, 1080 * 1080 // max(key[3] for key in keys)) // 2 * 2
    grow = f"scale=w='trunc(1920*{k}/2)*2':h='trunc(1080*{k}/2)*2':eval=frame"
    x = f"clip({eased(1)}*{k}-540,0,trunc(1920*{k}/2)*2-1080)"
    y = f"clip({eased(2)}*{k}-{band / 2},0,trunc(1080*{k}/2)*2-{band})"
    return f"{grow},crop=1080:{band}:x='{x}':y='{y}'", band


def feather() -> str:
    """Alpha fading the square scene into the paper over 90 px, top and bottom (9:16 only)."""
    return (
        "format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':"
        "a='255*min(1,min(Y,H-1-Y)/90)'"
    )


def segment(i: int, row, offsets: dict[str, int], fmt: str) -> Path:
    sid, sec, pic, words = row
    f = FMT[fmt]
    W, H = f["W"], f["H"]
    after = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else None
    n = round((sec + DISSOLVES.get((sid, after), 0.0)) * FPS)  # runs on under a dissolve
    kind, *rest = pic.split("|")
    out = OUT / "seg" / fmt / f"{i:02d}-{sid}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    inputs: list[str] = []
    graph: list[str] = []
    loop = ["-loop", "1", "-framerate", str(FPS), "-i"]

    if kind in ("blender", "close"):
        shot = rest[0]
        first = int(rest[1]) if len(rest) > 1 else 1  # "blender|07|8": start at frame 8
        start = offsets.get(shot, first - 1) + 1
        offsets[shot] = start - 1 + n
        inputs += [
            "-framerate",
            str(FPS),
            "-start_number",
            str(start),
            "-i",
            str(OUT / "frames" / shot / "%04d.png"),
        ]
        if fmt == "16x9":
            graph.append("[0]null[bg]")
        else:  # the shot's moving window (REFRAME_9X16), feathered onto paper
            window, band = reframe(shot, start)
            graph.append(f"color=c={PAPER}:s={W}x{H}:r={FPS}[paper]")
            graph.append(f"[0]{window},{feather()}[sq]")
            graph.append(f"[paper][sq]overlay=0:{SCENE_Y_9X16 - band // 2}:shortest=1[bg]")
        last = "bg"
        if kind == "close":
            inputs += loop + [str(brand(f, fmt))]
    elif kind == "card":  # a still paper card (the dissolves are its only motion)
        inputs += loop + [str(card_png(f, fmt, rest[0], words))]
        graph.append("[0]null[bg]")
        last = "bg"
    else:
        rec, label = rest[0], rest[1]
        under = rest[2] if len(rest) > 2 else ""
        path = READY.get(rec)
        rect = screen_rect(rec, f, fmt)
        live = recording_box(path, rect) if path else None
        if fmt == "16x9":
            inputs += loop + [str(OUT / "frames/plate.png")]
            graph.append("[0]null[bg]")
        else:
            inputs += ["-f", "lavfi", "-i", f"color=c={PAPER}:s={W}x{H}:r={FPS}"]
            graph.append("[0]null[bg]")
        inputs += loop + [str(screen_dressing(rec, label, under, f, fmt, live, rect))]
        graph.append("[bg][1]overlay=0:0[dressed]")
        last = "dressed"
        if live:  # the real screen, rounded corners, played from its offset
            start = offsets.get(rec, 0)
            offsets[rec] = start + n
            rw, rh = live
            x, y, bw, bh = rect
            r = 44
            inputs += ["-ss", f"{start / FPS:.3f}", "-i", str(path)]
            graph.append(
                f"[2]fps={FPS},scale={rw}:{rh},tpad=stop_mode=clone:stop_duration={sec},format=yuva420p,"
                f"geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':"
                f"a='if(gt(abs(X-W/2),W/2-{r})*gt(abs(Y-H/2),H/2-{r}),"
                f"if(lte(hypot(abs(X-W/2)-(W/2-{r}),abs(Y-H/2)-(H/2-{r})),{r}),255,0),255)'[rec]"
            )
            graph.append(f"[{last}][rec]overlay={x + (bw - rw) // 2}:{y + (bh - rh) // 2}[withrec]")
            last = "withrec"

    if fmt in ZOOM.get(sid, {}):  # a slow zoom: the focus point grows and glides to its place
        t0, s0, s1, fx, fy, tx, ty = ZOOM[sid][fmt]
        ramp = f"clip((t-{t0})/{sec - t0 - 0.3:.3f},0,1)"
        e = f"(3*pow({ramp},2)-2*pow({ramp},3))"  # eased 0 to 1
        z = f"({s0}+{s1 - s0}*{e})"
        grow = f"scale=w='trunc(iw*{z}/2)*2':h='trunc(ih*{z}/2)*2':eval=frame"
        # The focus point lands at (fx, fy) + ((tx, ty) - (fx, fy)) * e. The offset comes from the
        # zoom itself: crop reads the frame's size only once, not per frame.
        hold = f"crop={W}:{H}:x='{fx}*{z}-({fx}+{tx - fx}*{e})':y='{fy}*{z}-({fy}+{ty - fy}*{e})'"
        graph.append(f"[{last}]{grow},{hold}[zoomed]")
        last = "zoomed"
    idx = sum(1 for a in inputs if a == "-i")  # next input index
    if kind == "close":  # the name and address: fade in on the first close row only
        graph.append(
            f"[1]format=rgba{',fade=in:st=0:d=0.5:alpha=1' if sid == FIRST_CLOSE else ''}[brand]"
        )
        graph.append(f"[{last}][brand]overlay=0:0[branded]")
        last = "branded"
    cap = caption(sid, pic, words, f, fmt)
    if cap:
        inputs += loop + [str(cap)]
        before = SHOTS[i - 1][3] if i > 0 else None
        nxt = SHOTS[i + 1][3] if i + 1 < len(SHOTS) else None
        span = n / FPS  # a caption carried into the next row of its beat stays up to the cut
        if sid in CAPTION_OUT_EARLY:  # it leaves early, before a move (shot 2's push-in)
            span = sec - CAPTION_OUT_EARLY[sid]
        graph.append(fade(str(idx), "cap", span, fade_in=before != words, fade_out=nxt != words))
        graph.append(f"[{last}][cap]overlay=0:0[capped]")
        last = "capped"
    graph.append(f"[{last}]format=yuv420p[v]")
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            *inputs,
            "-filter_complex",
            ";".join(graph),
            "-map",
            "[v]",
            "-frames:v",
            str(n),
            *X264,
            str(out),
        ]
    )
    return out


def join(parts: list[Path], out: Path, total: float) -> None:
    """Join the segments: straight cuts, except a cross-dissolve at each shots.DISSOLVES join,
    where the outgoing segment (rendered that much longer) runs on under the incoming one."""
    ins: list[str] = []
    for p in parts:
        ins += ["-i", str(p)]
    graph, label, clock = [], "0:v", 0.0
    for k, row in enumerate(SHOTS):
        if k == 0:
            clock = row[1]
            continue
        cross = DISSOLVES.get((SHOTS[k - 1][0], row[0]), 0.0)
        if cross:  # the incoming shot starts on its cut; the outgoing one fades out over it
            graph.append(
                f"[{label}][{k}:v]xfade=transition=fade:duration={cross}:offset={clock:.3f}[j{k}]"
            )
        else:
            graph.append(f"[{label}][{k}:v]concat=n=2:v=1:a=0[j{k}]")
        label, clock = f"j{k}", clock + row[1]
    fades = f"fade=in:st=0:d=0.5:color={PAPER},fade=out:st={total - 0.8:.2f}:d=0.8:color={PAPER}"
    graph.append(f"[{label}]{fades}[v]")
    music = [HERE / MUSIC_TRACK] if (HERE / MUSIC_TRACK).exists() else []
    if "--no-music" in sys.argv:  # the voice-only version, for comparing
        music = []
    take = HERE / VOICE_TAKE
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *ins]
    maps, enc, n_in = ["-map", "[v]"], X264, len(parts)
    voice = None
    if take.exists():
        voice = voice_graph(graph, n_in, total)
        cmd += ["-i", str(take)]
        n_in += 1
    bed = None
    if music:  # the founder's track, at one steady level under the voice (shots.MUSIC_*)
        cmd += ["-i", str(music[0])]
        gain = music_gain(music[0], total) if voice else "pow(10,-16/20)"
        graph.append(
            f"[{n_in}:a]atrim={MUSIC_START}:{MUSIC_START + total:.3f},asetpts=PTS-STARTPTS,"
            f"volume='{gain}':eval=frame,afade=in:st=0:d=0.5,"
            f"afade=out:st={total - 2:.2f}:d=2,apad,atrim=0:{total:.3f}[bed]"
        )
        bed = "bed"
    fx = []  # the sound effects, each at its moment in its shot (shots.SFX)
    starts, clock = {}, 0.0
    for sid, sec, *_ in SHOTS:
        starts[sid], clock = clock, clock + sec
    for sid, sounds in SFX.items():
        for path, at, gain in sounds:
            cmd += ["-i", str(HERE / path)]
            lab = f"sfx{len(fx)}"
            graph.append(f"[{n_in}:a]aresample=44100,volume={gain}dB,"
                         f"adelay={int((starts[sid] + at) * 1000)}:all=1,apad,"
                         f"atrim=0:{total:.3f}[{lab}]")  # fmt: skip
            fx.append(lab)
            n_in += 1
    if voice or bed:
        mix = [x for x in (voice, bed) if x] + fx
        joined = "".join(f"[{x}]" for x in mix)
        mixed = f"{joined}amix=inputs={len(mix)}:normalize=0," if len(mix) > 1 else f"{joined}"
        graph.append(f"{mixed}loudnorm=I=-16:TP=-1.3:LRA=11,aresample=48000[a]")
        maps = ["-map", "[v]", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
        enc = [a for a in X264 if a != "-an"]
    run([*cmd, "-filter_complex", ";".join(graph), *maps, *enc, "-t", f"{total:.3f}",
         "-movflags", "+faststart", str(out)])  # fmt: skip


def normalize(path: Path, length: float) -> None:
    """Second loudness pass: measure the finished mix, raise it to -16 LUFS integrated with a plain
    gain, and catch the few peaks that gain would push past the founder's -1 dBTP with a fast
    limiter 0.8 dB lower (the AAC encode adds a few tenths), repeating until within 0.1 LU. A
    loudness filter's own peak limit stopped short instead (the v4 music mix landed at -17.0).
    Remuxes the audio, padded to `length` s so the picture keeps its full length."""
    ceiling = 10 ** (-1.8 / 20)
    for _ in range(4):  # the limiter takes back a little each pass; stop within 0.1 LU
        have = lufs(["-i", str(path), "-vn", "-af", "ebur128"])
        if abs(have + 16) <= 0.1:
            break
        af = (f"volume={-16 - have:.2f}dB,alimiter=limit={ceiling:.4f}:attack=2:release=60:"
              f"level=disabled,aresample=48000,apad,atrim=0:{length:.3f}")  # fmt: skip
        tmp = path.with_suffix(".norm.mp4")
        run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(path),
                "-map",
                "0:v",
                "-map",
                "0:a",
                "-c:v",
                "copy",
                "-af",
                af,
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-t",
                f"{length:.3f}",
                "-movflags",
                "+faststart",
                str(tmp),
            ]
        )  # fmt: skip (padded, so the picture keeps its length)
        tmp.replace(path)


def lufs(args: list[str]) -> float:
    """Integrated loudness of whatever `args` (ffmpeg inputs and an audio filter) produce."""
    err = subprocess.run(["ffmpeg", "-hide_banner", *args, "-f", "null", "-"],
                         check=True, capture_output=True, text=True).stderr  # fmt: skip
    return float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", err)[-1])


def music_gain(track: Path, total: float) -> str:
    """The music's gain: one steady level, MUSIC_UNDER dB below the voice's speaking level (the
    founder: no swells in the gaps)."""
    pieces = [p for v in VOICE.values() for p in v]
    chain = "".join(
        f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[p{k}];" for k, (a, b) in enumerate(pieces)
    )
    chain += "".join(f"[p{k}]" for k in range(len(pieces)))
    voice_lufs = lufs(["-i", str(HERE / VOICE_TAKE), "-filter_complex",
                       f"{chain}concat=n={len(pieces)}:v=0:a=1,ebur128"])  # fmt: skip
    music_lufs = lufs(["-ss", str(MUSIC_START), "-t", f"{total:.3f}", "-i", str(track),
                       "-af", "ebur128"])  # fmt: skip
    gain = voice_lufs - MUSIC_UNDER - music_lufs
    print(f"music: voice {voice_lufs} LUFS, music {music_lufs} LUFS, steady gain {gain:.1f} dB")
    return f"pow(10,{gain:.2f}/20)"


def voice_graph(graph: list[str], first_in: int, total: float) -> str:
    """Lay each voice line (a span of the take, natural pauses kept) at its shot's start plus
    VOICE_LEAD; silence everywhere else. Appends to `graph`; returns the output label."""
    starts, clock = {}, 0.0
    for sid, sec, *_ in SHOTS:
        starts[sid], clock = clock, clock + sec
    labels = []
    for sid, pieces in VOICE.items():
        at = starts[sid] + VOICE_LEAD
        for a, b in pieces:
            lab = f"vo{len(labels)}"
            graph.append(f"[{first_in}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,"
                         f"adelay={int(at * 1000)}:all=1[{lab}]")  # fmt: skip
            labels.append(lab)
            at += b - a
    joined = "".join(f"[{x}]" for x in labels)
    graph.append(f"{joined}amix=inputs={len(labels)}:normalize=0,apad,atrim=0:{total:.3f}[vo]")
    return "vo"


def stills(parts: list[Path], fmt: str) -> None:
    folder = OUT / "shots"
    folder.mkdir(exist_ok=True)
    for p, row in zip(parts, SHOTS):  # noqa: B905 (one part per shot; macOS python3 is 3.9)
        sid, sec = row[0], row[1]
        name = f"{sid}.png" if fmt == "16x9" else f"{sid}-9x16.png"
        run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-ss",
                f"{sec * 0.7:.2f}",
                "-i",
                str(p),
                "-frames:v",
                "1",
                str(folder / name),
            ]
        )


def probe(path: Path) -> str:
    return subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_name,width,height,pix_fmt,r_frame_rate:format=duration",
            "-of",
            "compact=p=0:nk=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def main() -> None:
    for row in SHOTS:
        check(row[3])
    ensure_frames(allow="--no-blender" not in sys.argv)
    if "--frames-only" in sys.argv:
        return
    (OUT / "overlays").mkdir(parents=True, exist_ok=True)
    used: dict[str, float] = {}
    for r in SHOTS:
        if r[2].startswith("screen"):
            used[r[2].split("|")[1]] = used.get(r[2].split("|")[1], 0) + r[1]
    for rec, seconds in sorted(used.items()):
        READY[rec] = prepared(rec)
        if READY[rec]:
            refuse_home_screen(rec, READY[rec], seconds)
    total = sum(r[1] for r in SHOTS)
    cuts = (("16x9", f"{OUT_NAME}-16x9.mp4"), ("9x16", f"{OUT_NAME}-9x16.mp4"))
    if "--vertical" in sys.argv:  # the 9:16 cut only
        cuts = cuts[1:]
    if "--voice-preview" in sys.argv:  # 16:9 only, under its own name
        cuts = (("16x9", "kettle-launch-voice-preview.mp4"),)
    if "--voice-music-preview" in sys.argv:
        cuts = (("16x9", "kettle-launch-voice-music-preview.mp4"),)
    if "--preview" in sys.argv:  # --preview <file name>: 16:9 only
        cuts = (("16x9", sys.argv[sys.argv.index("--preview") + 1]),)
    for fmt, name in cuts:
        offsets: dict[str, int] = {}
        parts = [segment(i, row, offsets, fmt) for i, row in enumerate(SHOTS)]
        join(parts, OUT / name, total)
        if (HERE / VOICE_TAKE).exists() or (HERE / MUSIC_TRACK).exists():
            normalize(OUT / name, total)
        stills(parts, fmt)
        print(f"{name}: {probe(OUT / name).strip()}")
    missing = sorted(rec for rec, path in READY.items() if path is None)
    if missing:
        print("placeholders still in the cut for:", ", ".join(missing))


if __name__ == "__main__":
    main()
