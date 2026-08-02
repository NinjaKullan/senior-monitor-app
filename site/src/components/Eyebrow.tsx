/**
 * The small-caps section label (ruling 75).
 *
 * The typographic form travels from the reference; the semantics do not. This
 * labels **sections and scenarios only** — `HER MORNING` is a place on the page.
 * The device it comes from exists to deliver a judgement about a person's state
 * (`PAY ATTENTION`, `STRESSFUL DAY`), which is what product law #1 forbids, so
 * the slot is re-purposed rather than borrowed. The copy-law test plants a
 * person-status eyebrow to prove it would be caught.
 */
export function Eyebrow({ children }: { children: string }) {
  return (
    <p className="text-eyebrow uppercase text-secondary" data-testid="eyebrow">
      {children}
    </p>
  );
}
