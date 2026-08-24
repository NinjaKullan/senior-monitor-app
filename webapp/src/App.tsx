import { useCallback, useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import {
  claimMembership,
  loadSnapshot,
  sendMagicLink,
  type FamilySnapshot,
} from "@/lib/data";
import { TAGLINE } from "@/lib/copy";
import { computeParentToday, type ParentToday } from "@/lib/parentState";
import { buildSetupEntries } from "@/lib/setupLinks";
import {
  RESTORE_TIMEOUT_MS,
  clearStoredSession,
  isAuthFailure,
} from "@/lib/session";
import { supabase } from "@/lib/supabase";
import { FamilyScreen } from "@/screens/Family";
import { Login } from "@/screens/Login";
import { NoFamily } from "@/screens/NoFamily";
import { ParentDetail } from "@/screens/ParentDetail";
import { Today } from "@/screens/Today";

/**
 * Refresh interval. Polling rather than Supabase realtime — see DECISIONS.md
 * item 42: the underlying events happen at human pace (a handful of pings a
 * day), and a poll has no socket to drop, no channel-level RLS to reason about,
 * and no reconnect path to get wrong on a phone that has been in a pocket.
 */
const REFRESH_MS = 45_000;

/** The v5 layout switches from bottom tabs to the sidebar rail here. */
const WIDE_MIN_PX = 760;

type Tab = "today" | "family";

const TABS: { id: Tab; label: string }[] = [
  { id: "today", label: "Today" },
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
  const [tab, setTab] = useState<Tab>("today");
  /** The parent whose detail is open, or null for the Today card grid. */
  const [openParentId, setOpenParentId] = useState<string | null>(null);
  const [now, setNow] = useState(() => new Date());
  const [width, setWidth] = useState(() =>
    typeof window !== "undefined" ? window.innerWidth : 1200,
  );

  useEffect(() => {
    const onResize = () => setWidth(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // Both token sets ship (spec 008 §5.1): Day on the body, Night when the
  // system asks for dark, and live on the toggle like everything else here.
  useEffect(() => {
    const query = window.matchMedia?.("(prefers-color-scheme: dark)");
    const apply = () =>
      document.body.setAttribute("data-kt", query?.matches ? "night" : "day");
    apply();
    query?.addEventListener?.("change", apply);
    return () => query?.removeEventListener?.("change", apply);
  }, []);

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

  const isWide = width >= WIDE_MIN_PX;

  if (authState === "signed-out") {
    return (
      <Shell isWide={isWide}>
        <Login onSend={sendMagicLink} />
      </Shell>
    );
  }

  if (authState === "restoring" || !snapshot) {
    return (
      <Shell isWide={isWide}>
        <p style={{ color: "var(--ink2)" }}>Loading…</p>
      </Shell>
    );
  }

  if (!snapshot.family) {
    return (
      <Shell isWide={isWide} onSignOut={() => supabase.auth.signOut()}>
        <NoFamily />
      </Shell>
    );
  }

  const familyTz = snapshot.family.tz;
  // The two ping sets keep their audiences (DECISIONS 160/166): the windowed
  // set feeds today's state, the unwindowed latest rows feed the tripwire ages
  // inside computeParentToday and the setup card's has-ever-pinged check.
  const states: ParentToday[] = snapshot.parents.map((parent) =>
    computeParentToday(
      parent,
      familyTz,
      snapshot.signals,
      snapshot.pings,
      snapshot.latestPings,
      snapshot.setupLinks,
      now,
    ),
  );
  // The open parent survives a refresh only while they are still in the
  // snapshot; a parent removed from the family closes the detail rather than
  // leaving a stale one on screen.
  const openState = states.find((s) => s.parentId === openParentId) ?? null;

  const dateLine = new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(now);

  const navigate = (next: Tab) => {
    setTab(next);
    setOpenParentId(null);
  };

  return (
    <Shell
      isWide={isWide}
      onSignOut={() => supabase.auth.signOut()}
      tab={tab}
      onNavigate={navigate}
    >
      {tab === "today" &&
        (openState ? (
          <ParentDetail state={openState} onBack={() => setOpenParentId(null)} />
        ) : (
          <Today states={states} dateLine={dateLine} onOpen={setOpenParentId} />
        ))}
      {tab === "family" && (
        <FamilyScreen
          parentStates={states}
          members={snapshot.members}
          setupEntries={buildSetupEntries(
            snapshot.parents,
            snapshot.setupLinks,
            // Unwindowed (DECISIONS 166): "has ever pinged" must not revert
            // when a parent's pings age out of the 14-day window.
            snapshot.latestPings,
            now,
          )}
          onOpen={(id) => {
            setTab("today");
            setOpenParentId(id);
          }}
        />
      )}
    </Shell>
  );
}

/** The steam wordmark from the v5 rail, still by design outside the hero. */
function Wordmark({ size }: { size: "rail" | "header" }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <svg width="16" height="17" aria-hidden="true">
        <path
          d="M4.5 14.5 C3.2 12.4 5.8 10.8 4.6 8.6 C3.8 7.1 4.6 5.6 5.6 4.4"
          style={{ fill: "none", stroke: "var(--ink3)", strokeWidth: 1.5, strokeLinecap: "round" }}
        />
        <path
          d="M10.5 14.5 C9.2 12.4 11.8 10.8 10.6 8.6 C9.8 7.1 10.6 5.6 11.6 4.4"
          style={{ fill: "none", stroke: "var(--ink3)", strokeWidth: 1.5, strokeLinecap: "round" }}
        />
      </svg>
      <span
        className="kt-serif"
        style={{
          fontStyle: "italic",
          fontWeight: 500,
          fontSize: size === "rail" ? 24 : 20,
          letterSpacing: "-.01em",
        }}
      >
        Kettle
      </span>
    </div>
  );
}

/**
 * The v5 frame: a sidebar rail from 760px up, bottom tabs below it (spec 008
 * §5.1). Nav renders Today and Family only — the Digests entry the design file
 * shows is out of phase 1 (DECISIONS 169).
 */
function Shell({
  children,
  onSignOut,
  isWide,
  tab,
  onNavigate,
}: {
  children: React.ReactNode;
  onSignOut?: () => void;
  isWide: boolean;
  tab?: Tab;
  onNavigate?: (tab: Tab) => void;
}) {
  const showNav = Boolean(tab && onNavigate);
  return (
    <div style={{ minHeight: "100vh", display: "flex", background: "var(--paper)" }}>
      {isWide && (
        <div
          style={{
            width: 238,
            flex: "0 0 238px",
            boxSizing: "border-box",
            padding: "34px 26px",
            position: "sticky",
            top: 0,
            alignSelf: "flex-start",
            display: "flex",
            flexDirection: "column",
            gap: 30,
          }}
        >
          <Wordmark size="rail" />
          {showNav && (
            <nav aria-label="Screens" style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {TABS.map((entry) => {
                const active = tab === entry.id;
                return (
                  <button
                    key={entry.id}
                    type="button"
                    className="kt-rowbtn"
                    onClick={() => onNavigate?.(entry.id)}
                    style={{
                      boxSizing: "border-box",
                      width: "100%",
                      textAlign: "left",
                      background: active ? "var(--card)" : "none",
                      border: active ? "1px solid var(--hair)" : "1px solid rgba(0,0,0,0)",
                      borderRadius: 14,
                      padding: "11px 14px",
                      fontSize: 15.5,
                      fontWeight: 600,
                      color: active ? "var(--copperdeep)" : "var(--ink2)",
                      cursor: "pointer",
                    }}
                  >
                    {entry.label}
                  </button>
                );
              })}
            </nav>
          )}
          <div
            className="kt-serif"
            style={{
              marginTop: 4,
              fontStyle: "italic",
              fontSize: 13.5,
              lineHeight: 1.5,
              color: "var(--ink3)",
              maxWidth: 150,
            }}
          >
            {TAGLINE}
          </div>
          {onSignOut && (
            <button
              type="button"
              onClick={onSignOut}
              style={{
                textAlign: "left",
                background: "none",
                border: "none",
                padding: "9px 0",
                fontSize: 13.5,
                fontWeight: 600,
                color: "var(--ink3)",
                cursor: "pointer",
              }}
            >
              Sign out
            </button>
          )}
        </div>
      )}
      <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
        <main
          style={{
            flex: 1,
            boxSizing: "border-box",
            width: "100%",
            maxWidth: 1120,
            margin: "0 auto",
            padding: "26px 22px 84px",
          }}
        >
          {!isWide && (
            <header
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 8,
                padding: "4px 0 20px",
              }}
            >
              <Wordmark size="header" />
              {onSignOut && (
                <button
                  type="button"
                  onClick={onSignOut}
                  style={{
                    background: "none",
                    border: "none",
                    padding: "9px 0",
                    fontSize: 13.5,
                    fontWeight: 600,
                    color: "var(--ink3)",
                    cursor: "pointer",
                  }}
                >
                  Sign out
                </button>
              )}
            </header>
          )}
          {children}
        </main>
        {!isWide && showNav && (
          <nav
            aria-label="Screens"
            style={{
              position: "sticky",
              bottom: 0,
              zIndex: 20,
              display: "flex",
              alignItems: "stretch",
              background: "var(--tabbg)",
              backdropFilter: "blur(14px)",
              borderTop: "1px solid var(--hair)",
              padding: "6px 6px calc(6px + env(safe-area-inset-bottom, 0px))",
            }}
          >
            {TABS.map((entry) => (
              <button
                key={entry.id}
                type="button"
                onClick={() => onNavigate?.(entry.id)}
                style={{
                  flex: 1,
                  background: "none",
                  border: "none",
                  padding: "12px 4px",
                  minHeight: 48,
                  cursor: "pointer",
                  color: tab === entry.id ? "var(--copperdeep)" : "var(--ink3)",
                  fontSize: 14,
                  fontWeight: 600,
                  letterSpacing: ".01em",
                }}
              >
                {entry.label}
              </button>
            ))}
          </nav>
        )}
      </div>
    </div>
  );
}
