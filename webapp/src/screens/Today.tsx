/**
 * Today (spec 008 §5.1): one card per parent — glyph, name eyebrow, local
 * time, the state sentence, the last-heard line. The whole card is the tap
 * target into the parent's detail. Warmth rises; information stays coarse —
 * nothing here says more than the three-state model knows.
 */
import { KettleGlyph } from "@/components/KettleGlyph";
import { EMPTY_TODAY, OPEN_PARENT_LABEL, TODAY_TITLE } from "@/lib/copy";
import type { ParentToday } from "@/lib/parentState";

export function Today({
  states,
  dateLine,
  onOpen,
}: {
  states: ParentToday[];
  /** "Friday, August 22" in the viewer's zone. */
  dateLine: string;
  onOpen: (parentId: string) => void;
}) {
  return (
    <div className="kt-view" data-testid="today-screen">
      <h1
        className="kt-serif"
        style={{ margin: 0, fontWeight: 500, fontSize: 38, letterSpacing: "-.01em" }}
      >
        {TODAY_TITLE}
      </h1>
      <div style={{ marginTop: 7, fontSize: 15, color: "var(--ink2)" }}>{dateLine}</div>
      {states.length === 0 ? (
        <p style={{ marginTop: 24, color: "var(--ink2)" }}>{EMPTY_TODAY}</p>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
            gap: 16,
            marginTop: 24,
          }}
        >
          {states.map((state) => (
            <button
              key={state.parentId}
              type="button"
              data-testid="today-card"
              className="kt-cardbtn"
              aria-label={OPEN_PARENT_LABEL.replace("{name}", state.name)}
              onClick={() => onOpen(state.parentId)}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 18,
                boxSizing: "border-box",
                textAlign: "left",
                background: "var(--card)",
                border: "1px solid var(--hair)",
                borderRadius: 22,
                padding: "22px 24px",
                cursor: "pointer",
              }}
            >
              <span style={{ flex: "0 0 auto", marginTop: 2 }}>
                <KettleGlyph state={state.kind} size={44} />
              </span>
              <span style={{ minWidth: 0, display: "flex", flexDirection: "column", gap: 8 }}>
                <span style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
                  <span
                    style={{
                      fontSize: 12.5,
                      fontWeight: 600,
                      letterSpacing: ".09em",
                      textTransform: "uppercase",
                      color: "var(--ink2)",
                    }}
                  >
                    {state.name}
                  </span>
                  <span style={{ fontSize: 13, color: "var(--ink3)" }} data-testid="today-local">
                    {state.localTime}
                  </span>
                </span>
                <span
                  className="kt-serif"
                  data-testid="today-sentence"
                  style={{ fontWeight: 500, fontSize: 23, lineHeight: 1.25, letterSpacing: "-.01em" }}
                >
                  {state.sentence}
                </span>
                <span
                  style={{ fontSize: 14.5, color: "var(--ink2)", lineHeight: 1.45 }}
                  data-testid="today-meta"
                >
                  {state.meta}
                </span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
