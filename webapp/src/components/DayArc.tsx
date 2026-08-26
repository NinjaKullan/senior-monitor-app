/**
 * The day as a shape (spec 009 §3): ONE arc path drawn twice — background
 * stroke in --hearthring, progress in --olive revealed with pathLength and
 * stroke-dasharray to the fraction of the parent's local day elapsed — and
 * the dot sitting at the reveal's end, computed on the SAME quadratic curve.
 * Never two different curves: both path elements carry an identical `d`, and
 * a test pins that.
 */

import type { ArcCell } from "@/lib/parentState";

/** The mockup's curve, verbatim: M12 56 Q160 -14 308 56. */
const ARC_D = "M12 56 Q160 -14 308 56";
const P0 = { x: 12, y: 56 };
const P1 = { x: 160, y: -14 };
const P2 = { x: 308, y: 56 };

/** The quadratic Bézier point at parameter t — the same parameterisation
 *  pathLength reveals by, which is what keeps the dot ON the stroke's end. */
export function arcPoint(t: number): { x: number; y: number } {
  const u = 1 - t;
  return {
    x: u * u * P0.x + 2 * t * u * P1.x + t * t * P2.x,
    y: u * u * P0.y + 2 * t * u * P1.y + t * t * P2.y,
  };
}

export function DayArc({ fraction, cells }: { fraction: number; cells: ArcCell[] }) {
  const t = Math.min(1, Math.max(0, fraction));
  const dot = arcPoint(t);
  return (
    <div data-testid="day-arc">
      <svg viewBox="0 0 320 64" width="100%" aria-hidden="true" data-testid="day-arc-svg">
        <path
          d={ARC_D}
          style={{ fill: "none", stroke: "var(--hearthring)", strokeWidth: 5, strokeLinecap: "round" }}
        />
        <path
          d={ARC_D}
          pathLength={100}
          strokeDasharray={`${(t * 100).toFixed(1)} 100`}
          style={{ fill: "none", stroke: "var(--olive)", strokeWidth: 5, strokeLinecap: "round" }}
        />
        <circle cx={dot.x.toFixed(1)} cy={dot.y.toFixed(1)} r="6" style={{ fill: "var(--olive)" }} />
      </svg>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: "0.5rem" }}>
        {cells.map((cell) => (
          <div key={cell.part} style={{ textAlign: "center", width: "33%" }} data-testid="arc-cell">
            <div className="kt-serif" style={{ fontSize: "0.9375rem", fontWeight: 600 }}>
              {cell.part}
            </div>
            <div
              style={{
                fontSize: "0.75rem",
                color: cell.dim ? "var(--mute)" : "var(--inkmid)",
                marginTop: "0.125rem",
              }}
              data-testid="arc-caption"
            >
              {cell.text}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
