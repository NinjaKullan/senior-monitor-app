# Kettle — child PWA (demo grade)

Spec `specs/005a-child-pwa-demo.md`. Read-only, three screens, running against
the live backend. The onboarding wizard, billing and the TestFlight wrap are
005b.

The demo *is* the pitch, so nothing here is staged: every number on screen came
from a real ping through the real ingestion route, filtered by the real
policies.

## The security model in one paragraph

This is a static site. Every byte of `dist/` is downloadable by anyone who loads
the page, so the only credentials it holds are the Supabase URL and the
publishable key — both meant to be public. Every query runs as the
`authenticated` role and comes back filtered by RLS; the app never sends a
`family_id = ?` filter of its own, because a client asking politely for its own
rows would only hide a policy bug. **The service key bypasses RLS and must never
appear here.** `npm run verify:build` greps the built output for it — literal
patterns, plus any JWT whose decoded `role` claim is not `anon` — and CI runs
that on every push.

## Screens

| Screen | What it shows |
|---|---|
| **Today** (Glance) | per parent: name, `All normal` or `Quiet so far`, and "last routine seen {time} local" |
| **Digests** | reverse-chron list of what was actually sent, recomposed from the templates |
| **Family** | read-only roster of parents and members, and the privacy line |

`Quiet so far` is as dark as this app ever gets. Absence that warrants more than
that belongs to the escalation ladder, and the ladder has no surface here at
all. There is no red in the palette because there is no state that earns one.

The Digests screen stores nothing new: `digest_sends` records that a message
went out and deliberately holds no text, so the list is rebuilt from the same
templates the backend used, and the morning message's clock time is recomputed
from the pings it was derived from. `product/tests/test_webapp_contract.py`
fails if those templates ever drift from the Python originals.

Refresh is a 45-second poll rather than Supabase realtime — reasoning in
`specs/QUESTIONS.md` item 42.

## Local development

```bash
cd webapp
npm install
cp .env.example .env.local     # fill in URL + publishable key
npm run dev
```

```bash
npm run lint         # eslint
npm run test         # vitest
npm run build        # tsc --noEmit && vite build
npm run verify:build # grep the output for secrets
npm run ci           # all four, in the order CI runs them
```

## Deploy

```bash
cd webapp
fly launch --no-deploy          # sets `app` in fly.toml; keep the rest

fly deploy \
  --build-arg VITE_SUPABASE_URL="https://<project>.supabase.co" \
  --build-arg VITE_SUPABASE_PUBLISHABLE_KEY="<publishable key>"

curl -s https://kettle-app.fly.dev/healthz     # {"ok":true}
```

Build args rather than Fly secrets on purpose: these values are compiled into
the bundle and are public anyway, and `fly secrets` would imply otherwise. The
build fails if `check-build-secrets.mjs` finds anything else in the output, so a
service key pasted into the wrong variable cannot ship.

Supabase Auth needs the deployed origin in **Authentication → URL Configuration
→ Redirect URLs**, or the magic link will bounce.

## The demo script

Three commands, start to finish. Run the API's provisioning first if the demo
family does not exist yet:

```bash
# 1. A demo family, and a member row carrying the founder's own email.
DATABASE_URL=... python -m scripts.provision --demo
DATABASE_URL=... psql "$DATABASE_URL" -c \
  "insert into members (family_id, display_name, role, email)
   select id, 'Hema', 'owner', 'you@example.com' from families
   where name = 'Kettle Demo Family';"

# 2. Sign in at https://kettle-app.fly.dev with that email, open Today.
#    Both demo parents read "Quiet so far".

# 3. Fire a real ping from the URL the provisioner printed, and watch it flip.
curl "https://kettle-api.fly.dev/p/<demo-token>/whatsapp"
```

Within the refresh interval the parent's card turns `All normal` and the
last-seen time appears. Nothing about that path is special-cased for the demo:
it is the same route the Shortcut on a real phone calls, the same RLS the real
family gets, and the same templates the real digest sends.

## What is deliberately not here

Onboarding wizard, Shortcuts links, family codes, billing (all 005b). Any ladder
or alert surface. Settings or editing of any kind — read-only means read-only.
Push notifications. **Analytics of any kind**, including the privacy-friendly
sort; product law #4 does not have an exception for well-behaved trackers.
