/**
 * Today (spec 009 §2): the screen answers "is everyone okay?" in one line
 * before anything else. Kicker date, family rollup by precedence
 * unreachable > quiet > normal, one card per parent, and a footer only when
 * every parent is normal — when anyone is quiet or unreachable the rollup
 * already carries it, and repeating it would be a scoreboard.
 */
import { useState } from "react";
import { KettleGlyph } from "@/components/KettleGlyph";
import {
  EMPTY_TODAY,
  PAUSED_CARD,
  PAUSE_CANCEL,
  PAUSE_LINK,
  PAUSE_OPEN,
  PAUSE_WEEK,
  RESUME_BUTTON,
  TODAY_FOOT_REST,
  TODAY_FOOT_STRONG,
} from "@/lib/copy";
import type { ParentToday } from "@/lib/parentState";

/** Spec 017 §5: what an admin can do to a parent's card. Absent for a
 *  member, and then no control renders — the paused card still does. */
export interface PauseActions {
  onPause: (parentId: string, duration: "week" | "open") => Promise<void>;
  onResume: (parentId: string) => Promise<void>;
}

const SMALL_BTN: React.CSSProperties = {
  background: "none",
  border: "1px solid var(--hair)",
  borderRadius: "999px",
  padding: "0.5rem 0.875rem",
  minHeight: "2.75rem",
  fontSize: "0.8125rem",
  fontWeight: 600,
  color: "var(--ink2)",
  cursor: "pointer",
};

