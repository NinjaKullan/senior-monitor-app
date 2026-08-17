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
 */
export function Hero() {
  return (
    <section
      data-testid="section"
      className="bg-canvas px-6 py-28 text-ink md:py-36"
      style={{ backgroundImage: washBackground("morning") }}
    >
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-8">
        <Eyebrow>{HERO_EYEBROW}</Eyebrow>
        <h1 className="max-w-2xl text-display font-light" data-testid="page-heading">
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
