/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146).
 *
 * DECISIONS 160 — the silent-truncation bug, held shut. PostgREST caps an
 * unlimited select at 1000 rows without an error, and prod pings crossed that
 * cliff: the Today card computed "latest" from an arbitrary 1000-row subset
 * and showed a stale time over a parent who was actively pinging.
 *
 * The fake client here emulates the part of PostgREST that caused the bug —
 * filters and order and limit are honoured, and then the response is capped
 * at 1000 rows whatever the query asked for. Rows are stored oldest-first,
 * the way a table fills, so an unordered uncapped read loses exactly the
 * newest rows — which is what makes the regression test fail against the old
 * `readAll("pings")` and pass only against the bounded, ordered read.
 *
 * DECISIONS 166 joins it here: the unwindowed latest-row read per
 * (parent, signal) that keeps tripwire ages and the Setup card's
 * has-ever-pinged check honest past the 14-day window, inside the same
 * explicit-order-and-limit discipline.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

const SERVER_CAP = 1000;

interface Executed {
  table: string;
  columns: string;
  eq: Record<string, unknown>;
  gte: Record<string, string>;
  order: { column: string; ascending: boolean } | null;
  limit: number | null;
}

const tables: Record<string, Record<string, unknown>[]> = {};
const executed: Executed[] = [];

class FakeQuery {
  private call: Executed;

  constructor(private table: string) {
    this.call = { table, columns: "", eq: {}, gte: {}, order: null, limit: null };
  }

  select(columns: string) {
    this.call.columns = columns;
    return this;
  }

  eq(column: string, value: unknown) {
    this.call.eq[column] = value;
    return this;
  }

  gte(column: string, value: string) {
    this.call.gte[column] = value;
    return this;
  }

  order(column: string, options: { ascending: boolean }) {
    this.call.order = { column, ascending: options.ascending };
    return this;
  }

  limit(count: number) {
    this.call.limit = count;
    return this;
  }

