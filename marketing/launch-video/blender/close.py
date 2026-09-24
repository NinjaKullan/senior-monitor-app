"""Shot 15, the close: the painted kettle on its trivet on the table, a wisp of steam. The name, the
address and the lines are laid over it by the compositor, below the kettle.
Also `plate`: the empty table and wall that every screen shot sits on (one frame).

blender -b -P blender/close.py -- <15|plate> [still [frame] [out.png] | frames [WxH]]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper as P  # noqa: E402

FRAMES = {"15": 282, "plate": 1}  # 9.4 s; one still


def build(shot: str) -> None:
    P.stage(table_front=-1.9)
    P.light()
    if shot == "plate":
        P.camera((0.0, -2.6, 0.95), (0.0, 0.3, 0.42))
        return
    P.disc("trivet", P.INK, 0.085, 0.012, 0.0, 0.2)
    P.card("kettle", "assets/kettle.png", 0.27, 0.0, 0.2, z=0.012)
    steam = P.card("steam", "assets/layers/steam.png", 0.13, 0.105, 0.21, z=0.186)
    n = FRAMES[shot]
    full = tuple(steam.scale)
    P.key(steam, "scale", 1, (full[0] * 0.5, full[1] * 0.5, 1))
    P.key(steam, "scale", 45, full)
    P.key(steam, "location", 45, tuple(steam.location))
    P.key(
        steam, "location", n, (steam.location.x + 0.012, steam.location.y, steam.location.z + 0.04)
    )
    # The kettle in the upper third, leaving the lower half of the frame for the words.
    cam, _ = P.camera((0.0, -1.7, 0.50), (0.0, 0.2, -0.035))
    P.key(cam, "location", 1, (0.0, -1.7, 0.50))
    P.key(cam, "location", n, (0.0, -1.62, 0.48))


P.run(build, FRAMES)
