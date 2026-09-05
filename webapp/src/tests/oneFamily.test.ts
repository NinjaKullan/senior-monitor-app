/**
 * @vitest-environment jsdom
 *
 * DECISIONS 263 — one family per snapshot, held shut.
 *
 * An account can belong to more than one family (0008 links every matching
 * membership), and the founder's does. The snapshot used to pick
 * `families[0]` and then read parents, members, signals, links, notes and
 * contacts across EVERY family RLS let it see, so the Family screen showed
 * four parents and the same person twice in the circle. Every read is now
 * scoped to the chosen family — by family_id where the table has one, by the
 * chosen family's parent ids where it does not — and this file plants two
 * families in one account and checks nothing from the other one leaks.
 *
 * The fake client is the same PostgREST stand-in dataPings uses, with `in`
 * for the parent-keyed tables; it is redeclared here rather than shared so
 * that each file's vi.mock stays hoistable and self-contained.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

interface Executed {
  table: string;
  eq: Record<string, unknown>;
  in: Record<string, unknown[]>;
  order: { column: string; ascending: boolean } | null;
}

const tables: Record<string, Record<string, unknown>[]> = {};
const executed: Executed[] = [];

class FakeQuery {
  private call: Executed;
  private since: Record<string, string> = {};
  private cap: number | null = null;

  constructor(table: string) {
    this.call = { table, eq: {}, in: {}, order: null };
  }
  select() {
    return this;
  }
  eq(column: string, value: unknown) {
    this.call.eq[column] = value;
    return this;
  }
  in(column: string, values: unknown[]) {
    this.call.in[column] = values;
    return this;
  }
  gte(column: string, value: string) {
    this.since[column] = value;
    return this;
  }
  order(column: string, options: { ascending: boolean }) {
    this.call.order = { column, ascending: options.ascending };
    return this;
  }
  limit(count: number) {
    this.cap = count;
    return this;
  }
  then(resolve: (value: { data: Record<string, unknown>[]; error: null }) => void) {
    executed.push(this.call);
    let rows = [...(tables[this.call.table] ?? [])];
    for (const [column, value] of Object.entries(this.call.eq)) {
      rows = rows.filter((row) => row[column] === value);
    }
    for (const [column, values] of Object.entries(this.call.in)) {
      rows = rows.filter((row) => values.includes(row[column]));
    }
    for (const [column, value] of Object.entries(this.since)) {
      rows = rows.filter((row) => String(row[column]) >= value);
    }
    if (this.call.order) {
      const { column, ascending } = this.call.order;
      rows.sort((a, b) =>
        ascending
          ? String(a[column]).localeCompare(String(b[column]))
          : String(b[column]).localeCompare(String(a[column])),
      );
    }
    if (this.cap !== null) rows = rows.slice(0, this.cap);
    resolve({ data: rows, error: null });
  }
}

vi.mock("@/lib/supabase", () => ({
  isConfigured: true,
  supabase: { from: (table: string) => new FakeQuery(table) },
}));

import { loadSnapshot } from "@/lib/data";

const NOW = new Date("2026-09-04T12:00:00Z");
const recent = NOW.toISOString();

/** Two families the same account can see, the way the founder's looks:
 *  the older one is the one the app should show; the newer one, stored
 *  first so an unordered read would return it first, must not leak. */
function seedTwoFamilies() {
  tables.families = [
    { id: "newer", name: "Rehearsal", tz: "America/Chicago", created_utc: "2026-08-30T00:00:00Z" },
    { id: "older", name: "Suryaprakasam", tz: "Asia/Kolkata", created_utc: "2026-08-10T00:00:00Z" },
  ];
  const parent = (id: string, family_id: string) => ({
    id,
    family_id,
    display_name: id,
    tz: null,
    phone_e164: null,
    whatsapp_e164: null,
    relationship: null,
    city_label: null,
    tz_changed_utc: null, paused_until: null, paused_since: null,
  });
  tables.parents = [
    parent("amma", "older"),
    parent("appa", "older"),
    parent("testmom", "newer"),
    parent("testdad", "newer"),
  ];
  tables.members = [
    { id: "m1", family_id: "older", display_name: "Hema", role: "admin", digest_channel: "email", auth_user_id: "u1", mail: true },
    { id: "m2", family_id: "newer", display_name: "Hema", role: "admin", digest_channel: "email", auth_user_id: "u1", mail: true },
  ];
  tables.parent_signals = [
    { parent_id: "amma", signal: "whatsapp", alarm_grade: true, active: true },
    { parent_id: "testmom", signal: "whatsapp", alarm_grade: true, active: true },
  ];
  tables.setup_links = [
    { parent_id: "amma", slug: "s-amma", created_utc: recent, expires_utc: null, revoked_utc: null },
    { parent_id: "testmom", slug: "s-testmom", created_utc: recent, expires_utc: null, revoked_utc: null },
  ];
  tables.pings = [
    { parent_id: "amma", signal: "whatsapp", ts_utc: recent },
    { parent_id: "testmom", signal: "whatsapp", ts_utc: recent },
  ];
  tables.journal_entries = [
    { id: 1, family_id: "older", parent_id: null, author_label: "Hema", body: "ours", event_date: null, created_utc: recent, kind: "note" },
    { id: 2, family_id: "newer", parent_id: "testmom", author_label: "Hema", body: "theirs", event_date: null, created_utc: recent, kind: "note" },
    { id: 3, family_id: "older", parent_id: "amma", author_label: "Hema", body: "about amma", event_date: null, created_utc: recent, kind: "note" },
  ];
  tables.family_contacts = [
    { id: 1, family_id: "older", parent_id: null, label: "Neighbor", name: "R", phone_e164: "+911", phone_display: "1", note: "", position: 0 },
    { id: 2, family_id: "newer", parent_id: null, label: "Neighbor", name: "T", phone_e164: "+12", phone_display: "2", note: "", position: 0 },
  ];
}

