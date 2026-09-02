# Kettle feature backlog (seed)

Status: SEED, 2026-09-02. Sections 1 to 3 hold only ideas already on
record elsewhere in this repo, each with its source. Section 4 is empty
on purpose: it is filled by a separate creative session (brief in §0).
Nothing here is a decision. A backlog item becomes real only when it is
allocated a DECISIONS number or a spec.

Organizing question for every item: which of the three numbers does it
move, and by what mechanism?

- ACQUIRE: gets a family who has never heard of Kettle to the site or
  to a conversation.
- CONVERT: swings a family that is comparing us with doing nothing, a
  location app, a pendant, or "Parents Are OK".
- RETAIN: keeps a paying family paying past month 3, when the novelty
  is gone and nothing has happened to Mom.

Item format: `[A|C|R] Title. Mechanism (one line). Size S/M/L. Law
check: clears / needs LAW-n reopened. Source.`

## 0. Brief for the creative session (paste this whole file in)

You are doing a creative pass on Kettle's feature backlog. Kettle is a
passive peace-of-mind service for adult children with aging parents at
a distance. It watches for the normal morning thing happening (phone
picked up, a routine tap) and, when the morning is not as usual, asks
the parent first on WhatsApp ("Is everything okay? Reply with a 👍")
before anyone in the family is told. The family sees "all's well" and
nothing more. Payer is always the adult child. Founding rate
$10/parent/month; public price $20 to 25. Stage: founder's own parents
live on it; paid beta of 5 to 10 friend families next; then public.

Product laws in force (§5). You MAY propose items that break one, but
you must say which law, why it is worth reopening, and what the honest
version of the feature is if the law stands. Tag those "needs LAW-n
reopened". Do not propose anything that requires reading message
content, tracking location, inferring health or decline, or making the
parent do a daily chore for the family's comfort. Those are not laws,
they are the product.

Produce 30 to 60 items in the format above, sorted into §1 to §3, and
put them in §4 under "Creative pass, unreviewed, <date>". Prefer items
that are specific enough to size. For each, name the mechanism: not
"builds trust" but "a fence-sitter can see a real week of all's-well
before paying". Then give a top-10 with one sentence each on why.

## 1. ACQUIRE (already on record)

- [A] Resource library and guides (printable "okay living alone",
  "normal day", changes tracker, emergency info). Search doorway for
  adult children; Kettle only at the end. Size done/ongoing. Clears.
  Source: DECISIONS 198, docs/asset-*.md.
- [A] Blog series in writer voice (posts 1 to 6 drafted). SEO doorway
  plus shareable in WhatsApp family groups. Size ongoing. Clears.
  Source: docs/blog-post-*.md, docs/kettle-blog-voice-rules (memory).
- [A] Waitlist referral loop. Existing waitlist family invites another.
  Size S. Clears. Source: docs/gtm-roadmap.md (channels).
- [A] NRI / eldercare subreddits, WhatsApp groups, temple and community
  orgs as channels. Size ongoing, founder time. Clears. Source:
  docs/gtm-roadmap.md. Note: "no reddit" is a current founder rule for
  PM activity, not a channel kill.
- [A] Free "Phone Watch" tier, device-liveness only. A no-cost first
  rung that still delivers a daily all's-well. Size M. Clears. Source:
  docs/gtm-roadmap.md, founder decision Jul 31.
- [A] Android parent app (foreground service, first-unlock-of-day,
  per-OEM onboarding). Opens the half of the market whose parent is
  not on iPhone. Size L. Clears. Source: docs/android-signals-brief.md,
  docs/gtm-roadmap.md Wave 2, Asana 1216997773231871.
- [A] Responder partnerships in India (Emoha, Samarth, Yodda) as a
  channel, not a signal. Size L, BD. Clears. Source:
  docs/signal-expansion-ideas.md §5 C-j, docs/gtm-roadmap.md.
- [A] X / TikTok drafts via the AI-writers brief. Size S. Clears.
  Source: docs/kettle-brief-for-ai-writers.md (open on founder).

## 2. CONVERT (already on record)

- [C] Beta un-gated from TestFlight; PWA install from the site. Removes
  the app-store wall at the moment of decision. Done. Clears. Source:
  kettle-design-direction (memory), spec 005a/008.
- [C] Design 1+2 mash-up: kettle-ring states plus honest cards. The
  first screen answers "is she okay" in one glance. Done. Clears.
  Source: docs/design-language.md, spec 009.
- [C] Animated kettle hero on the homepage. Size M. Clears. Source:
  Asana 1217835128977059.
- [C] Homepage sweep: OFF_NOTIF to the v7 sentence with a sample name;
  "ordinary" to "normal". Size S. Clears. Source: Asana
  1217831042637424, DECISIONS 225.
- [C] Savviness-branch onboarding variant (parent's phone comfort
  level changes the setup path). Size M. Clears. Source: docs/PLAN.md
  Q109.
- [C] Per-parent native-language ask (non-English). Widens who can be
  the parent. Size M. NEEDS LAW-5 (English-only surfaces) reopened.
  Source: DECISIONS 150, kettle-founder-rulings (memory).
