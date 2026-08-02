import { Eyebrow } from "@/components/Eyebrow";
import { Section } from "@/components/Section";
import { SerifPhrase } from "@/components/SerifPhrase";
import {
  STORY_EYEBROW,
  STORY_H2,
  STORY_ONE_BODY,
  STORY_THREE_BODY,
  STORY_TWO_BODY,
  STORY_TWO_LEAD,
  STORY_TWO_SERIF,
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
 * The serif budget is spent once, on the phrase that is the idea itself.
 */
export function KettleStory() {
  return (
    <Section id="why-the-name">
      <Eyebrow>{STORY_EYEBROW}</Eyebrow>
      <h2 className="text-display font-light" data-testid="section-heading">
        {STORY_H2}
      </h2>
      <p className="max-w-xl text-lead text-secondary">{STORY_ONE_BODY}</p>
      <p className="max-w-xl text-lead">
        {STORY_TWO_LEAD}
        <SerifPhrase>{STORY_TWO_SERIF}</SerifPhrase> {STORY_TWO_BODY}
      </p>
      <p className="max-w-xl text-body text-secondary">{STORY_THREE_BODY}</p>
    </Section>
  );
}
