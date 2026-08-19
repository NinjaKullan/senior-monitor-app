import { useCallback, useRef } from "react";
import { Eyebrow } from "@/components/Eyebrow";
import { PillLink } from "@/components/Pill";
import {
  HERO_ALT,
  HERO_BODY,
  HERO_CTA,
  HERO_EYEBROW,
  HERO_H1,
  HERO_NO_DEVICE_BODY,
} from "@/copy";
import type { FieldHandle } from "@/lib/rhythmField";
import { useLazyField } from "@/lib/useLazyField";
import { washBackground } from "@/lib/wash";

/**
 * The hero shares the morning tint set: the page opens on her morning, which is
 * the moment the whole product is about. One CTA, no second path — the only
 * thing to do here is join, and a page that offers three next steps is a page
 * that has not decided what it is for.
 *
 * Below the headline is the brief's "two lives, one frame", now drawn rather
 * than photographed (founder decision, QUESTIONS 136): one wide illustration
 * holding both rooms — parent's morning on the left, her daughter's dusk on
 * the right — and the space between them, which is the part no drawn
 * connection line is allowed to do for it. It replaces the two-frame grid
 * outright: the artwork already contains the gap the grid used to stage. The
 * headline block keeps priority: text first in source and on screen, never
 * overlaid on the image. It loads eagerly — it is the hero; everything below
 * it lazy-loads.
 *
 * Behind and between them, the rhythm field (QUESTIONS 129/131): drifting
 * motes, soft amber rings for ordinary signals, and — once, slowly, after the
 * hero has been seen for about six seconds — the quiet morning, in which the
 * one amber mote travels to the *parent's* frame first and resolves in sage.
 * The ladder, animated; nothing that implies learning, scoring or inference,
 * and no labels in the field. The canvas is decoration: aria-hidden, behind
 * the content, loaded lazily, and the page is whole without it.
 */
/** Where the parent is inside the hero artwork, as a fraction of its width.
 *  The drawing puts her room in the left half, so the messenger aims at the
 *  middle of that half rather than at the middle of a frame that no longer
 *  exists (QUESTIONS 136). */
export const PARENT_X_FRACTION = 0.25;

export function Hero() {
  const heroImageRef = useRef<HTMLImageElement | null>(null);

  const start = useCallback(
    (module: typeof import("@/lib/rhythmField"), canvas: HTMLCanvasElement): FieldHandle =>
      module.startHeroField(canvas, {
        reducedMotion: module.prefersReducedMotion(),
        mobile: module.isMobileViewport(),
        // The messenger goes to the parent's side first — her half of the
        // drawing, located at flight time so a resize cannot strand it.
        parentTarget: () => {
          const image = heroImageRef.current;
          if (!image) return null;
          const c = canvas.getBoundingClientRect();
          const r = image.getBoundingClientRect();
          return {
            x: r.left - c.left + r.width * PARENT_X_FRACTION,
            y: r.top - c.top + r.height / 2,
          };
        },
      }),
    [],
  );
  const fieldRef = useLazyField(start);

  return (
    <section
      id="hero"
      data-testid="section"
      className="relative overflow-hidden bg-canvas px-6 py-28 text-ink md:py-36"
      style={{ backgroundImage: washBackground("morning") }}
    >
      <canvas
        ref={fieldRef}
        data-rhythm-field
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 h-full w-full"
      />
      <div className="relative z-10 mx-auto flex w-full max-w-3xl flex-col gap-8">
        <Eyebrow>{HERO_EYEBROW}</Eyebrow>
        <h1 className="max-w-2xl text-display" data-testid="page-heading">
          {HERO_H1}
        </h1>
        {/* One sub block, two sentences: what Kettle notices, and the objection
            it answers before anyone raises it. */}
        <div className="flex max-w-xl flex-col gap-2" data-testid="hero-sub">
          <p className="text-lead text-secondary">{HERO_BODY}</p>
          <p className="text-lead text-secondary">{HERO_NO_DEVICE_BODY}</p>
        </div>
        <div>
          <PillLink href="#waitlist">{HERO_CTA}</PillLink>
        </div>
        {/* One frame at every width, and the mobile arithmetic is simpler for
            it (QUESTIONS 136): at 390px the content column is 342px, so a
            single 16:9 frame is 192px tall — shorter than either half of the
            old two-column diptych, which means headline, sub and CTA still
            land in the first viewport height with room to spare. No breakpoint
            changes the crop, because the drawing is composed for this one. */}
        <img
          ref={heroImageRef}
          src="/hero-two-cities.webp"
          alt={HERO_ALT}
          decoding="async"
          data-testid="hero-image"
          className="mt-8 aspect-[16/9] w-full rounded-card object-cover"
        />
      </div>
    </section>
  );
}
