# Kettle — Go-to-Market Roadmap

*PM: Fable. Written Jul 28, 2026, day after YC submission. Goal: 100–200 paying families. Competitive clock: Parents Are OK is live and iterating in public; the YC RFS wave lands in the fall.*

## Strategy in one paragraph

Launch iPhone-parent families first, because they need no senior-side app: Shortcuts + a child-side PWA + WhatsApp/SMS is the whole stack, there is no app-store review anywhere in the critical path, and it is exactly what the live pilot already proves. Android (the bigger market) follows as Wave 2 once the senior app clears Play review and the OEM soak test. Charge from day one at a founding-family price — the RosterPro lesson. The family pilot keeps running; its Day-14 threshold math and Day-30 gates become launch configuration, not launch permission (reasoning in §5).

## Wave 0 — This week (while pilot Phase 1 runs)

| Item | Owner | Notes |
|---|---|---|
| Dad's phone + signed one-pager (Tue) | Hema | Pilot milestone, unchanged |
| Domain + landing page + waitlist | Hema + Fable (copy) | Waitlist asks THE question: "What phone does your parent use?" — this decides Wave 2 priority with data |
| Trademark quick-check on "Kettle" / fallbacks (Kettle Care, HeyKettle) | Hema (1 hr) | Working name is fine; know the collision landscape before spending on brand |
| WhatsApp Business API application (Meta business verification) | Hema | START NOW — verification lead time is days-to-weeks and it's on the critical path for the digest + senior ask |
| Stripe account | Hema | Payments from customer #1 |
| Spec 002: multi-tenant backend | Fable | See §3. Claude Code builds while pilot collects |
| Beta recruit list: 10 friend families, iPhone parents preferred | Hema | From your network + eldercare communities (genuine participation, not spam) |

## Wave 1 — Weeks 1–4 (target: closed beta ~Aug 18, first paying strangers ~Sep 1)

**Product scope (specs 002–005, in order):**

- **002 Multi-tenant core** — accounts, families, parents, devices, per-device tokens, per-family timezone. Supabase (Postgres + auth + RLS): founder already ships on it, and row-level security is the honest multi-tenant answer to the privacy promise. Ingestion endpoint stays API-compatible with the pilot's Shortcuts URLs.
- **003 Digest engine** — the two daily messages (morning "day started normally", evening summary), coarse language only per PLAN's digest decision. Delivery: WhatsApp template if API approved, else SMS (Twilio) at launch, WhatsApp when approved.
- **004 Ladder v1** — personal-baseline thresholds (seeded from pilot Phase-1 percentile method), senior-first ask via WhatsApp/SMS with reply, grace period, then family escalation in configured order. Local-responder rung ships as "family's named contact" (neighbor/relative); paid responder partners are post-launch.
- **005 Child PWA** — onboarding wizard (the FaceTime script productized: consent one-pager generation, routine-discovery quiz, Shortcuts walkthrough with screenshots/video per iOS version), the glance view ("all normal"), family-circle management, billing. PWA + Capacitor later if stores matter.

**Explicitly OUT of Wave 1:** Android senior app, trend anything, MCP endpoint, acuity tiers, fridge sensors, paid responder integration, native app stores.

**Beta plan:** 5–10 friend families at $10/mo founding rate (not free — payment is the retention signal), founder-assisted onboarding on purpose (every stumble = wizard improvement), success = a family reaching day 14 with zero founder intervention and zero false family escalations.

## Wave 2 — Weeks 5–10 (public, Android, scale to 100–200)

- Public launch to waitlist at $20–25/parent/mo; founding rate honored.
- **006 Android senior app** — first-unlock signal, foreground service, per-OEM onboarding; the ₹7k Xiaomi 30-day soak test starts the day Wave 1 beta opens (it runs in parallel, zero cost to timeline).
- Growth channels, in order of founder-authenticity: the eldercare/NRI subreddits (share pilot results as a builder, not ads), NRI WhatsApp groups and community orgs (temple/cultural associations — the founder can walk in as a member), waitlist referrals ("add your sibling free" is built-in virality), Parents Are OK's own gaps (their users asking for escalation/digest features they don't have).
- Emoha/Samarth/Yodda partnership conversation — needed for the premium tier, not for launch.

## §3 Architecture evolution (spec 002 grounding)

