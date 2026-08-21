import { Section } from "@/components/Section";
import {
  HOW_H2,
  HOW_STRIP_ALT,
  STEP_ONE_BODY,
  STEP_ONE_LABEL,
  STEP_THREE_BODY,
  STEP_THREE_LABEL,
  STEP_TWO_BODY,
  STEP_TWO_LABEL,
} from "@/copy";

/**
 * The mechanism, and the only section where delivery vocabulary is allowed.
 *
 * Naming WhatsApp, FaceTime or Shortcuts *here* is naming a mechanism — how the
 * thing works, which a buyer is entitled to know. Naming one inside a sentence
 * about her day would be narrating a person through app names, which is the
 * behaviour profile this product refuses to build. The copy law draws that line
 * and plants an app name in a scenario panel to prove it holds.
 *
 * The step numerals are two of the three digits allowed on this page.
 *
 * The strip that opens the section (DECISIONS 136) is decorative narrative: it
 * draws the same ladder the steps below spell out, and adds no claim of its
 * own. It sits after the heading rather than above it — every section on this
 * page starts with its heading, and an image that outranks one would be the
 * first exception to that.
 */
const STEPS = [
  { label: STEP_ONE_LABEL, body: STEP_ONE_BODY },
  { label: STEP_TWO_LABEL, body: STEP_TWO_BODY },
  { label: STEP_THREE_LABEL, body: STEP_THREE_BODY },
] as const;

export function HowItWorks() {
  return (
    <Section>
      <h2 className="text-heading" data-testid="section-heading">
        {HOW_H2}
      </h2>
      {/* Full content width, the artwork's own 1600x686. Below the hero, so
          it waits its turn like every other image on the page. */}
      <img
        src="/ill-story-strip.webp"
        alt={HOW_STRIP_ALT}
        loading="lazy"
        decoding="async"
        data-testid="story-strip"
        className="aspect-[1600/686] w-full rounded-card object-cover"
      />
      <ol className="flex flex-col gap-10">
        {STEPS.map((step, index) => (
          <li key={step.label} className="flex gap-5" data-testid="step">
            <span
              aria-hidden="true"
              data-testid="step-number"
              className="shrink-0 text-lead text-secondary"
            >
              {index + 1}
            </span>
            <div className="flex flex-col gap-2">
              <p className="text-body font-semibold">{step.label}</p>
              <p className="max-w-xl text-body text-secondary">{step.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </Section>
  );
}
