import { Card, CardContent } from "@/components/ui/card";
import {
  ARC_LABEL_NONE,
  ARC_LABEL_PREFIX,
  BEACON_LABEL,
  GLANCE_NO_ROUTINE_YET,
} from "@/lib/copy";
import type { ArcSegment, BeaconState, GlanceState } from "@/lib/glance";

/**
 * The anxious-moment screen (spec 005c).
 *
 * Warmth rises, information stays coarse. The headline knows the time of day,
 * the arc gives the day a shape, the dot breathes when the handset is really
 * reporting — and none of it says anything the two flat words did not. There is
 * no red in this file because no state here earns one.
 */
export function Glance({ states }: { states: GlanceState[] }) {
  if (states.length === 0) {
    return <p className="text-muted-foreground">No one is being watched over yet.</p>;
  }
  return (
    <div className="space-y-4">
      {states.map((state) => (
        <Card key={state.parentId} data-testid="glance-card">
          <CardContent className="space-y-4 pt-5">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">{state.name}</p>
                <p
                  className={
                    state.seenToday
                      ? "text-2xl font-semibold leading-snug text-calm"
                      : "text-2xl font-semibold leading-snug text-foreground"
                  }
                  data-testid="glance-headline"
                >
                  {state.headline}
                </p>
              </div>
              <Beacon state={state.beacon} />
            </div>

            <p className="text-sm text-muted-foreground" data-testid="glance-subline">
              {state.subline ?? GLANCE_NO_ROUTINE_YET}
            </p>

            <DayArc segments={state.arc} />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/** Three binary segments. No numbers, no tooltips, no history. */
function DayArc({ segments }: { segments: ArcSegment[] }) {
  const lit = segments.filter((s) => s.state === "lit").map((s) => s.name.toLowerCase());
  const label = lit.length > 0 ? `${ARC_LABEL_PREFIX}${lit.join(", ")}` : ARC_LABEL_NONE;

  return (
    <div className="flex gap-1.5" role="img" aria-label={label} data-testid="day-arc">
      {segments.map((segment) => (
        <span
          key={segment.name}
          aria-hidden="true"
          data-state={segment.state}
          data-testid="arc-segment"
          className={
            "h-2 flex-1 rounded-full transition-colors " +
            {
              // Warm, and the only lit thing on the card.
              lit: "bg-calm",
              // Past and quiet: soft, dim, unremarkable. Never red.
              quiet: "bg-muted",
              // Still to come: neutral, and deliberately close in weight to
              // quiet so an empty morning never reads as a verdict.
              ahead: "bg-muted/40",
            }[segment.state]
          }
        />
      ))}
    </div>
  );
}

/**
 * Phone status, never person status (attribution law). Absent when there is
 * nothing honest to show; still and grey when the last signal is old; breathing
 * only while a real one is recent.
 */
function Beacon({ state }: { state: BeaconState | null }) {
  if (state === null) return null;
  const breathing = state === "breathing";
  return (
    <span
      className="flex shrink-0 items-center gap-1.5 text-xs text-muted-foreground"
      data-testid="beacon"
      data-state={state}
    >
      <span
        aria-hidden="true"
        data-testid="beacon-dot"
        className={
          "inline-block h-2 w-2 rounded-full " +
          (breathing ? "bg-calm motion-safe:animate-breathe" : "bg-muted-foreground/40")
        }
      />
      {BEACON_LABEL}
    </span>
  );
}
