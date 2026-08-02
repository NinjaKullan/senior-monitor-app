import { useId, useState } from "react";
import { Eyebrow } from "@/components/Eyebrow";
import { ImageSlot } from "@/components/ImageSlot";
import { NotificationCard } from "@/components/NotificationCard";
import { SerifPhrase } from "@/components/SerifPhrase";
import {
  AFTERNOON_ALT,
  AFTERNOON_BODY,
  AFTERNOON_EYEBROW,
  AFTERNOON_LEAD,
  AFTERNOON_SERIF,
  AFTERNOON_TAB,
  MORNING_ALT,
  MORNING_BODY,
  MORNING_EYEBROW,
  MORNING_LEAD,
  MORNING_SERIF,
  MORNING_TAB,
  OFF_ALT,
  OFF_BODY,
  OFF_EYEBROW,
  OFF_LEAD,
  OFF_NOTIF,
  OFF_SERIF,
  OFF_TAB,
  SCENARIOS_H2,
  SEEN_ALT,
  SEEN_BODY,
  SEEN_EYEBROW,
  SEEN_LEAD,
  SEEN_NOTIF,
  SEEN_SERIF,
  SEEN_TAB,
} from "@/copy";
import { type WashSet, washBackground } from "@/lib/wash";

interface Scenario {
  set: WashSet;
  tab: string;
  eyebrow: string;
  /** The sans opening of the lead sentence. */
  lead: string;
  /** Its closing phrase, and the only serif on the panel. */
  serif: string;
  body: string;
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
    eyebrow: MORNING_EYEBROW,
    lead: MORNING_LEAD,
    serif: MORNING_SERIF,
    body: MORNING_BODY,
    alt: MORNING_ALT,
    notification: null,
  },
  {
    set: "afternoon",
    tab: AFTERNOON_TAB,
    eyebrow: AFTERNOON_EYEBROW,
    lead: AFTERNOON_LEAD,
    serif: AFTERNOON_SERIF,
    body: AFTERNOON_BODY,
    alt: AFTERNOON_ALT,
    notification: null,
  },
  {
    set: "off",
    tab: OFF_TAB,
    eyebrow: OFF_EYEBROW,
    lead: OFF_LEAD,
    serif: OFF_SERIF,
    body: OFF_BODY,
    alt: OFF_ALT,
    // Rendered on *her* phone: a question addressed to her, not a claim about
    // her, and the reason this string is allowlisted rather than banned.
    notification: OFF_NOTIF,
  },
  {
    set: "seen",
    tab: SEEN_TAB,
    eyebrow: SEEN_EYEBROW,
    lead: SEEN_LEAD,
    serif: SEEN_SERIF,
    body: SEEN_BODY,
    alt: SEEN_ALT,
    notification: SEEN_NOTIF,
  },
] as const;

export function Scenarios() {
  const [active, setActive] = useState(0);
  const base = useId();

  return (
    <section
      id="scenarios"
      data-testid="section"
      className="bg-canvas px-6 py-24 text-ink motion-safe:animate-rise md:py-32"
      style={{ backgroundImage: washBackground(SCENARIOS[active].set) }}
    >
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-8">
        <h2 className="text-display font-light" data-testid="section-heading">
          {SCENARIOS_H2}
        </h2>

        {/* Measured tab grammar: active is regular weight, full opacity and a
            3px ink bottom border; inactive is 0.7 opacity and a transparent
            border. No fill, no colour change, no weight change between states —
            the difference is presence, not emphasis. */}
        <div role="tablist" aria-label={SCENARIOS_H2} className="flex flex-wrap gap-6">
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
                "border-b-[3px] pb-2 text-feature font-normal transition-opacity duration-300 " +
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

        {/* Every panel is rendered. JavaScript hides the three that are not
            active; without it all four stack in order and the page still reads
            (AC9). `hidden` rather than unmounting is what makes that true. */}
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
            <Eyebrow>{scenario.eyebrow}</Eyebrow>
            <p className="text-card font-light">
              {scenario.lead}
              <SerifPhrase>{scenario.serif}</SerifPhrase>
            </p>
            <p className="max-w-xl text-body text-secondary">{scenario.body}</p>
            <ImageSlot alt={scenario.alt} />
            {scenario.notification !== null && (
              <NotificationCard body={scenario.notification} />
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