- [C] SMS fallback transport (spec 011 amendment; 10DLC approved
  2026-09-02). Parent without WhatsApp is no longer a lost sale. Size
  M. Clears. Source: DECISIONS 226 to 230.
- [C] Timezone edit for a cross-border parent. Size S. Clears. Source:
  docs/PLAN.md Q108, spec 010.

## 3. RETAIN (already on record)

- [R] Family Memory / journal v1.1 (first-reply line, what-never-how).
  Gives the family something to look back on when nothing happened.
  Shipped. Clears. Source: spec 012, DECISIONS 200 to 203.
- [R] Photos on the family Memory. Size M. Clears (photos are family
  content about the family, not parent content; confirm). Source:
  journal task standing review, phase 2/3.
- [R] Message-history screen (purpose-built view, not the raw ledger).
  Size M. Clears. Source: DECISIONS 156, post-beta.
- [R] Multi-family tier: per-recipient fan-out, aggregated evening
  digest, staged escalation family_1 to family_all, per-parent
  thresholds, max_gap as second daytime trigger. Size L. Clears.
  Source: DECISIONS 157, 169.
- [R] Per-member note toggles and invites; add-a-parent flow. Size M.
  Clears. Source: DECISIONS 157, 169 (blocked behind onboarding pause
  Q126).
- [R] Multi-account family circle plus MCP read access. Siblings each
  with their own login; an assistant can ask "how was Mom's morning".
  Size L. Clears. Source: Asana 1218034241842672, gtm-roadmap Wave 1
  "explicitly OUT".
- [R] Per-parent view of the Contacts card (schema already nullable; a
  filter, not a migration). Size S. Clears. Source: DECISIONS 202.
- [R] Corroborating signals, each admitted only as (who, signal,
  timestamp): app-open ping, charger event (48h, never co-primary),
  local Zigbee fridge-door sensor (no vendor cloud), alarm-dismissed
  (bench test first). Fewer false "not as usual" mornings means fewer
  annoyed parents and fewer cancellations. Size M each. Clears (each
  passed adversarial review). Source: docs/signal-expansion-ideas.md
  §3 S1, S2, S3, C2.
- [R] Consented sender-owner WhatsApp good-morning message as a
  check-in (parked, unreviewed). Size M. Law check unresolved.
  Source: docs/signal-expansion-ideas.md §4 F1 successor.
- [R] Routine-discovery (learn the parent's actual morning window
  instead of a configured one). Parked. Size L. Clears if it stores
  only timestamps. Source: docs/PLAN.md.
- [R] Native parent app as the device_alive home (replaces Shortcut
  fragility). Size L. Clears. Source: docs/PLAN.md Q107.
- [R] Acuity tiers; paid responder integration (premium). Size L.
  Clears. Source: docs/gtm-roadmap.md Wave 1 "explicitly OUT".

## 4. Creative pass (unreviewed)

Empty. Filled by the separate session per §0. Keep the date on each
batch. PM reviews; founder allocates DECISIONS numbers for anything
promoted.

## 5. Product laws (numbered here for tagging only)

- LAW-1 Admission rule: every signal reduces to (who or household,
  signal_name, server_timestamp). Nothing else enters.
- LAW-2 No content, location trail, health or body data, counts, or
  trend/series anywhere family-facing. No decline, dementia, or
  diagnostic inference or claim, ever.
- LAW-3 Payer is the adult child. The parent never pays and is never
  the account owner.
- LAW-4 Parent first: when the morning is not as usual, the parent is
  asked on their own phone with a grace period before the family is
  told. 👍-or-silence; no buttons; no daily chore for a healthy parent.
- LAW-5 English-only human-facing surfaces (founder ruling).
- LAW-6 No consent ceremony, ever (founder ruling). Consent posture
  lives in setup copy and the 10DLC verbal script, not a screen.
- LAW-7 Copy laws: what-never-how; no verdicts, counts, gendered
  pronouns, em dashes, "monitor", "track", "alert", "elderly",
  "seniors"; "normal" never "ordinary"; "heard from" never "checked
  in" (Kettle-as-actor "check in with" is pinned OK).
- LAW-8 A household-grade signal is never presented as proof that a
  specific person is fine.
- LAW-9 No client-side analytics on the site or app.
- LAW-10 Never scrape WhatsApp "last seen"; no camera, audio,
  keystrokes, or continuous location.

Permanently killed (not backlog): caretaker-log features; original
decline-detection concept (docs/research-synthesis.md); content
quotes and Send-a-note (law-checked out, see design direction).

## 6. Named competitors and adjacents (for the CONVERT section)

Life360, Snug (family safety / location). CarePredict, envoyatHome,
Sensi.AI (in-home hardware). Life Alert, Medical Guardian, Lively
(pendants). Apple Health Sharing / Walking Steadiness, Google
(platform-native). GaitIQ (phone-only, gait/cognition path we rejected).
"Parents Are OK" (direct, live, iterating in public: the competitive
clock). Emoha, Samarth, Yodda (India response services: partners, not
competitors).
