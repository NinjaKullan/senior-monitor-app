/**
 * The rhythm field's pixel probe — the check jsdom cannot stand in for.
 *
 * Two things are only true in a real browser: whether the field is visible at
 * all over the page's actual ground (DECISIONS 134), and whether the
 * three-fields canvas paints anything where the section's words are (DECISIONS
 * 135). Both are measured here by reading the canvas' own pixels and comparing
 * them against the laid-out boxes of the text, at the widths the ruling named.
 *
 * This is NOT part of `npm run ci`: it needs a browser, and Playwright is
 * deliberately not a dependency of this package. Run it by hand against a
 * preview server, or against the deployed site:
 *
 *   npm run build && npx vite preview --port 5288 &
 *   node scripts/probe-field.mjs http://127.0.0.1:5288/
 *
 * It exits non-zero if any canvas pixel lands inside a text box, so it can be
 * wired into a release check the day a browser is available in CI.
 */
import { chromium } from "/opt/node22/lib/node_modules/playwright/index.mjs";

const URL = process.argv[2] ?? "http://127.0.0.1:5288/";
const WIDTHS = [360, 390, 768, 1440];
/** The grounds the two fields are painted over, from tokens.css. */
const CREAM = [0xf6, 0xf2, 0xec];
const INK = [0x40, 0x3c, 0x36];

/** Runs in the page: how much of a canvas the eye actually receives. */
const measurePresence = ([index, bg]) => {
  const c = document.querySelectorAll("canvas[data-rhythm-field]")[index];
  if (!c) return null;
  const d = c.getContext("2d").getImageData(0, 0, c.width, c.height).data;
  const lum = (r, g, b) => 0.2126 * r + 0.7152 * g + 0.0722 * b;
  const bgL = lum(bg[0], bg[1], bg[2]);
  let painted = 0;
  let legible = 0;
  for (let k = 0; k < d.length; k += 4) {
    const a = d[k + 3] / 255;
    if (a <= 0.004) continue;
    painted++;
    const r = d[k] * a + bg[0] * (1 - a);
    const g = d[k + 1] * a + bg[1] * (1 - a);
    const b = d[k + 2] * a + bg[2] * (1 - a);
    if (Math.abs(lum(r, g, b) - bgL) >= 8) legible++;
  }
  const px = d.length / 4;
  return { paintedPct: (painted / px) * 100, legiblePct: (legible / px) * 100 };
};

/**
 * Runs in the page: for the three-fields canvas, every readable element's box
 * intersected with the canvas, and the count of painted pixels inside it.
 * Zero boxes and zero pixels is the passing answer.
 */
const measureCollision = () => {
  const canvas = document.querySelectorAll("canvas[data-rhythm-field]")[1];
  if (!canvas) return null;
  const section = canvas.closest("section");
  const box = canvas.getBoundingClientRect();
  const scaleX = canvas.width / box.width;
  const scaleY = canvas.height / box.height;
  const data = canvas.getContext("2d").getImageData(0, 0, canvas.width, canvas.height).data;

  const readable = Array.from(
    section.querySelectorAll("h1,h2,h3,p,li,a,button,label,span,strong,em"),
  ).filter((el) => (el.textContent ?? "").trim().length > 0);

  const overlaps = [];
  for (const el of readable) {
    const r = el.getBoundingClientRect();
    const left = Math.max(r.left, box.left);
    const right = Math.min(r.right, box.right);
    const top = Math.max(r.top, box.top);
    const bottom = Math.min(r.bottom, box.bottom);
    if (right <= left || bottom <= top) continue;

    let painted = 0;
    const x0 = Math.floor((left - box.left) * scaleX);
    const x1 = Math.ceil((right - box.left) * scaleX);
    const y0 = Math.floor((top - box.top) * scaleY);
    const y1 = Math.ceil((bottom - box.top) * scaleY);
    for (let y = y0; y < y1; y++) {
      for (let x = x0; x < x1; x++) {
        if (data[(y * canvas.width + x) * 4 + 3] > 1) painted++;
      }
    }
    overlaps.push({
      text: (el.textContent ?? "").trim().slice(0, 40),
      boxPx: Math.round((right - left) * (bottom - top)),
      paintedPx: painted,
    });
  }
  return { readable: readable.length, overlaps };
};

const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
let failed = false;

for (const width of WIDTHS) {
  const page = await browser.newPage({
    viewport: { width, height: 900 },
    deviceScaleFactor: 1,
  });
  await page.goto(URL, { waitUntil: "load" });
  await page.waitForTimeout(1200);
  await page.evaluate(() =>
    document.querySelectorAll("canvas[data-rhythm-field]")[1]?.scrollIntoView({ block: "center" }),
  );
  await page.waitForTimeout(3500);

  const collision = await page.evaluate(measureCollision);
  const fields = await page.evaluate(measurePresence, [1, INK]);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(1500);
  const hero = await page.evaluate(measurePresence, [0, CREAM]);

  if (!collision) {
    console.log(`${width}px: no three-fields canvas found`);
    failed = true;
  } else {
    const dirty = collision.overlaps.filter((o) => o.paintedPx > 0);
    const status = collision.overlaps.length === 0 ? "clear" : "OVERLAP";
    console.log(
      `${width}px  text/field: ${status} ` +
        `(${collision.readable} readable elements, ${collision.overlaps.length} intersecting, ` +
        `${dirty.reduce((n, o) => n + o.paintedPx, 0)} painted px inside them)  ` +
        `field ${fields.legiblePct.toFixed(2)}% legible  hero ${hero.legiblePct.toFixed(2)}% legible`,
    );
    for (const o of dirty) console.log(`    "${o.text}" — ${o.paintedPx} painted px`);
    if (collision.overlaps.length > 0) failed = true;
  }
  await page.close();
}

await browser.close();
if (failed) {
  console.error("FAIL: the field paints where the words are.");
  process.exit(1);
}
console.log("PASS: no canvas pixel lands in a text box at any tested width.");
