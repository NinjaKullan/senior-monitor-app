# Wave D Phase 0 — connect the real number (founder walkthrough)

Companion to spec 011 §2. Consoles only, no code, no repo change.
Everything here is yours to do; nothing needs Fable until the checkpoint
at the end.

## Before you start

- You need: Twilio console login, and the Meta Business Manager login
  for the account that holds the family's WABA. Use THAT Meta account
  when the embedded signup asks you to log in — logging in with a
  different Facebook/Meta identity is the most common way this flow
  goes sideways.
- Already true, no action: display name "HeyKettle" approved; number
  +1 984-370-4452 sits in the family's WABA.

## Steps

1. Twilio Console → Messaging → Senders → WhatsApp senders.
2. Click to create a new sender. This launches Meta's embedded signup
   in a popup (allow popups if it doesn't appear).
3. Log in to Meta with the account that owns the WABA.
4. When asked to create or select a business portfolio / WhatsApp
   Business Account: SELECT the existing WABA. Do not create a new one.
5. Select the existing number +1 984-370-4452. Do not buy or add a new
   number. The approved display name rides with the WABA; you should
   not be asked to propose a name, and if you are, it is "HeyKettle"
   exactly.
6. If prompted to verify the number, complete the SMS or voice code
   step on that number.
7. Finish the flow and return to the Twilio console.

## Done when

The sender for +1 984-370-4452 appears in Twilio's WhatsApp senders
list with status **Online**. "Pending" for a while is normal; give it
up to a few hours before worrying.

## Do NOT do yet

- Do not create or submit any message template. That is Phase 1, and
  the submission text gets PM review against DECISIONS first.
- Do not touch the sandbox configuration. It stays live until Phase 3
  sunset.
- Do not point any product config at the new sender. That is Phase 2
  (CC, after template approval).

## If it goes sideways

- Wrong Meta account used / WABA not offered: cancel out, log out of
  Meta in that browser, restart the flow with the right login. Nothing
  is damaged by abandoning the popup mid-flow.
- Number won't attach or shows as in use elsewhere: stop, note the
  exact error text, and bring it back. Do not try to deregister the
  number from anything to force it.
- Anything else: screenshot the error, stop there. No step in this
  phase is destructive, so stopping mid-way is always safe.

## Checkpoint

When the sender shows Online, tell Fable "Phase 0 done" (a screenshot
of the senders row is ideal). That unlocks the Phase 1 template
submission review.
