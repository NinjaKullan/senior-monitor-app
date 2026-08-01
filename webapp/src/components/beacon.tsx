import { BEACON_LABEL } from "@/lib/copy";
import type { BeaconState } from "@/lib/glance";

/**
 * Phone status, never person status (attribution law). Absent when there is
 * nothing honest to show; still and grey when the last signal is old; breathing
 * only while a real one is recent.
 *
 * Shared by the Glance card and its tripwire detail view, because 005d asks the
 * detail header to carry *the same* beacon — one definition means the detail
 * screen cannot drift into inventing a state the card never shows.
 */
export function Beacon({ state }: { state: BeaconState | null }) {
  if (state === null) return null;
  const breathing = state === "breathing";
  return (
    <span
      className="flex shrink-0 items-center gap-1.5 text-xs text-muted-foreground"
      data-testid="beacon"
      data-state={state}
    >
      <span
        aria-hidden="true"
        data-testid="beacon-dot"
        className={
          "inline-block h-2 w-2 rounded-full " +
          (breathing ? "bg-calm motion-safe:animate-breathe" : "bg-muted-foreground/40")
        }
      />
      {BEACON_LABEL}
    </span>
  );
}
