/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * AC8 — the self-containment scan, checked for teeth.
 *
 * `scripts/check-foreign-origins.mjs` runs against `dist/` in CI, where a
 * failure is a build failure. This runs the same script against planted
 * directories, because a scan with an allowlist is only as good as how narrow
 * the allowlist is — and the two entries in it (`www.w3.org`, `reactjs.org`) are
 * exemptions somebody has to keep honest.
 */
import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const SITE = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SCRIPT = join(SITE, "scripts", "check-foreign-origins.mjs");

function scan(contents: string): { ok: boolean; output: string } {
  const dir = mkdtempSync(join(tmpdir(), "kettle-origins-"));
  writeFileSync(join(dir, "index.html"), contents);
  try {
    execFileSync("node", [SCRIPT, dir], { encoding: "utf8", stdio: "pipe" });
    return { ok: true, output: "" };
  } catch (error) {
    const err = error as { stderr?: string; stdout?: string };
    return { ok: false, output: `${err.stdout ?? ""}${err.stderr ?? ""}` };
  }
}

describe("the foreign-origin scan", () => {
  it("passes a page that fetches nothing", () => {
    expect(scan('<link href="/assets/font.woff2"><img src="/hero.png">').ok).toBe(true);
  });

  it("fails a font CDN, the most likely accident", () => {
    const result = scan('<link href="https://fonts.googleapis.com/css2?family=Fraunces">');
    expect(result.ok).toBe(false);
    expect(result.output).toContain("fonts.googleapis.com");
  });

  it("fails an analytics beacon however it is spelled", () => {
    for (const beacon of [
      '<script src="https://plausible.io/js/script.js"></script>',
      '<script src="//www.googletagmanager.com/gtm.js"></script>',
      'fetch("https://api.segment.io/v1/track")',
      '<img src="https://facebook.com/tr?id=1">',
    ]) {
      expect(scan(beacon).ok, beacon).toBe(false);
    }
  });

  it("allows only the two inert hosts, and nothing that resembles them", () => {
    // The exemptions are exact hosts. A subdomain someone registered is not one.
    expect(scan('<svg xmlns="http://www.w3.org/2000/svg">').ok).toBe(true);
    expect(scan('throw new Error("https://reactjs.org/docs/error-decoder.html")').ok).toBe(true);
    expect(scan('<script src="https://cdn.reactjs.org.evil.test/x.js">').ok).toBe(false);
    expect(scan('<script src="https://w3.org.evil.test/x.js">').ok).toBe(false);
  });

  it("allows the API we control, because the form has to reach it", () => {
    expect(scan('fetch("https://kettle-api.fly.dev/waitlist")').ok).toBe(true);
  });
});
