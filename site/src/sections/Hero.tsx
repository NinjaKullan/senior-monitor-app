import { Eyebrow } from "@/components/Eyebrow";
import { ImageSlot } from "@/components/ImageSlot";
import { PillLink } from "@/components/Pill";
import { HERO_ALT, HERO_BODY, HERO_CTA, HERO_EYEBROW, HERO_H1 } from "@/copy";
import { washBackground } from "@/lib/wash";

/**
 * The hero shares the morning tint set: the page opens on her morning, which is
 * the moment the whole product is about. One CTA, no second path — the only
 * thing to do here is join, and a page that offers three next steps is a page
 * that has not decided what it is for.
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
        <p className="max-w-xl text-lead text-secondary">{HERO_BODY}</p>
        <div>
          <PillLink href="#waitlist">{HERO_CTA}</PillLink>
        </div>
        <ImageSlot alt={HERO_ALT} className="mt-8" />
      </div>
    </section>
  );
}
