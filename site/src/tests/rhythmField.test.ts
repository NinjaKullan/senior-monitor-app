/**
 * The Rhythm Field's hard requirements (QUESTIONS 129/131), tested where
 * jsdom can reach them. The engine is the mock's Canvas 2D code made
 * production-shaped, so these tests pin behaviour, not pixels: reduced
 * motion is a single still frame, a missing context is inert, the loop
 * parks off screen, phones get half the density, the quiet sequence goes to
 * the parent's side first and comes back to ordinary — and the hero field
 * never draws a word (the content-honesty rule, counted at fillText).
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  FIELDS_DUST,
  FIELDS_DUST_MOBILE,
  HERO_MOTES,
  HERO_MOTES_MOBILE,
  PRESENCE,
  startFieldsResolve,
  startHeroField,
} from "@/lib/rhythmField";

/** A recording stand-in for CanvasRenderingContext2D. */
function fakeContext() {
  const calls: Record<string, number> = {};
  const count = (name: string) => {
    calls[name] = (calls[name] ?? 0) + 1;
  };
  const ctx = {
    calls,
    fillTexts: [] as string[],
    setTransform: () => count("setTransform"),
    clearRect: () => count("clearRect"),
    beginPath: () => count("beginPath"),
    arc: () => count("arc"),
    fill: () => count("fill"),
    stroke: () => count("stroke"),
    setLineDash: () => count("setLineDash"),
    save: () => count("save"),
    restore: () => count("restore"),
    fillText(text: string) {
      count("fillText");
      ctx.fillTexts.push(text);
    },
    fillStyle: "",
    strokeStyle: "",
    lineWidth: 0,
    shadowColor: "",
    shadowBlur: 0,
    font: "",
    textAlign: "",
  };
  return ctx;
}

/** A canvas whose context and geometry the test controls. */
function fakeCanvas(ctx: ReturnType<typeof fakeContext> | null, w = 1000, h = 600) {
  const section = document.createElement("section");
  const canvas = document.createElement("canvas");
  section.appendChild(canvas);
  document.body.appendChild(section);
  Object.defineProperty(canvas, "clientWidth", { value: w });
  Object.defineProperty(canvas, "clientHeight", { value: h });
  canvas.getContext = (() => ctx) as never;
  section.getBoundingClientRect = () =>
    ({ top: 0, left: 0, width: w, height: h, bottom: h, right: w }) as DOMRect;
  return canvas;
}

/** Frame-stepped requestAnimationFrame: the test drives time. */
let frameQueue: FrameRequestCallback[] = [];
function step(frames: number) {
  for (let i = 0; i < frames; i++) {
    const queue = frameQueue;
    frameQueue = [];
    for (const cb of queue) cb(i);
  }
}

