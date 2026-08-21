import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  PRIVACY_FOOTER,
  SETUP_EXPIRES,
  SETUP_HOW,
  SETUP_NEEDS_LINK,
  SETUP_READY,
  SETUP_REPORTING,
  SETUP_SEND_LABEL,
  SETUP_TITLE,
} from "@/lib/copy";
import type { SetupEntry } from "@/lib/setupLinks";
import { effectiveTz } from "@/lib/time";
import type { Member, Parent } from "@/lib/types";

const SETUP_STATUS_LABEL = {
  reporting: SETUP_REPORTING,
  ready: SETUP_READY,
  needs_link: SETUP_NEEDS_LINK,
} as const;

/** The roster, each parent's setup card (spec 005b), and the privacy line. */
export function FamilyScreen({
  parents,
  members,
  familyTz,
  setupEntries,
}: {
  parents: Parent[];
  members: Member[];
  familyTz: string;
  setupEntries: SetupEntry[];
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
          <CardTitle>{SETUP_TITLE}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {setupEntries.map((entry) => (
            <div key={entry.parentId} className="space-y-1" data-testid="setup-entry">
              <div className="flex justify-between text-sm">
                <span>{entry.parentName}</span>
                <span className="text-muted-foreground" data-testid="setup-status">
                  {SETUP_STATUS_LABEL[entry.status]}
                </span>
              </div>
              {entry.status === "ready" && entry.shareHref && (
                <div className="flex items-baseline justify-between gap-2">
                  {/* The slug travels inside the href only; the visible text
                      never prints it (it is the page's credential). */}
                  <a
                    className="text-sm underline underline-offset-2"
                    href={entry.shareHref}
                    data-testid="setup-share"
                  >
                    {SETUP_SEND_LABEL}
                  </a>
                  {entry.expiresDate && (
                    <span className="text-xs text-muted-foreground">
                      {SETUP_EXPIRES.replace("{date}", entry.expiresDate)}
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
          {setupEntries.some((entry) => entry.status === "ready") && (
            <div className="space-y-1 pt-1">
              {SETUP_HOW.map((line) => (
                <p key={line} className="text-xs text-muted-foreground">
                  {line}
                </p>
              ))}
            </div>
          )}
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
