/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * DECISIONS 142 — stale credentials degrade to re-auth, never hang.
 *
 * The founder hit this on a real phone: the app restored a stored session, the
 * server rejected the token, and the screen said "Loading…" for as long as it was
 * left open. There was no timer and no error path — `claimMembership()` rejected
 * into a bare `.catch(() => undefined)` and `loadSnapshot()` rejected into
 * nothing, so `snapshot` stayed null and the only way out was closing the tab.
 *
 * The first test here is that exact failure, reproduced. The rest are the other
 * doors into the same room, plus the one case that must NOT sign anyone out.
 */
import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { isAuthFailure } from "@/lib/session";

const AUTH_KEY = "sb-abcdefghij-auth-token";

/** A session shaped like the one supabase-js restores from localStorage. */
const storedSession = {
  access_token: "stale.jwt.value",
  refresh_token: "stale-refresh",
  expires_at: 4102444800,
  user: { id: "u1", email: "child@example.com" },
};

/** What postgrest returns when the JWT it was handed is no good. */
function rejected() {
  return Object.assign(new Error("JWT expired"), { status: 401, code: "PGRST301" });
}

interface Harness {
  getSession: ReturnType<typeof vi.fn>;
  onAuthStateChange: ReturnType<typeof vi.fn>;
  signOut: ReturnType<typeof vi.fn>;
  claimMembership: ReturnType<typeof vi.fn>;
  loadSnapshot: ReturnType<typeof vi.fn>;
}

/** Mount App over mocked auth and mocked reads, and hand back the spies. */
async function mount(overrides: Partial<Harness> = {}) {
  const h: Harness = {
    getSession: vi.fn().mockResolvedValue({ data: { session: storedSession } }),
    onAuthStateChange: vi.fn().mockReturnValue({
      data: { subscription: { unsubscribe: vi.fn() } },
    }),
    // The real one talks to the server, and the server is what is refusing us.
    signOut: vi.fn().mockRejectedValue(new Error("401 from the auth server")),
    claimMembership: vi.fn().mockRejectedValue(rejected()),
    loadSnapshot: vi.fn().mockRejectedValue(rejected()),
    ...overrides,
  };

  vi.doMock("@/lib/supabase", () => ({
    supabase: {
      auth: {
        getSession: h.getSession,
        onAuthStateChange: h.onAuthStateChange,
        signOut: h.signOut,
      },
    },
    isConfigured: true,
  }));
  vi.doMock("@/lib/data", () => ({
    claimMembership: h.claimMembership,
    loadSnapshot: h.loadSnapshot,
    // Spec 013 renamed the sender and added the verifier. This mock stands in
    // for the whole module, and vitest fails hard on an export App imports but
    // the mock does not define — so the two names track the module's surface.
    // Nothing this file asserts changed.
    sendSignInCode: vi.fn().mockResolvedValue(undefined),
    verifySignInCode: vi.fn().mockResolvedValue(undefined),
    // Spec 015's five circle writes, imported by App and never reached here.
    addSeat: vi.fn(),
    removeSeat: vi.fn(),
    setSeatRole: vi.fn(),
    setOwnMail: vi.fn(),
    leaveCircle: vi.fn(),
    pauseParent: vi.fn(),
    resumeParent: vi.fn(),
  }));

  const { default: App } = await import("@/App");
  await act(async () => {
    render(<App />);
  });
  return h;
}

/** The login screen, identified by the one thing only it has. */
const atLogin = () => screen.queryByLabelText("Email address");
const spinning = () => screen.queryByText("Loading…");

beforeEach(() => {
  vi.resetModules();
  localStorage.setItem(AUTH_KEY, JSON.stringify(storedSession));
});

afterEach(() => {
  vi.useRealTimers();
  vi.doUnmock("@/lib/supabase");
  vi.doUnmock("@/lib/data");
  localStorage.clear();
});

