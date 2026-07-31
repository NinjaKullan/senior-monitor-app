import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

/** Magic link only. No passwords for a senior-adjacent audience. */
export function Login({ onSend }: { onSend: (email: string) => Promise<void> }) {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await onSend(email.trim());
      setSent(true);
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
        {sent ? (
          <p className="text-sm text-muted-foreground">
            Check your email for a sign-in link.
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
          </form>
        )}
      </CardContent>
    </Card>
  );
}
