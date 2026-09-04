/**
 * The circle's small pure helpers (spec 015): which circle a browser
 * remembers, and what a refused write says on screen.
 */
import {
  CIRCLE_DUPLICATE,
  CIRCLE_FULL,
  CIRCLE_LAST_ADMIN,
} from "./copy";
import type { Member } from "./types";

/** Per-browser memory of the chosen circle (§8): a convenience, never truth.
 *  Storage can be absent or throw (a private window, a thumbnail capture),
 *  so every touch is guarded and a missing value means "the oldest". */
const CIRCLE_KEY = "kettle-circle";

export function rememberedCircle(): string | null {
  try {
    return localStorage.getItem(CIRCLE_KEY);
  } catch {
    return null;
  }
}

export function rememberCircle(familyId: string): void {
  try {
    localStorage.setItem(CIRCLE_KEY, familyId);
  } catch {
    // Nothing to do: the choice lasts for this page load.
  }
}

/** The 0025 functions refuse with one short code as the message; the app
 *  turns the three a person can act on into §9's sentences. Anything else
 *  is a refusal the screen cannot explain better than "it did not happen",
 *  so it renders nothing and the row stays as it was. */
export function circleRefusal(error: unknown): string | null {
  const message = String((error as { message?: unknown })?.message ?? "");
  if (message.includes("last_admin")) return CIRCLE_LAST_ADMIN;
  if (message.includes("circle_full")) return CIRCLE_FULL;
  if (message.includes("duplicate_email")) return CIRCLE_DUPLICATE;
  return null;
}

export function isAdmin(members: Member[], authUserId: string | null): boolean {
  return members.some((m) => m.auth_user_id === authUserId && m.role === "admin");
}

/** §7's screen-side twin: nobody has mail on. */
export function nobodyListening(members: Member[]): boolean {
  return members.length > 0 && members.every((m) => !m.mail);
}
