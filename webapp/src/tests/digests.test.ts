/** AC3 — the digest list, recomposed from the templates that sent it. */
import { describe, expect, it } from "vitest";
import { buildDigestEntries } from "@/lib/digests";
import type { DigestSend, Parent, ParentSignal, Ping } from "@/lib/types";

const IST = "Asia/Kolkata";
const amma: Parent = { id: "p1", family_id: "f1", display_name: "Amma", tz: null };
const appa: Parent = { id: "p2", family_id: "f1", display_name: "Appa", tz: null };

const signals: ParentSignal[] = [
  { parent_id: "p1", signal: "whatsapp", alarm_grade: true, active: true },
  { parent_id: "p2", signal: "whatsapp", alarm_grade: true, active: true },
];

const pings: Ping[] = [
  { parent_id: "p1", signal: "whatsapp", ts_utc: "2026-08-03T02:42:00Z" }, // 08:12 IST
  { parent_id: "p2", signal: "whatsapp", ts_utc: "2026-08-03T03:10:00Z" },
];

describe("buildDigestEntries", () => {
  it("renders the morning template with the recomputed first-ping time", () => {
    const sends: DigestSend[] = [
      { parent_id: "p1", kind: "morning", local_date: "2026-08-03", ts_utc: "2026-08-03T03:30:00Z" },
    ];
    const [entry] = buildDigestEntries(sends, [amma], IST, signals, pings);
    expect(entry.message).toBe(
      "Good morning — Amma's day started normally (8:12 am local time).",
    );
  });

  it("rebuilds an aggregated evening from its per-parent rows", () => {
    const sends: DigestSend[] = [
      { parent_id: "p1", kind: "evening", local_date: "2026-08-03", ts_utc: "2026-08-03T15:00:00Z" },
      { parent_id: "p2", kind: "evening", local_date: "2026-08-03", ts_utc: "2026-08-03T15:00:00Z" },
    ];
    const entries = buildDigestEntries(sends, [amma, appa], IST, signals, pings);
    expect(entries).toHaveLength(1);
    expect(entries[0].message).toBe("Amma and Appa both had normal, active days.");
  });

  it("renders a single-parent evening", () => {
    const sends: DigestSend[] = [
      { parent_id: "p1", kind: "evening", local_date: "2026-08-03", ts_utc: "2026-08-03T15:00:00Z" },
    ];
    const [entry] = buildDigestEntries(sends, [amma, appa], IST, signals, pings);
    expect(entry.message).toBe("Amma had a normal, active day.");
  });

  it("sorts newest first", () => {
    const sends: DigestSend[] = [
      { parent_id: "p1", kind: "evening", local_date: "2026-08-01", ts_utc: "2026-08-01T15:00:00Z" },
      { parent_id: "p1", kind: "evening", local_date: "2026-08-03", ts_utc: "2026-08-03T15:00:00Z" },
    ];
    const entries = buildDigestEntries(sends, [amma], IST, signals, pings);
    expect(entries.map((e) => e.localDate)).toEqual(["2026-08-03", "2026-08-01"]);
  });

  it("returns nothing when nothing was sent", () => {
    expect(buildDigestEntries([], [amma], IST, signals, pings)).toEqual([]);
  });
});
