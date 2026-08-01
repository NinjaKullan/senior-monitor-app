import { Beacon } from "@/components/beacon";
import { Card, CardContent } from "@/components/ui/card";
import {
  ARC_LABEL_NONE,
  ARC_LABEL_PREFIX,
  GLANCE_NO_ROUTINE_YET,
  TRIPWIRE_OPEN_LABEL,
} from "@/lib/copy";
import type { ArcSegment, GlanceState } from "@/lib/glance";

/**
 * The anxious-moment screen (spec 005c).
 *
 * Warmth rises, information stays coarse. The headline knows the time of day,
 * the arc gives the day a shape, the dot breathes when the handset is really
 * reporting — and none of it says anything the two flat words did not. There is
 * no red in this file because no state here earns one.
 */
export function Glance({
  states,
  onOpen,
}: {
  states: GlanceState[];
  /** Tapping a card opens that parent's tripwire health (spec 005d). */
  onOpen?: (parentId: string) => void;
}) {
  if (states.length === 0) {
    return <p className="text-muted-foreground">No one is being watched over yet.</p>;
  }
  return (
    <div className="space-y-4">
      {states.map((state) => (
        <Card key={state.parentId} data-testid="glance-card">
          {/* The whole card is the tap target — the detail view is maintenance,
              and a family should never have to hunt for the way into it. */}
          <button
            type="button"
            className="w-full rounded-lg text-left"
            data-testid="glance-card-tap"
            aria-label={TRIPWIRE_OPEN_LABEL.replace("{name}", state.name)}
            onClick={() => onOpen?.(state.parentId)}
          >
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
          </button>
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

