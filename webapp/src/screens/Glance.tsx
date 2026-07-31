import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GLANCE_ALL_NORMAL } from "@/lib/copy";
import type { GlanceState } from "@/lib/glance";

/**
 * The anxious-moment screen. Large, calm, and two states deep.
 *
 * `Quiet so far` is the darkest thing this screen can say. Absence that would
 * warrant more than that belongs to the escalation ladder, which has no surface
 * in this app at all.
 */
export function Glance({ states }: { states: GlanceState[] }) {
  if (states.length === 0) {
    return <p className="text-muted-foreground">No one is being watched over yet.</p>;
  }
  return (
    <div className="space-y-4">
      {states.map((state) => {
        const normal = state.status === GLANCE_ALL_NORMAL;
        return (
          <Card key={state.parentId} data-testid="glance-card">
            <CardHeader>
              <CardTitle>{state.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p
                className={
                  normal
                    ? "text-3xl font-semibold text-calm"
                    : "text-3xl font-semibold text-foreground"
                }
                data-testid="glance-status"
              >
                {state.status}
              </p>
              <p className="text-sm text-muted-foreground">
                {state.lastSeen
                  ? `Last routine seen ${state.lastSeen} local`
                  : "No routine seen yet"}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
