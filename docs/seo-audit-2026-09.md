# SEO audit, heykettle.com, September 2026

Written 2026-09-12 by Claude Code. First milestone of the Domain Authority
objective: current state, the gap to peers, the strategies compared, the
recommendation, and what is owed by whom. The execution backlog and the
experiment log live in `docs/seo-backlog.md`. Nothing here is a spec; a
copy or ruling change named here becomes real only through the PM channel.

Binding rules honoured throughout: `docs/feature-backlog.md` §5 (LAW-7 copy
laws, LAW-9 no client-side analytics), DECISIONS 195 (paper rule and Google
rule), 198, 199, 201 (server logs and Search Console only), 142/168 (canonical
host), `docs/kettle-brief-for-ai-writers.md`. Reddit is off limits for any
activity on Kettle's behalf.

## 1. What Moz says Domain Authority is

Source: moz.com/learn/seo/domain-authority, "Last updated ... March 18, 2025",
fetched 2026-09-12. Documented facts, in Moz's words where it matters:

- DA is "a search engine ranking score developed by Moz" on a 1 to 100 scale.
  It "is not a Google ranking factor and has no effect on the SERPs."
- It is calculated by "a machine learning algorithm that evaluates multiple
  factors, primarily focusing on backlink data", drawn from Moz's own Link
  Explorer index. Inputs named: "the number of linking root domains, the
  quality of those links, and other signals that correlate with rankings".
- It is relative and logarithmic: "it's easier to grow your score from 20 to
  30 than it is to grow it from 70 to 80", and other sites' growth can lower a
  score with no change on your side.
- "New websites always start with a Domain Authority of 1 and increase as they
  earn authoritative backlinks over time."
- "Referring domains are one of the most important factors."
- Moz's own advice for raising it: earn links from relevant authoritative
  sites via "original research, expert guides, and shareable resources",
  remove toxic links, on-page and internal-linking hygiene.

Hypotheses (not documented by Moz, treated as such): that Moz's crawler does
not execute JavaScript; that a domain's first index appearance lags its first
crawlable link by weeks; that nofollow links count for little in DA. Moz's
help pages for Link Explorer and the index were not reachable (404 at the two
help-hub URLs tried), so the index refresh cadence is unverified here.

## 2. Baseline evidence and its limits

| Metric | Value | Source | Date | Scope | Confidence |
|---|---|---|---|---|---|
| Moz DA | 1 | Founder's Moz screenshot | before 2026-09-12 | "exact page" for https://heykettle.com/ | Low as a root-domain figure; DA is a domain metric so the number itself is likely the same at root scope, but not verified |
| Moz PA | 16 | same screenshot | same | exact page | Medium |
| Moz linking domains / inbound links / followed | 9 / 10 / 0 | same screenshot | same | exact page | Low. Not checked at root scope. The domain was registered 2026-08-21 (Namecheap, WHOIS 2026-09-12) yet Wayback holds captures from 2025-03-10 and 2025-03-11, so some of the 9 may be residue of a previous registrant's site. The 2025 capture body could not be retrieved |
| Moz root-domain reading | unavailable | moz.com/domain-analysis redirected to /free-metrics-limit in the founder's browser | 2026-09-12 | root | The free quota on this account is spent this month. Re-read after the quota resets |
| Google index of the site | no result returned by the search tool for site:heykettle.com or "heykettle" | WebSearch proxy | 2026-09-12 | all pages | Low. The proxy is not Google Search Console. It does show that no third-party page mentioning "HeyKettle" is indexed |
| Search Console | not consulted | DECISIONS 201 says the founder verified ownership by DNS; no data was available to this session | | | Access gap |
| Referral visits | not measurable server-side | nginx `kettle_counts` format logs date, status, path only, by design (DECISIONS 212) | | | Structural: referrals can only come from Search Console clicks and, later, self-reported "how did you hear of us" |
| Beta applications | not read this session | waitlist table (migration 0009) | | | Baseline to be recorded by the founder or PM before outreach starts |

Do not read "no data" above as zero. Three data gaps block a proper root-domain
baseline: the Moz quota, Search Console access, and the waitlist count.

