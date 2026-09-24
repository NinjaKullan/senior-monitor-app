"""Shot 1: a paper map on the table. The city on the left, Mom and Dad's house far off on the right,
the sun coming up behind it while the camera drifts from one to the other.

blender -b -P blender/map.py -- 01 [still [frame] [out.png] | frames [WxH]]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper as P  # noqa: E402

FRAMES = {"01": 126}                                  # 4.2 s


def build(shot: str) -> None:
    P.stage()
    P.card("map", "assets/layers/map.png", 0.86, 0.0, 0.0, flat=True)          # 1.54 m wide, lying flat
    P.card("hills-back", "assets/layers/hills.png", 0.12, -0.28, 0.36)
    P.card("hills", "assets/layers/hills.png", 0.16, 0.42, 0.34)
    P.card("city", "assets/layers/city.png", 0.32, -0.52, 0.02)
    P.card("house", "assets/layers/house.png", 0.22, 0.52, 0.02)
    for i, (x, y, h) in enumerate(((-0.18, 0.12, 0.12), (0.22, -0.14, 0.10), (0.74, 0.14, 0.11), (-0.78, 0.2, 0.10))):
        P.card(f"tree{i}", "assets/layers/tree.png", h, x, y)
    sun = P.disc("sun", P.YELLOW, 0.085, 0.004, 0.60, 0.40, z=0.02, upright=True, glow=0.25)
    P.light()
    n = FRAMES[shot]
    P.key(sun, "location", 1, (0.60, 0.40, 0.02))
    P.key(sun, "location", n, (0.60, 0.40, 0.155))   # just clears the hills
    cam, aim = P.camera((-0.30, -2.25, 1.30), (-0.22, 0.12, 0.12))
    P.key(cam, "location", 1, (-0.30, -2.25, 1.30))
    P.key(cam, "location", n, (0.30, -2.20, 1.26))
    P.key(aim, "location", 1, (-0.22, 0.12, 0.12))
    P.key(aim, "location", n, (0.26, 0.12, 0.12))


P.run(build, FRAMES)
