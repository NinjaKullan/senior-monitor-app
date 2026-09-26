#!/usr/bin/env python3
"""Build the Kettle launch video from scratch: python3 render.py

1. Blender renders any painted shot whose frames are missing (out/frames/<shot>/), and the plate.
2. Headless Chrome draws every caption, the name and address, and the grey placeholder cards as
   transparent PNGs in Patrick Hand (this ffmpeg has no drawtext).
3. ffmpeg composes one segment per row of shots.py, in 16:9 and 9:16, and joins them.
Out: out/kettle-launch.mp4 (1920x1080) and out/kettle-launch-9x16.mp4 (1080x1920), 30 fps, H.264
yuv420p, silent unless audio/music.* exists; a still per shot in out/shots/.
A recording saved as recordings/<R>.mp4 replaces its grey card on the next run, cut per
shots.RECORDINGS.
Flags: --frames-only (Blender only), --no-blender (fail if frames are missing).
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from pathlib import Path

from shots import RECORDINGS, SHOTS, check

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
FONT = HERE.parents[1] / "tools/social/fonts/PatrickHand-Regular.ttf"
BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAPER, INK, MUTED, GREY = "#F7F1E8", "#403C36", "#6E6860", "#C9C4BC"
FPS = 30
READY: dict[str, Path | None] = {}  # recording -> its prepared file, filled by main()
# 9:16 takes a 1080 px square from each painted frame: centred, unless a set needs it moved.
CROP_9X16: dict[str, int] = {}
SET_SCRIPT = {
    "01": "map.py",
    "02": "kitchen.py",
    "06": "kitchen.py",
    "07": "kitchen.py",
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
    "9x16": {"W": 1080, "H": 1920, "paint_cap": 340, "screen_cap": (540, 340),
             "card": (305, 540, 470, 1020), "under": 1615, "brand": (1010, 1110), "close_cap": 1330,
             "cap_px": 76, "wrap": True},
}  # fmt: skip


def run(cmd: list[str], quiet: bool = False) -> None:
    subprocess.run(cmd, check=True, capture_output=quiet)


def frames_needed() -> dict[str, int]:
    """Set shot -> frames the cut plays from it (consecutive rows play on through its frames)."""
    need: dict[str, int] = {}
    for _sid, sec, pic, _w in SHOTS:
        kind, *rest = pic.split("|")
        if kind in ("blender", "close"):
            need[rest[0]] = need.get(rest[0], 0) + round(sec * FPS)
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
    if kind == "screen":
        x, y = f["screen_cap"]
    elif kind == "close":
        x, y = W // 2, f["close_cap"]
    else:
        x, y = W // 2, f["paint_cap"]
    return overlay_png(
        text(words, x, y, px, wrap, W - 140), W, H, OUT / "overlays" / f"{fmt}-cap-{sid}.png"
    )


def brand(f: dict, fmt: str) -> Path:
    W, (y1, y2) = f["W"], f["brand"]
    body = text("Kettle", W // 2, y1, 130, False, W) + text(
        "heykettle.com", W // 2, y2, 64, False, W
    )
    return overlay_png(body, W, f["H"], OUT / "overlays" / f"{fmt}-brand.png")


def screen_dressing(
    rec: str, label: str, under: str, f: dict, fmt: str, live: tuple[int, int] | None
) -> Path:
    """The grey card (no recording yet) or the recording's shadow, and the line under the screen."""
    x, y, w, h = f["card"]
    if live:  # the recording's own box, centred where the card sits
        rw, rh = live
        box = f"left:{x + (w - rw) // 2}px;top:{y + (h - rh) // 2}px;width:{rw}px;height:{rh}px"
        body = f'<div class="shadow" style="{box}"></div>'
    else:
        body = (
            f'<div class="card" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">'
            f"{html.escape(rec)}<br>{html.escape(label)}<br>placeholder</div>"
        )
    if under:
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
    src = source(rec)
    if not src:
        return None
    edit = RECORDINGS.get(rec, {})
    out = OUT / "rec" / f"{rec}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    top, bottom = edit.get("crop", (0, None))
    crop = f"crop=iw:{f'{bottom}-{top}' if bottom else f'ih-{top}'}:0:{top}"
    if "hold" in edit:
        t = edit["hold"]
        graph = f"[0:v]trim=start={t}:duration=0.05,setpts=PTS-STARTPTS,{crop},fps={FPS}[v]"
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
        graph = ";".join(parts) + f";{joined}concat=n={len(pieces)}:v=1:a=0,{crop}[v]"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-filter_complex", graph,
         "-map", "[v]", *X264, str(out)])  # fmt: skip
    return out


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


