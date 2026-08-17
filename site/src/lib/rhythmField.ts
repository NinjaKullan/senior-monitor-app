/**
 * The Rhythm Field (QUESTIONS 129/131) — a faithful Canvas 2D port of the
 * approved mock, docs/mockups/rhythm-field-mock.html. The mock is the spec
 * for feel, pace, density and palette; the constants below are its constants,
 * and a change to the character of the motion belongs there first.
 *
 * Content honesty, non-negotiable: the motion depicts signals arriving and
 * the parent-first ask — the ladder, animated. There is no trend, no score,
 * no inference anywhere in this file, and the hero field draws no text at
 * all (a test counts fillText calls to keep that true).
 *
 * The page must never need this file: it is loaded lazily after first paint,
 * a missing 2D context returns an inert handle, `prefers-reduced-motion`
 * renders a single static composition, and an IntersectionObserver parks the
 * loop whenever the canvas is off screen.
 */

/* The mock's palette, read from tokens.css — canvas has no CSS, but its
 * colours still live in the one file that holds every colour (AC1). Each
 * token is a channel triplet the engine composes into paint; the values are
 * the approved mock's, verbatim, in tokens.css. */
export interface FieldPalette {
  signal: string;
  sage: string;
  graphite: string;
  dust: string;
  label: string;
  glow: string;
}

const FIELD_TOKENS: { [K in keyof FieldPalette]: string } = {
  signal: "--field-signal",
  sage: "--field-sage",
  graphite: "--field-graphite",
  dust: "--field-dust",
  label: "--field-label",
  glow: "--field-glow",
};

export function readPalette(): FieldPalette {
  const styles = window.getComputedStyle(document.documentElement);
  const entries = Object.entries(FIELD_TOKENS) as [keyof FieldPalette, string][];
  const palette = {} as FieldPalette;
  for (const [key, token] of entries) palette[key] = styles.getPropertyValue(token).trim();
  return palette;
}

/* Density: the mock runs 90 motes and 140 dust; phones get half. */
export const HERO_MOTES = 90;
export const HERO_MOTES_MOBILE = 45;
export const FIELDS_DUST = 140;
export const FIELDS_DUST_MOBILE = 70;

/* The quiet-morning sequence, in frames (~60/s): trigger after ~6 s in view,
 * ghost rings on the mock's pulse cadence, the messenger leaving one beat
 * after the pulses stop, and a short grace after the sage ring fades before
 * the field returns to ordinary. Played once per page load. */
const QUIET_TRIGGER_FRAMES = 360;
const PULSE_CADENCE = 150;
const MESSENGER_DELAY = 90;
const RESOLVE_FRAMES = 160;
const RESOLVE_GRACE = 60;

export interface FieldHandle {
  stop(): void;
  /** For tests: the numbers a reviewer would otherwise eyeball. */
  debug: {
    kind: "inert" | "static" | "animated";
    motes: number;
    mode(): string;
    frames(): number;
  };
}

export interface HeroFieldOptions {
  reducedMotion: boolean;
  mobile: boolean;
  /** Tests inject; the page reads tokens.css. */
  palette?: FieldPalette;
  /** Canvas-relative centre of the parent's photograph — where the messenger
   *  goes first. Falls back to the mock's fractions when unknowable. */
  parentTarget?: () => { x: number; y: number } | null;
}

interface Mote {
  x: number;
  y: number;
  r: number;
  dx: number;
  dy: number;
  c: string;
  ph: number;
}

interface Pulse {
  x: number;
  y: number;
  r: number;
  a: number;
  ghost?: boolean;
}

const INERT: FieldHandle = {
  stop() {},
  debug: { kind: "inert", motes: 0, mode: () => "inert", frames: () => 0 },
};

