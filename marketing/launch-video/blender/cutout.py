"""Key Gemini's solid-magenta layers to transparent PNGs, cropped to the object.

blender -b -P blender/cutout.py -- in1.png out1.png [in2.png out2.png ...]
Uses Blender's bundled numpy, so no Pillow. Magenta-ness is min(R, B) - G: 1 for the key, below 0
for every palette colour (cream, ink, green, yellow), so the object's own colours are never keyed.
"""
import sys

import bpy
import numpy as np

LO, HI, MARGIN = 0.12, 0.55, 12   # keying ramp on magenta-ness; crop margin in px


def cut(src: str, dst: str) -> None:
    img = bpy.data.images.load(src)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    r, g, b = px[..., 0], px[..., 1], px[..., 2]
    m = np.minimum(r, b) - g
    alpha = 1.0 - np.clip((m - LO) / (HI - LO), 0.0, 1.0)
    spill = np.clip(m, 0.0, None)                       # pull the pink fringe back to neutral
    px[..., 0] = r - spill
    px[..., 2] = b - spill
    px[..., 3] = alpha
    ys, xs = np.nonzero(alpha > 0.5)
    if not len(xs):
        sys.exit(f"cutout: nothing left after keying {src}")
    y0, y1 = max(ys.min() - MARGIN, 0), min(ys.max() + MARGIN + 1, h)
    x0, x1 = max(xs.min() - MARGIN, 0), min(xs.max() + MARGIN + 1, w)
    crop = np.ascontiguousarray(px[y0:y1, x0:x1])
    out = bpy.data.images.new("cut", x1 - x0, y1 - y0, alpha=True)
    out.pixels.foreach_set(crop.ravel())
    out.filepath_raw, out.file_format = dst, "PNG"
    out.save()
    print(f"cutout: {dst} {x1 - x0}x{y1 - y0}")


args = sys.argv[sys.argv.index("--") + 1:]
if not args or len(args) % 2:
    sys.exit("usage: blender -b -P blender/cutout.py -- in.png out.png [...]")
for i in range(0, len(args), 2):
    cut(args[i], args[i + 1])
