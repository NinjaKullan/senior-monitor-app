# Spec 005b — Family onboarding: delivery and setup without the founder

*PM: Fable, 2026-08-15. Written from the Amma field log (QUESTIONS 103–107) and the setup
brief (`docs/setup-delivery-brief.md`). One fork remains open — §5.1, marked below — and it
changes only the delivery mechanics, not the shape. Everything else here is decided.*

## 1. What it is

The path by which a family that is not the founder's goes from "child has an account" to "both
parents' cards are live", with no founder, no terminal, and no competent helper assumed. Two
surfaces:

- **The child wizard** (in the child app): provisions parents, chooses signals, and emits one
  labelled setup link per parent — "Mom's setup", "Dad's setup". The child forwards the right
  link to the right parent. The child never handles files (QUESTIONS 102).
- **The parent setup page** (hosted, per-parent URL on our domain): everything the parent (or
  the person helping them) sees. Unguessable, expiring, revocable — the URL carries that
  parent's shortcuts, so it *is* the device token in transit and inherits the token's rules.

The measured finding this spec exists to answer: delivery is ~15% of the parent's work and
automation-building is the rest, done by the least technical person in the transaction
(brief §2). So the wizard's job is **removing interactions, not decorating them**.

## 2. Design laws, from the field

1. **Merged method is the default** (QUESTIONS 107, 109): per parent, two shortcuts and two
   automations — `routine` (one App automation, multiple apps, one shortcut) and `charger`
   (Is Connected + Is Disconnected, one automation). Per-app is the opt-in path for a parent
   the child says is comfortable with their phone. Target arithmetic at the floor: 2 taps to
   add, 2 unlocked first runs, 2 automations.
2. **Step zero is the Shortcuts app** (QUESTIONS 103). The page's first screen checks-by-asking
   ("Do you see this icon?") with the App Store link right there. Never assume the app exists.
3. **Nobody reads** (QUESTIONS 106). One visual per step, one short paragraph maximum, speech
   bubbles over prose. Every screen answers "what do I tap next", nothing else.
4. **Remote eyes are a first-class assist** (QUESTIONS 104). The page works when the person
   reading it is not the person holding the phone: a "helping someone else?" toggle reorders
   copy for a camera-over-FaceTime session. The no-helper goal stands for the median parent;
   the floor gets this without shame.
5. **Run Immediately, always** (QUESTIONS 107). Both automation screens show the toggle
   explicitly; Run After Confirmation is a dead automation on a parent's phone.
6. **The scary prompt is pre-empted** (QUESTIONS 99). The screen before first run shows
   Apple's warning verbatim with "your phone will ask this; here is why it is safe".
7. **Consent is carried by the product, not the call** (QUESTIONS 106). The page opens with
   the consent one-pager in plain language — what is recorded (who, which signal, when), what
   is never recorded, who sees it, how it stops — and the parent's kill switch is shown, not
   described. When a helper drives the phone, this screen is the consent conversation's floor.
8. **Verification is prediction** (runbook §8, QUESTIONS 92). The final step: "open WhatsApp
   now" with a live green check on the page confirming the server saw the ping. That single
   step is simultaneously the item-92 permission grant (unlocked, before automations arm) and
   the crossed-files detector — one URL, one parent, nothing to cross by construction.

## 3. The fork — RESOLVED (QUESTIONS 117, 2026-08-16)

The experiment ran on-device: all three content types (`application/x-shortcut`,
`application/octet-stream`, `application/x-apple-shortcut`) produce Safari's download prompt,
never the Add Shortcut sheet, and the downloaded file buries itself in a Files app the floor
parent has never opened (field log, 2026-08-16). The Files-app hop was ruled a failure at the
floor. Therefore:

- **Files travel by WhatsApp document attachment** — field-proven on the first live install.
  The setup page's "send the buttons" step for the child opens a WhatsApp share; the parent
  receives the two shortcuts as documents in a conversation they already live in, and taps
  each → Add Shortcut (the proven path).
- **The page never serves a `.shortcut`.** It carries consent, the visual steps, the
  pre-empted warning, and the live verify check — the things only it can.
- iCloud link generation stays rejected (programmatic sharing unsupported; QUESTIONS 101/102
  standing rule).

Signing itself is unchanged either way: `shortcuts sign` is macOS-only, so a macOS runner
signs at provisioning, or files are signed in batches ahead of demand. Off the call's
critical path; not this spec's problem to solve, only to consume.

## 4. Requirements

1. Provisioning emits per-parent setup URLs; child app shows them as two labelled
   forward-ready links (WhatsApp share intent first).
2. Setup URL: unguessable (≥128-bit), expiring (default 7 days), revocable with the device
   token, single-parent scoped. Revoking the token kills the URL.
3. Page sequence: consent → step zero (Shortcuts check) → add shortcuts (2) → unlocked first
   run + Allow (2, warning pre-empted) → build automations (2, Run Immediately shown) →
   verify by prediction (live green check) → done card ("what happens now").
4. Helper toggle per §2.4; copy in the family's language is out of scope for v1 but the copy
   file structure must not preclude it.
5. Signals chosen in the wizard from the parent's actual habits — the load-bearing question
   ("which apps do you open every day without thinking?") is asked of the child, with the
   browser-signal consent sentence when applicable (QUESTIONS 94 note). Financial apps
   excluded at every tier, permanently.
6. Nothing typed by a parent, ever. No tokens visible anywhere on the page.
7. Laws hold: three fields stored, no decline inference, household signals never speak for a
   person, per-person consent with visible kill switch.

## 5. Acceptance criteria

1. A rehearsal family runs end-to-end from a fresh child account to two green cards with the
   founder's hands off the keyboard after provisioning.
2. Parent-side interaction count ≤ 12 taps from opening the link to verified (merged method,
   Shortcuts already installed); every tap enumerated in the spec's test script.
3. Expired and revoked URLs serve a plain-language dead-end with the child's contact path,
   never a file.
4. The verify step demonstrably catches a crossed pair (test: swap two rehearsal URLs,
   confirm the named-card check fails loudly).
5. Field-noted: first stranger family's install produces a numbered QUESTIONS block, same as
   the founder's own.

## 6. Non-goals

Routine discovery; Android (Q100); timezone edit (Q108) beyond displaying the provisioned
timezone; digest channel setup; the savviness branch beyond the single merged/per-app choice
(Q109 v2); native parent app (device_alive stays off the critical path per Q107).
