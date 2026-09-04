# Spec 015 — The circle: who sees a household, and who can change it

Status: RATIFIED by Hema, 2026-09-04 (DECISIONS 269): all four §11
items as PM recommended. Rulings in DECISIONS 264. Asana 1218034241842672 (layer 2). Builds on 0002
(RLS by membership), 0008 (claim by verified email), 265 (one-family
scoping), spec 013 (code sign-in).

## 1. What this is, and the law it lives under

A CIRCLE is one set of parents and the people who look after them.
Kettle's `families` row already is one; this spec gives it the two
things it lacks: a way to add and remove people from inside the app,
and a way for a person who belongs to two circles to pick one.

LAW (founder, 264): every role and every switch must be explainable
in one sentence to a sibling over the phone. Kettle's core is
monitoring; notes, numbers and documents are value-add; nothing here
is a secret store. Where this spec had a choice, it took the simpler
one and says so.

## 2. Words

- Circle: a `families` row. The app never shows its name unless the
  account belongs to more than one (law: "this app never says which
  family you are looking at" stands for every single-circle account).
- Seat: a `members` row. A seat exists before its person has signed
  in; the person claims it by signing in with the seat's email (0008,
  unchanged).
- Admin: a member who can add and remove seats, make another member
  an admin, change the parents' numbers and timezone, and cancel.
- Member: everyone else. Writes notes, contacts and documents exactly
  as an admin does. No secrets, no read-only tier.

One sentence each: "An admin can add or remove people; a member can
do everything else." "Kettle emails everyone in the circle unless
they turn it off."

## 3. Rulings carried in (264)

1. Two roles, admin and member. Full write for both on family content.
2. A circle always has at least one admin. The last admin cannot leave
   or demote themselves without making someone else an admin first.
   Setup nudges a second admin from day one.
3. The payment method belongs to the circle (`families.stripe_customer_id`
   already), not a person; any admin can change it. No payer role.
4. Seats are created on demand by an admin, by name and email; never
   pre-created beyond the admin's own.
5. Mail is on for every member by default; one switch per member turns
   all Kettle mail off. Follow-ons go to everyone still on, admins
   first. If nobody is on, the app says so.
6. Cap: eight seats per circle. Premium beyond it only if cost argues.
7. Parent-side visibility: parked.
8. A removed person sees nothing and gets no message.

## 4. Two simplifications proposed here (founder to confirm, §11)

- NO invite code. The task notes borrowed a per-circle code from the
  cricket project. Here the seat's email is verified by the sign-in
  code before 0008 links it, so a second code protects nothing and is
  one more thing to explain. Drop it.
- NO wizard step yet. Beta families are provisioned by the founder
  (005b), so "Who else should see this?" at signup has no signup to
  live in. The Family screen's "Add someone" is the whole feature;
  the wizard step lands with self-serve signup.

## 5. Data

Migration numbers are assigned at build time from the next free file
and recorded in the ledger; specs stop pencilling them (268).

- `members.role`: values become `admin` and `member`. Existing
  `owner` rows become `admin`; existing `child` rows become `member`.
  The check constraint follows.
- `members.mail boolean not null default true`. `digest_channel`
  stays as it is (untouched by this spec; a cleanup item once nothing
  reads it).
- Seat cap: enforced in the add function, not the schema.
- "At least one admin": enforced in the functions that change roles
  or remove seats, with a test that proves the last admin is stuck
  until they promote someone.

## 6. Functions (SECURITY DEFINER, `authenticated` only, 0004 doctrine)

Every one checks that the caller is a member of the circle it
touches, and for admin actions that the caller is an admin there.
None takes a family id from the client that the caller does not
belong to; all resolve through `app_current_family_ids()`.

- `app_add_seat(family_id, display_name, email)` — admin. Inserts a
  member row, role `member`, mail on, auth_user_id null. Refuses a
  ninth seat and a duplicate email within the circle. Returns the
  new member id.
- `app_remove_seat(member_id)` — admin. Deletes the row. Refuses if
  the target is the last admin. A removed person's next load shows
  the existing no-family screen (or their other circle).
- `app_set_role(member_id, role)` — admin. Refuses to demote the last
  admin, including themselves.
- `app_set_mail(mail)` — any member, on their own row only.
- `app_leave_circle()` — any member, own row; refuses for the last
  admin.

