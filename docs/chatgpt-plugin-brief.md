# ChatGPT plugin package and domain challenge (DECISIONS 358, third directory)

Scope: two small things so the PM can submit Kettle to the ChatGPT plugin
directory. No change to tools, copy, auth or the webapp. Report in the §7
shape of `docs/assistant-directories-brief.md`.

Source: https://developers.openai.com/plugins/deploy/submission and
https://developers.openai.com/plugins/build/plugins.md (read both first).

## 1. Domain challenge route (product)
- `GET /.well-known/openai-apps-challenge` on kettle-api returns the bare
  token from a new setting `OPENAI_APPS_CHALLENGE` as `text/plain`, no
  JSON, no trailing newline. When the setting is empty: 404. Served on
  every host, like the OAuth discovery documents.
- Setting lives in `config.py` beside `PUBLIC_BASE_URL`, default empty.
  The value itself is set as a Fly secret by the founder when OpenAI shows
  it; never committed.
- Tests: token served when set; 404 when unset; content type is text/plain.

## 2. The package (`tools/chatgpt-plugin/`)
Files, all under one root folder `kettle/`:
- `kettle/plugin.json`: `$schema`
  `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`, `name`
  `heykettle`, `version` `1.0.0`, `description` (PM copy below, under 1024
  characters), `author` `{name: "HeyKettle", url: "https://heykettle.com"}`,
  `homepage` `https://heykettle.com/connect/`, and
  `extensions.com.openai.interface` with exactly these fields, verbatim:
  - `displayName`: `Kettle`
  - `shortDescription`: `A caregiving log for family`
  - `longDescription`: the PM's long copy below
  - `developerName`: `HeyKettle`
  - `category`: `Productivity`
  - `capabilities`: the four lines below
  - `websiteURL`: `https://heykettle.com`
  - `supportURL`: `https://heykettle.com/connect/`
  - `privacyPolicyURL`: `https://heykettle.com/privacy.html`
  - `termsOfServiceURL`: `https://heykettle.com/terms.html`
  - `defaultPrompt`: the three prompts below
  - `logo`: `./assets/logo.png`, `composerIcon`: `./assets/logo.png`
- `kettle/mcp.json`: `$schema`
  `https://agent-plugins.org/schemas/1.0.0/mcp.schema.json`, one server
  `kettle` with `type` `streamable-http`, `url`
  `https://api.heykettle.com/mcp`. No auth fields; OAuth is discovered
  from the server.
- `kettle/assets/logo.png`: a copy of `webapp/public/icon-512.png`.
- No `skills/`, no `.app.json`, no hooks, no screenshots (the server has
  no UI and screenshots are rejected without one).
- `make-zip.sh`: builds `dist/kettle-plugin-<version>.zip` containing the
  `kettle/` folder and nothing beside it; `dist/` is gitignored.
- Test (`product/tests/test_chatgpt_plugin.py` or a tools test, whichever
  the tree already does for `tools/`): both JSON files parse; every
  required field present; every `./` path exists inside the root; limits
  hold (displayName and shortDescription 30, longDescription 4000,
  description 1024, developerName 80, each defaultPrompt 128, capabilities
  at most 20 of 120); the copy law scan from the site tests, or an
  equivalent, passes over every string a person reads.

## 3. PM copy (verbatim; do not edit)
description (package):
`Kettle is a family's shared record about a parent: a caregiving log the whole family writes to and reads from, plus a quiet signal that a normal routine happened on the parent's phone. Ask how Mom's day is going, who to call, or what the family wrote, and add a note by saying it.`

longDescription:
`Kettle is a shared record about a parent or anyone your family looks after. It acts as a caregiving log the whole family writes to and reads from. Connect it and you can ask ChatGPT how Mom's day is going, when her phone was last heard from, what your sister wrote this week, or who to call if you can't reach her. Say "add a note: called Dad, he sounded great" and it lands in the family's record for everyone to see. Each family member connects with their own Kettle sign-in and sees only their own circles. Kettle never reads messages, location or anything on a parent's phone; it hears a quiet signal that a normal routine happened, and keeps what the family writes. Reading has no side effects; adding a note is read back to you before it is saved.`

capabilities:
- `Ask how a parent's day is going and when their phone was last heard from`
- `Read what the family wrote, newest first, with anything upcoming on top`
- `See who to call if you cannot reach a parent`
- `Add a note or reply to one, read back to you before it is saved`

defaultPrompt:
- `How is Mom's day going?`
- `Who can I call if I can't reach Mom?`
- `Add a note: called Dad, he sounded great.`

## 4. Report
Table as in the directories brief. Say which Fly secret name the founder
sets, and the exact zip path. No deploy.