## 3. Current state of the site

### 3.1 What is live and correct

- Canonical origin https://heykettle.com/ serves 200; http 301s to https; the
  retired kettle-site.fly.dev host 301s to the apex (DECISIONS 142/148).
- `robots.txt` allows everything and names the sitemap; the sitemap lists
  every page and every PDF (21 URLs) and a test refuses a resource page that
  is missing from it.
- Every page carries `<html lang="en">`, a title, an H1, and (except the two
  index pages, privacy and terms) a meta description. Blog posts carry a
  self-canonical and `og:type article`. The home page carries canonical,
  description and a 1200x630 og:image.
- All eight PDFs carry a document title matching the page's H1.
- Directory URLs redirect slashless to slash with a relative Location
  (DECISIONS 168). Unknown paths return a real 404.
- Live pages equal the repository build: home text is identical to
  `site/dist/index.html` at HEAD, and the static pages differ only by a script
  Cloudflare injects (see 3.3). No site deploy is owed for content.
- Internal linking: home links to `/blog/` and `/resources/`; every article
  links to two or three resource pages; the resource pages link to each
  other and back to the blog. Nothing is orphaned.
- Page weight is small (home 22 KB HTML, static pages 6 to 13 KB), no
  runtime fetches from the site's own code, one typeface from the bundle.
  Core Web Vitals were not measured (no Lighthouse run this session).

### 3.2 Technical findings, with what was done

| # | Finding | Effect | Status |
|---|---|---|---|
| T1 | Sitemap `lastmod` values were stale (blog posts edited 2026-09-01 listed as 08-26/08-30; home copy changed 09-02 listed as 08-30) | Search engines discount inaccurate lastmod | Fixed this session: every lastmod now equals the file's last git commit date; ci green |
| T2 | www.heykettle.com serves the site with 200 rather than 301ing to the apex | The home page's canonical covers it; resource pages carry no canonical (by ruling) so www copies of them are true duplicates | Not changed. DECISIONS 168 pins www as "production-correct" and says naming it "forces a decision". Decision item D1 in the backlog. A Cloudflare redirect rule would achieve it outside nginx, also a decision |
| T3 | Cloudflare injects two scripts into every page: `email-decode.min.js` (Email Address Obfuscation) and the `challenge-platform/scripts/jsd` bot-detection beacon | The page no longer "fetches nothing"; the `mailto:` is rewritten to `/cdn-cgi/l/email-protection` so non-JS readers see "[email protected]"; the beacon is a Cloudflare telemetry call, which sits badly beside LAW-9 even though it is not analytics | Founder action: Cloudflare dashboard, Scrape Shield → Email Address Obfuscation off; Security → Bots → JavaScript Detections off. Backlog A3 |
| T4 | Home `<title>` is "HeyKettle — Know the day started normally." with an em dash | LAW-7 bans em dashes in anything human-facing; a title tag is the most-read human-facing string the site has | Copy change, PM. Backlog D4 |
| T5 | `/blog/` and `/resources/` have no meta description; privacy and terms have none | Snippets are auto-generated | Copy change, PM. Backlog D5 |
| T6 | Resource pages carry no canonical (PM ruling 2026-08-30, "resource pages stay bare") | Combined with T2, each resource page is reachable at two hosts plus `/index.html` variants | Decision D2 |
| T7 | Zero outbound links on the whole site. The standalone-page tests ban any absolute URL on blog and resource pages, so an article cannot cite NIA, CFPB or FEMA with a link even where the copy attributes them | Pages that cannot cite cannot participate in the citation web; editors notice. Not a DA factor, but it caps editorial credibility and reciprocity | Decision D3 |
| T8 | No structured data (JSON-LD) | A `<script>` is banned on static pages by the same posture; Article/Organization markup would need a ruling | Decision, low priority. Backlog D6 |
| T9 | Blog posts deliberately carry no og:image (DECISIONS 199 and the blog test) | Shares render bare cards | Ruled; not reopened here |
| T10 | Cloudflare edge caches `.pdf`, `.txt`, `.xml` for 4 hours (`max-age=14400`) above nginx's `no-cache` | A republished PDF can lag up to four hours | Note only |
| T11 | The only known external link, linkabitai.com's footer line "HeyKettle (heykettle.com) is a LINKABIT AI LABS LLC service", is rendered by JavaScript. The server HTML has the sentence but no `<a href>` | Non-JS crawlers, Moz's included on the stated hypothesis, see no link | Founder or CC in that repository: make it a real anchor in the static HTML. Backlog A2 |

