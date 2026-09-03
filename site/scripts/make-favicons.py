#!/usr/bin/env python3
"""Derive the favicon set from the shipped kettle asset (Asana 1217835128977059).

Every raster here is a CROP AND RESIZE of site/public/kettle-hero.webp — the
same true-alpha drawing the hero renders — never regenerated artwork. Re-run
this whenever that asset changes and the whole set follows it.

Not part of `npm run ci` (it needs Pillow, which is not a product dependency;
the repo commits the OUTPUTS and this script is how they were made):

    ../../.venv/bin/pip install pillow
    ../../.venv/bin/python scripts/make-favicons.py     # from site/

Geometry, measured from the asset's own alpha channel (2026-08-28): the solid
kettle occupies x 232-816, y 92-735 of the 1100x825 frame, so the master crop
is the 700px square centred on (524, 414) - the kettle plus ~4% air, soft
shadow included. favicon.svg is NOT produced here: it is the hand-simplified
glyph the hobnail texture cannot survive becoming at 16px, authored once and
committed beside the rasters.

Since DECISIONS 238 this also writes the WEBAPP's home-screen set into
webapp/public/, from the same crop and the same flatten: one kettle, one
source, and a re-run refreshes both sets.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image

SITE = Path(__file__).resolve().parents[1]
PUBLIC = SITE / "public"
SOURCE = PUBLIC / "kettle-hero.webp"

#: The site's canvas token (src/tokens.css --canvas). Apple flattens a
#: transparent touch icon to BLACK, and a share card renders in contexts we
#: don't control, so both get the site's own ground rather than transparency.
CANVAS = (0xF6, 0xF2, 0xEC, 0xFF)

CROP_CENTER = (524, 414)
CROP_SIDE = 700

WEBAPP = SITE.parent / "webapp" / "public"

#: Android renders a maskable icon through a shape of its choosing, and the
#: only region guaranteed to survive every one of them is the CIRCLE whose
#: diameter is 80% of the tile - so the safe radius is 0.40 of the tile, not
#: 0.40 of its width in each direction. A square scaled to 80% is therefore
#: NOT safe: its corners sit at 0.566 from the centre, well outside.
MASKABLE_SAFE_RADIUS = 0.40

#: Alpha above which a pixel is the kettle rather than its soft shadow. The
#: measured extent is identical from 64 through 200, so this sits in the middle
#: of a flat region rather than on a cliff - a threshold that has to be exactly
#: right is a threshold that will be wrong after the next asset.
INK_ALPHA = 64


def master() -> Image.Image:
    im = Image.open(SOURCE).convert("RGBA")
    cx, cy = CROP_CENTER
    half = CROP_SIDE // 2
    box = (cx - half, cy - half, cx + half, cy + half)
    crop = im.crop(box)
    # The asset carries invisible residual alpha (1-2 of 255) across its whole
    # frame; at icon sizes that becomes a faint dirty halo in the ICO mask, so
    # anything a person cannot see is dropped to exactly zero.
    r, g, b, a = crop.split()
    a = a.point(lambda v: 0 if v <= 8 else v)
    crop.putalpha(a)
    return crop


def transparent(size: int, source: Image.Image) -> Image.Image:
    return source.resize((size, size), Image.LANCZOS)


def on_canvas(size: int, source: Image.Image, content_fraction: float) -> Image.Image:
    """The kettle centred on the site's ground at `content_fraction` of the tile."""
    tile = Image.new("RGBA", (size, size), CANVAS)
    inner = round(size * content_fraction)
    kettle = source.resize((inner, inner), Image.LANCZOS)
    offset = (size - inner) // 2
    tile.alpha_composite(kettle, (offset, offset))
    return tile


def ink_radius_fraction(source: Image.Image) -> float:
    """How far the kettle itself reaches from the crop's centre, as a fraction.

    Measured rather than assumed, so the safe-zone scale below follows the
    asset instead of a number somebody typed once. Returns the largest
    distance from the centre to any pixel that is kettle rather than shadow,
    divided by the crop's side.
    """
    alpha = source.split()[3]
    width, height = alpha.size
    pixels = alpha.load()
    cx, cy = (width - 1) / 2, (height - 1) / 2
    longest = 0.0
    for y in range(height):
        for x in range(width):
            if pixels[x, y] > INK_ALPHA:
                distance = math.hypot(x - cx, y - cy)
                if distance > longest:
                    longest = distance
    return longest / width


