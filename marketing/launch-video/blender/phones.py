"""Shot 3: two phones lying side by side on the table, both screens plainly lit, one ink and
rounded,
one green and squarer: iPhone or Android, the phone she already owns. A slow arc over them.

blender -b -P blender/phones.py -- 03 [still [frame] [out.png] | frames [WxH]]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper as P  # noqa: E402

FRAMES = {"03": 156}  # 5.2 s


def build(shot: str) -> None:
    P.stage()
    flat = {"lean": 90, "stand": False, "z": 0.0045, "lit": 0.25}
    P.phone("phone-a", -0.09, -0.10, w=0.10, turn=-4, body=P.INK, corner=0.2, **flat)
    P.phone("phone-b", 0.09, -0.10, w=0.105, turn=3, body=P.GREEN, corner=0.06, **flat)
    P.box("napkin", P.PAPER, (0.12, 0.16, 0.006), (0.25, -0.02, 0.003), (0, 0, -8))
    P.box("napkin-fold", P.PAPER, (0.12, 0.08, 0.004), (0.25, -0.055, 0.008), (0, 0, -8))
    P.light()
    n = FRAMES[shot]
    # Close and high, the phones in the lower two thirds so the words sit on bare table above them.
    cam, aim = P.camera((-0.06, -0.62, 0.66), (0.06, 0.04, 0.0))
    P.key(cam, "location", 1, (-0.06, -0.62, 0.66))
    P.key(cam, "location", n, (0.06, -0.60, 0.64))


P.run(build, FRAMES)
