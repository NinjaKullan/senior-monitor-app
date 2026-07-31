import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { NO_FAMILY_BODY, NO_FAMILY_TITLE } from "@/lib/copy";

/**
 * RLS already guarantees this account can see nothing. This screen only makes
 * that kind rather than blank.
 */
export function NoFamily() {
  return (
    <Card data-testid="no-family">
      <CardHeader>
        <CardTitle>{NO_FAMILY_TITLE}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{NO_FAMILY_BODY}</p>
      </CardContent>
    </Card>
  );
}
