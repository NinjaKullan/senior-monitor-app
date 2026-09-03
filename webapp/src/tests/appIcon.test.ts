/**
 * @vitest-environment node
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146).
 * node rather than jsdom: this reads bytes off disk and never renders.
 */
/**
 * The home-screen icon is real artwork, not a placeholder (DECISIONS 238).
 *
 * The regression this exists for already happened: `icon-192.png` and
 * `icon-512.png` shipped as 506-byte and 2 KB stand-ins from the demo-grade
 * PWA commit, and nobody noticed until the founder added Kettle to an iPhone
 * home screen and got a teal square with a white box in it. Nothing in a test
 * suite or a build was ever going to catch that, because a placeholder PNG is
 * a perfectly valid PNG.
 *
 * So the check is deliberately crude and about SIZE: real kettle rasters on
 * the canvas ground are tens of kilobytes, and no flat placeholder is. A file
 * that quietly reverts to a coloured rectangle fails here rather than on
 * somebody's phone.
 *
 * These are also the files `manifest.webmanifest` and `index.html` name, so
 * the test doubles as a check that the three declared paths exist at all.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const PUBLIC = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "public");

/** Width and height out of a PNG's IHDR, which is always the first chunk. */
function pngSize(bytes: Buffer): { width: number; height: number } {
  // 8-byte signature, then a 4-byte length and the "IHDR" tag, then the
  // dimensions as big-endian 32-bit integers.
  expect(bytes.subarray(1, 4).toString("ascii")).toBe("PNG");
  expect(bytes.subarray(12, 16).toString("ascii")).toBe("IHDR");
  return { width: bytes.readUInt32BE(16), height: bytes.readUInt32BE(20) };
}

/** Under this, a file is a placeholder rather than a drawing of a kettle. */
const FLOOR_BYTES = 5 * 1024;

const ICONS: [file: string, side: number][] = [
  ["apple-touch-icon.png", 180],
  ["icon-192.png", 192],
  ["icon-512.png", 512],
];

describe("the home-screen icons", () => {
  it.each(ICONS)("%s exists at %ipx square and is real artwork", (file, side) => {
    const bytes = readFileSync(join(PUBLIC, file));
    expect(pngSize(bytes)).toEqual({ width: side, height: side });
    expect(bytes.byteLength).toBeGreaterThan(FLOOR_BYTES);
  });

  it("the manifest names icons that are actually on disk, at the sizes it claims", () => {
    // A manifest entry pointing at a missing file is invisible until an
    // install: the browser just falls back, and the family gets a letter.
    const manifest = JSON.parse(
      readFileSync(join(PUBLIC, "manifest.webmanifest"), "utf8"),
    ) as { icons: { src: string; sizes: string; type: string }[] };

    for (const icon of manifest.icons) {
      const bytes = readFileSync(join(PUBLIC, icon.src.replace(/^\//, "")));
      expect(bytes.byteLength).toBeGreaterThan(0);
      if (icon.type === "image/png") {
        const [side] = icon.sizes.split("x").map(Number);
        expect(pngSize(bytes)).toEqual({ width: side, height: side });
      }
    }
  });

  it("the splash ground matches the icon's own ground", () => {
    // background_color paints the splash behind the icon while the app boots.
    // If it differs from the canvas the icon is flattened onto, the icon sits
    // on a visible rectangle of a different colour for that whole moment.
    const manifest = JSON.parse(
      readFileSync(join(PUBLIC, "manifest.webmanifest"), "utf8"),
    ) as { background_color: string };
    expect(manifest.background_color.toLowerCase()).toBe("#f6f2ec");
  });
});
