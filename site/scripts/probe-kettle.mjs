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

console.log(`\nscreenshots: ${WIDTHS.map((w) => `/tmp/kettle-${w}.png`).join(" ")}`);
process.exit(failed ? 1 : 0);
