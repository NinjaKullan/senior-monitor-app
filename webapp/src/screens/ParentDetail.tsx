/**
 * Parent detail (spec 008 §5.2): the 200px hero glyph and sentence, the Call
 * button (only when a phone number exists — never a dead button), the day in
 * words, the two-minute-fix card gated on the same condition as the repair
 * nudge, the recent-days list, and an About block built only from fields that
 * exist. "The kettle's on" lives inside the glyph and only in its ordinary
 * state; steam drifts only here, and only for people who have not asked for
 * reduced motion.
 */
import { KettleGlyph } from "@/components/KettleGlyph";
import {
  ABOUT_TITLE,
  BACK_TO_TODAY,
  DAY_TITLE,
  FIX_TITLE,
  RECENT_TITLE,
  renderFixBody,
} from "@/lib/copy";
import type { ParentToday } from "@/lib/parentState";

const KICKER: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 700,
  letterSpacing: ".1em",
  textTransform: "uppercase",
  color: "var(--ink3)",
};

export function ParentDetail({
  state,
  onBack,
}: {
  state: ParentToday;
  onBack: () => void;
}) {
  return (
    <div className="kt-view" data-testid="parent-detail" style={{ maxWidth: 620, margin: "0 auto" }}>
      <button
        type="button"
        onClick={onBack}
        className="kt-rowbtn"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          background: "none",
          border: "none",
          borderRadius: 10,
          padding: "10px 8px",
          margin: "0 0 4px -8px",
          fontSize: 15,
          fontWeight: 600,
          color: "var(--copperdeep)",
          cursor: "pointer",
        }}
      >
        ‹ {BACK_TO_TODAY}
      </button>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          padding: "8px 0 6px",
        }}
      >
        <KettleGlyph state={state.kind} size={200} />
        <div
          style={{
            marginTop: 8,
            fontSize: 12.5,
            fontWeight: 600,
            letterSpacing: ".09em",
            textTransform: "uppercase",
            color: "var(--ink2)",
          }}
        >
          {state.name}
        </div>
        <div
          className="kt-serif"
          data-testid="detail-sentence"
          style={{
            marginTop: 12,
            maxWidth: 460,
            fontWeight: 500,
            fontSize: 31,
            lineHeight: 1.18,
            letterSpacing: "-.012em",
          }}
        >
          {state.sentence}
        </div>
        <div
          data-testid="detail-meta"
          style={{ marginTop: 12, maxWidth: 440, fontSize: 15.5, color: "var(--ink2)", lineHeight: 1.5 }}
        >
          {state.meta}
        </div>
        <div style={{ marginTop: 3, fontSize: 15.5, color: "var(--ink2)" }} data-testid="detail-local">
          {state.localLine}
        </div>
        {state.aside && (
          <div
            className="kt-serif"
            data-testid="detail-aside"
            style={{
              marginTop: 12,
              maxWidth: 420,
              fontStyle: "italic",
              fontSize: 16.5,
              lineHeight: 1.45,
              color: "var(--inkmid)",
            }}
          >
            {state.aside}
          </div>
        )}
        {state.tel && (
          <a
            href={state.tel}
            data-testid="call-button"
            className="kt-copperbtn"
            style={{
              display: "inline-flex",
              alignItems: "center",
              boxSizing: "border-box",
              minHeight: 44,
              marginTop: 20,
              padding: "11px 26px",
              borderRadius: 999,
              background: "var(--coppertint)",
              border: "1px solid var(--copperbd)",
              color: "var(--copperdeep)",
              fontSize: 15.5,
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            {state.callLabel}
          </a>
        )}
      </div>

      <div style={{ marginTop: 34 }}>
        <div style={KICKER}>{DAY_TITLE}</div>
        <div style={{ marginTop: 6 }}>
          {state.dayRows.map((row, index) => (
            <div
              key={row.part}
              data-testid="day-row"
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: 18,
                padding: "13px 0",
                borderTop: index === 0 ? "1px solid rgba(0,0,0,0)" : "1px solid var(--hair)",
              }}
            >
              <span style={{ flex: "0 0 88px", fontSize: 13, fontWeight: 600, color: "var(--ink2)" }}>
                {row.part}
              </span>
              <span
                className="kt-serif"
                style={{
                  fontSize: 17.5,
                  lineHeight: 1.45,
                  color: row.dim ? "var(--ink3)" : "var(--ink)",
                }}
              >
                {row.text}
              </span>
            </div>
          ))}
        </div>
      </div>

      {state.needsFix && (
        <div
          data-testid="fix-card"
          style={{
            marginTop: 28,
            boxSizing: "border-box",
            background: "var(--fixbg)",
            border: "1px solid var(--copperbd)",
            borderRadius: 22,
            padding: "20px 22px",
          }}
        >
          <div style={{ fontSize: 15.5, fontWeight: 600, color: "var(--copperdeep)" }}>{FIX_TITLE}</div>
          <div
            style={{ marginTop: 6, fontSize: 15, color: "var(--inkmid)", lineHeight: 1.55 }}
            data-testid="fix-body"
          >
            {renderFixBody(state.name)}
          </div>
        </div>
      )}

      <div style={{ marginTop: 30 }}>
        <div style={KICKER}>{RECENT_TITLE}</div>
        <div style={{ marginTop: 6 }}>
          {state.recentDays.map((recent, index) => (
            <div
              key={recent.day}
              data-testid="recent-day"
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: 16,
                padding: "11px 0",
                borderTop: index === 0 ? "1px solid rgba(0,0,0,0)" : "1px solid var(--hair)",
              }}
            >
              <span style={{ flex: "0 0 88px", fontSize: 13, fontWeight: 600, color: "var(--ink2)" }}>
                {recent.day}
              </span>
              <span className="kt-serif" style={{ fontSize: 17, color: "var(--ink)", lineHeight: 1.4 }}>
                {recent.line}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 30 }}>
        <div style={KICKER}>{ABOUT_TITLE}</div>
        <div style={{ marginTop: 8, fontSize: 15, color: "var(--ink2)" }} data-testid="about-tz">
          {state.tzNote}
        </div>
        {state.setupLine && (
          <div style={{ marginTop: 4, fontSize: 15, color: "var(--ink2)" }} data-testid="about-setup">
            {state.setupLine}
          </div>
        )}
      </div>
    </div>
  );
}
