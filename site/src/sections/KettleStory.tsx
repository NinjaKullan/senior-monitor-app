import { Eyebrow } from "@/components/Eyebrow";
import { Section } from "@/components/Section";
import {
  STORY_EYEBROW,
  STORY_H2,
  STORY_ONE_BODY,
  STORY_THREE_BODY,
  STORY_TWO_BODY,
  STORY_TWO_LEAD,
} from "@/copy";

/**
 * Why the name (Amendment B).
 *
 * Placed between the scenarios and the three fields on purpose: the story hands
 * off to the privacy centrepiece rather than interrupting it — kettle, then
 * phone, then the three columns that are the whole record. Read in order it is
 * one argument, not three sections.
 *
 * Flat canvas, no corner wash. Every other section that carries a wash is
 * telling you about a time of day; this one is telling you about a name, and a
 * tint here would imply a fifth scenario.
 *
 * The idea sentence used to be split so the serif could carry its ending; it is
 * one sentence again, in the one face the page speaks (QUESTIONS 135).
 */
export function KettleStory() {
  return (
    <Section id="why-the-name">
      <Eyebrow>{STORY_EYEBROW}</Eyebrow>
      <h2 className="text-heading" data-testid="section-heading">
        {STORY_H2}
      </h2>
      <p className="max-w-xl text-lead text-secondary">{STORY_ONE_BODY}</p>
      <p className="max-w-xl text-lead">
        {STORY_TWO_LEAD} {STORY_TWO_BODY}
      </p>
      <p className="max-w-xl text-body text-secondary">{STORY_THREE_BODY}</p>
    </Section>
  );
}
