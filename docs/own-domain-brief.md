# Own domain for the app and the API (brief for Claude Code)

Push needed: yes. Founder ruling 2026-09-27 (DECISIONS 357). PM-written.

## 1. What changes and why

Before the release post, the two customer-facing hosts move off Fly's shared
domain onto ours:

| Today | After |
|---|---|
| `https://kettle-app.fly.dev` (the family app) | `https://app.heykettle.com` |
| `https://kettle-api.fly.dev` (API, setup pages, MCP, webhooks) | `https://api.heykettle.com` |

`fly.dev` reads as a borrowed address, and it is printed where customers see
it: parents open setup links at `kettle-api.fly.dev/s/...`, the Family tab
shows `kettle-api.fly.dev/mcp`, Claude's answers say "in Kettle at
kettle-app.fly.dev", and the two directory submissions would carry it.
`care.heykettle.com` already works this way (DECISIONS 345/346); same recipe.

The old hosts keep working. Every forged shortcut on every parent's phone
points at `kettle-api.fly.dev`, and every Claude or ChatGPT connector already
added uses `kettle-api.fly.dev/mcp`. Nobody re-installs anything. The API
answers on both hosts indefinitely; the app's old host redirects.

## 2. Code changes (the whole list; nothing else)

1. `product/kettle/config.py`: defaults `public_base_url` ->
   `https://api.heykettle.com`, `app_origin` -> `https://app.heykettle.com`.
   Add `APP_ORIGINS_EXTRA` (comma list, default empty) merged into the CORS
   allow-list for `/oauth/approve` and wherever `app_origin` is used as an
   origin check, so the old app host can be granted during cutover the same
   way `WAITLIST_ORIGINS` grants old site origins. Nothing in the redirect
   or issuer logic changes: `public_base_url` stays the one issuer.
2. `webapp/src/lib/setupLinks.ts`: `SETUP_PAGE_BASE` ->
   `https://api.heykettle.com` (this also moves `API_BASE` and `MCP_URL` in
   `data.ts`, so the Family tab prints the new address).
3. `webapp/nginx.conf`: a second `server` block for `server_name
   kettle-app.fly.dev` that returns `301 https://app.heykettle.com$request_uri`.
   The default block stays as is.
4. Defaults in `product/scripts/provision.py` (`--base-url`),
   `product/scripts/stage_shortcut.py` (`DEFAULT_BASE_URL`) and
   `product/kettle/assistant_tools.py` (`app_origin` default): new hosts.
5. Tests: update the fixtures that pin `kettle-api.fly.dev`
   (`webapp/src/tests/copyLaw.test.tsx`, `household.test.tsx`,
   `actions.test.tsx`, and any pytest that asserts the old default). Add one
   test each: config default is the new host; the nginx redirect block exists
   (a string test on the file is enough); `APP_ORIGINS_EXTRA` parses like
   `WAITLIST_ORIGINS`.
6. `docs/onboarding-runbook.md` §2 and §5: `PUBLIC_BASE_URL` and `--base-url`
   read `https://api.heykettle.com`. Add one line: old shortcuts keep working.
7. `site/src/sections/Waitlist.tsx`: default `VITE_API_BASE_URL` ->
   `https://api.heykettle.com`. (CORS already allows heykettle.com.)

Do not touch `care/`, `specs/`, `DECISIONS.md`, Twilio, Supabase, DNS or
Fly settings; those are the founder's and the PM's, in section 3.

Report: files touched, test counts (root pytest, webapp vitest, site
vitest), and the one commit hash. Under 200 words.

## 3. Cutover order (PM and founder; after the build is deployed)

1. Deploy the build to `kettle-api` and `kettle-app` (founder). Nothing
   changes yet: secrets still say the old hosts, DNS has no new names.
2. DNS in Cloudflare (PM at the founder's word, as for `care`): `app` and
   `api` A/AAAA to the addresses `fly ips list -a kettle-app` and `-a kettle-api` print, proxied (as for care); `_acme-challenge.app`
   and `_acme-challenge.api` CNAMEs from `fly certs add`; the `_fly-ownership`
   TXTs. Then `fly certs add app.heykettle.com -a kettle-app` and
   `fly certs add api.heykettle.com -a kettle-api` (founder), wait for Issued.
3. Secrets, in one command so they land together (founder):
   `fly secrets set -a kettle-api PUBLIC_BASE_URL=https://api.heykettle.com APP_ORIGIN=https://app.heykettle.com APP_ORIGINS_EXTRA=https://kettle-app.fly.dev`.
   In the same minute, Twilio: the WhatsApp sender's inbound webhook from
   `https://kettle-api.fly.dev/outbound/reply` to
   `https://api.heykettle.com/outbound/reply` (founder in the console; PM
   fills, founder presses Save). The signature check is tied to
   `PUBLIC_BASE_URL`, which is why these two move together.
4. Supabase Auth: add `https://app.heykettle.com` to the redirect allow-list
   and set it as the site URL (founder in the dashboard). Sign-in is by
   emailed code, so this is belt and braces, not a blocker.
5. Verify (PM, from the founder's Chrome): app sign-in at
   `app.heykettle.com`; old app host redirects; a fresh setup link prints
   `api.heykettle.com/s/...`; `api.heykettle.com/mcp` answers a JSON-RPC
   initialize and its `.well-known` metadata names the new issuer; the old
   `kettle-api.fly.dev/mcp` still answers; Fly logs show a 204, not a 403,
   on the next WhatsApp reply.
6. Afterwards: re-record R5 (the Family tab now prints the new address);
   update the Asana directory-submission task to `api.heykettle.com/mcp`;
   `APP_ORIGINS_EXTRA` comes off after a week with no 4xx from the old host.
