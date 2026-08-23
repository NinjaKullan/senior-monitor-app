# Decisions

Claude Code: when a spec is ambiguous or looks wrong, add a dated entry here — don't
guess, don't build around it. Fable reviews this file on every pull. Numbers are
continuous and never reused.

**Next number: 166.** This line is the one to update; the `Next number:` lines inside
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

---

## Spec 007 Wave A build notes (implementer, 2026-08-21)

140. **The outbound channel's decision core is built and runs dark.** Everything §2
     names is in: the quiet-morning evaluator, the scheduler, the sent-once ledger
     (migration 0012), the copy-law-scanned template registry with §5's bodies
     verbatim, the console transport behind the `Transport` seam, and the reply-intake
     endpoint that nothing calls. §6.1's four days pass on a fake clock, §6.2's plants
     fail by name, all suites green (`pytest` 401), ruff clean, nothing deployed.

     **One thing needs a ruling before Wave B, and it is not small.**

     * **This is the second ladder and the second digest engine in the tree.** Spec
       004's `ladder.py` already implements candidate → ask → family escalation with
       shadow/live modes, its own `ladder_candidates`/`ladder_events` tables, its own
       ask copy in `ladder_messages.py`, and a live reply webhook at
       `/twilio/inbound`. Spec 003's `digest.py` already implements twice-daily
       digests with `digest_sends` and a channel abstraction. Spec 007 describes all
       of this again, in a cleaner shape, and says nothing about what happens to the
       old one. I built 007 as specified and touched neither — "pilot untouched" —
       but the result is two engines that would both speak the moment a transport
       lands. Today nothing collides because all three switches default off. **Before
       Wave B someone must rule: does 007 supersede 003/004, or run beside them?** If
       it supersedes, the migration path is the interesting part, because spec 004's
       ladder is the one with a live inbound webhook.

     **The execution calls the ruling invited, and one it did not.**

     * **§2.3's ledger key is `(family, date, kind)`; I built
       `(family, parent, date, kind)`.** Migration 0006 exists precisely because 0005
       keyed a send at family granularity and a family with two parents silently lost
       the second row. Every message here is about or to one person — the digest names
       a parent, the ask goes to a parent — and both of the founder's parents are
       live. The spec's literal key would have let exactly one of them be asked about
       per day. `parent_id` is NOT NULL, no sentinel. **Cheap to overrule; I do not
       think it should be.**
     * **§2.2's family-timezone rule: I used the parent's.** The spec says family
       timezone = the parents' provisioned timezone and calls it cheap to overrule.
       `effective_tz(parent.tz, family.tz)` is this codebase's existing law and the
       reason "Amma is visiting Texas" is a data change rather than a code change, so
       every decision here — digest included — is computed in the *parent's* zone.
       Consequence worth seeing: a family whose two parents have different zones gets
       two schedules, and there is no family-scoped clock anywhere in this build.
     * **The digest times, 08:30 and 20:30, are as specified — and they disagree with
       the digest engine that is already shipped.** Spec 003 runs a morning cutoff
       hour of 14:00 and an evening hour of 20:30 (`DIGEST_MORNING_CUTOFF_HOUR`,
       `DIGEST_EVENING_HOUR`). If 007 supersedes 003 that is fine; if they are to run
       side by side, a family would hear from Kettle at 08:30 and again whenever 003's
       morning window fires. Same ruling as above, arriving from a different direction.
     * **§4's premise is out of date, so migration 0012 adds one column, not a
       table.** "The parent's phone number, deliberately never collected until now" —
       `parents.phone_e164` has existed since 0007 (spec 004's ask number),
       `members.email` since 0001, and `family_contacts` is a *taken name*: 0007 uses
       it for the named local contact. So the migration adds `parents.whatsapp_e164`
       and nothing else. A second column rather than a reuse of `phone_e164` because
       that one belongs to the other ladder's SMS ask, and one column serving two
       senders makes "which channel did we reach her on" unanswerable.
     * **The §5 copy is verbatim, and two things in it are the PM's to settle.** The
       bodies say "her" and "she", while DECISIONS 24 is standing policy that nothing
       infers a pronoun from a name — `ladder_messages.py` carries a neutral clause
       for exactly that reason, and the founder's own family includes a father. The
       morning digest currently renders "Appa's morning looked like her morning." And
       the follow-on carries an em dash, which DECISIONS 127 retired from
       customer-facing *site* copy; whether that reaches product messages is a call.
       Both are flagged in the registry's docstring rather than edited.
     * **`/outbound/reply` 404s until a secret is configured** (implementer call).
       Cancelling a follow-on is safety-relevant: an unauthenticated endpoint would
       let anyone who knows a number suppress an escalation. Wave C swaps the shared
       secret for the provider's signature, the way `/twilio/inbound` already
       validates Twilio's. It also answers an unknown number and a known one with no
       pending ask identically, so it cannot be used to ask "is this a Kettle parent".
     * **`LogTransport` reports delivered even with no address on file.** Deliberate:
       a dark run's ledger is a record of the *decisions*, which is what §6.3 asks the
       founder to review. A transport with a network client must do the opposite — no
       address means no delivery, no ledger row, and the day's slot stays free. That
       asymmetry is the trap in this design and it is written into the class docstring.

     **Two assertions the plant drill said were missing, both found by planting and
     watching the suite stay green.** The unique index was never being exercised: a
     double *run* of the scheduler is stopped by the read before the write, so every
     acceptance scenario proved the observable property while `on conflict do nothing`
     could be deleted with no test noticing. There is now a test that calls the write
     twice directly. And "the body is never read" only checked the stored row — a
     planted `log.info("reply body: …")` passed, because a log line is a copy the row
     scan cannot see. Eight plants fire by name now: charger counting as a morning, a
     follow-on without its ask, the dedupe clause, the index's uniqueness, the reply
     secret, the reply body reaching a log, a transport with an HTTP client appearing
     in Wave A, and a verdict in a template.

     **Owed by the founder, unchanged from the spec:** Wave A runs dark for 48 hours
     and the ledger is reviewed against what actually happened; that review is the
     gate to Wave B. `docs/auth-smtp-plan.md` now says Resend (DECISIONS 138), so the
     domain errand and the DNS records are the next thing on the critical path.

---

## Retiring specs 003 and 004 (implementer, 2026-08-21)

141. **Specs 003 and 004 are retired; 007 is the only engine that can speak.**
     `digest.py`, `ladder.py`, `ladder_messages.py`, `messages.py`, `channels.py`,
     `twilio_signature.py` and `scripts/ladder.py` are deleted, both background loops
     are gone from `main.py`, `/twilio/inbound` 404s, the eight `DIGEST_*` /
     `LADDER_*` / `TWILIO_*` settings are removed, and migration **0013** retires the
     ladder's tables. `specs/README.md` is new — thirteen specs, one line each, a
     status — and 003 and 004 carry banners. Suites green (`pytest` 270 with Postgres
     up, `webapp` 102, `site` 172), ruff clean, nothing deployed. The pilot's ingest,
     provisioning, forge and family app were not touched.

     **`digest_sends` is deliberately still here, and it is the one thing in this
     retirement that needs a decision rather than a migration.** The family app reads
     it: `webapp/src/lib/queries.ts` declares it in `READ_SURFACE` and the Digests
     screen renders from it. Spec 007's `sent_messages` is not a replacement — it is
     RLS deny-all by design, so no client can read it at all. Dropping or renaming
     `digest_sends` would empty a screen in a live app that both of the founder's
     children use. **Two ways out, PM's call:** give `sent_messages` a family-scoped
     read policy and move the screen onto it, or retire the screen. Until then the
     table is a read-only historical record that nothing writes to any more, which is
     honest but will look increasingly odd — the screen shows a log that stopped. The
     migration header, `product/README.md`, the 003 banner and
     `test_retirement.py`'s docstring all say so, in the four places somebody might
     arrive from.

     **Checked, not assumed — the migration decides at apply time.** This container's
     test database is not evidence about production, so 0013 counts rows per table:
     empty ones are dropped outright, and any table holding rows is renamed to
     `retired_<name>`, has every policy on it dropped, and has privileges revoked from
     `anon` and `authenticated`. History kept, reach removed. Shadow-mode ladder rows
     are the labelled ledger that was meant to tune the thresholds; deleting them
     silently would be the wrong call to make on someone else's behalf. The **archive
     branch is tested**, on its own database built to 0012 with a `family_contacts`
     row planted, because every other test in the suite runs against empty tables and
     therefore only ever exercises the drop path — the branch production might take
     was the one nothing covered.

     **Left in place on purpose:** `families.ladder_mode` and its CHECK, and the
     per-parent columns 0007 added (`phone_e164`, `alarm_deadline`, `max_gap_minutes`,
     `grace_minutes`, `family_gap_minutes`). The ruling named tables, a column drop is
     not reversible, and `phone_e164` holds a real number the founder entered. Nothing
     reads them now that the module is gone. A later migration can take them once
     007's own contact fields have been through a wave that actually sends.

     **What 007 does not have that the retired engines did.** Read out of both before
     deleting them, as instructed. Nothing here blocks Wave A — it runs dark — but
     several are load-bearing before anything reaches a family, and four of them are
     the difference between a quiet system and a silent one.

     *Safety and honesty, in rough order of how much they matter:*

     * **The founder learns nothing when a message fails.** `digest.py` raised four
       ops-alert kinds — `digest_skipped`, `digest_delivery_failed`,
       `digest_channel_unavailable`, `digest_unroutable` — on ntfy, to the founder
       only, per law #3. 007 raises none. An undeliverable message today is a log
       line in a process nobody is watching. **This is the one I would build first.**
     * **`ask_skipped` has no equivalent, and its absence is worse than it sounds.**
       When there was no number to ask on, 004 recorded that fact and escalated on the
       clock anyway. In 007, a transport that returns False writes no ask row — and
       because the follow-on is gated on an ask row existing, there is then *no
       follow-on ever*. A missing phone number silently disables the whole ladder for
       that parent. Wave C's real transport is where this becomes live, not theory.
     * **`mechanism_ok` is gone — the unreachable-handset distinction.** 004 knew the
       difference between "the phone has stopped reporting" and "the routine has
       changed", and said different, honest things for each. 007 has one story for
       both, so a dead battery reads as a changed morning.
     * **The morning digest was evidence-gated: no evidence, no reassurance.** That is
       law #6 wearing working clothes, and 007's morning note does not carry it.
     * **No morning cutoff, so no staleness guard.** 003 refused to send a morning
       digest after `DIGEST_MORNING_CUTOFF_HOUR`. 007 has no equivalent: a scheduler
       catching up after an outage will send "her morning looked ordinary" at
       dinnertime, correctly and absurdly.
     * **All-clear when routine resumes**, and the resolution-on-activity bookkeeping
       under it. 004 closed its own loops. 007 opens them.

     *Reach and shape:*

     * **Per-recipient fan-out.** 003 sent to every member; 007 has one child address.
     * **Recorded delivery status** (sent / failed) per message. 007's ledger records
       that a decision was made, not that it landed.
     * **The aggregated evening digest.** 003 sent one message per timezone group
       covering the family; 007 sends one per parent. A two-parent family gets two
       messages every evening where it used to get one.
     * **`max_gap` as a trigger** and the **daytime window** it lived in — 004's
       second way of noticing, independent of the morning.
     * **Staged escalation family_1 → family_all**, with the named local contact.
       007's follow-on is one step.
     * **Per-family `shadow` / `live` modes**, and the DB CHECK that made `live`
       impossible without `digest_enabled` — a schema-level interlock against a family
       being escalated at before it was ever messaged.
     * **Per-parent thresholds.** 007 evaluates every parent on the same clock.

     None of this was discarded quietly: the specs stay in the tree with banners, and
     the reasoning inside 004 — particularly its law-#6 argument for asking the senior
     before the family, which is the same argument 007's parent-first ordering rests
     on — is still the best account of why the shape is the shape.

     **Five plants, and one of them changed the code.** Retiring `digest_sends` did
     turn the suite red — but through `testsupport.TABLES`' truncate, not through the
     guardrail's assertion, so the failure read "relation digest_sends does not exist"
     pointing at a fixture, and the docstring saying why the table is load-bearing was
     never shown. A maintainer following that message would delete the fixture's
     reference, which is the wrong repair. That test now runs on its own database and
     fails with the sentence somebody needs. The other four fire by name as written: a
     dangling import in a file pytest never imports, an unconditional drop erasing the
     archive branch, the archive keeping a policy, and the Twilio webhook coming back.

     **§5's five corrected bodies are NOT in.** The ruling says to replace them with
     the founder's strings "verbatim", and that message is not in this session's
     context; `specs/007-outbound-channel.md` §5 still carries the originals, so there
     is nothing here to copy from. `outbound_templates.py` is therefore unchanged and
     still renders `"Appa's morning looked like her morning."` — the DECISIONS 24
     pronoun problem and the DECISIONS 127 em dash, both still live. Inventing five
     strings and labelling them the founder's would put words in someone's mouth in
     customer-facing copy, which is a worse failure than a pass finishing one item
     short. **Send the five strings and it is a ten-minute pass** (registry, spec §5,
     the copy-law tests).

---

## The domain cascade + session-restore hardening (implementer, 2026-08-21)

142. **heykettle.com is the canonical origin everywhere, and the family app no longer
     hangs on a rejected token.** All six items are in. Suites green (`pytest` 277 + 1
     xfail, `webapp` 111 + 10 new, `site` 172 with `npm run ci` clean end to end),
     ruff clean, pilot untouched, nothing deployed.

     * **Contact.** `FOOTER_CONTACT_HREF` and the privacy page's contact line are
       `hello@heykettle.com`. The site is clean — the only other place the string
       lived was the foreign-origin allowlist, which now names heykettle.com. Live
       docs (root `CLAUDE.md`, `site/README.md`, the SMTP plan's step 1, the spec
       index) say heykettle.com; history is annotated rather than rewritten, because
       the GTM roadmap's "domains getkettle.\*" and the naming shortlist's
       registrability research were true when written and are the record of how the
       decision was made. Spec 006 gets a banner in the superseded-spec shape.
     * **Canonical.** `<link rel="canonical" href="https://heykettle.com/" />` is in
       the head and survives the prerender into `dist/index.html` (asserted). There
       were no absolute self-referencing metadata URLs to repoint — the page carries
       a description and a title and nothing else, no `og:`, no `twitter:`.
     * **The 301** is a named `server` block, not host-matching inside the serving
       one. nginx resolves an exact `server_name` before falling back to `_`, so a
       request arriving on heykettle.com never enters the redirect block and the
       caching contract cannot be affected by anything written in it — a structural
       guarantee rather than a matter of reading order, and the test asserts there is
       no `if (` in the config at all.
     * **`WAITLIST_ORIGINS`** and the founder's command are below, in their own item.

     **Two implementer calls, both cheap to overrule.**

     * **`/healthz` answers on both hosts rather than redirecting.** `fly.toml`
       configures no HTTP check today, so nothing changes either way right now. This
       is about the check somebody adds later: a health endpoint that 301s to another
       host reports on *that* host, so a machine that is actually down still looks
       fine. Say the word and it redirects with everything else.
     * **privacy.html gets NO canonical, and I withdrew the one I added.** The ruling
       said "the site's head", singular; extending it to the privacy page was mine,
       and it tripped the standing law that page is held to — it stands alone, with
       no `<link>` and no absolute URL of any kind, so that the page a
       privacy-minded reader studies hardest provably fetches nothing. A canonical
       link fetches nothing either, so this is the law's letter rather than its
       purpose — but trading a plain privacy guarantee for an SEO hint is not a swap
       to make on the way past, and the 301 already stops that page being reachable
       at two addresses. **Yours if you want it made deliberately.**

143. **`WAITLIST_ORIGINS` is an env var on kettle-api, and setting it *replaces* the
     default rather than adding to it.** `_origins()` falls back to the shipped tuple
     only when the variable is empty, so a list naming just the fly.dev origin is a
     lockout, not an addition. The command:

     ```bash
     fly secrets set -a kettle-api \
       WAITLIST_ORIGINS="https://heykettle.com,https://www.heykettle.com,https://kettle-site.fly.dev"
     ```

     Drop the fly.dev entry once the old host stops being used; the remaining two are
     then identical to the default and the variable can be unset entirely.

     **The code-side default is heykettle.com and deliberately does not include
     kettle-site.fly.dev.** The default is what the system settles on, and a temporary
     allowance written into code is a permanent one — the transition grant belongs
     where removing it is one command. Both properties are now pinned by test, along
     with the replacement semantics, because the shape of the command above depends
     on them. `product/README.md` prints the whole list rather than the one addition
     for the same reason.

     **Standing caveat, unchanged and still unconfirmed:** the waitlist form is
     CORS-dead until this variable includes the serving origin. It has never been
     confirmed here that it was set on the last kettle-api deploy at all.

144. **The family app's session restore is hardened, and the bug was worse than a
     spinner.** Reproduced exactly as reported: a stored session, a token the server
     rejects, and "Loading…" for as long as the tab stays open. Three defects, one
     symptom. `claimMembership()` rejected into a bare `.catch(() => undefined)`;
     `loadSnapshot()` rejected into nothing at all, so `snapshot` stayed null;
     and `!session` could not tell *restoring* from *signed out*, so a stored session
     rendered the login screen for an instant and then a spinner forever. Nothing
     was watching a clock over any of it.

     Auth failures now end the session and land on login — on the claim, on every
     read, first load or an hour into a poll. `restoring` is a named state, which is
     what makes it boundable. "Loading…" is bounded at 15 seconds, and that timer
     deliberately knows nothing about *why* a restore stalled: the failures above are
     the ones anticipated, and the bound is for the ones nobody anticipated,
     including a promise that never settles.

     Two details worth the PM's eye. **`clearStoredSession` removes the storage key
     by hand after asking `signOut()` to** — `signOut()` talks to the server, and the
     server refusing this token is why we are here, so it can fail, and a stored
     session surviving a sign-out is the same bug again on the next page load.
     **`isAuthFailure` is deliberately narrow**: a 500, a 429 or a dropped connection
     is not a rejected credential, and signing a working session out over a train
     tunnel is this bug's mirror image, so a test holds that line from the other side.

     **Six plants, and one of them changed the code.** Restoring the original
     swallowed `.catch(() => undefined)` on the claim left all nine tests green: the
     first test refuses both calls, so the snapshot's guard reached login and the
     claim's guard proved nothing. The shape that isolates it — a refused claim
     behind a read that never settles — is now a test.

145. **A test in spec 007 was green every morning and red every evening, and had been
     since it was written.** Found because the suite went red this evening on
     unchanged code. `/outbound/reply` is the one decision in 007 that reads wall
     time instead of being handed an instant; its test writes the ask on the fixed
     test day, and after 18:30 UTC, IST is already tomorrow, so the reply matched no
     ask. It was written, reviewed and reported green inside a single afternoon,
     which is the entire window in which it worked. `create_app` now takes a `clock`
     defaulting to `now_utc`; behaviour in production is unchanged.

     **The seam uncovered a real defect underneath, and it needs a ruling.**
     `record_parent_reply` matches the ask by the parent's **local calendar day**. A
     parent asked at 11:00 who answers at 00:20 is answering on a different local
     day: no ask matches, nothing is marked replied, and the follow-on goes to her
     family after she has already said she is fine. That is precisely the failure
     §2.6 exists to prevent, and escalating over someone who answered is worse than a
     missed message. **Not fixed, because the repair is a spec choice, not a bug
     fix** — match the most recent *unanswered* ask instead of the day's, then decide
     the bound on "recent". It is pinned as a `strict=True` xfail asserting the
     behaviour that is wanted, so the day it is fixed the marker fails as XPASS and
     has to be removed. The marker cannot outlive the bug.

     **Both of these are now failure family 5** in `docs/failure-families.md` — the
     state with no exit, where the code does not do the wrong thing so much as
     decline to do anything, and waiting looks like working. Neither was found by the
     suite; one was found by the founder and one by the clock.

     **Numbering note:** the ruling said to file at the next number, which was 142.
     The pass covers four separable decisions the PM will want to cite individually,
     so it is filed as 142–145 and the top-of-file line now reads 146.

     **Still owed and unchanged: §5's five corrected template bodies** (DECISIONS
     141). They were not in the founder's message this time either, so
     `outbound_templates.py` still renders `"Appa's morning looked like her
     morning."`