Claiming stays 0008: sign in with the seat's email, the row links.

RLS: `members` gains no direct insert/update/delete policies; the
functions above are the only write path, which keeps 0004's "no
client write to membership" intact.

## 7. Outbound

`outbound_contacts` returns every member of the circle with `mail`
on and an email on file, admins first, then by created order. The
morning and evening digests and the follow-ons go to all of them.
Idempotency keys stay per (kind, parent, day, member), which
`digest_sends` already has (0006).

If the list is empty: no send, one ops_alert per day (kind
`circle_unreachable`), and the Family screen shows CIRCLE_NO_MAIL.

## 8. Webapp

- Switcher: shown ONLY when the account belongs to two or more
  circles. A row at the top of the left nav listing circle names;
  the chosen id replaces `families[0]` from 265 in every read;
  remembered per browser (localStorage) and defaulting to oldest.
  Single-circle accounts see no switcher and no name.
- Family screen, "Family circle" section becomes the seats list: one
  row per seat, "Name · Admin" or "Name · Member", a claimed seat in
  full ink and an unclaimed one in muted ink with CIRCLE_PENDING.
  Admins see "Add someone", and per row "Make admin", "Make member",
  "Remove". Everyone sees their own "Kettle emails me" switch.
- Removing shows one confirm line (CIRCLE_REMOVE_CONFIRM), no dialog
  chrome beyond the existing pattern.
- MCP constraint (founder direction, Sep 4): every read the app makes
  goes through a function scoped by circle id, never a bare table
  read; that is already the shape after 265, and this spec keeps it
  so a future MCP server can call the same functions.

## 9. Strings (VERBATIM; copy laws)

- CIRCLE_SECTION = "Family circle"
- CIRCLE_ROLE_ADMIN = "Admin"
- CIRCLE_ROLE_MEMBER = "Member"
- CIRCLE_PENDING = "Not signed in yet"
- CIRCLE_ADD = "Add someone"
- CIRCLE_ADD_NAME = "Their name"
- CIRCLE_ADD_EMAIL = "Their email"
- CIRCLE_ADD_SUBMIT = "Add"
- CIRCLE_ADDED = "Kettle will let them in when they sign in with this email."
- CIRCLE_MAKE_ADMIN = "Make admin"
- CIRCLE_MAKE_MEMBER = "Make member"
- CIRCLE_REMOVE = "Remove"
- CIRCLE_REMOVE_CONFIRM = "Remove them from the circle? They will not be told."
- CIRCLE_LAST_ADMIN = "Make someone else an admin first."
- CIRCLE_FULL = "This circle has eight people, which is the most for now."
- CIRCLE_MAIL_SWITCH = "Kettle emails me"
- CIRCLE_NO_MAIL = "No one in the circle is getting Kettle's notes."
- CIRCLE_SWITCHER_LABEL = "Looking at"
- CIRCLE_LEAVE = "Leave this circle"

Role words are nouns a sibling already knows; no "owner", no "seat"
on screen (seat is a build word).

## 10. Migration of what exists

Rehearsal, Suryaprakasam and Whitaker become circles unchanged; each
owner row becomes the admin. The founder's account belongs to two
circles and is the first switcher user; 265's oldest-first remains
the default. The founder's sister is the first seat added through
the app.

## 11. Founder decisions (RULED, DECISIONS 269)

1. No invite code (§4).
2. Switcher label is the family name as stored; the one place the
   name may appear, and only for accounts in two or more circles.
3. §9 strings stand verbatim.
4. Cap at eight.

## 12. Tests (CC)

Functions: non-member refused; member refused for admin actions;
ninth seat refused; duplicate email refused; last-admin guard on
remove, demote, leave; mail switch on own row only. RLS: a two-circle
account reads both, a one-circle account reads one; a removed member
reads nothing. Outbound: recipients = mail-on members admins-first;
empty list → no send + one alert per day. Webapp: switcher hidden
for one circle, shown for two; chosen id scopes every read; seats
list renders roles and pending state; admin controls hidden for
members. Copy-law test walks the new strings.

## 13. Out of scope

Billing screen (own spec); parent-side visibility; invite codes;
per-kind mail preferences; self-serve signup wizard step; the
`digest_channel` cleanup; MCP server itself (spec 016).
