"""Mom's kitchen, the set for shots 2, 6 and 7. First pass renders shot 2's still.

blender -b -P blender/kitchen.py -- [out.png]   (default out/stills/02.png)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper as P  # noqa: E402

P.reset()
P.stage()

TOP = 0.50                                        # worktop height
counter = P.card("counter", "assets/layers/counter.png", 0.53, 0.0, 0.14, sat=0.6)
P.box("worktop", P.PAPER, (1.12, 0.34, 0.012), (0.0, 0.31, TOP - 0.006))
P.card("window", "assets/layers/window.png", 0.25, -0.02, 0.595, z=0.56)   # low, over the worktop, clear of the caption band
P.card("kettle", "assets/kettle.png", 0.27, 0.30, 0.30, z=TOP)
P.card("steam", "assets/layers/steam.png", 0.15, 0.415, 0.31, z=TOP + 0.185, tint="E3DED4")   # rises from the spout tip
P.card("mug", "assets/layers/mug.png", 0.11, -0.12, 0.33, z=TOP)
P.card("plant", "assets/layers/plant.png", 0.26, -0.40, 0.40, z=TOP)

# Her phone on the worktop, screen lit: an ink body with a warm yellow face and a faint glow.
P.box("phone", P.INK, (0.085, 0.17, 0.008), (-0.24, 0.23, TOP + 0.004), rot=(0, 0, 12))
P.box("screen", P.YELLOW, (0.073, 0.152, 0.001), (-0.24, 0.23, TOP + 0.0085), rot=(0, 0, 12), glow=1.2)

P.light()
P.camera((0.0, -3.0, 1.12), (0.0, 0.3, 0.50))
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = args[0] if args else "out/stills/02.png"
P.render_settings(engine=args[1] if len(args) > 1 else "CYCLES")
P.still(out)
