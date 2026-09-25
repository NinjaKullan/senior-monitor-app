"""Mom's kitchen: shots 2 (a busy morning), 6 (a morning that isn't hers) and 7 (Kettle asks;
a thumbs up).

blender -b -P blender/kitchen.py -- <02|06|07> [still [frame] [out.png] | frames [WxH]]
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper as P  # noqa: E402

TOP = 0.50  # worktop height
FRAMES = {"02": 141, "06": 141, "07": 267}  # 4.7 s, 4.7 s, 8.9 s (07a + 07b) at 30 fps
PHONE = (-0.27, 0.22)


def build(shot: str) -> None:
    P.stage()
    P.card("counter", "assets/layers/counter.png", 0.53, 0.0, 0.14)
    P.box("worktop", P.PAPER, (1.12, 0.34, 0.012), (0.0, 0.31, TOP - 0.006))
    P.card(
        "window", "assets/layers/window.png", 0.25, -0.02, 0.595, z=0.56
    )  # low, clear of the caption band
    P.kettle(0.30, 0.30, TOP)
    P.card("plant", "assets/layers/plant.png", 0.26, -0.40, 0.40, z=TOP)
    P.contact("plant-contact", -0.40, 0.40, TOP, 0.06, 0.022)
    mug_x = -0.12 if shot != "07" else 0.06  # in the close-up the mug steps aside for the thumbs up
    P.card("mug", "assets/layers/mug.png", 0.11, mug_x, 0.33, z=TOP)
    P.contact("mug-contact", mug_x - 0.01, 0.33, TOP, 0.05, 0.02)
    # Her phone on a little paper stand, warm screen to the camera.
    # Shot 6: dark, the day not started.
    P.phone("phone", *PHONE, TOP, w=0.11, lean=14, lit=0.35 if shot != "06" else 0.0)
    P.light()
    n = FRAMES[shot]

    if shot == "02":  # slow push-in; steam rises; her phone lights up
        cam, _ = P.camera((0.0, -3.0, 1.12), (0.0, 0.3, 0.50))
        P.key(cam, "location", 1, (0.0, -3.0, 1.12))
        P.key(cam, "location", n, (0.03, -2.78, 1.08))
        steam = P.card("steam", "assets/layers/steam.png", 0.15, 0.415, 0.31, z=TOP + 0.186)
        full = tuple(steam.scale)
        P.key(steam, "scale", 1, (full[0] * 0.6, full[1] * 0.6, 1))
        P.key(steam, "scale", 30, full)
        P.key(steam, "location", 30, tuple(steam.location))
        P.key(
            steam,
            "location",
            n,
            (steam.location.x + 0.01, steam.location.y, steam.location.z + 0.03),
        )
        for f, glow in ((1, 0.0), (48, 0.0), (60, 0.35)):  # her phone wakes at about 1.6 s
            P.light_screen("phone", f, glow)
    elif shot == "06":  # held low and still, a whisper of drift; no steam
        cam, _ = P.camera((-0.05, -2.9, 1.0), (0.0, 0.3, 0.52))
        P.key(cam, "location", 1, (-0.05, -2.9, 1.0))
        P.key(cam, "location", n, (0.05, -2.9, 1.0))
    else:  # close on the phone: a paper slip settles, a thumbs up folds up
        cam, _ = P.camera((-0.30, -1.35, 1.02), (-0.18, 0.25, 0.66))
        P.key(cam, "location", 1, (-0.30, -1.35, 1.02))
        P.key(cam, "location", n, (-0.20, -1.28, 1.00))
        slip = P.box(
            "slip",
            P.PAPER,
            (0.07, 0.003, 0.045),
            (PHONE[0], PHONE[1] - 0.03, TOP + 0.9),
            (-14, 0, 0),
        )
        P.key(slip, "location", 12, (PHONE[0], PHONE[1] - 0.03, TOP + 0.9))
        P.key(slip, "location", 42, (PHONE[0], PHONE[1] - 0.035, TOP + 0.075))
        thumbs = P.card("thumbs", "assets/layers/thumbs.png", 0.14, -0.12, 0.26, z=TOP, lean=88)
        P.key(thumbs, "rotation_euler", 66, (math.radians(2), 0, 0))
        P.key(thumbs, "rotation_euler", 90, (math.radians(90), 0, 0))


P.run(build, FRAMES)
