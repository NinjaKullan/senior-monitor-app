#!/usr/bin/env node
/**
 * The kettle mark's scaling check, run in a real browser (DECISIONS 187).
 *
 * jsdom lays nothing out and computes no container query, so the suite can
 * assert that the stylesheet contains no pixels and still not know whether the
 * steam is the right size. This script is the layout half: it renders the mark
 * at three widths and measures what the browser actually produced.
 *
 * At each width it seeks every wisp animation through its whole cycle, takes
 * the furthest extent each one reaches, and expresses every measurement as a
 * fraction of the kettle's own width. The fix is proved by those fractions
 * being IDENTICAL at 120px, 240px and 420px — that is what "the steam is a
 * property of the kettle, not of the page" means, and it is exactly what the
 * mockup's fixed pixels could not do: at 120px its wisps were three times too
 * wide and travelled three times too far, which is the drift over the lid the
 * founder reported.
 *
 * It also checks the mark's blending, and it checks it the way the bug
 * demanded (DECISIONS 189). Blending has three premises and the first two are
 * cheap lies to pass: the CSS rule can be present, and the asset's ground can
 * be pure white, while the mark still paints a rectangle — because
 * `mix-blend-mode` composites only within its nearest STACKING CONTEXT, and an
 * ancestor that makes one hands the blend a transparent group to land on
 * instead of the page. Both earlier checks passed all the way through that.
 *
 * So the real check reads the RENDERED page: screenshot the mark's box, then
 * screenshot the same box with the mark hidden (`visibility`, which changes no
 * layout), and require the two to agree wherever the drawing's ground is
 * white. Multiplying by white is the identity, so where the ground is white
 * the page must look EXACTLY as it does with no mark there at all — wash,
 * gradient, and any rhythm-field dot drifting behind it. A dot that vanished
 * under the ground region, or a wash that flattened, is a difference this
 * cannot miss, whatever the CSS says. Run with reduced motion so both frames
 * are the same still.
 *
 * The asset's own ground is still read afterwards, as a second line of
 * defence and because it names the cause when the composite check fails.
 *
 * NOT part of `npm run ci`: it needs a browser, and Playwright is deliberately
 * not a dependency of this package. Run it against a preview server:
 *
 *   npm run build && npx vite preview --port 5288 &
 *   node scripts/probe-kettle.mjs http://127.0.0.1:5288/
 */
import { chromium } from "/opt/node22/lib/node_modules/playwright/index.mjs";

const url = process.argv[2] ?? "http://127.0.0.1:5288/";
const WIDTHS = [120, 240, 420];
const PLACES = 3;
/** Sub-pixel rounding only. A container query resolves to a fractional pixel
 *  and the browser rounds the used value, so the same fraction can land one
 *  thousandth apart at 120px and at 420px. Anything larger than this is not
 *  rounding — it is geometry that does not scale. */
const EPSILON = 0.002;

const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
await page.goto(url, { waitUntil: "networkidle" });

