/**
 * Every read the app performs, in one file.
 *
 * RLS decides what an account MAY see; this file decides what the app SHOWS,
 * and since DECISIONS 263 those are different questions. An account can
 * belong to more than one family (0008 links every matching membership, and
 * the founder's account owns two), and a snapshot that read every visible row
 * merged them into one household — four parents on Today, the same person
 * twice in the circle. So the snapshot now chooses ONE family and scopes
 * every other read to it: by family_id where the table carries one, by that
 * family's parent ids where it does not. These filters are shape filters,
 * not isolation filters — RLS still decides what comes back, and the family
 * chosen is always one the account is entitled to. A family switcher belongs
 * to a later spec (264); until then the choice is the oldest family the
 * account belongs to, so the same account always lands on the same one.
 *
 * **No unbounded read of a growing table** (DECISIONS 160). PostgREST caps an
 * unlimited select at 1000 rows and says nothing — the read "works", the data
 * is simply incomplete — and prod pings crossed that cliff and showed a stale
 * "Last routine seen" over a parent who was actively pinging. The unbounded
 * reads (the family itself, then readAllInFamily and readParentRows) are
 * therefore only for tables that cannot plausibly reach 1000 rows per family
 * under RLS, each with its reason:
 *
 *   families       — the handful an account belongs to (263); one is chosen.
 *   parents        — a handful of people.
 *   members        — a handful of people.
 *   parent_signals — parents × the fixed signal vocabulary (≤ ~8 each).
 *   setup_links    — one row per manual founder issuance; rotations accumulate
 *                    but at human pace, decades from four figures.
 *
 * `pings` is the one table that grows without bound, and it gets its own
 * bounded read below. A new table joins the unbounded reads only with a
 * written reason it cannot grow, or it gets the bounded treatment.
 */

import { supabase } from "./supabase";
import { READ_SURFACE } from "./queries";
import type {
  Family,
  FamilyContact,
  JournalEntry,
  Member,
  Parent,
  ParentSignal,
  Ping,
  SetupLink,
} from "./types";

/** What the latest-ping reads need from a signal row to key one query. */
type SignalKey = Pick<ParentSignal, "parent_id" | "signal">;

/**
 * Every circle the account belongs to, oldest first (DECISIONS 263, spec
 * 015 §8). A handful at most. The snapshot is about ONE of them: the one the
 * caller asks for when it is in the list, else the oldest — so the pick is
 * deterministic rather than whatever order PostgREST happened to answer in,
 * and a remembered choice that no longer applies (a circle left) falls back
 * rather than failing.
 */
async function readFamilies(): Promise<Family[]> {
  const { data, error } = await supabase
    .from("families")
    .select(READ_SURFACE.families)
    .order("created_utc", { ascending: true });
  if (error) throw error;
  return (data ?? []) as Family[];
}

/** Pure, so the fallback is testable without a client. */
export function chooseFamily(families: Family[], preferredId: string | null): Family | null {
  return families.find((family) => family.id === preferredId) ?? families[0] ?? null;
}

/** A small table keyed by parent rather than family, scoped by the chosen
 *  family's parent ids. An empty id list reads nothing rather than everything:
 *  PostgREST's `in.()` matches no row, which is the right answer for a family
 *  with no parents yet. */
async function readParentRows<T>(
  table: "parent_signals" | "setup_links",
  parentIds: string[],
): Promise<T[]> {
  const { data, error } = await supabase
    .from(table)
    .select(READ_SURFACE[table])
    .in("parent_id", parentIds);
  if (error) throw error;
  return (data ?? []) as T[];
}

