# Onboarding runbook — the real flow, run by hand

*PM: Fable, 2026-08-13.*

## 0 What you are doing, and why

Founder decision (2026-08-13): the parents move off the pilot backend onto `kettle-api.fly.dev`, and
the pilot's baseline window ends where it ends. Two parents, two device tokens, five shortcuts each.
The July shortcuts pointing at `kettle-pilot.fly.dev` get deleted; everything after this points at
the product backend, so the family app, the digests, the ladder and one-tap revocation all start
working for your own parents.

This is the semi-manual beta flow: every step a stranger will eventually get from 005b's wizard,
performed by the founder first. Run it as written and take notes — **the notes are the deliverable**,
and §10 is why this document exists.

Set aside **90 minutes for the first parent**. The second will be faster, and that delta is itself a
finding.

## 1 Rehearse on yourselves first

Run the whole thing on your own and your wife's phones before Chennai. Not a smoke test — play the
parts, read the consent one-pager aloud, and let her be the one who has never seen it before. Two
adults who can say *why* a step confused them are worth more than a clean install. Use a throwaway
family, not your parents' one:

```bash
python -m scripts.provision --family "Rehearsal" --parent "TestDad:America/New_York" --parent "TestMom:America/New_York" --owner-email <YOUR_EMAIL>
```

The same owner email is fine and useful: `members.auth_user_id` is not unique, so one login sees
several families side by side. A throwaway also means your parents' family starts with clean tokens
and no test pings in its history.

**Then run §2 through §10 exactly as written**, substituting the rehearsal tokens and folder. The
rehearsal is the whole procedure or it is not a rehearsal — forge, sign, send, install, the
unlocked first run, the automations, the verification, and the notes. Skipping to the interesting
parts is how a step gets discovered for the first time in front of your parents.

Rehearsal files get their own folder, exactly like a real family — `FAM=~/Projects/kettle-files/Rehearsal`
before you forge (§5). Reusing the Chennai `$FAM` for test shortcuts is the same crossed-files
mistake as any other, with the same silent failure mode, and it is easiest to make on the run you
are treating casually.

Afterwards, abandon that family and forge the real one fresh. **Do not rotate the rehearsal tokens
into production.** `--revoke` kills a device and nothing re-issues one for an existing parent
(QUESTIONS 95), so revocation is one-way — fine for a family you discard, not something to lean on.

## 2 Terminal setup, once

