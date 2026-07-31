# Spec 005a — Child PWA, demo-grade (read-only)

*PM: Fable. Purpose: an app a prospective beta family can see and feel. Read-only against the live backend; the onboarding wizard, billing, and TestFlight wrap are 005b. Ship fast, ship honest — the demo IS the pitch, so nothing in it may be staged or faked.*

## 1. Stack & shape

- Vite + React + Tailwind + shadcn/ui, `supabase-js` with Supabase Auth — the founder's shipped RosterPro stack, no new learning.
- Lives in `webapp/` at repo root. Deployed as a static site on its own Fly app (`kettle-app`) with an nginx/static Dockerfile — same platform as everything else, no new vendor.
- PWA manifest + icons (installable to home screen — "add it to your phone" is part of the demo). Capacitor/TestFlight is 005b.
- All data access through the `authenticated` role + RLS. The service key never touches this codebase. The app holds only the Supabase URL + publishable key (both safe to ship).

## 2. Auth & member linkage

- Supabase Auth, email magic link (no passwords — senior-adjacent users, founder demos on the fly).
- Linkage: `members.auth_user_id` is null until first login. Add a small RPC (SECURITY DEFINER, migration 0008) `app_claim_membership()`: on login, links `auth.uid()` to member rows whose `email` matches the JWT's verified email and whose `auth_user_id` is null. Follows the 0002 helper's grant pattern (authenticated only; anon revoked per 0004 doctrine) and the item-23 scoping lessons. Test both directions: match links, non-match doesn't, already-claimed rows untouched, cross-family email collision links both memberships (item 13's two-family case).
- Logged-in user with no membership sees a friendly "no family yet" screen with nothing else (RLS already guarantees zero data; the screen just makes it kind).

## 3. Screens (three, plus login)

1. **Glance ("Today")** — the anxious-moment screen and the demo centerpiece. Per parent: display name, a large calm status — `All normal` (alarm-grade ping seen today), `Quiet so far` (none yet today, before evening), never anything scarier — and "last routine seen {time} local". Auto-refresh (poll 30–60s or Supabase realtime — implementer's choice, note in QUESTIONS). Copy law applies: no counts, no signal names, no trend anything. `Quiet so far` is as dark as this screen ever gets — the ladder owns everything darker, and it isn't in this app yet.
2. **Digests** — reverse-chron list of this family's `digest_sends` rendered as the messages read (recompose from templates by kind + parent + date; do not store message text anywhere new). Empty state: "Your daily digests will appear here."
3. **Family** — parents (name, timezone) and members (name, channel) — read-only roster. Footer line, verbatim: "Kettle stores three things: who, which routine, when. Nothing else exists to show you."

## 4. Demo affordance (founder-only, no product surface)

A `--demo` provisioned family + a member row carrying the founder's email is enough: log in, open Glance, curl a demo ping URL, watch the status flip. Requires nothing built beyond the above — but verify the flow works end-to-end and document the demo script (the exact three commands) in `webapp/README.md`.

## 5. Non-goals

Onboarding wizard, Shortcuts links, family codes (005b). Billing (005b). Ladder UI/alerts of any kind. Settings/editing anything (read-only means read-only). Push notifications. Android/iOS store artifacts. Analytics of any kind (product law #4 — not even "privacy-friendly" ones).

## 6. Acceptance criteria

1. Magic-link login → membership claimed by email → Glance shows exactly the caller's family; a second family's user sees only theirs (re-use the two-family RLS fixtures through the real app's queries — this is the RLS proof at the UI layer).
2. Glance states: parent with an alarm-grade ping today shows `All normal` + correct local time; parent without shows `Quiet so far`; a fresh ping moves the status without reload within the refresh interval.
3. Digest list renders morning/evening entries matching the binding templates; empty state renders for a family with none.
4. Copy law: a test walks rendered output for the three screens — no digits beyond clock times, no signal names, no counts, no urgency vocabulary.
5. No-membership login shows the kind empty screen and zero data.
6. `app_claim_membership` tested per §2 including the two-family email case; advisor-clean after 0008.
7. Static build deploys to Fly (documented in `webapp/README.md`); the served app contains no secret beyond the publishable key (grep the build output for the service key pattern as a test/CI step).
8. CI extended: webapp lint + build must pass (JS tests where the logic warrants — the claim-RPC and glance-state logic at minimum via component/unit tests).
9. Backend suites still green, ruff clean, pilot untouched, no secrets in the diff.