---

## The environment split (implementer, 2026-08-21)

146. **`npm run ci` disagreed about the webapp depending on which machine ran it, and
     the mechanism is not what the flag suggested.** Fixed, with the founder's exact
     condition reproduced rather than inferred. Suites green on **both** Node builds —
     `webapp` 117, `site` 174, `pytest` 277 + 1 xfail, ruff clean, nothing deployed.

     **What it actually was.** Not the Node version, and not the lockfile: `jsdom`
     25.0.1 and `vitest` 2.1.8 are pinned exactly, and Node 24.18.1 running this repo
     unmodified passes. It is one line in vitest's jsdom setup. `populateGlobal`
     installs the jsdom window's properties onto `globalThis`, and `getWindowKeys`
     filters them:

     ```js
     if (k in global) return keysArray.includes(k);
     ```

     A name that **already exists on the host global** survives only if it is in
     vitest's own hard-coded KEYS list. `localStorage` is an own property of the jsdom
     window and is **not** in that list. So on any machine where Node itself defines
     `globalThis.localStorage` — webstorage behind a flag, an env var, a future
     default — jsdom's Storage is never installed, the host's object stays, and the
     tests use that.

     **Two things the reproduction proved that the hypothesis had wrong.**

     * **Node's own `Storage` does have `setItem`.** So "Node's webstorage global
       shadows the browser one" cannot by itself produce
       `localStorage.setItem is not a function`; whatever is on the founder's global
       is some third thing. The mechanism turns out to be indifferent to *which*
       object shadows, which is why the fix is "install our own" rather than "handle
       Node's" — that repair works for the object nobody has identified yet.
     * **The loud failure is the lucky one.** Reproduced with a host object that
       *works*, the suite goes **9-of-10 green** while the code under test writes to a
       different store than the assertions read. That is the false green, and it is
       what a future Node shipping webstorage by default would hand everybody. The
       founder's TypeError was the good outcome.

     **The fix, in two halves that do different jobs.** `src/tests/setup.ts` installs
     an explicit Storage unconditionally, after the environment has had its turn,
     owing nothing to the host. Items live as **enumerable own properties**, because
     `clearStoredSession` walks `Object.keys` to find `sb-*-auth-token` — a
     Map-backed fake passes every round-trip assertion and breaks its only caller, and
     that is a plant that fires. A non-enumerable marker lets the guardrail assert the
     stub *won*, not merely that storage works; without it the guardrail would pass
     against the very object that caused the bug. Separately, all 22 test files across
     both front ends now carry `@vitest-environment jsdom`. **The pin does not replace
     the stub** — the shadowing happens *inside* jsdom setup, so naming the
     environment does not prevent it. It closes the other door: `--environment node`
     on a command line.

     **Verified green under every condition, not just the fixed one:** Node 22.22.2
     and Node 24.18.1, each with a hostile host `localStorage` present (both the
     founder's shape and the working shape) and absent, and with
     `--experimental-webstorage` enabled. The hostile globals were injected with
     `--import`, which is the only way to be on `globalThis` before vitest builds the
     environment — a setup file cannot reproduce this, because setup files run after.

     **Every other test file is immune, and now provably so.** Nothing else in either
     suite touches storage — `sessionRestore.test.tsx` and `lib/session.ts` are the
     only references in the tree. The site suite therefore never had the storage
     exposure and gets **no stub**, deliberately; it shares the invocation exposure, so
     it gets the pins and a two-test guardrail, because a pin nothing reads rots.

     **One thing worth the PM's eye.** The same skip rule applies to **220** of the
     jsdom window's 442 own properties, including `crypto`, `atob`/`btoa`,
     `setTimeout`, `queueMicrotask` and `origin`. Most are harmless because Node's
     implementation matches, and `setTimeout` is already shadowed today. This is not
     worth pre-emptively stubbing — but it is the reason the failure family is written
     around the *shape* rather than around `localStorage`, and it is why the next one
     of these will not look like this one.

     **Filed as failure family 6**, appended rather than inserted: DECISIONS 145 cites
     "failure family 5" by number, and renumbering silently rewrites what an existing
     ruling points at. That rule is now stated at the top of the file.

     **Still owed, unchanged and untouched by this pass** (it blocks no deploy, and
     this one did): §5's five corrected template bodies (DECISIONS 141) and the
     local-midnight reply ruling (DECISIONS 145).
---

147. **(2026-08-22, Fable) Magic-link sign-in bounced back to login: Supabase infrastructure clock skew, not app code.** The founder requested a link, clicked it, and landed
     back on "email me a sign-in link." The auth logs showed the whole story in four
     lines: OTP issued, verify succeeded, user fetched — then every data call the app
     made 401'd and the app signed out fifteen seconds later, which is exactly what the
     8a51c0f session code is built to do with rejected credentials. The old code would
     have hung on Loading; the new code turned an infrastructure fault into a clean
     symptom in one try.

     **Root cause, proven not inferred.** A same-origin trap tab captured the fresh
     session token before sign-out wiped it. Replayed against the data API by hand:
     `PGRST303 — JWT issued at future`. The token's issued-at was already 66 seconds in
     the past by the browser's clock, and a replay four minutes later still got the
     same refusal, so PostgREST's clock was running more than four minutes behind
     GoTrue's. Postgres's own `now()` was accurate to the second — the skew lived in
     the data-API layer alone. Confirming detail: the founder's failing requests left
     zero `permission denied` rows in postgres_logs while a deliberate anon probe left
     two, so his requests were dying before the database ever saw them.

     **The blast radius rewrites an earlier diagnosis.** Edge logs showed every
     `/rest/v1/` request for at least 24 hours had failed — 1,188 requests, zero
     successes. The "kettle-app is down" incident (DECISIONS 142) was therefore only
     half diagnosed: the stale stored session was real, but no fresh login could have
     succeeded either. kettle-api was untouched throughout — it speaks to Postgres
     directly with the service role and never crosses PostgREST.

     **Fix:** founder restarted the Supabase project from the dashboard; the machine's
     clock resynced; the previously refused token immediately returned the family row
     with a 200. Total downtime about a minute.

     **What this leaves behind:** if sign-in ever regresses to this exact shape —
     verify succeeds, `/user` 200, then all data reads 401 — check the *clock* before
     the *token*: replay one captured request and read the error body. PGRST303 with
     "issued at future" is infrastructure, and no amount of app-side retry, storage
     clearing, or redeploying will move it.
---

148. **(2026-08-22, Fable) heykettle.com redirect loop: `server_name _` is not a default server.** Reported by the founder as "the site is not accessible"; Chrome showed
     ERR_TOO_MANY_REDIRECTS. DNS was healthy — both hosts resolved to Fly, so the
     fault was inside nginx. The 8a51c0f canonical-redirect config assumed nginx
     falls back to the `server_name _` block for unmatched hosts. It does not:
     with no `listen ... default_server` marked, nginx routes every unmatched Host
     to the FIRST server block in the file, which was the kettle-site.fly.dev →
     heykettle.com 301 block. So the canonical domain itself matched no name, fell
     into the redirect, and 301'd to itself forever, while the old fly.dev host —
     the only Host with an exact match — redirected correctly. The site had been
     looping since the cascade deploy; the founder's earlier 200s predate it.

     **Fix:** `default_server` added to the static-site block's listen line, and
     the comment that encoded the wrong fallback rule rewritten to state the real
     one. One word of configuration; the lesson is that the comment was confident
     and wrong, and nothing tested the canonical host end to end after deploy.

     **Also done in the same pass:** `site/public/illustrations/` (the six source
     PNGs, untracked) moved to `design-sources/illustrations/` at the repo root,
     per the standing errand — the next `npm run ci` would have shipped ~30MB of
     source PNGs to production.

     **Worth a test:** the site suite asserts copy and caching laws but nothing
     asserts "GET / with Host: heykettle.com returns 200, with Host:
     kettle-site.fly.dev returns 301 exactly once." A config-level check (even
     `nginx -t` plus a grep for `default_server`) would have caught this before
     deploy; a post-deploy curl of the canonical host would have caught it after.
     Flagged for Claude Code to pick up with the next site pass.

