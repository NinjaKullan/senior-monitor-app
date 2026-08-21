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

**Resend** — founder decision, DECISIONS 138. This document recommended Postmark and named Resend
as the acceptable alternative if the founder preferred one dashboard for future product email; that
is now what he wants, and spec 007's Wave B sends the family digest through the same account.

* One provider for both jobs. Auth mail and the digest are the only email this product sends, and a
  second dashboard for the second one buys nothing.
* Developer-simpler, and the free tier (~100/day) covers the beta severalfold. The trade-off, stated
  rather than glossed: a younger sending reputation than Postmark's, which is why the subdomain
  isolation and the DNS records in the steps below are not optional.
* It clears the real bar either way: the built-in mailer's limit is ~2/hour, and a beta family's
  worst case is maybe a dozen a day across everyone.

The reasoning that pointed at Postmark is kept rather than deleted, because it is what to re-read if
deliverability ever becomes the problem: its entire reputation is transactional deliverability,
magic links are the canonical transactional email, and its separate transactional/broadcast streams
mean nothing an account does can drag auth mail into a promotions tab.

Law #4 check, stated rather than assumed: an SMTP relay for auth mail is transactional
infrastructure, not analytics — no tracking pixels, and **open/click tracking must be switched OFF
in the provider settings** (it ships on by default on some plans; a magic-link email
with a rewritten tracking URL is also a broken magic link, so this is correctness as well as law).

## The steps, in order

1. **Domain — DONE.** The domain is `heykettle.com` and Resend is **verified on
   `send.heykettle.com`** (founder, DECISIONS 142), which is the subdomain this step asked for
   under a different name: a subdomain isolates reputation and the apex stays clean for whatever
   005b's product email becomes. From address: `Kettle <sign-in@send.heykettle.com>`, reply-to
   `hello@heykettle.com` so a confused parent's reply reaches a human. The plan below still says
   "the sending subdomain"; read that as `send.heykettle.com`.
2. **DNS, at the registrar:** Resend's DKIM records, SPF include on the sending subdomain, and
   Resend's custom return-path CNAME. Add a `p=none` DMARC record on the apex if none exists —
   monitoring first, policy later.
3. **Resend side:** create the domain, verify DNS, confirm the transactional stream, turn
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
