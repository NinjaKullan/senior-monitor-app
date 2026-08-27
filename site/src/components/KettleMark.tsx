/**
 * The living kettle (DECISIONS 187) — placement Option A, "the mark".
 *
 * A small kettle above the hero kicker, steaming. It is the quietest of the
 * three placements the wireframes offered: the page gains a heartbeat and no
 * layout moves, the hero illustration keeps the spotlight, and the mark reads
 * as a wordmark that happens to be alive rather than as a second picture
 * competing with the first.
 *
 * It is decoration and is built to say so: empty alt, the steam layers
 * aria-hidden, and the page whole without any of it. It loads eagerly for the
 * one reason an image is allowed to — it is above the fold, and at 61KB it
 * costs less than the pop-in would.
 *
 * All geometry lives in `src/kettle-mark.css`, in container-relative units.
 * There are no numbers in this file on purpose: a size written here would be a
 * size the stylesheet's scaling law cannot see.
 */
export function KettleMark() {
  return (
    <span className="kt-mark" data-testid="kettle-mark">
      <img
        src="/kettle-hero.webp"
        alt=""
        aria-hidden="true"
        loading="eager"
        decoding="async"
        className="kt-mark-image"
        data-testid="kettle-image"
      />
      {/* The spout: four wisps on staggered negative delays, so the kettle is
          already steaming when the page paints. */}
      <span className="kt-steam" aria-hidden="true" data-testid="kettle-steam">
        <span className="kt-wisp kt-wisp-a" data-testid="kettle-wisp" />
        <span className="kt-wisp kt-wisp-b" data-testid="kettle-wisp" />
        <span className="kt-wisp kt-wisp-c" data-testid="kettle-wisp" />
        <span className="kt-wisp kt-wisp-d" data-testid="kettle-wisp" />
      </span>
      {/* The lid rim's fainter leak, on its own slower cycle. */}
      <span className="kt-steam-lid" aria-hidden="true" data-testid="kettle-steam-lid">
        <span className="kt-wisp kt-wisp-lid" data-testid="kettle-wisp" />
      </span>
    </span>
  );
}
