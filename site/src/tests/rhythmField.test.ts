/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * The Rhythm Field's hard requirements (DECISIONS 129/131), tested where
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
  fieldsGeometry,
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
    /** Where paint actually landed — the only way to see the dust move. */
    arcs: [] as { x: number; y: number; r: number }[],
    textAt: [] as { text: string; x: number; y: number }[],
    setTransform: () => count("setTransform"),
    clearRect: () => count("clearRect"),
    beginPath: () => count("beginPath"),
    arc(x: number, y: number, r: number) {
      count("arc");
      ctx.arcs.push({ x, y, r });
    },
    fill: () => count("fill"),
    stroke: () => count("stroke"),
    setLineDash: () => count("setLineDash"),
    save: () => count("save"),
    restore: () => count("restore"),
    fillText(text: string, x: number, y: number) {
      count("fillText");
      ctx.fillTexts.push(text);
      ctx.textAt.push({ text, x, y });
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

/**
 * A canvas whose context and geometry the test controls, in the shape the page
 * actually renders: section > band > canvas. The band is what the resolve
 * watches and what the reserved-band fix created; the section is what the
 * pointer listener attaches to.
 */
function fakeCanvas(ctx: ReturnType<typeof fakeContext> | null, w = 1000, h = 600) {
  const section = document.createElement("section");
  const band = document.createElement("div");
  const canvas = document.createElement("canvas");
  band.appendChild(canvas);
  section.appendChild(band);
  document.body.appendChild(section);
  Object.defineProperty(canvas, "clientWidth", { value: w });
  Object.defineProperty(canvas, "clientHeight", { value: h });
  canvas.getContext = (() => ctx) as never;
  const rect = () =>
    ({ top: 0, left: 0, width: w, height: h, bottom: h, right: w }) as DOMRect;
  band.getBoundingClientRect = rect;
  section.getBoundingClientRect = rect;
  canvas.getBoundingClientRect = rect;
  return canvas;
}

/** The section a fakeCanvas hangs under — the pointer listener's host. */
const sectionOf = (canvas: HTMLCanvasElement) => canvas.closest("section")!;

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
 * DECISIONS 134 — the mock stays the spec.
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
      ["dust radius", /tctx\.arc\(x \+ d\.ox, y \+ d\.oy, ([\d.]+), 0, 7\)/, [P.dustRadius]],
      [
        "dust orbit",
        /dr: (\.[\d]+) \+ Math\.random\(\) \* (\.[\d]+),/,
        [P.dustOrbitMin, P.dustOrbitSpread],
      ],
      ["ring size", /const ring = Math\.min\((\d+), W \/ (\d+)\);/, [P.fieldsRingMax, P.fieldsRingDivisor]],
      [
        "outer orbit centres",
        /\{ x: W \* \(0\.5 - (\.[\d]+)\), y: H \* (\.[\d]+) \}/,
        [P.fieldsSpread, P.fieldsRowY],
      ],
      ["middle orbit centre", /\{ x: W \* 0\.5,\s+y: H \* (\.[\d]+) \}/, [P.fieldsRowYMid]],
      ["stir reach", /dist < (\d+)\) \{/, [PRESENCE.cursorRadius]],
      ["stir push", /push = (\d+) \* falloff \* falloff/, [PRESENCE.cursorPush]],
      ["stir ease", /d\.ox \+= \(tox - d\.ox\) \* (\.[\d]+);/, [PRESENCE.cursorEase]],
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

/**
 * DECISIONS 135 — the band, and what may happen inside it.
 *
 * The collision the reviewers saw was geometry: three fixed-radius rings on a
 * canvas that shared its box with flowing text. The rings now size themselves
 * to a band of their own, so the arithmetic is testable without a browser —
 * these are the four widths the ruling named, run through the real function the
 * engine draws with.
 */
describe("the three orbits fit their band", () => {
  /** Viewport width -> the canvas it produces: the content column is
   *  max-w-3xl (768px) inside px-6 (24px a side). */
  const CANVAS_WIDTH = (viewport: number) => Math.min(768, viewport - 48);
  /** h-64 below the md breakpoint, md:h-80 at and above it. */
  const CANVAS_HEIGHT = (viewport: number) => (viewport >= 768 ? 320 : 256);
  /** A deliberately fat estimate of the widest label, at the canvas' 19px. */
  const LABEL_HALF_WIDTH = ("signal".length * 19 * 0.6) / 2;
  const MARGIN = 16;

  for (const viewport of [360, 390, 768, 1440]) {
    it(`fits three rings and their words at ${viewport}px`, () => {
      const W = CANVAS_WIDTH(viewport);
      const H = CANVAS_HEIGHT(viewport);
      const { ring, centres } = fieldsGeometry(W, H);

      expect(ring).toBeGreaterThan(LABEL_HALF_WIDTH + 4);
      for (const [i, c] of centres.entries()) {
        expect(c.x - ring, `ring ${i} runs off the left at ${viewport}`).toBeGreaterThanOrEqual(MARGIN);
        expect(c.x + ring, `ring ${i} runs off the right at ${viewport}`).toBeLessThanOrEqual(W - MARGIN);
        expect(c.y - ring, `ring ${i} runs off the top at ${viewport}`).toBeGreaterThanOrEqual(MARGIN);
        expect(c.y + ring, `ring ${i} runs off the bottom at ${viewport}`).toBeLessThanOrEqual(H - MARGIN);
      }
      // And they do not touch each other: three overlapping rings read as one
      // smear, which is what the fixed 56px did below ~600px of canvas.
      for (let i = 1; i < centres.length; i++) {
        expect(centres[i].x - centres[i - 1].x, `rings ${i - 1} and ${i} overlap`).toBeGreaterThan(
          2 * ring + 12,
        );
      }
    });
  }

  it("would catch the fixed radius coming back", () => {
    // The regression this exists for: a ring that ignores the band. At the
    // narrowest canvas the mock's old 56px overlaps its neighbour.
    const W = CANVAS_WIDTH(360);
    const { centres } = fieldsGeometry(W, CANVAS_HEIGHT(360));
    expect(centres[1].x - centres[0].x).toBeLessThan(2 * PRESENCE.fieldsRingMax + 12);
  });

  it("keeps every grain of dust inside its own ring", () => {
    // Orbits are fractions of the ring, not pixels, so the widest orbit at the
    // narrowest band is still an orbit rather than an escape.
    const widest = PRESENCE.dustOrbitMin + PRESENCE.dustOrbitSpread;
    expect(widest).toBeLessThan(1);
  });
});

describe("stirring the dust", () => {
  const LABELS = ["who", "signal", "when"] as const;

  /** One frame's worth of paint, with the dust made identical so two runs are
   *  comparable. */
  function frameAfter(steps: number, pointer: boolean, cursor?: { x: number; y: number; type: string }) {
    const random = vi.spyOn(Math, "random").mockReturnValue(0.4);
    frameQueue = [];
    const ctx = fakeContext();
    const canvas = fakeCanvas(ctx);
    const handle = startFieldsResolve(canvas, {
      reducedMotion: false,
      mobile: false,
      pointer,
      labels: LABELS,
    });
    if (cursor) {
      const event = new MouseEvent("pointermove", {
        clientX: cursor.x,
        clientY: cursor.y,
        bubbles: true,
      });
      Object.defineProperty(event, "pointerType", { value: cursor.type });
      sectionOf(canvas).dispatchEvent(event);
    }
    step(steps);
    ctx.arcs.length = 0;
    ctx.textAt.length = 0;
    step(1);
    handle.stop();
    random.mockRestore();
    return { arcs: [...ctx.arcs], textAt: [...ctx.textAt] };
  }

  const MOUSE = { x: 500, y: 324, type: "mouse" };
  type Arc = { x: number; y: number; r: number };
  const dustOnly = (arcs: Arc[]) => arcs.filter((a) => a.r === PRESENCE.dustRadius);
  const ringsOnly = (arcs: Arc[]) => arcs.filter((a) => a.r !== PRESENCE.dustRadius);

  it("attaches nothing at all without a fine pointer", () => {
    frameQueue = [];
    const canvas = fakeCanvas(fakeContext());
    const spy = vi.spyOn(sectionOf(canvas), "addEventListener");
    const handle = startFieldsResolve(canvas, {
      reducedMotion: false,
      mobile: false,
      pointer: false,
      labels: LABELS,
    });
    expect(spy.mock.calls.map(([type]) => type)).toEqual([]);
    handle.stop();
    spy.mockRestore();
  });

  it("attaches nothing under reduced motion, even with a pointer", () => {
    // The designed still stays still: the section returns before any listener
    // exists, so there is nothing to disturb it.
    frameQueue = [];
    const canvas = fakeCanvas(fakeContext());
    const spy = vi.spyOn(sectionOf(canvas), "addEventListener");
    const handle = startFieldsResolve(canvas, {
      reducedMotion: true,
      mobile: false,
      pointer: true,
      labels: LABELS,
    });
    expect(handle.debug.kind).toBe("static");
    expect(spy.mock.calls.map(([type]) => type)).toEqual([]);
    spy.mockRestore();
  });

  it("listens passively, and gives the listeners back on stop", () => {
    frameQueue = [];
    const canvas = fakeCanvas(fakeContext());
    const section = sectionOf(canvas);
    const added = vi.spyOn(section, "addEventListener");
    const removed = vi.spyOn(section, "removeEventListener");
    const handle = startFieldsResolve(canvas, {
      reducedMotion: false,
      mobile: false,
      pointer: true,
      labels: LABELS,
    });
    expect(added.mock.calls.map(([type]) => type)).toEqual(["pointermove", "pointerleave"]);
    // Passive, so the browser never waits on us before scrolling — and no
    // listener anywhere calls preventDefault.
    for (const [, , options] of added.mock.calls) {
      expect(options).toEqual({ passive: true });
    }
    handle.stop();
    expect(removed.mock.calls.map(([type]) => type)).toEqual(["pointermove", "pointerleave"]);
    added.mockRestore();
    removed.mockRestore();
  });

  it("pushes the dust away from the cursor, and nothing else", () => {
    const still = frameAfter(400, false);
    const stirred = frameAfter(400, true, MOUSE);

    const near = (a: { x: number; y: number }) => Math.hypot(a.x - MOUSE.x, a.y - MOUSE.y);
    const stillDust = dustOnly(still.arcs);
    const stirredDust = dustOnly(stirred.arcs);
    expect(stillDust.length).toBe(stirredDust.length);
    expect(stillDust.length).toBeGreaterThan(0);

    const moved = stirredDust.filter((d, i) => d.x !== stillDust[i].x || d.y !== stillDust[i].y);
    expect(moved.length, "no dust reacted to the cursor").toBeGreaterThan(0);
    for (const [i, d] of stirredDust.entries()) {
      if (d.x === stillDust[i].x && d.y === stillDust[i].y) continue;
      expect(near(d), "dust moved toward the cursor").toBeGreaterThan(near(stillDust[i]));
    }
    // Only dust. The orbit rings and the three words are exactly where they
    // were: the schema does not wobble when the mouse goes past.
    expect(ringsOnly(stirred.arcs)).toEqual(ringsOnly(still.arcs));
    expect(stirred.textAt).toEqual(still.textAt);
    expect(stirred.textAt.map((t) => t.text)).toEqual([...LABELS]);
  });

  it("ignores a pointer that is not a mouse", () => {
    // A touchscreen that manages to send us a pointermove still changes
    // nothing — the gate is belt and braces with the listener never attaching.
    const still = frameAfter(400, false);
    const touched = frameAfter(400, true, { ...MOUSE, type: "touch" });
    expect(dustOnly(touched.arcs)).toEqual(dustOnly(still.arcs));
  });

  it("lets the dust go home when the cursor leaves", () => {
    const random = vi.spyOn(Math, "random").mockReturnValue(0.4);
    frameQueue = [];
    const ctx = fakeContext();
    const canvas = fakeCanvas(ctx);
    const handle = startFieldsResolve(canvas, {
      reducedMotion: false,
      mobile: false,
      pointer: true,
      labels: LABELS,
    });
    const move = new MouseEvent("pointermove", { clientX: MOUSE.x, clientY: MOUSE.y });
    Object.defineProperty(move, "pointerType", { value: "mouse" });
    sectionOf(canvas).dispatchEvent(move);
    step(400);
    ctx.arcs.length = 0;
    step(1);
    const displaced = dustOnly([...ctx.arcs]);

    sectionOf(canvas).dispatchEvent(new MouseEvent("pointerleave"));
    step(400);
    ctx.arcs.length = 0;
    step(1);
    const recovered = dustOnly([...ctx.arcs]);
    handle.stop();
    random.mockRestore();

    // Recovery is toward the orbit, not merely different: after the cursor
    // leaves, the same grain sits closer to where the cursor used to be than
    // it did while being pushed.
    const near = (a: { x: number; y: number }) => Math.hypot(a.x - MOUSE.x, a.y - MOUSE.y);
    const closer = recovered.filter((d, i) => near(d) < near(displaced[i]));
    expect(closer.length).toBeGreaterThan(0);
  });
});