def recording_box(path: Path, f: dict) -> tuple[int, int]:
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
    _, _, bw, bh = f["card"]
    scale = min(bw / info["width"], bh / info["height"])
    return int(info["width"] * scale) // 2 * 2, int(info["height"] * scale) // 2 * 2


def fade(label_in: str, label_out: str, dur: float, fade_in: bool = True) -> str:
    """Caption fades in over 0.4 s and out over the last 0.3 s of its shot."""
    parts = ["format=rgba"]
    if fade_in:
        parts.append("fade=in:st=0:d=0.4:alpha=1")
    parts.append(f"fade=out:st={dur - 0.3:.2f}:d=0.3:alpha=1")
    return f"[{label_in}]{','.join(parts)}[{label_out}]"


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
    n = round(sec * FPS)
    kind, *rest = pic.split("|")
    out = OUT / "seg" / fmt / f"{i:02d}-{sid}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    inputs: list[str] = []
    graph: list[str] = []
    loop = ["-loop", "1", "-framerate", str(FPS), "-i"]

    if kind in ("blender", "close"):
        shot = rest[0]
        start = offsets.get(shot, 0) + 1
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
        else:  # a square from the middle of the frame, feathered onto paper
            y0 = 560 if kind == "blender" else 300
            graph.append(f"color=c={PAPER}:s={W}x{H}:r={FPS}[paper]")
            cx = CROP_9X16.get(shot, "(iw-1080)/2")
            graph.append(f"[0]crop=1080:1080:{cx}:0,{feather()}[sq]")
            graph.append(f"[paper][sq]overlay=0:{y0}:shortest=1[bg]")
        last = "bg"
        if kind == "close":
            inputs += loop + [str(brand(f, fmt))]
    else:
        rec, label = rest[0], rest[1]
        under = rest[2] if len(rest) > 2 else ""
        path = READY.get(rec)
        live = recording_box(path, f) if path else None
        if fmt == "16x9":
            inputs += loop + [str(OUT / "frames/plate.png")]
            graph.append("[0]null[bg]")
        else:
            inputs += ["-f", "lavfi", "-i", f"color=c={PAPER}:s={W}x{H}:r={FPS}"]
            graph.append("[0]null[bg]")
        inputs += loop + [str(screen_dressing(rec, label, under, f, fmt, live))]
        graph.append("[bg][1]overlay=0:0[dressed]")
        last = "dressed"
        if live:  # the real screen, rounded corners, played from its offset
            start = offsets.get(rec, 0)
            offsets[rec] = start + n
            rw, rh = live
            x, y, bw, bh = f["card"]
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

    idx = sum(1 for a in inputs if a == "-i")  # next input index
    if kind == "close":  # the name and address: fade in on the first close row only
        graph.append(
            f"[1]format=rgba{',fade=in:st=0:d=0.5:alpha=1' if sid == '15a' else ''}[brand]"
        )
        graph.append(f"[{last}][brand]overlay=0:0[branded]")
        last = "branded"
    cap = caption(sid, pic, words, f, fmt)
    if cap:
        inputs += loop + [str(cap)]
        graph.append(fade(str(idx), "cap", sec))
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
    lst = out.with_suffix(".txt")
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    music = sorted((HERE / "audio").glob("music.*")) if (HERE / "audio").exists() else []
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst)]
    vf = f"fade=in:st=0:d=0.5:color={PAPER},fade=out:st={total - 0.8:.2f}:d=0.8:color={PAPER}"
    if music:  # quiet, no vocals (the founder's file), faded with the picture
        cmd += ["-i", str(music[0])]
        af = f"volume=0.35,afade=in:st=0:d=1,afade=out:st={total - 2:.2f}:d=2"
        cmd += [
            "-vf",
            vf,
            "-af",
            af,
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            *[a for a in X264 if a != "-an"],
            "-t",
            f"{total:.3f}",
            "-movflags",
            "+faststart",
            str(out),
        ]
    else:
        cmd += ["-vf", vf, *X264, "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)]
    run(cmd)
    lst.unlink()


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
    for fmt, name in (("16x9", "kettle-launch.mp4"), ("9x16", "kettle-launch-9x16.mp4")):
        offsets: dict[str, int] = {}
        parts = [segment(i, row, offsets, fmt) for i, row in enumerate(SHOTS)]
        join(parts, OUT / name, total)
        stills(parts, fmt)
        print(f"{name}: {probe(OUT / name).strip()}")
    missing = sorted(rec for rec, path in READY.items() if path is None)
    if missing:
        print("placeholders still in the cut for:", ", ".join(missing))


if __name__ == "__main__":
    main()