def maskable_fraction(source: Image.Image) -> float:
    """The tile fraction at which the kettle still fits the safe CIRCLE.

    DECISIONS 238 asks for the kettle inside the central 80% so that Android's
    circle crop keeps the spout and the handle. Those are two different things
    when the artwork is a square: scaling this crop to 0.80 of the tile puts
    the kettle's outermost ink at 0.80 x 0.5617 = 0.449 from the centre, which
    is OUTSIDE the 0.40 safe radius, and the circle crop would take exactly
    the spout tip and handle arc the ruling is protecting. So the scale is
    derived from the safe radius instead, and it comes out near 0.71.
    """
    return MASKABLE_SAFE_RADIUS / ink_radius_fraction(source)


def write_webapp_icons(source: Image.Image) -> None:
    """The home-screen set for the installed app (DECISIONS 238).

    Same crop, same ground, same flatten as the site's touch icon: the app a
    family taps and the site they read it about are one product, and two
    kettles drawn from two sources drift the first time either is touched.
    """
    WEBAPP.mkdir(parents=True, exist_ok=True)
    fraction = maskable_fraction(source)

    # iOS: no circle crop, just rounded corners, so it keeps the site's own
    # 0.84 and the extra presence that buys.
    on_canvas(180, source, 0.84).convert("RGB").save(
        WEBAPP / "apple-touch-icon.png", optimize=True
    )
    # Android maskable: opaque to the edges, because a maskable icon's
    # background is what the launcher's shape is cut OUT of - transparency
    # there is a hole, not a ground.
    for size in (192, 512):
        on_canvas(size, source, fraction).convert("RGB").save(
            WEBAPP / f"icon-{size}.png", optimize=True
        )

    print(f"webapp maskable scale: {fraction:.3f} of the tile")
    for name in ("apple-touch-icon.png", "icon-192.png", "icon-512.png"):
        path = WEBAPP / name
        print(f"webapp/{name}: {path.stat().st_size:,} bytes")


def main() -> None:
    source = master()

    # The tab icons: transparent, so they sit on whatever the browser chrome
    # is. 16 is the one the legibility check exists for.
    sizes = (16, 32, 48)
    icons = {size: transparent(size, source) for size in sizes}
    icons[16].save(PUBLIC / "favicon-16.png")
    icons[32].save(PUBLIC / "favicon-32.png")
    # One .ico carrying all three, PNG-32 and PNG-16 also shipped standalone.
    icons[48].save(
        PUBLIC / "favicon.ico",
        format="ICO",
        append_images=[icons[32], icons[16]],
        sizes=[(s, s) for s in sizes],
    )

    # Phone home screens: 180x180, opaque, a touch of air so iOS's corner
    # rounding does not clip the spout or the handle.
    on_canvas(180, source, 0.84).convert("RGB").save(
        PUBLIC / "apple-touch-icon.png", optimize=True
    )

    # The share card: 1200x630, the kettle alone on the site's ground. No
    # words - the linked page's own <title> and description ride beside it in
    # every scraper, and a text-free card has no copy-law surface at all.
    card = Image.new("RGBA", (1200, 630), CANVAS)
    kettle_h = 520
    kettle = master().resize((kettle_h, kettle_h), Image.LANCZOS)
    card.alpha_composite(kettle, ((1200 - kettle_h) // 2, (630 - kettle_h) // 2))
    card.convert("RGB").save(PUBLIC / "og-image.png", optimize=True)

    for name in (
        "favicon.ico",
        "favicon-16.png",
        "favicon-32.png",
        "apple-touch-icon.png",
        "og-image.png",
    ):
        path = PUBLIC / name
        print(f"{name}: {path.stat().st_size:,} bytes")

    write_webapp_icons(source)


if __name__ == "__main__":
    main()
