# The setup problem — design brief and session handoff

*PM: Fable, 2026-08-13. Written to end a long session cleanly. **A new session should read this
first, then `docs/onboarding-runbook.md`, then QUESTIONS items 92–102.** Everything below is
either settled fact, a measured finding, or a clearly-labelled proposal.*

---

## 1 The constraint, stated properly

The founder's own family is the design case, and it is deliberately the hard one:

- **The parent cannot be reached physically.** Chennai and Texas; no AirDrop, no hands on the phone.
- **The parent is not tech-savvy**, and in one case hard of hearing, so a phone-call walkthrough is
  degraded before it starts.
- **There is no helper.** A sibling in the house has two small children and no time; "let's do it
  another time" is a decline that never resolves. The founder's stated preference is to need
  nobody's help, and that is the correct product constraint, not a personality quirk: **any design
  that requires a competent third party in the room has a dependency most families cannot supply.**
- **The window is short.** Thirty to forty minutes on a call, once.

Solving this solves nearly every customer. **But it does not test the dimension most likely to
break first:** the founder can run a terminal, and a customer's child cannot. Every path below must
be judged twice — once for "can the founder do this for a family", once for "can the family do this
without the founder".

---

## 2 What the parent actually does today, counted

Per parent, with the current six-signal set:

| Step | Interactions |
|---|---|
| Receive files, tap each → Add Shortcut | ~12 |
| Open each shortcut manually while unlocked, tap Allow | ~18 |
| Build each automation (App → find app → Is Opened → Next → pick shortcut → confirm) | ~48 |
| **Total** | **~78** |

**This is the finding that reframes the problem.** Delivery — getting files onto the phone — is
roughly 15% of the work. The other 85% is automation building, done by the least technical person
in the transaction, over a call, in a foreign app. Optimising delivery alone cannot make this
succeed.

---

## 3 The levers, in order of leverage

### 3.1 Fewer signals (available today, no code)

`charge_on`, `charge_off` and `device_alive` are corroborating-only: under product law #6 they can
never stand in for a person. Their contribution to reassurance is zero by construction; they exist
for equipment health and future corroboration. **For a low-tech parent, two app signals are most of
the value at a third of the work.** Costs: thinner tripwire health, no device-liveness alert.

### 3.2 One automation covering several apps (proposal — verify first)

iOS's "App is opened" automation appears to accept **multiple apps in one automation**. If so, one
automation watching WhatsApp + YouTube + anything else, firing **one** shortcut, replaces six.
Setup collapses from ~78 interactions to roughly a dozen.

The trade-off is real and worth stating plainly: we would know *her routine happened*, not *which
app*. Consequences —

- **Product law: neutral-to-better.** We record who, signal, when; the signal simply becomes coarser
  (`routine` rather than `whatsapp`). Less is stored about her, not more. The digest language never
  named apps anyway.
- **Tripwire health gets coarser.** We could no longer say "her WhatsApp tripwire needs attention",
  only "her routine tripwire has not reported". The 005d repair surface would need rewording, and
  ruling 61 (the app names what the phone names) still applies.
- **Threshold work loses per-app granularity**, which the parked routine-discovery design wanted.

**This is the single highest-leverage open question in the product right now.** Verify on a real
iPhone before designing around it.

### 3.3 Delivery (the part the founder asked about)

Assessed today, worst to best:

| Route | Verdict |
|---|---|
| AirDrop | Only works in the same room. Not applicable. |
| Paste `.shortcut` into WhatsApp | **Fails.** WhatsApp does not accept the type by paste. |
| WhatsApp Web → paperclip → Document | **Works**, and is the beta answer. Needs no desktop app. |
| Email attachments | Works; risk of provider filtering, and Mail may not be a channel the parent uses. |
| iCloud Drive share link | Works; adds a Files-app hop for the parent. |
| Import to founder's Mac Shortcuts → iCloud links | **Refused.** The library is a flat namespace with no family scoping and it syncs to the founder's own devices — one family's shortcuts become indistinguishable from another's (this actually happened, QUESTIONS 101). Standing rule: **signed shortcuts never enter the founder's Shortcuts library.** |
| **Hosted per-parent setup page** | **The proposal.** See §4. |