const results = [];
for (const width of WIDTHS) {
  const measured = await page.evaluate(async (px) => {
    const mark = document.querySelector(".kt-mark");
    mark.style.width = `${px}px`;
    // Let the container query and the image reflow before anything is read.
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));

    const image = mark.querySelector(".kt-mark-image");
    const frame = image.getBoundingClientRect();
    const wisps = [...mark.querySelectorAll(".kt-wisp")];

    // Seek every animation through its cycle and keep the extreme box each
    // wisp reaches: the top it rises to and the left it drifts to.
    const extents = wisps.map(() => ({ top: Infinity, left: Infinity, width: 0, height: 0 }));
    const animations = wisps.map((wisp) => wisp.getAnimations()[0] ?? null);
    for (const animation of animations) if (animation) animation.pause();
    for (let step = 0; step <= 40; step++) {
      wisps.forEach((wisp, index) => {
        const animation = animations[index];
        if (animation) {
          const duration = animation.effect.getTiming().duration;
          animation.currentTime = (duration * step) / 40;
        }
        const box = wisp.getBoundingClientRect();
        const at = extents[index];
        at.top = Math.min(at.top, box.top);
        at.left = Math.min(at.left, box.left);
        at.width = Math.max(at.width, box.width);
        at.height = Math.max(at.height, box.height);
      });
    }
    return {
      frame: { width: frame.width, height: frame.height, top: frame.top, left: frame.left },
      wisps: extents.map((at) => ({
        // Everything as a fraction of the kettle's own width: how far above
        // the frame's top edge the wisp climbs, the leftmost and rightmost
        // edges it reaches measured from the frame's left edge, and its size.
        rise: (frame.top - at.top) / frame.width,
        leftmost: (at.left - frame.left) / frame.width,
        rightmost: (at.left + at.width - frame.left) / frame.width,
        width: at.width / frame.width,
        height: at.height / frame.width,
      })),
      animated: animations.filter(Boolean).length,
    };
  }, width);

  results.push({ width, ...measured });

  // The screenshots are for a person, so the wisps are parked where a person
  // would see them rather than at the transparent last frame the measuring
  // loop left them on: each one a fifth of the way into its own cycle, in the
  // staggered phase the negative delays produce live.
  await page.evaluate(() => {
    [...document.querySelectorAll(".kt-wisp")].forEach((wisp, index) => {
      const animation = wisp.getAnimations()[0];
      if (!animation) return;
      const duration = animation.effect.getTiming().duration;
      animation.currentTime = duration * (0.16 + index * 0.06);
    });
  });
  const box = await page.locator(".kt-mark").boundingBox();
  await page.screenshot({
    path: `/tmp/kettle-${width}.png`,
    clip: {
      x: Math.max(0, box.x - width * 0.5),
      y: Math.max(0, box.y - width * 1.2),
      width: box.width * 2,
      height: box.height + width * 1.4,
    },
  });
}

await browser.close();

const round = (n) => Number(n.toFixed(PLACES));
let failed = false;
const base = results[0];
console.log(`kettle mark, measured at ${WIDTHS.join(", ")}px — every number is a fraction of the kettle's width\n`);
for (const result of results) {
  console.log(
    `${String(result.width).padStart(4)}px  frame ${round(result.frame.width)}×${round(
      result.frame.height,
    )}px  wisps animating: ${result.animated}`,
  );
  result.wisps.forEach((wisp, index) => {
    console.log(
      `        wisp ${index + 1}: size ${round(wisp.width)}×${round(wisp.height)}  ` +
        `rise ${round(wisp.rise)}  spans ${round(wisp.leftmost)}–${round(wisp.rightmost)}`,
    );
  });
}

console.log("\nproportionality — the same steam at every size:");
for (const result of results.slice(1)) {
  result.wisps.forEach((wisp, index) => {
    for (const key of ["width", "height", "rise", "leftmost", "rightmost"]) {
      const here = wisp[key];
      const there = base.wisps[index][key];
      if (Math.abs(here - there) > EPSILON) {
        failed = true;
        console.error(
          `  FAIL wisp ${index + 1} ${key}: ${round(there)} at ${base.width}px, ` +
            `${round(here)} at ${result.width}px`,
        );
      }
    }
  });
}
if (!failed) {
  console.log(`  every wisp identical across ${WIDTHS.join("/")}px, within ${EPSILON} of the kettle`);
}

