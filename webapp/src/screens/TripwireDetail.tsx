import { Beacon } from "@/components/beacon";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  TRIPWIRE_BACK,
  TRIPWIRE_CONNECTED,
  TRIPWIRE_STALE,
  TRIPWIRE_TITLE,
  TRIPWIRE_UNSET,
  renderRecency,
  renderRepairNudge,
} from "@/lib/copy";
import type { GlanceState } from "@/lib/glance";
import type { TripwireHealthView, TripwireRow } from "@/lib/tripwires";

/**
 * Tripwire health for one parent (spec 005d).
 *
 * A maintenance surface — equipment status for the repair flow — and emphatically
 * not an activity feed. Three things follow from that, and each is a test:
 *
 * * **Signal names render here and nowhere else.** Repair is impossible without
 *   them; reassurance is worse with them. `copyLaw.test.tsx` holds an allowlist
 *   naming exactly these strings and exactly this view.
 * * **Day granularity only.** No clock times anywhere below. A per-app list
 *   stamped with times is ammunition; `3 days ago` answers the repair question
 *   without handing anyone a schedule.
 * * **Amber is the ceiling, and it describes equipment.** A tripwire that has
 *   stopped reporting is a Shortcuts problem until proven otherwise, so nothing
 *   here reaches past the phone to the person holding it.
 *
 * The header repeats the card's own headline and beacon rather than computing
 * anything new: tapping through must never reveal a state the card was hiding.
 */
export function TripwireDetail({
  glance,
  tripwires,
  onBack,
}: {
  glance: GlanceState;
  tripwires: TripwireHealthView;
  onBack: () => void;
}) {
  return (
    <div className="space-y-4" data-testid="tripwire-detail">
      <Button variant="ghost" size="sm" className="-ml-2" onClick={onBack}>
        {TRIPWIRE_BACK}
      </Button>

      <Card>
        <CardContent className="space-y-4 pt-5">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{glance.name}</p>
              <p
                className={
                  glance.seenToday
                    ? "text-xl font-semibold leading-snug text-calm"
                    : "text-xl font-semibold leading-snug text-foreground"
                }
                data-testid="detail-headline"
              >
                {glance.headline}
              </p>
            </div>
            <Beacon state={glance.beacon} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-3 pt-5">
          <h2 className="text-sm font-medium text-muted-foreground">{TRIPWIRE_TITLE}</h2>
          <ul className="space-y-3">
            {tripwires.rows.map((row) => (
              <TripwireRowView key={row.signal} row={row} />
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Only when something is actually stale. A repair nudge under a healthy
          list would be a standing suggestion that something is wrong. */}
      {tripwires.needsRepair && (
        <p className="px-1 text-sm text-muted-foreground" data-testid="repair-nudge">
          {renderRepairNudge(tripwires.parentName)}
        </p>
      )}
    </div>
  );
}

/**
 * Three chips, and only one of them is amber.
 *
 * `unconfigured` is deliberately the quietest of the three — quieter than
 * `Connected`, which at least earns its colour. A shortcut nobody has installed
 * is a setup step waiting for 005b's wizard, and it should read like an empty
 * field, not like a fault.
 */
const CHIP: Record<TripwireRow["health"], { label: string; className: string }> = {
  // Amber is the darkest thing on this screen, and it means a piece of
  // equipment that used to report went quiet. There is no red variant.
  stale: { label: TRIPWIRE_STALE, className: "font-medium text-attention" },
  connected: { label: TRIPWIRE_CONNECTED, className: "text-calm" },
  unconfigured: { label: TRIPWIRE_UNSET, className: "text-muted-foreground" },
};

function TripwireRowView({ row }: { row: TripwireRow }) {
  const chip = CHIP[row.health];
  return (
    <li className="flex items-baseline justify-between gap-3" data-testid="tripwire-row">
      <span className="text-sm" data-testid="tripwire-name">
        {row.name}
      </span>
      <span className="flex items-baseline gap-2 text-xs">
        <span data-testid="tripwire-health" data-health={row.health} className={chip.className}>
          {chip.label}
        </span>
        <span className="text-muted-foreground" data-testid="tripwire-recency">
          {renderRecency(row.recency.kind, row.recency.days)}
        </span>
      </span>
    </li>
  );
}
