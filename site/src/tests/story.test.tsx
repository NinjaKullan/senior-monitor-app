/**
 * Amendment B — the kettle story, and where it sits.
 *
 * A section whose whole job is a name could carry very little and still look
 * finished, which is why the assertions here are mostly about restraint: it
 * spends the serif once, it carries no wash (a tint would imply a fifth
 * scenario), and it names nobody. Its position is asserted too — the story is an
 * argument that hands off to the privacy centrepiece, and a section that drifts
 * below the three fields stops being an argument and becomes a footnote.
 */
import { render, screen, within } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import App from "@/App";
import { KettleStory } from "@/sections/KettleStory";
import {
  FIELDS_H2,
  HERO_BODY,
  HERO_NO_DEVICE_BODY,
  HOW_H2,
  SCENARIOS_H2,
  STORY_H2,
  STORY_ONE_BODY,
  STORY_THREE_BODY,
  STORY_TWO_BODY,
  STORY_TWO_LEAD,
  STORY_TWO_SERIF,
  WAITLIST_H2,
} from "@/copy";

describe("the section order", () => {
  it("puts the story between the scenarios and the three fields", () => {
    // kettle → phone → three fields, in that order, is the argument. The
    // amendment places it deliberately, so the placement is pinned rather than
    // left to whoever next adds a section to App.tsx.
    render(<App />);
    const headings = screen.getAllByTestId("section-heading").map((n) => n.textContent);
    expect(headings).toEqual([SCENARIOS_H2, STORY_H2, FIELDS_H2, HOW_H2, WAITLIST_H2]);
  });

  it("holds that order in the static HTML too", () => {
    const html = renderToStaticMarkup(<App />);
    const positions = [SCENARIOS_H2, STORY_H2, FIELDS_H2].map((h) => html.indexOf(h));
    expect(positions.every((index) => index >= 0)).toBe(true);
    expect([...positions].sort((a, b) => a - b)).toEqual(positions);
  });
});

describe("the story section itself", () => {
  it("renders its three paragraphs, with the middle one carrying the serif", () => {
    render(<KettleStory />);
    const text = document.body.textContent ?? "";
    expect(text).toContain(STORY_ONE_BODY);
    expect(text).toContain(`${STORY_TWO_LEAD}${STORY_TWO_SERIF} ${STORY_TWO_BODY}`);
    expect(text).toContain(STORY_THREE_BODY);
  });

  it("spends the serif exactly once, on the phrase that is the idea", () => {
    const { container } = render(<KettleStory />);
    const serifs = Array.from(container.querySelectorAll(".font-serif"));
    expect(serifs).toHaveLength(1);
    expect(serifs[0].textContent).toBe(STORY_TWO_SERIF);
    // Inside a sans sentence, not standing alone as one — design-language §3's
    // only permitted shape for it.
    const sentence = serifs[0].closest("p")!;
    expect(sentence.textContent).toContain(STORY_TWO_LEAD.trim());
    expect(sentence.textContent).toContain(STORY_TWO_BODY);
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

describe("the hero diptych", () => {
  it("keeps the headline block first, then two eager photographs in day order", () => {
    render(<App />);
    const diptych = screen.getByTestId("hero-diptych");

    // The headline block keeps priority: text before photographs, in source
    // and therefore on screen, per the brief's no-overlay law.
    const sub = screen.getByTestId("hero-sub");
    expect(
      sub.compareDocumentPosition(diptych) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();

    // Parent's morning left, child's evening right (profiles face inward,
    // docs/hero-diptych-brief.md: parent left is decided, not relitigable).
    const images = Array.from(diptych.querySelectorAll("img"));
    expect(images.map((i) => i.getAttribute("src"))).toEqual([
      "/hero-morning.webp",
      "/hero-evening.webp",
    ]);

    // The hero pair is the page's visual identity: never lazy. Everything
    // below the hero lazy-loads (asserted where those sections are tested).
    for (const image of images) {
      expect(image.getAttribute("loading")).not.toBe("lazy");
      expect(image.hasAttribute("alt")).toBe(true);
    }
  });
});