---

## Outbound copy rulings (PM, from the founder, 2026-08-23)

149. **Relationship labels, never names or pet names, in outbound copy.** Founder
     ruling: templates never use a parent's given name or a family's own pet name
     (Amma, Appa) — Kettle cannot know what a family calls their elders, and
     guessing pretends an intimacy the product does not have. Every template that
     references the parent uses a `{relationship}` label the child picks at setup
     from a standard set: Mom, Dad, Grandma, Grandpa, Aunt, Uncle (extendable).
     Pronouns are never guessed either: templates use singular they or are
     restructured to need none. This supersedes `{parent_name}` in spec 007 §5 and
     closes the DECISIONS 24 pronoun problem. Consistent with the US-market-default
     ruling on customer-facing material.

150. **The ask carries a universal icon; parent-language asks are planned, not
     built.** The ask becomes English plus an icon a parent who reads no English
     can still act on (see 151 for the verbatim string). Reply intake stays
     content-blind: a thumbs-up, a voice note, or a sentence in any language all
     count as "answered" — nothing parses content, per spec 007 §2.6. A per-parent
     language field for native-language asks is planned for a later spec; the
     English-only-surfaces rule stands until then. Founder ruling on scope: the
     site's quoted ask string is NOT updated in this pass. Spec 007 §5's "verbatim
     from the site's exemption" binding is relaxed to "the site's quote is
     illustrative"; if any test asserts site/product string equality, loosen the
     test, never the product copy.

