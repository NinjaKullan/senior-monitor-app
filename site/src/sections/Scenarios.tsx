import { useEffect, useId, useRef, useState } from "react";
import { NotificationCard } from "@/components/NotificationCard";
import {
  AFTERNOON_ALT,
  AFTERNOON_BODY,
  AFTERNOON_H3,
  AFTERNOON_LEAD,
  AFTERNOON_TAB,
  MORNING_ALT,
  MORNING_BODY,
  MORNING_H3,
  MORNING_LEAD,
  MORNING_TAB,
  OFF_ALT,
  OFF_BODY,
  OFF_H3,
  OFF_LEAD,
  OFF_NOTIF,
  OFF_TAB,
  SCENARIOS_H2,
  SEEN_ALT,
  SEEN_BODY,
  SEEN_H3,
  SEEN_LEAD,
  SEEN_NOTIF,
  SEEN_TAB,
} from "@/copy";
import { isOverflowing, scrollLeftFor } from "@/lib/tabStrip";
import { type WashSet, washBackground } from "@/lib/wash";

interface Scenario {
  set: WashSet;
  tab: string;
  /** The panel's one-line headline (beta conversion: the kickers retired). */
  headline: string;
  /** The lead sentence, whole — it used to be split so the serif could carry
   *  its ending (QUESTIONS 135). */
  lead: string;
  body: string;
  /** The commissioned illustration, from site/public/ (QUESTIONS 136 — the
   *  set replaced the photographs wholesale). */
  image: string;
  alt: string;
  notification: string | null;
}

/**
 * The four scenarios, in the order a day happens.
 *
 * They differ by **tint and content only**. One panel component renders all
 * four, which is not a tidiness preference: identical structure is what stops
 * `When something's off` acquiring a border, a badge or a heavier weight that
 * would turn a question into an alarm. AC5 asserts the four rendered panels have
 * the same DOM skeleton.
 */
export const SCENARIOS: readonly Scenario[] = [
  {
    set: "morning",
    tab: MORNING_TAB,
    headline: MORNING_H3,
    lead: MORNING_LEAD,
    body: MORNING_BODY,
    image: "/ill-her-morning.webp",
    alt: MORNING_ALT,
    notification: null,
  },
  {
    set: "afternoon",
    tab: AFTERNOON_TAB,
    headline: AFTERNOON_H3,
    lead: AFTERNOON_LEAD,
    body: AFTERNOON_BODY,
    image: "/ill-her-afternoon.webp",
    alt: AFTERNOON_ALT,
    notification: null,
  },
  {
    set: "off",
    tab: OFF_TAB,
    headline: OFF_H3,
    lead: OFF_LEAD,
    body: OFF_BODY,
    image: "/ill-somethings-off.webp",
    alt: OFF_ALT,
    // Rendered on *her* phone: a question addressed to her, not a claim about
    // her, and the reason this string is allowlisted rather than banned.
    notification: OFF_NOTIF,
  },
  {
    set: "seen",
    tab: SEEN_TAB,
    headline: SEEN_H3,
    lead: SEEN_LEAD,
    body: SEEN_BODY,
    image: "/ill-what-you-see.webp",
    alt: SEEN_ALT,
    notification: SEEN_NOTIF,
  },
] as const;

