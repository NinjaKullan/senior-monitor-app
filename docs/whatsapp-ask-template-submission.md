# WhatsApp ask template — submission text (spec 011 Phase 1)

**Status: PM REVIEWED AND SIGNED OFF, 2026-08-29.** Body, zero
variables, and button verified independently (53 codepoints, bare
U+1F44D, no U+FE0F). Category **Utility** confirmed; template name
**`kettle_ask_parent`** confirmed (Hema may veto the name before
submitting — it is permanent once approved). Nothing has been
submitted; submission waits on Phase 0, which waits on Meta's review
of the Kettle Labs portfolio restriction (requested 2026-08-29). Hema submits through
Twilio's Content Template Builder after the PM signs this page off; Meta
approval usually takes hours to a couple of days. Approved copy is then
recorded verbatim in DECISIONS, per standing law.

Prepared 2026-08-28 by extracting the shipping strings from the code, not by
retyping them. Nothing in the repo was changed to produce this page.

---

## 1. The body, verbatim

```
Everything okay today? Reply with a 👍 whenever suits.
```

Extracted from `product/kettle/outbound_templates.py`, template id
`ask_parent`. Fifty-three characters, and the exact bytes matter — the emoji
is **U+1F44D THUMBS UP SIGN, bare**, with no U+FE0F variation selector after
it. Paste this line rather than typing it; a keyboard or an editor that
"helpfully" adds the selector produces a different string from the one that
has been reaching a parent since Wave C.

## 2. Verification against the DECISIONS record

DECISIONS 151 item 4 records the founder-approved ask. Compared
character for character, by codepoint, between the registry source and the
DECISIONS text:

| | |
|---|---|
| Code (`ask_parent.body`) | `Everything okay today? Reply with a 👍 whenever suits.` |
| DECISIONS 151 item 4 | `Everything okay today? Reply with a 👍 whenever suits.` |
| Length | 53 codepoints, both |
| Equal | **yes, exactly — no drift** |

**One difference that is not drift, flagged so it cannot be pasted by
mistake.** `site/src/copy.ts` carries `OFF_NOTIF`:

```
Everything okay today? Reply whenever suits.
```

That string is shorter and has no 👍. It is the marketing page's
*illustrative* quote, and DECISIONS 150 explicitly relaxed spec 007 §5's
"verbatim from the site" binding to "the site's quote is illustrative" —
so this is a ruled difference, not a regression. **The product string above
is the one to submit.**

## 3. Variables

**None.** `ask_parent` declares `variables: ()` — the body has no
placeholders at all, and the registry's renderer rejects any variable passed
to it. So the template is submitted with **zero variables**; there is no
`{{1}}`, and no sample values are needed for approval.

This is deliberate and worth stating to the reviewer: the ask is the one
message that names nobody. Every other template in the registry carries
`{relationship}`; this one is addressed *to* the parent, so it needs no label
for them and may not carry one (DECISIONS 149).

## 4. The quick-reply button

One button, and its text is exactly:

```
👍
```

Again bare **U+1F44D**, matching the emoji in the body character for
character. Ruled in DECISIONS 193.

Why it is safe with the code as it stands today: tapping a quick reply sends
the button's text to us as an ordinary inbound message, and Kettle's reply
intake is **content-blind** — `record_parent_reply` matches an inbound
message from a known number against that parent's pending ask and reads
nothing of what it says. So a tap and a typed 👍 and the word "yes" are all
the same event to Kettle, which is what makes the button additive rather than
a second path to test. Nothing in the parser has to change for Phase 2.

## 5. Template metadata for the Builder form

| Field | Value | Note |
|---|---|---|
| Template name | `kettle_ask_parent` | Meta requires lowercase and underscores; keeping the registry's id in the name makes the ledger and the console line up |
| Category | **Utility** | It concerns an ongoing arrangement the parent set up, not marketing. The pricing note in spec 011 assumes utility |
| Language | English (`en`) | The only language the ask ships in today |
| Header | none | |
| Body | the line in §1, pasted | zero variables |
| Footer | none | |
| Buttons | one **Quick reply**, text `👍` | §4 |

Two fields that are not ours to guess and that the PM should confirm rather
than let the console default: the exact Meta **category** (a template
mis-categorised as marketing can be declined, and utility is the honest
description), and the template **name**, which is permanent once approved.

## 6. What happens to this text after approval

Phase 2 wires the Content SID into config — never a body in code — and the
send path uses the template API for business-initiated asks. The registry
keeps the same body string so the copy scan still governs it, and the ledger
keeps naming the template id it always has. Sandbox behaviour stays present
and functional behind config until the Phase 3 sunset.

---

## Post-submission record (2026-08-30)

Both submissions of this template were refused synchronously by
Meta's Graph API — no review ever happened, which is why WhatsApp
Manager shows nothing. Identical verbatim reason both times
(DECISIONS 205):

> Problem: Failed to create template, Reason: type=OAuthException,
> code=100, subCode=2388060, userMessage=Buttons can't have any
> variables, newlines, emojis, or formatting characters.,
> message=Invalid parameter

The BODY on this page is legal and was never judged; the quick-reply
BUTTON labeled 👍 is illegal by hard platform rule. `kettle_ask_parent`
(HXe33df5abd629b1c75d7dd64aac0f83e3) and `kettle_ask_parent_v2`
(HX31fd2ac24e80fe365a3f7ca35938caa7, copy codepoint-identical) are
both inert — Twilio allows one approval request per content resource.
A v3 per the founder's button ruling supersedes this page's button
row; everything else above stands.

**Resolution (same day):** founder ruled option (a) — drop the
button. `kettle_ask_parent_v3` (HXee3060b2784a551bffda9d12dbb07b86,
twilio/text, no buttons, body verbatim, Utility) submitted
2026-08-30 12:24:44 EDT and confirmed **In review** on the HeyKettle
WABA in WhatsApp Manager — the first submission to genuinely reach
Meta. The v3 supersedes this page's button row; body, name lineage,
and category on this page otherwise stand.
