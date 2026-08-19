import { Section } from "@/components/Section";
import {
  HOW_H2,
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
