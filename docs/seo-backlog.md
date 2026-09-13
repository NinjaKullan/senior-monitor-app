# SEO backlog and experiment log

State file for the Domain Authority objective. Companion to
`docs/seo-audit-2026-09.md` (evidence and reasoning). Keep this file in the
present tense; move history into the log at the bottom.

**Next review: 2026-10-06** (first full week of October, after Moz's free
quota resets and the first two weekly metrics emails have landed). Triggers
that bring it forward: a PM ruling on D1 to
D6, a YC decision, or a link reported live. No scheduled job polls anything.

Targets, from the audit §6: DA 10 is the first checkpoint, DA 20 the
long-term target, DA 50+ the ceiling kept on record and not planned for.
Business outcome tracked separately: qualified referral visits (Search
Console clicks) and beta applications.

## 1. Owed now, by whom

| # | Item | Owner | Approval | Why |
|---|---|---|---|---|
| A1 | Search Console: DONE 2026-09-12, readable in the founder's Chrome session (domain property sc-domain:heykettle.com). Keep the session logged in for the monthly reading | Founder | none | audit §2, §8 |
| A7 | Indexing requested in URL Inspection for all eight priority URLs, done 2026-09-12 on the founder's yes, each confirmed by the "Indexing requested" toast: /resources/okay-living-alone/, /resources/emergency-info/, /resources/normal-day/, /resources/changes-tracker/, /resources/, /blog/parent-doesnt-answer-the-phone/, /blog/how-often-should-you-check-on-a-parent/, /blog/the-information-youll-wish-you-had/. Every one showed "Discovered, currently not indexed" with no referring page detected | CC, founder's yes | done | audit T12. Check the indexing report at the next review; a request is a queue entry, not a promise |
| A2 | linkabitai.com anchor: DONE 2026-09-12 by the LinkaBIT agent, verified by curl of the server HTML (plain href, no rel, page not noindexed, robots allows Googlebot and Bingbot) | Founder | done | audit T11; link log row 1 |
| A3 | Cloudflare: Email Address Obfuscation OFF, done 2026-09-12 and verified live. JavaScript Detections cannot be disabled on the Free plan (Bot Fight Mode already off); the beacon stays until a plan change or Cloudflare fixes it. Closed as a platform limit | Founder | done | audit T3 |
| A8 | Cloudflare "Block AI bots" preference set to "Mixed purpose crawlers will continue to be allowed", done 2026-09-12 on the founder's yes and verified after reload. Googlebot, Bingbot and Applebot stay allowed on 09-15; pure AI-training crawlers stay blocked | Founder, done by CC | done | audit T14 |
| A4 | Waitlist count baseline: 0 beta applications as of 2026-09-12 (founder). Done | Founder | done | Baseline for the business outcome |
| A5 | Moz root-domain reading for heykettle.com and, if quota allows, snugsafe.com and parentsareok.app | Founder (the Moz account) | none, no spend | Replaces the exact-page snapshot; peers' DA is unknown (audit §4) |
| A6 | LinkedIn company page for HeyKettle, linking the site. Founder: 2026-09-13 | Founder | founder, creates an account | First foundation listing (S1); peers all have one |

## 2. Decisions for the PM (each is a ruling, not a fix)

