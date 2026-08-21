import "@testing-library/jest-dom/vitest";
import { beforeEach } from "vitest";

/** Marks the Storage this file installs, so a test can prove the stub won. */
export const TEST_STORAGE = Symbol.for("kettle.testStorage");

/**
 * The suite owns its own `localStorage`. It does not borrow the host's.
 *
 * DECISIONS 146. `npm run ci` passed here and failed on the founder's machine,
 * on identical code and an identical lockfile: ten tests, `TypeError:
 * localStorage.setItem is not a function`. The split is in vitest's jsdom setup,
 * and it is worth understanding because it will happen again with a different
 * global. `populateGlobal` decides which of jsdom's window properties to install
 * on `globalThis`, and skips any name that (a) already exists on the host global
 * and (b) is absent from its own hard-coded KEYS list:
 *
 *     if (k in global) return keysArray.includes(k);
 *
 * `localStorage` is an own property of the jsdom window but is **not** in that
 * KEYS list. So on a machine where Node itself defines `globalThis.localStorage`
 * — webstorage enabled by a flag, an env var, or simply a newer Node — jsdom's
 * Storage is never installed and the host's object stays in place. Whatever that
 * object is, the tests then use it instead of the browser one.
 *
 * That makes the failure mode machine-dependent in both directions, and the
 * quiet direction is the dangerous one: if the host's object happens to *work*,
 * the suite goes green while the code under test writes to a different store
 * than the assertions read. A hard TypeError is the lucky outcome.
 *
 * So the stub below is installed unconditionally, after the environment has had
 * its turn, and it depends on nothing outside this file. Pinning
 * `@vitest-environment jsdom` per file is the other half and does not replace
 * this one — the shadowing happens *inside* jsdom setup, so naming the
 * environment does not prevent it.
 */
function createStorage(): Storage {
  // Items live as enumerable own properties, the way a real Storage exposes
  // them, so `Object.keys(storage)` lists the stored keys — `clearStoredSession`
  // walks exactly that to find `sb-*-auth-token`, and a Map-backed fake with no
  // enumerable keys would pass its own unit tests while breaking the caller.
  const storage = {} as Storage & Record<string, unknown>;

  const define = (name: string, value: unknown) =>
    Object.defineProperty(storage, name, { value, enumerable: false, writable: true });

  define("getItem", (key: string) =>
    Object.prototype.hasOwnProperty.call(storage, String(key))
      ? (storage[String(key)] as string)
      : null,
  );
  define("setItem", (key: string, value: unknown) => {
    Object.defineProperty(storage, String(key), {
      value: String(value),
      enumerable: true,
      writable: true,
      configurable: true,
    });
  });
  define("removeItem", (key: string) => {
    delete storage[String(key)];
  });
  define("clear", () => {
    for (const key of Object.keys(storage)) delete storage[key];
  });
  define("key", (index: number) => Object.keys(storage)[index] ?? null);
  Object.defineProperty(storage, "length", {
    get: () => Object.keys(storage).length,
    enumerable: false,
  });
  // A mark the guardrail test can read. Non-enumerable, so it never shows up in
  // `Object.keys(storage)` and never looks like a stored item. Without it, a test
  // asserting "storage works" would pass just as happily against the host's
  // object — which is the exact failure this file exists to stop.
  Object.defineProperty(storage, TEST_STORAGE, { value: true, enumerable: false });
  return storage;
}

for (const name of ["localStorage", "sessionStorage"] as const) {
  Object.defineProperty(globalThis, name, {
    value: createStorage(),
    configurable: true,
    writable: true,
  });
}

// Files must not inherit each other's storage. Registered here, so it runs
// before any per-file `beforeEach` that seeds a key.
beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});
