/**
 * The mobile check, run in a real browser (QUESTIONS 136).
 *
 * The founder reviews this site on a phone, and twice now he has found on a
 * handset something no test could see: the field's orbits sitting on the
 * section's words, and the scenario tabs folding into a ragged two-line block.
 * jsdom lays nothing out, so neither was findable in the suite — the classes
 * are pinned with their arithmetic beside them, but arithmetic is not layout.
 *
 * This script is the layout half. At each width it asks three things of the
 * rendered page:
 *
 *   1. Nothing overflows the viewport horizontally — not the document, not any
 *      element in it. A page a reader can pan sideways is a bug every time.
 *   2. The scenario tab row is one line — every tab shares a top edge.
 *   3. Every tab is at least 40px tall, and the row's fade is present exactly
 *      when the row is actually clipped.
 *
 * It also drives the scenario tabs: each tab is clicked and required to be
 * wholly inside its strip afterwards, which is the behaviour the strip's
 * scroll arithmetic exists for and the one thing the unit tests take on trust.
 *
 * NOT part of `npm run ci`: it needs a browser, and Playwright is deliberately
 * not a dependency of this package. Run it against a preview server:
 *
 *   npm run build && npx vite preview --port 5288 &
 *   node scripts/probe-responsive.mjs http://127.0.0.1:5288/
 *
 * Exits non-zero on any finding, so it can be wired into a release check the
 * day a browser is available in CI.
 */
import { chromium } from "/opt/node22/lib/node_modules/playwright/index.mjs";

const URL = process.argv[2] ?? "http://127.0.0.1:5288/";
/** The phones the founder actually holds, plus the tablet breakpoint. */
const WIDTHS = [360, 390, 428, 768];
const MIN_TAP_TARGET = 40;

/** Runs in the page: everything that sticks out past the viewport. */
const findOverflow = () => {
  const limit = document.documentElement.clientWidth;
  const wide = [];
  /** Something above this element already clips it, so what it sticks out of
   *  is that box and not the page — a tab inside the scrolling tab strip is
   *  the intended case, and the page's own overflow number is the check that
   *  still catches a strip which is itself too wide. */
  const isClipped = (el) => {
    for (let node = el.parentElement; node && node !== document.body; node = node.parentElement) {
      const overflowX = getComputedStyle(node).overflowX;
      if (overflowX === "auto" || overflowX === "scroll" || overflowX === "hidden") return true;
    }
    return false;
  };

  for (const el of Array.from(document.querySelectorAll("body *"))) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    if (isClipped(el)) continue;
    // Anything left is laid out against the page itself, and is never allowed
    // to stick out past the viewport.
    if (r.right > limit + 1 || r.left < -1) {
      wide.push({
        tag: el.tagName.toLowerCase(),
        testid: el.getAttribute("data-testid") ?? "",
        text: (el.textContent ?? "").trim().slice(0, 40),
        left: Math.round(r.left),
        right: Math.round(r.right),
      });
    }
  }
  return {
    documentOverflow: Math.round(document.documentElement.scrollWidth - limit),
    wide: wide.slice(0, 8),
  };
};

/** Runs in the page: the tab row's geometry and its scroll behaviour. */
const inspectTabs = () => {
  const strip = document.querySelector('[data-testid="scenario-tablist"]');
  if (!strip) return null;
  const tabs = Array.from(strip.querySelectorAll('[data-testid="scenario-tab"]'));
  const tops = tabs.map((t) => Math.round(t.getBoundingClientRect().top));
  const heights = tabs.map((t) => Math.round(t.getBoundingClientRect().height));
  return {
    count: tabs.length,
    lines: new Set(tops).size,
    minHeight: Math.min(...heights),
    clipped: strip.scrollWidth > strip.clientWidth,
    faded: strip.className.includes("fade-edge-x"),
    scrollWidth: strip.scrollWidth,
    clientWidth: strip.clientWidth,
  };
};

/** Runs in the page: is the tab at `index` wholly inside its strip? */
const tabFullyVisible = (index) => {
  const strip = document.querySelector('[data-testid="scenario-tablist"]');
  const tab = strip.querySelectorAll('[data-testid="scenario-tab"]')[index];
  const s = strip.getBoundingClientRect();
  const t = tab.getBoundingClientRect();
  return { left: Math.round(t.left - s.left), right: Math.round(s.right - t.right) };
};

const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
const findings = [];

for (const width of WIDTHS) {
  const page = await browser.newPage({ viewport: { width, height: 844 }, deviceScaleFactor: 1 });
  await page.goto(URL, { waitUntil: "load" });
  await page.waitForTimeout(900);

  const overflow = await page.evaluate(findOverflow);
  if (overflow.documentOverflow > 1) {
    findings.push(`${width}px: the page scrolls sideways by ${overflow.documentOverflow}px`);
  }
  for (const el of overflow.wide) {
    findings.push(
      `${width}px: <${el.tag}${el.testid ? ` data-testid="${el.testid}"` : ""}> ` +
        `spans ${el.left}..${el.right} — "${el.text}"`,
    );
  }

  const tabs = await page.evaluate(inspectTabs);
  if (!tabs) {
    findings.push(`${width}px: no scenario tab row found`);
  } else {
    if (tabs.lines !== 1) findings.push(`${width}px: the tab row wrapped onto ${tabs.lines} lines`);
    if (tabs.minHeight < MIN_TAP_TARGET) {
      findings.push(`${width}px: a tab is only ${tabs.minHeight}px tall`);
    }
    if (tabs.clipped !== tabs.faded) {
      findings.push(
        `${width}px: the row is ${tabs.clipped ? "clipped" : "not clipped"} but ` +
          `${tabs.faded ? "is" : "is not"} faded`,
      );
    }

    // Every tab, clicked, must end up wholly inside the strip.
    const buttons = await page.$$('[data-testid="scenario-tab"]');
    for (let i = 0; i < buttons.length; i++) {
      await buttons[i].click();
      await page.waitForTimeout(120);
      const seen = await page.evaluate(tabFullyVisible, i);
      if (seen.left < -1 || seen.right < -1) {
        findings.push(`${width}px: tab ${i} sits ${seen.left}px / ${seen.right}px from the edges`);
      }
    }

    console.log(
      `${width}px  tabs: ${tabs.count} on ${tabs.lines} line, ${tabs.minHeight}px tall, ` +
        `row ${tabs.scrollWidth}px in ${tabs.clientWidth}px ` +
        `(${tabs.clipped ? "clipped, faded" : "fits, no fade"})  ` +
        `page overflow ${overflow.documentOverflow}px`,
    );
  }
  await page.close();
}

await browser.close();
if (findings.length > 0) {
  console.error("\nFAIL:");
  for (const finding of findings) console.error(`  ${finding}`);
  process.exit(1);
}
console.log("PASS: no wrap, no overflow, every tab reachable and in view.");
