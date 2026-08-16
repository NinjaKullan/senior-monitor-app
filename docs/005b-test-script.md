# 005b test script — rehearsal run, tap enumeration, crossed-pair drill

*Implementer, 2026-08-16. This is the script acceptance criteria 1, 2 and 4 of
`specs/005b-family-onboarding.md` are checked against. Run it with a Rehearsal
family only (runbook §1): rehearsal tokens for anything that fires.*

## 1 The end-to-end rehearsal (acceptance 1)

Provision fresh — the founder's only keyboard act, per the acceptance wording
("hands off the keyboard after provisioning"):

```bash
python -m scripts.provision --family "Rehearsal" \
    --parent "TestDad:America/New_York" --parent "TestMom:America/New_York" \
    --owner-email <YOUR_EMAIL> --signals routine,charger
```

The printout now carries a `setup page:` line per parent. Forge and sign the
two merged files per parent as usual (runbook §5–6). From here the keyboard is
closed:

1. Log into kettle-app with the owner email. **Family tab → Setup card**: both
   parents read *Ready to send*, each with a send link.
2. Tap **Send TestDad's setup link** — WhatsApp opens with the message
   pre-filled. Pick the right chat, send.
3. In the same chat, attach TestDad's **two signed files as documents** — one
   person's set at a time, never two people's files in one sitting.
4. On the parent phone, open the link and walk the page: consent → Shortcuts
   check → add both buttons → run each once and Allow → build both automations
   (Run Immediately, both charger boxes) → verify: open WhatsApp → **the page
   names the card and turns green**.
5. Repeat for TestMom. Watch kettle-app: two green cards, right names.
6. Afterwards the Setup card rows read *Set up and reporting* and the send
   links disappear.

Done means: two green cards, zero founder keystrokes after step 0, and field
notes filed as a numbered QUESTIONS block (acceptance 5 discipline).

## 2 Tap enumeration (acceptance 2) — merged method, Shortcuts installed

Counted on the parent's phone from opening the link to the green check.
App-switches counted as one tap each; iOS dialog defaults counted only when a
tap is genuinely required.

| # | Tap |
|---|---|
| 1 | page: "I understand — let's set it up" |
| 2 | page: "I found it" (Shortcuts app check) |
| 3 | switch to WhatsApp |
| 4 | tap file 1 |
| 5 | "Add Shortcut" |
| 6 | tap file 2 |
| 7 | "Add Shortcut" |
| 8 | back to the page (Safari) |
| 9 | page: "I added them all" |
| 10 | switch to Shortcuts |
| 11 | tap "Kettle — Daily routine" |
| 12 | "Allow" (the pre-empted warning) |
| 13 | tap "Kettle — Charger" |
| 14 | "Allow" |
| 15 | back to the page |
| 16 | page: "Done — I ran each one and tapped Allow" |
| 17 | switch to Shortcuts, Automation tab |
| 18 | "+" |
| 19 | "App" |
| 20–21 | pick two habit apps (one tap per app) |
| 22 | "Is Opened" (when not preselected) |
| 23 | "Run Immediately" |
| 24 | "Next" |
| 25 | pick "Kettle — Daily routine" |
| 26 | "+" |
| 27 | "Charger" |
| 28–29 | tick "Is Connected" and "Is Disconnected" |
| 30 | "Run Immediately" |
| 31 | "Next" |
| 32 | pick "Kettle — Charger" |
| 33 | back to the page |
| 34 | page: "The automations are built" |
| 35 | switch to WhatsApp (the verify open) |
| 36 | back to the page |
| 37 | page: "I opened WhatsApp" → green check |

**Honest total: ~37 taps** (±3 for iOS version differences in the automation
builder), of which the page's own CTAs are 8 and the automation builder is
~16. **This does not meet acceptance 2's ≤ 12.** The enumeration is the
deliverable the criterion asked for; the discrepancy is filed as QUESTIONS 121
rather than met by counting generously. The floor configuration the ≤ 12
arithmetic fits is page CTAs + add + first-run only — i.e. a world where the
automations are built by the helper or arrive pre-built, which iOS does not
offer today.

## 3 The crossed-pair drill (acceptance 4)

Swap the two rehearsal URLs on purpose: send TestDad's link where TestMom's
should go, with each phone holding its **own** correct files.

1. On TestMom's phone, open **TestDad's** page. The header says "TestDad's
   setup" — first tripwire, often caught right here.
2. Walk to verify and open WhatsApp on TestMom's phone.
3. The ping lands on TestMom's card. TestDad's page is watching TestDad's
   card: **the check stays waiting**, and after ~75 s says plainly that a
   different name's card changing means two links may have been swapped —
   stop and check.

The server-side half of this drill is pinned by
`test_crossed_urls_fail_loudly_not_silently`; the human half is the named
header and the named green message ("TestDad's card just turned green"), which
is the runbook §8 prediction discipline carried onto the page.

The other half of the old crossed-*files* failure — both the URL **and** the
files swapped — greens the wrong card convincingly on the page, exactly as it
always did on the app. The defence there is unchanged: the child watches the
named card in kettle-app (say the name before the open), and one person's
files never share a sitting with another's.

## 4 Dead-end checks (acceptance 3)

* Wait out (or SQL-expire) a rehearsal link: the page serves the expired dead
  end naming the owner; `/state` mirrors with 410. No steps, no file.
* `--setup-link` the same device: the old URL serves the replaced dead end,
  the new one is live.
* `--revoke` the device: the URL dies with the token.