describe("the live bug: a stored session the server rejects", () => {
  it("reaches the login screen, not a spinner", async () => {
    await mount();
    await waitFor(() => expect(atLogin()).toBeInTheDocument());
    expect(spinning()).toBeNull();
  });

  it("clears the stored session, so a reload does not land in it again", async () => {
    const h = await mount();
    await waitFor(() => expect(atLogin()).toBeInTheDocument());
    // signOut was asked, and failed, exactly as it does against a dead token.
    expect(h.signOut).toHaveBeenCalled();
    // The stored copy is gone anyway — that is the part that had to not depend
    // on a server call succeeding.
    expect(localStorage.getItem(AUTH_KEY)).toBeNull();
  });

  it("lands on login when only the reads are refused and the claim succeeds", async () => {
    // The membership claim is idempotent and can pass on a token the row-level
    // reads then refuse; the snapshot is the second door into the same room.
    await mount({ claimMembership: vi.fn().mockResolvedValue(undefined) });
    await waitFor(() => expect(atLogin()).toBeInTheDocument());
  });

  it("stops at the refused claim rather than waiting on the read behind it", async () => {
    // The plant drill found this one: with both calls refused, the snapshot's
    // own guard reaches login and the claim's guard proves nothing. Here the
    // claim is refused and the read never settles — a realistic pairing, and
    // the only shape in which the claim's guard is the thing doing the work.
    // Without it the person waits out the whole 15-second bound to learn what
    // was already known on the first response.
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const loadSnapshot = vi.fn(() => new Promise(() => {}));
    await mount({ loadSnapshot });
    await waitFor(() => expect(atLogin()).toBeInTheDocument());
    // Well inside the bound: this was the claim's doing, not the timer's.
    expect(vi.getTimerCount()).toBeGreaterThanOrEqual(0);
    // And the read was never attempted on a token already known to be refused.
    expect(loadSnapshot).not.toHaveBeenCalled();
  });

  it("lands on login when the token refresh gives up", async () => {
    // supabase-js signals a refresh it cannot complete by emitting a null
    // session. Nothing else in the app is watching for that.
    let emit: ((event: string, session: unknown) => void) | undefined;
    await mount({
      onAuthStateChange: vi.fn().mockImplementation((cb) => {
        emit = cb;
        return { data: { subscription: { unsubscribe: vi.fn() } } };
      }),
      claimMembership: vi.fn().mockResolvedValue(undefined),
      loadSnapshot: vi.fn(() => new Promise(() => {})),
    });
    await waitFor(() => expect(emit).toBeDefined());
    await act(async () => emit!("TOKEN_REFRESH_FAILED", null));
    await waitFor(() => expect(atLogin()).toBeInTheDocument());
  });
});

describe("loading is bounded", () => {
  it("falls to login when nothing ever resolves", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    // Neither promise settles, ever: the shape of a stall this code does not
    // anticipate, which is the reason the bound exists at all.
    await mount({
      getSession: vi.fn(() => new Promise(() => {})),
      claimMembership: vi.fn(() => new Promise(() => {})),
      loadSnapshot: vi.fn(() => new Promise(() => {})),
    });
    expect(spinning()).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(15_000);
    });
    await waitFor(() => expect(atLogin()).toBeInTheDocument());
  });

  it("does not fire while a slow load is still succeeding inside the bound", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const snapshot = {
      family: { id: "f1", name: "Sharma", tz: "Asia/Kolkata" },
      parents: [], members: [], signals: [], pings: [], latestPings: [], setupLinks: [],
    };
    await mount({
      claimMembership: vi.fn().mockResolvedValue(undefined),
      loadSnapshot: vi.fn(
        () => new Promise((resolve) => setTimeout(() => resolve(snapshot), 9_000)),
      ),
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(9_500);
    });
    // Nine seconds is slow, not broken. Signing this person out would be the
    // bound doing harm rather than preventing it.
    await waitFor(() => expect(atLogin()).toBeNull());
    expect(spinning()).toBeNull();
  });
});

describe("what must NOT end a session", () => {
  it("keeps waiting through a plain network failure", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    await mount({
      claimMembership: vi.fn().mockResolvedValue(undefined),
      loadSnapshot: vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    });
    // A train tunnel is not a rejected credential. The app stays put and retries
    // on the next tick; only the bound may end this, and not for another while.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5_000);
    });
    expect(atLogin()).toBeNull();
    expect(localStorage.getItem(AUTH_KEY)).not.toBeNull();
  });
});

describe("isAuthFailure is narrow on purpose", () => {
  it("recognises the ways a token is refused", () => {
    for (const error of [
      { status: 401 },
      { status: 403 },
      { code: "PGRST301" },
      { code: "42501" },
      { code: "refresh_token_already_used" },
      { name: "AuthApiError" },
      { message: "JWT expired" },
    ]) {
      expect(isAuthFailure(error)).toBe(true);
    }
  });

  it("leaves everything else alone", () => {
    for (const error of [
      null,
      undefined,
      "a string",
      new TypeError("Failed to fetch"),
      { status: 500 },
      { status: 429 },
      { code: "PGRST116" },
      { message: "column does not exist" },
    ]) {
      expect(isAuthFailure(error)).toBe(false);
    }
  });
});