| # | Question | Pinned by | Options |
|---|---|---|---|
| D1 | DONE 2026-09-13 (founder ruling 2026-09-12): www is a named host of nginx's redirect block, one 301 to the same path on the apex; canonicalHost.test.ts and test_site_caching.py re-pinned, plant-verified. Live since 2026-09-13 | was: DECISIONS 168 pin | (a) a Cloudflare redirect rule, nginx untouched, canonicalHost test updated to expect the rule; (b) a `www.heykettle.com` server block in nginx alongside the fly.dev one; (c) leave it and rely on canonicals, which resource pages do not have (D2) |
| D2 | DONE 2026-09-13: each resource page carries its own canonical, the register stays bare, resources.test.tsx narrowed like blog.test.tsx, plant-verified. Live since 2026-09-13 | was: PM ruling 2026-08-30 | The blog test already admits one canonical and nothing else; the same narrowing would work for resources |
| D3 | May static pages carry outbound links to the sources they attribute (NIA, CFPB, FEMA, Eldercare Locator)? | The standalone-page tests ban any absolute URL | If yes: allowlist named origins in the test, `rel` left plain. If no: record that the site does not cite by link, and expect S2 to be slower |
| D4 | Replace the em dash in the home `<title>` ("HeyKettle — Know the day started normally.") | LAW-7 | e.g. "HeyKettle. Know the day started normally." or "Know the day started normally. HeyKettle" |
| D5 | Meta descriptions for `/blog/`, `/resources/`, privacy and terms | copy law | PM drafts; the resources test already scans the description slot |
| D6 | Organization and Article JSON-LD | `<script>` banned on static pages | Low priority; only worth a ruling if D3 passes |
| D7 | DONE 2026-09-13: the footer links every guide and every post by its H1 (labels in copy.ts, no new words), the register names the three articles; a disk-derived test holds both; checked at 360/390/768. Live since 2026-09-13 | was: copy law | Internal links are the cheapest crawl signal the site can send for T12; four link texts to draft |
| D8 | Cloudflare's managed robots.txt overrides the repo's and disallows ClaudeBot, GPTBot, Google-Extended and six others, with `ai-train=no` (audit T15) | founder policy | (a) keep: no AI training on the site's text, and no citations from assistants that use those crawlers; (b) switch Cloudflare's robots.txt management off so the repo file is what is served, and decide any AI policy in the repo where a test can hold it; (c) keep the training block but allow search-and-answer crawlers. The repo file cannot currently be trusted as the served file either way |

## 2a. Recommendations on D1 to D8 (Claude Code, 2026-09-12, from first principles)

A search engine rewards three things a site controls: one address per page,
a crawl path to every page, and honest signals about what each page is and
cites. The site's own laws already say "one page, one address" (142) and
"rules live where a test holds them". Each recommendation ships with its
test changed, plant-and-revert.

- **D1, yes, in nginx.** 168 deferred the www question to avoid a loop; the
  data now shows the cost (the www privacy page wins the brand query). A
  third server block 301s www to the apex, one hop, and the canonical-host
  pin changes from "www serves 200" to "www 301s". Not a Cloudflare rule,
  which the repo cannot see or test (the D8 problem).
- **D2, yes.** A canonical is a page's own statement of its address. The blog
  test already admits exactly one canonical; give resource pages the same
  narrowing. Still useful after D1 for `/index.html` variants.
- **D3, yes, to an allowlist of public-sector origins.** The absolute-URL ban
  was a proxy for "fetches nothing"; an anchor fetches nothing until clicked.
  Keep the real ban (no foreign link, script, img, iframe); allow `<a href>`
  to nia.nih.gov, cdc.gov, consumerfinance.gov, fema.gov, eldercare.acl.gov
  and similar. Public sector only, so no vendor endorsement ever appears.
- **D4, promise first, brand last, period separator:** "Know the day started
  normally. HeyKettle". One string in `index.html`.
- **D5, one description, for /blog/.** Resources already has one; privacy and
  terms do not need one, D1 fixes their brand-query impressions at source.
- **D6, Organization JSON-LD on the home page only, later.** Inert data, and
  the home page already runs a bundle. Value is entity disambiguation
  (search confuses "hey kettle" with tea companies). Article markup: no.
- **D7, yes, with zero new copy.** Link each printable and each article from
  the home page using its existing H1 verbatim; link the three articles from
  the resources index. The 18 uncrawled pages are two clicks deep today.
