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

## 3. Cutover order (as done 2026-09-27; CC corrected the PM's first draft)

The build redirects the old app host the moment it deploys and hardcodes
the new API host, so certificates must exist before any deploy.

1. `fly certs add` for both hosts (founder); DNS in Cloudflare (PM at the
   founder's word): A/AAAA proxied, `_acme-challenge` CNAMEs DNS-only,
   `_fly-ownership` TXTs. Wait for `fly certs check` to say Issued.
2. `product/fly.toml` `[env] PUBLIC_BASE_URL` -> the new host (CC missed
   it; PM fixed, commit 4830e46). No `APP_ORIGIN` secret is needed: the
   code default is the new host and `APP_ORIGIN` is unset in prod.
   `APP_ORIGINS_EXTRA` was not needed either: the old app host redirects,
   so it never serves the app.
3. Stage the Twilio WhatsApp sender's inbound webhook to
   `https://api.heykettle.com/outbound/reply` (PM fills, founder presses
   Update WhatsApp Sender) right after `cd product && fly deploy`
   finishes: the signature check is tied to `PUBLIC_BASE_URL`.
4. `cd webapp && fly deploy`.
5. Supabase Auth: Site URL `https://app.heykettle.com`, added to Redirect
   URLs (founder).
6. Verified from the founder's Chrome: old app host 301s; new app loads;
   `api.heykettle.com/mcp` answers 401 with metadata naming the new
   issuer; old API host still answers; a connector added on the old host
   still works. The WhatsApp reply path is unverified until a parent
   next sends a 👍 (Mom paused at the time).
7. Afterwards: re-record R5 (Family tab prints the new address). The
   Asana directory-submission task is Care Compare's, already on
   `care.heykettle.com`, so nothing to change there (357 overstated
   this). Everyone signs in again on the new host once; sessions do not
   carry across hosts.
