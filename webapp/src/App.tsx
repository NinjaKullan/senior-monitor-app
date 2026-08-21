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
import { buildSetupEntries } from "@/lib/setupLinks";
import {
  RESTORE_TIMEOUT_MS,
  clearStoredSession,
  isAuthFailure,
} from "@/lib/session";
import { supabase } from "@/lib/supabase";
import { computeTripwires } from "@/lib/tripwires";
import { Digests } from "@/screens/Digests";
import { FamilyScreen } from "@/screens/Family";
import { Glance } from "@/screens/Glance";
import { Login } from "@/screens/Login";
import { NoFamily } from "@/screens/NoFamily";
import { TripwireDetail } from "@/screens/TripwireDetail";

/**
 * Refresh interval. Polling rather than Supabase realtime — see DECISIONS.md
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

/**
 * Where the app is with respect to being signed in.
 *
 * `restoring` is the state the field bug lived in (DECISIONS 142). It used to be
 * indistinguishable from `signed-out`, so a stored session that the server was
 * about to reject rendered the login screen for an instant and then a spinner
 * forever. Naming it is what makes it boundable: a state with no exit is only
 * safe if something is watching the clock on it.
 */
type AuthState = "restoring" | "signed-in" | "signed-out";

export default function App() {
  const [authState, setAuthState] = useState<AuthState>("restoring");
  const [session, setSession] = useState<Session | null>(null);
  const [snapshot, setSnapshot] = useState<FamilySnapshot | null>(null);
  const [tab, setTab] = useState<Tab>("glance");
  /** The parent whose tripwire health is open, or null for the card list (005d). */
  const [openParentId, setOpenParentId] = useState<string | null>(null);
  const [now, setNow] = useState(() => new Date());

  /**
   * End the session and land on login. The one exit from every failure below.
   *
   * Stale credentials must degrade to re-auth, never hang: the login screen is
   * the only screen a person can act on when their token has gone bad, so every
   * path that learns the token is bad ends here.
   */
  const failToLogin = useCallback(async () => {
    await clearStoredSession(supabase.auth);
    setSession(null);
    setSnapshot(null);
    setAuthState("signed-out");
  }, []);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setAuthState(data.session ? "signed-in" : "signed-out");
    });
    const { data } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);
      setAuthState(next ? "signed-in" : "signed-out");
    });
    return () => data.subscription.unsubscribe();
  }, []);

  const refresh = useCallback(async () => {
    if (!session) return;
    try {
      setSnapshot(await loadSnapshot());
      setNow(new Date());
    } catch (error) {
      // A read refused for authentication reasons is the session ending, whether
      // it happens on the first load or an hour into a poll. Anything else — a
      // dropped connection, a 500 — leaves the last good snapshot on screen and
      // waits for the next tick, because signing someone out over a train tunnel
      // would be its own bug.
      if (isAuthFailure(error)) await failToLogin();
    }
  }, [session, failToLogin]);

  useEffect(() => {
    if (!session) {
      setSnapshot(null);
      return;
    }
    let cancelled = false;
    // Claim first: members.auth_user_id is null until the invited email logs in.
    // A claim refused for authentication reasons is the stored session being
    // rejected — the field bug's first symptom, and it used to be swallowed
    // whole by a bare `.catch(() => undefined)`.
    claimMembership()
      .catch((error: unknown) => {
        if (isAuthFailure(error)) {
          void failToLogin();
          return "stop";
        }
        return undefined;
      })
      .then((outcome) => (cancelled || outcome === "stop" ? undefined : refresh()));
    const timer = setInterval(refresh, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [session, refresh, failToLogin]);

  /**
   * The bound on "Loading…". Nothing here knows *why* a restore stalled — that
   * is the point. The failures above are the ones we anticipated; this catches
   * the ones we did not, including a promise that simply never settles, and it
   * ends where all of them end.
   */
  const stalled = authState === "restoring" || (authState === "signed-in" && !snapshot);
  useEffect(() => {
    if (!stalled) return;
    const timer = setTimeout(() => void failToLogin(), RESTORE_TIMEOUT_MS);
    return () => clearTimeout(timer);
  }, [stalled, failToLogin]);

  if (authState === "signed-out") {
    return (
      <Shell>
        <Login onSend={sendMagicLink} />
      </Shell>
    );
  }

  if (authState === "restoring" || !snapshot) {
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
          setupEntries={buildSetupEntries(
            snapshot.parents,
            snapshot.setupLinks,
            snapshot.pings,
            now,
          )}
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
