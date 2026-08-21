#!/usr/bin/env node
/**
 * AC9 — the built HTML contains the page, not an empty root.
 *
 * The reader this product is for is often on a locked-down work laptop, a slow
 * connection, or a browser they did not choose. A single-page app that ships
 * `<div id="root"></div>` and 300kB of JavaScript gives them a blank page and no
 * way to know what Kettle is. So the page is prerendered at build time — and
 * because a prerender step that silently stops running looks fine to everyone
 * whose browser executes scripts, this reads the output back and fails loudly.
 *
 * The expected strings are derived from `src/copy.ts` rather than duplicated
 * here: copy that gets edited without this file being touched must still be
 * checked, or the guard rots into a test of six sentences nobody uses any more.
 */
import { readFileSync } from "node:fs";

const html = readFileSync(process.argv[2] ?? "dist/index.html", "utf8");
const copy = readFileSync("src/copy.ts", "utf8");
// The privacy placeholder is a hand-written static page rather than a React
// route, so its copy is checked against that file. Reading both here means the
// two cannot drift: edit the constant without editing the page and this fails.
const privacy = readFileSync("dist/privacy.html", "utf8");

/** Every `export const NAME = "…";` (single or wrapped across lines). */
const constants = new Map();
for (const match of copy.matchAll(/export const ([A-Z0-9_]+)\s*=\s*((?:"[^"]*"\s*\+?\s*)+);/g)) {
  constants.set(match[1], [...match[2].matchAll(/"([^"]*)"/g)].map((m) => m[1]).join(""));
}

// Array copy — the founder note's paragraphs (DECISIONS 132). Each element is
// required in the prerendered HTML under the array's own role suffix, so a
// letter is covered exactly like a sentence; a paragraph dropped from the
// render fails here by name.
const arrayElements = [];
for (const match of copy.matchAll(/export const ([A-Z0-9_]+)\s*=\s*\[([\s\S]*?)\]\s*as const;/g)) {
  for (const run of match[2].matchAll(/(?:"[^"]*"\s*\+?\s*)+/g)) {
    const value = [...run[0].matchAll(/"([^"]*)"/g)].map((m) => m[1]).join("");
    if (value) arrayElements.push([match[1], value]);
  }
}

/** The roles that must be legible with no JavaScript at all. */
const MUST_RENDER = /_(H1|H2|BODY|LEAD|EMPHASIS|TAB|EYEBROW|CTA|LABEL|ALT|NOTIF)$/;

const decoded = (html + privacy)
  .replace(/&#x27;|&#39;/g, "'")
  .replace(/&quot;/g, '"')
  .replace(/&amp;/g, "&")
  .replace(/&lt;/g, "<")
  .replace(/&gt;/g, ">")
  .replace(/&#x2F;/g, "/");

const missing = [];
for (const [name, value] of constants) {
  if (!MUST_RENDER.test(name)) continue;
  // Success and error states are rendered by the script after a submit; they
  // are the only copy legitimately absent from the static HTML.
  if (name === "WAITLIST_SUCCESS" || name === "WAITLIST_ERROR") continue;
  if (!decoded.includes(value)) missing.push(name);
}
for (const [name, value] of arrayElements) {
  if (!MUST_RENDER.test(name)) continue;
  if (!decoded.includes(value)) missing.push(`${name}: ${value.slice(0, 40)}…`);
}

if (constants.size === 0) {
  console.error("no copy constants parsed from src/copy.ts — this check proves nothing");
  process.exit(1);
}

if (missing.length > 0) {
  console.error("Copy missing from the prerendered HTML:");
  for (const name of missing) console.error(`  ${name}`);
  console.error("\nThe page must read with JavaScript off. Did the prerender step run?");
  process.exit(1);
}

// The meta description is copy — and, for most people who ever encounter this
// page, the *only* copy they read. It duplicated HERO_BODY by hand, which is
// exactly the pair that drifts: one gets edited at review, the other stays
// behind in a file nobody thinks of as containing sentences. Tied structurally
// here rather than by a second copy of the string (DECISIONS 85, PM-approved).
const description = html.match(/<meta\s+name="description"\s+content="([^"]*)"/s);
if (!description) {
  console.error("dist/index.html has no meta description");
  process.exit(1);
}
const meta = description[1]
  .replace(/\s+/g, " ")
  .replace(/&#x27;|&#39;/g, "'")
  .replace(/&quot;/g, '"')
  .replace(/&amp;/g, "&")
  .trim();
if (meta !== constants.get("HERO_BODY")) {
  console.error("The meta description has drifted from HERO_BODY.");
  console.error(`  index.html: ${meta}`);
  console.error(`  HERO_BODY:  ${constants.get("HERO_BODY")}`);
  process.exit(1);
}

// All four scenario panels, in the order a day happens.
const order = ["morning", "afternoon", "off", "seen"].map((set) =>
  html.indexOf(`data-scenario="${set}"`),
);
if (order.some((index) => index < 0) || order.some((index, i) => i > 0 && index < order[i - 1])) {
  console.error("The four scenario panels are missing or out of order in the static HTML.");
  process.exit(1);
}

console.log(
  `Prerendered HTML carries all ${constants.size + arrayElements.length} copy strings ` +
    "and four panels in order.",
);