/** A small table that carries family_id, read whole within the chosen family. */
async function readAllInFamily<T>(
  table: "parents" | "members",
  familyId: string,
): Promise<T[]> {
  const { data, error } = await supabase
    .from(table)
    .select(READ_SURFACE[table])
    .eq("family_id", familyId);
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
 * parents the snapshot already holds; RLS still decides what is visible.
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

async function readJournalFamily(familyId: string): Promise<JournalEntry[]> {
  const { data, error } = await supabase
    .from("journal_entries")
    .select(READ_SURFACE.journal_entries)
    .eq("family_id", familyId)
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
  /** Spec 012 §5: the webapp's own auto note names its kind (city_change);
   *  a plain family note omits this and the schema defaults it to 'note'. */
  kind?: string;
  /** Spec 016: set on a reply. The row's parent_id is then the NOTE's — the
   *  0026 trigger overwrites whatever travels here — so callers pass null. */
  parent_entry_id?: number;
}): Promise<void> {
  const { error } = await supabase.from("journal_entries").insert(entry);
  if (error) throw error;
}

/* --- the contacts sheet (spec 012 §4) ------------------------------------ */

async function readContacts(familyId: string): Promise<FamilyContact[]> {
  const { data, error } = await supabase
    .from("family_contacts")
    .select(READ_SURFACE.family_contacts)
    .eq("family_id", familyId)
    .order("position", { ascending: true })
    .order("id", { ascending: true })
    .limit(50);
  if (error) throw error;
  return (data ?? []) as FamilyContact[];
}

/** What a saved contact carries. E.164 stored beside the display string —
 *  the two travel together so neither is ever derived at render. */
export interface ContactDraft {
  label: string;
  name: string;
  phone_e164: string;
  phone_display: string;
  note: string;
  /** Spec 012 §9.3: null means the contact is for the whole household.
   *  Parents living separately carry different numbers, so a contact belongs
   *  to one of them or to everyone, and never to "the family" by default. */
  parent_id: string | null;
}

/** The typed number, made href-safe: keep a leading +, drop everything that
 *  is not a digit. What the person TYPED stays the display string verbatim —
 *  this never renders, it only dials. */
export function telHrefNumber(typed: string): string {
  const digits = typed.replace(/[^\d]/g, "");
  return typed.trim().startsWith("+") ? `+${digits}` : digits;
}

export async function addContact(
  familyId: string,
  draft: ContactDraft,
  position: number,
): Promise<void> {
  const { error } = await supabase
    .from("family_contacts")
    // parent_id now travels inside the draft (§9.3): the caller decides who a
    // contact is for, and the old hardcoded null is gone. `position` is the
    // rank the family put the rows in — 0021 already carries the column.
    .insert({ family_id: familyId, ...draft, position });
  if (error) throw error;
}

export async function updateContact(id: number, draft: ContactDraft): Promise<void> {
  const { error } = await supabase.from("family_contacts").update(draft).eq("id", id);
  if (error) throw error;
}

/** Reorder one contact (§9.3): the call-first / then / then order the family
 *  chose. Position is written on its own so a move never rewrites the fields
 *  a person typed, and RLS scopes the row the same way every other write is
 *  scoped — by policy, never by a family_id the client supplies. */
export async function moveContact(id: number, position: number): Promise<void> {
  const { error } = await supabase.from("family_contacts").update({ position }).eq("id", id);
  if (error) throw error;
}

export async function deleteContact(id: number): Promise<void> {
  const { error } = await supabase.from("family_contacts").delete().eq("id", id);
  if (error) throw error;
}

/** Clearing the field clears the label ONLY and never touches tz
 *  (spec 010 §1); also the spec-009 label write. Column-scoped grants
 *  server-side: nothing else on parents is writable from here. */
export async function saveCityLabel(parentId: string, cityLabel: string | null): Promise<void> {
  const { error } = await supabase
    .from("parents")
    .update({ city_label: cityLabel })
    .eq("id", parentId);
  if (error) throw error;
}

/**
 * The one write a pick performs (spec 010 §1): label and zone together, and
 * tz_changed_utc stamped when — and only when — the zone actually changed.
 * Pure, so the only-when-changed rule is testable without a client: the
 * "current" zone is the EFFECTIVE one (parent.tz, else the family's), so
 * picking a city in the zone a parent already inherits does not fabricate a
 * changeover window over a clock that never moved.
 */