- **D8, switch Cloudflare's robots.txt management off, then set the policy
  in the repo.** The served file must be the tested file. Then: block
  training-only crawlers (GPTBot, CCBot, Bytespider, Google-Extended,
  Applebot-Extended, meta-externalagent), allow search and answer crawlers,
  state "no training" via the Content-Signal line. A blanket block forfeits
  assistant citations for no privacy gain on public pages.

Order: D1+D2, then D7, then D3/D4/D5 as one copy pass, D8 when the founder
has a view on AI policy, D6 last.

## 3. First 30 days (2026-09-12 to 2026-10-12), prioritized

Sessions do not draft outreach or new content until the items in §1 that
gate them are done and the founder has said go.

| P | Item | Owner | Depends on | Evaluate on | Continue if / stop if |
|---|---|---|---|---|---|
| 1 | A1 to A6 above | Founder / PM | | 2026-10-06 | Continue when A1 and A5 are in hand |
| 2 | Prospect list for S2, resource-page inclusion: one row per target with the page URL, its maintainer, what it already links to, which Kettle printable fits, and why. Seed list from `docs/gtm-market-research-2026-08.md` and the audit: PlaneTree Health Library caregiving LibGuide, Caregiver Action Network long-distance page, Daughterhood, Working Daughter, Village to Village member sites, Area Agencies on Aging resource pages, public-library caregiving LibGuides (search "libguides caregiving aging parent"), Where You Live Matters | CC | none | when 25 rows exist | Continue if at least 10 targets already link out to free printables from other makers |
| 3 | Outreach drafts for the top 10 of P2: one personal note each, plain voice, printable named, no ask beyond "if it fits your list", Kettle described in one sentence with no banned word | CC drafts, founder approves each send | P2, A1, A4 | 8 weeks after first send | Continue if 2 of 10 reply; change the note if 0 of 10; never send a second unsolicited note to the same person |
| 4 | Publish blog post 3 ("Small things that actually help"): rule-checked and ready; sitemap and index entries; PM review | CC then PM | PM go | Search Console after 8 weeks | It is brand content, not a search bet; judge on shares and links, not rank |
| 5 | Wave-2 who-to-call crosswalk (DECISIONS 198: dated numbers-checked footer, every number verified on its official page the day the file is generated) | CC, PM review | the five owed research verifications in 198 | 12 weeks after live | Continue if S2 targets cite it; it is the strongest link magnet in the set |
| 6 | Founder editorial list for S3: podcasts and newsletters that interview founders in this niche (Working Daughter, Daughterhood, Happy Healthy Caregiver as guest, Aging and Health Technology Watch, aiht substack). One pitch each, founder voice, no sponsorship | CC lists, founder pitches | founder go | 3 months | Continue if one booking per 10 pitches |
| 7 | YC directory entry if the Fall 2026 application is accepted; Show HN when the product is public | Founder | external | on event | |
| 8 | Monthly reading: Moz root-domain, Search Console, link log, waitlist count, recorded in §5 | CC or founder | A1, A5 | monthly | |

## 4. Later, kept with reasons