beforeEach(() => {
  frameQueue = [];
  vi.stubGlobal("requestAnimationFrame", (cb: FrameRequestCallback) => {
    frameQueue.push(cb);
    return frameQueue.length;
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  document.body.innerHTML = "";
});

describe("the hero field", () => {
  it("is inert without a 2D context, and the page never knows", () => {
    const handle = startHeroField(fakeCanvas(null), {
      reducedMotion: false,
      mobile: false,
    });
    expect(handle.debug.kind).toBe("inert");
    expect(frameQueue).toHaveLength(0);
    handle.stop();
  });

  it("renders one still composition under prefers-reduced-motion", () => {
    const ctx = fakeContext();
    const handle = startHeroField(fakeCanvas(ctx), { reducedMotion: true, mobile: false });
    expect(handle.debug.kind).toBe("static");
    expect(ctx.calls.fill).toBeGreaterThan(0);
    // A still frame, not a slow animation: nothing was scheduled.
    expect(frameQueue).toHaveLength(0);
  });

  it("halves the density on phones", () => {
    const ctx = fakeContext();
    const desktop = startHeroField(fakeCanvas(ctx), { reducedMotion: false, mobile: false });
    const mobile = startHeroField(fakeCanvas(fakeContext()), {
      reducedMotion: false,
      mobile: true,
    });
    expect(desktop.debug.motes).toBe(HERO_MOTES);
    expect(mobile.debug.motes).toBe(HERO_MOTES_MOBILE);
    expect(HERO_MOTES).toBe(90); // the mock's density — motes, not hundreds
    desktop.stop();
    mobile.stop();
  });

  it("plays the quiet morning once after ~6s in view, to the parent's side, then returns", () => {
    const ctx = fakeContext();
    const parent = { x: 220, y: 430 };
    const handle = startHeroField(fakeCanvas(ctx), {
      reducedMotion: false,
      mobile: false,
      parentTarget: () => parent,
    });

    expect(handle.debug.mode()).toBe("ordinary");
    step(365);
    expect(handle.debug.mode()).toBe("quiet");
    // The ghost ring is dashed — the field's only dashed stroke.
    expect(ctx.calls.setLineDash).toBeGreaterThan(0);

    // The messenger travels slowly to the parent's frame and resolves; the
    // field then returns to ordinary on its own and never replays.
    step(1200);
    expect(handle.debug.mode()).toBe("ordinary");
    step(400);
    expect(handle.debug.mode()).toBe("ordinary");
    handle.stop();
  });

  it("never draws a word in the hero — the field carries no labels", () => {
    const ctx = fakeContext();
    const handle = startHeroField(fakeCanvas(ctx), {
      reducedMotion: false,
      mobile: false,
      parentTarget: () => ({ x: 200, y: 400 }),
    });
    step(1600); // ordinary, the whole quiet sequence, and back
    expect(ctx.calls.fillText ?? 0).toBe(0);
    handle.stop();
  });

  it("parks the loop while the canvas is off screen", () => {
    class FakeIO {
      static instance: FakeIO | null = null;
      callback: IntersectionObserverCallback;
      constructor(cb: IntersectionObserverCallback) {
        this.callback = cb;
        FakeIO.instance = this;
      }
      observe() {}
      disconnect() {}
      fire(isIntersecting: boolean) {
        this.callback(
          [{ isIntersecting } as IntersectionObserverEntry],
          this as unknown as IntersectionObserver,
        );
      }
    }
    vi.stubGlobal("IntersectionObserver", FakeIO as never);

    const ctx = fakeContext();
    const handle = startHeroField(fakeCanvas(ctx), { reducedMotion: false, mobile: false });
    step(5);
    const drawnWhileVisible = ctx.calls.clearRect ?? 0;
    expect(drawnWhileVisible).toBeGreaterThan(0);

    FakeIO.instance!.fire(false);
    step(30);
    // Parked before painting: the visibility guard runs ahead of clearRect,
    // so an off-screen field draws nothing at all.
    expect(ctx.calls.clearRect).toBe(drawnWhileVisible);

    FakeIO.instance!.fire(true);
    step(3);
    expect(ctx.calls.clearRect).toBeGreaterThan(drawnWhileVisible);
    handle.stop();
  });
});

describe("the three-fields resolve", () => {
  const LABELS = ["who", "signal", "when"] as const;

  it("is inert without a context", () => {
    const handle = startFieldsResolve(fakeCanvas(null), {
      reducedMotion: false,
      mobile: false,
      labels: LABELS,
    });
    expect(handle.debug.kind).toBe("inert");
  });

  it("renders the fully resolved composition as a still under reduced motion", () => {
    const ctx = fakeContext();
    const handle = startFieldsResolve(fakeCanvas(ctx), {
      reducedMotion: true,
      mobile: false,
      labels: LABELS,
    });
    expect(handle.debug.kind).toBe("static");
    // The three labels are there in the still — the section loses nothing.
    expect(ctx.fillTexts).toEqual(["who", "signal", "when"]);
    expect(frameQueue).toHaveLength(0);
    handle.stop();
  });

  it("draws exactly the schema's three words once resolved, and dims the free dust", () => {
    const ctx = fakeContext();
    const handle = startFieldsResolve(fakeCanvas(ctx), {
      reducedMotion: false,
      mobile: false,
      labels: LABELS,
    });
    // The section rect is fully in view, so resolveAmt climbs; run it in.
    step(400);
    const drawn = new Set(ctx.fillTexts);
    expect(drawn).toEqual(new Set(["who", "signal", "when"]));
    handle.stop();
  });

  it("halves the dust on phones", () => {
    const desktop = startFieldsResolve(fakeCanvas(fakeContext()), {
      reducedMotion: false,
      mobile: false,
      labels: LABELS,
    });
    const mobile = startFieldsResolve(fakeCanvas(fakeContext()), {
      reducedMotion: false,
      mobile: true,
      labels: LABELS,
    });
    expect(desktop.debug.motes).toBe(FIELDS_DUST);
    expect(mobile.debug.motes).toBe(FIELDS_DUST_MOBILE);
    desktop.stop();
    mobile.stop();
  });
});

describe("the page never waits for the field", () => {
  it("loads the engine only through a dynamic import, from idle", async () => {
    // Source-level: the sections reach the engine via useLazyField, whose
    // import() makes Vite split the chunk — the prerendered headline and CTA
    // exist before any animation code is requested. A static import creeping
    // into a section would bundle the engine into the critical path.
    const { readFileSync } = await import("node:fs");
    const { join, dirname } = await import("node:path");
    const { fileURLToPath } = await import("node:url");
    const src = join(dirname(fileURLToPath(import.meta.url)), "..");

    const lazy = readFileSync(join(src, "lib", "useLazyField.ts"), "utf8");
    expect(lazy).toMatch(/import\("\.\/rhythmField"\)/);
    expect(lazy).toMatch(/requestIdleCallback/);

    for (const section of ["sections/Hero.tsx", "sections/ThreeFields.tsx"]) {
      const source = readFileSync(join(src, section), "utf8");
      expect(source, `${section} must not import the engine statically`).not.toMatch(
        /import\s+\{[^}]*start(HeroField|FieldsResolve)[^}]*\}\s+from/,
      );
      // The type-only import is fine; it vanishes at build time.
      expect(source).toMatch(/import type \{ FieldHandle \}/);
    }
  });
});

