# Custom SMTP for Supabase auth — the plan (DECISIONS 115)

*Planned 2026-08-16, not yet applied. Founder-applied when it happens: every step here is dashboard
and DNS work, nothing in this repo changes except `.env.example`'s documentation of the fact. Owed
before any family that is not the founder's.*

## Why this is on the critical path

Supabase's built-in mailer is dev-grade and rate-limits at roughly **two emails an hour**. The third
magic-link request of the founder's debugging evening returned `429 over_email_send_rate_limit` and
cost an hour; a stranger's family whose second login attempt sends nothing will conclude the product
is broken and leave, and unlike the founder they will not read the auth logs. Magic link is the only
way into the app — there are no passwords — so the mailer is a single point of failure sized for
demos.

The app-side half is already done: the login screen now surfaces rate limits and failures as words,
and sets the it-can-take-a-minute / check-spam expectation on success. Words make the failure
legible; custom SMTP is what makes it rare.

## Provider

**Postmark, transactional-only** is the recommendation; Resend is the acceptable alternative if the
founder prefers one dashboard for future product email.

* Postmark's entire reputation is transactional deliverability, magic links are the canonical
  transactional email, and their separate transactional/broadcast streams mean nothing this account
  ever does can drag auth mail into a promotions tab.
* Resend is developer-simpler and its free tier (~100/day) covers the beta severalfold; its trade-off
  is a younger sending reputation.
* Either clears the real bar: the built-in mailer's limit is ~2/hour, and a beta family's worst case
  is maybe a dozen a day across everyone.

Law #4 check, stated rather than assumed: an SMTP relay for auth mail is transactional
infrastructure, not analytics — no tracking pixels, and **open/click tracking must be switched OFF
in the provider settings** (both providers ship it on by default for some plans; a magic-link email
with a rewritten tracking URL is also a broken magic link, so this is correctness as well as law).

## The steps, in order

1. **Domain.** Send from `auth.getkettle.com` (a subdomain isolates reputation; the apex stays
   clean for whatever 005b's product email becomes). From address: `Kettle <sign-in@auth.getkettle.com>`,
   reply-to `hello@getkettle.com` so a confused parent's reply reaches a human.
2. **DNS, at the registrar:** the provider's DKIM records, SPF include on the sending subdomain, and
   the provider's custom return-path CNAME. Add a `p=none` DMARC record on the apex if none exists —
   monitoring first, policy later.
3. **Provider side:** create the server/domain, verify DNS, confirm the transactional stream, turn
   OFF open/click tracking, note the SMTP host/port/credentials.
4. **Supabase dashboard** → Authentication → SMTP settings: host, port 587, user, password, sender
   name and address from step 1. The SMTP password is a real secret — it lives in the dashboard and
   nowhere in this repo.
5. **Raise the auth rate limits** (Authentication → Rate limits): custom SMTP unlocks them. Set
   email sends to something human-shaped — 30/hour is far above any legitimate family and far below
   abuse-tool territory. Leave the other limits at defaults.
6. **Test, from a clean inbox:** three magic links inside ten minutes (the exact sequence that broke
   the built-in mailer); confirm all three arrive, land in the inbox not spam, and the link works.
   Then one send to a Gmail *and* an Outlook address — the two spam filters that matter.
7. **Record the result in DECISIONS** and update `.env.example`'s comment block to name the sending
   domain, so the next implementer knows auth mail is custom-SMTP and where it is configured.

## Rollback

Toggling custom SMTP off in the Supabase dashboard restores the built-in mailer instantly —
dev-grade, but a working floor. Nothing in the repo needs to change in either direction, which is
the point of keeping this a configuration plan rather than code.