export function placeUpdate(
  currentTz: string | null,
  familyTz: string,
  entry: { city: string; iana: string },
  nowIso: string,
): { city_label: string; tz: string; tz_changed_utc?: string } {
  const changed = entry.iana !== (currentTz ?? familyTz);
  return {
    city_label: entry.city,
    tz: entry.iana,
    ...(changed ? { tz_changed_utc: nowIso } : {}),
  };
}

/** Apply one pick. The zone is validated against the shipped list by the
 *  caller (cities.isKnownIana) before this is ever reached. */
export async function savePlace(
  parentId: string,
  update: { city_label: string; tz: string; tz_changed_utc?: string },
): Promise<void> {
  const { error } = await supabase.from("parents").update(update).eq("id", parentId);
  if (error) throw error;
}

export interface FamilySnapshot {
  /** Every circle the account belongs to, oldest first (spec 015 §8): the
   *  switcher's list. One is chosen and everything else is about it. */
  families: Family[];
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
  /** The family's contacts sheet (spec 012 §4): small, read whole. */
  contacts: FamilyContact[];
}

/* --- the circle (spec 015 §6) ------------------------------------------- */

/**
 * The five membership writes, each a SECURITY DEFINER function (0025) and
 * the ONLY write path to `members`. No family id travels that the caller
 * does not belong to — the functions check membership against the JWT, and
 * a refusal comes back as an error whose message is one of the short codes
 * `circleRefusal` below turns into words.
 */
export async function addSeat(familyId: string, displayName: string, email: string): Promise<void> {
  const { error } = await supabase.rpc("app_add_seat", {
    p_family_id: familyId,
    p_display_name: displayName,
    p_email: email,
  });
  if (error) throw error;
}

export async function removeSeat(memberId: string): Promise<void> {
  const { error } = await supabase.rpc("app_remove_seat", { p_member_id: memberId });
  if (error) throw error;
}

export async function setSeatRole(memberId: string, role: "admin" | "member"): Promise<void> {
  const { error } = await supabase.rpc("app_set_role", { p_member_id: memberId, p_role: role });
  if (error) throw error;
}

export async function setOwnMail(familyId: string, mail: boolean): Promise<void> {
  const { error } = await supabase.rpc("app_set_mail", { p_family_id: familyId, p_mail: mail });
  if (error) throw error;
}

export async function leaveCircle(familyId: string): Promise<void> {
  const { error } = await supabase.rpc("app_leave_circle", { p_family_id: familyId });
  if (error) throw error;
}

/* --- edit and delete (spec 018 §3) --------------------------------------- */

/** Two SECURITY DEFINER functions are the only paths after the insert (0028):
 *  the author edits their own text; the author or an admin deletes. */
export async function editEntry(entryId: number, body: string): Promise<void> {
  const { error } = await supabase.rpc("app_edit_entry", { p_entry_id: entryId, p_body: body });
  if (error) throw error;
}

export async function deleteEntry(entryId: number): Promise<void> {
  const { error } = await supabase.rpc("app_delete_entry", { p_entry_id: entryId });
  if (error) throw error;
}

/* --- the pause (spec 017 §3) --------------------------------------------- */

/** Admin only, checked server-side (0027). "week" is seven days from now;
 *  "open" stores 'infinity', which the read surface hands back as the
 *  string "infinity". */
export async function pauseParent(parentId: string, duration: "week" | "open", now: Date = new Date()): Promise<void> {
  const until =
    duration === "open" ? "infinity" : new Date(now.getTime() + 7 * 86_400_000).toISOString();
  const { error } = await supabase.rpc("app_pause_parent", { p_parent_id: parentId, p_until: until });
  if (error) throw error;
}

