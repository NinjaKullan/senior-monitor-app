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
 * The asset's own alpha is still read afterwards, as a second line of defence
 * and because it names the cause when the composite check fails: since
 * DECISIONS 190 the drawing carries real transparency instead of a white
 * ground, so the corners must be empty rather than white, and the arch under
 * the handle must be an open window rather than a filled one.
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
      // artwork leaves EMPTY is a pixel the page must show unchanged. (Until
      // DECISIONS 190 the same samples were chosen by whiteness, because the
      // ground was white and reached the page through multiply; the drawing
      // is transparent now, so the mask reads alpha and the expected value is
      // simply the bare page.) Drawn at the SIZE THE PAGE DRAWS IT, because
      // that is the only version whose pixels line up with the screenshot:
      // the mark renders at a fraction of the artwork's width, so a rendered
      // pixel beside the handle is an average of empty ground and dark metal,
      // and testing the full-size art would call it ground and then fail on
      // the handle.
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
      const alpha = (data, x, y) => data.data[(y * data.width + x) * 4 + 3];
      let sampled = 0;
      let worst = { delta: -1 };
      const STEPS = 40;
      for (let row = 1; row < STEPS; row++) {
        for (let col = 1; col < STEPS; col++) {
          const x = Math.floor((a.width * col) / STEPS);
          const y = Math.floor((a.height * row) / STEPS);
          // Ground only if this pixel AND its neighbours are empty: the soft
          // shadow is real semi-transparent drawing, and one edge pixel away
          // it still tints what the page paints.
          let ground = true;
          for (let dy = -1; dy <= 1 && ground; dy++) {
            for (let dx = -1; dx <= 1 && ground; dx++) {
              const nx = Math.min(a.width - 1, Math.max(0, x + dx));
              const ny = Math.min(a.height - 1, Math.max(0, y + dy));
              // Strictly zero. An alpha of 4 is invisible to a person and
              // still darkens the page by four levels, which is exactly the
              // size of the departure this check is meant to notice.
              if (alpha(artData, nx, ny) !== 0) ground = false;
            }
          }
          if (!ground) continue; // the kettle, its shadow, or an edge beside them
          sampled++;
          const painted = pixel(a, x, y);
          const bare = pixel(b, x, y);
          // What source-over is defined to produce where the source is empty:
          // the backdrop, untouched. Nothing is drawn there, so nothing may
          // change there — no blend mode, no arithmetic, no allowance.
          const expected = bare;
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
    const w = image.naturalWidth;
    const h = image.naturalHeight;
    const full = ctx.getImageData(0, 0, w, h);
    const alphaAt = (x, y) => full.data[(y * w + x) * 4 + 3];

    // The handle window: the arch of empty space between the handle and the
    // lid. Found rather than guessed at a coordinate, so a re-export that
    // fills it in fails here instead of quietly gaining a lump of paper. A
    // pixel counts only when it is transparent AND has opaque drawing to its
    // left and right on the same row — which is what "enclosed" means.
    let enclosed = 0;
    let widestRun = { run: 0, y: -1, x: -1 };
    for (let y = 0; y < h; y++) {
      let first = -1;
      let last = -1;
      for (let x = 0; x < w; x++) {
        if (alphaAt(x, y) > 200) {
          if (first < 0) first = x;
          last = x;
        }
      }
      if (first < 0 || last - first < 4) continue;
      let run = 0;
      for (let x = first + 1; x < last; x++) {
        if (alphaAt(x, y) < 24) {
          enclosed++;
          run++;
          if (run > widestRun.run) widestRun = { run, y, x: x - run + 1 };
        } else {
          run = 0;
        }
      }
    }

    return {
      mode,
      size: [w, h],
      ground: {
        "top-left": alphaAt(1, 1),
        "top-right": alphaAt(w - 2, 1),
        "top-middle": alphaAt(Math.floor(w / 2), 2),
        "bottom-left": alphaAt(1, h - 2),
        "bottom-right": alphaAt(w - 2, h - 2),
      },
      window: { enclosed, widestRun },
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
    `  FAIL the mark paints where it draws nothing: at (${worst.x}, ${worst.y}) the page ` +
      `paints rgb(${worst.painted.join(", ")}) with the mark and rgb(${worst.bare.join(", ")}) ` +
      `without it — ${worst.delta} levels out over ${sampled} empty samples`,
  );
} else {
  console.log(
    `  ${sampled} empty samples, worst departure ${worst.delta} of 255 — where the ` +
      `drawing is empty the page is painted exactly as it is with no mark there`,
  );
}

// No blend mode, on any browser (DECISIONS 190): the drawing is transparent,
// so nothing has to be composited cleverly for the page to show through.
if (blend.mode !== "normal") {
  failed = true;
  console.error(
    `  FAIL the image carries blend mode "${blend.mode}" — the transparent asset needs ` +
      `none, and iOS Safari does not honour one across the rhythm canvas anyway`,
  );
} else {
  console.log("  blend mode: none — the drawing is transparent, not composited");
}
// Empty means empty: an alpha of 8 over a warm canvas is a rectangle nobody
// can name but everybody can see.
const ALPHA_CEILING = 8;
for (const [corner, alpha] of Object.entries(blend.ground)) {
  if (alpha > ALPHA_CEILING) {
    failed = true;
    console.error(
      `  FAIL ground at ${corner} has alpha ${alpha} of 255 — the background is still ` +
        `there, and it will paint over the wash on every browser`,
    );
  } else {
    console.log(`  ground at ${corner}: alpha ${alpha} — nothing there`);
  }
}
const { enclosed, widestRun } = blend.window;
if (enclosed < 2_000) {
  failed = true;
  console.error(
    `  FAIL only ${enclosed} enclosed transparent pixels — the window under the handle ` +
      `is filled, so the mark carries a lump of paper the wash cannot reach`,
  );
} else {
  console.log(
    `  handle window open: ${enclosed} enclosed transparent pixels, widest span ` +
      `${widestRun.run}px at row ${widestRun.y}`,
  );
}

console.log("\npaint order — the field stays behind the words:");
// The other half of removing the hero wrapper's z-index (DECISIONS 189):
// nothing lifts the copy above the canvas explicitly any more, so the
// guarantee is DOM order and this is how it is checked.
//
// Not by looking for the field's own dust over the text — that was the first
// version, and it is a coin toss: the dust is sparse and translucent, so a
// canvas painting straight over the headline can still leave every solid
// stroke pixel untouched, and the check reported green through a planted
// regression. So the canvas is FORCED opaque in a colour this palette does
// not contain, and the question becomes decisive: with an opaque sheet in
// that layer, is the headline still there? Below the copy, the text renders
// over it and every stroke survives. Above it, the words are simply gone.
const paint = await (async () => {
  // Greyscale anti-aliasing, so a rasterization difference cannot be read as
  // a layering one (Chromium picks subpixel or greyscale AA by what it knows
  // about the backdrop, and that changes when a compositing layer does).
  const browser3 = await chromium.launch({
    executablePath: "/opt/pw-browsers/chromium",
    args: ["--disable-lcd-text"],
  });
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
  const SHEET = "rgb(255, 0, 255)";
  await page3.addStyleTag({
    content: `[data-rhythm-field] { background: ${SHEET} !important; }`,
  });
  const covered = (await page3.screenshot({ clip })).toString("base64");
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
      const withSheet = await decode(a64);
      const withoutField = await decode(b64);
      const inkIn = (data) => {
        let n = 0;
        for (let i = 0; i < data.data.length; i += 4) {
          if (Math.max(data.data[i], data.data[i + 1], data.data[i + 2]) <= 80) n++;
        }
        return n;
      };
      // The sheet has to be reachable at all, or this passes on a page where
      // the style never applied.
      let sheet = 0;
      for (let i = 0; i < withSheet.data.length; i += 4) {
        const [r, g, b] = [withSheet.data[i], withSheet.data[i + 1], withSheet.data[i + 2]];
        if (r > 200 && g < 60 && b > 200) sheet++;
      }
      return { covered: inkIn(withSheet), alone: inkIn(withoutField), sheet };
    },
    [covered, alone],
  );
  await browser3.close();
  return out;
})();
if (paint.alone < 500) {
  failed = true;
  console.error(`  FAIL only ${paint.alone} ink pixels found — the headline is not being read`);
} else if (paint.sheet === 0) {
  failed = true;
  console.error("  FAIL the forced sheet never painted — this check proved nothing");
} else if (paint.covered < paint.alone * 0.9) {
  failed = true;
  console.error(
    `  FAIL the field paints over the headline: an opaque sheet in that layer leaves ` +
      `${paint.covered} of ${paint.alone} ink pixels standing`,
  );
} else {
  console.log(
    `  an opaque sheet in the field's layer leaves ${paint.covered} of ${paint.alone} ink ` +
      `pixels standing (${paint.sheet} sheet pixels around them) — the words are on top`,
  );
}