console.log("\nsilhouette — the steam belongs to the spout:");
for (const result of results) {
  const rise = Math.max(...result.wisps.map((w) => w.rise));
  const widest = Math.max(...result.wisps.map((w) => w.width));
  const leftmost = Math.min(...result.wisps.map((w) => w.leftmost));
  const rightmost = Math.max(...result.wisps.map((w) => w.rightmost));
  // A wisp wider than a third of the kettle, one climbing more than a
  // kettle-width above the frame, or one that has wandered off either side of
  // the pot, is the fixed-pixel bug at a small size.
  const ok = widest < 0.34 && rise < 1 && leftmost >= 0 && rightmost <= 1;
  if (!ok) failed = true;
  console.log(
    `  ${String(result.width).padStart(4)}px  widest wisp ${round(widest)} of the kettle, ` +
      `highest rise ${round(rise)}, spans ${round(leftmost)}–${round(rightmost)}  ${ok ? "ok" : "FAIL"}`,
  );
}

console.log("\nblending — the mark composites onto the page, not over it:");
const blend = await (async () => {
  const browser2 = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
  // Reduced motion, so the steam stands still and the rhythm field draws its
  // designed still: the two screenshots below must differ only where the mark
  // is, never because a frame moved between them.
  const page2 = await browser2.newPage({
    viewport: { width: 1280, height: 900 },
    reducedMotion: "reduce",
  });
  await page2.goto(url, { waitUntil: "networkidle" });

  const box = await page2.locator(".kt-mark").boundingBox();
  const clip = {
    x: Math.round(box.x),
    y: Math.round(box.y),
    width: Math.round(box.width),
    height: Math.round(box.height),
  };
  // The steam is hidden for BOTH frames: it is not what is being tested, and
  // a wisp sitting over the ground would read as a difference.
  const hide = (selector, value) =>
    page2.evaluate(
      ([s2, v]) => {
        for (const node of document.querySelectorAll(s2)) node.style.visibility = v;
      },
      [selector, value],
    );
  await hide(".kt-steam, .kt-steam-lid", "hidden");
  const painted = (await page2.screenshot({ clip })).toString("base64");
  await hide(".kt-mark", "hidden");
  const bare = (await page2.screenshot({ clip })).toString("base64");
  await hide(".kt-mark", "");
  await hide(".kt-steam, .kt-steam-lid", "");

  const composite = await page2.evaluate(
    async ([withMark, withoutMark, source]) => {
      const decode = async (data) => {
        const image = new Image();
        image.src = `data:image/png;base64,${data}`;
        await image.decode();
        const canvas = document.createElement("canvas");
        canvas.width = image.naturalWidth;
        canvas.height = image.naturalHeight;
        canvas.getContext("2d").drawImage(image, 0, 0);
        return canvas.getContext("2d").getImageData(0, 0, canvas.width, canvas.height);
      };
      const a = await decode(withMark);
      const b = await decode(withoutMark);

      // The drawing itself decides which samples are ground: a pixel the
      // artwork paints white is a pixel the page must show unchanged. Drawn
      // at the SIZE THE PAGE DRAWS IT, because that is the only version whose
      // pixels line up with the screenshot: the mark renders at an eighth of
      // the artwork's width, so a rendered pixel beside the handle is an
      // average of white ground and dark metal, and testing the full-size art
      // would call it ground and then fail on the handle.
      const art = new Image();
      art.src = source;
      await art.decode();
      const artCanvas = document.createElement("canvas");
      artCanvas.width = a.width;
      artCanvas.height = a.height;
      artCanvas.getContext("2d").drawImage(art, 0, 0, a.width, a.height);
      const artData = artCanvas
        .getContext("2d")
        .getImageData(0, 0, artCanvas.width, artCanvas.height);

      const pixel = (data, x, y) => {
        const i = (y * data.width + x) * 4;
        return [data.data[i], data.data[i + 1], data.data[i + 2]];
      };
      let sampled = 0;
      let worst = { delta: -1 };
      const STEPS = 40;
      for (let row = 1; row < STEPS; row++) {
        for (let col = 1; col < STEPS; col++) {
          const x = Math.floor((a.width * col) / STEPS);
          const y = Math.floor((a.height * row) / STEPS);
          // Ground only if this pixel AND its neighbours are white: an
          // anti-aliased edge one pixel away still tints what the page paints.
          let ground = true;
          for (let dy = -1; dy <= 1 && ground; dy++) {
            for (let dx = -1; dx <= 1 && ground; dx++) {
              const nx = Math.min(a.width - 1, Math.max(0, x + dx));
              const ny = Math.min(a.height - 1, Math.max(0, y + dy));
              const [ar, ag, ab] = pixel(artData, nx, ny);
              if (Math.min(ar, ag, ab) < 250) ground = false;
            }
          }
          if (!ground) continue; // kettle, its shadow, or an edge beside them
          sampled++;
          const painted = pixel(a, x, y);
          const bare = pixel(b, x, y);
          const art = pixel(artData, x, y);
          // What multiply is defined to produce: backdrop x source / 255. For
          // a ground of 255 that is the backdrop untouched; for the ground's
          // real 250-255 it is a level or two below it. Comparing against the
          // arithmetic rather than against the bare page means the tolerance
          // is rounding error and nothing else — a blend landing on the wrong
          // backdrop cannot hide inside a slack allowance.
          const expected = bare.map((c, i) => Math.round((c * art[i]) / 255));
          const delta = Math.max(...painted.map((c, i) => Math.abs(c - expected[i])));
          if (delta > worst.delta) worst = { delta, x, y, painted, bare, expected };
        }
      }
      return { sampled, worst };
    },
    [painted, bare, "/kettle-hero.webp"],
  );

  const out = await page2.evaluate(async () => {
    const rendered = document.querySelector(".kt-mark-image");
    const mode = getComputedStyle(rendered).mixBlendMode;

    const image = new Image();
    image.src = rendered.getAttribute("src");
    await image.decode();
    const canvas = document.createElement("canvas");
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(image, 0, 0);
    const at = (x, y) => [...ctx.getImageData(x, y, 1, 1).data];
    // The four corners and the mid-points of the top and bottom edges: the
    // ground, sampled where the kettle and its shadow never reach.
    const w = image.naturalWidth;
    const h = image.naturalHeight;
    return {
      mode,
      size: [w, h],
      ground: {
        "top-left": at(1, 1),
        "top-right": at(w - 2, 1),
        "top-middle": at(Math.floor(w / 2), 2),
        "bottom-left": at(1, h - 2),
        "bottom-right": at(w - 2, h - 2),
      },
    };
  });
  await browser2.close();
  return { ...out, composite, clip };
})();

