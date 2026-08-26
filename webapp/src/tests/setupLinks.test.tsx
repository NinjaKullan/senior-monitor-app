/**
 * @vitest-environment jsdom
 *
 * Pinned per file rather than left to vite.config.ts alone (DECISIONS 146): a
 * suite whose verdict depends on how it was invoked is the false green wearing
 * a new coat, and `--environment node` on the command line is one flag away.
 */
/**
 * The family's forwarding surface (spec 005b §4.1).
 *
 * Two properties carry the weight. The share intent is WhatsApp-first and the
 * URL rides *inside* it, correctly encoded — a mangled link is a parent stuck
 * on a dead page 8,000 miles away. And the slug is a credential: it may
 * travel in an href, but the visible text of the app must never print it.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { buildSetupEntries, setupPageUrl, shareText } from "@/lib/setupLinks";
import { FamilyScreen } from "@/screens/Family";
import type { Parent, Ping, SetupLink } from "@/lib/types";
import { SETUP_SEND_LABEL } from "@/lib/copy";

const NOW = new Date("2026-08-16T12:00:00Z");
const bare = {
  tz: null,
  phone_e164: null,
  whatsapp_e164: null,
  relationship: null,
  city_label: null,
};
const parents: Parent[] = [
  { id: "p1", family_id: "f1", display_name: "Amma", ...bare },
  { id: "p2", family_id: "f1", display_name: "Appa", ...bare },
];

const liveLink = (parent_id: string, slug: string, created = "2026-08-15T00:00:00Z"): SetupLink => ({
  parent_id,
  slug,
  created_utc: created,
  expires_utc: "2026-08-22T00:00:00Z",
  revoked_utc: null,
});

describe("buildSetupEntries", () => {
  it("offers a ready link only to parents the server has never heard from", () => {
    const pings: Ping[] = [{ parent_id: "p1", signal: "routine", ts_utc: "2026-08-16T02:00:00Z" }];
    const links = [liveLink("p1", "slugA000000000000000000A"), liveLink("p2", "slugB000000000000000000B")];

    const [amma, appa] = buildSetupEntries(parents, links, pings, NOW);
    expect(amma.status).toBe("reporting");
    expect(amma.shareHref).toBeNull();
    expect(appa.status).toBe("ready");
    expect(appa.url).toBe(setupPageUrl("slugB000000000000000000B"));
    expect(appa.expiresDate).toBe("2026-08-22");
  });

  it("treats expired and revoked links as absent", () => {
    const expired: SetupLink = {
      ...liveLink("p1", "slugexpired0000000000000"),
      expires_utc: "2026-08-15T00:00:00Z",
    };
    const revoked: SetupLink = {
      ...liveLink("p2", "slugrevoked0000000000000"),
      revoked_utc: "2026-08-15T00:00:00Z",
    };
    const [amma, appa] = buildSetupEntries(parents, [expired, revoked], [], NOW);
    expect(amma.status).toBe("needs_link");
    expect(appa.status).toBe("needs_link");
  });

  it("prefers the newest live link after a rotation", () => {
    const links = [
      liveLink("p1", "slugolder00000000000000O", "2026-08-10T00:00:00Z"),
      liveLink("p1", "slugnewer00000000000000N", "2026-08-15T00:00:00Z"),
    ];
    const [amma] = buildSetupEntries([parents[0]], links, [], NOW);
    expect(amma.url).toContain("slugnewer00000000000000N");
  });

  it("encodes the share message for the WhatsApp intent", () => {
    const [amma] = buildSetupEntries(
      [parents[0]],
      [liveLink("p1", "slugA000000000000000000A")],
      [],
      NOW,
    );
    expect(amma.shareHref).toMatch(/^https:\/\/wa\.me\/\?text=/);
    const text = decodeURIComponent(amma.shareHref!.split("text=")[1]);
    expect(text).toBe(shareText("Amma", setupPageUrl("slugA000000000000000000A")));
    expect(text).toContain("/s/slugA000000000000000000A");
  });
});

describe("the Family screen's setup card", () => {
  const entries = buildSetupEntries(
    parents,
    [liveLink("p2", "slugB000000000000000000B")],
    [{ parent_id: "p1", signal: "routine", ts_utc: "2026-08-16T02:00:00Z" }],
    NOW,
  );

  const shared = {
    parentStates: [],
    cities: {},
    members: [],
    journal: [],
    todayDate: "2026-08-16",
    onOpen: () => undefined,
    onAddNote: async () => undefined,
    onSaveCity: async () => undefined,
  };

  function renderCard() {
    // The setup card is what these tests exercise; the parents list above it
    // renders from precomputed states and gets an empty list here.
    return render(<FamilyScreen {...shared} setupEntries={entries} />);
  }

  it("labels each parent's state and offers the share link", () => {
    renderCard();
    const statuses = screen.getAllByTestId("setup-status").map((n) => n.textContent);
    expect(statuses).toEqual(["Set up and reporting", "Ready to send"]);

    const share = screen.getByTestId("setup-share");
    // The channel, named by ruling (DECISIONS 122). The parent it belongs to is
    // the line directly above it, which is why the label no longer carries a
    // name — one card, one parent, one button.
    expect(share).toHaveTextContent(SETUP_SEND_LABEL);
    expect(share).toHaveTextContent("Send on WhatsApp");
    expect(share.getAttribute("href")).toContain("wa.me");
  });

  it("never prints the slug as visible text", () => {
    renderCard();
    expect(document.body.textContent).not.toContain("slugB000000000000000000B");
  });

  it("shows the sending drill only while a link is waiting to be sent", () => {
    const withReady = renderCard();
    expect(document.body.textContent).toContain("one person's set at a time");
    withReady.unmount();

    render(
      <FamilyScreen
        {...shared}
        setupEntries={buildSetupEntries(
          [parents[0]],
          [],
          [{ parent_id: "p1", signal: "routine", ts_utc: "2026-08-16T02:00:00Z" }],
          NOW,
        )}
      />,
    );
    // Everyone is reporting: the drill has nothing left to instruct.
    expect(document.body.textContent).not.toContain("one person's set at a time");
  });
});