- S4 original consented research (a small survey of adult children on calling
  habits and the worry threshold): the strongest press magnet in this category
  (Snug's only earned pickup was a survey) but needs a real audience, consent
  and honest methodology. Not before the beta and a newsletter exist.
- App-store listings when the family app is public: the largest single link
  source for every peer. Product-gated.
- Remaining printables (#5 long-distance planner, #7 home safety check, #8
  "Who's checking on Mom?", #9 local safety net, #10 monthly check-in) and
  keep-listed articles (topics 1, 9, 10, 12, 16, 18, merged 6/17). Topic 18
  first: uncontested SERP.
- Post 2 ("The button in the drawer"): blocked on two founder anecdotes.
- Unlinked-mention and lost-link sweep: nothing exists yet; re-check monthly
  with the Moz reading.

## 5. Ruled out, with the rule

- Reddit, any form: off limits by instruction.
- Paid links, sponsored posts with passing links, guest-post networks,
  directories that charge, bulk directory submissions: Google's link spam
  policy names each.
- Scaled or AI-generated content for search: scaled content abuse policy and
  the writers' brief (no invented anecdotes).
- Expired domains, redirects for score, private blog networks.
- Client-side analytics of any kind, including "privacy-friendly" ones: LAW-9
  and DECISIONS 201.
- Vocabulary: no "monitor", "track", "alert", "elderly", "seniors" about
  Kettle or a parent, anywhere, including outreach and listings. Searcher
  words only in contrast position on web pages (DECISIONS 195).

## 6. Experiment and measurement log

Record source, date, scope, confidence. Never credit an action with a change
merely because the change came after it.

| Date | Reading or event | Source, scope | Value | Confidence, notes |
|---|---|---|---|---|
| before 2026-09-12 | Moz DA 1, PA 16, 9 linking domains, 10 links, 0 followed | founder's Moz screenshot, exact page https://heykettle.com/ | | Low as root-domain baseline; domain registered 2026-08-21, Wayback captures exist from 2025-03 under an unknown prior use |
| 2026-09-12 | Moz root-domain reading attempted | moz.com/domain-analysis in the founder's browser | redirected to free-metrics-limit | Quota spent; retry in October (A5) |
| 2026-09-12 | Indexed third-party mentions of "HeyKettle" | WebSearch proxy | none | Not Search Console |
| 2026-09-12 | Sitemap lastmod corrected to git dates; `cd site && npm run ci` green | repo | 21 URLs | Technical hygiene; no DA effect expected |
| 2026-09-12 | Live pages equal HEAD build except Cloudflare-injected scripts | diff of live vs repo | | No content deploy owed |
| 2026-09-12 | Search Console performance, 2026-08-28 to 09-10 | sc-domain:heykettle.com, founder's browser | 0 clicks, 18 impressions, position 17.8, one query "hey kettle" | High. Baseline for clicks and impressions |
| 2026-09-12 | Search Console indexing | same | 2 indexed, 18 discovered-not-crawled, 1 crawled-not-indexed, 1 alternate (www home), 1 duplicate, 2 redirects | High. Baseline for indexed priority pages: 0 of 8 |
| 2026-09-12 | Search Console sitemap | same | read 09-10, Success, 21 URLs | |
| 2026-09-12 | Search Console links | same | processing, no data | Re-read 2026-10-06 |
| 2026-09-12 | Cloudflare Email Address Obfuscation off; live check shows one script (the bundle) plus the challenge-platform beacon; plain mailto restored | founder's Cloudflare session; curl | | Beacon is a Free-plan limit |
| 2026-09-12 | Cloudflare mixed-purpose crawler preference switched to allowed (A8) | founder's Cloudflare session, founder's yes | | Re-check search crawl in Search Console after 09-15 |
| 2026-09-12 | Beta applications | founder, waitlist | 0 | Conversion baseline |
| 2026-09-12 | Indexing requested for 8 priority URLs (A7) | Search Console URL Inspection | 8 of 8 confirmed | Evaluate: indexed count in the Pages report on 2026-10-06; baseline 2 of 21 |
| 2026-09-13 | D1, D2, D7 deployed (`fly deploy` on the founder's go) and verified live: www 301s to the apex on three paths, four canonicals present, eight footer links and the register's article line served, old host still 301s, healthz ok | curl against heykettle.com | | Evaluate at the 2026-10-06 review: www impressions should fall to zero; indexed count against baseline 2 of 21 |

## 7. Link log

One row per placement. Verified live means the linking page was fetched and
the anchor seen in the server HTML.

| Date reported | Linking page | Target | Attribute | Verified live | Seen by Moz | Notes |
|---|---|---|---|---|---|---|
| 2026-09-12 | https://linkabitai.com/ | https://heykettle.com/ | followed (no rel) | yes, 2026-09-12, server HTML | not yet; check with the October Moz reading | Self-owned entity domain; counts as a referring domain, low weight |
