# Specs

Every spec, one line, and what state it is in. The specs themselves are the
authority on what was asked for; this file exists so nobody has to open thirteen
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
| [006](006-landing-page.md) | Landing page (getkettle.*) | Built. Four passes since (DECISIONS 134–137) are unshipped pending a founder deploy. |
| [007](007-outbound-channel.md) | The outbound channel — Kettle learns to speak | **Wave A built and running dark.** Waves B–D are each gated on one founder errand. Supersedes 003 and 004. |

## What "superseded" means here

The spec file stays, with a banner at the top saying what replaced it. It is
history, and the reasoning inside it is often still the best account of *why*
something is the way it is — spec 004's law-#6 argument for asking the senior
first is the same argument 007's parent-first ordering rests on.

What does not stay is the code. A superseded spec's modules are deleted rather
than left dormant, because a dormant engine with a kill-switch is one flag away
from speaking at the same family twice.
