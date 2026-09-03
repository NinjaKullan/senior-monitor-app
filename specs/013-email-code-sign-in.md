# Spec 013 — Sign in with a 6-digit email code (magic link kept as the second path)

Status: RATIFIED by Hema, 2026-09-02 (DECISIONS 235); BUILT 2dad423, awaiting founder template edit + deploy (DECISIONS 236): both code and
link in the email, code first. Pre-beta. Asana 1218034241842672
(layer 1). Builds on DECISIONS 115 (make failures visible) and 234
(custom SMTP live).

## 1. The problem, in one paragraph

A family member signs in by tapping a link in an email. On a phone the
link opens inside the mail app's browser, not inside the installed
Kettle app, so the session lands in the wrong place and the app they
tap next still shows the sign-in screen. They conclude Kettle is
broken. A 6-digit code has no such problem: they read it in the mail
app and type it into Kettle. Supabase issues the code from the same
`signInWithOtp` call; the app needs a second step and one dashboard
template edit. Parents are excluded by design: they never sign in.

## 2. What changes (webapp)

Two-step sign-in screen, same file (`src/screens/Login.tsx`).

Step 1 (as today): email field; button **"Email me a code"** (was
"Email me a sign-in link"). On success show LOGIN_SENT and reveal step
2 under it. Failures as today (LOGIN_RATE_LIMITED, LOGIN_FAILED).

Step 2: one field, `inputmode="numeric"`, `autocomplete="one-time-code"`
(iOS offers the code from the mail app), label **"6-digit code"**,
placeholder "000000"; button **"Sign in"**. Submit calls
`supabase.auth.verifyOtp({ email, token, type: "email" })`. Success is
observed by the existing `onAuthStateChange`; nothing else in App.tsx
changes. Below the field a text link **"Send a new code"** which
re-runs step 1 with the same email (the SMTP 60-second per-user
minimum means a quick second tap surfaces LOGIN_RATE_LIMITED; that is
correct behaviour, not a bug). Once step 2 is revealed it is never
hidden again: a rate-limited or failed resend shows its message beside
the "Send a new code" link and leaves the code field and whatever was
typed in place, because the family may be holding a good code from the
first email. (Ruled on the build report, DECISIONS 236.)

Step-2 failures, distinct and in words (DECISIONS 115 posture):
- wrong or expired code (Supabase returns a 403 with "Token has
  expired or is invalid"): LOGIN_CODE_WRONG.
- anything else: LOGIN_FAILED.

The link in the same email keeps working exactly as today (desktop
users tap it; `onAuthStateChange` fires). No PWA detection, no
platform branching: phones get a code because the code is what they
will use; laptops get a link because it is one tap.

`sendMagicLink` in `src/lib/data.ts` is renamed `sendSignInCode`; the
call stays `signInWithOtp({ email })`. New `verifySignInCode(email,
token)` wraps `verifyOtp` and throws on error, same reason as 115.

## 3. Strings (VERBATIM; copy laws apply; no em dashes)

- LOGIN_BUTTON = "Email me a code"
- LOGIN_SENT = "Check your email for a 6-digit code and type it below.
  It can take a minute. Look in spam if it hasn't arrived."
- LOGIN_CODE_LABEL = "6-digit code"
- LOGIN_CODE_BUTTON = "Sign in"
- LOGIN_CODE_RESEND = "Send a new code"
- LOGIN_CODE_WRONG = "That code didn't match, or it has expired. Check
  the newest email, or ask for a new code."
- LOGIN_RATE_LIMITED, LOGIN_FAILED: unchanged.
- Email subject: "Your Kettle sign-in code"
- Email body (Supabase template, founder pastes; see §4):
  "Your sign-in code is {{ .Token }}. Type it into Kettle. It works
  for the next hour and only once. On a computer you can use this
  link instead: {{ .ConfirmationURL }}. If you didn't ask for this,
  ignore it."

## 4. Founder dashboard tasks (before CC deploys)

Supabase → Authentication → Emails → Templates. Edit BOTH "Magic Link"
and "Confirm signup" (a first-time address gets the second one), same
subject and body as §3, `{{ .Token }}` present in each. Leave OTP
length at 6 and expiry at the default (1 hour). Custom SMTP is already
live (234), so the mail arrives from hello@send.heykettle.com.

## 5. Tests (CC)

`src/tests/login.test.tsx`: existing three outcomes on step 1 with the
new strings; step 2 renders only after a successful send; `verifyOtp`
called with `{ email, token, type: "email" }`; wrong/expired →
LOGIN_CODE_WRONG; resend calls `signInWithOtp` again and a rate-limit
error shows LOGIN_RATE_LIMITED; code field has `inputmode="numeric"`
and `autocomplete="one-time-code"`. `sessionRestore.test.tsx`
unchanged in what it asserts (its module mock must list the renamed
exports; that is the only permitted edit). Copy-law test picks up the new strings automatically if it
walks `copy.ts`; if it pins a list, add them.

## 6. Verify live (founder, then PM reads the ledger)

Phone, app installed: request code, read it in Mail, type it, land on
Today without leaving the app. Laptop: tap the link, land on Today.
Phone again, tap the link in Mail on purpose: the old wrong-context
behaviour may still occur there and is now irrelevant because the code
path exists; note it, don't chase it.

## 7. Out of scope

Circles / claimable seats (layer 2, spec 012 phase 2). Any parent-side
authentication. Password sign-in. SMS codes.
