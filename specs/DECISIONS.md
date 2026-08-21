# Decisions

Claude Code: when a spec is ambiguous or looks wrong, add a dated entry here — don't
guess, don't build around it. Fable reviews this file on every pull. Numbers are
continuous and never reused.

**Next number: 140.** This line is the one to update; the `Next number:` lines inside
older items are the values that were current when those items were filed, and are
history like the rest of them.

**Items 1 through 120 are in `specs/DECISIONS-archive.md`** — append-only, load it only
when a cited number falls in that range.

---

## Spec 005b build notes (implementer, 2026-08-16) — continued

*Items 118 through 120 of this section are in the archive.*

121. **Acceptance 2's ≤ 12 taps does not survive an honest count.** The enumeration
     (`docs/005b-test-script.md` §2) lands at ~37 taps for the merged method with
     Shortcuts installed — page CTAs 8, add + first-run ~14, automation builder ~16 —
     and the builder alone exceeds the bound. The ≤ 12 arithmetic fits a world where
     automations arrive pre-built or the page's CTAs are the only counted interactions;
     iOS offers no way to ship an automation. Filed rather than met by generous
     counting: the PM should either re-bound the criterion, scope it ("taps excluding
     the automation builder"), or treat it as the target that a future
     builder-elimination (routine discovery, or an Apple API that does not exist yet)
     would meet.

122. **Two copy-law collisions on the Family screen, resolved inside the law.** The
     setup card renders on a surface the copy law scans with no allowlist, so (a) the
     share button does not say "WhatsApp" — the wa.me href says it for us; if the PM
     wants the channel named, the law needs a scoped channel-name exemption like the
     `sms` pinning, which is a PM decision, not an implementer one; and (b) the habits
     question is phrased "what do they reach for on their phone every day without
     thinking" — the same question with no banned word in it. Also in this pass: the
     copy-law scanner itself gained word boundaries at element seams, because the
     plant-and-revert drill proved a banned word flush at the end of one element
     escaped the `\b`-bounded scan (`textContent` glues adjacent elements —
     "…WhatsApp" + "Send…" scanned as "whatsappsend"). The scan now joins text nodes
     with a space; the planted regression fails by name.

123. **`setup_links` carries `parent_id` denormalised, and the write ban is
     belt-and-braces.** The webapp renders "Amma's setup" from `setup_links` alone, so
     its read surface never touches `devices` and tokens stay out of every browser
     (Q101's standing rule extended). The migration's explicit write revokes turned out
     to be redundant with 0004's default-privilege revocation — discovered when the
     planted regression (deleting the revoke block) failed to break the write-ban test;
     the block stays as defence in depth, and the test was re-verified against the real
     regression class (a future migration granting writes), which it catches.

**PM rulings on the 005b build flags, 2026-08-16 (morning). Line-level review of
`4f4126d..a1c7cac` complete; approved. Items 119, 120 and 123 exceeded the spec — same-origin
verify with the credential living only in the address bar, law #6 enforced at the green check
with the server owning the clock, and the denormalisation that keeps tokens out of every
browser — all three adopted as the standard for future surfaces.**

* **118 — upheld.** Provisioning stays terminal until the signing runner exists; in-app
  creation would mint links for buttons that cannot exist. The implementer's scope reading is
  the correct one. Revisit only when Mac-less signing lands.
* **121 — the criterion moves, not the count.** Acceptance 2 is amended in the spec (same
  commit): every tap enumerated honestly, ≤ 40 total in v1, the enumeration itself is the
  artifact, and the automation builder (~16 taps, Apple's UI, not ours) is the named
  reduction target. The spec's ≤ 12 assumed a world where automations can ship pre-built;
  iOS offers no such thing. From ~78 at the start of this week to ~37 honest is the record.
* **122 — scoped exemption granted.** The share CTA may name the channel ("Send on
  WhatsApp"). Rationale for the law's history: the copy law bans app names where they would
  *describe a parent's behaviour*; this string describes the child's own next action —
  navigation, not surveillance vocabulary. Implementation (queued for Claude Code): a
  channel-name exemption pinned to that single copy key, in the `sms`-pinning style item
  122 itself pointed at; nothing broader. The seam-joining scanner fix stands as shipped.

124. **The app never says which family you are looking at** (founder, 2026-08-16, live in
     production — backlog). One login can see several families (the runbook's own rehearsal
     trick relies on `members.auth_user_id` being non-unique), and the Today view renders all
     parents as one undifferentiated card list — the founder's screen shows Amma, Appa,
     TestDad and TestMom with nothing marking two of them as a different family. The Family
     tab discloses it, but only on navigation. Asked for, when picked up: family context made
     visible where cards live — a family-name header or grouping on Today (collapsed to
     nothing when the login sees exactly one family, which is the normal case and should stay
     clean), and the family name titled on the Family tab. Second observation from the same
     screenshot, same surface: the Family circle lists the founder's contact **twice** —
     either contact rows are duplicated at provisioning or the render does not de-duplicate;
     small, but a stranger reads duplication as a bug and trusts the rest of the page less.

125. **Founder rulings, 2026-08-16: the consent *ceremony* is dead, and product surfaces are
     English-only.** Two rulings, both standing:

     **(a) No signed consent document — ever.** No printable one-pager, no signature block, no
     sign/scan round-trip, no e-signature (which assumes email, which assumes away the actual
     customer). A product that requires printing kills itself at checkout. What survives is
     what the product laws already carry *in the product*: the setup page's plain-language
     first screen, the always-visible kill switch, and three-fields honesty — item 106's own
     conclusion ("consent is carried by the product, not the call") taken to its end. Legal
     language moves to Terms of Use, presented where payment happens. Follow-ups queued:
     `git rm docs/consent-onepager.md docs/consent-onepager-bilingual.html`; rewrite runbook
     §7's "read the one-pager together" step to "open the setup link together — the first
     screen is the consent conversation"; the laws in `docs/setup-delivery-brief.md` §6 are
     untouched (per-person consent and the kill switch are product mechanics, not paperwork).

     **(b) English-only surfaces.** The child is the installer and the translator; if the
     family speaks something else, live translation on the call is their natural mode — the
     remote-eyes pattern already is that. No localized artifacts are produced by default;
     translation happens case-by-case on explicit founder request, priced against a real
     family that needs it. This supersedes the bilingual one-pager experiment (2026-08-16,
     same day it was made — cheap lesson).

---

## Field log — Appa's install, the first merged-method setup (founder, 2026-08-16)

126. **Appa is live — routine (Safari + WhatsApp) and charger — and the install produced the
     sharpest onboarding findings yet.** Both parents are now reporting in production; Appa's
     is the first field run of the merged two-shortcut method and of the setup page. What the
     call taught:

     * **The real pain is app-jumping, not any single step.** The actual path on Appa's phone
       was: WhatsApp → download the file → share icon → Apple share sheet → find Shortcuts →
       Add → open Shortcuts → test → *back to WhatsApp* → repeat everything for file two.
       Every arrow is a context switch, and **one wrong tap lands on a different screen and
       the flow breaks** — with the helper eight thousand miles away and unable to point.
       An educated, capable parent struggled; the distance multiplies every stumble.
     * **The WhatsApp install path is not uniform.** Amma's install (two days earlier, per-app
       files) was "tap the file → Add Shortcut" directly; Appa's needed the share-sheet hop
       through the Apple share options. Same product, different iOS/WhatsApp behaviour — any
       instruction that promises one exact path will be wrong for someone.
     * **A parent's natural tap finds the shortcut editor.** Mid-call, Appa tapped into the
       edit view — raw URL, token, "Get contents of" staring back at him — instead of running
       the shortcut. Nothing broke (back arrow exits), but the page's first-run step should
       say: "if you ever see a screen full of code, just tap the back arrow."
     * **Founder ruling — onboarding investment is PAUSED.** The setup page needs to be better
       and the founder knows it, but for the beta group the answer is handholding — there is
       no way around it, and "the onboarding is a mini-product by itself" must not distract
       from the product. Do what is needed manually for beta. The page stays as shipped;
       improvements queue behind real beta-family evidence.
     * **Next cheap artifact, logged not scheduled:** a stitched-screenshot walkthrough video
       (YouTube), so a parent can watch on the TV while doing the steps on the phone — the
       remote-eyes pattern inverted: instead of the helper seeing the parent's screen, the
       parent sees the steps at television size.
     * Minor, verify within 48h: Appa's charger automation may have only "Is Connected"
       ticked (charger-on fired in testing). Corroborating-only either way; tidy on the next
       touch, not worth a call.

---

## Site image + copy pass build notes (implementer, 2026-08-17)

127. **The photography wired, the em dash retired — and the four execution calls a
     reviewer should see.** The six webp files replaced every placeholder; ImageSlot and
     its label are deleted rather than parked. Calls made in the founder's absence,
     each cheap to overrule:

     * **Diptych order is derived from the photographs, not assumed.** The morning frame
       faces right, the evening frame faces left, so parent-left/child-right satisfies
       both "profiles face inward" and the brief's non-relitigable parent-left ruling in
       one arrangement. Pinned by test with the brief cited, so a future re-crop that
       flips a profile fails loudly instead of quietly facing the frames apart.
     * **Alt text now describes the actual stills** — the six shipped photographs are
       still lifes and prior alts described people who are not in frame. Register per
       the founder's example: descriptive, calm, digit-free (the digit walk reads `alt`
       as a perceivable attribute). Sizing is class-only for the same reason: a
       `width="1536"` would be the digit walk's first legitimate kill.
     * **Two serif seams were rewritten, not just de-dashed**, because the dash WAS the
       element boundary: "Two short messages a day, and | a phrase when there's
       something worth saying." and "The gentle idea was to | notice the ordinary, and
       say so." Both keep design-language §3's only permitted serif shape (an italic
       phrase inside a sans sentence — a period there would have stranded the serif as
       its own sentence). Founder may prefer different words; the seams are one-line
       swaps.
     * **Page titles took periods**: "Kettle. Know the day started normally." and
       "Kettle. Privacy." — the instruction said periods or commas, and a comma after a
       brand name in a browser tab reads as a typo.
     * **The copy-law scan grew an `img[alt]` walk** (with a has-alt assertion): alt is
       neither textContent nor `[aria-label]`, so an inline literal beside the markup
       escaped the rendered-page law until the plant drill proved it. Same class as the
       webapp's element-seam fix in item 122; all seven planted regressions for this
       pass fail by name.

---

## Rhythm Field + beta conversion pass (implementer, 2026-08-17)

129. **Founder decision, recorded: the Rhythm Field and the beta conversion.** The
     approved scope, verbatim in intent: (1) the Rhythm Field in two placements — hero
     (drifting motes between the photographs; the quiet-morning sequence playing the
     ladder once, parent-first, after ~6 s in view; content-honesty rule: signals and
     the parent-first ask, nothing implying learning, scoring or inference) and the
     three-fields section (dust resolving into the three labelled orbits) — Canvas 2D
     preferred, reduced-motion static, canvas-failure safe, off-screen paused, mobile
     density simpler, lazy module with no LCP regression, photographs framed and never
     replaced; (2) the beta conversion — hero second line, conversational CTAs with
     reassurance microcopy, the founding-families section with the founder note, the
     optional `help_with` form field (migration 0011), scenario kickers replaced by
     one-line headlines; (3) the mobile hero tightened; (4) the copy law extended to ban
     learns / learning / intelligence / AI on the site surface.

     **Built this pass: everything except item (1)** — see 130 for why. Execution calls
     a reviewer should see, each cheap to overrule:

     * **The AC12 CTA cap moved from two flat words to six** to fit "Apply for the
       family beta" and "See if Kettle fits my family". The flatness the old cap
       enforced survives in the urgency bans, which are untouched: longer may be
       warmer, never louder.
     * **The zero-free-text pin was amended, not deleted**: email required, one
       optional note, nothing else typed. The old test's filter never inspected
       textareas, so it would have kept passing with the new field present — it now
       pins the new truth instead of the old one by accident. The note upserts through
       coalesce: silence keeps an earlier answer, retyping replaces it — silence is
       not an erasure request. Truncation over rejection at a thousand characters (a
       kindness, not a gate), with the column CHECK as the wall behind forgetful code.
     * **"Only promises we keep" was read as instruction, not copy** — the founding
       section renders the four promises and nothing else; no closing line was
       invented. The founder-note paragraph ships as a loud bracketed stub under a
       constant named FOUNDER_WHY_STUB_BODY; it must be replaced before deploy, and
       the name keeps the gap visible in every review surface.
     * **Panel headlines** joined as a new `_H3` role (≤ 7 words) rather than reusing
       a looser suffix; the retired `_EYEBROW` constants were deleted outright so the
       prerender contract tracks only what renders.
     * **The inference ban is exactly the four ruled words.** A dotted "a.i." entry
       was planted and dropped: unescaped dots turned the word-bounded scan into a
       wildcard that banned "amid" and "axis". "learn" in the plain sense stays free —
       "nothing to learn" is a promise about the parent's effort, not a model.
     * **Mobile hero**: side by side at every width, 3:4 crop under md (165 × 220 per
       frame at 390 px, CTA inside the first viewport height); jsdom cannot measure,
       so the producing classes are pinned with the arithmetic beside them.

130. **BLOCKED, awaiting the founder: the approved motion mock is not in the
     repository.** The pass names `docs/mockups/rhythm-field-mock.html` as the spec for
     the Rhythm Field's feel, pace, density and palette, and says to open it first. It
     is not on `origin/main` (which ends at this session's own last commit) nor on any
     remote branch; `docs/mockups/` holds only the 005b setup-page mock. Item (1) is
     therefore **unstarted by design**: matching "the approved mock's motion character"
     to a file that is not there would mean inventing the thing that was approved, and
     the motion carries a non-negotiable content-honesty rule that only the real
     reference can anchor. Everything mock-independent shipped (item 129). When the
     mock lands: note the two structural guards that will need conscious amendment —
     the refused-components test bans `<canvas>` outright (it was written against
     charts and scores; a decorative aria-hidden field mount is a different animal and
     the exemption should be scoped to it), and the motion law ("entry fade + rise
     only") gains its first scripted exception, which belongs in the design language's
     text, not just in code.

     **RESOLVED same session:** the founder pushed the mock while this pass was being
     merged (`5bb4180`). The field is built — item 131.

131. **The Rhythm Field, as built** (implementer, 2026-08-17, same pass — the mock
     landed mid-merge and unblocked item 129's first half). The engine is a faithful
     Canvas 2D port of the mock: constants verbatim (90 motes, the pulse cadence, the
     messenger's ease, the resolve geometry), palette verbatim but moved into
     `tokens.css` as `--field-*` channel triplets so the colour law keeps holding —
     the engine may compose `rgba()` but a numeric channel inside it fails the scan,
     and the token read is positively asserted. Both placements per the ruling: hero
     (field behind and between the photographs; quiet morning once after ~6 s in
     view, messenger to the parent's frame located at flight time from the real
     `<img>`, sage resolve, back to ordinary) and the three-fields resolve (dust into
     three orbits labelled from `FIELDS_CHIPS` itself, so the canvas cannot drift
     from the chips' claim; 19px cream on the dark glow, per the mock).

     Judgement calls, each cheap to overrule:

     * **The messenger departs ~1.5 s after the pulses stop** rather than at the same
       instant (the mock's button does both at once). The founder's narration orders
       it stop → ghost → travel; the delay makes that read at the approved pace.
     * **The DOM keeps the words.** The mock itself renders `who · signal · when` in
       HTML *and* draws the orbit labels; production mirrors that — the chips remain
       the structural truth (prerender contract, copy law, screen readers), the
       canvas draws the labels above the dust. With the canvas gone or motion
       reduced, the section says everything it ever said.
     * **Reduced motion is a designed still, not a blank**: hero motes mid-breath
       with one soft ring; fields fully resolved with labels. "Static composition"
       read as composition, not absence.
     * **Guards amended in the open**: the refused-components canvas ban is scoped to
       exactly two aria-hidden, pointer-inert, `data-rhythm-field` backdrops (charts
       and scores stay dead; a third canvas fails by count); the colour law's
       refinement is above. The design-language text amendment for the motion law
       (its first scripted exception) is PM-owed prose — flagged in 130, still true.
     * **Hard requirements are pinned as behaviour**: fillText count zero in the hero
       (content honesty), inert on missing context, park-before-paint off screen,
       half density on phones, dynamic-import-only loading (a static import fails a
       source test). The engine ships as its own hashed chunk under `/assets/`, so
       the caching contract serves it immutably.

128. **The scenario tabs were decorative, and the fix is one loud CSS rule; gostatic
     retires for the Q112 contract** (implementer, from the founder's fix list,
     2026-08-17). Two findings from the same pass:

     **(a) `hidden` lost to the display utility.** Every tab click set the `hidden`
     attribute correctly and changed nothing visible: the panels' `flex` class is an
     author rule and beats the preflight's plain `[hidden]`, so all four scenarios
     rendered stacked in every browser — while jsdom, which computes no cascade, showed
     the tests a working tab strip. Fix: `[hidden] { display: none !important; }` in the
     base layer. Conditional classes were refused (the AC5 identical-classes guard
     exists so panels cannot diverge) and unmounting was refused (the prerender contract
     reads every panel's copy from the static HTML). Pinned twice — behaviourally
     (exactly one unhidden panel through clicks and arrow keys) and as a text pin on the
     stylesheet rule, since jsdom cannot verify the cascade half. Consequence accepted
     and stated: the no-JS view now shows the morning panel alone rather than all four
     stacked; the copy stays in the document, which is what AC9 asserts. Keyboard and
     ARIA re-verified while in there (tablist role, roving tabindex, arrow-wrap all
     pre-existing and green).

     **(b) The site served header-less from gostatic.** No cache headers at all — the
     landing page's version of Q112, quieter: stable-named photographs and a prerendered
     shell mean a heuristic lifetime pins old imagery and copy to returning visitors.
     The Dockerfile moves to the webapp's nginx pattern; `site/nginx.conf` carries the
     ported contract (unhashed → no-cache with 304s, `/assets/` → immutable year, regex
     locations banned, unknown paths 404 — a document has no routes to fall back for);
     `test_site_caching.py` asserts it in the webapp test's shape plus the wiring the
     webapp never needed: the Dockerfile actually loads this conf, the listen port
     matches fly.toml, and the six photographs really are unhashed stable names. All
     five planted regressions fail by name.

132. **PM review of `e815276`, the founder texts that unblock deploy, and the PM-owed
     motion-law prose** (PM, 2026-08-17).

     **Review verdict: approved, no overrules.** The Rhythm Field engine is a faithful
     port of the approved mock (constants, palette-as-tokens, parent-first messenger
     located from the real hero `<img>` at flight time, designed stills under reduced
     motion, dynamic-import-only chunk, zero hero fillText); migration 0011 is correctly
     shaped (nullable, CHECK-capped, RLS posture untouched); every execution call filed
     in 129 and 131 stands as made, including the CTA cap at six words, the coalesce
     upsert semantics, the scoped two-canvas exemption, and the four-word inference ban.
     The one deploy gate was the founder-note stub, now closed by the rulings below.

     **Founder rulings from the same review, binding on the finishing pass:**

     * **The founder note is final, in the founder's own words** (six paragraphs,
       delivered 2026-08-17), with exactly one PM substitution accepted for the copy
       law: "Every now and then" → "Once in a while" — the page-wide urgency scan owns
       the word "now" and the note is on the page. The card renders it as paragraphs,
       not one `<p>`; `FOUNDER_WHY_STUB_BODY` retires with the stub (the STUB name was
       the gap's alarm, and the gap is closed).
     * **Privacy policy: what, never how.** Founder IP ruling, standing: public
       surfaces describe what is collected and never the mechanism. No Shortcuts, no
       automations, no "no app installed" (a Kettle mobile app is coming, so it is also
       just false), no named infrastructure — providers are "established cloud
       infrastructure providers in the United States," named on request. Mechanism
       transparency for joined families lives on the setup surface behind expiring
       links, which is where the obscurity strategy wants it. Deletion window: 45 days,
       founder-set. The policy text is founder-final (2026-08-17) and replaces the
       placeholder page wholesale, which also retires the placeholder's
       "being written with counsel" sentence; a counsel pass remains PM-recommended
       before payment launches, alongside the ToU where consent language lives.

     **The motion law's first scripted exception — design-language text (owed since
     130):** Motion on the page is entry fade and rise, once, and nothing else — with
     one scripted exception, the Rhythm Field. The field earns motion no other element
     gets because it depicts the product's one story and nothing beyond it: signals
     arriving, and a quiet morning asked about, parent first. The exception is
     conditional and the conditions are the law: it draws no words where it decorates
     the hero, implies no learning and no verdicts, hides itself from assistive
     technology, pauses when unseen, stands down to a designed still when the visitor
     asks for reduced motion, and the page must remain whole without it. A second
     animated element is not covered by this exception; it is a new argument, to be made
     here first.

---

## Finishing pass build notes (implementer, 2026-08-18)

133. **The founder texts landed verbatim; the calls around them, filed.** Item 132's
     three deliverables are in: the note (six paragraphs, rendered as paragraphs, the
     STUB name retired), the privacy policy (wholesale, placeholder and its "counsel"
     sentence retired and pinned retired), and the motion-law prose placed in
     design-language §6. Judgement calls a reviewer should see:

     * **Two pinned literals on the privacy page's law scan**, both the same move: the
       founder's guarantees "stops collection immediately" and "with delivery tracking
       turned off" use banned words to promise their *absence* — the opposite of the
       selling and surveilling the bans exist to stop. Pinned whole, DECISIONS-62
       shape, so nothing else rides in on the words.
     * **The what-never-how ruling became a MECHANISM ban list** (tooling, automation
       vocabulary, named infrastructure) across the copy module, the rendered page,
       and the privacy page — which forced the pass's one copy change: STEP_ONE_BODY
       now reads "Kettle notices her phone's ordinary moments. She approves every part
       of the setup, and can switch any of it off herself." — and the old STEP_
       mechanism exemption retired with it. Founder may prefer different words; the
       what-not-how is the fixed part. Dotted ban entries are escaped now (the a.i.
       lesson applied); "Days fly by" stays legal beside a banned "fly.io".
     * **The scans grew to array copy**: the note ships as a readonly array, the ban
       scans walk its elements, check-prerender requires each paragraph in the static
       HTML by name (a dropped paragraph fails citing its own first words), and the
       AC12 shape rules deliberately stay on layout strings — they are rules for
       sentences, not letters. Arrays classify by the array's own suffix (…_BODY,
       …_CHIPS — CHIPS joined the role set).
     * **"Last updated: 2026-08-18"** — the pass date, on the founder's instruction to
       stamp the deploy date. If the deploy slips past the date, it is a one-line edit
       at deploy time; the founder owns the line.

     All six planted regressions fail by name (mechanism word in copy, banned word
     inside a note paragraph, named infrastructure in the policy, the counsel sentence
     returning, a script tag on the standalone page, a silently dropped paragraph).

---

## Presence pass build notes (implementer, 2026-08-18)

134. **The field was invisible, and now it is not — plus the founder's twenty-five
     years.** Two founder items off a live-browser review. The note correction is
     literal and unremarkable ("two years ago" → "twenty-five years ago", spelled out
     and hyphenated because AC4's digit scan walks the letter like any other sentence
     and "25" would fail it). The Rhythm Field ruling is the substantive one, and it
     supersedes the approved mock's constants. What a reviewer should see:

     * **It was measured, not eyeballed.** Before touching anything, a throwaway
       Playwright probe read each canvas' own pixels in a real browser and composited
       them over the ground actually behind them. The hero carried paint on **0.14%**
       of its pixels, of which **0.108%** cleared a luminance delta of 8 against
       `--canvas` — roughly one legible pixel in a thousand. "Invisible" was the
       correct word. After: **0.274%** legible (2.5×), mean luminance delta 34 → 51,
       and **0.56%** of the frame changing each second against 0.23%. These numbers
       chose the values; they are not an acceptance test and are not pinned anywhere.
       The acceptance test is the PM's eyes on the live site after deploy, as ruled.
     * **Density was deliberately left alone.** The ruling asked for larger, brighter,
       amber-er, faster and breathing — not *more*. 90 motes and 140 dust stand, and
       the parity test pins that they stand.
     * **One change is not just a bigger number: the drift floor.** The mock spread
       drift symmetrically around zero (`(random - .5) * .18`), which left a crowd of
       motes travelling at almost no speed at all — half of why the field read as
       static specks, and something doubling the spread would not have fixed. Drift is
       now a direction plus a magnitude with a floor under it: peak doubled as asked,
       and nothing frozen.
     * **The three-fields dust was lifted proportionally, not identically.** The
       ruling made that treatment conditional on it suffering the same washout, and it
       does not: cream over ink measured **1.04%** painted against the hero's 0.14%.
       So it gets a wider grain (1.6 → 2.2) and a floor under its free-drift alpha
       (0.14 → 0.24), not the hero's multiple. **PM: worth a second look on the live
       site** — this is the one number in the pass chosen against a threshold rather
       than against a complaint.
     * **The ruling's stated reason is revised, and it changes nothing.** The mock was
       said to have been tuned against a warmer, darker composition than the page has.
       Its hero ground is `#f6efe7`, within a hair of the site's `#f6f2ec` — the mock
       was showing the *same* washout all along. That is why the values looked right
       when approved and wrong the moment someone looked at the page, and it is an
       argument for the parity test below rather than against the ruling.
     * **The mock is enforced as the spec, not asked to be.** Every presence number is
       ported back into `docs/mockups/rhythm-field-mock.html`, and the field's test now
       reads each number back out of the mock's source and compares it to the shipped
       constant. Five planted regressions fail by name — a changed mock radius, a
       changed mock cadence, a changed mock density, a changed *engine* constant, and
       a mock expression renamed out of existence.
     * **Two engine values the parity test cannot reach**, because the mock has no such
       state: the reduced-motion still's ring alpha (0.3 → 0.45, so the still is a
       still and not a faint one) and the messenger halo's line width, which used to
       *inherit* whatever the pulse loop last set and is now stated explicitly — the
       pulses got thicker, and an inherited width would have dragged the messenger
       along with them silently.
     * **Nothing in the honesty set moved**, and the pass was scoped to make that
       checkable: no text in the hero, no learning or inference implied, parent asked
       first, reduced motion still a single still frame, lazy chunk still lazy. The
       existing tests for all five still pass untouched.

     **Next number: 135.**

---

## One-voice pass build notes (implementer, 2026-08-19)

135. **One typeface, a band of its own, and dust you can stir.** Three founder items
     off two independent reviews of the live site. All three are built; what a reviewer
     should see, and the calls made inside them:

     **1 — Typography.** The serif role is retired: Fraunces is out of the bundle,
     `font-serif` is out of the Tailwind theme so the class cannot be reached, and the
     five phrases it carried are back inside the sentences they were cut out of. The
     words are unchanged; only the element boundary is gone. The scale went seven sizes
     to five — display (48, the page's single `h1`), heading (32, every section `h2`),
     lead (20), body (16), eyebrow (13). The three that went each had exactly one user:
     `feature` was a button size, `card` was one paragraph, `quote` was the pull-quote
     that no longer exists.

     * **Section headings are visibly smaller.** `h2` used to be the display size, which
       is why "display" meant nothing. It is now 32 against the `h1`'s 48. This is the
       most visible change in the pass and it is on every section — **PM, look at this
       first on the live site.**
     * **`font-light` never rendered, on any heading, ever.** Instrument Sans has no 300
       file; its range starts at 400. The class was written across every heading and the
       browser served 400, so the old type law's "display gets lighter as it grows" was
       describing something no visitor has seen. The class is gone and the law now names
       three weights that exist as files: 400, 500 (the one emphasis role and the panel
       headlines), 600 (buttons and labels). 500 was added; the three Fraunces faces
       left. Net bundle change is a wash.
     * **FIELDS_SERIF became FIELDS_EMPHASIS, and AC12 gained the role.** The ruling
       allows emphasis on a whole sentence by weight or accent colour, and that line
       ("What isn't collected can't leak.") is exactly that, so it stayed a line of its
       own rather than being merged into the paragraph above it. The four scenario
       fragments and the story fragment had no such standing and were merged.
     * **`site/SerifPhrase.tsx` deleted** — a byte-identical duplicate of the retired
       component, outside the build's `src/**` glob since it was committed by accident
       in 9a5bfb3. **`site/Pill.tsx` is the same kind of stray** (a stale copy of the
       real component, also dead) but has nothing to do with this ruling, so it was left
       alone. It should go; say the word.

     **2 — The collision.** The cause was structural: the canvas was a backdrop spanning
     the section, so at some width its orbits were always going to be under a paragraph.
     The field now has a reserved band — a flow sibling below the words, `h-64` /
     `md:h-80`, which text cannot enter at any width — and `Section`'s backdrop slot is
     **deleted rather than left unused**, since a section that can take a layer behind
     its text will be given one again. The section also lost its `min-h-[80vh]`: the band
     gives it real height, and an artificial minimum on top of that is just empty ground.

     * **Geometry now answers to the band.** The mock's fixed 56px ring overlapped its
       own neighbours below roughly 600px of canvas. Ring is `min(56, W/8)`, centres sit
       at 0.2 / 0.5 / 0.8 with rows at 0.46 / 0.54, and dust orbits are fractions of
       their ring rather than pixel radii, so nothing escapes a ring that shrank.
     * **Verified in a browser, as ruled.** `site/scripts/probe-field.mjs` reads the
       canvas' pixels and intersects them with every readable element's laid-out box at
       360, 390, 768 and 1440: **zero intersecting boxes, zero painted pixels**, against
       the production build. Planting the old backdrop back reproduces the reviewers'
       report exactly — 6 of 6 elements intersecting at every width, "who" and "signal"
       and "when" and the body paragraph each named with a pixel count — and the probe
       exits non-zero. Unlike the presence pass's throwaway, this one is committed; it
       is **not** in `npm run ci`, because Playwright is not a dependency of the package.
     * **At 390px the fit is real but not generous**: outer rings clear the band edge by
       ~26px and "signal" nearly fills its ring. The test asserts 16px of edge margin and
       12px between rings, so it will fail before it collides — but it is worth the PM's
       eye on a phone.

     **3 — Stirring the dust.** Reach 120px, maximum displacement 26px, ease 0.09, with a
     squared falloff so the edge of the reach is a suggestion rather than a wall.
     Displacement is measured from where each grain *belongs*, never from where the last
     frame pushed it, so a mote cannot chase its own escape. Every constraint is a
     condition and each is tested: passive listener on the section, canvas still
     `pointer-events: none`, no `preventDefault` anywhere, no listener at all without a
     fine pointer, a non-mouse `pointerType` ignored even if one arrives, and a
     reduced-motion viewer returning before any of it exists. The rings and the three
     words are never displaced — asserted byte-for-byte between a stirred run and a still
     one. The motion law's own rule ("a second animated element is a new argument, to be
     made here first") is honoured: design-language §6 now carries the extension, scoped
     to the dust alone.

     **The plant drill caught one of its own tests.** "The rings are never stirred" was
     first planted by displacing a ring with `dust[0].ox` — and it passed, because with
     `Math.random` pinned, dust[0] orbits the *left* ring and was never inside the
     cursor's reach. Re-planted with `dust[1]`, which is the grain the cursor actually
     touches, it fails by name. Eleven plants in total across the pass; the other ten
     failed first time.

     **Next number: 136.**

---

## Illustration set + mobile tab row build notes (implementer, 2026-08-19)

136. **The drawings are in, the tabs stay a row, and mobile verification is now a
     rule with a script behind it.** Everything in the ruling is built. What a
     reviewer should see, the calls made inside it, and two things found on the way
     that are not mine to decide:

     **Imagery.** The hero's two-frame grid is *gone* rather than collapsed — it
     existed to stage the gap between two rooms with a column gap, and the drawing
     contains that gap, so keeping the grid would have staged it twice. The
     messenger's target moved with it: `PARENT_X_FRACTION = 0.25` is exported from
     `Hero.tsx` and pinned inside the left half by a test, because law #6 is at
     stake in that flight and a fraction at or past the middle would put the
     parent's question on her daughter's side of the page. Scenario containers are
     4:3 and the strip is `aspect-[1600/686]` — the artwork's own ratios rather than
     the nearest nice fraction, so nothing is cropped by a frame that disagrees with
     the drawing. Mobile arithmetic improved: at 390px one 16:9 hero frame is 192px
     tall against the old diptych's 220px.

     * **The strip sits after the "How Kettle works" heading, not above it.** Every
       section on this page starts with its heading, and an image that outranked one
       would be the first exception to that. "The section's opening image" reads
       both ways; this is the reading that keeps the page's structure. **One line to
       flip if the PM meant the other.**
     * **All six alt strings passed the copy law unmodified** — the ban scans, the
       culture-coded scan and the digit walk all run over alt text. "amber glow" is
       legal here: what this site refuses is an amber *token* and alarm vocabulary,
       not the word for a colour in a description of a drawing.

     **The tab row.** Below md the row stops wrapping and scrolls sideways; from md
     it is the wrapping row it always was. Three decisions worth naming:

     * **The fade is a mask**, so it is alpha only — no colour is involved and it
       cannot quietly become a second palette (AC1) — and it is applied only while
       the row is *measured* to be clipped. The desktop row therefore needs no
       breakpoint rule to stay unfaded: it is never clipped, so it is never faded.
     * **`scrollLeft` on the strip, never `scrollIntoView`**, which scrolls every
       ancestor and would have taken the page with it — a worse bug than the one
       being fixed, and an easy one to ship.
     * **`EDGE_FADE` and the CSS `calc(100% - 2.5rem)` are asserted to be the same
       number.** If they drift, the active tab is scrolled to a position underneath
       its own fade, which relocates the bug rather than fixing it.

     **The standing rule** is in CLAUDE.md's working norms and the site README's own
     table, with `scripts/probe-responsive.mjs` behind it: at 360/390/428/768 it
     checks page overflow, that the tab row is one line, that every tab clears 40px,
     that the fade matches the clipping, and then clicks every tab and requires it
     to end up wholly inside the strip. Current reading: no wrap, no overflow, 43px
     tabs, every tab in view. Planting the wrapping row back reproduces the founder's
     report exactly — two lines at 360, 390 and 428, one at 768.

     **Housekeeping, with one correction and one absence.**

     * **`check-prerender.mjs` was checking nothing, and that was mine.** Its
       MUST_RENDER list still required the retired `_SERIF` role, and `_EMPHASIS` —
       the role that replaced it in 135 — was not in the list at all. So the page's
       one emphasis line has not been required in the static HTML since that pass.
       Fixed and planted: dropping the line now fails the check by name.
     * **`site/public/illustrations/` does not exist.** The founder's commit b4da2c2
       shipped only the six optimized webps, so there was nothing to delete.
     * `@fontsource/fraunces` and `site/Pill.tsx` are gone as ruled. The caching
       test's manifest is the new six, and a retired photograph left behind in
       `public/` now fails it — which is what keeps that list a manifest.
     * **`docs/hero-diptych-brief.md` now describes a retired form.** Left alone:
       rewriting a brief is the PM's call, not a housekeeping item.

     **Two traps worth recording, both found by drilling rather than by thinking.**

     * **A failed build leaves `dist/` stale, so a verify run after one proves
       nothing.** The first attempt at the prerender plant removed the emphasis line
       but left its import, `tsc` failed, `vite build` never ran, and
       `check-prerender` cheerfully passed against the *previous* build. Same family
       as the Postgres false green: read what the step before you actually did.
     * **`--revoke <token>` fails on roughly one device token in sixty-four.**
       `test_provisioning.py` failed once in a full run and passed eight times on
       re-run: `secrets.token_urlsafe` draws from `A-Za-z0-9-_`, so a token
       beginning with `-` is read by argparse as a flag ("expected one argument").
       This is live founder tooling for revoking a *lost phone*, and it is not
       something this pass touched — reported rather than fixed. The two candidate
       fixes: document and use the `--revoke=<token>` form, which argparse always
       accepts, or give the option `nargs=1` handling that tolerates a leading dash.
       **`--setup-link` has the same shape and the same exposure.** PM/founder call.

     Eleven plants, all failing by name: a retired photograph path, an eager strip,
     the strip above the heading, the wrapping row (in jsdom and in the browser), the
     fade and the margin drifting apart, `scrollIntoView` creeping back, the tap
     target shrinking, the messenger aimed at the daughter, a retired webp left in
     `public/`, and the emphasis line dropped from the prerender.

     **Next number: 137.**

---

## Floating CTA build notes (implementer, 2026-08-19)

137. **The ask stays reachable without the page acquiring an overlay.** Built as
     ruled. What a reviewer should see, and one finding about the design that is
     worth knowing before it is trusted:

     * **It yields by not existing.** While the hero, the waitlist or the footer is
       on screen the component renders `null` — not a hidden element, not an
       `aria-hidden` one, nothing. So there is no invisible layer over the page, no
       pointer target, no screen-reader stop, and no focus landing in the middle of
       the footer. Every "absent" case in the tests checks absence from the DOM
       rather than a class that happens to hide it.
     * **The frame does the centring, not a transform.** A full-width
       `pointer-events-none` strip with `justify-center` / `md:justify-end` puts the
       pill bottom-centre on a phone and bottom-right on a desktop. The obvious
       alternative, `-translate-x-1/2`, would have slipped past AC7's motion scan on
       a technicality — the pattern is `^translate-` and the class starts with a
       minus — and a static transform that dodges the scan is exactly the kind of
       thing that makes the scan stop meaning anything.
     * **`pb-safe` is `calc(1.5rem + env(safe-area-inset-bottom))`**, so one class
       clears the iPhone home indicator and is a plain 24px everywhere else.
     * **No observer, no button.** jsdom has none, and neither do some old browsers.
       A CTA that cannot tell whether it is sitting on the form is the permanent
       overlay the ruling refuses, so the answer to not knowing is silence. A missing
       selector is treated the same way.
     * **Measured at 360/390/428/768/1440:** 48px tall (the ruling asks 44), centred
       with equal margins on phones, 24px from the right on desktop, inside the
       viewport, absent at the hero, the form and the footer, and never overlapping
       another link, button or field.

     **The finding: the footer entry is currently redundant, and the unit test is
     what holds it.** At every viewport height measured — 844, 600 and 420 — the
     waitlist section is *still on screen* whenever the footer is, because the footer
     is only 232px tall and sits at the end of a much taller section. So "hide at the
     footer" can never fire on its own as the page stands: removing the footer from
     the yield list and re-running the browser probe changes nothing, while the unit
     test fails immediately. It is kept because it makes "never covers the privacy
     link" true by construction rather than by an arithmetic that a longer footer or
     a shorter form would quietly break — but a reviewer should know it is belt to
     the positioning's braces rather than a rule doing visible work today.

     **Two calls worth the PM's eye:**

     * **The button waits for the hero to clear completely.** Centring the scenarios
       section still leaves ~17px of hero on screen, and the button stays away for
       those 17px. That is the ruling read literally ("hidden while the hero section
       is in view"), and it means the CTA appears slightly later than "once you start
       reading the scenarios". If it should appear sooner, the fix is a threshold on
       the observer, not a change to the rule.
     * **It is last in `<main>`**, so a keyboard user reaches it after the footer
       links rather than in the middle of the page. That keeps the reading and tab
       order of everything above it exactly as it was, which seemed the more
       conservative of the two.

     **The probe learned two things about itself**, both found by running it rather
     than reasoning about it: it was scrolling *smoothly* (the stylesheet asks for
     it) and reading 400ms later while the page was still in flight, which reported
     the button "present at the form" when it is not; and its mid-page stop was the
     scenarios section, where the button is correctly absent. Scrolls are instant now
     and the stop moved to the story section, with the reason written beside it.

     Nine plants, all failing by name: the footer dropped from the yield list, the
     guard removed so it never hides, `aria-hidden` added, the frame's
     `pointer-events-none` removed, the entry animation ungated, its own words, its
     own target, and showing up with no observer at all.

     **Next number: 138.** *(taken below)*

138. **device_alive on iOS is a third automation, not an app; the native app pairs with
     the Android wave** (PM ruling with the founder, 2026-08-19; supersedes the open
     mechanics of Q107's device_alive note, keeps its intent).

     The founder proposed a mobile app sending a once-daily device-alive ping as a
     second line of signal. Investigated and ruled:

     * **No iOS permission buys a guaranteed daily background wake.** "Allow tracking"
       (ATT) gates only the advertising identifier and has zero effect on execution.
       Background App Refresh is opportunistic and skips lightly-used phones — a
       parent's phone exactly. Silent pushes are throttled and explicitly not
       guaranteed. "Always" location wakes reliably only on *movement*, so a homebound
       week produces manufactured silence — the one failure mode Kettle cannot carry,
       before even reaching the privacy page's "no location, ever collected," which is
       load-bearing. Borrowed VoIP/audio background modes are rejection bait. An
       unreliable absence-signal is worse than none: this product reads absence as
       meaning.
     * **iOS already has a reliable device_alive: a time-of-day Shortcuts automation.**
       "Every day at HH:MM" personal automations fire dependably in the background on
       modern iOS, locked phone included. One more automation in the existing setup
       flow — same shortcut pattern, same ping URL, `device_alive` signal, never
       alarm-grade — proves daily that the phone is powered and connected, which is the
       feature's whole semantic. Cost: one extra automation in a flow whose tap count
       we fight for; therefore **optional at provisioning, not default**. The charger
       signal already behaves as a de facto daily heartbeat for most phones.
     * **The native app moves to the Android wave**, where a daily background ping is
       actually honest, and where the app is simultaneously the first-line signal
       source for Android parents (no Shortcuts equivalent exists there). One build,
       two problems. The waitlist's parent_phone answers decide when that wave earns
       its slot.

     Build order unchanged: outbound channel → SMTP (Resend, per the founder's
     existing account; the SMTP plan doc's Postmark-class placeholder updates to
     Resend when next touched) → stranger install. The time-of-day automation enters
     the wizard whenever provisioning next gets worked on, not before.

     **Next number: 139.**

---

## Context pass build notes (implementer, 2026-08-19)

139. **The log is renamed and split, CLAUDE.md is a page again, and five queued
     hygiene items are done.** Founder-ordered, one pass. What a reviewer should see,
     and the calls made inside it:

     **The rename** is 252 insertions against 252 deletions across 92 files — the shape
     a mechanical rename should have. Numbering is untouched; DECISIONS 107 is the item
     QUESTIONS 107 was. The name had been wrong for a while: the file stopped being a
     list of open questions long ago and became the log of what was decided and why.

     **The split** moves items 1 through 120 verbatim into `specs/DECISIONS-archive.md`
     and leaves the live file at 741 lines from 2,881. Two things a reader should know:

     * **It falls inside a section, because item 121 does.** The live file opens with
       that section's heading marked as a continuation and a line naming which of its
       items are in the archive, so nobody meets 121 with no idea what it belongs to.
       That heading is new scaffolding; no item is reworded.
     * **The next number now lives in exactly one place** — the line at the top of the
       live file. It had already drifted: CLAUDE.md said 138 in its working-norms
       section and 139 in the baton while the log said 139. The `Next number:` lines
       inside older items are left alone as history.

     **The diet: 278 lines to 72**, and nothing deleted. The judgement call worth
     stating is the mechanism. The ruling said `.claude/rules/` *if the tooling supports
     path scoping, otherwise `docs/norms/`* — but `.claude/rules/` is not a Claude Code
     feature, so it would have been a folder nobody loads, and `docs/norms/` scopes
     nothing at all. The mechanism the tooling actually has is a **nested `CLAUDE.md`**,
     loaded when a session works in that subtree. So the norms live in
     `site/CLAUDE.md`, `product/CLAUDE.md` and `webapp/CLAUDE.md`, the root file names
     all three in a table for human readers, and a session touching only `site/` no
     longer pays for the Postgres recipe. **If the PM wanted the literal folder, this is
     the line to overrule.**

     * **The six product laws stayed in the root file.** Everything else moved, but the
       constitution binds every surface and costs fourteen lines; a session that never
       reads it is the failure the whole file exists to prevent.
     * `docs/failure-families.md` groups the traps by *shape* rather than by suite — the
       false green, the test that passes for the wrong reason, jsdom's layout blindness,
       work lost or buried — because the countermeasure repeats even when the surface
       does not. `docs/baton.md` took the state of the build whole; it was the largest
       block in the root file and it is the one thing that is stale by design.

     **The hygiene, and one thing to look at:**

     * **`--revoke <token>` works for every token the generator can produce.** The pair
       is joined into `--revoke=<token>` before argparse sees it, and *only* when the
       value is not itself a known option string — so `--revoke --demo` still refuses
       the ambiguous invocation rather than trying to revoke a device called "--demo".
       That guard is tested directly, because it is the part that could turn a fix into
       a worse bug. `--setup-link` and `--set-signals` are covered too.
     * **Both front-end builds clear their output first**, so a build that dies leaves
       nothing for verification to pass against. Verified by breaking `tsc` on purpose:
       the build exits 2, `dist/` is gone, and all three verifiers refuse. They also say
       why now — "dist is missing, the build did not finish" — which is the difference
       between a checker that failed and a checker that broke. `rm -rf` rather than a
       `rimraf` dependency: this repo justifies every dependency, and both machines that
       run it are POSIX.
     * **The share CTA says "Send on WhatsApp"** (the 122 exemption, granted after item
       123). It is pinned twice — the copy-law scan exempts the *key*, and a test pins
       the key's *value* — because either half alone is a loophole, and a third test
       requires the same screen to fail with no allowlist. **PM: the label loses the
       parent's name**, which the ruling's wording implies and the card's structure
       supports (the name is the line directly above it). But a screen reader listing
       links now hears the same name twice on a two-parent family. If that matters the
       fix is copy, which is yours to write.
     * Runbook §7 opened with "read `docs/consent-onepager.md` together" — a file
       deleted three passes ago. It reads "open the setup link together" now, with 125a's
       reasoning stated and 125b named where it lands. `product/README.md` pointed at the
       same dead file and now points at the setup page's copy module.
     * `docs/hero-diptych-brief.md` gets a superseded banner rather than a deletion: the
       format is retired, the reasoning still governs the artwork.

     **Numbering note:** 138 was filed between passes (the founder's `device_alive`
     ruling), so this pass is 139 as instructed, and the top-of-file line now reads 140.

     Two plants, both failing by name: bypassing the argparse joiner reproduces the
     original "expected one argument" exactly, and scanning the Family screen without
     the channel exemption still rejects it.
