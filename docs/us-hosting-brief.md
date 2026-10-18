# Move the database and the product hosts to the United States (brief for Claude Code)

Founder ruling, 2026-10-18 (DECISIONS 365). The privacy page says data is stored in
the United States. Today the Supabase project is in ap-south-1 (Mumbai) and
kettle-api and kettle-app run in Fly region sin (Singapore), a leftover of the
Chennai pilot. The page stays as written; the hosting moves to match it. One
family's worth of data, so the move is small now and only gets bigger.

Target: Supabase project in us-east-1; kettle-api and kettle-app in Fly region
iad (where kettle-site already is). Nothing changes for parents' phones, the
Twilio webhook, Resend, the assistant connectors or any public address.

## 1. Code changes (the whole list; nothing else)

1. `product/fly.toml` and `webapp/fly.toml`: `primary_region = "iad"`, comment
   updated (the Chennai latency note goes).
2. Any test or doc that pins `sin` or Mumbai as the live region (grep
   `sin"`, `ap-south`, `Mumbai`, `Singapore` across product/, webapp/, docs/,
   README files): update to iad / us-east-1. `docs/baton.md` host lines included.
3. A runbook section at the end of this file, §3, written by CC with the exact
   commands, in the order below. The PM's draft of the order is §2; CC corrects
   it where the tools say otherwise, as happened in 357.
4. No schema change, no migration, no copy change. The privacy page is not
   touched.

## 2. Cutover order (PM draft; CC rewrites as §3)

Before: founder enables two-factor on the Supabase account (done or in
progress), and confirms migration 0034 is applied on the old project.

1. Founder creates the new Supabase project (us-east-1, same org), records the
   project ref, the service-role DATABASE_URL, the publishable key, the JWKS URL.
2. PM applies migrations 0001 to 0034 in order to the new project, one file at
   a time. Empty database at this point.
3. Announce a 30-minute window. Pings that land in the window are lost; that is
   acceptable (the day's "heard from" catches up at the next ping).
4. Founder dumps data from the old project: `public` schema data only, plus
   `auth.users` and `auth.identities` data so the user ids referenced from
   public tables match. Restores into the new project. CC writes the exact
   pg_dump / psql lines, including what to exclude (supabase-owned schemas,
   sequences are reset by the restore).
5. Founder sets kettle-api secrets `DATABASE_URL` and `SUPABASE_JWKS_URL` to
   the new project (one `fly secrets set`, so one restart).
6. Founder rebuilds and deploys kettle-app with the new `VITE_SUPABASE_URL` and
   `VITE_SUPABASE_PUBLISHABLE_KEY`.
7. New project's Auth settings: site URL and redirect list copied from the old
   project (app.heykettle.com and the fly.dev host; see 357), email-code sign
   in on, the same email template.
8. Fly regions: move kettle-api and kettle-app machines to iad and remove the
   sin machines. CC names the commands (clone-then-destroy, or scale by
   region) and what to check between them (`fly machines list`).
9. Verify: `/healthz` on api.heykettle.com; sign in on the app (everyone signs
   in again; sessions do not survive a JWKS change); a Rehearsal parent's
   ping lands; the Claude connector still answers `today` without
   re-authorising (grants live in the copied tables); the weekly site email
   still schedules.
10. Old project: pause for 14 days, then delete. Update `docs/baton.md`, the
    infra facts, and the Meta data-processing form (storage: United States
    only).

## 3. Runbook (CC writes this section)
