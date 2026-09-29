"""The three short feature videos (founder, 2026-09-28): the launch film's style, sets and
recordings, each on its own voice take. FEATURES.md is the human copy of these shot lists.

KETTLE_CUT=<family|smarthome|carecompare> python3 render.py  -> out/kettle-<cut>-16x9.mp4 and -9x16
shots.py swaps these values in for its own when KETTLE_CUT is set, so render.py builds a feature
video exactly as it builds the launch film. Pacing as the launch film: 0.3 s dissolves, each line
0.2 s after its cut, at least 0.5 s between lines; the v7 end card on the last line.
"""

END = "Kettle\nheykettle.com\nFor checking in, not checking up.\nNow open to founding families."


def _cut(name, take, rows, total_range, recordings=None, zoom=None):
    shots = [row[:4] for row in rows]
    return {
        "SHOTS": shots,
        "VOICE_TAKE": f"audio/vo-{take}.mp3",
        # Each line is the span between the take's silences (silencedetect -40 dB, 0.3 s),
        # padded 0.05 s.
        "VOICE": {row[0]: row[4] for row in rows},
        "DISSOLVES": {(a[0], b[0]): 0.3 for a, b in zip(shots, shots[1:])},  # noqa: B905
        "CAPTION_LAYOUT": {},
        "CAPTION_OUT_EARLY": {},
        "SFX": {},
        "ZOOM": zoom or {},
        "EXTRA_RECORDINGS": recordings or {},
        "OUT_NAME": f"kettle-{name}",
        "TOTAL_RANGE": total_range,
    }


CUTS = {
    "family": _cut("family", "family", [
        ("f1", 4.2, "blender|01",
         "Mom and Dad live on their own,\nand the whole family wants to help.", [(0.00, 3.64)]),
        ("f2", 3.7, "blender|sc", "But the updates end up scattered\nacross texts and calls.",
         [(3.94, 7.08)]),
        ("f3", 3.4, "screen|R3|Memory", "Kettle keeps it in one place,\nfor everyone.",
         [(7.39, 10.20)]),
        ("f4", 2.9, "screen|R5|Family circle", "Brothers and sisters\nsee the same notes.",
         [(10.52, 12.83)]),
        ("f5", 3.4, "screen|R6|Claude: who to call",
         "And you can reach it\nfrom Claude or ChatGPT.", [(13.09, 15.90)]),
        ("f6", 2.5, "screen|R7|Claude: leave a note", "Ask who to call,\nor leave a note.",
         [(16.18, 18.13)]),
        ("f7", 4.1, "card|end", END, [(18.45, 21.39)]),
    ], (15, 25)),
    # Short (founder: about 11 to 12 s, minimum pacing, no long silent holds).
    "smarthome": _cut("smarthome", "smarthome", [
        ("s1", 3.2, "blender|10a", "Already have a smart plug\nor Alexa at Dad's?", [(0.00, 2.69)]),
        # From frame 30, so the lamp comes on (35 to 65) inside the 1.4 s.
        ("s2", 1.4, "blender|10b|30", "Add it to Kettle.", [(2.95, 3.79)]),
        ("s3", 2.8, "blender|10c", "One more way Kettle\nhears from his day.", [(4.08, 6.35)]),
        ("s4", 3.9, "card|end", END, [(6.67, 9.40)]),
    ], (10, 13)),
    # No jump back (founder): the question being typed, the results, a slow close-up on the ZIP
    # in the question bubble above those results (the results' last frame), the final screen.
    "carecompare": _cut("carecompare", "carecompare", [
        ("c1", 2.8, "screen|R9a|Claude: the question|Care Compare by HeyKettle",
         "Looking for home health care\nfor Mom?", [(0.00, 2.24)]),
        ("c2", 5.2, "screen|R9b|Claude: the results|Care Compare by HeyKettle",
         "Care Compare by HeyKettle\nreads Medicare's own ratings,\nin plain words.",
         [(3.07, 7.72)]),
        ("c3", 2.5, "screen|R9c|Claude: the ZIP|Care Compare by HeyKettle",
         "Free.\nJust enter a ZIP code.", [(7.94, 9.88)]),
        ("c4", 2.6, "screen|R9d|Claude: when you call|Care Compare by HeyKettle",
         "Then call and ask\nyour own questions.", [(10.15, 12.22)]),
        ("c5", 4.1, "card|end", END, [(12.46, 15.49)]),
    ], (15, 25), recordings={
        # The start, typing still under way at 2.8 s (the question is complete at 3.2 s).
        "R9a": {"src": "R9", "crop": (300, None), "cuts": [(0.0, 3.2, 1)]},
        # The five agencies arriving, a touch slowed to fill the line; the question bubble stays
        # at the top until 16.0 s, when the answer starts to scroll.
        "R9b": {"src": "R9", "crop": (300, None), "cuts": [(12.0, 16.0, 0.75)]},
        # R9b's last frame, as a 900 px square detail pushing in slowly on the ZIP in the question
        # bubble, at (958, 230) of the cropped recording, from 1.0x to 2.0x; its own box in 16:9.
        "R9c": {"src": "R9", "crop": (300, None), "hold": 16.0,
                "zoom": (2.8, 1.0, 2.0, 958, 230, 900, 900), "box": (970, 90, 900, 900)},
        # The end of the answer: Medicare's source line and "When you call, ask whether...".
        "R9d": {"src": "R9", "crop": (300, None), "hold": 25.8},
    }),
}  # fmt: skip


def cut(name: str) -> dict:
    if name not in CUTS:
        raise SystemExit(f"unknown KETTLE_CUT {name!r}; the feature videos are {sorted(CUTS)}")
    return CUTS[name]