151. **The five outbound template bodies, verbatim (founder-approved 2026-08-23).**
     Recorded here in full because the last approved set lived only in a chat
     transcript and was lost (see 141, 145). These replace spec 007 §5's originals
     and are what `product/outbound_templates.py` renders. No em dashes in any
     body (DECISIONS 127).

     1. Digest, morning, normal:
        "{relationship}'s morning looked like a normal morning. Next note this evening."
     2. Digest, evening, normal:
        "An ordinary day, start to finish. Next note in the morning."
     3. Digest, morning, quiet-so-far:
        "Quiet so far this morning. Kettle will check in with {relationship} first if that continues."
     4. The ask (to the parent):
        "Everything okay today? Reply with a 👍 whenever suits."
     5. Follow-on (to the child):
        "{relationship}'s usual morning hasn't shown up today, and they haven't answered Kettle's note yet. You know their day best. A call from you beats anything Kettle can send."

---

## Outbound copy pass build notes (implementer, 2026-08-23)

152. **149/150/151 are built; the execution calls a reviewer should see, and the
     two the task brief predicted would need a ruling.** The registry renders the
     five approved bodies verbatim, `{relationship}` superseded `{parent_name}`
     everywhere, and the copy-law scan now enforces the two rules that graduated
     to law — no gendered pronoun (149, closing 24) and no em dash in any body
     (151, extending 127 to product copy) — with plants of the exact regressions
     151 replaced. Suites: pytest 315 + 1 xfail (the 145 marker untouched),
     webapp 117, site 174, ruff clean. Calls made, each cheap to overrule:

     * **Storage shape: a nullable `relationship` column on `parents`
       (migration 0014), closed by a named check constraint.** Not a lookup
       table, because the standard set is product vocabulary like the signal
       set, not family data; not free text, because a family's own words stored
       server-side and rendered into messages is what 149 rules out.
       "Extendable" therefore means: widen `parents_relationship_known` in a
       migration and add the same word to `RELATIONSHIP_LABELS`
       (`kettle/provisioning.py`) — a test fails by name if the two lists
       drift. Nullable because both live parents predate the column.
     * **Where the child picks it: founder-entered at provisioning for beta,
       like every contact field so far (spec 007 §4's own precedent).**
       `--parent "Amma::Mom"` at provisioning; `--set-relationship
       <device-token> --relationship Mom` for the two live parents. **The
       child-facing picker is NOT built and needs a ruling**: the natural home
       is the family app or the setup flow, but onboarding-surface investment
       is founder-PAUSED (126), and 149 says "the child picks at setup"
       without saying which surface setup is. Filed rather than guessed.
     * **A parent with no label waits rather than rendering a blank.** A
       relationship-bearing send is skipped without a ledger row — the day's
       slot stays free, and the run after the label is set releases what the
       slot held. The ask names nobody, so parent-first survives the gap by
       construction; a test walks that day end to end. The founder-visible
       consequences, owed alongside migrations 0012/0013: **apply 0014, then
       set labels for both live parents**, or their morning digests and
       follow-ons stay silent while asks still go.
     * **Template ids are unchanged** (`digest_morning_normal` etc.): the
       ledger stores ids, and Wave D's WhatsApp registration maps onto them —
       the bodies changed, the identities did not.
     * **The site's quoted ask string is untouched, per 150's explicit scope
       ruling.** The product test that pinned site/product equality now pins
       DECISIONS 151's string instead ("the site's quote is illustrative").

---

## Midnight-reply repair build notes (implementer, 2026-08-23)

153. **The DECISIONS 145 defect is fixed as ruled; the three calls inside the
     ruling's edges, each cheap to overrule.** A reply now matches the parent's
     pending ask — most recent, sent, unanswered, follow-on not yet gone —
     bounded to asks sent within the last 24 hours, no calendar day in the
     match. Spec 007 §2.6 amended; the 145 strict xfail became a plain
     assertion in the same commit as the fix, so the suite carries **zero
     xfails** for the first time since 142. Boundary tests walk each edge:
     23:00/00:20 matches, no-pending-ask notes only, after-follow-on notes
     only, older-than-24h notes only, newest-of-two-pending wins. Every edge
     verified by plant (oldest-wins, missing follow-on clause, missing bound,
     narrowed window, silent arrival — five plants, five named failures).

     * **"Record that a reply arrived" is a masked log line, not a row.** The
       ruling says record the arrival; it does not say where. A stored-reply
       table would be new schema holding per-person interaction data with no
       consumer, and intake is content-blind (150) with nothing worth keeping
       beyond "it happened" — so the arrival is `log.info` with the number
       masked, timestamp only, and `record_parent_reply` still returns False.
       If the PM wants arrivals queryable (e.g. for the Wave A ledger review),
       that is a schema decision to make explicitly, not a side effect.
     * **The 24-hour bound is exclusive at exactly 24h** (`sent_utc > now -
       interval '24 hours'`): an ask precisely a day old is no longer
       answerable. The ruling says "within the last 24 hours"; the fencepost
       had to land somewhere and nothing real sits on it.
     * **"Follow-on not yet sent" is judged per the ask's own ledger day, and
       a late reply leaves the ask unanswered.** Once the family has been
       told, marking the ask answered afterwards would rewrite the ledger into
       a question that never needed escalating — the row stays as the family
       experienced it, and the arrival is noted in the log only.

---

## The dark loop pass (implementer, 2026-08-23)

154. **Spec 007's scheduler now runs in the lifespan; the calls inside the PM's
     "wire it now", each cheap to overrule.** The stale main.py comment — "no
     loop until it has a transport that can reach anyone" — inverted §2.5 and
     is gone; §2.5 now says explicitly that Wave A IS the loop running dark.
     Same shape as the heartbeat monitor: own connection, minutely pass in a
     worker thread, cancelled on shutdown, survives any pass failure,
     `OutboundState` for live ops visibility. All guardrails verified by plant
     (validation removed, registry defaulting open, loop never wired, flag
     ignored, fly flag off — five plants, five named failures).

     * **Both switches are on in fly.toml, and they mean different things.**
       `OUTBOUND_LOOP` runs the machinery; `OUTBOUND_ENABLED` is read live on
       every pass as the kill switch on the decisions themselves, so the
       founder can stop the engine deciding (`fly secrets` / env change)
       without killing the process that also runs the heartbeat. The task
       named only OUTBOUND_LOOP for fly.toml; ENABLED had to come with it or
       the dark run would decide nothing and the §6.3 review would review an
       empty ledger.
     * **The config value is "console"; the transport's log label stays
       "log".** OUTBOUND_TRANSPORT selects from a closed registry
       (`kettle.outbound.TRANSPORTS`, one entry) and an unknown name raises at
       `create_app` — before the app object exists, loop flag on or off — so a
       typo is a crash-loop the founder sees, never a latent branch. fly.toml
       deliberately does not set OUTBOUND_TRANSPORT: the code default is the
       registry's only entry, and a test pins its absence.
     * **The loop reads the enabled flag per pass rather than once at boot** —
       a restart-to-disable on a safety-relevant engine is the wrong shape.
       Settings are still immutable; what is re-read is the field, not the env.

155. **Correcting the record: the 2026-08-18 deploy did NOT start Wave A.** The
     baton and DECISIONS 141-era notes could be read as "Wave A runs dark in
     production" from that deploy on. It did not and could not: no loop
     existed — the lifespan comment explicitly declined to start one — so
     nothing evaluated, nothing wrote the ledger, and the §6.3 48-hour review
     clock has never started. **The dark run starts with the deploy that
     follows this pass**, and the ledger review gates Wave B from that deploy,
     not from any earlier date. Two preconditions the deployer must confirm,
     both founder-side: migrations 0012 and 0013 applied (0014 was applied
     today by the PM via SQL, and both live parents' labels are set Mom/Dad —
     but 0012 creates `sent_messages`, and a loop without its ledger table
     fails every pass, loudly in logs and invisibly in the product); and the
     post-deploy check that the logs show `outbound (dark):` lines at the
     expected local times.

---

## The four owed PM rulings (Fable, 2026-08-23)

156. **The Digests screen retires; `digest_sends` follows once nothing reads it.**
     Of DECISIONS 141's two ways out, the screen goes, not the ledger's privacy
     posture. `sent_messages` stays RLS deny-all: it is the engine's own record,
     and holding it unreadable from every client is a safety posture worth more
     than a screen that duplicates the family's inbox — from Wave B onward the
     digest IS the email; the family already has the record in their own hands.
     Sequence: webapp drops the Digests screen and `digest_sends` leaves
     `READ_SURFACE`; a later migration retires `digest_sends` the 0013 way
     (row-count check, rename-if-holding-rows). A message-history screen can
     return post-beta if families ask; it would read a purpose-built view, never
     the raw ledger.

157. **The sixteen missing capabilities (DECISIONS 141), ranked into waves.**
     *Build with Wave B (blocking, next pass):* founder ops alerts on every
     failed, unroutable, or skipped send — the DECISIONS 152 label-skip and a
     failed loop pass included (law #3: founder-only, ntfy, like the pilot);
     recorded delivery status (sent/failed) on the ledger row; the morning
     staleness cutoff (a scheduler catching up late does not send "her morning
     looked ordinary" at dinnertime — skip and ops-alert instead); the evidence
     gate (a reassurance body never renders from an empty evidence window: a
     zero-signal day sends no evening-normal digest and raises an ops alert —
     absence of data is an ops condition, not a family message; the morning
     quiet-so-far path is already honest absence and stands).
     *Build with Wave C:* the ask_skipped equivalent (a transport with nobody to
     reach records the skip and still escalates on the clock — a missing phone
     number must never silently disable the ladder); all-clear on routine
     resume and its resolution bookkeeping; the mechanism_ok unreachable-handset
     distinction (dead battery must not read as a changed morning once real
     follow-ons flow).
     *Later, when more than one family exists:* per-recipient fan-out, the
     aggregated per-family evening digest, staged escalation family_1 →
     family_all, the per-family shadow/live schema interlock, per-parent
     thresholds, and max_gap as a second daytime trigger.

158. **Three accepted calls, made deliberate.** (a) `/healthz` answers on both
     hosts and never redirects — a health endpoint that 301s reports on the
     wrong machine (DECISIONS 142, confirmed). (b) privacy.html carries no
     canonical link and no absolute URL of any kind: the fetch-nothing guarantee
     outranks an SEO hint, and the 301 already collapses the duplicate address
     (DECISIONS 142, the withdrawal is now the ruling). (c) The relationship
     label stays founder-entered at provisioning while the onboarding pause
     (QUESTIONS 126) holds; the child-facing picker joins the setup page
     whenever that pause lifts, not before (closes DECISIONS 152's open
     question).

---

## Wave B pass build notes (implementer, 2026-08-23)

159. **Everything 157 ranked Wave B-blocking is built; the calls inside it, each
     cheap to overrule.** Migration 0015 puts status on the ledger; the engine
     ops-alerts every failed, unroutable and skipped send plus loop-pass
     failures; the staleness cutoff and evidence gate withhold rather than lie;
     the `resend` transport carries digests behind the same seam; the Digests
     screen is retired per 156. Deployed config untouched: console transport,
     nothing sent, flip steps in the baton §4. Every new guardrail verified by
     plant — eleven plants, eleven named failures, including one that caught a
     scanner reading its own comment and one that proved a masked-log test was
     guarding the wrong call site until it was re-planted against the right one.

     * **The status vocabulary is three, not two.** The task named sent/failed;
       'skipped' is the third real outcome (label-skip, staleness, evidence
       gate, unroutable, no-transport-for-kind) and folding it into 'failed'
       would make "the transport tried" unfalsifiable in the ledger review.
       'sent' is final; 'failed'/'skipped' claim the slot but stay upgradable,
       and re-recording the same non-sent status is a no-op — that transition
       rule IS the alert dedupe, so a standing skip costs one ntfy, not one a
       minute. This supersedes 152's "skipped without recording" detail; the
       property 152 actually ruled — the slot releases the moment the label is
       set — survives as a status transition instead of an absent row.
     * **MORNING_STALE_CUTOFF = 2 hours** (the flagged v1 constant): nothing
       "about this morning" goes out after 10:30 local. Consequence accepted
       and tested: a first pass at 11:00 sends the ask and never the morning
       digest. Asks deliberately have no staleness — ask-clock semantics are
       157's Wave C item.
     * **The evidence window is 06:00 → evening digest**, the evaluator's own
       `is_quiet` over the day. A day whose only events are charger plumbing
       counts as zero evidence, which is law #6 agreeing with the gate.
     * **Failed/skipped slots re-attempt once a minute** while due (bounded by
       the cutoff for the morning digest, by midnight for the rest). Alerts do
       not repeat; HTTP retries against a down Resend do. Accepted for one
       family; backoff is a later-families concern.
     * **Email shape:** subject "A note from Kettle" lives in the template
       registry and passes the copy-law scan; from defaults to
       `Kettle <notes@send.heykettle.com>` (RESEND_FROM overrides), reply-to
       `hello@heykettle.com` — both per docs/auth-smtp-plan.md's pattern,
       words are the founder's to change. Plain text only, so the tracking-off
       rule has nothing to rewrite.
     * **`ops_alerts` gains `outbound_*` kinds** — same founder-only posture as
       the heartbeat's rows; the pilot-paths test now pins that every outbound
       write there carries the prefix rather than pinning the table empty.

---

## The 1000-row cliff (implementer, 2026-08-23)

160. **Prod bug, fixed: the Today card showed a stale "Last routine seen" over
     a parent who was actively pinging.** `loadSnapshot`'s `readAll("pings")`
     selected with no order and no limit; PostgREST silently caps such a
     response at 1000 rows, prod pings crossed 1000 today (1051 at diagnosis),
     and the client computed "latest" from an arbitrary 1000-row subset that
     the newest pings fell outside. Left alone it worsens daily and ends at
     "Quiet so far" over someone mid-routine — the exact dishonesty the Glance
     laws exist to prevent. Filed under failure family 1: the read *worked*,
     the data was simply incomplete (bullet added to
     `docs/failure-families.md`).

     **The fix**: pings are fetched per parent — last 14 days, `ts_utc`
     descending, limit 500. Descending order means truncation of any kind
     drops the oldest rows, so the newest ping always survives; the per-parent
     partition stops one prolific phone crowding a sibling out of a shared
     cap. The `eq(parent_id)` is a shape filter over parents the snapshot
     already holds, not an isolation filter — RLS still decides visibility,
     `data.ts`'s no-family-filter law stands. Every other `readAll` table now
     carries a written reason it cannot plausibly reach 1000 rows per family
     (families: one; parents/members: a handful; parent_signals: people × a
     fixed vocabulary; setup_links: manual founder issuances), and a test
     asserts the set of unbounded reads is exactly that list, so a new table
     re-runs the audit by failing. The regression suite runs against a
     PostgREST-faithful fake that honours order/limit/filters and then caps at
     1000 silently; planted reverts (the whole old read, and dropping only the
     `.order`) fail by name.

     **Two consequences of the 14-day window, flagged rather than hidden.**
     Both surfaces that read pings for "has this ever happened" now see at
     most 14 days: (a) a tripwire whose last ping is older than the window
     renders as never-reported ("Not set up yet") instead of "N days ago" —
     with daily-ish cadences a signal silent 14+ days has long since paged the
     founder via heartbeat, but the label is still wrong about setup state;
     (b) the Setup card's "first ping heard" check reverts to unheard if a
     parent's only pings age out. If either matters before the next pass, the
     repair is a per-(parent, signal) latest-row read (limit 1, no window)
     feeding the tripwire and setup surfaces — small, and the PM's to order.
     The window and limit are named constants (`PINGS_WINDOW_DAYS`,
     `PINGS_LIMIT_PER_PARENT`), one edit to overrule.

---

## Wave C copy and the prod cleanup (PM, from the founder, 2026-08-23)

161. **Two new template bodies, verbatim (founder-approved 2026-08-23), joining
     DECISIONS 151's five.** Recorded here in full, same reason as 151. Both
     pronoun-free, no em dashes, {relationship} per DECISIONS 149.

     6. All-clear (to the child, only after a follow-on has gone out, when the
        parent's routine resumes):
        "The shape of {relationship}'s usual day is back. Kettle returns to its twice-a-day notes."
     7. Unreachable-phone follow-on (replaces the standard follow-on when the
        phone has stopped reporting entirely, per DECISIONS 157's mechanism_ok
        distinction):
        "{relationship}'s phone has been silent today, which is different from a quiet morning. A phone that is off or out of battery looks exactly like this. A call from you settles it either way."

     The standard follow-on (151 body 5) remains for the changed-morning case:
     signals still arriving, routine absent. Which follow-on renders is the
     engine's distinction to make; the two bodies never both send for the same
     day.

162. **Prod data cleanup, 2026-08-23 (founder-run via SQL editor, PM-authored).**
     Deleted outright, history included: Kettle Demo Family (Demo Amma, Demo
     Appa, Demo Wife) and the three provisioning-test "Patel" families (Dad
     London, Mom Chicago x3). Kept: Rehearsal (TestDad, TestMom — the founder's
     and his wife's instrumented phones, now labeled Dad/Mom) and Suryaprakasam
     (Amma/Mom, Appa/Dad). Prod now holds exactly 2 families, 4 parents, 0
     unlabeled. Ledger reviewers: rows before this date may reference families
     that no longer exist; sent_messages/ops_alerts for the deleted families
     were removed with them. The label-less-parent skip alerts stop as of this
     cleanup.

---

## Wave C pass build notes (implementer, 2026-08-23)

163. **The ask/reply rung and the Wave C tier are built; the calls inside, each
     cheap to overrule.** Templates 6 and 7 verbatim from 161 (pinned against
     the ruling's text); migration 0016 widens the kind check to 'all_clear';
     the `twilio_whatsapp` transport carries the ask and only the ask; the
     reply webhook verifies Twilio's request signature; escalation, the
     unreachable distinction and the all-clear are live in the engine. Console
     stays the deployed default; the flip steps are in the baton. All
     guardrails plant-verified — and two all-clear tests initially PASSED
     their plants, one because the ledger's unique index masks a re-SEND by
     refusing only the re-record, one because a transport that cannot carry
     the all-clear hides a wrongly-earned one behind its own skip. Both were
     re-aimed at the real observable (the transport's send list) before the
     plants failed properly. Failure family 2, working as intended.

     * **The 159 amendment, filed as ordered.** The follow-on's precondition
       reads the day's ask row at ANY status (`db.message_row`, the
       escalation-clock lookup) — an ask that recorded skipped or failed still
       starts the grace clock from the moment it was due, so a missing phone
       number cannot silently disable the ladder. Everything else that treats
       a row as "Kettle spoke" is unchanged and sent-only: the sent-once
       check, the all-clear's follow-on precondition, and the reply matcher —
       an undelivered ask is not an answerable question, and a test pins that
       the amendment reaches the clock and nothing else. One knowing
       consequence: an unsendable ask keeps retrying after the follow-on has
       gone, so a late-recovering channel can deliver an ask post-escalation;
       harmless (it is still a question to the parent) and noted rather than
       special-cased.
     * **Multi-channel is a comma, not a mode.** OUTBOUND_TRANSPORT accepts a
       comma list building a first-match-by-kind roster in the order named;
       one bad name or missing credential refuses the whole boot, and a list
       never partially applies. Wave C's value is `twilio_whatsapp,resend`.
       Pre-routing skips (staleness, evidence, label) record the stack's name
       ("roster"); routed outcomes record the leaf carrier's.
     * **The unreachable window is the local day from midnight**, any signal,
       any grade, allowlist-blind: "has this device said anything at all
       today". A 03:00 ping is not a morning but it IS a phone that reported,
       so it selects the changed-morning body. This count never anchors
       reassurance or alarm (law #6); it only chooses which follow-on reports
       the silence honestly.
     * **The all-clear's resolution record is its ledger row** — one per
       (family, parent, day) under the existing unique index; no new table.
       Sent follow-ons only: a skipped follow-on earns no all-clear, because
       the family was never worried by Kettle in the first place.
     * **The webhook keeps the shared secret as break-glass** beside the
       Twilio signature; either credential admits, neither configured means
       the route does not exist, and the signature is verified against
       PUBLIC_BASE_URL + path — the URL Twilio signed, not Fly's proxied one.
     * **`twilio_signature.py` returns from the retired list deliberately**:
       rebuilt for /outbound/reply, written new, and the retirement guardrail
       now records why it left.
     * **Open question for the PM, flagged not built:** the evening-normal
       digest ("An ordinary day, start to finish") still sends on a day that
       carried a follow-on and an all-clear, since the evidence gate sees
       signals. Whether a followed-up day should close with that sentence is
       a copy ruling; the engine change is small once ruled.

164. **(2026-08-23, Fable) A followed-up day gets no evening digest.** Answering
     163's flagged question: "An ordinary day, start to finish" is a false
     sentence on any day Kettle escalated, and no ordinary-day body belongs on
     it. Ruling: when a follow-on (either body) has been sent for a parent's
     day, that day's evening digest is withheld — not replaced, withheld. The
     follow-on and, when earned, the all-clear already told the day's story;
     the twice-a-day notes resume with the next morning digest. The withholding
     is recorded in the ledger the same way the evidence gate records its own
     (no silent absence), but it raises no ops alert — this absence is the
     system working, not failing. Small build; goes into the next product pass.

---

## The followed-up evening (implementer, 2026-08-23)

165. **DECISIONS 164 is built exactly as ruled; two mechanics worth a
     reviewer's eye.** The withhold sits with the other withhold rules in
     `run_outbound`, checked BEFORE the evidence gate so a still-quiet
     followed-up day records the 164 reason silently rather than the gate's
     loudly — the quiet-day test is what pins that ordering. The no-alert path
     is `_record_outcome(alert=False)`: the ledger row still says why the slot
     is empty (no silent absence) and an info log line remains, but neither
     ntfy nor `ops_alerts` hears — asserted against both. SENT follow-ons
     only, per the ruling's word: a skipped follow-on told the family nothing,
     so their evening note still comes, and a plant that widens the check to
     any-status fails by name. Resumption needs no code: the next local day is
     a new ledger slot by construction, and a test walks into 2026-08-22 to
     prove the morning digest returns. Suites: pytest 386, zero xfails, ruff
     clean; three plants, three named failures — plus one bonus catch during
     the build, when the registry-only copy scan rejected a code comment for
     quoting the evening body verbatim, which is that guardrail doing
     precisely its job.
