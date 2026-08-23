/**
 * Every read the app performs, in one file.
 *
 * No query names a family: RLS decides what comes back. The client asking
 * politely for its own rows would only mask a policy bug, and this is the layer
 * a future spec is most likely to extend carelessly.
 *
 * **No unbounded read of a growing table** (DECISIONS 160). PostgREST caps an
 * unlimited select at 1000 rows and says nothing — the read "works", the data
 * is simply incomplete — and prod pings crossed that cliff and showed a stale
 * "Last routine seen" over a parent who was actively pinging. `readAll` is
 * therefore only for tables that cannot plausibly reach 1000 rows per family
 * under RLS, each with its reason:
 *
 *   families       — exactly one per account.
 *   parents        — a handful of people.
 *   members        — a handful of people.
 *   parent_signals — parents × the fixed signal vocabulary (≤ ~8 each).
 *   setup_links    — one row per manual founder issuance; rotations accumulate
 *                    but at human pace, decades from four figures.
 *
 * `pings` is the one table that grows without bound, and it gets its own
 * bounded read below. A new table joins `readAll` only with a written reason
 * it cannot grow, or it gets the bounded treatment.
 */

import { supabase } from "./supabase";
import { READ_SURFACE } from "./queries";
import type {
  Family,
  Member,
  Parent,
  ParentSignal,
  Ping,
  SetupLink,
} from "./types";

async function readAll<T>(table: keyof typeof READ_SURFACE): Promise<T[]> {
  const { data, error } = await supabase.from(table).select(READ_SURFACE[table]);
  if (error) throw error;
  return (data ?? []) as T[];
}

/**
 * The bounded pings read (DECISIONS 160): what the UI consumes, and only that.
 *
 * Every derivation downstream — latest alarm-grade ping, per-signal latest,
 * the day arc — needs recent rows, so the read is a recent window, newest
 * first, with an explicit limit. Ordering matters as much as the limit: with
 * `ts_utc` descending, any truncation drops the OLDEST rows, so the newest
 * ping — the one the Today card's honesty hangs on — always survives.
 *
 * Per parent rather than per family, so one prolific phone cannot crowd
 * another parent's pings out of a shared cap. The `eq(parent_id)` here is a
 * shape filter, not an isolation filter — it partitions the limit between
 * parents the snapshot already holds; RLS still decides what is visible, and
 * no query names a family.
 */
export const PINGS_WINDOW_DAYS = 14;
export const PINGS_LIMIT_PER_PARENT = 500;

async function readRecentPings(parentIds: string[], now: Date): Promise<Ping[]> {
  const since = new Date(
    now.getTime() - PINGS_WINDOW_DAYS * 86_400_000,
  ).toISOString();
  const perParent = await Promise.all(
    parentIds.map(async (parentId) => {
      const { data, error } = await supabase
        .from("pings")
        .select(READ_SURFACE.pings)
        .eq("parent_id", parentId)
        .gte("ts_utc", since)
        .order("ts_utc", { ascending: false })
        .limit(PINGS_LIMIT_PER_PARENT);
      if (error) throw error;
      return (data ?? []) as Ping[];
    }),
  );
  return perParent.flat();
}

export interface FamilySnapshot {
  family: Family | null;
  parents: Parent[];
  members: Member[];
  signals: ParentSignal[];
  pings: Ping[];
  setupLinks: SetupLink[];
}

/**
 * Request a magic link, and make failures visible (DECISIONS 115).
 *
 * supabase-js returns errors rather than throwing them. The founder's lost hour
 * was exactly this line swallowing a 429: the screen said "check your email"
 * over a link the rate-limited mailer had refused to send. Throwing is what
 * lets the Login screen put the failure into words.
 */
export async function sendMagicLink(email: string): Promise<void> {
  const { error } = await supabase.auth.signInWithOtp({ email });
  if (error) throw error;
}

export async function claimMembership(): Promise<void> {
  const { error } = await supabase.rpc("app_claim_membership");
  if (error) throw error;
}

export async function loadSnapshot(now: Date = new Date()): Promise<FamilySnapshot> {
  const [families, parents, members, signals, setupLinks] = await Promise.all([
    readAll<Family>("families"),
    readAll<Parent>("parents"),
    readAll<Member>("members"),
    readAll<ParentSignal>("parent_signals"),
    readAll<SetupLink>("setup_links"),
  ]);
  // Pings wait for the parent list: the bounded read is per parent.
  const pings = await readRecentPings(
    parents.map((parent) => parent.id),
    now,
  );
  return {
    family: families[0] ?? null,
    parents,
    members,
    signals,
    pings,
    setupLinks,
  };
}
