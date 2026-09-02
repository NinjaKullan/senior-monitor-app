import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  LOGIN_BUTTON,
  LOGIN_CODE_BUTTON,
  LOGIN_CODE_LABEL,
  LOGIN_CODE_RESEND,
  LOGIN_CODE_WRONG,
  LOGIN_FAILED,
  LOGIN_RATE_LIMITED,
  LOGIN_SENT,
} from "@/lib/copy";

/**
 * Two steps, one email (spec 013). No passwords for a senior-adjacent audience.
 *
 * Step 1 asks for an address; step 2 takes the 6-digit code that arrives. The
 * code exists because of where a LINK lands: tapped in a mail app on a phone,
 * it opens inside that app's browser rather than the installed Kettle, so the
 * session is created somewhere the family never looks and the app they open
 * next still asks them to sign in. They conclude Kettle is broken. A code has
 * no context to get wrong. The same email still carries the link for laptops,
 * where tapping it is the shorter path, and no platform detection decides
 * between them: both work, and the person picks.
 *
 * Failures surface as words (DECISIONS 115). The founder's lost hour was a
 * mailer rate limit that this screen swallowed: it said "check your email" over
 * a link that was never sent, and the only evidence was an auth log nobody was
 * reading. The mailer is equipment, so its failures read like equipment — calm,
 * specific, next step included — in the app's plain foreground, because nothing
 * here earns red and a login hiccup is not going to be the first thing that does.
 *
 * A wrong code gets its OWN sentence rather than the generic one: a mistyped
 * digit and a dead mailer need different next steps, and one message for both
 * would send a family back to a step that cannot help them.
 */
type SendState = "idle" | "sent" | "rate_limited" | "failed";
type CodeState = "idle" | "wrong" | "failed";

/** The 429 the mailer returns after a couple of emails in an hour. */
function isRateLimit(error: unknown): boolean {
  const shaped = error as { status?: number; code?: string } | null;
  return shaped?.status === 429 || shaped?.code === "over_email_send_rate_limit";
}

/**
 * Supabase says a bad or stale code the same way it says an expired one, and
 * says it in prose rather than in a code worth matching on: a 403 whose message
 * is "Token has expired or is invalid". Matched loosely and case-insensitively
 * so a wording change downgrades this to the generic failure rather than
 * throwing; anything unrecognised is LOGIN_FAILED by design.
 */
function isBadCode(error: unknown): boolean {
  const shaped = error as { status?: number; message?: string; code?: string } | null;
  const message = (shaped?.message ?? "").toLowerCase();
  return (
    shaped?.code === "otp_expired" ||
    (message.includes("token") && (message.includes("expired") || message.includes("invalid")))
  );
}

export function Login({
  onSend,
  onVerify,
}: {
  onSend: (email: string) => Promise<void>;
  onVerify: (email: string, token: string) => Promise<void>;
}) {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [state, setState] = useState<SendState>("idle");
  const [codeState, setCodeState] = useState<CodeState>("idle");
  const [busy, setBusy] = useState(false);
  const [sentOnce, setSentOnce] = useState(false);

  async function send(address: string) {
    setBusy(true);
    try {
      await onSend(address);
      setState("sent");
      setSentOnce(true);
    } catch (error) {
      setState(isRateLimit(error) ? "rate_limited" : "failed");
    } finally {
      setBusy(false);
    }
  }

  async function submitEmail(event: React.FormEvent) {
    event.preventDefault();
    await send(email.trim());
  }

  async function submitCode(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await onVerify(email.trim(), code.trim());
      // Nothing to do on success: `onAuthStateChange` in App.tsx observes the
      // new session, the same way it does when the link is tapped on a laptop.
      setCodeState("idle");
    } catch (error) {
      setCodeState(isBadCode(error) ? "wrong" : "failed");
    } finally {
      setBusy(false);
    }
  }

  /**
   * Step 2 is revealed by the FIRST successful send and never hidden again.
   * A resend that comes back rate-limited must not take the code field away
   * with it: the family may already be holding a perfectly good code from the
   * first email, and collapsing back to step 1 would throw away what they had
   * typed and tell them to start over for no reason.
   */
  const revealed = state === "sent" || sentOnce;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Kettle</CardTitle>
      </CardHeader>
      <CardContent>
        {revealed ? (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground" data-testid="login-sent">
              {LOGIN_SENT}
            </p>
            <form onSubmit={submitCode} className="space-y-3">
              <Input
                type="text"
                required
                value={code}
                // `one-time-code` is what makes iOS offer the digits straight
                // from the mail app, which is most of why the code path is
                // shorter than the link path on a phone at all.
                inputMode="numeric"
                autoComplete="one-time-code"
                placeholder="000000"
                aria-label={LOGIN_CODE_LABEL}
                onChange={(e) => setCode(e.target.value)}
                data-testid="login-code"
              />
              <Button type="submit" disabled={busy} className="w-full">
                {LOGIN_CODE_BUTTON}
              </Button>
              {codeState !== "idle" && (
                <p role="alert" className="text-sm text-foreground" data-testid="login-error">
                  {codeState === "wrong" ? LOGIN_CODE_WRONG : LOGIN_FAILED}
                </p>
              )}
            </form>
            {/* A second tap inside the mailer's 60-second per-user minimum
                surfaces LOGIN_RATE_LIMITED. That is the correct answer, not a
                bug: the screen must never claim a code is on its way when the
                mailer has refused to send one. */}
            <button
              type="button"
              disabled={busy}
              onClick={() => void send(email.trim())}
              className="text-sm underline underline-offset-4 text-muted-foreground"
              data-testid="login-resend"
            >
              {LOGIN_CODE_RESEND}
            </button>
            {(state === "rate_limited" || state === "failed") && (
              <p role="alert" className="text-sm text-foreground" data-testid="login-send-error">
                {state === "rate_limited" ? LOGIN_RATE_LIMITED : LOGIN_FAILED}
              </p>
            )}
          </div>
        ) : (
          <form onSubmit={submitEmail} className="space-y-3">
            <Input
              type="email"
              required
              value={email}
              placeholder="you@example.com"
              aria-label="Email address"
              onChange={(e) => setEmail(e.target.value)}
            />
            <Button type="submit" disabled={busy} className="w-full">
              {LOGIN_BUTTON}
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
