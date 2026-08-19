import { Section } from "@/components/Section";
import {
  FOOTER_CONTACT_HREF,
  FOUNDER_CONTACT_LABEL,
  FOUNDER_NAME_LABEL,
  FOUNDER_WHY_BODY,
  FOUNDING_FEEDBACK_BODY,
  FOUNDING_H2,
  FOUNDING_PRICE_BODY,
  FOUNDING_SETUP_BODY,
  FOUNDING_SUPPORT_BODY,
} from "@/copy";

/** The four promises, in the order a family meets them. */
const PROMISES = [
  FOUNDING_SETUP_BODY,
  FOUNDING_SUPPORT_BODY,
  FOUNDING_PRICE_BODY,
  FOUNDING_FEEDBACK_BODY,
] as const;

/**
 * What the beta actually is, said before the form asks for anything
 * (beta conversion, QUESTIONS 129). Only promises that will be kept: setup,
 * support, the price, a few conversations — no outcomes, no roadmap. The
 * founder's note sits under them because a beta this small is a relationship
 * with a person, and the person should be on the page. The note is the
 * founder's final text, verbatim (QUESTIONS 132), rendered as the paragraphs
 * it was written in.
 */
export function FoundingFamilies() {
  return (
    <Section>
      <h2 className="text-heading" data-testid="section-heading">
        {FOUNDING_H2}
      </h2>
      <ul className="flex max-w-xl flex-col gap-4" data-testid="founding-promises">
        {PROMISES.map((promise) => (
          <li
            key={promise}
            data-testid="founding-promise"
            className="border-l-2 border-clay pl-4 text-body text-secondary"
          >
            {promise}
          </li>
        ))}
      </ul>
      <div
        className="max-w-xl rounded-card border border-ink/15 p-6"
        data-testid="founder-note"
      >
        <p className="text-body">{FOUNDER_NAME_LABEL}</p>
        <div className="mt-2 space-y-3">
          {FOUNDER_WHY_BODY.map((paragraph) => (
            <p key={paragraph} className="text-body text-secondary">
              {paragraph}
            </p>
          ))}
        </div>
        <a
          className="mt-4 inline-block text-body underline underline-offset-4"
          href={FOOTER_CONTACT_HREF}
        >
          {FOUNDER_CONTACT_LABEL}
        </a>
      </div>
    </Section>
  );
}
