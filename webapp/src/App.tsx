import { useCallback, useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { Button } from "@/components/ui/button";
import {
  claimMembership,
  loadSnapshot,
  sendMagicLink,
  type FamilySnapshot,
} from "@/lib/data";
import { buildDigestEntries } from "@/lib/digests";
import { computeGlance } from "@/lib/glance";
import { supabase } from "@/lib/supabase";
import { computeTripwires } from "@/lib/tripwires";
import { Digests } from "@/screens/Digests";
import { FamilyScreen } from "@/screens/Family";
import { Glance } from "@/screens/Glance";
import { Login } from "@/screens/Login";
import { NoFamily } from "@/screens/NoFamily";
import { TripwireDetail } from "@/screens/TripwireDetail";

/**
 * Refresh interval. Polling rather than Supabase realtime — see QUESTIONS.md
 * item 42: the underlying events happen at human pace (a handful of pings a
 * day), and a poll has no socket to drop, no channel-level RLS to reason about,
 * and no reconnect path to get wrong on a phone that has been in a pocket.
 */
const REFRESH_MS = 45_000;

type Tab = "glance" | "digests" | "family";

const TABS: { id: Tab; label: string }[] = [
  { id: "glance", label: "Today" },
  { id: "digests", label: "Digests" },
  { id: "family", label: "Family" },
];

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [snapshot, setSnapshot] = useState<FamilySnapshot | null>(null);
  const [tab, setTab] = useState<Tab>("glance");
  /** The parent whose tripwire health is open, or null for the card list (005d). */
  const [openParentId, setOpenParentId] = useState<string | null>(null);
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data } = supabase.auth.onAuthStateChange((_event, next) => setSession(next));
    return () => data.subscription.unsubscribe();
  }, []);

  const refresh = useCallback(async () => {
    if (!session) return;
    setSnapshot(await loadSnapshot());
    setNow(new Date());
  }, [session]);

  useEffect(() => {
    if (!session) {
      setSnapshot(null);
      return;
    }
    let cancelled = false;
    // Claim first: members.auth_user_id is null until the invited email logs in.
    claimMembership()
      .catch(() => undefined)
      .then(() => (cancelled ? undefined : refresh()));
    const timer = setInterval(refresh, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [session, refresh]);

  if (!session) {
    return (
      <Shell>
        <Login onSend={sendMagicLink} />
      </Shell>
    );
  }

  if (!snapshot) {
    return (
      <Shell>
        <p className="text-muted-foreground">Loading…</p>
      </Shell>
    );
  }

  if (!snapshot.family) {
    return (
      <Shell onSignOut={() => supabase.auth.signOut()}>
        <NoFamily />
      </Shell>
    );
  }

  const familyTz = snapshot.family.tz;
  const states = snapshot.parents.map((parent) =>
    computeGlance(parent, familyTz, snapshot.signals, snapshot.pings, now),
  );
  const entries = buildDigestEntries(
    snapshot.digests,
    snapshot.parents,
    familyTz,
    snapshot.signals,
    snapshot.pings,
  );

  // The open parent survives a refresh only while they are still in the
  // snapshot; a parent removed from the family closes the detail rather than
  // leaving a stale one on screen.
  const openParent = snapshot.parents.find((p) => p.id === openParentId) ?? null;
  const openGlance = states.find((s) => s.parentId === openParentId) ?? null;

  return (
    <Shell onSignOut={() => supabase.auth.signOut()}>
      <nav className="mb-5 flex gap-1" aria-label="Screens">
        {TABS.map((entry) => (
          <Button
            key={entry.id}
            variant={tab === entry.id ? "default" : "ghost"}
            size="sm"
            onClick={() => {
              setTab(entry.id);
              setOpenParentId(null);
            }}
          >
            {entry.label}
          </Button>
        ))}
      </nav>
      {tab === "glance" &&
        (openParent && openGlance ? (
          <TripwireDetail
            glance={openGlance}
            tripwires={computeTripwires(
              openParent,
              familyTz,
              snapshot.signals,
              snapshot.pings,
              now,
            )}
            onBack={() => setOpenParentId(null)}
          />
        ) : (
          <Glance states={states} onOpen={setOpenParentId} />
        ))}
      {tab === "digests" && <Digests entries={entries} />}
      {tab === "family" && (
        <FamilyScreen
          parents={snapshot.parents}
          members={snapshot.members}
          familyTz={familyTz}
        />
      )}
    </Shell>
  );
}

function Shell({
  children,
  onSignOut,
}: {
  children: React.ReactNode;
  onSignOut?: () => void;
}) {
  return (
    <main className="mx-auto min-h-screen w-full max-w-md px-4 py-8">
      <header className="mb-6 flex items-baseline justify-between">
        <h1 className="text-xl font-semibold tracking-tight">Kettle</h1>
        {onSignOut && (
          <Button variant="ghost" size="sm" onClick={onSignOut}>
            Sign out
          </Button>
        )}
      </header>
      {children}
    </main>
  );
}