Pilot stays untouched on its own Fly app until Day 30 — it is a YC-evidence instrument. Product backend is a fresh deployment: Supabase (auth/DB/RLS) + the FastAPI ingestion/digest/ladder service on Fly. Pilot code carries over: signal allowlisting, UTC/IST discipline, dedupe, heartbeat pattern, alarm-grade separation — all of it already reviewed and tested. What changes: Postgres, per-device tokens, per-family config, and jobs (digest scheduler, ladder engine) built multi-tenant from day one.

## §4 Non-negotiables that survive the speed-up (product law, unchanged)

Three fields per event. No content, location, health, counts, or trends anywhere family-facing. Senior-first ask before any family alert. Household-grade never proves a person (law #6). Every family gets the consent one-pager; the senior always has the kill switch. Privacy policy + FTC HBNR posture written before the first stranger pays.

## §5 Why we're not waiting for the Day-30 gates (decision record)

The gates were designed when the concept itself was unproven. Since then: Parents Are OK proved category demand with paying users; the Reddit demand research replicated it; the pilot's mechanism already works end-to-end on a real parent's phone. Remaining pilot value is threshold tuning (G2/G3) and consent design (G4) — which feed launch *configuration* (Phase-1 percentile math seeds every customer's baseline; Dad's redlines seed the consent flow). If a gate fails hard at Day 30, we stop onboarding and fix before scaling — the beta is small enough to pause. Building in parallel risks ~3 weeks of Claude Code time; waiting risks the market.

## Founder feedback, Jul 28 (decisions + onboarding findings)

**Wave-0 status:** Stripe ✅. Landing page Thursday. Dad's phone + signing Friday. WhatsApp Business API: Hema, separate session. Name FINAL: Kettle, domains getkettle.* — no further ideation. Beta recruiting starts only once the child app is on TestFlight → child PWA gets a Capacitor wrap + TestFlight distribution in Wave 1 (RosterPro playbook).

**Onboarding findings (from founder's own setup error — the `curl "` paste bug):**
1. Zero free-text-fields principle: seniors/children never type or paste URLs. Pre-built shortcuts delivered as iCloud links ("Kettle — Mom WhatsApp"); automation wrapper selects the existing shortcut, no action search, no paste. → spec 005.
2. Path-style readable ping URLs (`/p/<family-code>/<who>/<signal>`) alongside query-param route. → spec 002.
3. Wizard verifies by server-side proof: "open WhatsApp now" → green check only when the ping lands. Setup is done when the server says so. → spec 005.
4. Apple's periodic "N automations ran" notification cannot be suppressed: handled by expectation-setting (consent script line + senior-facing "what your phone will show you" one-pager) + heartbeat detection with child-facing repair flow. → spec 005 content.
5. Any elder, not just parents (founder, Jul 29): families add unlimited monitored loved ones (grandparent, aunt, uncle) at per-person pricing — schema already supports it (spec 002 parents table is unbounded, per-person tz/signals/devices). Invariants: consent flow runs per person (no silent adds, ever) and each elder gets their own baseline + ladder. Product copy says "loved ones."
6. Token delivery: tokens are never typed by humans. Delivery = pre-built shortcut via tapped iCloud link or QR scan. Apple can't mass-generate per-family iCloud links, so: beta = semi-manual per-family shortcuts; scale = one universal shortcut with an Apple "import question" asking for a short checksummed family code (e.g. KETL-7Q4M), entered once by the child. Wrong token → silent 403, no data pollution; wizard verification (screen C) surfaces any failure in seconds. Tokens are per-device (spec 002) so a lost phone is a one-tap revoke. → specs 002/005.

## §6 Risks worth naming

1. **WhatsApp Business verification lag** → SMS fallback specced from day one.
2. **Onboarding is the product.** If a stranger can't set up Shortcuts remotely with our wizard, nothing else matters. Beta exists to grind this smooth; measure setup-completion rate and time.
3. **Support load at 100+ families on a solo founder** → heartbeat-driven proactive support (we detect their broken Shortcut before they do) is both the product and the support strategy.
4. **"Private server" promise vs multi-tenant reality** → the pilot one-pager's wording was pilot-specific; the product privacy policy says the true thing (isolated per-family data, RLS-enforced, we can't read content because none exists). Never reuse the pilot one-pager verbatim for customers.
5. **Trademark collision on Kettle** → check before buying brand assets.
