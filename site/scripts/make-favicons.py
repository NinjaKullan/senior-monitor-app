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
"""

from __future__ import annotations

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


if __name__ == "__main__":
    main()
