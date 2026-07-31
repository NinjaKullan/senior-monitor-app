import { Card, CardContent } from "@/components/ui/card";
import { DIGESTS_EMPTY } from "@/lib/copy";
import type { DigestEntry } from "@/lib/digests";

/** What was actually sent, rebuilt from the templates that sent it. */
export function Digests({ entries }: { entries: DigestEntry[] }) {
  if (entries.length === 0) {
    return <p className="text-muted-foreground">{DIGESTS_EMPTY}</p>;
  }
  return (
    <div className="space-y-3">
      {entries.map((entry) => (
        <Card key={entry.key} data-testid="digest-entry">
          <CardContent className="space-y-1 pt-5">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              {entry.localDate} · {entry.kind}
            </p>
            <p className="text-base">{entry.message}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
