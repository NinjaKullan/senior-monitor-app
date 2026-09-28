"""Make the film's kettle from the approved Gemini painting (candidate 4, round 2).

blender -b -P blender/kettle_fix.py -- candidates/layer-kettle-ref-4.png assets/layers/kettle.png
Founder's fixes (2026-09-27), in order:
1. Key the magenta tightly, then give every edge pixel the colour of the solid paper just inside
   it, so no pink or brown fringe survives anywhere on the outline (it showed on the grip wrap).
2. Paint out the body's dots: green pixels darker than their surroundings, filled with the
   surrounding green.
3. Replace the knob, whose thin neck read poorly, with a short, wide, low rounded button in the
   knob's own yellow, sitting on the lid.
Blender's numpy only, like cutout.py.
"""

import sys

import bpy
import numpy as np

src, dst = sys.argv[sys.argv.index("--") + 1 :][:2]
img = bpy.data.images.load(src)
w, h = img.size
p = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1].copy()  # top-first
r, g, b = p[..., 0], p[..., 1], p[..., 2]


def box_mean(values: np.ndarray, mask: np.ndarray, radius: int) -> np.ndarray:
    """Mean of `values` over each pixel's (2r+1)^2 neighbourhood, counting only `mask` pixels."""
    k = 2 * radius + 1

    def box(x):
        c = np.pad(x, radius, mode="edge").cumsum(0).cumsum(1)
        c = np.pad(c, ((1, 0), (1, 0)))
        return c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]

    n = box(mask.astype(np.float32))
    out = np.stack([box(values[..., i] * mask) for i in range(values.shape[-1])], -1)
    return out / np.maximum(n, 1e-6)[..., None]


# 1. A tight key (the ramp starts earlier than cutout.py's), then the outer 4 px of every shape
#    take their colour from the clean paper just inside.
m = np.minimum(r, b) - g
alpha = 1.0 - np.clip((m - 0.04) / (0.35 - 0.04), 0.0, 1.0)
solid = alpha > 0.98
inner = solid.copy()
for _ in range(4):  # four pixels in from the edge: the tint reaches that far into the wrap
    shrunk = inner.copy()
    for axis in (0, 1):
        for step in (1, -1):
            shrunk &= np.roll(inner, step, axis)
    inner = shrunk
rgb = p[..., :3]
fill = box_mean(rgb, inner, 6)
edge = (alpha > 0) & ~inner
rgb[edge] = fill[edge]

# 2. The dots: small, round, isolated spots of green darker than the green around them. Lines
#    (the lid's edge) and broad shading are long or large, so only compact blobs of dot size go.
lum = 0.3 * rgb[..., 0] + 0.6 * rgb[..., 1] + 0.1 * rgb[..., 2]
green = inner & (rgb[..., 1] > rgb[..., 0] + 0.1) & (rgb[..., 1] > rgb[..., 2])
around = box_mean(lum[..., None], green, 14)[..., 0]
dark = green & (lum < around - 0.012)
labels = np.zeros(dark.shape, np.int32)
dots = np.zeros_like(dark)
count = 0
for y0, x0 in zip(*np.nonzero(dark)):  # noqa: B905 (a pair of index arrays)
    if labels[y0, x0]:
        continue
    count += 1
    stack, blob = [(y0, x0)], []
    labels[y0, x0] = count
    while stack:
        y, x = stack.pop()
        blob.append((y, x))
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and dark[ny, nx] and not labels[ny, nx]:
                labels[ny, nx] = count
                stack.append((ny, nx))
    by, bx = zip(*blob)  # noqa: B905
    tall, wide = max(by) - min(by) + 1, max(bx) - min(bx) + 1
    if (
        15 <= len(blob) <= 700
        and max(tall, wide) <= 2.2 * min(tall, wide)
        and max(tall, wide) <= 40
    ):
        dots[by, bx] = True
spots = int(dots.sum())
for _ in range(6):  # take in each dot's soft rim too
    grown = dots.copy()
    for axis in (0, 1):
        for step in (1, -1):
            grown |= np.roll(dots, step, axis)
    dots = grown & green
body = box_mean(rgb, green & ~dots, 12)
rgb[dots] = body[dots]

# 3. The knob: the yellow blob in the middle band (the grip wrap is the yellow at the top).
yellow = (alpha > 0.1) & (rgb[..., 0] > 0.7) & (rgb[..., 1] > 0.55) & (rgb[..., 2] < 0.62)
band = np.zeros_like(yellow)
band[int(0.2 * h) : int(0.5 * h)] = True
knob = yellow & band
ys, xs = np.nonzero(knob)
colour = np.median(rgb[knob], axis=0)
cx, bottom, width = xs.mean(), ys.max(), xs.max() - xs.min()
box_y = slice(ys.min() - 4, bottom + 1)
box_x = slice(xs.min() - 6, xs.max() + 7)
not_green = ~(rgb[..., 1] > rgb[..., 0] + 0.08)
clear = np.zeros_like(knob)
clear[box_y, box_x] = True
alpha[clear & not_green] = 0.0  # the old knob, neck and halo go; the green lid stays
rx, ry = width * 0.6, width * 0.34  # a low rounded button, wider than tall, no neck
yy, xx = np.mgrid[0:h, 0:w]
cy = bottom - ry * 0.55  # most of it above the lid, its foot tucked into the lid
button = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0
rgb[button], alpha[button] = colour, 1.0

# 4. Bleed the solid colour out into every see-through pixel beside an edge. The keyed background
#    still holds magenta under zero alpha, and any scaling (Blender's texture filter, the card)
#    mixes it back in as a pink rim; this leaves nothing pink to mix.
solid = alpha > 0.98
for radius in (2, 4, 8):
    near = box_mean(rgb, solid, radius)
    reach = box_mean(np.ones_like(rgb[..., :1]), solid, radius)[..., 0] > 0
    rgb[~solid & reach] = near[~solid & reach]
    solid = solid | reach
p[..., :3] = rgb
p[..., 3] = alpha
ys, xs = np.nonzero(alpha > 0.5)
y0, y1, x0, x1 = max(ys.min() - 12, 0), min(ys.max() + 13, h), max(xs.min() - 12, 0), xs.max() + 13
crop = np.ascontiguousarray(p[y0:y1, x0:x1][::-1])  # back to Blender's bottom-first rows
out = bpy.data.images.new("kettle", x1 - x0, y1 - y0, alpha=True)
out.pixels.foreach_set(crop.ravel())
out.filepath_raw, out.file_format = dst, "PNG"
out.save()
print(f"kettle: {dst} {x1 - x0}x{y1 - y0}; {spots} px of dots filled; knob {width} px wide")
