/**
 * The floating CTA (DECISIONS 137).
 *
 * A persistent button is the easiest thing on a page like this to get wrong:
 * it becomes an overlay that is always there, or it lands on the form it points
 * at, or it sits on the privacy link, or it turns into a second offer with
 * different words. So what is asserted here is mostly *absence* — when it must
 * not exist, and that when it does not exist it is not merely invisible.
 *
 * jsdom has no IntersectionObserver, which is itself one of the cases: the
 * component's answer to "I cannot tell where I am" has to be silence. The
 * observer-driven cases run against a fake one the test steps by hand, and the
 * laid-out ones live in scripts/probe-responsive.mjs.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "@/App";
import { FloatingCta, YIELDS_TO, shouldFloat } from "@/components/FloatingCta";
import { HERO_CTA } from "@/copy";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..");

/** An IntersectionObserver the test drives, one target at a time. */
class FakeIO {
  static live: FakeIO[] = [];
  callback: IntersectionObserverCallback;
  targets: Element[] = [];
  disconnected = false;

  constructor(callback: IntersectionObserverCallback) {
    this.callback = callback;
    FakeIO.live.push(this);
  }

  observe(target: Element) {
    this.targets.push(target);
  }

  unobserve() {}

  disconnect() {
    this.disconnected = true;
  }

  /** Report each named selector's target as in view or out of it. React only
   *  flushes this because the caller wraps it in `act`. */
  report(states: Record<string, boolean>) {
    const entries = this.targets
      .filter((target) => target.matches(Object.keys(states).join(",")))
      .map((target) => {
        const selector = Object.keys(states).find((key) => target.matches(key))!;
        return { target, isIntersecting: states[selector] } as IntersectionObserverEntry;
      });
    this.callback(entries, this as unknown as IntersectionObserver);
  }
}

/** Everything on screen — the state the page loads in. */
const ALL_IN_VIEW = Object.fromEntries(YIELDS_TO.map((selector) => [selector, true]));
/** Mid-page: hero gone, form and footer not yet arrived. */
const MID_PAGE = Object.fromEntries(YIELDS_TO.map((selector) => [selector, false]));

function renderWithObserver() {
  FakeIO.live = [];
  vi.stubGlobal("IntersectionObserver", FakeIO as never);
  const view = render(<App />);
  return { view, observer: () => FakeIO.live.at(-1)! };
}

afterEach(() => {
  vi.unstubAllGlobals();
  FakeIO.live = [];
});

describe("when the floating CTA may float", () => {
  it("floats only when all three are off screen", () => {
    expect(shouldFloat([false, false, false])).toBe(true);
    expect(shouldFloat([true, false, false])).toBe(false);
    expect(shouldFloat([false, true, false])).toBe(false);
    expect(shouldFloat([false, false, true])).toBe(false);
  });

  it("says no when it cannot tell where it is", () => {
    // A short list means a selector found nothing, which means the page is not
    // the page this component was written against. Silence, not a guess.
    expect(shouldFloat([])).toBe(false);
    expect(shouldFloat([false, false])).toBe(false);
  });

  it("yields to the hero, the form and the footer, and names them", () => {
    expect([...YIELDS_TO]).toEqual(["#hero", "#waitlist", '[data-testid="footer"]']);
  });
});

describe("the floating CTA on the page", () => {
  it("renders nothing at all with no IntersectionObserver", () => {
    // Not hidden — absent. There is no invisible layer over the page for a
    // pointer or a screen reader to find.
    expect(typeof IntersectionObserver).toBe("undefined");
    render(<App />);
    expect(screen.queryByTestId("floating-cta")).toBeNull();
    expect(screen.queryByTestId("floating-cta-frame")).toBeNull();
  });

  it("stays away while the hero, the form or the footer is on screen", () => {
    const { observer } = renderWithObserver();
    act(() => observer().report(ALL_IN_VIEW));
    expect(screen.queryByTestId("floating-cta")).toBeNull();

    for (const selector of YIELDS_TO) {
      act(() => observer().report({ ...MID_PAGE, [selector]: true }));
      expect(screen.queryByTestId("floating-cta"), `${selector} was on screen`).toBeNull();
    }
  });

  it("arrives once the hero has scrolled past, and leaves at the form", () => {
    const { observer } = renderWithObserver();
    act(() => observer().report(MID_PAGE));
    expect(screen.getByTestId("floating-cta")).toBeTruthy();

    act(() => observer().report({ ...MID_PAGE, "#waitlist": true }));
    expect(screen.queryByTestId("floating-cta")).toBeNull();
  });

  it("observes exactly the three, and lets go on unmount", () => {
    FakeIO.live = [];
    vi.stubGlobal("IntersectionObserver", FakeIO as never);
    const { unmount } = render(<App />);
    const observer = FakeIO.live.at(-1)!;
    expect(observer.targets).toHaveLength(YIELDS_TO.length);
    expect(observer.disconnected).toBe(false);
    unmount();
    expect(observer.disconnected).toBe(true);
  });
});

