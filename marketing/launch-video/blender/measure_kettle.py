"""Measure a kettle cut-out so every scene can seat it and steam it without hand-tuned numbers.

blender -b -P blender/measure_kettle.py -- <kettle.png> <out.json>
Writes, in pixels from the image's top-left: the image size; the seat row (the lowest row as wide
as a quarter of the kettle, so a thin shadow or stray pixel under the base is ignored); the base's
centre and width, taken on its widest row just above the seat because a cut edge can be skewed;
and the spout tip (the topmost opaque pixel at whichever side reaches furthest from the base).
"""

import json
import sys

import bpy
import numpy as np

src, dst = sys.argv[sys.argv.index("--") + 1 :][:2]
img = bpy.data.images.load(src)
w, h = img.size
a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, 3] > 0.5  # top-first
widths = a.sum(axis=1)
seat = int(max(i for i in range(h) if widths[i] >= 0.25 * widths.max()))
band = range(max(seat - int(0.04 * h), 0), seat + 1)  # the base ring, near the bottom
xs = np.nonzero(a[max(band, key=lambda i: widths[i])])[0]
base_x, base_w = float((xs.min() + xs.max()) / 2), float(xs.max() - xs.min())
cols = np.nonzero(a.any(axis=0))[0]
left, right = int(cols.min()), int(cols.max())
side = left if base_x - left > right - base_x else right
near = [c for c in cols if abs(c - side) <= 0.03 * w]
tip_y = int(min(np.nonzero(a[:, near].any(axis=1))[0]))
tip_x = int(np.mean([c for c in near if a[tip_y, c]]))
out = {"image": src, "size": [w, h], "seat": seat, "base_x": base_x, "base_w": base_w,
       "tip": [tip_x, tip_y]}  # fmt: skip
with open(dst, "w") as f:
    json.dump(out, f, indent=1)
print("kettle:", json.dumps(out))
