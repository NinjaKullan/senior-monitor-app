# Spec 005e — Shortcut forge (generate + sign real .shortcut files)

*PM: Fable, from founder first-principles review Aug 2: the iCloud-link plan still required a human to assemble shortcuts by hand in an app they've never opened. Apple permits generating and signing shortcut FILES programmatically; only the automation wrapper is irreducibly manual. This spec removes every removable step.*

## 1. What it is

A founder tool (beta) that, given a device, emits ready-to-send signed `.shortcut` files — one per active signal — named exactly as the repair surface names them (`Kettle — {Signal}` — amended by QUESTIONS 96a, founder on-device: the parent's name truncated the tile and told the reader nothing), each containing a single `Get Contents of URL` action pointed at that device's ping URL.

Two components:

- **`product/scripts/forge.py`** (runs anywhere): given `--device-token` (or `--parent` lookup via DATABASE_URL), generates the unsigned `.shortcut` plists into an output dir. The shortcut plist format (`WFWorkflowActions` with `is.workflow.actions.downloadurl` / URL action) is stable and documented by inspection; keep the generated action set minimal — exactly one URL-fetch action, no input, no output, nothing else.
- **`product/scripts/forge-sign.sh`** (macOS only): wraps `shortcuts sign --mode anyone --input X --output X-signed.shortcut` over the output dir. The container cannot run this — mark it clearly and make `forge.py --verify` validate plist structure so the Linux side tests everything except the signature itself.

## 2. Requirements

1. Generated plist: one action, the device's URL, correct name; deterministic output (same inputs → identical bytes, so files are diffable).
2. `forge.py` round-trip test: generate → parse back with plistlib → assert action type, URL, and name. A plant test proves a second action or an extra key fails validation.
3. No secrets beyond the device token may appear in the file (test greps the plist for DATABASE_URL/ntfy/etc. patterns — same decode-don't-grep discipline where JWT-shaped strings are concerned).
4. Token handling: files are credentials-adjacent (the token is inside). Output dir is gitignored; README says treat files like the token itself; a test asserts the output dir is covered by .gitignore.
5. README section: the founder loop (generate on Mac → sign → AirDrop/WhatsApp the signed files → recipient taps → Add Shortcut → build automations picking the pre-made shortcut → live verification on /status or the app). Note Apple Settings requirement on the receiving phone if any (document what `--mode anyone` requires of the receiver, honestly, from Apple's docs).
6. Scale note in the spec, not built: CI macOS runner job signing per-family files on provisioning is the 005b path; the wizard serves them as download links.

## 3. Acceptance criteria

1. `forge.py --device-token X --out dir/` emits one valid, parseable `.shortcut` per active signal with correct URL and name (tested against a provisioned demo device fixture).
2. Round-trip validation + plant tests per §2.2–2.3.
3. Deterministic bytes (two runs diff clean).
4. macOS signing wrapper exists, is excluded from Linux test runs, and README documents the full founder loop.
5. Both suites green, ruff clean, pilot untouched, no secrets in the repo (the output dir gitignored and tested as such).
