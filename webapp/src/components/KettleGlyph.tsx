/**
 * The one three-state glyph (spec 008 §3). Geometry copied from
 * docs/Kettle-Design.html verbatim — circle, cup path, handle path, steam and
 * pause rects — never redrawn by eye.
 *
 * Three states, two sizes:
 * - ordinary:    hearth-filled disc, cup in --cup, two steam rects in --steam
 * - quiet:       unfilled disc, thinner --copper stroke, cup in --copper, no steam
 * - unreachable: unfilled disc, --mute stroke, no cup, two --mute pause bars
 *
 * "The kettle's on" renders ONLY inside the ordinary-state 200px hero, and the
 * steam animates only there (classes defined solely under
 * prefers-reduced-motion: no-preference in kettle.css). The 44px card glyph is
 * always still.
 */

export type GlyphState = "ordinary" | "quiet" | "unreachable";

const NONE = "rgba(0,0,0,0)";

interface Palette {
  ringFill: string;
  ringStroke: string;
  swBig: string;
  cupC: string;
  steamC: string;
  pauseC: string;
  onC: string;
}

function palette(state: GlyphState): Palette {
  if (state === "ordinary") {
    return {
      ringFill: "var(--hearthfill)",
      ringStroke: "var(--hearthring)",
      swBig: "11",
      cupC: "var(--cup)",
      steamC: "var(--steam)",
      pauseC: NONE,
      onC: "var(--cup)",
    };
  }
  if (state === "quiet") {
    return {
      ringFill: NONE,
      ringStroke: "var(--copper)",
      swBig: "7",
      cupC: "var(--copper)",
      steamC: NONE,
      pauseC: NONE,
      onC: NONE,
    };
  }
  return {
    ringFill: NONE,
    ringStroke: "var(--mute)",
    swBig: "7",
    cupC: NONE,
    steamC: NONE,
    pauseC: "var(--mute)",
    onC: NONE,
  };
}

export function KettleGlyph({
  state,
  size,
}: {
  state: GlyphState;
  /** 44 on cards, 200 on the detail hero. */
  size: 44 | 200;
}) {
  const p = palette(state);

  if (size === 44) {
    return (
      <svg
        width="44"
        height="44"
        viewBox="0 0 44 44"
        aria-hidden="true"
        data-testid="kettle-glyph"
        data-glyph-state={state}
        data-glyph-size="44"
        style={{ flex: "0 0 auto" }}
      >
        <circle cx="22" cy="22" r="18" style={{ fill: p.ringFill, stroke: p.ringStroke, strokeWidth: 2.5 }} />
        <rect x="17.8" y="11.4" width="1.9" height="5" rx="0.95" style={{ fill: p.steamC }} />
        <rect x="22.2" y="12.8" width="1.9" height="3.6" rx="0.95" style={{ fill: p.steamC }} />
        <path
          d="M14.8 20.6 L25.2 20.6 L25.2 26.2 A2.6 2.6 0 0 1 22.6 28.8 L17.4 28.8 A2.6 2.6 0 0 1 14.8 26.2 Z"
          style={{ fill: "none", stroke: p.cupC, strokeWidth: 2.2, strokeLinejoin: "round" }}
        />
        <path
          d="M25.2 22 L26.6 22 A2.3 2.3 0 0 1 26.6 26.6 L25.2 26.6"
          style={{ fill: "none", stroke: p.cupC, strokeWidth: 2.2, strokeLinecap: "round" }}
        />
        <rect x="17.2" y="16" width="3" height="12" rx="1.5" style={{ fill: p.pauseC }} />
        <rect x="23.8" y="16" width="3" height="12" rx="1.5" style={{ fill: p.pauseC }} />
      </svg>
    );
  }

  return (
    <svg
      width="200"
      height="200"
      viewBox="0 0 200 200"
      aria-hidden="true"
      data-testid="kettle-glyph"
      data-glyph-state={state}
      data-glyph-size="200"
    >
      <circle cx="100" cy="100" r="88" style={{ fill: p.ringFill, stroke: p.ringStroke, strokeWidth: p.swBig }} />
      <rect
        className={state === "ordinary" ? "kt-steam-hero" : undefined}
        x="93"
        y="50"
        width="4.5"
        height="16"
        rx="2.25"
        style={{ fill: p.steamC }}
      />
      <rect
        className={state === "ordinary" ? "kt-steam-hero-late" : undefined}
        x="103.5"
        y="55"
        width="4.5"
        height="11"
        rx="2.25"
        style={{ fill: p.steamC }}
      />
      <path
        d="M82 76 L109 76 L109 90 A7 7 0 0 1 102 97 L89 97 A7 7 0 0 1 82 90 Z"
        style={{ fill: "none", stroke: p.cupC, strokeWidth: 5.5, strokeLinejoin: "round" }}
      />
      <path
        d="M109 79.5 L112.5 79.5 A6 6 0 0 1 112.5 91.5 L109 91.5"
        style={{ fill: "none", stroke: p.cupC, strokeWidth: 5.5, strokeLinecap: "round" }}
      />
      {state === "ordinary" && (
        <text
          x="100"
          y="134"
          data-testid="kettles-on"
          style={{
            textAnchor: "middle",
            fill: p.onC,
            fontFamily: "'Newsreader', Georgia, serif",
            fontWeight: 600,
            fontSize: 20,
          }}
        >
          The kettle’s on
        </text>
      )}
      <rect x="85" y="80" width="10" height="40" rx="5" style={{ fill: p.pauseC }} />
      <rect x="105" y="80" width="10" height="40" rx="5" style={{ fill: p.pauseC }} />
    </svg>
  );
}
