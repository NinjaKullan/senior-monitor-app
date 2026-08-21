import { useCallback } from "react";
import { Section } from "@/components/Section";
import { FIELDS_BODY, FIELDS_CHIPS, FIELDS_EMPHASIS, FIELDS_H2 } from "@/copy";
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
 * Below the words — never behind them — the rhythm field's second placement
 * (DECISIONS 131, re-housed by 135): cream dust resolves into three labelled
 * orbits as the band scrolls into view. The canvas used to span the whole
 * section as a backdrop, which put drawn words underneath written ones at most
 * widths; two reviewers read the result as a collision because it was one. It
 * now has a reserved band of its own, a flow sibling the text cannot enter, so
 * the separation is structural rather than a margin that happens to hold.
 *
 * The DOM chips above stay the structural truth: with the canvas gone or motion
 * reduced to a still, the section says everything it ever said.
 */
export function ThreeFields() {
  const start = useCallback(
    (module: typeof import("@/lib/rhythmField"), canvas: HTMLCanvasElement): FieldHandle =>
      module.startFieldsResolve(canvas, {
        reducedMotion: module.prefersReducedMotion(),
        mobile: module.isMobileViewport(),
        // Desktop pointers only, decided here rather than in the engine so the
        // test can hand it either answer (DECISIONS 135).
        pointer: module.hasFinePointer(),
        labels: FIELDS_CHIPS,
      }),
    [],
  );
  const fieldRef = useLazyField(start);

  return (
    <Section inverted>
      <h2 className="text-heading" data-testid="section-heading">
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
      {/* The page's one emphasis line: a whole sentence, carried by weight in
          the body face. Never an italic fragment inside another sentence. */}
      <p className="max-w-xl text-lead font-medium" data-testid="emphasis">
        {FIELDS_EMPHASIS}
      </p>
      {/* The field's reserved band. Height is fixed rather than fluid so the
          three orbits always have the room the engine sizes them for, and no
          text of any width can be laid over them. */}
      <div className="relative mt-4 h-64 w-full md:h-80" data-testid="field-band">
        <canvas
          ref={fieldRef}
          data-rhythm-field
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 h-full w-full"
        />
      </div>
    </Section>
  );
}
