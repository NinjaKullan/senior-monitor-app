/**
 * Parent detail (spec 009 §3): the screen answers "do I need to do anything?"
 * in a literal box. Order is law: back link, hero, time block, Call button,
 * The day (the arc), Recent days (the dots), What this means, the fix card
 * when a tripwire has stopped reporting, Family notes scoped to this parent.
 */
import { DayArc } from "@/components/DayArc";
import { KettleGlyph } from "@/components/KettleGlyph";
import { NotesPanel, type NoteDraft, type ReplyDraft } from "@/components/NotesPanel";
import { RecentDots } from "@/components/RecentDots";
import {
  BACK_TO_TODAY,
  DAY_TITLE,
  FIX_STEPS_LABEL,
  RECENT_TITLE,
  renderFixBody,
} from "@/lib/copy";
import type { ParentToday } from "@/lib/parentState";
import type { JournalEntry } from "@/lib/types";

const PANEL: React.CSSProperties = {
  background: "var(--card)",
  border: "1px solid var(--hair)",
  borderRadius: "1.125rem",
  padding: "1rem",
  marginBottom: "0.875rem",
};

const PANEL_H: React.CSSProperties = {
  fontSize: "0.6875rem",
  letterSpacing: ".14em",
  textTransform: "uppercase",
  color: "var(--mute)",
  fontWeight: 700,
  margin: 0,
  marginBottom: "0.625rem",
};

export function ParentDetail({
  state,
  notes,
  todayDate,
  tz,
  onBack,
  onAddNote,
  onAddReply,
  onSteps,
}: {
  state: ParentToday;
  notes: JournalEntry[];
  todayDate: string;
  /** The family's timezone, for dating notes (DECISIONS 251). */
  tz: string;
  onBack: () => void;
  onAddNote: (draft: NoteDraft) => Promise<void>;
  onAddReply?: (draft: ReplyDraft) => Promise<void>;
  /** The fix card's "See the simple steps →" destination (flagged call: the
   *  Family screen's setup card is the steps surface that exists). */
  onSteps: () => void;
}) {
  const fix = renderFixBody(state.label);
  const fixSplit = fix.indexOf(". ") + 1;
  return (
    <div className="kt-view" data-testid="parent-detail" style={{ maxWidth: "40rem", margin: "0 auto" }}>
      <button
        type="button"
        onClick={onBack}
        className="kt-rowbtn"
        style={{
          background: "none",
          border: "none",
          borderRadius: "0.625rem",
          padding: "0.625rem 0.5rem",
          margin: "0 0 0.25rem -0.5rem",
          fontSize: "0.8125rem",
          fontWeight: 600,
          color: "var(--inkmid)",
          cursor: "pointer",
          minHeight: "2.75rem",
        }}
      >
        ← {BACK_TO_TODAY}
      </button>

      <div style={{ display: "flex", alignItems: "center", gap: "0.875rem", margin: "1rem 0 0.25rem" }}>
        <KettleGlyph state={state.kind} size={44} />
        <div style={{ minWidth: 0 }}>
          <div
            style={{
              fontSize: "0.75rem",
              letterSpacing: ".1em",
              textTransform: "uppercase",
              fontWeight: 700,
              color: "var(--inkmid)",
            }}
            data-testid="hero-kicker"
          >
            {state.heroKicker}
          </div>
          <div
            className="kt-serif"
            style={{ fontSize: "1.625rem", fontWeight: 500, lineHeight: 1.15 }}
            data-testid="detail-sentence"
          >
            {state.sentence}
          </div>
        </div>
      </div>

      <div style={{ margin: "0.625rem 0 0" }}>
        <div style={{ fontSize: "1rem", fontWeight: 700 }} data-testid="detail-heard">
          {state.heard}
        </div>
        <div
          style={{ fontSize: "0.8125rem", color: "var(--mute)", marginTop: "0.125rem" }}
          data-testid="detail-sub"
        >
          {state.heroSub}
        </div>
      </div>
      {state.aside && (
        <div
          className="kt-serif"
          data-testid="detail-aside"
          style={{
            margin: "0.75rem 0 0",
            maxWidth: "26rem",
            fontStyle: "italic",
            fontSize: "1rem",
            lineHeight: 1.45,
            color: "var(--inkmid)",
          }}
        >
          {state.aside}
        </div>
      )}
      {state.callHref && (
        <div style={{ margin: "0.875rem 0 1.25rem" }}>
          <a
            href={state.callHref}
            data-testid="call-button"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4375rem",
              background: "var(--copperdeep)",
              color: "var(--oncopper)",
              borderRadius: "999px",
              padding: "0.5625rem 1.125rem",
              fontWeight: 700,
              fontSize: "0.875rem",
              textDecoration: "none",
              minHeight: "2.75rem",
              boxSizing: "border-box",
            }}
          >
            {state.callLabel}
          </a>
        </div>
      )}

      <section style={PANEL} data-testid="day-panel">
        <h3 style={PANEL_H}>{DAY_TITLE}</h3>
        <DayArc fraction={state.arcFraction} cells={state.arcCells} />
      </section>

      <section style={PANEL} data-testid="recent-panel">
        <h3 style={PANEL_H}>{RECENT_TITLE}</h3>
        <RecentDots dots={state.recentDots} />
      </section>

      <section style={PANEL} data-testid="means-card">
        <div className="kt-serif" style={{ fontSize: "1.0625rem", fontWeight: 600 }} data-testid="means-head">
          {state.meansHead}
        </div>
        <p
          style={{ fontSize: "0.84375rem", color: "var(--inkmid)", marginTop: "0.25rem", marginBottom: 0, lineHeight: 1.5 }}
          data-testid="means-body"
        >
          {state.meansBody}
        </p>
      </section>

      {state.needsFix && (
        <section
          data-testid="fix-card"
          style={{
            background: "var(--fixbg)",
            border: "1px solid var(--copperbd)",
            borderRadius: "1.125rem",
            padding: "1rem",
            marginBottom: "0.875rem",
          }}
        >
          <div
            className="kt-serif"
            style={{ fontSize: "1rem", fontWeight: 600, color: "var(--copperdeep)" }}
            data-testid="fix-head"
          >
            {fix.slice(0, fixSplit)}
          </div>
          <p
            style={{ fontSize: "0.8125rem", color: "var(--inkmid)", margin: "0.25rem 0 0.5rem", lineHeight: 1.5 }}
            data-testid="fix-body"
          >
            {fix.slice(fixSplit + 1)}
          </p>
          <button
            type="button"
            onClick={onSteps}
            data-testid="fix-steps"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.375rem",
              color: "var(--copperdeep)",
              fontWeight: 600,
              fontSize: "0.875rem",
              background: "none",
              border: "none",
              padding: "0.375rem 0",
              minHeight: "2.75rem",
              cursor: "pointer",
            }}
          >
            {FIX_STEPS_LABEL}
          </button>
        </section>
      )}

      <NotesPanel
        entries={notes}
        todayDate={todayDate}
        tz={tz}
        onAdd={onAddNote}
        onReply={onAddReply}
        fixedParentId={state.parentId}
      />
    </div>
  );
}