console.log("\ncomposition — the mark replaces breathing room rather than adding to it:");
// Two acceptances (DECISIONS 190). On a desktop the headline has to sit
// HIGHER than it did before the mark arrived, or the mark cost the page its
// opening rather than becoming it. On a phone the whole promise — kicker,
// headline, both sub paragraphs and the CTA — has to land inside the first
// viewport, because a reader who has to scroll to find out what this is has
// already been asked for something.
const composition = await (async () => {
  const browser4 = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
  const measure = async (viewport) => {
    const page4 = await browser4.newPage({ viewport, reducedMotion: "reduce" });
    await page4.goto(url, { waitUntil: "networkidle" });
    const out = await page4.evaluate(() => {
      const box = (selector) => {
        const node = document.querySelector(selector);
        if (!node) return null;
        const rect = node.getBoundingClientRect();
        return {
          top: Math.round(rect.top + window.scrollY),
          bottom: Math.round(rect.bottom + window.scrollY),
        };
      };
      const mark = document.querySelector(".kt-mark");
      const markBox = mark ? mark.getBoundingClientRect() : null;
      const kicker = document.querySelector('[data-testid="eyebrow"]');
      return {
        markWidth: markBox ? Math.round(markBox.width) : 0,
        markVisible: mark ? getComputedStyle(mark).display !== "none" : false,
        markToKicker:
          markBox && kicker
            ? Math.round(kicker.getBoundingClientRect().top - markBox.bottom)
            : null,
        mark: box(".kt-mark"),
        kicker: box('[data-testid="eyebrow"]'),
        heading: box('[data-testid="page-heading"]'),
        sub: box('[data-testid="hero-sub"]'),
        cta: box('#hero [data-testid="cta"]'),
      };
    });
    await page4.close();
    return out;
  };
  const desktop = await measure({ width: 1440, height: 900 });
  const phone = await measure({ width: 390, height: 844 });
  await browser4.close();
  return { desktop, phone };
})();