export function Today({
  states,
  rollup,
  dateLine,
  onOpen,
  pause,
}: {
  states: ParentToday[];
  rollup: { line: string; sub: string };
  /** "Wednesday · August 26" in the viewer's zone — middot, never a dash. */
  dateLine: string;
  onOpen: (parentId: string) => void;
  pause?: PauseActions;
}) {
  const [choosing, setChoosing] = useState<string | null>(null);
  // A paused parent is left out of "everyone is normal" (spec 017).
  const watched = states.filter((s) => !s.paused);
  const allNormal = watched.length > 0 && watched.every((s) => s.kind === "ordinary");
  return (
    <div className="kt-view" data-testid="today-screen" style={{ maxWidth: "40rem", margin: "0 auto" }}>
      <div
        style={{
          fontSize: "0.6875rem",
          letterSpacing: ".14em",
          textTransform: "uppercase",
          color: "var(--mute)",
          fontWeight: 700,
        }}
      >
        {dateLine}
      </div>
      {states.length === 0 ? (
        <p style={{ marginTop: "1.5rem", color: "var(--ink2)" }}>{EMPTY_TODAY}</p>
      ) : (
        <>
          <h1
            className="kt-serif"
            data-testid="rollup"
            style={{
              fontWeight: 500,
              fontSize: "1.875rem",
              lineHeight: 1.15,
              margin: "0.625rem 0 0.25rem",
            }}
          >
            {rollup.line}
          </h1>
          <div
            style={{ color: "var(--inkmid)", fontSize: "0.875rem", marginBottom: "1.125rem" }}
            data-testid="rollup-sub"
          >
            {rollup.sub}
          </div>

          {states.map((state) =>
            state.paused ? (
              <div
                key={state.parentId}
                data-testid="today-card"
                data-paused="true"
                style={{
                  background: "var(--card)",
                  border: "1px solid var(--hair)",
                  borderRadius: "1.125rem",
                  padding: "1rem 1rem 0.875rem",
                  marginBottom: "0.875rem",
                }}
              >
                <div
                  style={{ fontSize: "0.75rem", letterSpacing: ".1em", textTransform: "uppercase", fontWeight: 700, color: "var(--inkmid)" }}
                  data-testid="card-name"
                >
                  {state.label}
                </div>
                <div
                  className="kt-serif"
                  style={{ fontSize: "1.1875rem", fontWeight: 500, margin: "0.625rem 0 0.125rem", lineHeight: 1.25 }}
                  data-testid="card-line"
                >
                  {PAUSED_CARD.replace("{name}", state.label)}
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--ink2)", marginTop: "0.375rem" }} data-testid="card-paused-line">
                  {state.pausedLine}
                </div>
                {pause && (
                  <div style={{ marginTop: "0.875rem" }}>
                    <button
                      type="button"
                      style={SMALL_BTN}
                      data-testid="resume-button"
                      onClick={() => void pause.onResume(state.parentId)}
                    >
                      {RESUME_BUTTON}
                    </button>
                  </div>
                )}
              </div>
            ) : (
            <div
              key={state.parentId}
              data-testid="today-card"
              style={{
                background: "var(--card)",
                border: "1px solid var(--hair)",
                borderRadius: "1.125rem",
                padding: "1rem 1rem 0.875rem",
                marginBottom: "0.875rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <KettleGlyph state={state.kind} size={44} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: "0.75rem",
                      letterSpacing: ".1em",
                      textTransform: "uppercase",
                      fontWeight: 700,
                      color: "var(--inkmid)",
                    }}
                    data-testid="card-name"
                  >
                    {state.label}
                  </div>
                  <div
                    style={{ fontSize: "0.75rem", color: "var(--mute)", marginTop: "0.0625rem" }}
                    data-testid="card-city"
                  >
                    {state.cityNow}
                  </div>
                </div>
              </div>
              <div
                className="kt-serif"
                style={{
                  fontSize: "1.1875rem",
                  fontWeight: 500,
                  margin: "0.625rem 0 0.125rem",
                  lineHeight: 1.25,
                }}
                data-testid="card-line"
              >
                {state.sentence}
              </div>
              <div
                style={{ fontSize: "0.875rem", fontWeight: 600, marginTop: "0.375rem" }}
                data-testid="card-heard"
              >
                {state.heard}
              </div>
              {state.dualLine && (
                <div
                  style={{ fontSize: "0.78125rem", color: "var(--mute)", marginTop: "0.125rem" }}
                  data-testid="card-dual"
                >
                  {state.dualLine}
                </div>
              )}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "0.75rem",
                  marginTop: "0.875rem",
                  flexWrap: "wrap",
                }}
              >
                {state.callHref ? (
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
                ) : (
                  <span />
                )}
                <button
                  type="button"
                  onClick={() => onOpen(state.parentId)}
                  data-testid="view-day"
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.375rem",
                    color: "var(--copperdeep)",
                    fontWeight: 600,
                    fontSize: "0.875rem",
                    background: "none",
                    border: "none",
                    padding: "0.5rem 0",
                    minHeight: "2.75rem",
                    cursor: "pointer",
                  }}
                >
                  {state.viewLabel}
                </button>
              </div>
              {pause && choosing !== state.parentId && (
                <button
                  type="button"
                  onClick={() => setChoosing(state.parentId)}
                  data-testid="pause-link"
                  style={{
                    background: "none",
                    border: "none",
                    padding: "0.5rem 0 0",
                    fontSize: "0.78125rem",
                    fontWeight: 600,
                    color: "var(--mute)",
                    cursor: "pointer",
                    minHeight: "2.75rem",
                  }}
                >
                  {PAUSE_LINK}
                </button>
              )}
              {pause && choosing === state.parentId && (
                <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.625rem" }} data-testid="pause-choices">
                  <button
                    type="button"
                    style={SMALL_BTN}
                    data-testid="pause-week"
                    onClick={() => {
                      setChoosing(null);
                      void pause.onPause(state.parentId, "week");
                    }}
                  >
                    {PAUSE_WEEK}
                  </button>
                  <button
                    type="button"
                    style={SMALL_BTN}
                    data-testid="pause-open"
                    onClick={() => {
                      setChoosing(null);
                      void pause.onPause(state.parentId, "open");
                    }}
                  >
                    {PAUSE_OPEN}
                  </button>
                  <button type="button" style={SMALL_BTN} onClick={() => setChoosing(null)}>
                    {PAUSE_CANCEL}
                  </button>
                </div>
              )}
            </div>
            ),
          )}

          {allNormal && (
            <div
              style={{
                marginTop: "0.375rem",
                color: "var(--inkmid)",
                fontSize: "0.84375rem",
                lineHeight: 1.5,
              }}
              data-testid="today-foot"
            >
              <b style={{ color: "var(--ink)" }}>{TODAY_FOOT_STRONG}</b> {TODAY_FOOT_REST}
            </div>
          )}
        </>
      )}
    </div>
  );
}