function sizeCanvas(c: HTMLCanvasElement): void {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  c.width = c.clientWidth * dpr;
  c.height = c.clientHeight * dpr;
  c.getContext("2d")?.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function makeMotes(count: number, W: number, H: number, palette: FieldPalette): Mote[] {
  const motes: Mote[] = [];
  for (let i = 0; i < count; i++) {
    motes.push({
      x: Math.random() * W,
      y: Math.random() * H,
      r: 1 + Math.random() * 2.2,
      dx: (Math.random() - 0.5) * 0.18,
      dy: (Math.random() - 0.5) * 0.12,
      c: Math.random() < 0.12 ? palette.signal : Math.random() < 0.4 ? palette.sage : palette.graphite,
      ph: Math.random() * Math.PI * 2,
    });
  }
  return motes;
}

function drawMotes(
  ctx: CanvasRenderingContext2D,
  motes: Mote[],
  W: number,
  H: number,
  t: number,
  drift: boolean,
): void {
  for (const m of motes) {
    if (drift) {
      m.x = (m.x + m.dx + W) % W;
      m.y = (m.y + m.dy + H) % H;
    }
    const tw = 0.35 + 0.3 * Math.sin(t / 60 + m.ph);
    ctx.beginPath();
    ctx.arc(m.x, m.y, m.r, 0, 7);
    ctx.fillStyle = `rgba(${m.c},${tw})`;
    ctx.fill();
  }
}

/** Watch visibility where the platform allows; assume visible where it can't. */
function observeVisibility(el: Element, onChange: (visible: boolean) => void): () => void {
  if (typeof IntersectionObserver === "undefined") {
    onChange(true);
    return () => {};
  }
  const io = new IntersectionObserver((entries) => {
    for (const entry of entries) onChange(entry.isIntersecting);
  });
  io.observe(el);
  return () => io.disconnect();
}

/**
 * The hero field: drifting motes, soft amber pulses for ordinary signals,
 * and — once, slowly, after the hero has been in view about six seconds —
 * the quiet morning: pulses stop, a dashed ghost ring marks the one that
 * should have come, a single amber mote travels to the parent's side first,
 * and a sage ring says the question was asked, quietly. Then ordinary again.
 */
export function startHeroField(
  canvas: HTMLCanvasElement,
  opts: HeroFieldOptions,
): FieldHandle {
  const ctx = canvas.getContext("2d");
  if (!ctx) return INERT;

  sizeCanvas(canvas);
  const palette = opts.palette ?? readPalette();
  const moteCount = opts.mobile ? HERO_MOTES_MOBILE : HERO_MOTES;
  const motes = makeMotes(moteCount, canvas.clientWidth, canvas.clientHeight, palette);

  if (opts.reducedMotion) {
    // One still composition: the field mid-breath, one soft ring, no loop.
    const W = canvas.clientWidth;
    const H = canvas.clientHeight;
    drawMotes(ctx, motes, W, H, 30, false);
    ctx.beginPath();
    ctx.arc(W * 0.45, H * 0.38, 34, 0, 7);
    ctx.strokeStyle = `rgba(${palette.signal},0.3)`;
    ctx.lineWidth = 1.4;
    ctx.stroke();
    return {
      stop() {},
      debug: { kind: "static", motes: moteCount, mode: () => "static", frames: () => 0 },
    };
  }

  let t = 0;
  let visibleFrames = 0;
  let mode: "ordinary" | "quiet" = "ordinary";
  let quietAt = 0;
  let played = false;
  let pulses: Pulse[] = [];
  let messenger: {
    x: number;
    y: number;
    tx: number;
    ty: number;
    done: boolean;
    doneAt: number;
  } | null = null;

  let stopped = false;
  let visible = true;
  let scheduled = false;

  const onResize = () => sizeCanvas(canvas);
  window.addEventListener("resize", onResize);

  function beginQuiet(): void {
    mode = "quiet";
    quietAt = t;
    played = true;
  }

  function tick(): void {
    scheduled = false;
    if (stopped || !visible) return;
    t++;
    const W = canvas.clientWidth;
    const H = canvas.clientHeight;
    ctx!.clearRect(0, 0, W, H);

    drawMotes(ctx!, motes, W, H, t, true);

    // Ordinary signals arriving: a soft ring every couple of seconds.
    if (mode === "ordinary" && t % PULSE_CADENCE === 0) {
      pulses.push({
        x: W * (0.25 + Math.random() * 0.5),
        y: H * (0.25 + Math.random() * 0.35),
        r: 0,
        a: 0.5,
      });
    }

    // The quiet morning plays itself once, after ~6 s of the hero being seen.
    visibleFrames++;
    if (!played && visibleFrames >= QUIET_TRIGGER_FRAMES) beginQuiet();

    if (mode === "quiet") {
      // The absence: pulses stop; a dashed ghost marks where one belonged.
      if ((t - quietAt) % PULSE_CADENCE === 0) {
        pulses.push({ x: W * 0.5, y: H * 0.33, r: 0, a: 0.28, ghost: true });
      }
      // One beat later, the messenger leaves for the parent's side first.
      if (!messenger && t - quietAt >= MESSENGER_DELAY) {
        const target = opts.parentTarget?.() ?? null;
        messenger = {
          x: W * 0.5,
          y: H * 0.35,
          tx: target ? target.x : W * 0.3,
          ty: target ? target.y : H * 0.72,
          done: false,
          doneAt: 0,
        };
      }
    }

    pulses = pulses.filter((p) => p.a > 0.01);
    for (const p of pulses) {
      p.r += 0.8;
      p.a *= 0.975;
      ctx!.beginPath();
      ctx!.arc(p.x, p.y, p.r, 0, 7);
      ctx!.strokeStyle = p.ghost ? `rgba(${palette.graphite},${p.a})` : `rgba(${palette.signal},${p.a})`;
      ctx!.setLineDash(p.ghost ? [4, 6] : []);
      ctx!.lineWidth = 1.4;
      ctx!.stroke();
      ctx!.setLineDash([]);
    }

    if (messenger && !messenger.done) {
      const g = messenger;
      const k = 0.012;
      g.x += (g.tx - g.x) * k;
      g.y += (g.ty - g.y) * k;
      ctx!.beginPath();
      ctx!.arc(g.x, g.y, 3.2, 0, 7);
      ctx!.fillStyle = `rgba(${palette.signal},0.9)`;
      ctx!.fill();
      ctx!.beginPath();
      ctx!.arc(g.x, g.y, 8 + 3 * Math.sin(t / 12), 0, 7);
      ctx!.strokeStyle = `rgba(${palette.signal},0.35)`;
      ctx!.stroke();
      if (Math.abs(g.x - g.tx) < 6 && Math.abs(g.y - g.ty) < 6) {
        g.done = true;
        g.doneAt = t;
      }
    }
    if (messenger?.done) {
      // The question was asked, quietly: a sage ring, then ordinary again.
      const dt = t - messenger.doneAt;
      if (dt < RESOLVE_FRAMES) {
        ctx!.beginPath();
        ctx!.arc(messenger.tx, messenger.ty, 10 + dt * 0.5, 0, 7);
        ctx!.strokeStyle = `rgba(${palette.sage},${Math.max(0, 0.5 - dt / 320)})`;
        ctx!.lineWidth = 2;
        ctx!.stroke();
      } else if (dt > RESOLVE_FRAMES + RESOLVE_GRACE) {
        messenger = null;
        mode = "ordinary";
      }
    }

    schedule();
  }

  function schedule(): void {
    if (stopped || !visible || scheduled) return;
    scheduled = true;
    requestAnimationFrame(tick);
  }

  const unobserve = observeVisibility(canvas, (now) => {
    visible = now;
    schedule();
  });

  schedule();

  return {
    stop() {
      stopped = true;
      unobserve();
      window.removeEventListener("resize", onResize);
    },
    debug: { kind: "animated", motes: moteCount, mode: () => mode, frames: () => t },
  };
}

export interface FieldsResolveOptions {
  reducedMotion: boolean;
  mobile: boolean;
  labels: readonly [string, string, string];
  /** Tests inject; the page reads tokens.css. */
  palette?: FieldPalette;
}

interface Dust {
  x: number;
  y: number;
  home: number;
  dr: number;
  ph: number;
  resolve: number;
}

/**
 * The three-fields resolve: cream dust drifts free, and as the section
 * scrolls into view it settles into three slow orbits labelled with the
 * schema's own words — 19px cream over a dark glow, drawn above the dust,
 * exactly as the mock's second section.
 */
export function startFieldsResolve(
  canvas: HTMLCanvasElement,
  opts: FieldsResolveOptions,
): FieldHandle {
  const ctx = canvas.getContext("2d");
  const section = canvas.parentElement;
  if (!ctx || !section) return INERT;

  sizeCanvas(canvas);
  const palette = opts.palette ?? readPalette();
  const dustCount = opts.mobile ? FIELDS_DUST_MOBILE : FIELDS_DUST;
  const dust: Dust[] = [];
  for (let i = 0; i < dustCount; i++) {
    dust.push({
      x: Math.random(),
      y: Math.random(),
      home: i % 3,
      dr: 30 + Math.random() * 22,
      ph: Math.random() * 7,
      resolve: Math.random(),
    });
  }

  const W = () => canvas.clientWidth;
  const H = () => canvas.clientHeight;
  const targets = () => [
    { x: W() * 0.3, y: H() * 0.62, label: opts.labels[0] },
    { x: W() * 0.5, y: H() * 0.68, label: opts.labels[1] },
    { x: W() * 0.7, y: H() * 0.62, label: opts.labels[2] },
  ];

  function drawFrame(tt: number, resolveAmt: number): void {
    ctx!.clearRect(0, 0, W(), H());
    const T = targets();
    for (const d of dust) {
      const t0 = T[d.home];
      const ang = tt / 200 + d.ph;
      const homex = t0.x + Math.cos(ang) * d.dr;
      const homey = t0.y + Math.sin(ang) * d.dr * 0.6;
      const freex = d.x * W();
      const freey = d.y * H();
      const k = Math.min(1, Math.max(0, (resolveAmt - d.resolve * 0.35) * 1.6));
      const x = freex + (homex - freex) * k;
      const y = freey + (homey - freey) * k;
      ctx!.beginPath();
      ctx!.arc(x, y, 1.6, 0, 7);
      ctx!.fillStyle = `rgba(${palette.dust},${0.14 + 0.34 * k})`;
      ctx!.fill();
    }
    if (resolveAmt > 0.5) {
      const a = Math.min(1, (resolveAmt - 0.5) * 2.2);
      for (const t0 of T) {
        ctx!.beginPath();
        ctx!.arc(t0.x, t0.y, 56, 0, 7);
        ctx!.strokeStyle = `rgba(${palette.signal},${a * 0.8})`;
        ctx!.lineWidth = 1.4;
        ctx!.stroke();
        ctx!.save();
        ctx!.shadowColor = `rgba(${palette.glow},0.9)`;
        ctx!.shadowBlur = 10;
        ctx!.fillStyle = `rgba(${palette.label},${a})`;
        ctx!.font = '600 19px "Instrument Sans", -apple-system, sans-serif';
        ctx!.textAlign = "center";
        ctx!.fillText(t0.label, t0.x, t0.y + 6);
        ctx!.restore();
      }
    }
  }

  if (opts.reducedMotion) {
    // The resolved composition, still: orbits and labels, no loop.
    drawFrame(0, 1);
    return {
      stop() {},
      debug: { kind: "static", motes: dustCount, mode: () => "static", frames: () => 0 },
    };
  }

  let tt = 0;
  let resolveAmt = 0;
  let stopped = false;
  let visible = true;
  let scheduled = false;

  const onResize = () => sizeCanvas(canvas);
  window.addEventListener("resize", onResize);

  function tick(): void {
    scheduled = false;
    if (stopped || !visible) return;
    tt++;
    const rect = section!.getBoundingClientRect();
    const vis = Math.min(1, Math.max(0, (window.innerHeight - rect.top) / (window.innerHeight * 0.9)));
    resolveAmt += (vis - resolveAmt) * 0.03;
    drawFrame(tt, resolveAmt);
    schedule();
  }

  function schedule(): void {
    if (stopped || !visible || scheduled) return;
    scheduled = true;
    requestAnimationFrame(tick);
  }

  const unobserve = observeVisibility(canvas, (now) => {
    visible = now;
    schedule();
  });

  schedule();

  return {
    stop() {
      stopped = true;
      unobserve();
      window.removeEventListener("resize", onResize);
    },
    debug: { kind: "animated", motes: dustCount, mode: () => "resolve", frames: () => tt },
  };
}

/** How the components decide, kept here so tests exercise the same seams. */
export function prefersReducedMotion(): boolean {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
}

export function isMobileViewport(): boolean {
  return window.matchMedia?.("(max-width: 768px)").matches ?? false;
}
