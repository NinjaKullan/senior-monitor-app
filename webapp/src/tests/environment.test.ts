/**
 * @vitest-environment jsdom
 *
 * The suite's verdict must not depend on which machine ran it (DECISIONS 146).
 *
 * `npm run ci` was green here and red on the founder's machine, on identical
 * code and an identical lockfile. The cause was vitest's jsdom setup declining
 * to install jsdom's `localStorage` whenever the host Node already defined one
 * — see `setup.ts` for the mechanism. Both halves of the fix are asserted here,
 * because both are invisible: nothing else in the suite fails if the storage
 * stub silently stops being installed, or if a file quietly loses its
 * environment pin. They just start meaning something different somewhere else.
 */
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { TEST_STORAGE } from "./setup";

// process.cwd() is webapp/ under vitest; import.meta.url is a transformed
// virtual path here and does not resolve to this directory.
const HERE = join(process.cwd(), "src", "tests");

describe("storage is the suite's own, not the host's", () => {
  it("is the stub setup.ts installed", () => {
    // The load-bearing assertion. "localStorage works" would pass against the
    // host's object too, and passing against the host's object IS the bug.
    for (const storage of [localStorage, sessionStorage]) {
      expect((storage as unknown as Record<symbol, unknown>)[TEST_STORAGE]).toBe(true);
    }
    expect(localStorage).not.toBe(sessionStorage);
  });

  it("behaves like a Storage, including the enumeration the app relies on", () => {
    localStorage.setItem("sb-abc-auth-token", "value");
    localStorage.setItem("other", "2");
    // `clearStoredSession` walks Object.keys to find the auth key. A Map-backed
    // fake would pass every other assertion here and break that caller.
    expect(Object.keys(localStorage).sort()).toEqual(["other", "sb-abc-auth-token"]);
    expect(localStorage.getItem("sb-abc-auth-token")).toBe("value");
    expect(localStorage.length).toBe(2);
    expect(localStorage.key(0)).toBe("sb-abc-auth-token");

    localStorage.removeItem("other");
    expect(localStorage.getItem("other")).toBeNull();
    localStorage.clear();
    expect(localStorage.length).toBe(0);
    expect(Object.keys(localStorage)).toEqual([]);
  });

  it("coerces like the real thing, so a test cannot rely on richer behaviour", () => {
    localStorage.setItem("n", 1 as unknown as string);
    expect(localStorage.getItem("n")).toBe("1");
    expect(localStorage.getItem("never-set")).toBeNull();
  });
});

describe("every test file pins its environment", () => {
  it("carries the @vitest-environment docblock", () => {
    // vite.config.ts sets jsdom globally, and that is one `--environment node`
    // on a command line away from not being true. A file that needs a DOM says
    // so in the file.
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