/**
 * QUESTIONS 134 — the mock stays the spec.
 *
 * The presence pass was a founder ruling about how the field *looks*, and the
 * one thing jsdom can check about it is that the two files still agree: the
 * approved mock is where the character of the motion is decided, and an engine
 * that has quietly drifted away from it is a spec nobody can review. Each row
 * below reads the number back out of the mock's own source and compares it to
 * the constant the site ships.
 */
describe("the presence constants match the approved mock", () => {
  const MOCK = join(
    dirname(fileURLToPath(import.meta.url)),
    "..","..","..","docs","mockups","rhythm-field-mock.html",
  );
  const mockSource = () => readFileSync(MOCK, "utf8");

  /** Pull one or more numbers out of the mock by the expression around them. */
  const read = (source: string, pattern: RegExp): number[] => {
    const match = source.match(pattern);
    expect(match, `the mock no longer contains ${pattern}`).not.toBeNull();
    return match!.slice(1).map(Number);
  };

  it("finds the mock at all, with its canvas code intact", () => {
    const source = mockSource();
    expect(source).toContain("Rhythm Field mock");
    expect(source).toContain("requestAnimationFrame");
  });

  it("carries the same motes, pulses and dust as the engine", () => {
    const source = mockSource();
    const P = PRESENCE;
    const rows: [string, RegExp, number[]][] = [
      ["mote radius", /r: ([\d.]+) \+ Math\.random\(\) \* ([\d.]+),/, [P.moteRadiusMin, P.moteRadiusSpread]],
      [
        "mote drift",
        /dx: drift\(([\d.]+), ([\d.]+)\), dy: drift\(([\d.]+), ([\d.]+)\)/,
        [P.driftXMin, P.driftXSpread, P.driftYMin, P.driftYSpread],
      ],
      [
        "colour shares",
        /Math\.random\(\) < ([\d.]+) \? AMBER : \(Math\.random\(\) < ([\d.]+) \? SAGE/,
        [P.amberShare, P.sageShare],
      ],
      ["twinkle", /const tw = ([\d.]+) \+ ([\d.]+) \* Math\.sin/, [P.twinkleBase, P.twinkleSwing]],
      ["pulse cadence", /this\.mode === 'ordinary' && this\.t % (\d+) === 0/, [P.pulseCadence]],
      ["ghost cadence", /this\.missedAt\) % (\d+) === 0/, [P.pulseCadence]],
      ["pulse alpha", /r: 0, a: ([\d.]+) \}\);/, [P.pulseAlpha]],
      ["ghost alpha", /a: ([\d.]+), ghost: true/, [P.ghostAlpha]],
      ["pulse growth and fade", /p\.r \+= ([\d.]+); p\.a \*= ([\d.]+);/, [P.pulseGrowth, P.pulseDecay]],
      [
        "pulse width",
        /hctx\.lineWidth = ([\d.]+); hctx\.stroke\(\); hctx\.setLineDash/,
        [P.pulseWidth],
      ],
      ["messenger", /hctx\.arc\(g\.x, g\.y, ([\d.]+), 0, 7\)/, [P.messengerRadius]],
      [
        "messenger halo",
        /rgba\(\$\{AMBER\},(\.[\d]+)\)`; hctx\.lineWidth = ([\d.]+); hctx\.stroke/,
        [P.messengerHaloAlpha, P.messengerHaloWidth],
      ],
      ["dust radius", /tctx\.arc\(x, y, ([\d.]+), 0, 7\)/, [P.dustRadius]],
      ["dust alpha", /rgba\(244,237,228,\$\{([\d.]+) \+ ([\d.]+) \* k\}\)/, [P.dustAlphaFloor, P.dustAlphaRange]],
      ["dust ring width", /tctx\.lineWidth = ([\d.]+); tctx\.stroke\(\)/, [P.dustRingWidth]],
    ];
    for (const [name, pattern, expected] of rows) {
      expect(read(source, pattern), `${name} drifted from the mock`).toEqual(expected);
    }
  });

  it("keeps the density the ruling did not touch", () => {
    // More presence, not more motes: the founder raised size, brightness,
    // colour share and pace, and said nothing about how many there are.
    const source = mockSource();
    expect(read(source, /for \(let i = 0; i < (\d+); i\+\+\) \{\n\s+this\.motes/)).toEqual([HERO_MOTES]);
    expect(read(source, /for \(let i = 0; i < (\d+); i\+\+\) \{\n\s+dust\.push/)).toEqual([FIELDS_DUST]);
  });
});