describe("what the floating CTA is made of", () => {
  const floating = () => {
    const { observer } = renderWithObserver();
    act(() => observer().report(MID_PAGE));
    return screen.getByTestId("floating-cta");
  };

  it("is a real link to the form, in the hero's own words", () => {
    const link = floating().querySelector("a")!;
    expect(link.getAttribute("href")).toBe("#waitlist");
    expect(link.textContent).toBe(HERO_CTA);
    // One offer, worded once. Every link-shaped CTA on the page points at the
    // form and says the same thing; the form's own submit button is the only
    // other CTA, and it is a button on the form rather than a second ask.
    const asks = screen.getAllByTestId("cta").filter((cta) => cta.tagName === "A");
    expect(asks.map((cta) => cta.getAttribute("href"))).toEqual(["#waitlist", "#waitlist"]);
    expect(new Set(asks.map((cta) => cta.textContent))).toEqual(new Set([HERO_CTA]));
  });

  it("is content, never decoration: no aria-hidden anywhere on it", () => {
    floating();
    const frame = screen.getByTestId("floating-cta-frame");
    for (const node of [frame, ...Array.from(frame.querySelectorAll("*"))]) {
      expect(node.hasAttribute("aria-hidden"), node.outerHTML).toBe(false);
    }
  });

  it("keeps a visible focus ring, because it is reached by keyboard", () => {
    const link = floating().querySelector("a")!;
    expect(link.tagName).toBe("A");
    expect(link.className).toContain("focus-visible:ring-2");
    // 24px of body line-height plus py-3 top and bottom is a 48px target,
    // above the 44px the ruling asks for.
    expect(link.className).toContain("py-3");
    expect(link.className).toContain("text-body");
  });

  it("cannot intercept a scroll or a tap outside the pill itself", () => {
    const pill = floating();
    const frame = screen.getByTestId("floating-cta-frame");
    expect(frame.className).toContain("pointer-events-none");
    expect(pill.className).toContain("pointer-events-auto");
  });

  it("enters with the motion law's one animation, and nothing else", () => {
    const pill = floating();
    expect(pill.className).toContain("motion-safe:animate-rise");
    // No exit animation, because the law has none: it is unmounted, and a
    // transition class here would be a second kind of motion on the page.
    expect(pill.className).not.toMatch(/transition|duration-\d/);
  });

  it("sits bottom-centre on a phone and bottom-right from md, clear of the inset", () => {
    // jsdom cannot measure, so the classes carry the arithmetic: a full-width
    // frame does the centring, so no transform is involved, and `pb-safe` is
    // 24px plus whatever the device reserves for its home indicator.
    floating();
    const frame = screen.getByTestId("floating-cta-frame");
    expect(frame.className).toContain("fixed");
    expect(frame.className).toContain("inset-x-0");
    expect(frame.className).toContain("bottom-0");
    expect(frame.className).toContain("justify-center");
    expect(frame.className).toContain("md:justify-end");
    expect(frame.className).toContain("px-6");
    expect(frame.className).toContain("pb-safe");
    expect(frame.className).not.toMatch(/translate-/);

    const css = readFileSync(join(SRC, "index.css"), "utf8");
    expect(css).toMatch(/\.pb-safe\s*\{[^}]*calc\(1\.5rem \+ env\(safe-area-inset-bottom\)\)/);
  });

  it("watches with an observer and nothing else", () => {
    // The stir's discipline: no scroll listener, no preventDefault, no work on
    // the main thread every frame.
    const source = readFileSync(join(SRC, "components", "FloatingCta.tsx"), "utf8");
    expect(source).not.toMatch(/addEventListener\s*\(\s*["']scroll/);
    expect(source).not.toMatch(/preventDefault\s*\(/);
    expect(source).toMatch(/new IntersectionObserver\(/);
  });
});

describe("the page without it", () => {
  it("still carries the hero CTA and the form, so it is an addition", () => {
    // If the floating button ever became the only way to reach the form, its
    // absence at the hero and at the footer would be a dead end.
    render(<FloatingCta />);
    expect(screen.queryByTestId("floating-cta")).toBeNull();
    render(<App />);
    expect(screen.getAllByTestId("cta").length).toBeGreaterThanOrEqual(1);
    expect(document.querySelector("#waitlist")).not.toBeNull();
  });
});