const { desktop, phone } = composition;
console.log(
  `  1440px  mark ${desktop.markWidth}px, mark→kicker ${desktop.markToKicker}px, ` +
    `headline top at ${desktop.heading.top}px`,
);
console.log(
  `   390px  mark ${phone.markWidth}px${phone.markVisible ? "" : " (hidden)"}, ` +
    `mark→kicker ${phone.markToKicker}px, headline top at ${phone.heading.top}px`,
);
console.log(
  `   390x844 first viewport: kicker ${phone.kicker.top}, headline ` +
    `${phone.heading.top}–${phone.heading.bottom}, sub ${phone.sub.top}–${phone.sub.bottom}, ` +
    `CTA ends ${phone.cta.bottom}`,
);
const VIEWPORT = 844;
if (phone.cta.bottom > VIEWPORT) {
  failed = true;
  console.error(
    `  FAIL the CTA ends ${phone.cta.bottom}px down a ${VIEWPORT}px viewport — the promise ` +
      `does not fit on a phone without scrolling`,
  );
} else {
  console.log(
    `  the whole promise fits: ${VIEWPORT - phone.cta.bottom}px to spare below the CTA at 390x844`,
  );
}

console.log(`\nscreenshots: ${WIDTHS.map((w) => `/tmp/kettle-${w}.png`).join(" ")}`);
process.exit(failed ? 1 : 0);
