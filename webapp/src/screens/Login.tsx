import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { LOGIN_FAILED, LOGIN_RATE_LIMITED, LOGIN_SENT } from "@/lib/copy";

/**
 * Magic link only. No passwords for a senior-adjacent audience.
 *
 * Failures surface as words (QUESTIONS 115). The founder's lost hour was a
 * mailer rate limit that this screen swallowed: it said "check your email" over
 * a link that was never sent, and the only evidence was an auth log nobody was
 * reading. The mailer is equipment, so its failures read like equipment — calm,
 * specific, next step included — in the app's plain foreground, because nothing
 * here earns red and a login hiccup is not going to be the first thing that does.
 */
type SendState = "idle" | "sent" | "rate_limited" | "failed";

/** The 429 the built-in mailer returns after a couple of links in an hour. */
function isRateLimit(error: unknown): boolean {
  const shaped = error as { status?: number; code?: string } | null;
  return shaped?.status === 429 || shaped?.code === "over_email_send_rate_limit";
}

export function Login({ onSend }: { onSend: (email: string) => Promise<void> }) {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<SendState>("idle");
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await onSend(email.trim());
      setState("sent");
    } catch (error) {
      setState(isRateLimit(error) ? "rate_limited" : "failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Kettle</CardTitle>
      </CardHeader>
      <CardContent>
        {state === "sent" ? (
          <p className="text-sm text-muted-foreground" data-testid="login-sent">
            {LOGIN_SENT}
          </p>
        ) : (
          <form onSubmit={submit} className="space-y-3">
            <Input
              type="email"
              required
              value={email}
              placeholder="you@example.com"
              aria-label="Email address"
              onChange={(e) => setEmail(e.target.value)}
            />
            <Button type="submit" disabled={busy} className="w-full">
              Email me a sign-in link
            </Button>
            {(state === "rate_limited" || state === "failed") && (
              <p role="alert" className="text-sm text-foreground" data-testid="login-error">
                {state === "rate_limited" ? LOGIN_RATE_LIMITED : LOGIN_FAILED}
              </p>
            )}
          </form>
        )}
      </CardContent>
    </Card>
  );
}