---

## 4 The proposed end state

**The family never handles files.** Provisioning emits one **per-parent setup URL** on our own
domain — unguessable, expiring, revocable — carrying that parent's shortcuts as tappable links plus
the instructions in plain language. The child app shows two labelled links ("Mom's setup", "Dad's
setup"); the child forwards the right one to the right parent. One link, one parent, nothing to
cross, no attachment a mail provider can strip, no filename anyone has to interpret.

Security posture: that URL *is* the device token in transit, so it inherits the token's rules —
unguessable, expiring, revocable.

---

## 5 The two cheap experiments that decide most of this

1. **Does iOS open a `.shortcut` served over HTTPS straight into the Add Shortcut sheet?** With the
   correct content type it plausibly does. If yes, Apple's iCloud sharing is unnecessary and
   delivery becomes a URL. *Ten minutes, any host, a rehearsal file.*
2. **Does one App automation accept multiple apps?** *Two minutes on the founder's own phone.* This
   is worth doing before anything else in this document.

A third, lower priority: **can signing run without a Mac in the loop** (`shortcuts sign` is
macOS-only)? Either a macOS runner signs at provisioning, or files are signed in batches ahead of
demand. The hosted-link design does not remove this constraint; it moves it off the critical path
of a call.

---

## 6 Bounds — what a solution may not do

- Three fields only: who, signal, server timestamp. Nothing else is stored (law #2).
- No decline/health inference of any kind (law #1).
- Household- and device-grade signals never speak for a person (law #6).
- The parent consents per person, and always holds the kill switch. **No design may assume the
  child talks the parent into it** — the founder's beachhead ruling (GTM, 2026-08-13) says
  resistance is a qualification signal, but the consent itself remains genuine and per-person.
- Nothing typed by a parent. Tokens are never entered by a human.

---

## 7 State of the world at handoff

**Live:** `kettle-api.fly.dev` (product backend), `kettle-app.fly.dev` (child PWA),
`kettle-site.fly.dev` (landing page, pre-Amendment-B build), `kettle-pilot.fly.dev` (pilot, idle,
leave alone until the Day-30 memo).

**Families provisioned in production:** Suryaprakasam (Amma, Appa — provisioned, shortcuts forged
and signed, **not yet delivered**), Rehearsal (TestDad, TestMom — complete and verified end to end,
both reporting), Patel (imaginary walkthrough family; forged, never to be delivered).

**Proven working end to end:** provision → forge → sign → install → unlocked first run + Allow →
automations → ping → card turns green, across two devices and two continents, with correct
per-parent timezones.

**Owed by the founder, unrelated to this brief:** migration 0009 and `WAITLIST_ORIGINS` on
kettle-api (the landing page cannot collect signups until both), a site redeploy for Amendment B,
NC annual reports for LinkAbit, and the WhatsApp display name (rejected twice as "Kettle"; parked
with the naming question).

**Queued for Claude Code:** QUESTIONS 93 (forge derives output path from token), 94 (`provision
--signals`, plus an "adding a signal" procedure), 95 (`--add-device` / `--rotate`), 100 (replace
`news`, make the seeded set platform-aware), 101 (filename carries the person; plist name does
not), 102 (this brief's delivery design, for spec 005b).

**Not yet written:** spec 005b. It should be written *after* the two experiments in §5, because
their answers change its shape substantially.

---

## 8 Recommendation

1. **Run experiment §5.2 first** — two minutes, and if multi-app automations work it changes what
   005b is for.
2. **For the founder's parents this week, do not wait for any of this.** Use WhatsApp Web with
   document attachments, and cut to two or three signals rather than six. Tomorrow's call is a
   deadline, not a design input; ugly and done beats elegant and pending.
3. **Write 005b after the experiments**, with delivery and setup-minimisation as its spine rather
   than as details — this session established that the wizard's job is removing interactions, not
   decorating them.
