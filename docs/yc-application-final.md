# YC Fall 2026 — Kettle — FINAL (paste-ready)

*Deadline: TODAY, Sun Jul 27, 8:00pm PT (11:00pm ET). All decisions resolved — everything below is final and paste-ready.*

## Basics / Role / Background

Same as RosterPro application (name, contact, Apex NC, age 47, Founder, 100% equity, technical founder: yes, school: no, exclusive commitment: yes, LinkedIn, education, Martin Marietta).

**Accomplishments:**
> I ship products for the people around me: RosterPro (youth-sports coordination, live and in weekly use by my own team, parents on the PWA), gimbl (a game built for my son, published on itch.io), and now Kettle (running on my mother's phone as of this weekend). I build what my family needs, then find out how many families need it too.

**Who writes code / non-founder work?**
> I write and direct all of it. I run a spec-driven workflow with AI agents: I write the product decisions and specs, Claude Code implements against them, and a second AI session reviews every diff before it merges. Pytest and ruff gate every commit. No non-founder human has written any of it. The pilot backend went from spec to deployed on Fly.io in one weekend this way.

**Are you looking for a cofounder?**
> Yes. Two committed builders from my network are ready to join if accepted: an infrastructure engineer with deep AWS experience (the same one named in my Spring application) and a mobile development expert, which matters because the product build is Android-first. I'm also willing to relocate to SF for the batch. That said, I've built everything so far solo and I'm not waiting on anyone to ship. This pilot's backend went from spec to deployed and collecting in one weekend.

## Company

**Company name:** Kettle

**50 chars or less:**
> Know your aging parents are OK — without cameras.

**What is your company going to make?**
> Kettle gives adult children peace of mind about aging parents who live far away, without surveilling them. Japan solved elder monitoring 25 years ago with a kettle that emails your kids when Mom makes tea. Detect the absence of routine, observe nothing else. Your parent's phone is already that kettle. Kettle passively notices that the normal routine happened (WhatsApp opened, phone charged) and stores three fields: who, which routine, when. No content, no location, no camera, no wearable, no health data. When a routine breaks, the phone asks the parent first: "All good? Tap yes." Family is pinged only if she stays silent, and a local responder we help arrange is the final step. The family gets two quiet messages a day: "Mom's day started normally" in the morning and a short evening digest. There is also an app for the anxious moment. You are in the middle of a movie and think of your mother, or a cousin asks how she's doing and you realize you've been taking the morning text for granted. You open the app, it says all normal, and the anxiety is gone. We show no activity counts and no trend charts, because those become ammunition for family friction. An opt-in MCP integration lets the family's own AI assistant (Claude, ChatGPT, whichever they use) answer "how has Amma's week been?" from the same three fields. First market: families separated by distance, starting with the 5M Indian-American corridor, where the pain is sharpest, the buyer earns in dollars, and nobody serves both sides of the ocean. Then other diasporas and American long-distance families, who are already asking for this in every eldercare forum.

**Where do you live / where based after YC?**
> Apex (Raleigh), NC today; willing to relocate to SF if that's right for the company — open to YC's guidance.

## Progress

**How far along are you?**
> The 30-day family pilot on my own parents (both in their 70s, Chennai) is starting now. The backend is built and deployed as of this weekend: webhook ingestion, a personal-baseline status page, and heartbeat alerting that goes only to me. My mother's iPhone is instrumented with consented, content-free routine signals. My father's phone is set up this week after our consent conversation. He is a privacy-minded attorney, and whatever he redlines in my one-page consent doc becomes the product's privacy spec. The protocol has pass/fail gates written down before data collection: signal completeness, baseline stability, false-escalation rate, and whether my father keeps it installed for 30 days. Day labels are logged blind; my own dashboard refuses to show data until the day's ground-truth labels are entered. A second pilot wave of friends and families, US-domestic included, is lining up behind it. Before writing any code I ran adversarial diligence with three frontier AI models on the fashionable version of this idea, passive decline detection. All three killed it, and that discipline shaped what I'm building instead. Previously: built and shipped RosterPro solo. It is live and in weekly use by my own team, with parents on the PWA.

**How long have you been working on this?**
> ~3 weeks: structured diligence and pilot design first, then the pilot backend built and deployed in the past week. Part-time alongside my day job, mornings and weekends.

**Tech stack (incl. AI models/tools):**
> Pilot: Python 3.12, FastAPI, SQLite, Fly.io (Singapore region for Chennai latency), iOS Shortcuts as the senior-side signal source, ntfy for founder alerts, pytest and ruff gating every commit. Development runs as a spec-driven AI-agent workflow. I act as PM and write specs, Claude Code (Opus) implements, and a separate Claude session (Fable) reviews every diff. Adversarial red-teaming between models is part of the product process, not just the code process. Product build: Android-first (Kotlin) for the India-side market, an iOS tier via productized Shortcuts, and the WhatsApp Business API for the senior-first "all good?" check-in.

**Are people using your product?**
> No — pilot participants only (my parents; 30 days of data by late August).

**Do you have revenue?** > no

## Idea

**Why this idea? Domain expertise? How do you know people need it?**
> I left India 26 years ago. My parents are in their 70s in Chennai; my sister is in Texas. Between timezones, kids, and work, my check-ins decayed from daily to weekly, and the calls that do happen are tactical. How's work, how are the kids, okay good, okay bye. What's left is a guilt that isn't dramatic, just a low hum that never really goes away. When I started researching this, I found the same feeling described almost word for word across Reddit's eldercare and NRI threads: the hum, the fear that something will blow up and the parents won't say anything, and the same question over and over: how do I know they're okay without pointing cameras and AirTags at them? Some of those posters live forty minutes from their parents. The pain is not Indian; the corridor is just where it is sharpest and least served. I am the customer. My parents are users zero. My mother will accept anything I install. My father is a privacy-minded attorney who will fight every permission, and if the design survives him it survives the market's hardest segment. I also tried existing products for my own parents. Everything ended up abandoned or resented, and that taught me why the whole category keeps failing: every product taxes somebody's habits. The senior has to wear it, charge it, answer it, or remember it. The child has to check a dashboard or coordinate check-ins. Discipline is the exact resource that distance already used up. A family organized enough to sustain new daily habits would just call. Kettle asks nothing of anyone. The parent lives a normal day; the child gets two quiet messages. That is why I believe this succeeds where the others didn't. I'm recruiting a second pilot wave now from these communities and my own network, US-domestic families included. Professionally I run planning analytics and AI/ML teams, and I've shipped consumer products solo.

**Competitors? What do you understand that they don't?**
> The closest is Parents Are OK, a new app by a founder in Portugal with his mother in Romania: passive phone-inactivity alerts, no GPS, no camera. It validates the category, and it is a smoke detector. One fixed 24-hour rule and an alert straight to the family. Nothing before the alert (no senior-first confirmation, no personal baseline, so a broken morning routine surfaces a day late) and nothing after it (their own FAQ says it is not for emergencies; the alert lands and the family is on their own, an ocean away, which is exactly where our product begins with the escalation ladder and the local responder). It also sends nothing on good days, the same silent-until-alarm model that killed Alexa Together's retention, versus our daily positive digest. The rest of the field: Life360 and Snug are location-centric and US-only. CarePredict and envoyatHome are $500 hardware, home-bound, and feel like surveillance. Medical alerts carry stigma and only react. Apple's Health Sharing is a real threat on the signal side, but the product isn't the signal. It is the senior-consent design, the escalation ladder that ends in a local human, and the cross-border family experience. India's eldercare services (Emoha, Samarth, Yodda) are partners rather than competitors; they are our last rung. What I understand that the RFS-chasing entrants won't: seniors reject being watched, and the science for passive decline detection isn't there. Apple and Biogen's 23,000-person study couldn't validate it, and Mindstrong burned $160M trying. I ran that diligence before writing a line of code and designed for what survives it: coarse routine-failure detection with senior-first confirmation. And the hardest onboarding step, naming the local human at the end of the escalation chain, is not an edge case. It is the business model.

**How will you make money? How much?**
> The adult children pay. Pricing is per parent monitored, not per watcher: $20–30/mo per parent, with the digest and alerts going to the whole family circle, around 10 recipients. Siblings in the loop are a retention feature, because a family that is collectively watching doesn't churn when one member gets busy. A premium tier at $40–70/mo adds the on-the-ground responder through partners in India (Emoha, Samarth, Yodda). Not dependent on Medicare; I verified that RPM/RTM codes don't cover this data class. Beachhead math: 5M Indian-Americans, roughly 1M households with aging parents in India. 2% penetration at $25/parent/mo is about $6M ARR, before other diaspora corridors, American long-distance families (the Reddit threads show they're already looking), and employer caregiver benefits. The durable asset is the closed loop of alerts, causes, resolutions, and the responder network. No platform vendor bundling raw signals will build that.

**Category:** Consumer *(note for Hema, not for the form: we choose Consumer, not Healthcare, on purpose. Kettle stays in the general-wellness lane: no diagnostics, no medical claims. That is a regulatory position.)*

**Other ideas considered:**
> RosterPro (youth-sports coordination; applied Spring 2026) is shipped and in live use with my own team, and remains a side product. I'm applying with Kettle because it is the problem I personally wake up with, the pilot is already producing data, and the YC RFS on aging will flood this space with teams building the surveillance version. Someone should build the one seniors will keep installed.

**If applying with a different idea than a previous batch: why did you pivot, and what did you learn?**
> Different idea. In Spring 2026 I applied with RosterPro, a youth-sports coordination app. I wasn't accepted, and I shipped it anyway; it is live and my own team uses it weekly. This isn't so much a pivot as running into the company I should have been building all along. Two lessons carried over. First: charge the motivated payer from day one. RosterPro serves rec leagues that run on $40/kid seasons and have almost no budget, so monetization is a slow layer on top. Kettle's buyer is an adult child with a US income and an acute recurring worry, and they pay from the first family. Second: I proved I can ship a complete consumer product alone, which is why Kettle's pilot went from spec to deployed backend to an instrumented phone in one weekend. What hasn't changed is that I build for problems I live. I coach my son's team every weekend, and I call Chennai every week.

**Incubator / accelerator participation?**
> No. I have not participated in or committed to any incubator or accelerator.

## Equity

**Have you formed ANY legal entity yet?** > yes

**List all legal entities:**
> LINKABIT AI LABS LLC, North Carolina — my wholly-owned LLC. It houses RosterPro, and Kettle operates under it today. If accepted, I'd form a Delaware C-Corp for Kettle per YC's standard structure, with RosterPro staying in the LLC so Kettle's cap table starts clean.

**Equity breakdown:** > 100% — sole founder. No outside investors, no grants, clean cap table.
**Taken investment?** > no  **Currently fundraising?** > no

## Curious

**What convinced you to apply?**
> Your Fall 2026 RFS names "AI for the Aging Population." I'm building the version of it that adversarial diligence across three frontier AI models says is actually buildable, and I'll have 30 days of real pilot data from two real 70-somethings by decision time. I'll build Kettle either way; costs are low and I can self-fund. YC compresses the two things I can't do alone fast: credibility for responder partnerships in India, and speed against the wave of RFS-driven entrants who will spend a year rediscovering what my diligence already ruled out. I applied last batch with RosterPro and wasn't accepted. I shipped it anyway. This time I'm applying with the company I was born to build. I am the customer, twenty-six years running.

**How did you hear about YC:** X and social media; follow Garry Tan and founder podcasts.

**Batch:** current (Fall 2026)

## Video — FINAL script (~65 sec; use as beat sheet, don't read it — YC says no reciting)

> "Hi, I'm Hema. I left India twenty-six years ago. My parents are in their seventies in Chennai, and my check-ins slid from every day to... every week. And when they do happen, they've become hurried. Not from lack of love — you just start assuming your parents will always be there, and life starts happening. What's left is a guilt that isn't dramatic — just a low hum that never really goes away.
>
> I've tried every product out there for my own parents, and they all failed the same way: they tax somebody's habits, or demand a new lifestyle. Seniors have to wear something, charge something, answer a robot my dad would call 'roll call in jail.' And a family organized enough for new daily habits... would just call.
>
> Japan solved this decades ago with a kettle that emails your kids when Mom makes tea. Detect the broken routine. Watch nothing else. Ask nothing of anyone.
>
> Your parent's phone is already that kettle — that's why we're called Kettle. It's running on my mother's phone right now, and my father — a privacy lawyer — signs off this week. I'm the customer. There are millions of us."

Beats: pause after "low hum that never really goes away" · after "...would just call" · after "Ask nothing of anyone." Phone at eye level, light on face, two takes max, warmer take wins.

## Submission checklist

- [x] Mom's phone: 5 automations live ✅ (set up in TX — works anywhere; the tripwire travels home to Chennai with her)
- [x] Cofounder answer — two committed joiners + willing to relocate ✅
- [x] Entity answer — LINKABIT AI LABS LLC now, DE C-Corp for Kettle at acceptance ✅
- [x] RosterPro status — live, weekly use, own team, PWA ✅
- [ ] Video recorded
- [ ] Pasted into ycombinator.com/apply form
- [ ] Submitted by ~9pm ET (deadline 11pm ET)
- [ ] `git add -A && git commit -m "YC final" && git push`