export function Scenarios() {
  const [active, setActive] = useState(0);
  const [clipped, setClipped] = useState(false);
  const stripRef = useRef<HTMLDivElement | null>(null);
  const base = useId();

  // Is the row actually clipped? Measured rather than assumed from the
  // breakpoint, so a row that happens to fit is never faded (QUESTIONS 136).
  useEffect(() => {
    const strip = stripRef.current;
    if (!strip) return;
    const measure = () => setClipped(isOverflowing(strip.scrollWidth, strip.clientWidth));
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, []);

  // Keep the active tab wholly in view, including when the arrow keys move it
  // past the clipped edge. Setting scrollLeft on the strip itself — never
  // scrollIntoView, which would scroll every ancestor and take the page with
  // it — and instantly, because this is a position, not an animation.
  useEffect(() => {
    const strip = stripRef.current;
    const tab = strip?.children[active];
    if (!strip || !(tab instanceof HTMLElement)) return;
    strip.scrollLeft = scrollLeftFor(strip, tab);
  }, [active]);

  return (
    <section
      id="scenarios"
      data-testid="section"
      className="bg-canvas px-6 py-24 text-ink motion-safe:animate-rise md:py-32"
      style={{ backgroundImage: washBackground(SCENARIOS[active].set) }}
    >
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-8">
        <h2 className="text-heading" data-testid="section-heading">
          {SCENARIOS_H2}
        </h2>

        {/* Measured tab grammar: active is regular weight, full opacity and a
            3px ink bottom border; inactive is 0.7 opacity and a transparent
            border. No fill, no colour change, no weight change between states —
            the difference is presence, not emphasis. */}
        {/* On a phone the four tabs need about 540px and have 312–380, so a
            wrapping row folds into a ragged two-line block (founder, on a real
            handset). Below md the row stops wrapping and scrolls sideways
            instead; from md it is the wrapping row it always was, where four
            tabs have never come close to needing a second line. */}
        <div
          ref={stripRef}
          role="tablist"
          aria-label={SCENARIOS_H2}
          data-testid="scenario-tablist"
          className={
            "flex gap-6 overflow-x-auto scrollbar-none md:flex-wrap md:overflow-x-visible " +
            (clipped ? "fade-edge-x md:[mask-image:none] " : "")
          }
        >
          {SCENARIOS.map((scenario, index) => (
            <button
              key={scenario.set}
              type="button"
              role="tab"
              id={`${base}-tab-${scenario.set}`}
              aria-selected={index === active}
              aria-controls={`${base}-panel-${scenario.set}`}
              tabIndex={index === active ? 0 : -1}
              data-testid="scenario-tab"
              data-state={index === active ? "active" : "inactive"}
              onClick={() => setActive(index)}
              onKeyDown={(event) => {
                const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
                if (step === 0) return;
                event.preventDefault();
                setActive((current) => (current + step + SCENARIOS.length) % SCENARIOS.length);
              }}
              className={
                // `shrink-0` and `whitespace-nowrap` are what make the row a
                // row: without them flex compresses the tabs and the longest
                // label breaks across two lines inside its own tab. `py-2`
                // rather than `pb-2` gives a 40px tap target at body size.
                "shrink-0 whitespace-nowrap border-b-[3px] py-2 text-body " +
                "transition-opacity duration-300 " +
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink " +
                (index === active
                  ? "border-ink opacity-100"
                  : "border-transparent opacity-70")
              }
            >
              {scenario.tab}
            </button>
          ))}
        </div>

        {/* Every panel is rendered and stays in the document: the prerender
            contract (AC9) reads every panel's copy out of the static HTML, and
            reader modes get all four in day order. On screen, `hidden` marks
            the three inactive panels — backed by the stylesheet's [hidden]
            override, because the display utility would otherwise beat the
            attribute and stack all four (QUESTIONS 128). `hidden` rather than
            unmounting is what keeps the copy in the markup. */}
        {SCENARIOS.map((scenario, index) => (
          <div
            key={scenario.set}
            role="tabpanel"
            id={`${base}-panel-${scenario.set}`}
            aria-labelledby={`${base}-tab-${scenario.set}`}
            data-testid="scenario-panel"
            data-scenario={scenario.set}
            data-state={index === active ? "active" : "inactive"}
            hidden={index !== active}
            className="flex flex-col gap-6"
          >
            <h3 className="text-lead font-medium" data-testid="scenario-headline">
              {scenario.headline}
            </h3>
            <p className="text-lead">{scenario.lead}</p>
            <p className="max-w-xl text-body text-secondary">{scenario.body}</p>
            {/* Below the hero, so it lazy-loads; sized by class so the
                digit walk over perceivable attributes stays clean. 4:3 is the
                set's own crop — the container matches the artwork rather than
                cropping it (QUESTIONS 136). */}
            <img
              src={scenario.image}
              alt={scenario.alt}
              loading="lazy"
              decoding="async"
              className="aspect-[4/3] w-full rounded-card object-cover"
            />
            {scenario.notification !== null && (
              <NotificationCard body={scenario.notification} />
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