  /** Thenable, like the real builder: awaiting it runs the query. */
  then(
    resolve: (value: { data: Record<string, unknown>[]; error: null }) => void,
  ) {
    executed.push(this.call);
    let rows = [...(tables[this.table] ?? [])];
    for (const [column, value] of Object.entries(this.call.eq)) {
      rows = rows.filter((row) => row[column] === value);
    }
    for (const [column, value] of Object.entries(this.call.gte)) {
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
    if (this.call.limit !== null) rows = rows.slice(0, this.call.limit);
    // The bug: the server answers 200 with the first 1000 rows, silently.
    rows = rows.slice(0, SERVER_CAP);
    resolve({ data: rows, error: null });
  }
}

vi.mock("@/lib/supabase", () => ({
  isConfigured: true,
  supabase: { from: (table: string) => new FakeQuery(table) },
}));

import {
  PINGS_LIMIT_PER_PARENT,
  PINGS_WINDOW_DAYS,
  loadSnapshot,
} from "@/lib/data";

const NOW = new Date("2026-08-23T12:00:00Z");

const iso = (msBeforeNow: number) => new Date(NOW.getTime() - msBeforeNow).toISOString();
const HOUR = 3_600_000;
const DAY = 24 * HOUR;

function seedFamily(parentIds: string[]) {
  tables.families = [{ id: "f1", name: "Sharma", tz: "Asia/Kolkata" }];
  tables.parents = parentIds.map((id) => ({
    id,
    family_id: "f1",
    display_name: id,
    tz: null,
  }));
  tables.members = [];
  tables.parent_signals = [];
  tables.setup_links = [];
  tables.pings = [];
}

beforeEach(() => {
  for (const key of Object.keys(tables)) delete tables[key];
  executed.length = 0;
});

describe("the bounded pings read", () => {
  it("the newest ping wins past the server's 1000-row cap", async () => {
    seedFamily(["p1"]);
    // Oldest-first, the way a table fills: 1050 pings over the last two days,
    // the newest one last. An unordered uncapped read returns the first 1000
    // and loses it.
    for (let i = 0; i < 1050; i++) {
      tables.pings.push({
        parent_id: "p1",
        signal: "whatsapp",
        ts_utc: iso(2 * DAY - i * 60_000),
      });
    }
    const newest = iso(HOUR);
    tables.pings.push({ parent_id: "p1", signal: "whatsapp", ts_utc: newest });

    const snapshot = await loadSnapshot(NOW);
    const latest = snapshot.pings
      .map((p) => p.ts_utc)
      .sort()
      .at(-1);
    expect(latest).toBe(newest);
  });

  it("orders descending with an explicit limit and a recent window, pinned", async () => {
    // The pin the bug demands: a future refactor that drops the order, the
    // limit or the window reverts to trusting the server's silent cap.
    seedFamily(["p1", "p2"]);
    tables.pings.push({ parent_id: "p1", signal: "whatsapp", ts_utc: iso(HOUR) });

    await loadSnapshot(NOW);
    // Two shapes of pings read since DECISIONS 166: the windowed per-parent
    // one (gte + limit 500) and the latest-row per-(parent, signal) one
    // (limit 1, no window). Nothing else may read pings.
    const pingReads = executed.filter((call) => call.table === "pings");
    const windowed = pingReads.filter((call) => "ts_utc" in call.gte);
    const latest = pingReads.filter((call) => !("ts_utc" in call.gte));
    expect(windowed.length).toBe(2); // one bounded read per parent
    for (const read of windowed) {
      expect(read.order).toEqual({ column: "ts_utc", ascending: false });
      expect(read.limit).toBe(PINGS_LIMIT_PER_PARENT);
      expect("parent_id" in read.eq).toBe(true);
    }
    for (const read of latest) {
      expect(read.order).toEqual({ column: "ts_utc", ascending: false });
      expect(read.limit).toBe(1);
      expect("parent_id" in read.eq && "signal" in read.eq).toBe(true);
    }
    // And the limit itself stays under the cliff it exists to avoid.
    expect(PINGS_LIMIT_PER_PARENT).toBeLessThanOrEqual(SERVER_CAP);
  });

  it("partitions the limit per parent, so a prolific phone cannot crowd one out", async () => {
    seedFamily(["busy", "quiet"]);
    for (let i = 0; i < 1200; i++) {
      tables.pings.push({
        parent_id: "busy",
        signal: "whatsapp",
        ts_utc: iso(DAY - i * 30_000),
      });
    }
    const quietNewest = iso(3 * DAY);
    tables.pings.push({ parent_id: "quiet", signal: "whatsapp", ts_utc: quietNewest });

    const snapshot = await loadSnapshot(NOW);
    const quietPings = snapshot.pings.filter((p) => p.parent_id === "quiet");
    expect(quietPings.map((p) => p.ts_utc)).toEqual([quietNewest]);
  });

  it("reads only the recent window", async () => {
    seedFamily(["p1"]);
    const inside = iso((PINGS_WINDOW_DAYS - 1) * DAY);
    const outside = iso((PINGS_WINDOW_DAYS + 1) * DAY);
    tables.pings.push({ parent_id: "p1", signal: "whatsapp", ts_utc: inside });
    tables.pings.push({ parent_id: "p1", signal: "whatsapp", ts_utc: outside });

    const snapshot = await loadSnapshot(NOW);
    expect(snapshot.pings.map((p) => p.ts_utc)).toEqual([inside]);
  });

  it("no other read grows past the cap, by construction or by bound", async () => {
    // The audit, as an assertion: every table the snapshot reads either has a
    // written cannot-grow reason in data.ts (families, parents, members,
    // parent_signals, setup_links) or is the bounded pings read. A new table
    // appearing here means the audit has to happen again.
    seedFamily(["p1"]);
    await loadSnapshot(NOW);
    const unbounded = executed.filter((call) => call.limit === null);
    expect(new Set(unbounded.map((call) => call.table))).toEqual(
      new Set(["families", "parents", "members", "parent_signals", "setup_links"]),
    );
  });
});

describe("the unwindowed latest-row reads (DECISIONS 166)", () => {
  const twentyDaysAgo = () => iso(20 * DAY);

  function seedOldSignal() {
    seedFamily(["p1"]);
    tables.parent_signals = [
      { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
    ];
    tables.pings.push({
      parent_id: "p1",
      signal: "whatsapp",
      ts_utc: twentyDaysAgo(),
    });
  }

  it("a 20-day-old last ping shows its true age, never 'never reported'", async () => {
    seedOldSignal();
    const snapshot = await loadSnapshot(NOW);

    // The windowed set is honestly empty; the latest set reaches past it.
    expect(snapshot.pings).toEqual([]);
    expect(snapshot.latestPings.map((p) => p.ts_utc)).toEqual([twentyDaysAgo()]);

    // Through the real surface: the tripwire carries an age, not "never".
    const { computeTripwires } = await import("@/lib/tripwires");
    const view = computeTripwires(
      { id: "p1", family_id: "f1", display_name: "Amma", tz: null },
      "Asia/Kolkata",
      snapshot.signals,
      snapshot.latestPings,
      NOW,
    );
    const [row] = view.rows;
    expect(row.health).toBe("stale");
    expect(row.recency).not.toBeNull();
  });

  it("a parent whose pings all aged out still counts as heard on the Setup card", async () => {
    seedOldSignal();
    const snapshot = await loadSnapshot(NOW);

    const { buildSetupEntries } = await import("@/lib/setupLinks");
    const [entry] = buildSetupEntries(
      [{ id: "p1", family_id: "f1", display_name: "Amma", tz: null }],
      [],
      snapshot.latestPings,
      NOW,
    );
    expect(entry.status).toBe("reporting");
  });

  it("reads one latest row per (parent, signal), each with limit 1 and no window", async () => {
    seedFamily(["p1", "p2"]);
    tables.parent_signals = [
      { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
      { parent_id: "p1", signal: "charge_on", alarm_grade: false, active: false },
      { parent_id: "p2", signal: "routine", alarm_grade: true, active: true },
    ];
    await loadSnapshot(NOW);
    const latest = executed.filter(
      (call) => call.table === "pings" && !("ts_utc" in call.gte),
    );
    expect(
      latest.map((call) => [call.eq.parent_id, call.eq.signal]).sort(),
    ).toEqual([
      ["p1", "charge_on"],
      ["p1", "whatsapp"],
      ["p2", "routine"],
    ]);
    for (const call of latest) {
      expect(call.limit).toBe(1);
      expect(call.order).toEqual({ column: "ts_utc", ascending: false });
      expect(call.gte).toEqual({});
    }
  });

  it("App feeds the two surfaces from latestPings and the glance from the window", async () => {
    // Both sets are Ping[], so a swap back to the windowed set would compile
    // cleanly and quietly reintroduce the false sentences. Pinned at the
    // source, the way the product side pins queries.ts.
    const fs = await import("node:fs");
    // vitest runs with cwd = webapp/; jsdom rewrites import.meta.url, so the
    // plain relative path is the reliable one.
    const source = fs.readFileSync("src/App.tsx", "utf8");
    const callOf = (name: string) => {
      const start = source.indexOf(`${name}(`);
      expect(start).toBeGreaterThan(-1);
      return source.slice(start, source.indexOf(")}", start));
    };
    expect(callOf("computeTripwires")).toContain("snapshot.latestPings");
    expect(callOf("computeTripwires")).not.toContain("snapshot.pings,");
    expect(callOf("buildSetupEntries")).toContain("snapshot.latestPings");
    expect(callOf("buildSetupEntries")).not.toContain("snapshot.pings,");
    expect(callOf("computeGlance")).toContain("snapshot.pings");
    expect(callOf("computeGlance")).not.toContain("latestPings");
  });
});
