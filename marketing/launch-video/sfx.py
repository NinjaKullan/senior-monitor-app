#!/usr/bin/env python3
"""The kitchen shot's two soft sounds, synthesized with ffmpeg (source: generated here, so no
licence applies and nothing is downloaded).

python3 sfx.py -> assets/sfx/tick.wav (Mom's reply lands) and assets/sfx/pop.wav (the paper
thumbs up rises)

- tick: a warm, rounded text tick. Two sine partials (1175 Hz and 2350 Hz, the upper 12 dB down)
  with a 4 ms rise and a fast exponential fall, low-passed at 2.8 kHz, 0.2 s long.
- pop: a light paper pop. A 35 ms burst of noise band-passed around 1.6 kHz over a soft 190 Hz body,
  with a 3 ms rise so it never clicks, low-passed at 4 kHz, 0.15 s long.
Both peak at -18 dBFS in the file, well under the voice; render.py places them (shots.SFX).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "assets" / "sfx"
RATE = 48000
SOUNDS = {
    "tick": (
        0.20,
        "(sin(2*PI*1175*t)+0.25*sin(2*PI*2350*t))*min(t/0.004,1)*exp(-t/0.035)",
        "lowpass=f=2800",
    ),
    "pop": (
        0.15,
        "(0.8*(random(0)*2-1)*exp(-t/0.012)+0.9*sin(2*PI*190*t)*exp(-t/0.03))*min(t/0.003,1)",
        "bandpass=f=1600:w=1800:t=h,lowpass=f=4000",
    ),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (length, expr, shape) in SOUNDS.items():
        out = OUT / f"{name}.wav"
        raw = OUT / f".{name}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        f"aevalsrc='{expr}':s={RATE}:d={length}", "-af", shape, str(raw)],
                       check=True)  # fmt: skip
        probe = ["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "volumedetect", "-f", "null", "-"]
        peak = subprocess.run(probe, capture_output=True, text=True).stderr
        top = float(peak.split("max_volume: ")[1].split(" dB")[0])
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af",
                        f"volume={-18 - top:.2f}dB", str(out)], check=True)  # fmt: skip
        raw.unlink()
        print(f"wrote assets/sfx/{name}.wav ({length} s, peak -18 dBFS)")


if __name__ == "__main__":
    main()
