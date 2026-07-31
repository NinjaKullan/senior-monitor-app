import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PRIVACY_FOOTER } from "@/lib/copy";
import { effectiveTz } from "@/lib/time";
import type { Member, Parent } from "@/lib/types";

/** The read-only roster, and the sentence that explains the whole product. */
export function FamilyScreen({
  parents,
  members,
  familyTz,
}: {
  parents: Parent[];
  members: Member[];
  familyTz: string;
}) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Looking after</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {parents.map((parent) => (
            <div key={parent.id} className="flex justify-between text-sm" data-testid="roster-parent">
              <span>{parent.display_name}</span>
              <span className="text-muted-foreground">{effectiveTz(parent.tz, familyTz)}</span>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Family circle</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {members.map((member) => (
            <div key={member.id} className="flex justify-between text-sm" data-testid="roster-member">
              <span>{member.display_name ?? "—"}</span>
              <span className="text-muted-foreground">{member.digest_channel}</span>
            </div>
          ))}
        </CardContent>
      </Card>

      <p className="px-1 text-sm text-muted-foreground" data-testid="privacy-footer">
        {PRIVACY_FOOTER}
      </p>
    </div>
  );
}
