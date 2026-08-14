# imstillokay.com — a dead competitor's post-mortem, and what it changes

*PM: Fable, 2026-08-13. Source: r/InternetIsBeautiful thread "I made a free daily check-in service
for seniors who live alone" (Feb 2023, 2,915 upvotes, 176 comments) plus the founder's own replies
through Apr 2026. Read this before the next demand claim goes in a deck.*

## 1 The finding that matters

The service is **dead**. The founder (Jouni Flemming, building with a 73-year-old co-founder) wrote
the epitaph himself, twice:

> "There was a massive amount of interest, for example in this post here. But this interest did not
> translate into actual users. So, if anyone is reading this data in the future thinking that this
> kind of product needs to be built because this post got a lot of upvotes: nope … We got hundreds
> and hundreds of people saying how this is a good idea. But no one actually wanted to use this."
> *(Oct 2025)* — and again, Apr 2026: "I closed this down, because no one really wanted to use it."

Nearly 3,000 upvotes, a flood of "this is beautiful," at least three commenters announcing they had
just signed up — and it converted to approximately nothing.

**This is a direct challenge to our own reasoning.** `docs/gtm-roadmap.md` §5 justifies building
ahead of the Day-30 gates partly on "the Reddit demand research replicated it." That research
measured *enthusiasm*, and this thread is the control experiment showing enthusiasm in this category
is nearly free and nearly worthless. The roadmap's other two legs — Parents Are OK's *paying* users
and the pilot's working mechanism — still stand. The Reddit leg does not. Amend the claim rather than
repeat it.

## 2 Why it died, and why that is our thesis

Their design required **the senior to act**: an email arrives, she clicks a button, every day,
forever. The comment section diagnosed the failure in real time, before it happened.

- **Seniors don't do email.** The single most-upvoted feedback (112) came from a non-profit worker:
  "A lot of folks in this demographic simply don't do email … the more steps it takes to check in,
  the more likely folks will be to put it off and then forget entirely." Repeated a dozen times,
  always with the same fix: SMS, or an app, or a button.
- **They forget.** "Many seniors won't remember to push the button daily." "Have it alarm each day
  until pushed, Nanna wont remember otherwise." A commenter whose mother has dementia: "There is no
  way she would remember to check in on her own. **Some sort of passive check in would be amazing.**"
- **They resent it.** The founder's own words on emergency bracelets: people take them "in a bit
  negative way. Like they are being monitored." A grandson: "That's exactly how my grandpa feels —
  like he's being watched and he feels emasculated." And the sharpest line in the thread: "It might
  be the best for the safety of the body, but it's demeaning to the person who lives within it if
  they feel it's demeaning."
- **They game it.** "If I were an elderly person and using that service, I would purposely forget to
  push that button, so my relatives come and visit me from time to time." An active check-in has a
  strategy; ambient routine does not.
- **The saddest one, and the real competitor:** "Me: I set you up on this cool website that lets you
  login and tell me you're ok. / Her: Why wouldn't you just call me? I love to hear from you. It's
  very quiet here."

Every one of those failure modes is a mode Kettle does not have, because nothing is asked of the
parent. That is not a coincidence — it is the whole reason for negative-space monitoring — but it is
the first time we have watched the alternative fail in public with a body count.

## 3 The buyer, stated by a stranger

The most commercially useful comment in the thread, unprompted:

> "I think maybe you're targeting the wrong audience? … targeting me who has aging parents would
> also be a way, I would happily subscribe to this service for my own peace of mind. Am sure there
> are more of us."

They built a free product for the senior. **The willingness to pay sits with the adult child**, which
is exactly who Kettle charges and exactly whose anxiety the landing page addresses. A second
commenter volunteered to pay for hardware on top of a free service. Sample of two, but it is the
same two the pricing model assumes.

## 4 The kettle, independently invented

Two commenters, unprompted, reached for our metaphor:

> "I saw a version of this in Japan linked to a rice cooker. If the loved one hadn't used the rice
> cooker by a certain time an alert was sent. Saw a similar suggestion for a link to a kettle for UK
> loved ones. Because if rice or tea haven't been made … well something has gone wrong."

> "Have it linked to an IoT socket, switch or plugin. If they're making a cup of tea then they're
> alright."

Useful three ways: it confirms the origin story in spec 006 §11 is a real folk idea rather than a
brand conceit; it shows ordinary people find the appliance-as-signal intuitive with no explanation;
and it is a reminder of **product law #6** — the kettle proves a kettle boiled, not that a person is
fine, which is precisely why our story section says *notice the ordinary* and stops there.

## 5 The category, as the thread reveals it

Named by users, with condition where known: **Snug Safety** (a 2026 user: "the app continually fails
to notify me daily to check in"), **iamfine** (daily phone call, paid), **AllsOK** (Android, daily
notification → email), **Eyeon** (terminated Mar 2024), **imstillokay** (dead; had moved to ~$15/mo
before closing), and from the earlier name search, **Daily OK** and **AssureOkay**. Two dead, one
flaky, all built on the same active-check-in mechanic. The graveyard is a moat: the obvious version
of this product has been tried repeatedly and keeps not working.

Also worth noting for the free-tier temptation: the free product still failed. Price was not the
barrier; **the daily ask was**.

## 6 What to do about it

1. **Amend the demand claim.** Drop "Reddit demand research replicated it" from the GTM reasoning
   and any investor narrative. Replace with the honest version: *enthusiasm for this category is
   abundant and near-worthless; the only credible demand signals are paying users (Parents Are OK)
   and our own waitlist conversion.* Which raises the stakes on migration 0009 — the waitlist is
   now the primary demand instrument, not a nice-to-have.
2. **Make "nothing to remember" a first-class marketing claim.** The hero already says "No new
   devices — only the phone they already have." The unclaimed half is the daily ask: no button, no
   daily tap, nothing for her to do. Candidate for a future amendment, not a scramble.
3. **Distribution note:** r/agingparents was recommended twice in-thread as the place caretakers
   actually gather, and a homebound-seniors caseworker in rural Georgia asked for something like
   this. Both consistent with the GTM's community-first channel plan; the eldercare-worker angle is
   an under-explored one.
4. **Do not build a hardware button.** Half the thread asks for it. It is a per-unit-cost, shipping,
   battery-replacement, RMA business attached to a software product, and the pressure-mat and
   motion-sensor variants are household-grade signals that law #6 forbids from speaking for a
   person. The demand is real and the answer is still no.
5. **One design borrow:** their grace period (3 hours) was invisible on the site until a user
   complained they could not find how long the gap was before contacts got emailed. Ours is a ladder
   setting — make the wait legible wherever a family can see it. Fold into 005b.