export async function resumeParent(parentId: string): Promise<void> {
  const { error } = await supabase.rpc("app_resume_parent", { p_parent_id: parentId });
  if (error) throw error;
}

/**
 * Request a magic link, and make failures visible (DECISIONS 115).
 *
 * supabase-js returns errors rather than throwing them. The founder's lost hour
 * was exactly this line swallowing a 429: the screen said "check your email"
 * over a link the rate-limited mailer had refused to send. Throwing is what
 * lets the Login screen put the failure into words.
 */
/**
 * Ask Supabase to email a sign-in code (spec 013 §2).
 *
 * The CALL is unchanged from the magic-link era — one `signInWithOtp` sends an
 * email carrying both a code and a link, and which one a person uses is their
 * choice, not a branch here. Only the name changed, because "magic link" stopped
 * describing what this is for once the code became the path a phone takes.
 *
 * It throws rather than returning the error, and that is the whole point
 * (DECISIONS 115): supabase-js hands failures back as VALUES, so the original
 * bug was a call site that discarded a 429 and told the family to check an
 * inbox nothing had been sent to.
 */
export async function sendSignInCode(email: string): Promise<void> {
  const { error } = await supabase.auth.signInWithOtp({ email });
  if (error) throw error;
}

/**
 * Exchange a typed 6-digit code for a session (spec 013 §2).
 *
 * `type: "email"` covers both templates a family can receive: the magic-link
 * mail for an address that has signed in before, and the confirm-signup mail a
 * first-time address gets. Success is not returned from here — the existing
 * `onAuthStateChange` observes it, exactly as it does when someone taps the
 * link on a laptop, so there is one place in the app that decides a person is
 * signed in.
 *
 * Throws for the same reason as above.
 */
export async function verifySignInCode(email: string, token: string): Promise<void> {
  const { error } = await supabase.auth.verifyOtp({ email, token, type: "email" });
  if (error) throw error;
}

export async function claimMembership(): Promise<void> {
  const { error } = await supabase.rpc("app_claim_membership");
  if (error) throw error;
}

export async function loadSnapshot(
  now: Date = new Date(),
  preferredFamilyId: string | null = null,
): Promise<FamilySnapshot> {
  // The families first, alone: everything below is scoped to the chosen one
  // (DECISIONS 263), so nothing else can be asked for until it is known. No
  // family means an empty snapshot — the NoFamily screen, not a merge of
  // nothing.
  const families = await readFamilies();
  const family = chooseFamily(families, preferredFamilyId);
  if (!family) {
    return {
      families,
      family: null,
      parents: [],
      members: [],
      signals: [],
      pings: [],
      latestPings: [],
      setupLinks: [],
      journal: [],
      journalByParent: {},
      contacts: [],
    };
  }
  const [parents, members] = await Promise.all([
    readAllInFamily<Parent>("parents", family.id),
    readAllInFamily<Member>("members", family.id),
  ]);
  const parentIds = parents.map((parent) => parent.id);
  // parent_signals and setup_links carry no family_id; the chosen family's
  // parent ids are their scope.
  const [signals, setupLinks] = await Promise.all([
    readParentRows<ParentSignal>("parent_signals", parentIds),
    readParentRows<SetupLink>("setup_links", parentIds),
  ]);
  // The bounded reads wait for the earlier rows: pings per parent and per
  // (parent, signal), journal per family and per parent — every one ordered
  // and limited.
  const [pings, latestPings, journal, journalByParent, contacts] = await Promise.all([
    readRecentPings(parentIds, now),
    readLatestPings(
      signals.map(({ parent_id, signal }) => ({ parent_id, signal })),
    ),
    readJournalFamily(family.id),
    readJournalByParent(parentIds),
    readContacts(family.id),
  ]);
  return {
    families,
    family,
    parents,
    members,
    signals,
    pings,
    latestPings,
    setupLinks,
    journal,
    journalByParent,
    contacts,
  };
}
