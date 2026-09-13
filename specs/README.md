# Specs

Every spec, one line, and what state it is in. The specs themselves are the
authority on what was asked for; this file exists so nobody has to open two dozen
of them to find out which ones still describe the product.

`DECISIONS.md` is the decision log and the PM channel — the next number is the
line at its top. Items 1 through 120 are in `DECISIONS-archive.md`.

| Spec | What it is | Status |
|---|---|---|
| [001](001-pilot-backend.md) | Pilot webhook backend — the two-phone Chennai pilot | Built. Superseded in practice by 002's multi-tenant core; kept as the record of what the pilot was. |
| [001a](001a-device-alive-timer.md) | `device_alive` timer signal, an amendment to 001 | Built. The signal is live and corroborating-grade. |
| [002](002-multitenant-core.md) | Product backend: families, parents, devices, RLS | Built. The core everything else stands on. |
| [003](003-digest-engine.md) | Digest engine — the two daily messages | **Superseded by 007** (DECISIONS 141). Engine and copy retired; `digest_sends` survives because the family app reads it. |
| [004](004-ladder-v1.md) | Escalation ladder v1 — senior-first, shadow by default | **Superseded by 007** (DECISIONS 141). Engine, copy, CLI and the `/twilio/inbound` webhook retired; its tables dropped or archived by migration 0013. |
| [005a](005a-child-pwa-demo.md) | Child PWA, demo-grade, read-only | Built. The family app's first form. |
| [005b](005b-family-onboarding.md) | Family onboarding: delivery and setup without the founder | Built and PM-approved. Onboarding-surface investment is founder-PAUSED (DECISIONS 126). |
| [005b-copy](005b-copy.md) | The setup page's keyed copy deck | PM-authored. The built page predates it; reconciling the two is queued behind the same pause. |
| [005c](005c-glance-warmth.md) | Glance warmth pass | Built. |
| [005d](005d-tripwire-health.md) | Tripwire health panel | Built. Carries the app's one scoped copy-law exemption. |
| [005e](005e-shortcut-forge.md) | Shortcut forge — generate and sign real `.shortcut` files | Built. Signing is a macOS founder step; generation runs anywhere. |
| [006](006-landing-page.md) | Landing page (heykettle.com) | Built and live, behind Cloudflare's proxy since Sep 6 (DECISIONS 306); the SEO pass of Sep 12–13 is live (332). The spec says getkettle.* throughout; the domain changed after it was written (142). |
| [007](007-outbound-channel.md) | The outbound channel — Kettle learns to speak | Built and live through Wave D (DECISIONS 263): digests and follow-ons by email, the ask to the parent on WhatsApp from the registered number on the v7 template, the all-clear. Supersedes 003 and 004. |
| [008](008-webapp-restyle.md) | The webapp wears Kettle v5 | Built and live (DECISIONS 170). |
| [009](009-glance-redesign.md) | Glance redesign: Today, parent detail, family notes | Built and live (DECISIONS 176–181). Amended in practice by 299 (a day counts from 06:00 local) and 303 (night is not quiet). |
| [010](010-city-timezone.md) | The city is the timezone: moving a parent | Built and live (DECISIONS 185); the city control's current form is the button pass's (324–327). |
| [011](011-wave-d-real-number.md) | Wave D: the real HeyKettle number | Built and flipped Sep 4 (DECISIONS 263). v7 is the ask and template iteration is stopped (253/262). The sandbox sunset needs its own ruling. |
| [011 A](011-wave-d-real-number.md#amendment-a-2026-09-02-sms-transport-for-1-parents) | Amendment A: SMS for +1 parents | Built and live (DECISIONS 291–294); dark stage complete on TestMom (310), so a real +1 parent may be enrolled by text. Amma stays on WhatsApp. |
| [012](012-family-memory.md) | Family Memory: the journal becomes a place | Built and live, v1.1 (the filter, the scrolling card, "Who to call") included (DECISIONS 202/214); in daily use (327). |
| [013](013-email-code-sign-in.md) | Sign in with a 6-digit email code | Built and live (DECISIONS 283). |
| [014](014-android-senior-app.md) | Android senior app (the phone's voice) | Server side built (§6 items 1, 2, 4, 5; DECISIONS 330/331), migration 0033 applied, product deploy owed. The app lives in `android/`; the Xiaomi soak (§8.1) waits on the Redmi 15C. Held: the setup page's Android branch (§6.3, until the Play listing exists) and the runbook section (§6.7, after the first real install). |
| [015](015-circles.md) | The circle: who sees a household, and who can change it | Built and live (DECISIONS 270/283). |
| [016](016-replies.md) | Replies on a note | Built and live (DECISIONS 275/283). |
| [017](017-pause.md) | Pause Kettle for one parent | Built and live (DECISIONS 276/283). |
| [018](018-notes-edit-delete.md) | Notes: edit, delete, the optimistic composer, viewer-zone dates | Built and live (DECISIONS 281/283). |
| [019](019-mcp.md) | Ask Kettle from an assistant (read-only MCP) | Built and live (DECISIONS 285–288); Claude and Codex both connected. CIMD works through a shipped copy of Claude's client document (319–321). |
| [019 A](019-mcp.md#amendment-a-2026-09-08-notes-and-replies-through-the-assistant) | Amendment A: notes and replies through the assistant | Built and live (DECISIONS 317/318/322/323): `add_note` and `reply` behind the `kettle:write` scope, lines marked "{name} via {client}". |
| [020](020-household-devices.md) | The family's own devices (a recorded fact, never a judgement) | Built and live (DECISIONS 313–315). Nothing a device says feeds the engine. |

## What "superseded" means here

The spec file stays, with a banner at the top saying what replaced it. It is
history, and the reasoning inside it is often still the best account of *why*
something is the way it is — spec 004's law-#6 argument for asking the senior
first is the same argument 007's parent-first ordering rests on.

What does not stay is the code. A superseded spec's modules are deleted rather
than left dormant, because a dormant engine with a kill-switch is one flag away
from speaking at the same family twice.
