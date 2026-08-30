# Wave 1, asset #1 — "Is Mom or Dad okay living alone?"

Content draft for PM review. Nothing published. Governed by DECISIONS 195
(two registers) and 198 (wave-1 list, house print spec).

Ships as three files:
- `[web]` page at /resources/okay-living-alone/
- `[paper]` print-only PDF, US Letter, 3 pages
- `[paper]` fillable PDF, same layout, AcroForm checkboxes and text fields

Built. Files on disk:
- `site/public/resources/okay-living-alone/index.html`
- `site/public/resources/okay-living-alone/okay-living-alone-checklist-print.pdf`
- `site/public/resources/okay-living-alone/okay-living-alone-checklist-fillable.pdf`
- `tools/printables/asset1_okay_living_alone.py` (generates both PDFs from one
  content block so the two versions cannot drift; rerun after any copy change)

Free download, no email (195 gating ruling).

---

## PAPER REGISTER — the printable, full copy

**Title:** Is Mom or Dad okay living alone?

**Subtitle:** 30 things worth noticing. A checklist for adult children.

**Intro:**

This is not a test and there's no score at the bottom. It's a list of things
worth noticing, written for the visit where everything looks fine and you
still drive home uneasy.

Answer for how things are now compared with a year ago. One check mark on its
own means nothing. Three or four in the same section usually means something
worth a conversation, either with them or with their doctor.

Take it with you. Fill it in afterwards, not in front of them.

---

### Food and the kitchen

1. There's food gone bad in the fridge, or very little food in it at all.
2. They're eating the same one or two simple things every day.
3. Pans, the stove or the microwave show signs of something burned.
4. They've lost or gained noticeable weight since you last saw them.
5. Cooking has quietly stopped, and it used to be something they did.

Notes:

### The house

6. Dishes, laundry or trash are piling up in a way they never used to.
7. Something has been broken for months and nobody has fixed it.
8. There are rugs, cords or piles in the walking routes through the house.
9. There's nothing to hold on to in the bathroom.
10. The route from the bed to the bathroom is dark at night.

Notes:

### Medicines

11. There's no one place where all the medicines live.
12. You find pills loose on counters, tables or the floor.
13. They can't tell you what one of their medicines is for.
14. Bottles are running out much faster or much slower than they should.
15. Nobody outside the house has a current list of what they take.

Notes:

### Getting around

16. They hold on to furniture or walls to cross a room.
17. They've had a fall, or you think they've had one they didn't mention.
18. Stairs, the tub, or getting out of a chair have become an event.
19. There are bruises they explain vaguely, or don't explain at all.
20. They've stopped going somewhere they always went.

Notes:

### Money and mail

21. Unopened mail is stacking up.
22. Bills have gone unpaid, or been paid twice.
23. There are charges, subscriptions or gifts you can't account for.
24. Someone new is calling or visiting often, and money is involved.
25. They're vague or defensive about money in a way they never used to be.

Notes:

### How they seem, and reaching them

26. They repeat the same question or story inside one conversation.
27. They've been unsure what day or date it is more than once.
28. They've dropped a hobby, a group, or the friends they used to see.
29. They seem flat, anxious, or angrier than is usual for them.
30. You often can't reach them, and there's nobody nearby you could ask to
    go and knock on the door.

Notes:

---

### What to do with this

**One check mark is noise.** People have bad weeks. What matters is a cluster
in one section, or the same item still true in three months.

**Take the specifics to their doctor, not the conclusion.** "She's had two
falls she didn't tell me about and she's lost weight since March" gets further
than "I'm worried about my mother." A doctor can also say the thing you can't
say without it becoming a fight.

**Fix the physical things first.** A light on the landing, a bar in the
bathroom, the rug that's been curling for a decade. Nobody argues about a
light bulb, and these are the items on this list that are cheapest to close.

**Number 30 is the one people skip.** Being unreachable is not a small thing
when there's nobody within twenty minutes of the front door. If that line is
checked and you have no name to call, that's the first gap to close, before
any of the others.

**Footer:** heykettle.com

---

## WEB REGISTER — the page copy

Slug: `/resources/okay-living-alone/`
Title tag: Elderly parent living alone checklist, free and printable · HeyKettle
Meta description: A free printable checklist for adult children wondering
whether an elderly parent is still okay living alone. 30 plain things worth
noticing, and what to do with the answers. No email required.
(og:title stays in our voice: "Is Mom or Dad okay living alone?", since that
is the text a person sees when the page is shared.)

