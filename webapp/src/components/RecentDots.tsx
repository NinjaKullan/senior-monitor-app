/**
 * The week as dots (spec 009 §3): seven chips, oldest left, today right,
 * reusing the three hearth states — filled ring for a normal day, copper
 * outline for a quiet start, mute outline for a day nothing was heard. NO
 * tally, NO checkmarks, NO count anywhere: one odd day is information, not a
 * scoreboard, and a test asserts the panel carries no digits.
 *
 * Never color alone: normal is the only FILLED chip (a fill/outline shape
 * difference survives with color removed), and the always-visible legend
 * names all three states in words.
 */

import {
  LEGEND_NORMAL,
  LEGEND_QUIET,
  LEGEND_UNHEARD,
} from "@/lib/copy";
import type { DotKind, RecentDot } from "@/lib/parentState";

function chipStyle(kind: DotKind, size: string): React.CSSProperties {
  const base: React.CSSProperties = {
    display: "inline-block",
    width: size,
    height: size,
    borderRadius: "50%",
    boxSizing: "border-box",
  };
  if (kind === "normal")
    return { ...base, background: "var(--hearthfill)", border: "2px solid var(--hearthring)" };
  if (kind === "quiet") return { ...base, background: "none", border: "2px solid var(--copper)" };
  return { ...base, background: "none", border: "2px solid var(--mute)" };
}

export function RecentDots({ dots }: { dots: RecentDot[] }) {
  return (
    <div data-testid="recent-dots">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginTop: "0.25rem" }}>
        {dots.map((dot, index) => (
          <div key={index} style={{ textAlign: "center", flex: 1 }} data-testid="recent-dot" data-dot-kind={dot.kind}>
            <span style={chipStyle(dot.kind, "1rem")} aria-hidden="true" />
            <div style={{ fontSize: "0.6875rem", color: "var(--mute)", marginTop: "0.375rem" }}>
              {dot.abbr}
            </div>
          </div>
        ))}
      </div>
      <div
        style={{ display: "flex", gap: "0.875rem", marginTop: "0.75rem", fontSize: "0.71875rem", color: "var(--mute)", flexWrap: "wrap" }}
        data-testid="dots-legend"
      >
        <span style={{ display: "inline-flex", alignItems: "center", gap: "0.3125rem" }}>
          <span style={chipStyle("normal", "0.625rem")} aria-hidden="true" />
          {LEGEND_NORMAL}
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: "0.3125rem" }}>
          <span style={chipStyle("quiet", "0.625rem")} aria-hidden="true" />
          {LEGEND_QUIET}
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: "0.3125rem" }}>
          <span style={chipStyle("none", "0.625rem")} aria-hidden="true" />
          {LEGEND_UNHEARD}
        </span>
      </div>
    </div>
  );
}