### 3.3 Content inventory and what each piece is for

Live, with the search intent each was built to catch (`docs/blog-research-round-2.md`, DECISIONS 198):

| URL | Register | Target | Notes |
|---|---|---|---|
| /resources/okay-living-alone/ + 2 PDFs | web + paper | "elderly parent living alone checklist" | flagship printable, fillable PDF is the quality edge |
| /resources/emergency-info/ + 2 PDFs | paper | "emergency information sheet ... template" | weakest incumbent SERP in the set |
| /resources/normal-day/ + 2 PDFs | paper | none, by ruling | not judged on search; flagship/email asset |
| /resources/changes-tracker/ + 2 PDFs | paper | none, by ruling | distributed as the download from the checklist |
| /blog/parent-doesnt-answer-the-phone/ | web | topic 8 | best low-competition topic |
| /blog/how-often-should-you-check-on-a-parent/ | web | topic 5 | Quora and Mumsnet on page one |
| /blog/the-information-youll-wish-you-had/ | web | topic 19 | |
| /blog/the-call-ive-rehearsed-and-never-made/ | founder voice | none | the voice reference |

Drafted, unpublished: post 2 "The button in the drawer" (blocked on founder
anecdotes), post 3 "Small things that actually help" (rule-checked,
publishable). Decided, unbuilt: the wave-2 "who do I call for what" crosswalk
with its dated numbers-checked footer (DECISIONS 198), five more printables,
seven keep-listed article topics, the flagship planner (the only email gate).

The resource library is the asset base for link acquisition. It was built for
exactly this and nothing has yet been done to put it in front of anyone who
maintains a resource list.

### 3.4 Off-site footprint

Nothing. No indexed third-party mention of HeyKettle, no LinkedIn company page
(404), no YC directory entry (404; the Fall 2026 application is pending), no
Crunchbase entry, no app-store listing (the family app is beta, the parent
side is TestFlight), no press, no podcast, no directory. The one known link is
T11. Social accounts are planned in the writers' brief, not created.

## 4. Peers and the gap

Moz figures for peers could not be pulled (quota). The comparison below is
from public evidence gathered 2026-09-12 and is qualitative.

| Peer | What earns their links | Evidence |
|---|---|---|
| Snug Safety (snugsafe.com) | Featured by AARP and Forbes; a customer survey (1,800 respondents) picked up as a press release by Aging and Health Technology Watch; App Store and Google Play listings; Trustpilot profile; an aiht.substack.com write-up | search results 2026-09-12 |
| Parents Are OK (parentsareok.app) | App Store and Play listings; own YouTube, Instagram, Facebook, LinkedIn and a subreddit; testimonials on site; "In the news" page. No third-party editorial coverage surfaced in search | site fetch + search 2026-09-12 |
| I'm Alive, Still OK, MorrowVault, AloneAssist, Sage Companion | Rank for "app to check on elderly parent living alone" with their own comparison articles and location pages; each has an app store listing | search 2026-09-12 |
| AARP, Caring.com, Caregiver Action Network, AssistedLiving.org, PlaneTree Health Library LibGuide, Where You Live Matters | Own the "long-distance caregiving" SERP with resource pages that link out | search 2026-09-12 |

Why the gap exists, in order of weight:

1. **Age and inventory.** The domain is three weeks old. Moz says every new
   site starts at 1. Peers have years of app-store listings, reviews and
   coverage. This is the largest single factor and only time and links move it.
2. **No listings of any kind.** Every peer's baseline links come from places
   Kettle is not yet in: app stores (needs a public app), LinkedIn, YC's
   directory (needs acceptance), review sites.