**H1:** Is Mom or Dad okay living alone?

**Opening (this is the contrast position permitted by 195, and the only place
the searcher's vocabulary appears):**

Search "elderly parent living alone checklist" and you'll get a dozen lists of
warning signs, most of them published by companies that sell assisted living.
They're not wrong, exactly. They're just written to end in a phone call to a
sales team.

This one is a sheet of paper. It's free, there's no email box, and it ends
with you knowing what to do next.

[the 30 items, rendered on the page in the same six sections]

[What to do with this, same four points]

**Download block:** Print version (PDF) · Fillable version (PDF)
One page for the fridge, one for the sibling who lives 900 miles away.

**Closing line:** I'm Hema. I built HeyKettle after realizing how much of my
day went on wondering whether the morning in Chennai had been a normal one.
It asks nothing of my parents.

---

## Notes for the PM

**Vocabulary, and one thing your ruling 4 didn't quite cover.** You wrote
"title tag and meta only" and said what I shipped was exactly the rule. It
wasn't, quite: the H1 was clean, but the page's opening body line quoted the
search phrase in contrast position, which 195's Google rule permits and your
ruling's wording does not. I've taken your wording as governing and rewritten
that line without the word, so "elderly" now appears only in the title tag and
meta description on both new surfaces and nowhere below the H1. The line now
reads "Search for a checklist about a parent living alone and you'll get a
dozen lists of warning signs..." Say the word if you'd rather have the exact
phrase back in the opening; it is a small ranking loss as it stands.

Following the same ruling in the other direction: the title tag and meta
description previously had no search phrase in them at all, so the page had
its doorway shut. They now carry "elderly parent living alone checklist"
outright. og:title and the H1 stay in our voice.

**The old CTA is dead.** The round-1 research had a CTA written for this asset:
"A checklist gives you a snapshot. Passive monitoring can help you see changes
in everyday routines between visits." That describes Kettle with a banned word
and also describes how it works. Not used. Replaced with the closing line
above.

**The 30 items are new.** The round-1 docs only ever specified the title
"30-Point Family Checklist" and never listed a single item. These 30 are drawn
from the round-1 Reddit research (falls people hide, pills loose on the floor,
mail piling up, the scam pattern, the unreachable-parent thread) plus the
small-items research. Nothing is invented from a clinical source and nothing
claims a statistic.

**NIA attribution: your call.** 198 adopts the house print spec from NIA's
senior-friendly print guidance. The standing line is "Content informed by
resources from the National Institute on Aging." We took their typography
guidance, not their content, so putting that line on this sheet would slightly
overstate it. I've left it off. Say the word and it goes on.

**Item 30 does double duty.** It's the honest last item and it's the hand-off
to article topic 8 and, later, to asset #6. It's also the closest the sheet
comes to being about us, which is why it's phrased as a gap to close with a
name and a phone number, not with a product.

**Page count: three, not two.** I guessed two before building it. At the house
spec (14pt, 60-character lines) thirty items plus the guidance will not fit in
two, and I would rather be over the norm than shrink the type below what 198
adopted. It lands as a clean three: page 1 is the intro and sections 1 to 3,
page 2 is sections 4 to 6 plus the notes area, page 3 is the guidance and the
contacts block. No section splits across a page. If you want two pages, the
guidance page comes off and lives only on the web page.

**One thing on the sheet that isn't in the copy above.** Page 3 ends with a
short "If you can't reach them" block: four labelled lines for a neighbor, a
nearby relative, the building or front desk, and their doctor, with fillable
name and phone fields. It exists because the guidance tells people to close
item 30 and it was hollow to say that and then give them nowhere to write the
name. It touches asset #9's territory (build the local safety net), so if you
want that kept clean for #9, say so and it comes out.

**Not in this build:** asset #3, the changes tracker, which 198 says ships as
this page's download. This draft has no link to it yet. Flag when you want it.

**Verification gate.** Nothing in this asset depends on the five outstanding
researcher verifications: no phone numbers, no FEMA or Medicare references, no
NIA content reused, no page counts cited. 198's "writer may start on wave-1
assets that do not depend on these" covers it.
