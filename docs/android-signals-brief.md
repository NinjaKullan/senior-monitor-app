# Android parents — signal-source options brief (PM, 2026-08-31)

The question: what has to exist before a family whose parent carries
an Android phone can join Kettle. Asana: W2 "Android senior app +
Xiaomi soak test" (1216997773231871). This brief ends in a
recommendation and the founder decisions it needs.

## The gap, precisely

Kettle's parent-side needs two things. The ASK channel is WhatsApp —
already universal, nothing to do. The MORNING SIGNALS are the gap:
today they ride iOS Shortcuts automations pinging kettle-api
(charger/routine vocabulary), and Android has no Shortcuts. An
Android parent is a phone Kettle never hears from: every morning
reads as quiet, the ask rung fires daily, and the product's promise
("asks nothing of them" — the ask is the EXCEPTION) inverts. So this
is beta-gating: no Android-parent family can join honestly today.

## Options

**A. Off-the-shelf automation app (MacroDroid / Tasker).** The kid
installs one on the parent's phone and recreates the ping
automations; kettle-api needs nothing new (it already accepts any
HTTP client). Cheap to try; zero code. Against: setup is a
20-minute technical ritual per phone in an app built for tinkerers;
Chinese/Korean OEMs (Xiaomi, Oppo, Samsung) kill background
automation unless battery-optimization exemptions are hand-set per
OEM menu; every OEM update can silently break it; and a stranger's
family is being told to install a third-party automation tool with
broad permissions — a trust problem Kettle can't fix. Verdict:
acceptable for ONE pilot family we hand-hold; wrong as the product
answer.

**B. Minimal native senior app (RECOMMENDED).** A small Android app
whose only job is to be the phone's voice: it sends the same pings
the Shortcuts send, from the same vocabulary, and nothing else. Kid
installs and signs it in via the existing setup_links flow; the
parent is asked NOTHING ever after (elder-proof = invisible).
Signal sources, all content-free: charger connect/disconnect
broadcasts, first-unlock/user-present count for the day (the phone
WOKE — never which apps were used; app-usage tracking is
surveillance-shaped and stays out, whatever it would buy), and the
significant-motion / step-count sensor as a third voice (see the
motion section). Engineering posture: WorkManager + system
broadcasts, one battery-exemption prompt at setup with per-OEM
guidance, and the **Xiaomi soak test as the acceptance gate** — the
backlog task already names the right bar. Costs: $25 one-time Play
account, CC-buildable (Kotlin), one more artifact to maintain.

**C. PWA on the parent's phone.** No reliable background execution
exists for web apps on Android; a PWA can't be a passive signal
source. Dead end for this purpose; recorded so nobody re-walks it.

**D. WhatsApp-only degraded mode.** Let Android-parent families
join with no morning signals at all. Every morning would be quiet
→ daily asks → the inverted product. Reject for now; revisit ONLY
if spec 013 (kids own the ask) ships and a family knowingly chooses
"ask-anchored" coverage — that is a different, lesser product and
must never be the silent default.

## The motion question (founder idea, 2026-08-31)

Proposal: the senior app detects whether the phone MOVED that day —
no location, just movement — as (a) a signal in its own right and
(b) double coverage for iPhone users whose Shortcut got turned off.

**PM verdict: yes to (a), honest no to (b) — with a better answer
for the iOS worry.**

- **(a) On Android, in the native app: adopt.** The significant-
  motion sensor and the day's step-count delta are exactly the kind
  of signal Kettle already speaks: content-free, passive, what-
  never-how ("the phone moved today", never where, never a count
  shown to anyone — a signal, not a metric). No location permission
  is requested, ever; the word "location" appears nowhere. It also
  covers the parent who doesn't charge daily or unlock much: three
  independent voices where iOS has one.
- **(b) As iPhone double coverage: not now, but not never.** The
  blunt version ("iOS won't allow it") is too absolute. One
  legitimate mechanism exists: HealthKit background delivery — an
  app with Health read permission for step count can be woken by
  iOS (roughly hourly) as steps accumulate, and each wake is a
  chance to ping. Honest limits: a force-quit kills all background
  delivery, timing is best-effort, and the Shortcuts automations
  remain the MOST reliable iOS source precisely because they fire
  with no app alive. So: an iOS senior app is a named FUTURE option
  (founder framing, Aug 31: it opens future options; it is not a
  v1 need) — supplementary voice, never a replacement.
- **The iOS shortcut-off case already has a better answer, half
  built:** the server ALREADY notices a phone gone silent (the
  no-routine-pings ops_alert fired today, correctly, for TestMom)
  and the unreachable distinction (161/163) separates "quiet
  morning" from "phone reporting nothing at all". What's missing is
  only surfacing: the kid should see "Kettle has not heard from the
  phone since yesterday" in the app — a small, honest feature that
  fixes the real failure (a dead Shortcut misread as a quiet
  morning) on BOTH platforms with zero new sensors. Recommend this
  ships in the kid app regardless of everything else in this brief,
  and before strangers join.

## The parent who turns things off (founder question, answered)

"What if the parent keeps turning off the shortcut — do we say they
are not the right customer?" No. The customer is the KID; a parent
disabling an automation is a product reality in the same category
as a phone that never gets charged, and the response is a ladder,
not a verdict: (1) Kettle NOTICES — the phone-gone-silent surfacing
below, which is why it is recommendation #1; (2) the kid re-enables
it on the next call or visit — a documented recovery path, not a
support ticket; (3) eventually a second voice (the iOS app above)
so one dead shortcut is not blindness. The true boundary is only
the parent who wants nothing on their phone at all — and once spec
013 exists, even that family can knowingly choose ask-anchored
coverage. Nobody is turned away for being a normal parent with a
normal phone.

## Recommendation, in order

1. Ship the "phone gone silent" surfacing in the kid app (small,
   platform-independent, closes the founder's actual worry).
2. Build option B, Android-first, with motion as a third signal;
   Xiaomi soak test is the gate. Sequence: after Wave D sunset +
   Memory v1.1; before Android-parent beta families are admitted.
3. Keep option A in the back pocket for a single hand-held pilot
   family if one arrives before B ships.

## Founder decisions needed (not yet — when this is picked up)

(1) Adopt the ordering above, or resequence against beta demand.
(2) Whether the beta recruiting message admits Android-parent
families now (with B promised) or waits — this touches tonight's
message wording. (3) At app-build time: the app's name and every
string on its one setup screen (verbatim, DECISIONS-recorded).