// The composite: what the page actually painted, against what it paints with
// no mark there at all. Anything above a couple of levels is the mark failing
// to reach the backdrop — the stacking-context bug of DECISIONS 189.
const COMPOSITE_TOLERANCE = 2;
const { sampled, worst } = blend.composite;
if (sampled < 100) {
  failed = true;
  console.error(`  FAIL only ${sampled} ground samples found — the check is not looking at anything`);
} else if (worst.delta > COMPOSITE_TOLERANCE) {
  failed = true;
  console.error(
    `  FAIL the ground does not composite: at (${worst.x}, ${worst.y}) the page paints ` +
      `rgb(${worst.painted.join(", ")}); multiplying the drawing onto the page there ` +
      `(bare rgb(${worst.bare.join(", ")})) must give rgb(${worst.expected.join(", ")}) — ` +
      `${worst.delta} levels out over ${sampled} ground samples. The blend is landing ` +
      `on something other than the page.`,
  );
} else {
  console.log(
    `  ${sampled} ground samples, worst departure from multiply's own arithmetic ` +
      `${worst.delta} of 255 — the drawing is landing on the page itself`,
  );
}

if (blend.mode !== "multiply") {
  failed = true;
  console.error(`  FAIL the image's blend mode is "${blend.mode}", not multiply`);
} else {
  console.log("  blend mode: multiply");
}
// Multiplying by white is the identity. Anything short of it darkens the
// backdrop by exactly the shortfall, per channel — which is what a visible
// rectangle IS.
const GROUND_FLOOR = 250;
for (const [corner, [r, g, b, a]] of Object.entries(blend.ground)) {
  const white = Math.min(r, g, b) >= GROUND_FLOOR && a === 255;
  if (!white) {
    failed = true;
    console.error(
      `  FAIL ground at ${corner} is rgb(${r}, ${g}, ${b}) — multiply will darken the ` +
        `backdrop behind the mark by ${255 - r}/${255 - g}/${255 - b} per channel, ` +
        `which is the rectangle it is supposed to dissolve`,
    );
  } else {
    console.log(`  ground at ${corner}: rgb(${r}, ${g}, ${b}) — composites to the backdrop`);
  }
}

