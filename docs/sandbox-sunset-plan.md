# Sandbox sunset — retirement plan (findings only)

The WhatsApp sandbox was the Wave C parent-side channel. Wave D flipped the ask
to the registered HeyKettle number on 2026-09-04 (DECISIONS 263), and DECISIONS
271 put the retirement "on its calendar — seven days of the real configuration
with no alerts, ask or no ask." That week (Sep 4–11) has elapsed, so the ruling
spec 011 §sunset asks for is now due. This document is findings only: it maps
every reference, states the exact order and the rollback, and names the one
decision the PM has to make. **No code was changed.** The PM rules Monday.

Reviewed on `668f44e` (main). Nothing here has been applied.

---

## 1. "The sandbox" is three different things

Retiring it is not one deletion, because the word covers three separate things
that came apart at the Wave D flip:

1. **A phone number** — `whatsapp:+14155238886`, Twilio's shared WhatsApp
   sandbox. It is **not a live production value.** Prod's `TWILIO_WHATSAPP_FROM`
   has been the real `+19843704452` since Sep 1 (runbook Pass 2; DECISIONS
   263/322). The sandbox number now survives only as (a) the documented
   rollback target and (b) three test constants.

2. **A code path** — in `TwilioWhatsAppTransport.send`
   (`product/kettle/outbound_whatsapp.py:155`), `TWILIO_ASK_CONTENT_SID` unset
   sends `payload["Body"] = render(...)` (the "sandbox body"), and set sends the
   `ContentSid` template. Prod has the SID set (v7), so the body branch is not
   used in production — but it stays reachable the instant the SID is emptied,
   which is exactly what today's rollback does.

3. **A Twilio-console footprint** — the sandbox's joined-numbers list, its
   "When a message comes in" inbound webhook, and the join-code step. None of
   this is in the repo; it lives in the Twilio console.

The number and the console footprint are pure decommission. The code path is the
only part whose retirement is a code change — and it is the part the PM must rule
on (§3).

## 2. Every reference, by where it lives

| # | Reference | Location | What it is | Dies on sunset? |
|---|---|---|---|---|
| R1 | `whatsapp:+14155238886` as rollback target | `docs/wave-d-dark-stage-runbook.md:100` | The one-command rollback from the real number | Yes — see §5, this is the sharp one |
| R2 | `SANDBOX_FROM = "whatsapp:+14155238886"` | `product/tests/test_wave_d_template.py:50` | Pins the no-SID body send byte-for-byte | Only under Scope B |
| R3 | `FROM = "whatsapp:+14155238886"` | `product/tests/test_outbound_whatsapp.py:20` | The whole Wave C suite runs the body path off this | Only under Scope B |
| R4 | `twilio_whatsapp_from="whatsapp:+14155238886"` | `product/tests/test_outbound.py:1214` | The roster/fail-closed test's sender | Only under Scope B (a constant swap) |
| R5 | The no-SID body branch | `product/kettle/outbound_whatsapp.py:155` (`else: payload["Body"]`) | The sandbox send shape | Only under Scope B |
| R6 | `twilio_ask_content_sid` is **optional** | `product/kettle/config.py:64`, factory `outbound.py:238` | Unset is a valid (sandbox) config today | Becomes mandatory under Scope B |
| R7 | Sandbox prose in the transport docstring | `product/kettle/outbound_whatsapp.py:1,12,31,125` | Describes the two shapes and the join step | Doc edit, either scope |
| R8 | Sandbox prose in the registry | `product/kettle/outbound_templates.py:178,191` | "on the sandbox from this string" | Doc edit, either scope |
| R9 | Sandbox prose in config | `product/kettle/config.py:49,61,62,76` | Comments describing the sandbox path | Doc edit, either scope |
| R10 | Sandbox prose in the engine | `product/kettle/outbound.py:1307,1325` | The bare-number reply matcher, "sandbox era's callers" | Comment only; the behaviour (a bare `From` still matches) stays for SMS |
| R11 | Runbook Pass 1/Pass 2, rollback law, "step 2 with the v6 copy" | `docs/wave-d-dark-stage-runbook.md:90–155` | The dark-stage procedure, written around the sandbox | Rewrite/retire, either scope |
| R12 | Spec 011 §sunset clause | `specs/011-wave-d-real-number.md:111` | "after one clean week, sandbox config is removed" | The clause this plan satisfies |
| R13 | Spec index line "sandbox sunset needs its own ruling" | `specs/README.md:28` | Status note | Update after the ruling |
| R14 | `tools/submit_ask_template.py:42,72` | Tool | "sandbox stays the production path until…" (now stale — v7 is live) | Doc edit; the tool is a record, not run |
| R15 | v6 template `HX61758012edba26686ec7ee361a0f493f` | `docs/wave-d-dark-stage-runbook.md:143`; DECISIONS only | Approved-but-unused fallback template | Console retire + doc edit (§4) |
| R16 | Site quote of the ask sentence | `site/src/copy.ts:103` | Marketing copy quoting the ask | **No** — it quotes the ask copy, not the sandbox; unaffected |

