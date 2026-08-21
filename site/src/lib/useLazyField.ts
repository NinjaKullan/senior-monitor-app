import { useEffect, useRef } from "react";
import type { FieldHandle } from "./rhythmField";

type FieldModule = typeof import("./rhythmField");

/**
 * Mount a rhythm-field canvas without ever making the page wait for it.
 *
 * The engine loads via dynamic import from an idle callback, so it is a
 * separate chunk fetched after first paint: the headline and CTA are in the
 * prerendered HTML and hydrate before any animation code is even requested
 * (the no-LCP-regression requirement, DECISIONS 129). A canvas that cannot
 * give a 2D context makes the engine return an inert handle, and unmounting
 * stops whatever started.
 */
export function useLazyField(
  start: (module: FieldModule, canvas: HTMLCanvasElement) => FieldHandle,
) {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    let handle: FieldHandle | null = null;
    let cancelled = false;

    const idle: (cb: () => void) => unknown =
      typeof window.requestIdleCallback === "function"
        ? (cb) => window.requestIdleCallback(cb)
        : (cb) => window.setTimeout(cb, 1);

    idle(() => {
      if (cancelled) return;
      import("./rhythmField").then((module) => {
        if (cancelled) return;
        handle = start(module, canvas);
      });
    });

    return () => {
      cancelled = true;
      handle?.stop();
    };
  }, [start]);

  return ref;
}
