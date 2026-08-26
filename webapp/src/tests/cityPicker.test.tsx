/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * The city picker (spec 010 §1) — the ONE surface that moves a parent's clock.
 *
 * The properties that carry the weight: only a PICKED entry ever commits (free
 * text reverts on blur, Enter commits nothing), clearing clears the label and
 * nothing else, the IANA name never reaches the screen, and the pick's write
 * shape — label + zone together, the changeover stamp only when the zone
 * actually moved — is pure logic tested without a client.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CityPicker } from "@/components/CityPicker";
import { CITIES, displayOf, isKnownIana, searchCities } from "@/lib/cities";
import { placeUpdate } from "@/lib/data";
import { CITY_ESCAPE_HATCH, CITY_PLACEHOLDER } from "@/lib/copy";

/** Anywhere an IANA zone name would show, this shape gives it away. */
const IANA_SHAPE = /(Asia|America|Europe|Africa|Australia|Pacific|Atlantic|Indian)\//;

describe("the curated list", () => {
  it("is weighted to the pilot's geography and knows its own zones", () => {
    expect(CITIES.length).toBeGreaterThanOrEqual(300);
    const chennai = CITIES.find((e) => e.city === "Chennai")!;
    expect(chennai.iana).toBe("Asia/Kolkata");
    expect(isKnownIana("Asia/Kolkata")).toBe(true);
    expect(isKnownIana("Asia/Madeupistan")).toBe(false);
  });

  it("has no two entries wearing the same display", () => {
    const displays = CITIES.map(displayOf);
    expect(new Set(displays).size).toBe(displays.length);
  });

  it("searches by city prefix first, substring later, case-insensitively", () => {
    const results = searchCities("chen");
    expect(results[0].city).toBe("Chennai");
    expect(searchCities("CHEN")[0].city).toBe("Chennai");
    expect(searchCities("zzzz")).toEqual([]);
    expect(searchCities("a").length).toBeLessThanOrEqual(8);
  });
});

describe("the write a pick performs (placeUpdate)", () => {
  const NOW = "2026-08-21T15:00:00Z";
  const dallas = { city: "Dallas", iana: "America/Chicago" };

  it("writes label and zone together, stamping the change when the zone moved", () => {
    expect(placeUpdate("Asia/Kolkata", "Asia/Kolkata", dallas, NOW)).toEqual({
      city_label: "Dallas",
      tz: "America/Chicago",
      tz_changed_utc: NOW,
    });
  });

  it("never stamps a changeover for a zone that did not move", () => {
    expect(placeUpdate("America/Chicago", "Asia/Kolkata", dallas, NOW)).toEqual({
      city_label: "Dallas",
      tz: "America/Chicago",
    });
  });

  it("compares against the EFFECTIVE zone: a null tz inherits the family's", () => {
    // Picking a city in the very zone the parent already inherits must not
    // fabricate a changeover window over a clock that never moved.
    const chennai = { city: "Chennai", iana: "Asia/Kolkata" };
    expect(placeUpdate(null, "Asia/Kolkata", chennai, NOW)).toEqual({
      city_label: "Chennai",
      tz: "Asia/Kolkata",
    });
    expect(placeUpdate(null, "Asia/Kolkata", dallas, NOW)).toEqual({
      city_label: "Dallas",
      tz: "America/Chicago",
      tz_changed_utc: NOW,
    });
  });
});

describe("the picker component", () => {
  function mount(committed = "") {
    const onPick = vi.fn();
    const onClear = vi.fn();
    render(<CityPicker name="Amma" committed={committed} onPick={onPick} onClear={onClear} />);
    return { onPick, onClear, input: screen.getByTestId("city-input") as HTMLInputElement };
  }

  it("carries the pinned placeholder with the parent's name in it", () => {
    const { input } = mount();
    expect(CITY_PLACEHOLDER).toBe("Where {name} lives");
    expect(input.placeholder).toBe("Where Amma lives");
  });

  it("offers matches while typing and commits the FULL entry on a pick", () => {
    const { onPick, input } = mount();
    fireEvent.change(input, { target: { value: "dall" } });
    const option = screen
      .getAllByTestId("city-option")
      .find((n) => n.textContent === "Dallas, United States")!;
    fireEvent.mouseDown(option);
    fireEvent.click(option);
    expect(onPick).toHaveBeenCalledTimes(1);
    expect(onPick.mock.calls[0][0]).toEqual({
      city: "Dallas",
      country: "United States",
      iana: "America/Chicago",
    });
    expect(input.value).toBe("Dallas");
  });

  it("lets free text commit nothing: Enter is inert and blur reverts", () => {
    const { onPick, onClear, input } = mount("Chennai");
    fireEvent.change(input, { target: { value: "Atlantis" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onPick).not.toHaveBeenCalled();
    fireEvent.blur(input);
    expect(input.value).toBe("Chennai");
    expect(onPick).not.toHaveBeenCalled();
    expect(onClear).not.toHaveBeenCalled();
  });

  it("clearing a committed city clears the label only", () => {
    const { onPick, onClear, input } = mount("Chennai");
    fireEvent.change(input, { target: { value: "" } });
    fireEvent.blur(input);
    expect(onClear).toHaveBeenCalledTimes(1);
    expect(onPick).not.toHaveBeenCalled();
  });

  it("does not cry clear over a field that was already empty", () => {
    const { onClear, input } = mount("");
    fireEvent.focus(input);
    fireEvent.blur(input);
    expect(onClear).not.toHaveBeenCalled();
  });

  it("shows the escape hatch under the results, verbatim", () => {
    const { input } = mount();
    fireEvent.change(input, { target: { value: "xyzzy-no-such-place" } });
    expect(screen.getByTestId("city-escape").textContent).toBe(
      "Can't find it? Pick the nearest big city.",
    );
    expect(CITY_ESCAPE_HATCH).toBe("Can't find it? Pick the nearest big city.");
  });

  it("never renders an IANA zone name", () => {
    const { input } = mount();
    for (const query of ["chen", "dal", "new", "lon"]) {
      fireEvent.change(input, { target: { value: query } });
      expect(document.body.textContent).not.toMatch(IANA_SHAPE);
    }
  });
});

describe("App's pick wiring, pinned at the source", () => {
  it("validates the zone, writes through placeUpdate, and journals the move", async () => {
    // The same style of pin dataPings uses for the two ping sets: the wiring
    // is invisible to a component test (App owns the client), so the source
    // is the surface. What must hold: no pick bypasses the shipped-list
    // check, the write goes through placeUpdate (the only place the
    // changeover stamp rule lives), the journal notes the move in the
    // product's own hand (spec 010 §4, ruled BUILD), and a no-op pick
    // journals nothing.
    const fs = await import("node:fs");
    const source = fs.readFileSync("src/App.tsx", "utf8");
    const start = source.indexOf("const pickCity");
    expect(start).toBeGreaterThan(-1);
    const body = source.slice(start, source.indexOf("const clearCity", start));
    expect(body).toContain("isKnownIana(entry.iana)");
    expect(body).toContain("placeUpdate(parent.tz, familyTz, entry,");
    expect(body).toContain("AUTO_NOTE_AUTHOR");
    expect(body).toContain("CITY_CHANGED_NOTE");
    expect(body).toContain("if (!unchanged)");
    // Clearing goes through the label-only writer, never the place writer.
    const clear = source.slice(source.indexOf("const clearCity"), source.indexOf("const navigate"));
    expect(clear).toContain("saveCityLabel(parentId, null)");
    expect(clear).not.toContain("savePlace");
  });
});
