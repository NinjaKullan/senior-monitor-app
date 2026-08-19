import { useCallback, useRef } from "react";
import { Eyebrow } from "@/components/Eyebrow";
import { PillLink } from "@/components/Pill";
import {
  HERO_BODY,
  HERO_CTA,
  HERO_EVENING_ALT,
  HERO_EYEBROW,
  HERO_H1,
  HERO_MORNING_ALT,
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
 * The diptych below the headline is the brief's "two lives, one frame"
 * (docs/hero-diptych-brief.md): parent left in his morning, adult child right
 * in her evening, profiles facing inward, the gap between the frames doing the
 * work no drawn connection line is allowed to. Side by side on desktop,
 * stacked on mobile. The headline block keeps priority: text first in source
 * and on screen, never overlaid on the photograph. Both images load eagerly —
 * they are the hero; everything below it lazy-loads.
 *
 * Behind and between them, the rhythm field (QUESTIONS 129/131): drifting
 * motes, soft amber rings for ordinary signals, and — once, slowly, after the
 * hero has been seen for about six seconds — the quiet morning, in which the
 * one amber mote travels to the *parent's* frame first and resolves in sage.
 * The ladder, animated; nothing that implies learning, scoring or inference,
 * and no labels in the field. The canvas is decoration: aria-hidden, behind
 * the content, loaded lazily, and the page is whole without it.
 */
export function Hero() {
  const parentFrameRef = useRef<HTMLImageElement | null>(null);

  const start = useCallback(
    (module: typeof import("@/lib/rhythmField"), canvas: HTMLCanvasElement): FieldHandle =>
      module.startHeroField(canvas, {
        reducedMotion: module.prefersReducedMotion(),
        mobile: module.isMobileViewport(),
        // The messenger goes to the parent's side first — the left frame,
        // located at flight time so a resize cannot strand it.
        parentTarget: () => {
          const frame = parentFrameRef.current;
          if (!frame) return null;
          const c = canvas.getBoundingClientRect();
          const r = frame.getBoundingClientRect();
          return { x: r.left - c.left + r.width / 2, y: r.top - c.top + r.height / 2 };
        },
      }),
    [],
  );
  const fieldRef = useLazyField(start);

  return (
    <section
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
        {/* Side by side at every width (QUESTIONS 129): stacking both
            portraits made the mobile hero two photographs tall. At 390px the
            arithmetic is 342px of content, two columns and a 12px gap, so
            each frame is 165px wide and, at 3:4, 220px tall — headline, sub
            and CTA all land in the first viewport height, and the diptych
            stays a diptych instead of a scroll. Desktop keeps the 4:5 crop. */}
        <div className="mt-8 grid grid-cols-2 gap-3 md:gap-4" data-testid="hero-diptych">
          <img
            ref={parentFrameRef}
            src="/hero-morning.webp"
            alt={HERO_MORNING_ALT}
            decoding="async"
            className="aspect-[3/4] w-full rounded-card object-cover md:aspect-[4/5]"
          />
          <img
            src="/hero-evening.webp"
            alt={HERO_EVENING_ALT}
            decoding="async"
            className="aspect-[3/4] w-full rounded-card object-cover md:aspect-[4/5]"
          />
        </div>
      </div>
    </section>
  );
}