console.log("\npaint order — the field stays behind the words:");
// The other half of removing the hero wrapper's z-index (DECISIONS 189).
// Nothing now lifts the copy above the canvas explicitly, so the guarantee is
// DOM order — and the way to know it held is to hide the canvas and find the
// headline's ink unchanged. Dust painted OVER the text would lighten it.
const paint = await (async () => {
  const browser3 = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
  const page3 = await browser3.newPage({
    viewport: { width: 1280, height: 900 },
    reducedMotion: "reduce",
  });
  await page3.goto(url, { waitUntil: "networkidle" });
  const box = await page3.locator('[data-testid="page-heading"]').boundingBox();
  const clip = {
    x: Math.round(box.x),
    y: Math.round(box.y),
    width: Math.round(box.width),
    height: Math.round(box.height),
  };
  const over = (await page3.screenshot({ clip })).toString("base64");
  await page3.evaluate(() => {
    document.querySelector("[data-rhythm-field]").style.visibility = "hidden";
  });
  const alone = (await page3.screenshot({ clip })).toString("base64");
  const out = await page3.evaluate(
    async ([a64, b64]) => {
      const decode = async (data) => {
        const image = new Image();
        image.src = `data:image/png;base64,${data}`;
        await image.decode();
        const canvas = document.createElement("canvas");
        canvas.width = image.naturalWidth;
        canvas.height = image.naturalHeight;
        canvas.getContext("2d").drawImage(image, 0, 0);
        return canvas.getContext("2d").getImageData(0, 0, canvas.width, canvas.height);
      };
      const withField = await decode(a64);
      const withoutField = await decode(b64);
      let ink = 0;
      let worst = 0;
      for (let i = 0; i < withoutField.data.length; i += 4) {
        // The SOLID middle of a stroke only. A glyph's anti-aliased edge is
        // part backdrop by construction — it changes whenever what is behind
        // it changes, correct layering included — so an edge-inclusive mask
        // reports the field as painting over text that it is sitting neatly
        // behind. Ink this dark is opaque.
        // 80 is a shade above the --ink token's own red channel (0x40 = 64),
        // so this admits solid strokes and nothing that is mostly paper.
        if (withoutField.data[i] > 80) continue;
        ink++;
        for (let c = 0; c < 3; c++) {
          worst = Math.max(worst, Math.abs(withField.data[i + c] - withoutField.data[i + c]));
        }
      }
      return { ink, worst };
    },
    [over, alone],
  );
  await browser3.close();
  return out;
})();
if (paint.ink < 500) {
  failed = true;
  console.error(`  FAIL only ${paint.ink} ink pixels found — the headline is not being read`);
} else if (paint.worst > 2) {
  failed = true;
  console.error(
    `  FAIL the field paints over the headline: hiding it changes the ink by ` +
      `${paint.worst} levels across ${paint.ink} pixels`,
  );
} else {
  console.log(
    `  ${paint.ink} ink pixels in the headline, unchanged by hiding the field ` +
      `(worst ${paint.worst} of 255)`,
  );
}

console.log(`\nscreenshots: ${WIDTHS.map((w) => `/tmp/kettle-${w}.png`).join(" ")}`);
process.exit(failed ? 1 : 0);
