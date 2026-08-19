/**
 * The three-fields section, after QUESTIONS 135.
 *
 * Two independent reviewers of the live site reported the field's orbits
 * landing on the section's words, on phones and on desktops. The cause was
 * structural — the canvas was a backdrop spanning the whole section, so at some
 * width it was always going to be underneath a paragraph — and so is the fix:
 * the field has a reserved band of its own, a flow sibling below the text that
 * no text can enter.
 *
 * These tests pin the structure. The geometry inside the band is pinned in
 * rhythmField.test.ts, and the pixels are checked in a real browser by
 * scripts/probe-field.mjs, which jsdom cannot stand in for.
 */
import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "@/App";
import { ThreeFields } from "@/sections/ThreeFields";
import { FIELDS_BODY, FIELDS_CHIPS, FIELDS_EMPHASIS, FIELDS_H2 } from "@/copy";

const textNodes = (root: HTMLElement) =>
  Array.from(root.querySelectorAll("h1,h2,h3,p,li,a,button,label,span"));

describe("the field's reserved band", () => {
  it("puts the canvas in a band of its own, after all of the words", () => {
    const { container } = render(<ThreeFields />);
    const band = screen.getByTestId("field-band");
    const canvas = container.querySelector("canvas")!;

    expect(canvas.parentElement).toBe(band);
    // Nothing readable lives inside the band — not now, and the assertion is
    // what stops the next person putting a caption in there.
    expect(textNodes(band)).toEqual([]);
    expect(band.textContent).toBe("");

    // And the band comes last, so every word is above it in the flow rather
    // than layered over it.
    const column = band.parentElement!;
    expect(Array.from(column.children).at(-1)).toBe(band);
  });

  it("gives the band a height of its own rather than borrowing the section's", () => {
    render(<ThreeFields />);
    const band = screen.getByTestId("field-band");
    // A fixed band at both breakpoints: the engine sizes three orbits to fit
    // this box, so a box that collapses to its (empty) content would strand
    // them. `relative` is what the absolutely-positioned canvas fills.
    expect(band.className).toMatch(/\bh-64\b/);
    expect(band.className).toMatch(/\bmd:h-80\b/);
    expect(band.className).toMatch(/\brelative\b/);
  });

  it("keeps the canvas decorative and untouchable", () => {
    const { container } = render(<ThreeFields />);
    const canvas = container.querySelector("canvas")!;
    expect(canvas.getAttribute("aria-hidden")).toBe("true");
    expect(canvas.className).toContain("pointer-events-none");
  });

  it("no longer offers a backdrop slot for anything to be layered into", () => {
    // The collision's actual cause. A section that can take a decorative layer
    // behind its text will be given one again, so the slot is gone rather than
    // merely unused (the field is the only thing that ever used it).
    const { container } = render(<App />);
    for (const section of Array.from(container.querySelectorAll("section"))) {
      const canvases = Array.from(section.querySelectorAll("canvas"));
      for (const canvas of canvases) {
        const parent = canvas.parentElement!;
        const isHero = section.querySelector('[data-testid="page-heading"]') !== null;
        // The hero's field is a true backdrop and stays one: it draws no words,
        // so it has nothing to collide with. Every other field is banded.
        if (isHero) continue;
        expect(parent.getAttribute("data-testid"), canvas.outerHTML).toBe("field-band");
      }
    }
  });
});

describe("the section still says everything it said", () => {
  it("renders the heading, the three chips, the body and the emphasis line", () => {
    render(<ThreeFields />);
    expect(screen.getByTestId("section-heading").textContent).toBe(FIELDS_H2);
    const chips = within(screen.getByTestId("field-chips")).getAllByTestId("field-chip");
    expect(chips.map((c) => c.textContent)).toEqual([...FIELDS_CHIPS]);
    expect(document.body.textContent).toContain(FIELDS_BODY);
    expect(screen.getByTestId("emphasis").textContent).toBe(FIELDS_EMPHASIS);
  });
});
