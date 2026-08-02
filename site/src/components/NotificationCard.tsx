import { NOTIFICATION, cardRadius } from "@/lib/notification";
import { NOTIF_APP_LABEL, NOTIF_TIMESTAMP_LABEL } from "@/copy";

/**
 * The notification mockup, rebuilt at the measured proportions (spec 006 §5).
 *
 * Transparent fill on purpose: the slot behind shows through, the way a real
 * notification sits over a real photograph. Stroke is ink at reduced opacity —
 * present, never assertive — and there is no red badge, no count, no siren,
 * because there is no token on this site to make one with.
 *
 * The timestamp reads `Today`, never a clock time. A landing page that shows
 * `7:42 am` beside a parent's name has published their waking hour to everyone who
 * scrolls past, and the digit walk (AC4) fails on it.
 */
export function NotificationCard({ body }: { body: string }) {
  const icon = `${NOTIFICATION.iconPercentOfWidth}%`;
  return (
    <div
      data-testid="notification"
      className="flex w-full items-center gap-3 bg-transparent px-[3%]"
      style={{
        aspectRatio: String(NOTIFICATION.aspectRatio),
        borderRadius: cardRadius(),
        borderWidth: `${NOTIFICATION.strokeWidthPx}px`,
        borderStyle: "solid",
        // Ink at reduced opacity, expressed against the token rather than as a
        // second colour value — AC1's "one file holds every colour" survives it.
        borderColor: `color-mix(in srgb, var(--ink) ${
          NOTIFICATION.strokeOpacity * 100
        }%, transparent)`,
      }}
    >
      <span
        aria-hidden="true"
        data-testid="notification-icon"
        className="shrink-0 bg-calm"
        style={{
          width: icon,
          aspectRatio: "1",
          borderRadius: `${NOTIFICATION.iconRadiusPercentOfIcon}%`,
        }}
      />
      <span className="min-w-0 flex-1 truncate text-body" data-testid="notification-body">
        <span className="sr-only">{NOTIF_APP_LABEL}: </span>
        {body}
      </span>
      <span className="shrink-0 text-eyebrow text-secondary" data-testid="notification-time">
        {NOTIF_TIMESTAMP_LABEL}
      </span>
    </div>
  );
}
