"""Shot 2 (was shot 3): two phones lying side by side on the table, one ink with a notch, one
green with a punch-hole, while the camera arcs slowly over them for the length of the "Meet
Kettle" line. Then (shot "03") the camera pushes into the green phone's screen, which has just
switched to the morning-note email, so the push lands on the note that shot 4 shows. "03n" is the
same arc without the push-in, for the dissolve alternative (A/B clip A); its first frames match.

blender -b -P blender/phones.py -- <03|03n> [still [frame] [out.png] | frames [WxH] [from=N]]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper as P  # noqa: E402

ARC_END, PUSH_END = 204, 234  # 6.8 s of slow arc, then a 1 s push-in
# 03: the arc, the push-in, a 0.75 s hold on the note (v6) and a 0.3 s run-on; 03n: v5's A/B arc.
FRAMES = {"03": 270, "03n": 252}
ARC_FROM, ARC_TO = (-0.06, -0.62, 0.66), (0.06, -0.60, 0.64)
AIM = (0.0, 0.04, 0.0)
# The green phone's screen centre (pivot at (0.085, -0.10), turned 3 degrees, 20.5 cm tall).
SCREEN = (0.0796, 0.0024)
# The push-in's end: the screen filling most of the frame height, right of centre, where shot 4's
# phone card sits (card centre x 1410 of 1920: 0.096 m right of the frame centre at this height).
PUSH_AIM = (SCREEN[0] - 0.096, SCREEN[1], 0.0)
PUSH_CAM = (PUSH_AIM[0], SCREEN[1] - 0.12, 0.57)


def build(shot: str) -> None:
    P.stage()
    flat = {"lean": 90, "stand": False, "z": 0.0045, "lit": 0.35}
    # Two makes, told apart without a logo: ink with a notch bar, green with a punch-hole camera.
    P.phone("phone-a", -0.085, -0.10, w=0.10, turn=-4, body=P.INK, notch=True, **flat)
    P.phone("phone-b", 0.085, -0.10, w=0.10, turn=3, body=P.GREEN, **flat)
    P.light()
    cam, aim = P.camera(ARC_FROM, AIM)
    P.key(cam, "location", 1, ARC_FROM)
    P.key(cam, "location", ARC_END, ARC_TO)
    P.key(aim, "location", 1, AIM)
    P.key(aim, "location", ARC_END, AIM)
    if shot == "03":
        # Just before the push, the green phone shows the morning-note email (a frame of shot 3's
        # recording, Mom's note: -ss 1.0, crop=1206:1940:0:190, scale=1000:-2, padded to 2060).
        P.screen_sequence("phone-b", [None, "assets/screens/note.png"], [(1, 0), (ARC_END - 6, 1)])
        P.key(cam, "location", PUSH_END, PUSH_CAM)
        P.key(aim, "location", PUSH_END, PUSH_AIM)
    else:  # the arc carries on a touch further, then the cut dissolves into shot 4
        P.key(cam, "location", FRAMES[shot], (0.075, -0.597, 0.637))


P.run(build, FRAMES)