**Not a reference, stated so it is not mistaken for one:** the bare-number reply
match in `outbound.py` (R10) reads "sandbox era's callers passed bare numbers."
That behaviour is still load-bearing for SMS (a `From` without `whatsapp:`
matches `phone_e164`), so only the *comment* is about the sandbox; the code stays.

## 3. The one decision the PM has to make

"Sunset" resolves to one of two scopes. They are not the same amount of work and
they have different rollback consequences.

**Scope A — operational decommission (no code change).** Retire the sandbox as
the rollback target and from the runbook, retire v6, tear down the console
sandbox. The no-SID body branch (R5) stays in the code as dormant/defensive
paths; the tests (R2–R4) stay green untouched because the code they pin still
exists. This is exactly the ruling the calendar asks for and can ship as docs
plus console actions.

**Scope B — also close the code path (a real code change, its own review).**
Make `TWILIO_ASK_CONTENT_SID` mandatory for `twilio_whatsapp` (fail-closed at
boot, the `TWILIO_WHATSAPP_FROM` posture at `outbound_whatsapp.py:105`), delete
the body branch (R5), rewrite the two suites that pin it (R2, R3), and swap the
`test_outbound.py` sender constant to the real number (R4). This removes the
latent misconfiguration where an emptied SID silently falls back to a body send
a registered number cannot use — but it also removes the last cheap rollback
(§5).

**Recommendation.** Rule **Scope A now** — it is what spec 011 §sunset and
DECISIONS 271 ask for, and it is reversible. Hold **Scope B as a follow-up
spec** once A has settled and the fail-loud posture (§5) has been accepted in
practice, because B is a code change that deletes the rollback and deserves its
own build with its own guardrail test. The rest of this plan is written for
Scope A, with the Scope-B additions marked.

## 4. The v6 fallback

v6 (`kettle_ask_parent_v6`, `HX61758012edba26686ec7ee361a0f493f`) is an
approved, Utility-category template kept "as the proven-delivered fallback"
(runbook Pass 2). Two findings:

- **It is not wired as an automatic fallback anywhere in code.** The transport
  reads exactly one SID, `TWILIO_ASK_CONTENT_SID` (`outbound.py:238`). "Fallback"
  has only ever meant "a human swaps the SID back to v6 in a `fly secrets set`"
  — which is the same manual rollback the sandbox retirement affects (§5). Its
  SID lives in no code, only in DECISIONS and the runbook.
- **Retiring it is a console action plus a doc edit.** Nothing in the app breaks
  if v6 is paused or deleted in the Twilio console; the running system never
  names it. Keeping it approved-but-unused costs nothing either, and it is the
  only pre-approved Utility template that is not v7 — so it is the fastest
  same-copy rollback if v7 is ever paused by Meta. **Recommendation: keep v6
  approved as break-glass, and drop only the runbook language that treats it as
  the dark-stage's live template.** If the PM would rather retire it, that is a
  one-line console action; the repo needs only the doc edits in R11/R14.

## 5. The rollback finding (the sharp consequence)

Today, rolling the ask back off the real number is one command
(`docs/wave-d-dark-stage-runbook.md:97`):

