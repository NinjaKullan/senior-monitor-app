import { IMAGE_PLACEHOLDER_LABEL } from "@/copy";

/**
 * A commissioned photograph that does not exist yet (spec 006 §6).
 *
 * It ships as a flat warm block with the **final alt text baked in now**, and
 * not as stock photography — ever. The category audit's banned-cliché list makes
 * stock a liability rather than a shortcut: toothpaste-ad senior smiles,
 * scrubs-as-competence caregivers, window-forlorn loneliness staging. An honest
 * placeholder beats any of them, and it keeps the alt text — which *is* copy, and
 * passes the copy law — written and reviewable before the shoot.
 *
 * `role="img"` with the alt as the accessible name, so a screen-reader user gets
 * the described scene rather than the word "placeholder".
 */
export function ImageSlot({ alt, className = "" }: { alt: string; className?: string }) {
  return (
    <div
      role="img"
      aria-label={alt}
      data-testid="image-slot"
      className={
        "flex aspect-[4/3] w-full items-end rounded-card bg-clay/30 p-4 " +
        `text-eyebrow uppercase text-secondary ${className}`
      }
    >
      <span aria-hidden="true">{IMAGE_PLACEHOLDER_LABEL}</span>
    </div>
  );
}
