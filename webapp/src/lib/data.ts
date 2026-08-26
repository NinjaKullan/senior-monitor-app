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
  JournalEntry,
  Member,
  Parent,
  ParentSignal,
  Ping,
  SetupLink,
} from "./types";

/** What the latest-ping reads need from a signal row to key one query. */
type SignalKey = Pick<ParentSignal, "parent_id" | "signal">;

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

/**
 * The unwindowed latest ping per (parent, signal) — DECISIONS 166, repairing
 * 160's flagged consequence. The 14-day window is right for the Today card
 * and the day arc, but it put a floor under two has-this-ever-happened
 * surfaces: a tripwire whose last ping predates the window rendered "never
 * reported" instead of its true age, and the Setup card's first-ping-heard
 * check reverted once a parent's pings aged out. Both were false sentences.
 *
 * One row per (parent, signal) from the parent's own allowlist — inactive
 * entries included, because history counts for "has ever pinged" — ordered
 * ts_utc descending with limit 1 and deliberately NO time window: the whole
 * point is reaching past it. Bounded by construction: parents × the fixed
 * signal vocabulary, never by table growth, which is what keeps it inside
 * this file's explicit-order-and-limit discipline.
 */
async function readLatestPings(keys: SignalKey[]): Promise<Ping[]> {
  const perSignal = await Promise.all(
    keys.map(async ({ parent_id, signal }) => {
      const { data, error } = await supabase
        .from("pings")
        .select(READ_SURFACE.pings)
        .eq("parent_id", parent_id)
        .eq("signal", signal)
        .order("ts_utc", { ascending: false })
        .limit(1);
      if (error) throw error;
      return (data ?? []) as Ping[];
    }),
  );
  return perSignal.flat();
}

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

/**
 * The bounded journal reads (spec 009 §4, under the DECISIONS 160 rule): the
 * table grows without bound, so every scope is its own newest-first read with
 * an explicit limit — one for the Family screen's consolidated list, one per
 * parent for the detail panel. Ordering matters like it does for pings: with
 * created_utc descending, truncation drops the OLDEST notes, never the one
 * the family just wrote.
 */
export const JOURNAL_LIMIT_PER_SCOPE = 50;

async function readJournalFamily(): Promise<JournalEntry[]> {
  const { data, error } = await supabase
    .from("journal_entries")
    .select(READ_SURFACE.journal_entries)
    .order("created_utc", { ascending: false })
    .limit(JOURNAL_LIMIT_PER_SCOPE);
  if (error) throw error;
  return (data ?? []) as JournalEntry[];
}

async function readJournalByParent(
  parentIds: string[],
): Promise<Record<string, JournalEntry[]>> {
  const perParent = await Promise.all(
    parentIds.map(async (parentId) => {
      const { data, error } = await supabase
        .from("journal_entries")
        .select(READ_SURFACE.journal_entries)
        .eq("parent_id", parentId)
        .order("created_utc", { ascending: false })
        .limit(JOURNAL_LIMIT_PER_SCOPE);
      if (error) throw error;
      return [parentId, (data ?? []) as JournalEntry[]] as const;
    }),
  );
  return Object.fromEntries(perParent);
}

/** The app's first own write path (spec 009 §4): one insert, RLS-scoped to
 *  the caller's family server-side; v1 has no edit and no delete. */
export async function addJournalEntry(entry: {
  family_id: string;
  parent_id: string | null;
  author_label: string;
  body: string;
  event_date: string | null;
}): Promise<void> {
  const { error } = await supabase.from("journal_entries").insert(entry);
  if (error) throw error;
}

/** The display-only city label (spec 009 §5). The grant is column-scoped
 *  server-side: nothing else on parents is writable from here. */
export async function saveCityLabel(parentId: string, cityLabel: string | null): Promise<void> {
  const { error } = await supabase
    .from("parents")
    .update({ city_label: cityLabel })
    .eq("id", parentId);
  if (error) throw error;
}

export interface FamilySnapshot {
  family: Family | null;
  parents: Parent[];
  members: Member[];
  signals: ParentSignal[];
  /** The bounded 14-day window (DECISIONS 160): the Today card and day arc. */
  pings: Ping[];
  /** One unwindowed latest row per (parent, signal) (DECISIONS 166): tripwire
   * ages and the Setup card's has-ever-pinged check, and nothing else. */
  latestPings: Ping[];
  setupLinks: SetupLink[];
  /** The Family screen's consolidated notes: newest 50, family-wide. */
  journal: JournalEntry[];
  /** The detail panels' notes: newest 50 per parent, keyed by parent id. */
  journalByParent: Record<string, JournalEntry[]>;
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
  // The bounded reads wait for the earlier rows: pings per parent and per
  // (parent, signal), journal per family and per parent — every one ordered
  // and limited.
  const [pings, latestPings, journal, journalByParent] = await Promise.all([
    readRecentPings(
      parents.map((parent) => parent.id),
      now,
    ),
    readLatestPings(
      signals.map(({ parent_id, signal }) => ({ parent_id, signal })),
    ),
    readJournalFamily(),
    readJournalByParent(parents.map((parent) => parent.id)),
  ]);
  return {
    family: families[0] ?? null,
    parents,
    members,
    signals,
    pings,
    latestPings,
    setupLinks,
    journal,
    journalByParent,
  };
}