These hold for the session, and every later command assumes them. **Paste one line at a time, and
never use trailing backslashes** — a continuation with a stray space after the `\` fails as `zsh: no
such file or directory: PUBLIC_BASE_URL=…`, which has cost time once already.

```bash
cd ~/Projects/senior-monitor-app/product
source .venv/bin/activate
export DATABASE_URL='postgresql://…'
export PUBLIC_BASE_URL=https://kettle-api.fly.dev
```

The venv must be **Python 3.12**. Xcode's bundled 3.9 fails on `datetime.UTC`; if the venv was built
against that, rebuild it with `/opt/homebrew/bin/python3.12`.

**Single quotes around `DATABASE_URL`, always.** The URL carries `?sslmode=require` and often `&` or
`$` in the password. Unquoted, `&` backgrounds the command; double quotes still expand `$`. Single
quotes pass it through untouched. Give that line a **leading space** to keep it out of
`~/.zsh_history` — the production URL is a credential.

## 3 Provision the family

```bash
python -m scripts.provision --family "Suryaprakasam" --parent "Amma:Asia/Kolkata" --parent "Appa:Asia/Kolkata" --owner-email <YOUR_EMAIL>
```

`--owner-email` is *your* address — the child account that will own this family.

The printout gives **one device token per parent**, plus their ping URLs. A token is a credential —
anyone holding it can post pings as that parent — so it is never typed by a human and never sent in
a message on its own.

## 4 Which signals each parent gets

**Decided (founder, 2026-08-13): five per parent — `whatsapp`, `youtube`, `charge_on`, `charge_off`,
`device_alive`.** News is skipped; Safari was considered and dropped. Five automations each, not six.

Know what that costs, because it is structural: **only WhatsApp and YouTube are person-anchored.**
Charger events and Daily Check are household- and device-grade, and under product law #6 they may
corroborate but never speak for a person. Reassurance therefore rests on two signals — on a parent
who rarely opens one of them, effectively on one. Thin, but honest, and better than a tripwire nobody
trips.

That makes one question on the call load-bearing: **which apps do you open every day without
thinking?** A tripwire only works on an app opened without deliberation, so pick from habit rather
than guesswork, and record their answers either way. Two constraints: a browser signal needs its own
sentence in the consent conversation, because people hear "browsing" even though we only see that an
app opened; and financial apps are excluded at every tier, permanently.

**The merged end state exists now (QUESTIONS 107): `routine` and `charger`.** One multi-app
automation ("Any of N Apps") fires the `routine` shortcut; one charger automation with **Connected
and Disconnected both checked** fires `charger`. Two files, two unlocked first-runs, two automations
— roughly a third of the per-app install, on the surface where every tap costs most. The record says
`routine`, never which app, and the consent one-pager now has the sentence that says so aloud.
`routine` is alarm-grade; `charger` stays corroborating-only (law #6 — coarsening the two plug edges
into one event changes nothing about who it may speak for). A live parent's per-app setup is
untouched until merged shortcuts are signed and delivered; nothing is rebuilt remotely for elegance.

Provisioning seeds the standard set unless told otherwise — `--signals routine,charger,device_alive`
chooses at provisioning time, and `--set-signals <device_token> --signals routine,charger` re-points
an existing parent's allowlist without hand-written SQL (both from QUESTIONS 94/107). To skip a
signal, do not build its automation — it reads `Not set up yet`, which is neutral, with no amber and
no repair nudge. **Adding a new key to the vocabulary is still a two-file code change with a drift
test, not a database row** — ask before the call, not during.

## 5 Forge the shortcuts (unsigned)

Files live in `~/Projects/kettle-files/<family>/`, a **sibling of the repo and never inside it**:
they carry device tokens in their URLs, and keeping them out of the working tree means no
`.gitignore` rule is the last defence between a token and a public commit. Each person ends up with
two folders — `<person>-shortcuts` from this step, `<person>-signed` from §6.

Same terminal as §2, so the exports are still live. One line at a time, once per parent:

```bash
FAM=~/Projects/kettle-files/suryaprakasam
mkdir -p "$FAM"
python -m scripts.forge --device-token <AMMA_TOKEN> --base-url https://kettle-api.fly.dev --out "$FAM/amma-shortcuts"
```

Then the same for Appa, with his token and `appa-shortcuts`.

**Use plain `--device-token`, with no `--name`.** In that mode the forge queries the database for
this parent's real display name and their actual signal list, so what you generate cannot disagree
with what the server believes. `--name` is the *offline* mode for a laptop with no database access,
and it silently falls back to the standard **six** — which is how unwanted News shortcuts got
generated once already. If you must work offline, `--signals` is not optional:

```bash
python -m scripts.forge --device-token <AMMA_TOKEN> --name "Amma" --signals whatsapp,youtube,charge_on,charge_off,device_alive --base-url https://kettle-api.fly.dev --out "$FAM/amma-shortcuts"
```

**Before moving on, count the files.** Five per folder, named for the right person. The forge prints
its signal list before writing; read it rather than trusting the flag you meant to type.

## 6 Sign them

A separate step, on macOS only, online and signed in to iCloud. Signing sends each file to Apple for
validation, and it is what makes them install with a single tap on a parent's phone.

```bash
./scripts/forge-sign.sh "$FAM/amma-shortcuts" "$FAM/amma-signed"
./scripts/forge-sign.sh "$FAM/appa-shortcuts" "$FAM/appa-signed"
```

**Only `-signed` gets sent.** The tell is file size: unsigned is roughly 1 KB per file, signed
roughly 22 KB. An unsigned file makes the phone demand *Allow Untrusted Shortcuts* in Settings —
precisely the friction the forge exists to remove, and ten minutes you do not want to spend
mid-call with a parent watching.

Once the family is verified and running, delete `$FAM` entirely. A signed shortcut sitting on your
laptop is a live credential with no remaining purpose.

## 7 On the call

**Consent first, phone second.** Read `docs/consent-onepager.md` together, one per parent, in the
language you will actually speak: what is recorded (who, which app, when), what is never recorded (no
messages, calls, location or listening), who sees it, and how it stops. Then **ask them to say back
what they think it does** and correct any gap. **If either of them is uneasy, stop.** A parent who
agrees to be polite is a parent who switches it off silently in three weeks and tells nobody.

**Delete the old July pilot automations before installing anything**, so there is never a moment with
two systems half-working on one phone: Shortcuts app → Automation tab. If the names no longer mean
anything to you, delete every automation you cannot positively identify.

**Install the shortcuts.** WhatsApp the five signed files to that parent. They tap each one → **Add
Shortcut**. No Settings toggle, no warning — field-proven twice.

**Then the step everyone skips: open each shortcut once by hand, while the phone is unlocked, and tap
Allow.** The first run asks permission to contact `kettle-api.fly.dev`, and iOS cannot show that
prompt on a locked phone. Skip it and the automations fail with *"requires privacy permissions that
cannot be granted while your device is locked"* — silently, from the family's point of view
(QUESTIONS 92).

**Build the automations.** Shortcuts → Automation → + → App → *(WhatsApp / YouTube / …, or all the
habit apps at once for a merged `routine` setup — the trigger reads "Any of N Apps")* → Is Opened →
**Run Immediately** → Next → pick the pre-made shortcut by name.

**The Charger trigger has the same trap with a different default (QUESTIONS 107):** it comes up as
**Run After Confirmation**, which on a parent's phone means a prompt at every plug-in that never gets
tapped. Flip it to **Run Immediately**, exactly like the App trigger. And check **Is Connected and Is
Disconnected in the same automation** — one automation, one `charger` shortcut, both edges. Know the
cosmetic gotcha too: the automation list's subtitle shows only the shortcut name, so a merged
automation reads "Kettle — Daily routine" under "When any of 3 apps are opened" — that is correct,
not mislabelled.

Warn them here about Apple's periodic "N automations ran" notice: it cannot be turned off, it is not
an error, and it is the phone being honest about what it is doing.

## 8 Verify by prediction

The load-bearing step, and it only works in this order:

1. **Say out loud which card you expect to change.** "Appa is about to open WhatsApp, so *Appa's*
   card should go green."
2. Ask them to open the app.
3. Watch **kettle-app.fly.dev**.

If the card you named changes, you have the right phone, token and person. If a *different* card
changes, you have crossed two people's files and caught it in ten seconds instead of a month. Fix:
revoke both tokens, re-forge, resend, redo this step.

Watching whether "a card lights up" confirms almost nothing; naming the card first turns observation
into a test. Do it for **two signals per parent**, and do the *first* signal for each parent
**before** building the remaining automations — an error at signal one costs five minutes, the same
error at signal five costs the session. Charger On/Off and Daily Check verify themselves within a
day; leave them.

Why this earns its time: a file mix-up is *recoverable* — revoke, re-forge, resend. What makes it
dangerous is that it is **silent**, reporting the wrong person's routine indefinitely from a system
that looks perfect. The defence is detection, not care while sending.

## 9 After

- Watch the app for 48 hours. Every tripwire should leave `Not set up yet`.
- Anything still amber after two days is the first live repair case, and the first real test of
  whether the repair nudge says something a family can act on.
- If a phone is lost or a parent wants out:

```bash
python -m scripts.provision --revoke <DEVICE_TOKEN>
```

It prints the family, person and platform it killed, so you can confirm before closing the laptop.

## 10 Field notes — the deliverable

The install is not the point; the notes are. Capture, per parent:

1. **Where they frowned.** Every moment of confusion is a wizard screen.
2. **Elapsed time**, and how much of it was the automations.
3. **What they asked that you had not thought to explain.** These become the wizard's copy.
4. **Whether the unlocked-first-run step caught anyone out** even though you knew about it.
5. **What either parent asked to exclude.** A refused signal is a requirement, not a setback.
6. **Their own words for what this is.** A sentence better than our landing page is the landing page.

File them in `specs/QUESTIONS.md` as a numbered founder-field block, the way the on-device UI round
(items 65–68) went in, starting at the next free number (see `CLAUDE.md`). 005b gets written from
these.

## 11 Known rough edges

- **Ten manual automation taps total** (five per parent) is the biggest cost here, and 005b's first
  target.
- **The child app has no onboarding of its own** — you provision from a terminal. Fine for your own
  family, impossible for a stranger, which is why 005b exists.
- **No digests yet.** WhatsApp's display name is unapproved, so the channel is registered but not
  sending. Collection and the app work regardless, and the parents will not notice because nothing
  was promised to them.
- **The pilot backend keeps running** with no traffic. Leave it alone until the Day-30 findings memo
  is written; it is still the YC-evidence instrument.

Tooling gaps queued, so you work around them once rather than twice: **QUESTIONS 93** (forge derives
its output path from the token, deleting the `--out` naming decision), **94** (`provision
--signals`), **95** (`--add-device`, `--rotate`, `--delete-family`).
