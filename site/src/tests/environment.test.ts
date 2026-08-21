/**
 * @vitest-environment jsdom
 *
 * The invocation half of DECISIONS 146, ported from the webapp.
 *
 * This suite was never exposed to the storage half of that bug — nothing here
 * touches `localStorage`, so vitest's jsdom setup has no chance to hand it the
 * host's object instead of the browser's, and no stub is installed. What it does
 * share is the other exposure: every file here needs a DOM, and until now the
 * only thing saying so was one line in `vite.config.ts`. Pins rot unless
 * something reads them, which is what this file is for.
 */
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

// process.cwd() is site/ under vitest; import.meta.url is a transformed virtual
// path here and does not resolve to this directory.
const HERE = join(process.cwd(), "src", "tests");

describe("every test file pins its environment", () => {
  it("carries the @vitest-environment docblock", () => {
    const unpinned = readdirSync(HERE)
      .filter((name) => /\.test\.tsx?$/.test(name))
      .filter((name) => !readFileSync(join(HERE, name), "utf8").includes("@vitest-environment"));
    expect(unpinned).toEqual([]);
  });

  it("is actually running in one — document and window agree", () => {
    expect(typeof document).toBe("object");
    expect(globalThis.window).toBe(globalThis);
  });
});
