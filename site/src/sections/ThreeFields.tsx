import { useCallback } from "react";
import { Section } from "@/components/Section";
import { SerifPhrase } from "@/components/SerifPhrase";
import { FIELDS_BODY, FIELDS_CHIPS, FIELDS_H2, FIELDS_SERIF } from "@/copy";
import type { FieldHandle } from "@/lib/rhythmField";
import { useLazyField } from "@/lib/useLazyField";

/**
 * The privacy centrepiece, and the one section whose claims must be literally
 * true of the schema.
 *
 * `who · signal · when` is not a simplification for marketing — it is the whole
 * row. The copy-law test plants a drifted claim (a fourth chip, a softened
 * "almost nothing else") and requires it to fail, because a privacy promise that
 * has quietly stopped matching the database is the most expensive sentence a
 * company like this can publish.
 *
 * Dark section: `inverted` swaps the tokens, so the ground becomes ink and the
 * text becomes canvas with no second palette anywhere.
 *
 * Behind the content, the rhythm field's second placement (QUESTIONS 129/131):
 * cream dust resolves into three labelled orbits as the section scrolls into
 * view — the labels the canvas draws are the chips' own words, taken from
 * FIELDS_CHIPS, so the animation cannot drift from the claim. The DOM chips
 * above stay the structural truth: with the canvas gone or motion reduced to
 * a still, the section says everything it ever said.
 */
export function ThreeFields() {
  const start = useCallback(
    (module: typeof import("@/lib/rhythmField"), canvas: HTMLCanvasElement): FieldHandle =>
      module.startFieldsResolve(canvas, {
        reducedMotion: module.prefersReducedMotion(),
        mobile: module.isMobileViewport(),
        labels: FIELDS_CHIPS,
      }),
    [],
  );
  const fieldRef = useLazyField(start);

  return (
    <Section
      inverted
      className="min-h-[80vh]"
      backdrop={
        <canvas
          ref={fieldRef}
          data-rhythm-field
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 h-full w-full"
        />
      }
    >
      <h2 className="text-display font-light" data-testid="section-heading">
        {FIELDS_H2}
      </h2>
      <ul className="flex flex-wrap gap-3" data-testid="field-chips">
        {FIELDS_CHIPS.map((chip) => (
          <li
            key={chip}
            data-testid="field-chip"
            className="rounded-tile border border-ink/30 px-5 py-2 text-body"
          >
            {chip}
          </li>
        ))}
      </ul>
      <p className="max-w-xl text-body text-secondary">{FIELDS_BODY}</p>
      <SerifPhrase as="p">{FIELDS_SERIF}</SerifPhrase>
    </Section>
  );
}