3. **No distribution of the library.** The printables are competitive with
   what DailyCaring, A Place for Mom and AARP offer, and the fillable PDF is
   a real edge, but nobody who maintains a caregiving resource page knows they
   exist.
4. **Vocabulary.** Peers rank by saying "elderly", "monitor", "alert" about
   themselves. Kettle may use those words only to name the category being
   replaced (DECISIONS 195). This is a deliberate trade and it costs search
   vocabulary; it does not cost links.
5. **No citation capacity.** T7: the site cannot link out, so it cannot take
   part in the ordinary reciprocity of the caregiving web (a LibGuide
   maintainer checks whether you cite the sources they respect).
6. **No measurement of referrals.** By design the server keeps no referrer, so
   the business outcome of a link can only be seen in Search Console clicks
   and in beta applications.

Unknowns: the real root-domain Moz figures and whether the 9 linking domains
are residue; Search Console impressions to date; whether Google has indexed
all 21 URLs; peers' DA.

## 5. Strategies compared

Relevance, evidence, link quality, effort, cost, timing, value, risk and
confidence, in that order, for each.

| Strategy | Relevance | Evidence | Link quality / durability | Effort, dependencies | Cost | Time to launch / to evaluate | Expected value | Risk, confidence |
|---|---|---|---|---|---|---|---|---|
| S1 Foundation listings (LinkedIn company page, YC directory on acceptance, Crunchbase, app stores when public, a real anchor on linkabitai.com) | Medium | Every peer's base links are these | Mostly nofollow except YC/app stores; durable | Low; founder creates accounts | $0 | Days / 6 to 8 weeks for Moz to see them | Identity anchoring, first referring domains; small DA movement | Low risk. High confidence they appear, low confidence they move DA much |
| S2 Resource-page inclusion for the printables (public-library LibGuides, Caregiver Action Network, Area Agencies on Aging, Village to Village members, Daughterhood, Working Daughter, PlaneTree) | High | Those pages exist and already link to free printables; the fillable PDF is the differentiator (198) | Editorial, followed, durable | Medium; outreach drafts then founder-approved sends; one-by-one, personal | $0 | 2 weeks to first sends / 8 to 12 weeks | The best DA-per-hour available and the only path that also brings the right visitors | Moderate: response rates for cold email are low; confidence medium |
| S3 Founder editorial: podcast guest spots and newsletter interviews in the caregiving niche (Working Daughter, Daughterhood, Happy Healthy Caregiver as a guest not a sponsor), a Show HN when the product is public | High | The founder-voice post is the site's strongest writing; peers' best links came from features | Editorial, followed or nofollow, durable | Medium; founder time on calls | $0 (decline paid sponsorship for links, it is link spam under Google's policy) | 3 to 6 weeks to first booking / 3 months | Coverage plus links plus qualified visitors | Moderate; confidence medium |
| S4 Original, consented research (a small survey of adult children about calling habits and the "how long before I worry" threshold) | High | Snug's only earned press pickup was a survey | Editorial, durable, repeatable | High; needs an audience to survey, consent, honest methodology | $0 to low | Not before an audience exists; 4 to 6 months | The strongest link magnet in this category if done honestly | Risk of thin samples; do not run until the beta and newsletter exist. Confidence low now, higher later |
| S5 Wave-2 content: the who-to-call crosswalk, post 3, topic 18 | High | Crosswalk is format whitespace (198); topic 18 uncontested | Only earns links if distributed via S2 | Medium; CC writes, PM reviews | $0 | Weeks / 3 months | Feeds S2 with a second reason to link | Confidence medium |
| S6 Reclaiming lost links and unlinked mentions | n/a | None exist yet | | Trivial | $0 | Re-check monthly | Zero today | |
| S7 Directories | Low | Caregiving directories are vendor-pay or low quality; Google names "low-quality directory ... links" as link spam | Poor | Low | Often paid | | Near zero, possible harm | Rejected except S1's credible identity listings |
| S8 Paid placements, guest-post networks, sponsored articles | | Google's link spam policy names paying for links or advertorials with passing links | | | Money | | Negative | Rejected |
| S9 Technical fixes (T1 done; D1 to D6 decisions) | | | | Low | $0 | Immediate | Hygiene; no DA effect beyond making existing links count | |
| S10 Search Console and measurement setup | | DECISIONS 201 | | Low; founder grants access | $0 | Days | Makes every other line evaluable | |

Rejected outright as well: Reddit in any form (off limits), scaled content,
expired domains, comment or forum links, link exchanges.

## 6. Recommendation and milestones

Run S10 and S1 now, S2 as the main line, S3 in parallel at the founder's
pace, S5 to feed S2, and S4 only once there is an audience to survey
honestly. Everything else is hygiene or rejected.

What the evidence supports saying about the targets:

- **DA 10, first checkpoint.** Plausible within roughly three to six months
  after the first ten to twenty relevant referring domains are live and
  found by Moz. That is a judgement from Moz's own description of a
  logarithmic, referring-domain-led score, not a formula.
- **DA 20, long-term target.** Needs sustained editorial coverage and a
  public product with app-store listings. A twelve-month-plus horizon with
  medium confidence, assuming S2 and S3 are executed steadily.
- **DA 50+.** Not a realistic expectation for a three-week-old,
  single-founder site under available resources. Domains at that level in
  this space are AARP, NIA, Caring.com and established publishers. Keep it as
  the aspirational ceiling, report against DA 10 and DA 20, and revisit the
  ceiling only if S3 or S4 produces national coverage. This is stated rather
  than silently changed.

Intermediate milestones, in order: Search Console data in hand; Moz
root-domain baseline recorded (after the quota resets); Cloudflare scripts
off; first five foundation listings live; first ten resource-page pitches
approved and sent; first editorial link verified live; first Moz-discovered
link; DA 10.

## 7. Approvals and access needed

- **Access:** Search Console (read access or a monthly export); the waitlist
  count as a conversion baseline; Moz root-domain reading when the quota
  resets.
- **Founder actions, no spend:** Cloudflare toggles (T3); LinkedIn company
  page; a real anchor on linkabitai.com; social accounts named in the writers'
  brief when the founder is ready to post.
- **Decisions for the PM:** D1 to D6 in the backlog.
- **Outreach:** no message is sent without the founder's explicit approval of
  the exact text and recipient. Nothing was drafted this session by
  instruction.
- **Spend:** none proposed. The only paid options seen (podcast sponsorship,
  directories) fail the link-spam test or the value test.

## 8. Measurement plan

| Signal | Source | Cadence | Recorded where |
|---|---|---|---|
| Moz DA, linking domains, followed links, root scope | Moz free Domain Analysis (10 reads a month) | Monthly, first week | seo-backlog.md experiment log |
| Impressions, clicks, queries, indexed pages | Search Console | Monthly | same |
| Links verified live | curl of the linking page, attribute recorded | On each report of a placement | link log in seo-backlog.md |
| Path counts | weekly metrics email (DECISIONS 211/212) | Weekly | founder's inbox; monthly totals copied to the log |
| Beta applications | waitlist table | Monthly | same |

Rules: record source, date, scope and confidence for every reading; never
credit an action with a change merely because the change came after it;
distinguish links verified live from links Moz has discovered from DA moves.
No scheduled job exists for any of this; the next review date is named at
the top of `docs/seo-backlog.md` and nothing polls in between.

## 9. Commands used for the technical audit (re-runnable)

```
curl -sS -o /dev/null -D - https://www.heykettle.com/ | grep -iE '^HTTP|^location'
curl -sS https://heykettle.com/ | grep -oE '<script[^>]*>'
curl -sS https://heykettle.com/sitemap.xml | grep -c '<loc>'
for p in blog/parent-doesnt-answer-the-phone; do diff <(curl -sS https://heykettle.com/$p/) site/public/$p/index.html; done
whois heykettle.com | grep -i 'creation date'
curl -sS 'http://web.archive.org/cdx/search/cdx?url=heykettle.com&output=json&fl=timestamp,statuscode&limit=3'
```
