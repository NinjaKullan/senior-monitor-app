/**
 * The family's side of onboarding (spec 005b §4.1): one labelled,
 * forward-ready setup link per parent, and where each parent's setup stands.
 *
 * The child never handles tokens and never sees a slug as text — the link
 * rides inside an href, and the WhatsApp share intent is the first-class way
 * to pass it on. The judgement of *whether* setup worked belongs to the
 * page's verify step and the Glance card, not to this list; this list only
 * answers "does {name} still need their link, and how do I send it".
 */

import type { Parent, Ping, SetupLink } from "./types";

/**
 * Where setup pages live: the API's public address, a constant of the
 * product, not a secret and not configuration this bundle reads from the
 * environment (the env surface stays exactly two Supabase values).
 */
export const SETUP_PAGE_BASE = "https://kettle-api.fly.dev";

export type SetupStatus = "reporting" | "ready" | "needs_link";

export interface SetupEntry {
  parentId: string;
  parentName: string;
  status: SetupStatus;
  /** The page URL, href-only — never rendered as text. */
  url: string | null;
  /** WhatsApp share intent carrying the link (spec: share intent first). */
  shareHref: string | null;
  /** ISO date the live link stops answering. */
  expiresDate: string | null;
}

export function setupPageUrl(slug: string, base: string = SETUP_PAGE_BASE): string {
  return `${base}/s/${slug}`;
}

/** The message the share sheet pre-fills. The files travel separately (Q117). */
export function shareText(parentName: string, url: string): string {
  return `${parentName}'s Kettle setup: ${url}\nOpen it when the button files arrive in this chat.`;
}

export function buildSetupEntries(
  parents: Parent[],
  links: SetupLink[],
  pings: Ping[],
  now: Date,
  base: string = SETUP_PAGE_BASE,
): SetupEntry[] {
  const heard = new Set(pings.map((p) => p.parent_id));
  return parents.map((parent) => {
    // A phone that has ever reported is set up; the link's remaining life is
    // irrelevant and offering to re-send it would only confuse.
    if (heard.has(parent.id)) {
      return {
        parentId: parent.id,
        parentName: parent.display_name,
        status: "reporting" as const,
        url: null,
        shareHref: null,
        expiresDate: null,
      };
    }

    const live = links
      .filter(
        (l) =>
          l.parent_id === parent.id &&
          l.revoked_utc === null &&
          new Date(l.expires_utc).getTime() > now.getTime(),
      )
      .sort((a, b) => b.created_utc.localeCompare(a.created_utc))[0];

    if (!live) {
      return {
        parentId: parent.id,
        parentName: parent.display_name,
        status: "needs_link" as const,
        url: null,
        shareHref: null,
        expiresDate: null,
      };
    }

    const url = setupPageUrl(live.slug, base);
    return {
      parentId: parent.id,
      parentName: parent.display_name,
      status: "ready" as const,
      url,
      shareHref: `https://wa.me/?text=${encodeURIComponent(shareText(parent.display_name, url))}`,
      expiresDate: live.expires_utc.slice(0, 10),
    };
  });
}
