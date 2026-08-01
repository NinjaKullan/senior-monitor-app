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
| **Today** (Glance) | per parent: a day-part-aware headline, a dual-timezone "last routine seen" subline, a three-segment day arc, and a liveness beacon |
| **Digests** | reverse-chron list of what was actually sent, recomposed from the templates |
| **Family** | read-only roster of parents and members, and the privacy line |

`Quiet so far …` is as dark as this app ever gets. Absence that warrants more
than that belongs to the escalation ladder, and the ladder has no surface here at
all. There is no red in the palette because there is no state that earns one.

Spec 005c warmed that surface without widening it: **warmth rises, information
stays coarse.** The headline knows the parent's local time of day
(`Amma's morning started the usual way` / `A normal, gentle day` /
`Quiet so far today`), the subline gives their clock and yours side by side, and
the arc gives the day a shape — three binary segments, lit once any routine
happened in them. Binary is the point: a segment that glowed brighter for more
pings would be a count in a costume, and counts are what turn reassurance into a
behaviour profile. The guardrail is a test, not a convention — one asserts the
arc's DOM carries no digit a reader or a screen reader could find, and another
renders the same card from one ping and from many and requires identical markup.

The beacon is labelled `phone` because it is phone status, never person status
(product law #6). It breathes only while a real mechanism signal is recent,
goes still and grey when one is not — stillness, not alarm — and is absent
entirely for a parent with no `device_alive`/charger signal configured. An
animation that ran unconditionally would be a liveness indicator that indicates
nothing, which is the most expensive lie a reassurance product can tell, so a
test plants a stale fixture and requires the still variant.

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
#    Both demo parents read "Quiet so far …".

# 3. Fire a real ping from the URL the provisioner printed, and watch it flip.
curl "https://kettle-api.fly.dev/p/<demo-token>/whatsapp"
```

Within the refresh interval the parent's card warms to the headline for that
time of day, the last-seen subline appears in both clocks, and the matching arc
segment lights. Nothing about that path is special-cased for the demo:
it is the same route the Shortcut on a real phone calls, the same RLS the real
family gets, and the same templates the real digest sends.

## What is deliberately not here

Onboarding wizard, Shortcuts links, family codes, billing (all 005b). Any ladder
or alert surface. Settings or editing of any kind — read-only means read-only.
Push notifications. **Analytics of any kind**, including the privacy-friendly
sort; product law #4 does not have an exception for well-behaved trackers.
