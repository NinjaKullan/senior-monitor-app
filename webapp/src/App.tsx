import { useCallback, useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import {
  addContact,
  addJournalEntry,
  addSeat,
  claimMembership,
  deleteContact,
  deleteEntry,
  editEntry,
  leaveCircle,
  loadSnapshot,
  pauseParent,
  removeSeat,
  resumeParent,
  setOwnMail,
  setSeatRole,
  placeUpdate,
  saveCityLabel,
  savePlace,
  sendSignInCode,
  verifySignInCode,
  moveContact,
  updateContact,
  type ContactDraft,
  type FamilySnapshot,
} from "@/lib/data";
import {
  AUTO_NOTE_AUTHOR,
  CIRCLE_SWITCHER_LABEL,
  CITY_CHANGED_NOTE,
  TAGLINE,
  WHO_TO_CALL_TAB,
} from "@/lib/copy";
import { isAdmin, rememberCircle, rememberedCircle } from "@/lib/circle";
import type { Family } from "@/lib/types";
import { isKnownIana, type CityEntry } from "@/lib/cities";
import { computeParentToday, computeRollup, type ParentToday } from "@/lib/parentState";
import { buildSetupEntries } from "@/lib/setupLinks";
import { localDate } from "@/lib/time";
import type { NoteDraft, ReplyDraft } from "@/components/NotesPanel";
import {
  RESTORE_TIMEOUT_MS,
  clearStoredSession,
  isAuthFailure,
} from "@/lib/session";
import { supabase } from "@/lib/supabase";
import { FamilyScreen } from "@/screens/Family";
import { MemoryScreen } from "@/screens/Memory";
import { WhoToCallScreen } from "@/screens/WhoToCall";
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

type Tab = "today" | "memory" | "who" | "family";

// Spec 012 §2: the journal is a place now, so the nav names it — Today for
// the day, Memory for the record, Family for the household's settings.
const TABS: { id: Tab; label: string }[] = [
  { id: "today", label: "Today" },
  { id: "memory", label: "Memory" },
  // Spec 012 §9.3, label ruled VERBATIM by DECISIONS 211. It sits beside
  // Memory because that is where it used to live, and before Family because
  // it is something a family reaches for, not something they configure.
  { id: "who", label: WHO_TO_CALL_TAB },
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
  /** The chosen circle (spec 015 §8): remembered per browser, oldest by
   *  default. The snapshot loader falls back when it no longer applies. */
  const [circleId, setCircleId] = useState<string | null>(() => rememberedCircle());
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
      setSnapshot(await loadSnapshot(new Date(), circleId));
      setNow(new Date());
    } catch (error) {
      // A read refused for authentication reasons is the session ending, whether
      // it happens on the first load or an hour into a poll. Anything else — a
      // dropped connection, a 500 — leaves the last good snapshot on screen and
      // waits for the next tick, because signing someone out over a train tunnel
      // would be its own bug.
      if (isAuthFailure(error)) await failToLogin();
    }
  }, [session, circleId, failToLogin]);

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
        <Login onSend={sendSignInCode} onVerify={verifySignInCode} />
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
  const familyId = snapshot.family.id;
  const viewerId = session?.user?.id ?? null;
  // Spec 018: the viewer's seat decides whose Edit and Delete render; the
  // functions decide server-side regardless. Journal dates render on the
  // viewer's own clock (DECISIONS 279); the family zone stays for parents.
  const viewer = {
    memberId: snapshot.members.find((m) => m.auth_user_id === viewerId)?.id ?? null,
    admin: isAdmin(snapshot.members, viewerId),
  };
  const viewerTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const editNote = async (entryId: number, body: string) => {
    await editEntry(entryId, body);
    await refresh();
  };
  const deleteNote = async (entryId: number) => {
    await deleteEntry(entryId);
    await refresh();
  };

  // Spec 015 §8: choosing a circle is remembered and reloads the snapshot;
  // the open parent closes because it belonged to the other household.
  const chooseCircle = (id: string) => {
    rememberCircle(id);
    setOpenParentId(null);
    setCircleId(id);
  };
  // Spec 017 §5: admins only; a member's card carries the state, not the
  // control. The functions refuse a non-admin server-side regardless.
  const pause = isAdmin(snapshot.members, viewerId)
    ? {
        onPause: async (parentId: string, duration: "week" | "open") => {
          await pauseParent(parentId, duration);
          await refresh();
        },
        onResume: async (parentId: string) => {
          await resumeParent(parentId);
          await refresh();
        },
      }
    : undefined;
  const circle = {
    onAddSeat: async (displayName: string, email: string) => {
      await addSeat(familyId, displayName, email);
      await refresh();
    },
    onRemoveSeat: async (memberId: string) => {
      await removeSeat(memberId);
      await refresh();
    },
    onSetRole: async (memberId: string, role: "admin" | "member") => {
      await setSeatRole(memberId, role);
      await refresh();
    },
    onSetMail: async (mail: boolean) => {
      await setOwnMail(familyId, mail);
      await refresh();
    },
    onLeave: async () => {
      await leaveCircle(familyId);
      // Leaving may have left the account with another circle or none; the
      // remembered id no longer applies either way, so the loader's fallback
      // (oldest, or the NoFamily screen) decides.
      setCircleId(null);
      await refresh();
    },
  };
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
      now,
    ),
  );
  const rollup = computeRollup(states, familyTz, now);
  // The open parent survives a refresh only while they are still in the
  // snapshot; a parent removed from the family closes the detail rather than
  // leaving a stale one on screen.
  const openState = states.find((s) => s.parentId === openParentId) ?? null;

  // "Wednesday · August 26" (spec 009 §2): middot, never a dash.
  const dateLine = `${new Intl.DateTimeFormat("en-US", { weekday: "long" }).format(now)} · ${new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric" }).format(now)}`;
  const todayDate = localDate(now, Intl.DateTimeFormat().resolvedOptions().timeZone);

  const addNote = async (draft: NoteDraft) => {
    await addJournalEntry({
      family_id: familyId,
      parent_id: draft.parentId,
      author_label: draft.authorLabel,
      body: draft.body,
      event_date: draft.eventDate,
    });
    await refresh();
  };

  // Spec 016: a reply is the same insert with parent_entry_id; the tag is
  // the note's and the 0026 trigger writes it, so null travels here.
  const addReply = async (draft: ReplyDraft) => {
    await addJournalEntry({
      family_id: familyId,
      parent_id: null,
      author_label: draft.authorLabel,
      body: draft.body,
      event_date: null,
      parent_entry_id: draft.parentEntryId,
    });
    await refresh();
  };

  // Spec 010 §1/§4: one pick writes label + zone (+ the changeover stamp
  // when the zone actually moved), validated against the shipped list, and
  // the journal remembers the move in the product's own hand.
  const pickCity = async (parentId: string, entry: CityEntry) => {
    const parent = snapshot.parents.find((p) => p.id === parentId);
    if (!parent || !isKnownIana(entry.iana)) return;
    const unchanged = parent.city_label === entry.city && parent.tz === entry.iana;
    await savePlace(
      parentId,
      placeUpdate(parent.tz, familyTz, entry, new Date().toISOString()),
    );
    if (!unchanged) {
      await addJournalEntry({
        family_id: familyId,
        parent_id: parentId,
        author_label: AUTO_NOTE_AUTHOR,
        body: CITY_CHANGED_NOTE.replace("{name}", parent.display_name).replace(
          "{city}",
          entry.city,
        ),
        event_date: null,
        // Spec 012 §5: the webapp's one auto note names its kind.
        kind: "city_change",
      });
    }
    await refresh();
  };

  const clearCity = async (parentId: string) => {
    await saveCityLabel(parentId, null);
    await refresh();
  };

  // Spec 012 §4: the contacts sheet — editable reference data, RLS-scoped
  // server-side like everything else; position keeps the family's own order.
  const addContactRow = async (draft: ContactDraft) => {
    await addContact(familyId, draft, snapshot?.contacts.length ?? 0);
    await refresh();
  };
  const updateContactRow = async (id: number, draft: ContactDraft) => {
    await updateContact(id, draft);
    await refresh();
  };
  const removeContactRow = async (id: number) => {
    await deleteContact(id);
    await refresh();
  };

  // Spec 012 §9.3: the call-first order. A move SWAPS the two rows' positions
  // rather than renumbering the list, so one move is two writes and never
  // touches a row the family did not point at. Positions can arrive equal
  // (0021 defaults them to 0), so the neighbour is found in the list's own
  // rendered order and the swap writes distinct ranks either way.
  const moveContactRow = async (id: number, direction: -1 | 1) => {
    const ordered = (snapshot?.contacts ?? [])
      .slice()
      .sort((a, b) => a.position - b.position || a.id - b.id);
    const index = ordered.findIndex((contact) => contact.id === id);
    const swapWith = ordered[index + direction];
    if (index === -1 || !swapWith) return;
    await moveContact(id, index + direction);
    await moveContact(swapWith.id, index);
    await refresh();
  };

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
      families={snapshot.families}
      circleId={familyId}
      onChooseCircle={chooseCircle}
    >
      {tab === "today" &&
        (openState ? (
          <ParentDetail
            state={openState}
            notes={snapshot.journalByParent[openState.parentId] ?? []}
            todayDate={todayDate}
            tz={viewerTz}
            onBack={() => setOpenParentId(null)}
            onAddNote={addNote}
            onAddReply={addReply}
            viewer={viewer}
            onEdit={editNote}
            onDelete={deleteNote}
            onSteps={() => navigate("family")}
          />
        ) : (
          <Today states={states} rollup={rollup} dateLine={dateLine} onOpen={setOpenParentId} pause={pause} />
        ))}
      {tab === "memory" && (
        <MemoryScreen
          parentLabels={states.map((s) => ({ parentId: s.parentId, label: s.label }))}
          journal={snapshot.journal}
          todayDate={todayDate}
          tz={viewerTz}
          onAddNote={addNote}
          onAddReply={addReply}
          viewer={viewer}
          onEdit={editNote}
          onDelete={deleteNote}
        />
      )}
      {tab === "who" && (
        <WhoToCallScreen
          parentLabels={states.map((s) => ({ parentId: s.parentId, label: s.label }))}
          contacts={snapshot.contacts}
          onAddContact={addContactRow}
          onUpdateContact={updateContactRow}
          onRemoveContact={removeContactRow}
          onMoveContact={moveContactRow}
        />
      )}
      {tab === "family" && (
        <FamilyScreen
          parentStates={states}
          cities={Object.fromEntries(
            snapshot.parents.map((parent) => [parent.id, parent.city_label ?? ""]),
          )}
          members={snapshot.members}
          viewerId={viewerId}
          circle={circle}
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
          onPickCity={pickCity}
          onClearCity={clearCity}
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
  families = [],
  circleId = null,
  onChooseCircle,
}: {
  children: React.ReactNode;
  onSignOut?: () => void;
  isWide: boolean;
  tab?: Tab;
  onNavigate?: (tab: Tab) => void;
  /** Spec 015 §8: the switcher, rendered ONLY for two or more circles. A
   *  single-circle account sees no switcher and no family name (DECISIONS
   *  124 stands for them); the name shows here and nowhere else (269). */
  families?: Family[];
  circleId?: string | null;
  onChooseCircle?: (id: string) => void;
}) {
  const showNav = Boolean(tab && onNavigate);
  const switcher =
    families.length >= 2 && onChooseCircle ? (
      <CircleSwitcher families={families} circleId={circleId} onChoose={onChooseCircle} />
    ) : null;
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
          {switcher}
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
              {switcher}
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

/** The circle switcher (spec 015 §8): "Looking at" and the circle names as
 *  stored, one row at the top of the rail (a select in the narrow header). */
function CircleSwitcher({
  families,
  circleId,
  onChoose,
}: {
  families: Family[];
  circleId: string | null;
  onChoose: (id: string) => void;
}) {
  return (
    <label
      data-testid="circle-switcher"
      style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 12, fontWeight: 700, letterSpacing: ".08em", textTransform: "uppercase", color: "var(--mute)" }}
    >
      {CIRCLE_SWITCHER_LABEL}
      <select
        value={circleId ?? ""}
        onChange={(event) => onChoose(event.target.value)}
        style={{
          minHeight: "2.75rem",
          padding: "0.5rem 0.75rem",
          border: "1px solid var(--hair)",
          borderRadius: "0.75rem",
          background: "var(--card)",
          color: "var(--ink)",
          fontSize: "0.9375rem",
          fontWeight: 600,
          textTransform: "none",
          letterSpacing: 0,
        }}
      >
        {families.map((family) => (
          <option key={family.id} value={family.id}>
            {family.name}
          </option>
        ))}
      </select>
    </label>
  );
}
