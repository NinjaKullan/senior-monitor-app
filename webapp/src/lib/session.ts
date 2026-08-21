/**
 * Stale credentials degrade to re-authentication. They never hang.
 *
 * The field bug (DECISIONS 142): the app restored a stored session from
 * localStorage, the server rejected the token, `claimMembership()` rejected into
 * a `.catch(() => undefined)`, `loadSnapshot()` rejected into nothing at all, and
 * `snapshot` stayed null forever. The screen said "Loading…" and meant it — there
 * was no timer, no retry and no path out of that state except closing the tab.
 * The founder hit it on a real phone, and the only reason it is survivable is
 * that this app is read-only: a family looking for reassurance got a spinner.
 *
 * A stored session is a *claim* about being signed in, and the server is the only
 * thing that can settle it. Anything that says the claim is false — a 401, an
 * expired JWT, a refresh that will not refresh — has to end at the login screen,
 * because that is the one screen from which a person can fix it themselves.
 */

/** Postgrest and GoTrue codes that all mean "this token is not good any more". */
const AUTH_CODES = new Set([
  "PGRST301", // JWT expired — postgrest's code, not an HTTP status
  "PGRST302", // no JWT / anonymous where authentication was required
  "42501", // insufficient_privilege: RLS refused the role the token carries
  "invalid_claim",
  "bad_jwt",
  "session_not_found",
  "refresh_token_not_found",
  "refresh_token_already_used",
]);

/**
 * Does this error mean the credentials are no longer good?
 *
 * Deliberately narrow. A network blip, a 500, a typo in a query — none of those
 * are grounds for throwing someone out of the app, and signing a working session
 * out because the wifi dropped would be its own bug. Only the errors that say the
 * *token* is the problem end the session.
 */
export function isAuthFailure(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const e = error as { status?: number; code?: string; message?: string; name?: string };
  if (e.status === 401 || e.status === 403) return true;
  if (e.code && AUTH_CODES.has(e.code)) return true;
  if (e.name === "AuthApiError" || e.name === "AuthSessionMissingError") return true;
  const message = (e.message ?? "").toLowerCase();
  return message.includes("jwt expired") || message.includes("invalid claim");
}

/**
 * How long "Loading…" is allowed to be the whole screen.
 *
 * Generous on purpose — these are seven small reads over a phone connection that
 * may be on a train — but finite, because the point is that no failure mode this
 * bound does not anticipate can still produce a permanent spinner. A slow success
 * inside the bound renders normally; anything else lands on login, where the
 * person can act.
 */
export const RESTORE_TIMEOUT_MS = 15_000;

/** Supabase persists its session under `sb-<project-ref>-auth-token`. */
const STORAGE_KEY = /^sb-.*-auth-token$/;

/**
 * Clear the stored session by hand, after asking the client to.
 *
 * `signOut()` talks to the server, and the whole reason we are here is that the
 * server is refusing this token — so the call can fail, and on some paths it
 * leaves the stored copy behind. A stored session that survives a sign-out is
 * the bug again on the next page load, so the storage key is removed directly
 * rather than trusted to a call that is already failing. `scope: "local"` asks
 * for the local half only, which is the half that matters here.
 */
export async function clearStoredSession(
  auth: { signOut: (options?: { scope?: "local" }) => Promise<unknown> },
  storage: Storage | undefined = typeof localStorage === "undefined" ? undefined : localStorage,
): Promise<void> {
  try {
    await auth.signOut({ scope: "local" });
  } catch {
    // Expected on a rejected token. The removal below is the part that must happen.
  }
  if (!storage) return;
  try {
    for (const key of Object.keys(storage)) {
      if (STORAGE_KEY.test(key)) storage.removeItem(key);
    }
  } catch {
    // Private mode, or storage disabled. Nothing was stored, so nothing to clear.
  }
}
