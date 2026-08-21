#!/usr/bin/env node
/**
 * AC8 — no byte of this page may reach an origin we do not control.
 *
 * Law #4 says no third-party analytics, tracking or telemetry. On a marketing
 * page that rule is easy to break by accident and impossible to see afterwards:
 * a font CDN, an embedded video, a "just this once" script tag, and suddenly
 * every visitor's request to read about elder monitoring has been announced to
 * somebody else. A visitor who has not yet decided to trust this product should
 * not have their interest in it disclosed to anyone.
 *
 * So this greps the built output for absolute URLs and fails on any host that is
 * not on the list below. Fonts are self-hosted (`@fontsource` vendors the woff2
 * into `dist/assets`), which is why nothing here needs a font CDN entry.
 */
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join } from "node:path";

const DIST = process.argv[2] ?? "dist";
/* A missing dist/ means the build did not finish (DECISIONS 139): every
   build clears its output first, so there is nothing stale to pass against. */
if (!existsSync(DIST)) {
  console.error(`${DIST} is missing — the build did not finish. Run \`npm run build\` first.`);
  process.exit(1);
}

/** Hosts we control, and the one reason each is allowed to appear. */
const OURS = new Set([
  "kettle-api.fly.dev", // the waitlist POST target
  "heykettle.com", // canonical site origin (DECISIONS 142)
  "www.heykettle.com",
  "localhost",
  "127.0.0.1",
]);

/**
 * Hosts that appear as *text* and are never fetched. Each is listed by name so
 * the exemption is visible rather than inferred, and the list stays short:
 *
 * - `www.w3.org` — the SVG/XML namespace identifier, an id that happens to be
 *   spelled like a URL.
 * - `reactjs.org` — React's minified-error link, baked into its production
 *   build's throw messages. It is a string in an exception, not a request; a
 *   visitor who never hits a React error never sees it, and one who does is not
 *   contacted by anyone either way.
 *
 * The narrowness is the point: a real beacon would be a host that is *not* on
 * this list, and `tests/foreignOrigins.test.ts` plants one to prove it fails.
 */
const NAMESPACES = new Set(["www.w3.org", "reactjs.org"]);

const TEXT = new Set([".html", ".js", ".css", ".json", ".svg", ".txt", ".webmanifest"]);
const URL_RE = /(?:https?:)?\/\/([A-Za-z0-9._-]+(?::\d+)?)/g;

function walk(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) out.push(...walk(path));
    else out.push(path);
  }
  return out;
}

let failures = 0;
let scanned = 0;

for (const file of walk(DIST)) {
  if (!TEXT.has(extname(file))) continue;
  scanned += 1;
  const source = readFileSync(file, "utf8");
  for (const [match, hostPort] of source.matchAll(URL_RE)) {
    const host = hostPort.split(":")[0];
    if (OURS.has(host) || NAMESPACES.has(host)) continue;
    failures += 1;
    console.error(`FOREIGN ORIGIN in ${file}: ${match}`);
  }
}

if (failures > 0) {
  console.error(
    `\n${failures} reference(s) to an origin we do not control. ` +
      "Self-host it, inline it, or drop it — this page makes no third-party requests.",
  );
  process.exit(1);
}

console.log(`No foreign origins in ${scanned} built files.`);