beforeEach(() => {
  for (const key of Object.keys(tables)) delete tables[key];
  executed.length = 0;
});

describe("one family per snapshot (DECISIONS 263)", () => {
  it("chooses the oldest family the account belongs to, whatever order the rows arrive in", async () => {
    seedTwoFamilies();
    const snapshot = await loadSnapshot(NOW);
    expect(snapshot.family?.id).toBe("older");
    const familiesRead = executed.filter((call) => call.table === "families");
    expect(familiesRead).toHaveLength(1);
    expect(familiesRead[0].order).toEqual({ column: "created_utc", ascending: true });
  });

  it("nothing from the other family reaches the snapshot", async () => {
    seedTwoFamilies();
    const snapshot = await loadSnapshot(NOW);
    expect(snapshot.parents.map((p) => p.id).sort()).toEqual(["amma", "appa"]);
    expect(snapshot.members.map((m) => m.id)).toEqual(["m1"]);
    expect(snapshot.signals.map((s) => s.parent_id)).toEqual(["amma"]);
    expect(snapshot.setupLinks.map((l) => l.parent_id)).toEqual(["amma"]);
    expect(snapshot.pings.map((p) => p.parent_id)).toEqual(["amma"]);
    expect(snapshot.latestPings.map((p) => p.parent_id)).toEqual(["amma"]);
    expect(snapshot.journal.map((j) => j.body).sort()).toEqual(["about amma", "ours"]);
    expect(Object.keys(snapshot.journalByParent).sort()).toEqual(["amma", "appa"]);
    expect(snapshot.contacts.map((c) => c.id)).toEqual([1]);
  });

  it("every read after the family is scoped to it, pinned at the query", async () => {
    // The pin the bug demands: a table that reads without a family_id (or,
    // for the parent-keyed tables, without the chosen family's parent ids)
    // is back to merging households, even if today's fixture happens not to
    // show it.
    seedTwoFamilies();
    await loadSnapshot(NOW);
    for (const call of executed) {
      if (call.table === "families") continue;
      const byFamily = call.eq.family_id === "older";
      const byParent =
        "parent_id" in call.eq
          ? ["amma", "appa"].includes(call.eq.parent_id as string)
          : "parent_id" in call.in &&
            (call.in.parent_id as string[]).every((id) => ["amma", "appa"].includes(id));
      expect(byFamily || byParent, `${call.table} read is not scoped to the chosen family`).toBe(true);
    }
  });

  it("a preferred circle is chosen when the account belongs to it, else the oldest (spec 015)", async () => {
    seedTwoFamilies();
    const chosen = await loadSnapshot(NOW, "newer");
    expect(chosen.family?.id).toBe("newer");
    expect(chosen.parents.map((p) => p.id).sort()).toEqual(["testdad", "testmom"]);
    expect(chosen.families.map((f) => f.id)).toEqual(["older", "newer"]);
    const fallen = await loadSnapshot(NOW, "left-this-one");
    expect(fallen.family?.id).toBe("older");
  });

  it("no family means an empty snapshot and no further reads", async () => {
    seedTwoFamilies();
    tables.families = [];
    const snapshot = await loadSnapshot(NOW);
    expect(snapshot.family).toBeNull();
    expect(snapshot.parents).toEqual([]);
    expect(executed.map((call) => call.table)).toEqual(["families"]);
  });
});