```
fly secrets unset TWILIO_ASK_CONTENT_SID --stage
fly secrets set TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

That rollback **depends on the sandbox still being joinable.** Retiring the
sandbox (removing the join list, tearing down its webhook) deletes this rollback
path. After sunset there is no one-command fallback for a broken real WhatsApp
sender.

This is not a reason not to sunset — it is a thing to decide with eyes open. The
honest posture after sunset is **fail-loud, which the system already does**: a
refused or undeliverable ask records a `failed` ledger row and fires an ops alert
with Twilio's own words (`outbound_whatsapp.py:_refusal`; tests
`test_a_paused_template_is_a_loud_failure...`), and **everything child-facing
stays on email regardless**, so a broken WhatsApp sender never silences the
family's digests or escalations. What is lost is only the ability to re-route the
*parent ask* in one command.

**Recommendation:** keep the Twilio sandbox project *joinable* as documented
break-glass for a defined period (say through the first stranger family), even
while removing it from the everyday rollback story — decommission the operational
use, not the account capability. Replace the runbook's rollback block with the
fail-loud posture as the primary story and the sandbox re-join as a
time-boxed break-glass with its steps written out.

## 6. Secrets that would become dead

**None of the Fly secrets on kettle-api die.** Stated plainly because the
question invites a longer answer than the truth:

| Secret | After sunset |
|---|---|
| `TWILIO_ACCOUNT_SID` | Live — same account owns the real sender |
| `TWILIO_AUTH_TOKEN` | Live — real sends **and** the inbound-webhook signature (`main.py` `/outbound/reply`) |
| `TWILIO_WHATSAPP_FROM` | Live — the real number; only its *sandbox value* dies as a rollback target |
| `TWILIO_ASK_CONTENT_SID` | Live (v7); under Scope B it changes from optional to **required**, not dead |
| `TWILIO_MESSAGING_SERVICE_SID` | Live — the SMS carrier (011 Amendment A), untouched |

What actually goes dead is not a secret: the sandbox number *value*
(`+14155238886`), the Twilio-console sandbox (join list + inbound webhook), and —
if the PM retires it — the v6 template. The plan should say so rather than hunt
for a secret to unset.

## 7. Retirement order (Scope A)

Each step names its rollback. Nothing here is code; it is docs and console.

1. **Confirm the clean week held.** Read the ledger and `ops_alerts` for Sep 4–11:
   no ask failed for a sender/number reason, no unexpected `outbound_failed`.
   DECISIONS 271 made the week a calendar, not a gate on a real ask, so "no ask
   fired" is a pass. *Rollback: n/a (a read).*
2. **Docs: rewrite the runbook (R1, R11).** Replace the sandbox rollback block
   with the fail-loud posture (§5) as the primary story and, if kept, the
   time-boxed sandbox re-join as break-glass. Retire the Pass 1/Pass 2 procedure
   to a "how the flip was done" record. *Rollback: `git revert` the doc commit.*
3. **Docs: stale-language sweep (R7–R10, R14).** Update the sandbox prose in
   `outbound_whatsapp.py`, `outbound_templates.py`, `config.py`, `outbound.py`
   (comment only) and `tools/submit_ask_template.py` to past tense. No behaviour
   changes; these are comments and a docstring. *Rollback: `git revert`.*
4. **Spec + index (R12, R13).** Mark spec 011 §sunset done and change the
   `specs/README.md` line from "sandbox sunset needs its own ruling" to the
   retirement's DECISIONS number. *Rollback: `git revert`.*
5. **Console: tear down the sandbox** (founder, Twilio console) — remove the
   sandbox inbound webhook and, if v6 is being retired, pause v6. Leave the
   sandbox *project joinable* if break-glass is kept (§5). *Rollback: re-add the
   sandbox webhook; re-approve/unpause v6.*
6. **DECISIONS entry.** Record the retirement at the header's number, naming what
   was torn down, what was kept (v6? the joinable sandbox?), and the new rollback
   posture. Update the header line.

**No Fly secret is set or unset in Scope A.** `TWILIO_WHATSAPP_FROM` and
`TWILIO_ASK_CONTENT_SID` stay exactly as they are (real number, v7).

## 8. Scope-B additions (only if the PM rules Scope B)

Do these as a separate spec/build after A, with the guardrail-plant discipline:

1. **Make the SID mandatory.** In `_twilio_transport`/`TwilioWhatsAppTransport`,
   add `TWILIO_ASK_CONTENT_SID` to the missing-credentials check so
   `twilio_whatsapp` refuses to boot without it — the exact posture
   `TWILIO_WHATSAPP_FROM` already has (`outbound_whatsapp.py:105`). Plant: unset
   the SID, assert the app refuses to boot.
2. **Delete the body branch (R5)** and the `else` in `send`; a template send is
   the only shape.
3. **Rewrite R2/R3.** `test_wave_d_template.py`'s "the sandbox, unchanged"
   section and the whole no-SID premise of `test_outbound_whatsapp.py` go; keep
   the template-path, failure-honesty and reply tests.
4. **Swap R4.** `test_outbound.py:1214`'s sender constant moves to the real
   number (the roster test does not care which, but the sandbox number should
   stop appearing in the suite).
5. **Rollback for the whole of B is `git revert` of the build**, and note in its
   DECISIONS entry that B removed the sandbox re-route rollback — after B, a
   broken real sender is fail-loud only (§5), so B should not land until that
   posture is accepted.

## 9. Verification (either scope)

- `KETTLE_REQUIRE_POSTGRES=1 pytest` green from the repo root (904 as of 333).
  Under Scope A the count is unchanged — no test changes. Under Scope B, the
  count moves and the plant proofs are listed in the build's DECISIONS entry.
- `grep -rn "14155238886" product/ docs/` returns nothing under Scope B, and
  only the (rewritten) break-glass mention under Scope A.
- One real quiet-morning ask still delivers from HeyKettle after step 5 (or the
  next one is watched live, per DECISIONS 271 — not a gate).

## 10. What does not change

- The real sender, v7, and every Fly secret (§6).
- Child-facing email — digests, follow-ons, all-clears — none of which ever rode
  WhatsApp.
- The reply webhook and its Twilio-signature check (`TWILIO_AUTH_TOKEN`).
- SMS for +1 parents (011 Amendment A) and its `TWILIO_MESSAGING_SERVICE_SID`.
- The bare-number reply match (`outbound.py:1307`) — still needed for SMS.
- The site's quote of the ask copy (`site/src/copy.ts:103`) — it quotes the sentence,
  not the sandbox.

---

*Findings only. No code, config, or console change has been made; this plan is
for the PM to rule on. The one decision that blocks the rest is Scope A vs Scope
B (§3); the one consequence to accept either way is the loss of the one-command
rollback (§5).*
