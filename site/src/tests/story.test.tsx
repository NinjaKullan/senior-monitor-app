/**
 * Amendment B — the kettle story, and where it sits.
 *
 * A section whose whole job is a name could carry very little and still look
 * finished, which is why the assertions here are mostly about restraint: it
 * says its idea in one whole sentence, it carries no wash (a tint would imply a
 * fifth scenario), and it names nobody. Its position is asserted too — the story is an
 * argument that hands off to the privacy centrepiece, and a section that drifts
 * below the three fields stops being an argument and becomes a footnote.
 */
import { render, screen, within } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import App from "@/App";
import { KettleStory } from "@/sections/KettleStory";
import { PARENT_X_FRACTION } from "@/sections/Hero";
import {
  FIELDS_H2,
  FOUNDING_H2,
  HERO_BODY,
  HERO_NO_DEVICE_BODY,
  HOW_H2,
  SCENARIOS_H2,
  STORY_H2,
  STORY_ONE_BODY,
  STORY_THREE_BODY,
  STORY_TWO_BODY,
  STORY_TWO_LEAD,
  WAITLIST_H2,
} from "@/copy";

describe("the section order", () => {
  it("puts the story between the scenarios and the three fields", () => {
    // kettle → phone → three fields, in that order, is the argument. The
    // amendment places it deliberately, so the placement is pinned rather than
    // left to whoever next adds a section to App.tsx. The founding-families
    // section (beta conversion, QUESTIONS 129) sits directly before the form:
    // what the beta is, then the ask.
    render(<App />);
    const headings = screen.getAllByTestId("section-heading").map((n) => n.textContent);
    expect(headings).toEqual([
      SCENARIOS_H2,
      STORY_H2,
      FIELDS_H2,
      HOW_H2,
      FOUNDING_H2,
      WAITLIST_H2,
    ]);
  });

  it("holds that order in the static HTML too", () => {
    const html = renderToStaticMarkup(<App />);
    const positions = [SCENARIOS_H2, STORY_H2, FIELDS_H2].map((h) => html.indexOf(h));
    expect(positions.every((index) => index >= 0)).toBe(true);
    expect([...positions].sort((a, b) => a - b)).toEqual(positions);
  });
});

