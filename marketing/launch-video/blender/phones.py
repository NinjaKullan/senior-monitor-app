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
    flat = {"lean": 90, "stand": False, "z": 0.0045, "lit": 0.35}
    # Two makes, told apart without a logo: ink with a notch bar, green with a punch-hole camera.
    P.phone("phone-a", -0.085, -0.10, w=0.10, turn=-4, body=P.INK, notch=True, **flat)
    P.phone("phone-b", 0.085, -0.10, w=0.10, turn=3, body=P.GREEN, **flat)
    P.light()
    n = FRAMES[shot]
    # Close and high, the phones in the lower two thirds so the words sit on bare table above them.
    cam, aim = P.camera((-0.06, -0.62, 0.66), (0.0, 0.04, 0.0))
    P.key(cam, "location", 1, (-0.06, -0.62, 0.66))
    P.key(cam, "location", n, (0.06, -0.60, 0.64))


P.run(build, FRAMES)