describe("the story section itself", () => {
  it("renders its three paragraphs", () => {
    render(<KettleStory />);
    const text = document.body.textContent ?? "";
    expect(text).toContain(STORY_ONE_BODY);
    expect(text).toContain(`${STORY_TWO_LEAD} ${STORY_TWO_BODY}`);
    expect(text).toContain(STORY_THREE_BODY);
  });

  it("says the idea in one unbroken sentence, in the page's one face", () => {
    // The phrase used to be an italic serif fragment spliced into this
    // sentence. QUESTIONS 135 retired that role; the sentence is whole, and
    // nothing inside the paragraph changes face or slope.
    const { container } = render(<KettleStory />);
    const sentence = Array.from(container.querySelectorAll("p")).find((node) =>
      (node.textContent ?? "").includes(STORY_TWO_LEAD),
    )!;
    expect(sentence.textContent).toBe(`${STORY_TWO_LEAD} ${STORY_TWO_BODY}`);
    expect(sentence.querySelectorAll("em, i, .font-serif, .italic")).toHaveLength(0);
  });

  it("carries no corner wash", () => {
    // Every section that has one is telling you about a time of day. This one is
    // telling you about a name, and a tint here would read as a fifth scenario.
    const { container } = render(<KettleStory />);
    const section = container.querySelector("section")!;
    expect(section.getAttribute("style")).toBeNull();
    expect(section.className).not.toMatch(/tint/);
  });

  it("keeps the standard entry motion, gated like every other section", () => {
    const { container } = render(<KettleStory />);
    expect(container.querySelector("section")!.className).toContain("motion-safe:animate-rise");
  });

  it("names no company and no product but this one", () => {
    // A real service inspired the story; marketing does not borrow someone
    // else's trademark to explain its own name. The story is told anonymously
    // and stays that way.
    render(<KettleStory />);
    const text = (document.body.textContent ?? "").replace(/\bKettle\b/g, "");
    expect(text).not.toMatch(/[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*™|®/);
    expect(text.toLowerCase()).not.toMatch(/\b(inc|ltd|corp|co\.|gmbh|k\.k\.)\b/);
  });

  it("does not restate the senior-first mechanism", () => {
    // The off panel already carries it. Saying it twice would sell the ladder
    // twice — and the framing that reaches for it ("before alerting family")
    // uses a word banned on this surface.
    render(<KettleStory />);
    const text = (document.body.textContent ?? "").toLowerCase();
    for (const phrase of ["asks her first", "asks them first", "before anyone", "alert"]) {
      expect(text, `the story restates the ladder: ${phrase}`).not.toContain(phrase);
    }
  });
});

describe("the hero sub, now two sentences", () => {
  it("renders both in one block", () => {
    render(<App />);
    const sub = screen.getByTestId("hero-sub");
    expect(within(sub).getByText(HERO_BODY)).toBeInTheDocument();
    expect(within(sub).getByText(HERO_NO_DEVICE_BODY)).toBeInTheDocument();
  });

  it("answers the device objection without naming a device", () => {
    // "No new devices" is the whole claim. A page that starts listing what it
    // is not — no pendant, no wristband, no sensor — has made the reader
    // picture all three.
    expect(HERO_NO_DEVICE_BODY.toLowerCase()).not.toMatch(
      /pendant|wristband|sensor|wearable|camera|button/,
    );
  });
});

describe("the hero image", () => {
  it("keeps the headline block first, then one eager illustration", () => {
    render(<App />);
    const image = screen.getByTestId("hero-image");

    // The headline block keeps priority: text before the artwork, in source
    // and therefore on screen, per the brief's no-overlay law.
    const sub = screen.getByTestId("hero-sub");
    expect(
      sub.compareDocumentPosition(image) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();

    expect(image.getAttribute("src")).toBe("/hero-two-cities.webp");
    // The hero image is the page's visual identity: never lazy. Everything
    // below the hero lazy-loads (asserted where those sections are tested).
    expect(image.getAttribute("loading")).not.toBe("lazy");
    expect(image.hasAttribute("alt")).toBe(true);
  });

  it("is one frame, not two — the grid is gone rather than collapsed", () => {
    // The diptych staged the gap between two rooms with a column gap. The
    // drawing contains that gap, so the grid has no job left; a two-column
    // container here would be staging it twice (QUESTIONS 136).
    const { container } = render(<App />);
    const hero = screen.getByTestId("hero-image").closest("section")!;
    expect(hero.querySelectorAll("img")).toHaveLength(1);
    expect(screen.queryByTestId("hero-diptych")).toBeNull();
    expect(container.querySelector('[class*="grid-cols-2"]')).toBeNull();
  });

  it("uses one crop at every width, with the phone arithmetic beside it", () => {
    // jsdom cannot measure, so the classes that produce the layout are pinned
    // with their arithmetic: at 390px the content column is 342px, so a 16:9
    // frame is 192px tall — shorter than either half of the old diptych, which
    // is what keeps headline, sub and CTA in the first viewport height.
    render(<App />);
    const image = screen.getByTestId("hero-image");
    expect(image.className).toContain("aspect-[16/9]");
    expect(image.className).toContain("w-full");
    expect(image.className).not.toMatch(/md:aspect-/);
  });

  it("still sends the messenger to the parent's half of the drawing", () => {
    // Law #6 at the animation: the quiet morning asks the parent first, and
    // the mote has to land on her room. The frame that used to locate her is
    // gone, so the fraction that replaces it is pinned — anything at or past
    // the middle would put her question on her daughter's side of the page.
    expect(PARENT_X_FRACTION).toBeGreaterThan(0);
    expect(PARENT_X_FRACTION).toBeLessThan(0.5);
    expect(PARENT_X_FRACTION).toBe(0.25);
  });
});
