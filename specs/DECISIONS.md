# Decisions

Claude Code: when a spec is ambiguous or looks wrong, add a dated entry here — don't
guess, don't build around it. Fable reviews this file on every pull. Numbers are
continuous and never reused.

**Next number: 229.** This line is the one to update; the `Next number:` lines inside
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

---

## The window's floor lifted (implementer, 2026-08-23)

166. **DECISIONS 160's flagged consequence is repaired as prescribed, webapp
     only.** The snapshot now carries two ping sets with their audiences
     named: the 14-day window (160, unchanged) feeds the Today card and the
     day arc; a new `latestPings` set — one row per (parent, signal), ts_utc
     descending, limit 1, deliberately no time window — feeds exactly the
     tripwire ages and the Setup card's has-ever-pinged check. A tripwire
     whose last ping is 20 days old says so again instead of "Not set up
     yet", and a parent whose pings aged out stays "reporting". Suites:
     webapp 119, full `npm run ci` clean; product/site untouched.

     * **Keyed off the allowlist, inactive rows included** — history counts
       for "has ever pinged", and the read count is people × the fixed signal
       vocabulary, bounded by construction rather than by table growth, which
       is what admits an unwindowed read to data.ts's explicit-order-and-limit
       discipline. The audit test now names the two legal shapes of pings
       read; anything else fails it.
     * **The App call sites are pinned at the source** (the queries.ts
       precedent): both sets share the `Ping[]` type, so rewiring a surface
       back to the windowed set would compile cleanly and quietly
       reintroduce the false sentence — a source-scan test holds
       computeTripwires and buildSetupEntries to `latestPings` and
       computeGlance to the window. Three plants, three named failures
     * **Cost accepted:** up to parents × signals extra limit-1 requests per
       45-second poll (≤ ~16 today). A per-family RPC or view collapses them
       if that ever matters; not built unprompted.

167. **(2026-08-23, Fable) Phone numbers shown to a family are always full
     international format, and the preferred form is a link that does the
     typing.** Learned live: the founder's mother could not join the WhatsApp
     sandbox because the number was given as a bare US-format string. WhatsApp
     resolves a bare number using the READER'S country code — her Indian-numbered
     account looked up +91-415-523-8886, which does not exist, and offered her
     "invite to WhatsApp" dead ends. The founder's US phone resolved the same
     string fine, which is exactly why this class of bug survives founder
     testing. Rules, applying to every family-facing surface and instruction
     (setup page, WhatsApp copy, emails, support replies): (1) numbers render in
     full E.164 with the + and country code, always; (2) any step that asks a
     person to message a number ships as a tap-to-act link with the message
     pre-filled (wa.me/<E164-digits>?text=... style), never as "send X to Y"
     prose; (3) anything a parent must do is walked through mentally on a
     non-US, non-technical phone before it ships. The fix that worked:
     https://wa.me/14155238886?text=join%20leader-color — one tap, message
     pre-typed. Same family as the copy laws: the surface must work for the
     least-technical reader, not the author.

---

## Canonical-host coverage (implementer, 2026-08-23)

168. **The test DECISIONS 148 flagged is built; how it earns trust is the part
     worth reading.** `site/src/tests/canonicalHost.test.ts` parses the real
     nginx.conf and simulates nginx's documented host dispatch — exact
     server_name, else default_server, else the FIRST block in the file, the
     rule whose absence from anyone's head caused the outage — then follows
     redirects across hosts. Seven assertions: canonical 200 first try; old
     host exactly one 301 to https://heykettle.com/ and no chain; www pinned
     as production-correct (deliberately unnamed → default block → direct 200;
     naming it someday fails the pin and forces a decision); default_server on
     the serving block and only there; no Host can loop; /healthz on the old
     host answers rather than redirects (142/158); and a config-shape pin.

     * **The simulator is not trusted on its own word** — that would be 148's
       "confident and wrong" comment wearing a test's clothes. It was
       validated against a real nginx 1.24 running this exact config in this
       container: healthy config produced 200/200/301+200/200 across
       canonical/www/old/unknown hosts exactly as the simulation says, and
       with `default_server` removed the real binary looped
       (301 → itself) precisely as the simulation does. The test header
       records this; the parser throws on any unrecognised config shape and a
       shape-pin test routes restructures back through real-binary
       validation instead of letting the simulation drift from reality.
     * **Why simulate at all:** no nginx binary exists on the founder's
       machine or in this suite's other hosts, and a test that skips without
       one is the false green (family 1) while a test that requires one makes
       the verdict machine-dependent (family 6). The simulation runs
       everywhere; the binary check went where the binary lives instead —
       `RUN nginx -t` in site/Dockerfile, so an unparseable conf fails
       `fly deploy` at build, never at serve.
     * Three plants, three named failure sets: default_server removed (the
       outage itself — five tests fail, the loop among them), the old host's
       redirect pointed back at itself, and www quietly added to the redirect
       block. Test-only pass: no deploy owed for it.

169. **(2026-08-23, Fable) Webapp restyle phase-1 scope, and two copy rulings
     from the v5 design audit.** The locked v5 design (docs/Kettle-Design.html,
     spec 008) ships in phase 1 as Today + Parent detail + Family-parents-list
     only. Out: the Digests screen (156 still governs; when it returns its
     notes are per-parent — v5's merged "ordinary day for Mom and Dad" bodies
     are ruled out), per-member note toggles/invites (157's later tier), and
     add-a-parent (onboarding pause, Q126). Copy: "She answered — all is well"
     becomes "She answered." — the reply is content-blind and "all is well"
     asserts knowledge Kettle does not hold. Otherwise the v5 strings passed
     the full audit: no parent speech, no send-a-note, no counts or bars, no
     mechanism words.

170. **(2026-08-24, Claude Code) Spec 008 built — the execution calls, filed
     not guessed.** Webapp restyled to Kettle v5 (Today, Parent detail,
     Family parents-list; nav is Today and Family only). Suite 119 → 101:
     three glance-era suites retired with their screens, two suites added
     (`parentState`, `kettleGlyph`). All calls below are reversible; PM veto
     requested where marked.
     * **"She answered." (169) does not render anywhere.** Not defiance of
       the ruling — the client cannot know it: reply state lives in
       `sent_messages`, which is RLS deny-all to the family app by design.
       The ruled string is the right copy for whatever surface can see
       replies (the founder digest, a future server-rendered note); no such
       surface exists in the webapp. Needs a PM home, not a webapp hack.
     * **Unreachable is defined as:** at least one tripwire has reported at
       some point, every tripwire that ever reported is now stale, and none
       is connected. A never-configured signal is a setup step, not silence
       (005d's unconfigured ruling carried forward), and one connected
       tripwire vetoes the state however stale the rest — both pinned by
       test. The sentence is about the phone (law #6).
     * **v5 strings that assert unobservables do not ship:** the
       learned-cadence aside ("His mornings usually start around eight") is
       trend inference (hard constraint 1 / DECISIONS 59 deferral), and the
       dusk "Quiet all day" close is darker than the floor. "Quiet so far"
       remains the darkest person-sentence in the app.
     * **The fix card keeps the existing repair-nudge body.** The v5 file's
       fix steps say "Open Kettle on the phone" — there is no app on the
       parent's phone; the honest repair is the two-minute FaceTime the
       nudge already describes. v5's "Text the steps" button is omitted with
       it (fan-out tier, 157). Same gate as the nudge: a tripwire that
       *stopped* reporting.
     * **The About block renders only fields that exist:** no city field in
       the schema, so no city line; the clock difference ships in words
       ("Ten and a half hours ahead of you"), falling back to "A different
       clock from yours." for shapes the word list cannot carry (Kathmandu
       from Chicago). Setup month from the earliest setup link.
     * **Family keeps its live surfaces** — the 005b setup card (122's CTA
       pin intact) and the member roster — restyled under the v5 parents
       list, though the spec's scope list names only the list. Deleting a
       live forwarding surface needed a ruling; keeping it did not.
     * **No third-party font requests.** The v5 stacks name Newsreader and
       Source Sans 3; they are named in the stacks with Georgia/system
       fallbacks, and nothing is fetched (hard constraint 4 posture).
       Self-hosting the faces is a separate, PM-priced step.
     * **Night is driven by `prefers-color-scheme`** onto `body[data-kt]`,
       live on the OS toggle. No in-app switch until a spec asks.
     * **Day-row and recent-day wording is my mapping from the v5
       vocabulary** ("An ordinary morning — heard from at 8:15 am." /
       "Quiet so far." for the stretch being stood in / "Quiet." only for a
       finished one / "Still to come." / "Nothing has reached Kettle.";
       recent days: "An ordinary day." / "A quiet day." / "Nothing reached
       Kettle."). No verdicts on unfinished time. Veto welcome, strings are
       one file (`webapp/src/lib/copy.ts`).
     * **The copy law came out stronger:** the tripwire rows were the one
       surface allowed signal names; rows gone, exemption deleted — no scan
       carries a signal-name allowlist any more. Gendered pronouns joined
       the rendered-surface ban (24/34): fixtures record no pronoun, so a
       hardcoded she/her in any default string fails. Two allowances remain
       beside 122's CTA: day-words recency ("6 days ago", the 005d §2
       shape, now on the last-heard meta) and the Today date line.
     * **`phone_e164` joined the parents read surface** (structure 48 +
       DECISIONS 167): fetched to build the Call button's `tel:` href and
       nothing else; a printed digit anywhere fails the law scan, and the
       Call button renders only when a number exists.

171. **(2026-08-24, Fable, founder-approved) The service's formal public name
     is "HeyKettle."** Meta rejected both "Kettle" (generic, no entity
     linkage) and "heykettle" (the exact string, capitalization included,
     must appear on the business's website — it did not). Ruling: HeyKettle
     (capital H, capital K) is the formal name on public/legal surfaces —
     site title, footer, privacy policy, the WhatsApp sender name — operated
     by LINKABIT AI LABS LLC. "Kettle" remains the friendly short form
     everywhere inside the product: wordmarks, app UI, message bodies, "The
     kettle's on." No existing customer copy changes; the site gains three
     evidence lines (title, footer, privacy sentence) in their own pass, then
     the display name is resubmitted as exactly "HeyKettle."

172. **(2026-08-24, Fable) Restyle review verdict on DECISIONS 170's flagged
     calls.** Accepted: the unreachable definition and its pinned edges; the
     withheld learned-cadence aside and "quiet all day" dusk close (both
     violate the inference ban / darkness floor — v5's copy, not ours); the
     honest FaceTime fix body over v5's steps for an app the parent does not
     have; request-free fonts; the day-row/recent-day vocabulary mapping.
     Ruled: "She answered." is WITHHELD from the webapp until a purpose-built,
     family-readable reply surface exists — it will ride with the post-beta
     Digests-return view (156); the ledger stays deny-all. Two copy vetoes:
     EMPTY_TODAY becomes "No one is set up yet." ("watched over" is the
     framing this product exists to avoid), and FIX_BODY becomes "Something on
     {name}'s phone may need a quick fix. It's a two-minute FaceTime."
     ("tripwire" is internal vocabulary and never customer-facing; extend the
     copy-law scan's mechanism-word list with "tripwire" so it cannot
     return).

173. **(2026-08-24, Claude Code) DECISIONS 171/172 built — the execution calls.**
     Site suite 181 → 183; webapp 101 → 102; product 386 unchanged. Nothing
     deployed.
     * **The entity name required an allowlist widening, done in the
       DECISIONS-62 shape.** "LINKABIT AI LABS LLC" contains "AI", which the
       site's inference ban word-bounds — the footer line and the privacy
       sentence would have failed the scan. The allowlist (page-wide and the
       privacy page's own) gains one literal: the bare registered name.
       Pinned on both halves by test, with would-catch assertions proving
       "ai" outside that exact string still fails. A proper noun in a legal
       line is not the sound the ban exists to stop.
     * **`PAGE_TITLE_LABEL` follows the title** — the existing prerender
       tether caught the drift before any test did. Title is pinned as
       "HeyKettle — Know the day started normally."; the hero H1 and footer
       wordmark are pinned as staying "Kettle"/unchanged, so the formal name
       cannot creep onto friendly surfaces.
     * **The privacy sentence ships in the page's own typographic style**
       (&ldquo;-entities, matching the rest of the file); the scan decodes
       before comparing, and the fetch-nothing law was re-asserted: no
       links, no absolute URLs, plain text.
     * **The webapp constant renamed with its body**: TRIPWIRE_REPAIR →
       FIX_BODY (aligning with FIX_TITLE), renderRepairNudge →
       renderFixBody. The ruling's ban lands as "tripwire"/"tripwires" in
       the rendered-surface mechanism list; identifiers, filenames
       (lib/tripwires.ts) and test names keep the word — the scan walks
       rendered text only, which is the exemption the ruling describes.
     * **EMPTY_TODAY had no fixture rendering it** (it appears only with
       zero parents), so the veto also added the first empty-state scan:
       the new string pinned, "watch" vocabulary asserted absent, full law
       over the render.
     * **The product-side copy contract followed** (test-only; nothing the
       pilot runs changed): the pin moves to FIX_BODY, asserts no TRIPWIRE_
       constant exists in the copy module, and scans every exported webapp
       string for "tripwire" — the Python half of the same ban. Flagging
       because the task said "product/pilot untouched": leaving the
       contract pinning a vetoed string would have been a red suite, and
       the contract is the webapp copy's other half, not pilot code.
     * Five plants, five named failures: extra "AI" smuggled beside the
       entity name; the privacy sentence removed; the title reverted;
       "tripwire" back in the fix body (caught by webapp scan AND product
       contract); "watched over" back in the empty state.

174. **(2026-08-26, Claude Code, PM-ordered) The blog exists, and post #1 is
     published verbatim.** Site only; suite 183 → 196; nothing deployed.
     * **Post #1** is `docs/blog-post-1-draft.md`'s body, shipped verbatim
       between sentinel comments and diffed paragraph-for-paragraph against
       the draft by test — the Editor's notes and title-options block
       stripped, nothing else touched. Title: "The call I've rehearsed and
       never made". Slug: `/blog/the-call-ive-rehearsed-and-never-made`
       (canonical form carries the trailing slash; the slash-less form is
       one relative 301 away).
     * **Teaser, verbatim:** "On the phone call every far-away child
       rehearses, and never wants to make."
     * **Meta description, verbatim:** "My parents live in Chennai and I
       live in the US. This is about the call I hope I never have to make."
     * **Byline** is "Hema · Founder, HeyKettle" — the middot form, since
       the copy this pass authors carries no em dashes (the body, being
       final, is exempt from every scan; a test proves the exemption is an
       excision, not a lax rule).
     * **Form:** two standalone pages in the privacy.html posture — locked
       palette inlined, Newsreader named for article text with Georgia
       standing in and no font fetched, 66ch measure, no scripts, no links
       out, no absolute URLs. No og:image yet.
     * **The site's first header:** wordmark plus one quiet Blog link, and
       the same link in the footer nav. Deliberately not a second CTA; the
       hero still offers exactly one next step.
     * **nginx learned `absolute_redirect off`,** because the blog is the
       config's first directory-shaped content and the index module's
       trailing-slash 301 would otherwise be written absolute from nginx's
       own view — `http://<host>:8080/blog/`, wrong scheme, unreachable
       port behind Fly's TLS proxy. Validated against a real nginx 1.24
       over the real layout (the 168 discipline) in both the healthy and
       the planted state; the canonical-host simulator gained the same
       file model and reproduces both redirect shapes, so removing the
       directive fails the suite the way it would fail production.

175. **(2026-08-26, Claude Code, PM-ordered) The blog entry is the way in,
     visibly.** Founder feedback on /blog/: the entry read as static text
     ("I had to think about where the entire article was"). The whole block
     (title, date, teaser) is now one anchor to the article: the title
     carries the site's link treatment at rest (underline, 4px offset), the
     block tints on hover and shows a focus-visible ring, and the entry
     closes with an explicit read line in the link style. The string,
     verbatim: **"Read the post →"** (arrow U+2192; no em dash anywhere in
     the authored chrome, which the existing scan enforces and did enforce:
     it caught an em dash in this pass's own CSS comment before commit).
     Accessibility: the anchor's accessible name is the post title via an
     aria-labelledby pair, and no link nests inside the block link. Tests
     pin the affordance itself: one anchor carrying all four lines, the
     at-rest underline plus hover/focus declarations, the read line
     verbatim, and the no-nested-anchors rule. Site suite 196 → 199.

176. **(2026-08-26, Claude Code) Spec 009 §1 built — "normal" everywhere,
     "in N days".** `STATE_ORDINARY` renders "Today looks like a normal
     day." (internal name unchanged); the unreachable duration is "Nothing
     has reached Kettle in {n} days." / "…in 1 day." The webapp copy scan
     now bans "ordinary" as a rendered word, "checked in" as a phrase, and
     the "since N days ago" shape (checked against unmasked text so no
     allowance can hide it); the product-side contract pins the same three.
     The RECENCY_ vocabulary retired whole with the old rows — relative
     forms live in `renderHeard`, which has no clock variant by
     construction.

177. **(2026-08-26, Claude Code) Spec 009 §2 built — Today.** All strings
     verbatim from the spec: rollup "Everything looks normal today." /
     "Quiet so far for {names}." (names joined "Mom, Dad and Grandma" —
     words, never a count) / the unreachable sentence; sub-line "Next note
     this evening." / "Next note in the morning."; footer "Nothing needs
     you today." + "Kettle will write if that changes." (bold first
     sentence, only when every parent is normal); card lines "{city} ·
     {time} there now" / "{time} {Name}'s time", "Heard from moments/N
     minutes/1 hour/N hours/1 day/N days ago" with the DECISIONS 166 form
     past the window, dual line "{time} in {city} · {time} your time";
     "Call {Name} ↗", "View {Name}'s day →". Execution calls, flagged:
     * **The Call pill ships on `--copperdeep`, not the mockup's
       `--copper`.** White-on-copper at the mockup's 14px bold reads
       3.94:1 — below §6's own 4.5:1 law, which this spec makes a tested
       law. Copperdeep reads 5.6:1 (6.9:1 Night). The mockup's copper
       CHOICE (over green) is honored — same family, one shade deeper —
       but the PM should ratify or re-spec the size upward (18.7px bold
       would make copper lawful as large text).
     * **The evening-digest hour is a mirrored constant**
       (`EVENING_DIGEST_MINUTES` = 20:30, from outbound.py's v1 value,
       family-local). An engine retune must touch both sides.
     * The name in every {Name} slot is the relationship label where set
       (149's vocabulary), else display_name.

178. **(2026-08-26, Claude Code) Spec 009 §3 built — the detail.** Arc:
     one quadratic drawn twice (identical `d`, pinned), reveal via
     pathLength/dasharray, dot computed on the same curve at the same t
     (the mockup's own 82% point is the test fixture). Segments at
     noon/six with the LAST heard time per segment; dots are seven,
     oldest left, today right, fill-vs-outline plus an always-visible
     legend ("A normal day" / "A quiet start" / "Couldn't hear"), no
     digits anywhere in the panel (tested). What-this-means verbatim per
     state; unreachable's body is the standing aside. Flagged calls:
     * **The CURRENT segment with no pings reads "Quiet so far"** — the
       spec captions only past-with-none ("Quiet") and future ("Still
       ahead"); a bare "Quiet" on unfinished time would be a verdict
       (the standing spec-008 rule), so the hedged form fills the gap.
     * **"See the simple steps →" routes to the Family screen's setup
       card** — the only steps surface that exists; a dead link would
       break the never-a-dead-button law. PM may re-point it.
     * The hero is the 44px glyph per the mockup (the 200px hero was
       spec 008's; geometry untouched, from KettleGlyph only).

179. **(2026-08-26, Claude Code) Spec 009 §4 built — Family notes v1.**
     Migration 0017: table as specced, RLS mirroring 0002 exactly
     (deny-all; family select+insert; a tagged parent must belong to the
     same family; no update/delete), select+insert plus identity-sequence
     usage granted — verified against a real local postgres in every
     direction before tests pinned it, and the weakened-policy plant
     fails the isolation test. Scoping as ruled: parent page filters,
     Family consolidates with tag prefixes, null renders "Family". The
     Upcoming strip and entry metadata verbatim. Linkification is
     escape-then-build: bodies render as text nodes and panel-built
     anchors only (target=_blank, rel=noopener noreferrer, copper
     underline); a body containing <script> renders inert, by test. Both
     read scopes are newest-50 with explicit order and limit (160
     discipline), audited beside the ping reads. Flagged strings the
     spec was silent on: the composer's submit button "Add" (keyboard-
     only Enter would fail §6) and the tag picker's accessible name
     "Who this note is about". "Signed as" persists via localStorage,
     empty renders as "Family".

180. **(2026-08-26, Claude Code) Spec 009 §5 built — the city label.**
     Migration 0018: `parents.city_label text` with a 40-char check; the
     update grant is COLUMN-scoped so `display_name` stays refused on the
     same table (pinned product-side), and RLS bounds a blanket update to
     the caller's own family (tested live, then pinned). The Family
     screen's parent row carries the "City" field; where absent every
     surface falls back to "{Name}'s time". Timezone stays uneditable.

181. **(2026-08-26, Claude Code) Spec 009 §6 built — accessibility as
     law.** Every fontSize in the spec-009 surfaces is a rem string,
     enforced by a source scan (px zoom-breaks fail by name); AA contrast
     is computed from kettle.css's own token values for both palettes over
     the exact ink-on-surface pairs the screens use, with the chip
     outlines held to 3:1; no state rests on color alone (fill-vs-outline
     plus legend, tested). Token consequences, flagged: Day `--mute`
     darkened to mockup v2's #6E6A62 (the v5 value read 2.85:1 and §6
     puts metadata text in it); Night `--mute` lifted to #8F887C by the
     same law — an execution call, since the mockup ships no Night set.
     Reduced-motion gating is unchanged from spec 008 (the keyframes
     exist only inside the media block).

182. **(2026-08-26, Fable) Spec 009 review verdict: PASS. All six build
     flags ratified.** Checked the report against spec 009 section by
     section; every ordered surface, migration, law, and test is present,
     and the eight plant drills fired by name. Rulings: (1) the Call pill
     ships on `--copperdeep` — the contrast law outranks the mockup's
     exact shade, and copper-the-choice survives; (2) the Day `--mute`
     darkening and the Night `--mute` #8F887C stand, with the Night
     palette to be eyeballed on a real phone after deploy; (3) the
     current-with-no-pings arc segment caption "Quiet so far" is adopted
     into the state vocabulary; (4) "See the simple steps →" routing to
     the Family screen's setup card stands until a dedicated steps
     surface exists; (5) the composer strings "Add" and "Who this note
     is about" are adopted verbatim; (6) the mirrored
     `EVENING_DIGEST_MINUTES` constant is accepted with a standing note
     that any change to the outbound slot must touch both, recorded here
     so the drift has a name. Deploy order per the baton: 0017 then 0018
     applied to prod by the PM via MCP before `cd webapp && fly deploy`
     (Hema).

183. **(2026-08-26, Claude Code, PM-ordered correction to spec 009 §2) The
     webapp renders display_name, never the relationship label.** The spec
     put the relationship on the card kicker, and two parents who share one
     render indistinguishable cards — TestDad and Appa both read "DAD" on
     Today, in the rollup, on the Call pill, and in the notes prefixes.
     Names disambiguate; labels do not. `labelFor()` now returns
     `display_name`, and because every {Name} slot flows through it, one
     change corrects the card and detail kickers, the rollup ("Quiet so far
     for Appa."), "Call {display_name} ↗", "View {display_name}'s day →",
     the "{display_name}'s time" fallback, the what-this-means bodies, and
     the Family notes tag prefixes and composer picker. The relationship
     vocabulary (149) remains the OUTBOUND channel's register by design —
     email subjects and templates are untouched. Regression pinned: two
     parents sharing a relationship render distinct card names, and the
     plant (relationship restored in labelFor) fails eight tests by name.
     Housekeeping: `parents.relationship` still rides in the read surface
     un-rendered; the PM may narrow that read. Also: item 182 was filed
     without bumping the counter line — this entry took 183 and the line
     now says 184.

184. **(2026-08-26, Claude Code, PM-ordered) Email polish: per-parent
     subjects, the recovered evening, the HTML wrapper.** Product suite
     388 → 403; site 199 (one hosted asset added); nothing deployed.
     * **Subjects.** An email about one parent carries
       "A note about {relationship}'s day" (e.g. "A note about Mom's
       day"), from `subject_for()` in the registry module so the string
       lives with every other family-facing string and passes the same
       scan under every label. Anything not about a single parent — and a
       parent whose label is not set yet, since the evening bodies can
       send label-less — keeps "A note from Kettle". The relationship
       rides beside the template variables through every transport's
       send() (render() rejects undeclared variables); WhatsApp accepts
       and ignores it.
     * **The recovered evening.** New template
       `digest_evening_recovered`, body verbatim: "A quiet start, then a
       normal day. Next note in the morning." Selection, at the evening
       slot: the morning was quiet at the morning-digest slot (the same
       window that chose digest_morning_quiet and armed the ask) AND
       routine pings resumed between the morning and evening slots. A
       normal morning keeps `digest_evening_normal`; the followed-up-day
       skip (164) and the evidence gate are unchanged and 164 outranks
       the body choice (tested). Every other recorded body stays
       verbatim.
     * **The wrapper.** Every outbound email is MULTIPART: the registry
       body as plain text plus the outbound_html wrapper carrying the
       same words. Laws, each held by a test: table layout with every
       style inline; no external CSS and no remote fonts (Georgia,
       'Times New Roman', serif); EXACTLY one <img> — the 44px hearth
       glyph at the stable unhashed URL
       https://heykettle.com/email-glyph.png, width/height set,
       alt="Kettle"; no text exists only inside an image (stripping the
       img leaves chip, sentence, sub-line and footer whole); the v5
       palette inline (#F7F2E9 / #FDFBF6 / #2E2822, chip #E7EFD6 /
       #D5E3B8 / #7A4A26, rule #D5E3B8, link #96552D); no em dashes
       anywhere in the markup. The footer reuses EMAIL_SUBJECT verbatim
       plus the site domain as link text, so the wrapper adds no string
       the registry does not hold.
     * **Deploy order:** the SITE ships the glyph asset, so
       `cd site && npm run ci && fly deploy` goes before
       `cd product && fly deploy` — recorded in the baton.
     * **Flag:** the ordered design reference
       docs/mockups/email-polish-mockup-v1.html does not exist in the
       repo; the build followed the order's own written layout and
       palette. If the PM's mockup differs, the wrapper is one module
       (`kettle/outbound_html.py`) to restyle.


185. **(2026-08-26, Claude Code, PM-ordered) Spec 010: the city picker
     that moves a parent.** Product suite 403 → 410; webapp 126 → 145;
     migration 0019 written, NOT applied (PM applies via MCP before the
     webapp deploy); nothing deployed. Spec-verbatim strings shipped:
     placeholder "Where {name} lives", escape hatch "Can't find it? Pick
     the nearest big city.", auto note "{name}'s city changed to
     {city}." authored "Kettle" (§4 ruled BUILD), ops alert
     "{display_name}: timezone changed {old} → {new} (city {city_label})
     via webapp." Judgement calls the PM should check, each flagged in
     the report too:
     * **The changeover stamp compares the EFFECTIVE zone.** §1 says the
       stamp is written "only when the tz value actually changed". A
       parent starts with tz null and inherits the family zone, so
       "actually changed" is read against `parent.tz ?? family.tz`:
       picking a city in the inherited zone writes label + tz and NO
       stamp — a clock that never moved must not open a conservatism
       window. (`placeUpdate` in webapp/src/lib/data.ts, pure and
       pinned.)
     * **The changeover skips go through the ALERTING skip path.** §3
       asks for a skipped ledger row "whose detail names the timezone
       change" — but sent_messages has no detail column (0012), so the
       detail lives where details live: the ops_alerts row the alerting
       path writes, plus ntfy. A relocation day carries at most a
       handful of them. The 164 precedent (alert=False) was considered
       and rejected: that withholding is routine; this one is a
       once-per-move event the founder is already being told about.
     * **The old zone in the move alert.** Nothing stores the previous
       tz. First move: the old zone is the family's (what the engine was
       actually using). Later moves: parsed from the engine's OWN
       previous tz_changed ops_alert message — a pinned format
       round-tripped by test. A cleared city label renders "(city
       unset)", never blank.
     * **"Either zone's version of the day" is implemented as ANY
       zone's.** The webapp cannot read the old zone (it only holds the
       new tz), so the changeover dot reads normal if any routine ping
       landed in the widest UTC span the calendar date can occupy
       (UTC+14 through UTC−12, date 00:00Z − 14h to + 36h). Wider than
       either real zone's day, and can only UPGRADE the dot — the ruled
       direction (never "quiet", couldn't-hear only if truly nothing).
     * **A quiet morning inside the window records `skipped`.** §3 says
       digests still send "chosen from data actually seen" and the
       morning-quiet template is not used in the window. A morning WITH
       data sends digest_morning_normal on time; a morning with nothing
       has no honest body left, so the slot records skipped with the tz
       named in the alert detail, and neither body sends.
     * **The auto note skips a no-op pick.** Re-picking the standing
       city+zone writes (idempotently) but journals nothing — "{name}'s
       city changed" would be false.
     * **Structural:** cities.json (354 entries, every zone swept
       through zoneinfo AND Postgres in the product suite) lives under
       webapp/src/data/, which the root .gitignore's `data/` rule
       (pilot pings) silently swallowed — a scoped `!webapp/src/data/`
       exception is part of the build, or a fresh clone cannot compile
       the picker.

186. **(2026-08-26, Fable) Spec 010 review verdict: PASS. All seven
     judgement calls ratified.** Checked the report against spec 010
     section by section; every surface, the migration, the transition
     honesty, and the test list are present, and the seven plant drills
     fired by name. Rulings: (1) the effective-zone stamp (compare
     against parent.tz ?? family.tz; inherited-zone picks write no
     changeover) is correct and adopted; (2) the changeover skip's
     durable detail living in ops_alerts stands — sent_messages has no
     detail column and the ledger row plus the alert together satisfy
     the spec's intent; (3) old-zone recovery from the engine's own
     previous alert is accepted with a standing note that the alert
     format is now load-bearing and its test is the guard; (4) the
     any-zone widest-UTC-span day classification is the right
     conservative reading of "either zone's version of the day";
     (5) a quiet morning inside the changeover window recording
     `skipped` with no morning body is the honest option — a quiet
     verdict under a moved clock is not evidence, and a normal claim
     would be a lie; (6) the auto note skipping no-op picks stands;
     (7) the scoped .gitignore exception for webapp/src/data/ is a
     structural save recorded with thanks. Deploy order: PM applies
     0019 via MCP → `cd product && fly deploy` → `cd webapp && fly
     deploy` (Hema).


187. **(2026-08-27, Claude Code, PM-ordered) The living kettle joins the
     homepage: placement Option A, and the steam's fixed-pixel bug fixed
     at the law rather than at the value.** Site suite 199 → 213; nothing
     deployed. No new copy was authored, so no copy-law surface changed;
     the chrome scan still runs over the page with the mark on it.
     * **Placement: Option A ("the mark"), over B and C.** A small kettle
       above the hero kicker, 132px wide (inside the ordered 120–140
       range; the wireframe drew 120). It is the only one of the three
       that adds the heartbeat without moving anything — B put the kettle
       beside the copy and made two large images share the hero, C put it
       between the copy and the illustration and pushed the artwork down
       a page that is already tall on a phone. Verified at 360/390/428/
       768/1440 with `scripts/probe-responsive.mjs`: no wrap, no
       overflow, and headline plus sub still land in the first viewport
       at 390.
     * **Asset:** `site/public/kettle-hero.webp` (61KB, 1100×825),
       unhashed and stable, so it falls under the catch-all `no-cache`
       revalidate rule exactly like the illustrations and
       email-glyph.png. The `public/` manifest in
       `product/tests/test_site_caching.py` now names seven files — the
       one file outside `site/` this pass touches, and only because the
       site's own tree-side assertion has always lived there.
     * **The steam is a property of the kettle, never of the page.** The
       ordered bug fix, and it is a law rather than a value: every
       offset, wisp size, blur radius and keyframe travel in
       `src/kettle-mark.css` is a multiple of ONE container-relative unit
       (`--kt-u: 0.2380952cqw` = one mockup pixel at the 420px the
       mockups were drawn for), with `container-type: inline-size` on the
       mark. A bare `px` in that file is refused by the suite. Measured
       in a real browser at 120/240/420px
       (`scripts/probe-kettle.mjs`, not in `npm run ci` — it needs
       Playwright): every wisp's size, rise and span is the same fraction
       of the kettle at all three widths, within 0.002. The same probe
       run against the mockup's literal pixels reproduces the founder's
       report and quantifies it — at 120px the widest wisp is 25% of the
       kettle instead of 7.1%, the rise is 1.477 kettle-widths instead of
       0.183, and the wisps reach −0.215, i.e. off the left edge of the
       pot.
     * **Reduced motion:** every keyframe and every animation declaration
       lives inside the `no-preference` block (what `motion-safe:`
       compiles to, done by hand because these are component rules), and
       the `reduce` block is one faint motionless wisp at the spout —
       the designed still, not an absence. Scanned by position, so a
       declaration that drifts out by one brace fails.
     * **Decoration, said in both ways:** empty alt AND `aria-hidden` on
       the image, `aria-hidden` on both steam layers, `pointer-events:
       none`, no text content, `loading="eager"` (above the fold, 61KB).
       The imagery suite gained a named one-entry DECORATIVE exemption
       rather than a softened alt-text rule, and the eager list is now
       two images, both required to be inside `#hero`.
     * **Recorded as the third animated element** in
       `docs/design-language.md` §6, per the standing rule that a new one
       is an argument made there first. A fourth is a new argument.
     * **FLAG — the asset has an opaque cream ground.** Sampled from the
       shipped webp: every corner is ~rgb(253, 242, 216), alpha 255. That
       is the mockup's `--kettlecream` demo panel, not this site's canvas
       (#f6f2ec), so the mark renders as a faintly visible cream
       rectangle on the hero's morning wash rather than as a floating
       object. Built as ordered and NOT worked around, since the order
       says no image changes: the fixes are a re-export with a
       transparent background (best), or one line —
       `mix-blend-mode: multiply` on `.kt-mark-image` — if the PM prefers
       CSS. Screenshots at 120/240/420 and at phone widths were sent
       with the report.
     * **FLAG — the mockup's `breathe` was not built.** v5 also scales
       the kettle image 1.2% on a 9s cycle. The order's approved list is
       the steam (wisp count, colours, gradient stops, timing, negative
       delays, spout anchor, lid wisp) and the breathe is not steam; at
       132px it is a 1.6px pulse nobody would see, and it would be a
       fourth animated element by the site's own counting. Say the word
       and it is four lines inside the same no-preference block.
     * **Counter note:** item 186 was filed without moving the
       `Next number` line (the same slip as 182). Repaired here: the line
       now reads 188.


188. **(2026-08-27, Claude Code, PM-ordered) The kettle mark's blending:
     multiply is the law, and the asset is what makes it work.** Site
     suite 213 → 214; nothing deployed. **The ground-normalized asset did
     NOT reach this working tree** — see the blocker below.
     * **The rule.** `mix-blend-mode: multiply` on `.kt-mark-image`, and
       the reason is arithmetic rather than taste: multiplying by white
       is the identity, so a drawing whose ground is pure white
       composites to *exactly* the backdrop behind it — hero wash,
       gradient and drifting dots included — while the kettle and its
       soft shadow keep their weight. Nothing above the image may
       isolate the blend (`isolation: isolate`, or an opacity on an
       ancestor): that hands it a white stacking context to land on and
       the rectangle is back. Both halves are pinned in the suite.
     * **BLOCKER — the replaced asset is not here.**
       `site/public/kettle-hero.webp` in this container is byte-identical
       to the version committed in 187 (md5 bd2fa00ae3582ce4444de855c99f4e31),
       and no commit on `origin/main` carries a replacement. Its ground
       still samples rgb(253, 242, 216) at every corner, so multiply
       currently darkens the backdrop behind the mark by 2/13/39 per
       channel — the PM's own ~36-on-blue arithmetic, measured. The
       visible result improves a great deal on the opaque card and is
       still a faint warm rectangle. **The site must not be deployed
       until the normalized file is in the tree**; `node
       scripts/probe-kettle.mjs <preview-url>` says pass or fail in one
       line, and nothing else about this pass changes when the file
       lands. **RESOLVED the same day:** the normalized asset landed on
       `main` (md5 3ff6595b8f7f07806157fc3ed4c3ff3b, 60,010 bytes,
       comfortably inside the eager-load weight bound). Re-probed against
       it: blend mode multiply, ground rgb(254,254,254)/(255,255,253)/
       (255,255,255)/(255,253,252)/(255,255,253) at the five samples, so
       every ground pixel composites to the backdrop. The mark now sits
       on the wash with no rectangle; the deploy is unblocked.
     * **Where the ground check lives.** In the probe rather than in
       `npm run ci`: the fact to check is a property of the webp's
       pixels, which needs a decoder, and the browser the probe already
       launches has one. It samples four corners and the top edge and
       fails with the per-channel shortfall spelled out. Keeping it out
       of `ci` also keeps `ci` honest about what it can actually see —
       it holds the CSS law; the probe holds the asset's.
     * **Asset-bounds note.** Nothing in the suite pins the asset's
       bytes or a content hash, so the replacement invalidates no
       assertion. The one bound that exists — `1KB < bytes < 120KB`, the
       weight promise that justifies loading it eagerly above the fold —
       is deliberately generous and needs no edit unless the normalized
       export lands heavier than 120KB, which would be the right moment
       to make that decision again rather than inherit it.
     * **The breathe omission is ratified.** v5's 1.2% image-scale
       breathe stays out, per the PM. It is not steam, it is invisible at
       132px, and it would be a fourth animated element by the site's own
       counting (design-language §6).


189. **(2026-08-27, Claude Code, PM-ordered) The multiply blend was
     landing on a stacking context, not on the page.** Site suite
     214 → 216; nothing deployed. The PM's diagnosis from source was
     exactly right, and it is the third premise of blending that neither
     of the earlier checks could see.
     * **The bug.** `mix-blend-mode` composites only within its nearest
       STACKING CONTEXT. `sections/Hero.tsx` wrapped the hero's content
       in `relative z-10` — from long before the mark existed — and a
       positioned element with a non-auto z-index makes one. So the mark
       blended against that transparent group rather than against the
       section's wash and rhythm canvas: white ground multiplied by
       nothing stayed white, and the rectangle the normalized asset was
       cut to dissolve was still there. Both earlier checks passed
       through this untouched — the CSS rule was present and correct, and
       the asset's ground was white. My own comment in `kettle-mark.css`
       names this failure; the ancestor predated the mark and I never
       looked up the tree.
     * **The fix: `z-10` removed, nothing added.** The canvas still
       paints beneath the copy on DOM order alone — canvas and wrapper
       are both positioned with `z-index: auto`, and the canvas is
       written first — so no replacement z-index, and in particular
       nothing that would create a second stacking context between the
       mark and the section. Measured rather than reasoned: hiding the
       field changes 4,562 solid-ink pixels of the headline by 0 levels
       of 255, and lifting the canvas with a planted `z-10` moves them
       by 74.
     * **The probe now reads the rendered composite.** This is the
       lesson, not the z-index: the old check read the ASSET's pixels,
       which is a premise of blending rather than blending itself. It now
       screenshots the mark's box, screenshots it again with the mark
       hidden by `visibility` (no reflow), and requires every ground
       sample to equal what multiply is *defined* to produce there —
       backdrop × source ÷ 255 — so the tolerance is rounding (2 levels)
       and not a slack allowance. Before the fix: 27 to 144 levels out,
       the page painting the mark's own rgb(255, 255, 253) where it
       should have painted rgb(245, 237, 226). After: 956 ground
       samples, worst departure 2 of 255. Anything behind the mark shows
       through identically, drifting field dots included, which is the
       "is a dot still visible" question answered by construction.
     * **Two corrections inside the probe itself, both worth not
       undoing.** The ground mask draws the artwork at the size the PAGE
       draws it before deciding which pixels are ground: the mark renders
       at an eighth of the artwork's width, so a rendered pixel beside
       the handle is an average of white ground and dark metal, and
       masking off the full-size art called it ground and then failed on
       the handle. And the ink threshold for the paint-order check is 80,
       a shade above `--ink`'s own red channel (0x40): the first version
       used 60, found zero pixels, and would have passed forever on an
       empty sample.
     * **The regression is pinned in the suite too**, where it is free:
       walk from the mark up to the section and refuse any ancestor
       carrying a stacking-context utility or inline style — z-index,
       opacity below 100, transform, filter, backdrop-filter, blend mode,
       isolation, will-change, contain, perspective, or an animation
       (variants included, since a `motion-safe:` one still applies when
       it applies). `relative` stays legal and is asserted to stay legal:
       positioning alone creates nothing. Planted both ways — the exact
       `z-10` that caused this, and an `animate-rise` wrapper around the
       mark — and each fails by name.


190. **(2026-08-27, Claude Code, PM-ordered) The blend mode is retired: iOS
     Safari would not honour it, and a transparent drawing needs no
     compositing trick.** Site suite 216 → 216 (one pin retired, one
     added); nothing deployed.
     * **The failure.** `mix-blend-mode: multiply` composited correctly in
       desktop Chrome and not on iPhones: iOS Safari declines to blend
       across the GPU-composited rhythm canvas, so the white ground the
       multiply existed to dissolve was simply drawn — a white rectangle
       on every phone the founder looked at, on a page whose whole first
       impression is the hero. Every check we had was green: the CSS was
       right, the asset's ground was white, and the rendered composite
       agreed with multiply's arithmetic **in the browser the probe
       runs**. That is the shape of this one — a correct implementation
       of a technique one engine does not support where it matters.
     * **The resolution.** The PM re-cut the asset with true alpha
       (md5 c3bc1b013d5c1147f52a8e2c0b99a814, 92,278 bytes): background
       fully transparent, the soft shadow preserved as real
       semi-transparent pixels, the arch under the handle an open window.
       `mix-blend-mode` is gone from `kettle-mark.css` and the pin that
       required it is replaced by one that REFUSES a blend mode — it
       would be a browser-specific bug written back in. The mark now
       depends on no compositing behaviour at all: where the drawing is
       empty, nothing is drawn.
     * **The probe follows the mark.** The asset check reads ALPHA now
       (corners at 0–2 of 255) and finds the handle window rather than
       trusting a coordinate: 90,460 enclosed transparent pixels, widest
       span 429px, so a re-export that fills the arch fails instead of
       quietly gaining a lump of paper. The rendered-composite check is
       unchanged in shape and stricter in fact — same screenshots, same
       samples, expected value now simply "the page as it is with no mark
       there": **237 empty samples, worst departure 0 of 255**.
     * **The stacking-context pin stays** (189), with its why rewritten:
       the blend exposed it, but the layering it protects outlived the
       blend — steam over drawing, drawing over the hero's wash and
       canvas.
     * **Weight:** 92KB against the flattened 60KB, inside the existing
       1KB–120KB bound, so nothing else needed changing. The bound is the
       promise that justifies loading the mark eagerly above the fold;
       it is inherited here rather than remade, and noted in the test.
     * **Composition, all widths.** Hero padding halved (`py-28` → `py-14`,
       `md:py-36` → `md:py-20`); kettle, kicker and headline moved into
       one lockup on a 14px gap while the page's larger rhythm resumes
       below the headline; the mark is 96px on a phone and 140px from the
       `md` breakpoint up. Measured: at 1440px the headline's top edge
       moved from **391px to 297px** — 94px higher than before this pass.
       At 390×844 the whole promise now lands in the first viewport with
       **139px to spare below the CTA**, against 20px before. The mobile
       fallback the order authorised (hide the mark below 640px) was NOT
       needed and was not built.
     * **Reading recorded:** the order names only the mark→kicker gap, but
       "the larger gap rhythm resumes below the headline" only means
       something if the kicker→headline gap tightened too, so both are
       14px and the kettle/kicker/headline read as one lockup. Say the
       word if the kicker should keep its 32px from the headline.
     * **Three probe corrections, each of which had made a check lie.**
       (1) The ground mask now requires alpha exactly 0: at alpha 4 the
       drawing is invisible to a person and still darkens the page by 4
       levels, which is the size of the departure being looked for.
       (2) The paint-order check forces greyscale anti-aliasing
       (`--disable-lcd-text`): Chromium picks subpixel or greyscale AA by
       what it knows about the backdrop, so hiding a compositing layer
       rewrote every glyph edge by tens of levels and the check read a
       rasterization difference as a layering one. (3) That check no
       longer looks for the field's own dust over the text — the dust is
       sparse and translucent, and a planted canvas-above-copy regression
       passed it. It now forces the canvas opaque in a colour the palette
       does not contain and asks whether the headline survived: 4,562 of
       4,562 ink pixels standing normally, **0 of 4,562** with the
       regression planted.


191. **(2026-08-27, filed 2026-08-28 retroactively, Hema + Claude Code) The
     site Dockerfile makes file permissions unable to break serving.**
     Deployed by Hema on 2026-08-27; filed here after the fact, and the
     guard is now in the repo — see the flag.
     * **What happened.** `kettle-hero.webp` was written by a bridge with
       mode 0600. Nothing downstream corrects a mode: vite copies
       `public/` into `dist/` as-is, Docker `COPY` preserves what it is
       given, and nginx's non-root worker could not read the file — so
       the hero's kettle answered **403** on the live site while every
       other asset served. A broken image on the page's first impression,
       from a mode bit nobody set on purpose and no test could see.
     * **The guard.** `RUN chmod -R a+rX /usr/share/nginx/html`
       immediately after `COPY dist/`. `a+rX` is read for everyone on
       files and traverse on directories, which is what a static document
       root wants in every case; running it after the copy is the whole
       point, since before it the directory is empty.
     * **Both sides added it independently, and they agreed.** Hema had
       already committed the guard (34b5309) when this filing was
       written; the check that said otherwise was made against a local
       `main` that had not been fetched, and the claim that it was
       deployed-but-uncommitted was wrong. The `RUN` line is identical on
       both sides and only the comment differed, so the merge kept one
       comment naming both the cause and the ordering. What this filing
       does add is the test: a positional assertion in
       `product/tests/test_site_caching.py` that the chmod appears AFTER
       the COPY, since a guard that runs first is decorative and reads
       identically in a substring search. Planted both ways (deleted,
       and moved above the COPY) and each fails.
     * **The general shape**, worth naming because it will recur: an
       artifact's *metadata* can be wrong while its bytes are right, and
       every check in this repo reads bytes. The answer is not to check
       modes everywhere but to normalize them at the one door everything
       passes through.

192. **(2026-08-28, Fable + Hema, built by Claude Code) "Ordinary" becomes
     "normal" in email bodies.** Product suite 410 → 414; nothing
     deployed.
     * **Why.** Spec 009 replaced "ordinary" with "normal" in every
       webapp string and deferred the email bodies, which left the
       product saying both words for the same day. Thursday's real
       emails: "a normal morning" at 9:30, "An ordinary day, start to
       finish." that night, one family, one inbox.
     * **The sweep.** One template body carried the word. Verbatim,
       before and after:
       * `digest_evening_normal`
         * BEFORE: `An ordinary day, start to finish. Next note in the morning.`
         * AFTER: `A normal day, start to finish. Next note in the morning.`
       * No other body, subject or fragment in
         `kettle/outbound_templates.py` contained "ordinary" — checked
         across the whole registry under every relationship label, and
         that sweep is now a test rather than a claim. `EMAIL_SUBJECT`,
         `EMAIL_SUBJECT_PARENT` and the other seven bodies are unchanged,
         character for character.
     * **The guard.** "ordinary" joins the outbound copy scan's banned
       vocabulary as `RETIRED_WORDS`, so an email body may no longer use
       the word at all — the same ban the webapp has carried since 009,
       enforced exactly as hard. Planted with the exact string that
       shipped Thursday night, and with the word in a fresh sentence;
       both fail. The body also gained the verbatim pin it never had,
       which is how the word sat here disagreeing with every webapp
       string for a whole spec without anything noticing.
     * **Comments swept too.** Two comments in `kettle/outbound.py` and
       three test docstrings quoted the retired body. They are not copy,
       but a comment quoting retired copy is how retired copy comes back,
       so they now quote what ships.

193. **(2026-08-28, Hema, ruling) Spec 011 ratified: Wave D rides the
     Twilio WhatsApp sender, and the ask template carries a 👍
     quick-reply button.**
     * Architecture A stands. +1 984-370-4452 registers as a Twilio
       sender; the Wave-C-proven transport keeps working with a changed
       `from` and template Content SIDs. Option B (Meta Cloud API
       direct) is declined; the revisit trigger (~10k msgs/mo) stays as
       recorded in spec 011 §1.
     * The ask template gets a single quick-reply button whose text is,
       verbatim: `👍`. Tapping sends the button text as an ordinary
       inbound message, which the existing parser already accepts; a
       typed 👍 keeps working unchanged. Elder-proof both ways.
     * Effect: spec 011 unblocks. Next action is Phase 0 — Hema in the
       Twilio console, connecting the number via embedded Meta signup
       against the WABA holding the approved name "HeyKettle". Nothing
       builds before the templates phase per the spec.


194. **(2026-08-28, Claude Code, spec 011 Phase 1) FLAG — the ladder's
     timing audit: which rungs can fire outside a 24-hour service
     window.** Nothing built and nothing changed; this is the
     enumeration §3 asks for before Phase 2 begins. Sandbox behaviour
     untouched.
     * **The answer is one rung: the ask.** `ask_parent` is the ONLY
       message Kettle sends to a parent, and therefore the only one the
       WhatsApp window rule can reach. The WhatsApp transport declares
       `kinds = (KIND_ASK,)`; every other template in the registry is
       `audience="child"` and rides the Resend email transport, where a
       24-hour window is not a concept. So the template requirement
       covers `ask_parent` and nothing else today.
     * **The ask's clock.** Parent-local: window opens 06:00, morning
       digest 08:30 (email), **ask 11:00 (WhatsApp)**, follow-on at the
       ask + 2h grace (email), evening digest 20:30 (email), all-clear
       whenever the first alarm-grade ping lands after a sent follow-on
       (email).
     * **Can the ask ever be inside a window?** Sometimes, and never
       dependably — which is why it must be a template regardless. The
       window would have to have been opened by the previous day's
       reply: yesterday's ask fires at 11:00 local, a reply arrives
       after it, and today's ask fires at 11:00 local, so the reply is
       less than 24 hours old and today's ask lands inside. That case
       needs quiet mornings two days running AND a reply on the first,
       and it evaporates whenever the parent did not reply, whenever a
       day is skipped, and whenever the local clock shifts (spec 010's
       moves, or DST) so that "24 hours later" is not "11:00 again". The
       first ask a parent ever receives is always outside a window.
       Sending a template inside a window is always permitted, so the
       template is correct in both cases.
     * **Nothing rides inside a window today, at all.** A reply cancels
       the pending follow-on and Kettle answers the parent with
       *nothing* — `record_parent_reply` stores the match and is silent
       by design. So §3's "rungs inside a window stay free-form,
       unchanged" currently governs the empty set. Worth saying plainly
       because it means the ask template is the only parent-facing copy
       in the product, with no free-form path behind it.
     * **Two traps this audit exists to catch, both cheap to fall into
       later.** (1) The transport roster maps kinds to carriers by
       CONFIG: routing any child-facing kind to WhatsApp is a config
       change, not a code change, and the moment one is, those rungs
       become business-initiated too and need their own templates. The
       follow-on is the likely candidate the first time a family member
       prefers WhatsApp to email. (2) If the ladder ever acknowledges a
       reply — a "thanks", an all-clear to the parent rather than the
       child — that message would be the first thing Kettle has ever
       sent inside a window, and it is the one case where free-form is
       genuinely available. Neither is in scope for Wave D; both should
       come back to this entry when they are proposed.
     * **The ask copy was verified for Phase 1 in the same pass** and
       matches DECISIONS 151 item 4 character for character, 53
       codepoints, with the emoji as bare U+1F44D. The submission text
       for the PM is `docs/whatsapp-ask-template-submission.md`; the
       one difference found is the site's shorter illustrative quote
       (`OFF_NOTIF`), which DECISIONS 150 already ruled non-binding and
       which must not be the string submitted.

195. **(2026-08-29, Hema, ruling) Copy law amendment for the SEO/content
     library: two registers.** Ratified after the planner/resource
     research (docs/adult_children_aging_parent_resource_research.md,
     docs/aging_in_place_free_resources_strategy.md) exposed the
     tension between search vocabulary and Kettle's language laws.
     (Filed first as 194 in an uncommitted working tree while Claude
     Code's 194 was already pushed; renumbered here, nothing else
     changed.)
     * **Paper rule.** Anything a parent might see or hold — printable
       interiors, the planner, product surfaces, email bodies — obeys
       the copy laws in full. No monitor/track/alert/elderly/seniors,
       ever, no exceptions. A sheet on a parent's fridge never carries
       a word that describes them as a subject of observation.
     * **Google rule (contrast position).** A web page built to catch a
       search MAY use the searcher's words (e.g. "elderly monitoring")
       but ONLY to name the category being replaced — describing other
       products, never Kettle. Kettle self-description keeps the laws
       everywhere. Shape: name their words, then teach ours.
     * Gating ruling, same sitting: individual printables download
       free, no email required; only the flagship planner bundle asks
       for an email.
     * Standing attribution line for anything drawing on NIA material,
       verbatim: "Content informed by resources from the National
       Institute on Aging." Never rebrand nonprofit PDFs (alz.org,
       Family Caregiver Alliance, Red Cross, NCOA) — research and
       link-out only, unless explicit reuse permission exists.

196. **(2026-08-29, Hema + Fable, spec 011 Phase 0) The real number is
     LIVE as a Twilio sender — with one ruled deviation from §2.**
     Sender +1 984-370-4452 shows Online in Twilio; display name
     HeyKettle; throughput 80 MPS.
     * **The deviation.** §2 said to select the existing WABA in the
       embedded signup. Twilio's own documentation says the opposite —
       a WABA created outside Twilio should not be selected, and the
       popup enforces this by not offering it. Sequence that actually
       happened: (1) Meta's Aug-10 "Account Integrity" restriction on
       the Kettle Labs portfolio was reviewed and LIFTED same-day after
       Hema's identity verification (this alone had blocked the popup
       entirely); (2) the old WABA's number row — added in WhatsApp
       Manager, stuck Unverified because its verification SMS went to
       the Twilio number where no human reads inbox — was deleted by
       Hema (reason given: change of business service providers);
       (3) embedded signup created a NEW WABA "HeyKettle", ID
       1778487076826507, under Kettle Labs, with the number and the
       display name (typed exactly: HeyKettle) submitted in-flow.
     * **What carried and what re-runs.** Business verification lives
       on the portfolio and carried over. The display name approval
       did NOT carry — it was attached to the deleted row — and rides
       Meta's routine review of the new WABA (Commerce Policy check
       within 24h). Watch WhatsApp Manager for the name outcome before
       the dark stage.
     * Meta's "insights" and "order/lead event detection" data-sharing
       options were declined at setup.
     * The old WABA (1963801584280787) is now empty; retire it whenever
       convenient — nothing references it.
     * Phase 1 template submission is now unblocked; the submission
       text was signed off in docs/whatsapp-ask-template-submission.md
       before this entry.

197. **(2026-08-29, Hema, ruling) The ask offers 👍 or silence — no 👎,
     reaffirmed with the reasoning on the record.** Raised by Hema at
     template submission ("how do the parents say no?"), decided the
     same evening: the template ships as-is.
     * "Not okay" is captured by silence: the ask's signal is whether a
       reply comes at all, and no-reply is what the ladder exists for.
     * A 👎 would create an obligation Kettle refuses to fake: alerting
       the child on a tap is a verdict and an emergency channel;
       replying to the parent is chat (killed with Send-a-note);
       honoring it with nothing makes the button a lie. A button we
       cannot honor honestly is worse than no button.
     * **Known edge, watched not fixed:** reply intake is content-blind
       — ANY reply stands the ladder down, including typed distress,
       and Kettle neither answers it nor forwards it. Deliberate
       (Kettle is not a mail carrier between parent and child), and
       recorded in the Day-30 memo as a watched question: if real
       families type distress into the ask thread, revisit with data.
       See also 194's second trap (acknowledging a reply would be
       Kettle's first in-window message ever).

198. **(2026-08-29, PM, Hema to veto) Content library round-2 verdicts.**
     Research report docs/blog-research-round-2.md reviewed in full and
     ACCEPTED. The decisions it asked for:
     * **CFPB Managing Someone Else's Money: LINK, never co-brand.**
       The license forbids content changes, so the booklet can never be
       brought inside the paper rule (195), and Kettle's mark does not
       go on a register we cannot edit.
     * **First build wave (four assets):** #1 okay-living-alone
       checklist ([web] page + [paper] printable), #2 normal-day
       baseline ([paper], the spine — explicitly NOT judged on search
       traffic; flagship/email asset), #3 changes tracker (ships as
       #1's download, no own landing page), and #6 emergency info
       sheet — promoted on evidence: weakest SERP in the set, File of
       Life precedent. First articles: topics 8 (parent doesn't answer
       the phone), 5 (how often to check), 19 (what info to have in an
       emergency). The local-help "who do I call for what" crosswalk
       is wave 2, with a dated "numbers checked" footer REQUIRED and
       every phone number verified on its live official page the day
       the file is generated.
     * **Kill list accepted:** article topics 13/14/15 (vendor-owned
       monitoring SERPs) and 20 (query space owned by child-monitoring
       content) are dead; 4/7/11 merge into 1/3; topic 3 dies as an
       article, survives as a printable.
     * **House print spec adopted (from NIA's senior-friendly print
       guidance, which we already attribute):** type ≥13–14pt (16–18
       for low-vision variants), black on white, no patterned
       backgrounds, 50–65 character lines, left-aligned; US Letter
       with A4-safe margins; every single-sheet asset ships BOTH
       print-only and fillable PDF — the fillable form is the visible
       quality edge nothing in the free field has.
     * Researcher owes five verifications before the writer touches
       the affected items: NIA reuse policy page quoted verbatim, FEMA
       PDF click-verified, 1-800-MEDICARE confirmed on a live page,
       CFPB/AARP guide page counts, OutreachPro links replaced before
       2026-09-14. Writer may start on wave-1 assets that do not
       depend on these.
199. **(2026-08-30, Claude Code, PM-ordered — Asana 1217835128977059;
     filed as 196 in the branch commit and renumbered at merge, since
     196-198 landed concurrently on main) The
     favicon set, derived from the shipping kettle asset.** Site suite
     216 → 223; committed and pushed for PM review, NOT deployed — rides
     the next site batch. Per the pinned scope: every raster is a crop
     and resize of `site/public/kettle-hero.webp` (the true-alpha hero
     drawing), never regenerated artwork, via
     `site/scripts/make-favicons.py` — re-run it and the whole set
     follows the asset. The master crop is the 700px square centred on
     (524, 414), measured from the asset's own alpha channel.
     * **The set:** `favicon.ico` (16/32/48), `favicon-16.png`,
       `favicon-32.png`, `apple-touch-icon.png` (180×180, flattened onto
       the canvas token because iOS renders transparency as black),
       `og-image.png` (1200×630, the kettle alone on the site's ground),
       and `favicon.svg` — the hand-simplified glyph, silhouette only,
       for the sizes the hobnail texture cannot survive. All unhashed
       stable names under the DECISIONS 112 revalidate rule.
     * **16px legibility, checked as a screenshot rather than an
       assertion (the order's own instruction).** At a real 16 device
       pixels the raster reads as a kettle — belly, spout, handle arc,
       and the copper knob survives as a warm pixel — on light and dark
       tab bars both; the hobnail becomes texture and costs nothing.
       The FIRST draft of the svg glyph failed this check (it read as a
       blob: a 1.3px anti-aliased handle stroke vanishes) and was
       redrawn heavier before shipping; screenshots of both renders went
       to the founder. The check caught a real one.
     * **Head wiring:** ico + svg + png-32 icons, apple-touch-icon, and
       `og:image` with type/width/height. The og URL is absolute at the
       canonical origin, pinned equal to the canonical link's own by
       test. **Deliberately NO og:title/og:description/twitter tags**:
       scrapers fall back to the existing <title> and meta description,
       so the card adds zero new copy surface — and the card itself
       carries no words for the same reason. privacy.html stays
       icon-free (its no-<link>, no-absolute-URL law, 142) and a test
       holds that too.
     * **Judgement calls, each cheap to overrule:** og-image is PNG, not
       webp (WhatsApp/iMessage scrapers still mishandle webp cards, and
       the tree-side `*.webp` manifest stays a clean six-plus-mark);
       the svg's two colours are sampled from the artwork's own pixels
       (asset pixels like the webp's, not UI tokens — tokens.css cannot
       reach a static file); Pillow is a container tool for the
       generator, not a product dependency — the OUTPUTS are committed
       and the script documents its own invocation.
     * **Five plants, each red then reverted:** a linked icon deleted
       (the silent-404 case the head test exists for), the declared og
       width drifted from the file's real width, a <script> in the svg,
       the ico swapped for a bare png, and the set wired into
       privacy.html.
     * **Refinement on approval (founder): the svg answers the dark tab
       bar.** The first cut was near-invisible there — a dark kettle on
       a dark bar — and the svg is the ONE icon in the set a browser
       re-styles with the bar, so it gained a
       `@media (prefers-color-scheme: dark)` block lifting the
       silhouette to the drawing's own sage highlight (#aebcb0) with
       the knob brightened to match (#d09a5b); light scheme unchanged,
       rasters untouched. Verified as screenshots of real dark-scheme
       renders at 16/32/128 (the arc's presence was double-checked by
       computed style after a small-scale screenshot misread), and the
       dark block is pinned by test so a tidy-up cannot drop it.

200. **(2026-08-30, Hema, ruling) Spec 012 ratified: the journal becomes
     the Memory tab, with Kettle's gentle lines and the family's own
     contacts sheet.** Ratified in-session ~1:40am; filed first as 199
     in an uncommitted tree while Claude Code's favicon 199 was already
     in flight — renumbered here, nothing else changed. Spec at
     specs/012-family-memory.md; builds AFTER Wave D Phase 2 (Wave D
     keeps CC-queue priority).
     * Nav becomes Today / Memory / Family. Tab name: **Memory**.
     * Kettle-authored lines, VERBATIM (whats never hows; no verdicts;
       no escalation events ever — a month that was not clean gets
       nothing at all):
       * city_change (exists): "{Parent}'s city changed to {city}."
       * started: "Kettle's first morning with {Parent}."
       * first_reply: "Heard from {Parent} with a 👍."
       * clean_month: "A normal {month}, start to finish."
     * Empty state, verbatim: "Notes from your family and from Kettle
       live here. The first ones arrive on their own."
     * Contacts card heading, verbatim: "If you can't reach them" —
       family-entered contacts only, tap-to-call, editable; NO
       auto-populated local-services directory, ever (a stale
       emergency number we suggested is worse than a blank line the
       family owns).
     * Photos deferred; multi-account family circle and MCP read
       access remain phase 2/3 per the journal task's standing review;
       caretaker-log features permanently out of this spec's line.
     * Privacy gates before any stranger family: privacy.html names
       family notes and contacts, a deletion path exists, counsel
       pass. Pilot family ships without ceremony.
     * Process law, learned the hard way three counters running:
       DECISIONS numbers are allocated only against a just-pulled
       origin/main, and NOBODY files an entry while another agent has
       an open task that files one — the pushed repo owns the counter;
       local filings renumber, always.

201. **(2026-08-30, Hema, ruling) The site measures itself with server
     logs and Search Console — and nothing else, ever.** Prompted by
     198 judging asset #2 on downloads while nothing counted anything.
     * **Yes: server-side log summaries.** Fly/nginx access logs
       already exist; a small scheduled job summarizes weekly counts
       per path (pages and PDF downloads) and keeps ONLY the counts —
       raw logs age out on the platform's own schedule, and nothing
       is added to what a webserver inherently records. Built by CC
       after Wave D Phase 2; numbers feed the Day-30 memo.
     * **Yes: Google Search Console.** Ownership verified once by Hema
       (DNS record — founder console work); gives impressions,
       queries, and positions for the resources strategy with zero
       page changes. Its data feeds the researcher's future SERP
       passes.
     * **No, as standing law: no client-side analytics of any kind.**
       No scripts, no pixels, no cookies, no fingerprinting, no
       consent banner — the site remains a page that fetches nothing,
       and the standalone-page test keeps enforcing it. A future
       "just add Plausible" is a ruling reversal, not a tweak.


202. **(2026-08-30, Claude Code, PM-ordered) Spec 012 built: Family
     Memory.** Product suite 414 → 424; webapp 147 → 156 (147 was the
     merged baseline after Wave 1). Migrations 0020/0021 are FILES ONLY
     — nothing applied anywhere, nothing deployed; the PM applies
     per-action with Hema's ok. Every ruled string ships character for
     character from DECISIONS 200 and is pinned by test. Judgement
     calls, each flagged for review:
     * **Contacts card placement — CC proposes: top of Memory,
       family-wide.** The spec offered Memory-top or per-parent on
       ParentDetail. Memory-top mirrors the printable (one sheet for
       the household, the block at the top of its page), keeps
       ParentDetail unchanged as §2 requires, and a per-parent split of
       four suggested rows would fragment "their building or front
       desk" across parents who share one. parent_id stays on the
       schema nullable, so a per-parent view later is a filter, not a
       migration. PM may overrule; the card moves in one place.
     * **Idempotency is schema, not memory:** 0020's partial unique
       indexes (once ever per parent for started/first_reply; once per
       parent+month for clean_month, keyed by event_date = the month's
       first day) with ON CONFLICT DO NOTHING. Reruns, restarts, and
       racing schedulers land one row; planted by dropping the conflict
       clause (4 tests fail).
     * **clean_month honesty guards beyond the spec's letter:** "start
       to finish" is a coverage claim, so a month with zero sent
       digests, or one where the parent's first-ever sent digest lands
       after the month's first day, writes nothing. Escalation = a SENT
       follow_on with local_date in the month. Written on the 1st in
       the normal case but keyed to the month — a scheduler asleep on
       the 1st writes it on the 2nd, not never.
     * **first_reply hooks record_parent_reply and is
       transport-agnostic:** it cannot tell sandbox from the real
       number. The spec scopes it to Wave D's real number; in practice
       the once-ever key means the first matched reply after deploy
       writes it. If the PM wants it armed only after the flip, that is
       one config gate to add at Wave D Phase 3.
     * **The phone-as-text exemption:** spec 012 §4 orders
       human-readable numbers shown, which meets DECISIONS 167's
       numbers-in-hrefs-only law head on. Resolution: phone_display
       renders ONLY inside the tel: anchor (E.164 in the href), scoped
       to data-testid="contact-phone"; the copy scan removes that NODE
       and still walks every other digit. A number leaking anywhere
       else fails the scan — planted. E.164 derivation from the typed
       number is mechanical (keep a leading +, drop non-digits), the
       typed form stays the display string verbatim, both stored.
     * **Spec-silent strings, flagged:** the four suggested-label
       placeholders ("A neighbor", "Someone in the family nearby",
       "Their building or front desk", "Their doctor" — the spec's own
       list as strings), and contacts chrome "Add a contact" / "Save" /
       "Remove" / "Edit" / "Name" / "Phone number" / "Anything worth
       knowing". The Memory screen reuses NOTES_SUB as its sub-line
       rather than minting a new sentence.
     * **family_contacts is a reborn name:** 0013 dropped the retired
       ladder's call tree of the same name; 0021's table is a new thing
       doing a different job (the twilio_signature precedent, 163). The
       retirement suite's fresh-schema check narrows to the ladder
       tables with the distinction written down.
     * **Month separators live in the consolidated feed only**; the
       ParentDetail panel is untouched per §2, and the webapp copy scan
       gains one digit allowance shaped "August 2026".
     * **The DECISIONS 201 log-summary job did NOT fit this run** and
       queues: it needs a decision about where the job runs (Fly's log
       retention vs shipping), which is design, not a small commit.


203. **(2026-08-30, Hema + Fable, ruling; gate built by Claude Code) The
     five spec-012 flags ruled, and the one code change they ordered.**
     Product suite 424 → 426.
     * Rulings, as communicated: (1) contacts placement approved as
       proposed — top of Memory, family-wide, nullable parent_id as the
       future filter; (2) the phone-inside-tel-anchor resolution
       approved, the planted scan being the enforcement; (3) first_reply
       gains a CONFIG GATE — the line belongs to the real-number era and
       must not be spent on a sandbox or dark-stage reply; (4) the
       clean_month coverage guards approved; (5) the spec-silent strings
       approved as flagged in 202. 0020 applies before any webapp
       deploy, PM's hand on the migration; the 201 log job queues for
       its own design pass; PM code review precedes any ship.
     * **The gate, built:** `MEMORY_FIRST_REPLY`, default OFF, in
       Settings and .env.example, armed at the Wave D Phase 3 flip. The
       reply webhook passes it into `record_parent_reply` as
       `note_first_reply`; the once-ever schema key is unchanged
       underneath — the gate decides WHEN the first countable reply can
       happen, the schema still guarantees it counts once. Tested both
       ways: default-off holds a matched (ladder-cancelling) reply out
       of the memory entirely, and arming it later makes the NEXT reply
       the first countable one; the config default and the route wiring
       are pinned, and a plant that wires the gate open goes red.


204. **(2026-08-30, PM code review of spec 012; fix by Claude Code)
     `started` checks HISTORY, not just the absence of a journal row.**
     Product suite 426 → 428. Review verdict: PASS with this one required
     fix, everything else approved as built (target-month idempotency
     keying and the gate wiring included).
     * **The defect, correctly caught.** `note_started` fired after every
       sent digest and leaned on 0020's once-ever key alone. That key
       only knows whether the LINE exists, never whether the claim is
       true — so the first engine pass after deploy would have written
       "Kettle's first morning with {parent}." for every parent with
       months of history behind them. A false memory line, and the same
       shape the clean_month coverage guards already refuse: "first
       morning" is a claim about history, so it is checked against
       history.
     * **The fix.** The insert became one statement with a `where not
       exists` over `sent_messages` — no prior SENT digest row for that
       parent — so the check and the write cannot be separated by a
       concurrent pass. The slot being decided right now is excluded by
       `(local_date, kind)` rather than by counting, so a retry of the
       very digest that earned the line still reads as first. The
       once-ever unique index stays underneath as the backstop for two
       schedulers racing the same instant.
     * **Both halves are load-bearing, proven by plant:** removing the
       history check fails 4 tests (the deploy-day case among them);
       removing the ON CONFLICT backstop fails 1. Neither substitutes
       for the other.
     * Tests added per the review: a parent with three weeks of prior
       sent digests earns NO started line on the first pass after deploy
       or on any later day, and a genuinely new parent still earns
       exactly one — including through a re-decided slot.

205. **(2026-08-30, founder + PM at the Twilio and Meta consoles)
     Why the ask template was rejected — twice — and what it actually
     means: Meta forbids emojis in template BUTTONS. The body is fine.
     Founder ruling needed before any resubmission.**
     * **The hunt.** Twilio showed kettle_ask_parent
       (HXe33df5abd629b1c75d7dd64aac0f83e3) Rejected, with no reason on
       any console surface. Meta's WhatsApp Manager for the HeyKettle
       WABA (1778487076826507) shows ZERO templates — every status
       including Rejected, last 90 days — so no Meta human or reviewer
       ever saw it. First theory was sequencing (Phase 1 submitted
       before the sender existed). Founder approved a clean resubmit:
       PM duplicated in console as kettle_ask_parent_v2
       (HX31fd2ac24e80fe365a3f7ca35938caa7), copy verified
       codepoint-identical (body 53 codepoints, bare U+1F44D no VS16,
       button title bare U+1F44D), submitted Utility 12:15:30 EDT with
       the sender Online. It went Received → Rejected in SIX seconds.
       Sequencing theory dead.
     * **The real reason, verbatim, both templates identical** (from the
       console's own approval-request data; Meta's Graph API refuses the
       create synchronously, which is why nothing ever appears in
       WhatsApp Manager):
       `Problem: Failed to create template, Reason: type=OAuthException,
       code=100, subCode=2388060, userMessage=Buttons can't have any
       variables, newlines, emojis, or formatting characters.,
       message=Invalid parameter`
     * **What is and is not on trial.** The ask BODY — "Everything okay
       today? Reply with a 👍 whenever suits." — was never judged and
       is legal (emoji fine in body). The Utility category was never
       judged. Only the quick-reply BUTTON labeled 👍 is illegal, as a
       hard platform rule, not a review outcome. No appeal exists for a
       synchronous API validation.
     * **Founder ruling required (ask copy is 151-sacred; PM does not
       decide this):** the known options are (a) drop the button
       entirely — template becomes plain text, body verbatim unchanged,
       parents type/tap 👍 themselves as the body already invites;
       (b) keep a button with worded text (any word makes the tapped
       reply that WORD, not 👍 — touches first_reply parsing and the
       Memory line "Heard from {Parent} with a 👍."); (c) anything else
       the founder wants. PM recommends (a).
     * **State:** both HX templates are inert (Twilio allows one
       WhatsApp approval request per content resource, ever; their
       submit buttons are disabled; delete or keep as record). Sender
       +19843704452 (HeyKettle) Online on WABA 1778487076826507 — the
       infrastructure is healthy and waiting. Phase 2 stays STOPPED
       until a v3 template (per the ruling) shows Approved;
       docs/wave-d-phase-2-handoff.md gate updated accordingly.
     * **Ruling delivered same sitting: (a) — drop the button.** The
       ask body stays verbatim; the template becomes plain text;
       parents type or tap 👍 themselves, exactly as the body invites.
       No downstream change: first_reply parsing and the Memory line
       already key on the 👍 in the REPLY, which is unchanged.
     * **v3 created and submitted by PM (founder watching), same
       console session:** kettle_ask_parent_v3, Content SID
       **HXee3060b2784a551bffda9d12dbb07b86**, type twilio/text, NO
       buttons, language en, body verified codepoint-identical again
       (53 codepoints, bare U+1F44D), submitted Utility 2026-08-30
       12:24:44 EDT. It survived the synchronous validation that
       killed v1/v2 and — confirmed in WhatsApp Manager — now sits on
       the HeyKettle WABA as **In review** (Meta-side name carries a
       Twilio SID suffix: kettle_ask_parent_v3_hxee30…; code always
       uses the Content SID, so the suffix is cosmetic). This is the
       first genuine Meta review of the ask. The Phase 2 gate now
       waits on THIS template showing Approved.
     * Watch item: Twilio banner "Finish compliance for 1 number and
       sender" on the Senders page — likely routine number compliance;
       founder to glance on a future console visit.

206. **(2026-08-30, founder) The ask copy is reworded: "whenever
     suits" becomes "when you're free". v4 submitted; v3 stays in
     review as fallback.**
     * Founder's reasoning: "suits" can be hard to understand for
       some readers; "when you're free" says the same thing in
       plainer words. PM concurred — "whenever suits" was the one
       phrase in the ask with a British/Indian English flavor; the
       replacement keeps the same no-pressure register and stays
       fully law-clean.
     * **The ruled string, VERBATIM (supersedes the 151/200-era ask
       body wherever the v4 template is the sender):**
       "Everything okay today? Reply with a 👍 when you're free."
       Straight apostrophe U+0027 (as the founder typed it), bare
       U+1F44D, 55 codepoints. 👍-or-silence (197) unchanged; no
       button (205) unchanged.
     * **kettle_ask_parent_v4**, Content SID
       **HXdb4e38c90d0ccc51bbcd264a002d0a8a**, twilio/text, language
       en, category Utility, submitted 2026-08-30 12:39:20 EDT, body
       codepoint-verified before submit. Confirmed In review on the
       HeyKettle WABA alongside v3 — both genuinely with Meta.
     * **Precedence:** v4 is the shipping template. v3 (old wording)
       rides its review purely as fallback — it ships ONLY if v4 is
       rejected and v3 approved, and then only after a fresh founder
       ruling. If both approve, v3 is simply never used (delete at
       leisure). docs/wave-d-phase-2-handoff.md updated to carry v4.

207. **(2026-08-30, ~4pm ET, PM at the Meta console on the scheduled
     check) BOTH ask templates APPROVED — and Meta recategorized both
     Utility → Marketing at approval.**
     * WhatsApp Manager, HeyKettle WABA: kettle_ask_parent_v4 and
       kettle_ask_parent_v3 both show **Active - Quality pending**
       (approved and usable; quality rating accrues with sends). Both
       rows show **category Marketing** with a category-change notice —
       the submissions went in as Utility with allow_category_change
       on, and Meta's review judged an open-ended daily check-in to be
       Marketing. The copy itself passed review untouched.
     * Precedence unchanged (206): **v4 ships** ("when you're free");
       v3 is never used and can be deleted at leisure along with
       v1/v2.
     * **Cost consequence, for the Day-30 memo watch list:** Marketing
       per-message rates are materially higher than Utility (several
       times, US rates; exact current per-message figures to be read
       off Twilio's pricing page before the memo). At one ask per
       parent per day this is still cents per parent per month — not a
       beta blocker, but it belongs in unit economics. Remedy paths if
       ever needed: request recategorization under Account tools →
       Category updates (rarely granted for open-ended check-ins), or
       live with Marketing. Founder's call later; nothing gates on it.
     * **Gate status:** Meta is the authority and says approved, but
       the Phase 2 gate reads "shows Approved in Twilio", and sends go
       through Twilio's view of the template — the PM's Twilio console
       session expired, so the ten-second Twilio glance (v4 page shows
       Approved) is the founder's last box to tick before pasting the
       handoff to CC. Handoff category line updated to Marketing.


208. **(2026-08-30, Claude Code, PM-ordered) Wave D Phase 2 built: the
     ask goes out as the approved template.** Product suite 428 → 439;
     nothing deployed, no family flipped, no secret set — Phase 3 is a
     separate order.
     * **One variable is the whole switch.** `TWILIO_ASK_CONTENT_SID`
       set → the ask sends `ContentSid` (Meta's approved copy, zero
       variables, no `ContentVariables`); unset → the transport sends
       `Body` from the registry, byte-for-byte the request Wave C has
       always made. So the sandbox stays present and functional to the
       Phase 3 sunset, a rollback is emptying one variable, and nothing
       in code branches on category (Marketing per 207) or on which
       number is configured.
     * **No buttons, anywhere.** DECISIONS 205 removed them from the
       template; this build refuses to grow them back on either side.
       A test scans the outgoing form for button/payload/action shapes
       AND every module under `kettle/` for button-parsing vocabulary,
       so neither a send that Meta would refuse nor a reply path that
       only works for taps can appear. A parent's 👍 is an ordinary
       inbound message, which is what intake has always read.
     * **The ask body was updated to the approved v4 wording**
       (DECISIONS 206): "Everything okay today? Reply with a 👍 when
       you're free." — 55 codepoints, bare U+1F44D, straight
       apostrophe, all three pinned. This is a REAL change to the
       sandbox's words, made deliberately: on the real number the words
       come from Meta's template, on the sandbox from the registry, and
       a drift between them would be two different asks wearing one
       voice. Flagged because it is the one place this build changes
       what a parent reads today.
     * **Failure honesty: Twilio's own words, not a table of mine.** A
       refusal carries `code` and `message` verbatim into the detail, so
       the ops_alert and ntfy say "63016; Template is paused due to low
       quality" rather than "HTTP 400". Deliberately NOT a hardcoded
       error-code→meaning map: I cannot verify current Twilio code
       semantics from this container, and passthrough is both more
       honest and more informative on the day Meta pauses the template.
       The parser is defensive — a non-JSON error page, an empty body,
       or JSON of an unexpected shape still produces a failed result and
       an alert rather than an exception on the failure path.
     * **Untouched, and tested to be:** decision core, ledger,
       idempotency, webhook, signature verification, reply matching. The
       engine test proves a refused template send is a 'failed' row
       naming twilio_whatsapp with exactly one alert, and that the slot
       stays retryable — the template comes back, the ask goes.
     * **Four plants, each red then reverted:** a Body riding along with
       the ContentSid (the shape Meta refuses), the SID ignored so the
       real number silently body-sends, the refusal reason dropped back
       to a bare status, and a button payload creeping into the send.
     * **Phase 3 needs, recorded for the dark-stage order:** set
       `TWILIO_WHATSAPP_FROM=whatsapp:+19843704452` and
       `TWILIO_ASK_CONTENT_SID=HXdb4e38c90d0ccc51bbcd264a002d0a8a` as Fly
       secrets, and `MEMORY_FIRST_REPLY=1` when the flip is real
       (DECISIONS 203). No code change is owed at the flip.

209. **(2026-08-31, PM review of Wave D Phase 2) PASS — zero required
     fixes; the sandbox-wording change is ratified as within 206.**
     * Reviewed from pushed main (132c3ee) against spec 011 §4 and the
       194 ladder audit. Verified with own eyes: the transport accepts
       KIND_ASK only, so the ContentSid can never ride a follow-on or
       any family-facing message; unset SID reproduces the Wave C
       request byte-for-byte (test-pinned); the registry ask string is
       codepoint-identical to the 206 ruling (55 cps, bare U+1F44D,
       U+0027 apostrophe); `_refusal` fails loudly on non-JSON;
       the no-button scan covers both the outgoing form and the reply
       vocabulary; counter handled correctly.
     * **Scope ratification:** 206 was filed template-scoped; Claude
       Code applied the reword to the sandbox registry as well so both
       send shapes speak one ask, and flagged it rather than slipping
       it through. Ratified — that is the founder's intent, and the
       flag-not-hide behavior is the process working. Deploy-day
       consequence is exactly one: sandbox parents read "when you're
       free" from the next product deploy.
     * Next: founder deploys product (no secrets set — wording-only
       change), then Phase 3 per docs/wave-d-dark-stage-runbook.md,
       founder at the console, PM checking each step.

210. **(2026-08-31, founder, dark-stage pre-flight) Isolation accepted
     with eyes open; runbook corrected to the approved template; the
     missing precondition found before it could bite.**
     * **Isolation ruling:** the two Fly secrets are GLOBAL — setting
       them moves every family's ask to the real number; there is no
       per-family routing. Founder ruled: accept and keep the dark
       stage SHORT rather than build routing first. Measured exposure
       at ruling time: Appa 0 asks in 14 days, Amma 1 — and a leak
       arrives as the approved copy from "HeyKettle", i.e. the flip
       early for one message, watched not feared.
     * **Precondition was NOT met and is now a checked step:** both
       Rehearsal parents had NO whatsapp_e164 (or phone) on file —
       the runbook's "numbers point at Hema's own WhatsApp" was
       assumed, false, and would have made the first pass silently
       undeliverable. Hema sets TestMom's whatsapp_e164 to his own
       number before the secrets; reply-matching keys on the same
       column, so both directions need it.
     * **Runbook corrected for 205/206:** expected copy is now the v4
       wording; a BUTTON appearing is itself a stop signal; reply
       pass one is a typed 👍; pass two is a REACTION 👍 — with no
       button, the likeliest real-parent behavior — and its outcome
       is a finding for the flip decision either way (a reaction may
       never reach the webhook: the content-blind reply edge made
       concrete).
     * Flip-day flag MEMORY_FIRST_REPLY=1 stays OUT of the dark
       stage; only the two Twilio secrets are set now.

211. **(2026-08-31, founder) Four small rulings: the metrics email,
     and Memory v1.1's two open strings/defaults.**
     * **Weekly metrics email (201 design): Monday 9:00am ET**,
       founder-only, plain text, server counts only. **Search Console
       stays a separate console visit** — no manual-paste chore rides
       the email. Design: docs/log-summary-job-design.md (option C,
       count-at-the-edge; storage budget on file — ~2 MB/year against
       the free tier).
     * **Memory v1.1 default filter view: All parents × 3 months**,
       All-time one tap away.
     * **The contacts tab's label, VERBATIM: "Who to call"** — plain
       speech, the same language the topic-8 article already uses;
       the page keeps the DECISIONS-200 verbatim heading "If you
       can't reach them". Spec 012 §9 updated with both rulings.
     * Sequencing: CC builds the log-summary job FIRST (self-
       contained; the dark stage needs no deploys, so the build sits
       in the repo until PM review and a post-Wave-D deploy). Memory
       v1.1 queues behind it.

212. **(2026-08-31, Claude Code, PM-ordered) The weekly log-summary job is
     built: option C, per docs/log-summary-job-design.md, with 201 and 211
     governing.** Product suite 486 → 555. Nothing deployed, no secret set,
     no family touched, migration 0022 is a FILE ONLY. Five judgement calls
     and one repo finding, each flagged rather than quietly adjusted:

     * **FLAG 1 — the design's premise was wrong: nginx was not logging at
       all.** The doc says "nginx in the site container currently logs to
       stdout" and has the sidecar tail that stream. It does not:
       `site/nginx.conf` carried `access_log off` in BOTH server blocks, so
       there was nothing to tail and option C could not be built as written.
       Turning a log on is exactly the kind of change 201 is suspicious of, so
       it was turned on in the narrowest form that can exist: a custom
       `log_format kettle_counts` defined by SUBTRACTION from nginx's
       `combined` — no `$remote_addr`, no `$http_user_agent`, no
       `$http_referer`, and `$uri` rather than `$request` so no query string
       rides along. Three fields: timestamp, status, path. This is STRONGER
       than the design, which assumed IPs and user agents would be in the
       stream and would "die in-memory within the day" — there is now no
       address in the process to leak even by accident. The redirect-only
       server block keeps `access_log off`. **PM should confirm the reading of
       201** that a three-field ephemeral stream is a log the site may write.

     * **FLAG 2 — `auto_stop_machines` breaks a daily flush, so the flush is
       periodic and the upsert keeps a high-water mark.** The design has the
       counter flush daily, the endpoint upsert per date+path, and accepts
       that "a restart loses at most a partial day". But `site/fly.toml` sets
       `auto_stop_machines = 'stop'` with `min_machines_running = 0`: the site
       machine stops whenever it is idle, many times a day. A counter that
       flushed only at midnight would almost never reach one, and under a
       last-write-wins upsert the post-restart process — counting up from zero
       again — would ERASE the morning it never saw. Both changed together:
       the counter ships the day's RUNNING TOTAL every SITE_METRICS_INTERVAL_S
       (default 300s) plus once on SIGTERM, and the upsert is
       `greatest(existing, incoming)`. Re-POSTing an identical body still
       changes nothing, which is the idempotency the design asked for and the
       test it named; what a restart costs is only the requests during the
       gap, which is the partial day the design already accepts and the email
       footer states out loud. Pinned by test in both directions.

     * **FLAG 3 — a second table the design did not name.**
       `site_weekly_sends (week_start primary key)`. The ops loop runs every
       minute and the Monday window is an hour wide, so without a durable
       once-only key the founder gets sixty copies of the same note. The
       insert IS the lock. `site_daily_counts` is exactly as specified: date,
       path, count, nothing else.

     * **FLAG 4 — the status class is folded away at the counter.** The design
       has the counter hold `{date, path, status-class}` in memory but gives
       the table no column to put a class in, and "three fields, and they are
       literally three" argues against adding one. Resolved at the edge: 2xx
       and 304 count as served (a 304 is a returning reader), everything else
       is not a view of the thing and is dropped. Redirects, 404s and errors
       never appear.

     * **FLAG 5 — the family copy law cannot bind this email verbatim.** The
       order said "copy scan on every string in the email", and the scan in
       `test_outbound_copy.py` bans "count", "counts", "average" and "server"
       among others — which would forbid a founder note about server counts
       from existing at all. `test_site_metrics_copy.py` holds the founder-ops
       subset instead: no medical or decline vocabulary, no urgency, no
       verdict about a person, no person in it AT ALL, no em dash, no gendered
       pronoun, and nothing that could identify anyone. Six plants prove the
       scanner goes red. Recorded here so it reads as a ruling rather than an
       exemption someone took quietly.

     * **FLAG 6 — two pre-existing failures on main; one fixed, one left.**
       (a) `test_family_memory.py` pinned `Path("kettle/main.py")` relative to
       the working directory. CI runs `pytest` from the repo root, where that
       raised FileNotFoundError instead of checking anything — the source pin
       was inert in CI. Anchored to the test file; it is load-bearing now.
       (b) `ruff check .` reports 25 errors in `tools/printables/`, all
       pre-existing on a clean main and untouched by this pass. NOT fixed:
       that tooling generates the shipped PDFs, and a lint sweep there is its
       own pass with its own re-render check. CI stays red on lint until
       someone takes it.

     Two placements worth recording. The weekly send rides the HEARTBEAT loop,
     not the outbound one: both are "the existing scheduler", but the outbound
     loop is gated behind OUTBOUND_ENABLED, the kill switch on family sending,
     and a founder-only ops note must not be silenced by the switch that stops
     messages to families nor revived by the one that starts them — the
     heartbeat loop is already the founder-only channel. And the send does not
     go through `ResendTransport`: that class is the family channel (template
     registry, child-facing kinds, multipart HTML), and keeping this out of it
     makes law #3 structural rather than careful.

     Secrets, unset, for the founder at deploy (the Wave D pattern):
     `SITE_METRICS_TOKEN` on BOTH apps, `SITE_METRICS_EMAIL` on kettle-api,
     `SITE_METRICS_ENDPOINT` on kettle-site. Deploy is a separate founder step
     after PM review, post-Wave-D.

213. **(2026-08-31, PM review of the log-summary build) PASS — all
     three PM-decision flags ratified; counts are floors, not exacts,
     and that is on the record.**
     * Verified in the tree: three-field log format to stdout only
       (no IP/UA/referrer/query anywhere in the stream — the privacy
       guarantee made by the FORMAT, stronger than the design's
       premise, which had assumed logs existed at all); migration
       0022 counts-only with RLS on and no family grants (the table
       is invisible to family sessions); endpoint 404-unconfigured /
       401-bad-token with constant-time compare; greatest() upsert;
       site_weekly_sends claims the Monday send atomically; empty
       week says "Nothing was counted this week." rather than
       imitating data; drain-first sidecar degrades to a pass-through
       pipe rather than taking nginx down.
     * **Ratified:** (1) the three-field ephemeral stream reads as
       within 201 — a request line is still never remembered, a count
       of them now survives, which is what 201 permits; founder may
       veto on sight of this entry. (2) Periodic flush + greatest():
       right for auto-stop machines; noted honestly that a mid-day
       restart keeps the larger partial, so weekly numbers are
       FLOORS — fine for trend reads, never to be quoted as exact.
       (5) The founder-ops copy subset for this email is correct, not
       a loophole: no medical vocabulary, no urgency, no claims about
       any person; the family law's banned words cannot bind an email
       whose subject IS counts.
     * Also noted with credit: the pre-existing CI red
       (test_family_memory's cwd-relative source pin) found and fixed
       in its own commit; tools/printables ruff debt correctly left
       for a pass with its own re-render check.
     * **Deploy plan — HELD until after dark-stage pass 1** (a
       product deploy restarts kettle-api; the rehearsal is not to be
       disturbed for a metrics job). Then, founder: apply 0022 via
       Supabase Studio; set SITE_METRICS_TOKEN (same string, both
       apps), SITE_METRICS_EMAIL (kettle-api), SITE_METRICS_ENDPOINT
       (kettle-site); deploy product then site. First email lands the
       Monday after.

214. **(2026-08-31, Claude Code, PM-ordered) Memory v1.1 built: spec 012 §9,
     all four items.** Webapp 158 → 180; product 555 → 559 (the four new ones
     are RLS). Nothing deployed. Five flags, one of which changes what the
     pass contains:

     * **FLAG 1 — 9.3(i)'s migration was already shipped, so there is NO new
       migration in this pass.** The order and the spec both call for
       `family_contacts` to GAIN a nullable `parent_id` FK and a `rank`, with
       RLS mirroring 0021. Reading 0021 rather than assuming: it already has
       `parent_id uuid references parents(id)` (nullable), already has insert
       AND update policies checking that the parent belongs to the same
       family, and already has `position integer not null default 0`, which is
       the rank under a different name. The read surface in
       `webapp/src/lib/queries.ts` already selects both columns. What was
       missing was entirely in the app: `addContact` hardcoded
       `parent_id: null` and nothing ever wrote or read `position`. So the
       schema work for 9.3 is zero and the pass is webapp-only there. **PM
       call wanted:** rename `position` to `rank` for vocabulary alignment
       with the spec? Recommendation is NO — the column works, the app and the
       read surface already speak `position`, and a rename is churn with
       deploy risk for a word. Filed rather than done either way.

     * **FLAG 2 — the timeframe chips print the only bare numerals in the
       app.** "3 months" and "6 months" are the spec's own words, and the copy
       law's digit ban (`strayDigits`, DECISIONS 167) allows digits only
       inside a clock time or an ISO date, so those two strings would fail the
       scan. The ban exists so a PHONE NUMBER can never reach the screen as
       text, which a filter chip is not. Resolved the way every other
       legitimate numeral here is resolved — a narrow named pattern in the
       scan (`TIMEFRAME_DIGITS = /\b[36] months\b/`), pinned by a test to
       exactly those two copy keys, with a plant proving a widened pattern
       goes red and that the exemption does not swallow a phone number, a
       count, or a bare year. Spelling them ("Three months", "Six months")
       would need no exemption at all and is a one-line change if the PM
       prefers it; only "Who to call" was marked VERBATIM, so these were read
       as descriptive.

     * **FLAG 3 — the contacts card had to lose its own heading.** Moving the
       section to its own tab put the DECISIONS-200 line "If you can't reach
       them" on the page AND in the card, which is exactly the duplication
       9.4 exists to remove, one section down. The card's `<h3>` is gone and
       the page keeps the heading. Caught by a test failure, not by reading.

     * **FLAG 4 — spec-silent strings, each flagged as written.** The parent
       chip "All"; the two chip-group labels "Show notes about" and "Show
       notes from"; the per-contact tag control "Who this is for" with
       "Everyone" for an untagged row; "Move up" / "Move down". Also
       `FILTER_EMPTY` — "Nothing in this stretch. Try a longer one." — which
       the spec does not name at all but the build needs: a family that
       filters past its own history must not be told the ruled MEMORY_EMPTY
       line about first notes arriving on their own, because with a year of
       notes on file that sentence is false. Two silences, two sentences.

     * **FLAG 5 — a date bug found while testing, fixed.** Six months back
       from August 30th asks `Date.UTC` for February 30th, which overflows to
       March 2nd and silently excludes two days from a window the family
       believes is six months wide. The day is now clamped to the target
       month's length. "This month" is the calendar month, not a rolling
       thirty days — on the 2nd a family filtering to this month wants the
       1st.

     Two build decisions worth recording. A household contact (`parent_id`
     null) shows under EVERY parent's filter, not just under All: the
     neighbour with a key is who you call about either parent, and hiding that
     row while filtered to one of them would be the list lying about who is
     reachable. And a reorder SWAPS two rows' positions rather than
     renumbering the list, so one move is two writes and never touches a row
     the family did not point at.

     Filtering is client-side, which §9.1 leaves to CC: the journal read is
     already a bounded newest-first window (DECISIONS 160) and the contacts
     read is a handful of rows, so at pilot sizes a server round trip per chip
     tap would cost latency and buy nothing. The RLS posture is unchanged
     either way, as the spec says. Four RLS tests now cover both tables in
     both directions, including the two cross-family tag writes v1.1 makes
     reachable for the first time; seven planted regressions each turned a
     guardrail red before being reverted.

     Sequencing note: spec §9 says "build AFTER Wave D flip + sunset", and the
     order overrode that to build now with deploys held. Nothing here depends
     on the dark stage, so the build sits in the repo behind the same hold as
     the log-summary job (213).

215. **(2026-08-31, PM review of Memory v1.1 + founder string rulings)
     PASS — no-migration finding verified; all five flags settled.**
     * Verified in the tree: 0021 already carried parent_id (nullable
       FK), position, and the same-family insert/update policies — the
       §9.3(i) migration premise was the SPEC's error, found by CC
       reading the schema rather than trusting the spec. Ratified:
       zero DDL, webapp-only deploy. Also verified: the date clamp
       (six months back from Aug 30 no longer lands on March 2), the
       filters keying on parent tag never kind, the composer pinned
       outside the scroll, the removed duplicate heading (9.4's own
       logic one section down), and the household-contact rule (an
       untagged contact shows under every parent's filter — the
       neighbour with a key is who you call about either parent).
     * **PM ratified:** position stays position (rename to rank is
       churn with deploy risk for a word); reorder-by-swap; client-
       side filtering at current data sizes.
     * **Founder ruled:** the two digit chips stay "3 months" /
       "6 months" under CC's narrow tested exemption (the digit ban
       exists so a phone number never renders as text; a filter chip
       is not that, and the plant proves the exemption cannot widen).
       And the spec-silent strings are approved AS WRITTEN, verbatim:
       "All" · "This month" · "3 months" · "6 months" · "Show notes
       about" · "Show notes from" · "Who this is for" · "Everyone" ·
       "Move up" · "Move down" · and the filtered-empty line
       "Nothing in this stretch. Try a longer one."
     * Deploy: webapp-only, HELD behind the same dark-stage hold as
       the log-summary job. After the hold clears: `cd webapp && fly
       deploy` — no DDL, no secrets for this one.

216. **(2026-09-01, dark-stage pass 1 — founder + PM) The real-number
     ask CANNOT reach a US phone as built: Meta blocks every
     Marketing-category template to +1 numbers. Rolled back to the
     sandbox the same hour; 207's "cost footnote" is corrected here.**
     * **What happened.** TestMom's quiet-morning ask fired at 11:00:35
       ET on the real number, as the approved template, with the exact
       v4 body — Twilio Sent at 11:00:38, then **Undelivered at
       11:00:42, error 63049** ("Meta chose not to deliver this
       WhatsApp marketing message"; read from the console's own
       message record, MM0c325ee8913760aa68122f7b73bfba9c). Nothing
       reached the founder's phone.
     * **Why, structurally.** Since 2025-04-01 Meta blocks ALL
       marketing-category templates to US (+1) numbers, no exceptions,
       no lift date; Twilio's own guidance is "use SMS". Meta
       recategorized our ask Utility → Marketing at approval (207).
       Therefore the v4 template is undeliverable to every US parent
       — Amma in Austin, every US beta family — and deliverable only
       outside the US (Appa), subject there to Meta's per-user
       marketing caps. **Correction to 207:** the recategorization was
       recorded as a pricing footnote, not a blocker. For the US it is
       a wall. PM's miss; the dark stage did its job.
     * **Rollback, done 12:3x pm ET:** TWILIO_ASK_CONTENT_SID unset,
       TWILIO_WHATSAPP_FROM restored to whatsapp:+14155238886 (the
       sandbox). Discovered while writing the rollback: unsetting
       TWILIO_WHATSAPP_FROM outright would have failed the app closed
       at startup — the runbook now says so. Real family unaffected
       throughout: Amma's asks_14d = 1 and no real ask fired during the
       ~20 hours the real number was live; the only casualties were
       two rehearsal sends (63015 Sun, 63049 Tue).
     * **Founder ruling on the path (same sitting): A first, B in
       parallel.** (A) Win a UTILITY approval: reframe the ask as the
       agreed-upon service the parent opted into, submit with
       category-change DISALLOWED so Meta rejects rather than silently
       recategorizes — a clean verdict per attempt, minutes each. New
       wording is 151-sacred copy: founder rules each candidate
       verbatim. (B) SMS for +1 parents: spec 011 amendment (per-parent
       channel: SMS for US, WhatsApp elsewhere), inbound-SMS reply
       path, and US A2P 10DLC registration for +19843704452 (very
       likely what Twilio's "Finish compliance for 1 number and sender"
       banner is). Start the paperwork regardless of A's outcome.
     * Wave D flip is OFF the table until a template delivers to a US
       number in a dark-stage pass. Sandbox stays the production path.
       Today's ledger row for TestMom's ask reads 'sent' and its
       follow-on will fire on the clock — expected, harmless
       (Rehearsal family), recorded as evidence.

217. **(2026-09-01, founder) The ask is reworded again, this time for a
     UTILITY approval: it now names who asked. Verbatim, with one
     variable.**
     * **The ruled body, VERBATIM:**
       "{{1}} asked Kettle to check in with you when a morning looks
       different. Is everything okay? Reply with a 👍 when you're free."
       Bare U+1F44D, straight apostrophe. {{1}} = the FIRST NAME of the
       family member who set Kettle up (first word of the owner's
       display name); if missing, empty, or not a real name, the
       fallback is exactly "Your family" — the sentence was chosen so
       the fallback reads whole ("Your family asked Kettle to check in
       with you…"). "Check in with", Kettle as actor, is the pinned
       phrasing (DECISIONS record); "heard from / checked in" laws
       unchanged. 👍-or-silence (197) unchanged; no button (205)
       unchanged.
     * **Founder's reasoning, kept on record:** plain English for every
       mood and background — "Today it does." was a writer's beat, not
       how a person texts their mother; the direct question comes
       back because that is how people talk. PM concurred.
     * **Why the shape:** Meta's Utility category means a specific,
       agreed-upon service update. The first sentence IS that anchor;
       the earlier body was only the question, hence Marketing (207)
       and the US block (216). Submit as UTILITY with
       allow_category_change=FALSE so Meta rejects rather than
       recategorizes — a clean verdict. Console cannot set that flag;
       the Content API can, so CC writes the submission script and the
       founder runs it with his credentials.
     * **Both paths, one ask:** the sandbox registry body changes to
       the same words with the name rendered in, so a sandbox parent
       and a real-number parent read the identical message (the 209
       principle). The variable rides ContentVariables on the template
       path; zero buttons still.
     * Sequencing: sandbox remains production. If v5 approves as
       Utility, the dark stage restarts from step 1 with the same
       rehearsal setup; if Meta rejects it, the next candidate is the
       founder's call and Option B (SMS for +1, 10DLC) is already in
       motion.

218. **(2026-09-01, Claude Code, PM-ordered) The v5 Utility attempt is built
     in the repo: submission script, the variable on both send paths, and the
     reworded ask.** Product suite 562 → 570. Nothing submitted, nothing
     deployed, no secret set; the sandbox stays production per 216. Six
     planted regressions each turned a guardrail red before being reverted.
     Four flags:

     * **FLAG 1 — DECISIONS 149 had to be narrowed, and that is worth a
       ruling rather than a quiet edit.** `test_no_template_takes_a_name_or_
       says_one` asserted that every template's variables were a subset of
       `{relationship}`, so 217's `{owner_name}` failed it outright. 149's
       reasoning is about not GUESSING what a monitored parent is called;
       `owner_name` is the self-supplied display name of the family member who
       set Kettle up, addressed TO the parent, and it exists because Meta's
       Utility category requires the message to say who asked for it. So the
       test is renamed `test_no_template_names_the_parent_it_is_about`, the
       allowlist is two names wide with each justified in the docstring, the
       parent-naming ban itself is untouched, and a second assertion pins
       `owner_name` to the ask ALONE so the exception cannot spread to a body
       that is about a parent. **PM should confirm this reading of 149.**

     * **FLAG 2 — the fallback is enforced twice, on purpose.** 217 rules the
       fallback at the point the name is chosen, and `owner_first_name` is
       that point: the engine calls it, so the sandbox body can never render a
       blank. But the TEMPLATE path is the dangerous one — Meta holds the copy,
       so an empty `{{1}}` would deliver "  asked Kettle to check in with you"
       to a real phone before anything here could notice. The transport
       therefore falls back a second time on its own
       (`variables.get("owner_name") or OWNER_FALLBACK`) rather than trusting
       its caller. Belt and braces on the one path where a mistake is invisible
       until after it has been delivered. Both are pinned by test and both
       plants go red.

     * **FLAG 3 — the registry sentence and the submitted sentence are pinned
       to each other by test.** `tools/submit_ask_template.py` is the only
       place the Meta-side string lives in this repo, so
       `test_the_two_paths_say_the_same_sentence` loads the script by path and
       asserts `BODY.replace("{{1}}", "{owner_name}")` equals the registry
       body, along with the name, language, category and the single variable.
       That is the strongest local check available for the 209 principle:
       drift between the two is a difference nobody would see until a parent
       on one channel read a different ask from a parent on the other. A plant
       changing "okay" to "OK" in the script goes red.

     * **FLAG 4 — spec-silent and left alone.** `site/src/copy.ts`'s
       `OFF_NOTIF` still quotes the ORIGINAL ask ("Everything okay today?
       Reply whenever suits."). The registry comment and spec 007 both call
       the site's quote illustrative and not binding, and 217 did not reopen
       it, so it is untouched — but it is now two rewordings behind, and the
       landing page shows it in the notification mockup. Worth a founder
       glance; not changed here.

     * **FLAG 5 — site CI is RED on main, from the images pass, not this one.**
       `site/src/tests/resources.test.tsx` treats every directory under
       `site/public/resources/` as a resource page and asserts each has an
       `index.html`, is on the register, and is in the sitemap. Commit 4c18ed1
       added `public/resources/img/` to hold the four guide thumbnails, so the
       suite now fails five ways on a directory that is an ASSET folder and was
       never meant to be a page. Verified pre-existing by checking out a8d1300
       clean: same five failures, none of them this pass's. NOT fixed here
       because the right fix is a call this pass cannot make — either the
       images move somewhere the scan does not walk, or the scan learns to skip
       a directory with no index.html — and picking wrong would fight whatever
       the image layout was meant to be. Product suite, webapp CI and the site's
       other seventeen files are green.

     Codepoints, pinned in both renderings a parent can actually receive: 124
     with a name ("Priya asked Kettle…"), 130 with the fallback ("Your family
     asked Kettle…"), bare U+1F44D with no variation selector, straight
     apostrophe. The engine's withhold rule for empty variables (DECISIONS
     152) deliberately does NOT fire on a missing owner name — a family that
     never filled in a display name still gets asked, with a sentence that
     reads whole — and a parametrized engine test proves it over the seven
     shapes the ruling calls not-a-name.

     The submission script takes credentials from the environment only, never
     from the repo; uses stdlib urllib so it needs no install; prints the new
     Content SID before submitting, so a founder who loses the terminal still
     has it; and prints Meta's rejection reason VERBATIM, because a
     paraphrased rejection is the one thing the whole attempt was run to
     learn. It is not imported by the app and nothing schedules it.

219. **(2026-09-01, PM review of the v5 build) PASS; the 149 guardrail
     narrowing is ratified; the site CI red gets its ruling.**
     * Verified in the tree: tools/submit_ask_template.py carries the
       217 body byte-for-byte (124 codepoints, bare U+1F44D, straight
       apostrophe), name kettle_ask_parent_v5, category UTILITY,
       allow_category_change=False, one variable sampled "Priya",
       credentials from env only; the registry carries the same words
       with {owner_name}; OWNER_FALLBACK is exactly "Your family";
       ContentVariables ride the template send with no Body. The
       script and the registry are pinned to each other by test.
     * **149 narrowing — ratified.** 149's purpose is that no template
       ever guesses what a parent is called. {owner_name} is the
       self-supplied name of the family member who set Kettle up,
       addressed TO the parent, and Utility classification depends on
       it. The parent-naming ban is untouched; the exception is pinned
       to the ask alone so it cannot spread. Test renamed to say what
       it now checks.
     * **Double fallback — ratified**: the engine resolves the name so
       the sandbox never renders blank, and the transport falls back
       again because the template path is where a blank would reach a
       phone before anything here noticed.
     * **Site CI red on main — PM's own doing, ruled here:** the
       images pass (4c18ed1) put guide thumbnails under
       site/public/resources/img/, and resources.test.tsx rightly
       treats every directory there as a resource page. The fix is to
       MOVE the four thumbnails to site/public/img/guides/ and update
       the four hrefs in resources/index.html — never to loosen the
       scan. Writer task; site deploy waits for it. Also recorded: the
       writer's report claimed the resources assertions passed — its
       replica missed the directory scan; a lesson about replicas.
     * site/src/copy.ts OFF_NOTIF (homepage notification mockup) is
       now two rewordings behind the ask; folded into the homepage
       sweep task (Asana 1217831042637424): it becomes the 217
       sentence with a sample name.
     * **Next: the founder runs the script** (his credentials, his
       shell). Meta's verdict, Approved or Rejected with its verbatim
       reason, is the next ledger entry. Approved as Utility → dark
       stage restarts from step 1 (secrets set again, SID = v5).

220. **(2026-09-01, first run of the v5 script) The content was created;
     the approval POST hit a wrong path; and the premise behind
     allow_category_change turns out to be dead.**
     * Founder ran tools/submit_ask_template.py. Twilio created the
       content resource — SID HX8be9f36a7206df4a6fd9b389ccabf912, body
       printed and matching 217 — then the approval POST returned,
       verbatim: `Twilio said HTTP 405: {"code":20004,"message":"The
       requested resource
       /v1/Content/HX8be9f36a7206df4a6fd9b389ccabf912/ApprovalRequests
       does not support the attempted HTTP method
       POST","more_info":"https://www.twilio.com/docs/errors/20004",
       "status":405}`. Nothing was submitted to Meta; the template
       sits in Twilio unsubmitted.
     * Cause, from Twilio's Content API reference: the submit call is
       `POST /v1/Content/{sid}/ApprovalRequests/whatsapp`; the bare
       `/ApprovalRequests` path is GET-only (status fetch). The script
       used the bare path for both. PM review 219 checked the body,
       category and variable against the ledger and did not check
       the endpoint against the reference; a PM miss, recorded.
     * Larger correction. Twilio's changelog of 2025-04-25 ("Change to
       WhatsApp Category Reclassifications") says Meta discontinued
       allow_category_change: calls carrying it still submit, but it
       "will no longer prevent recategorizations", and Twilio has
       unpublished the field. So the reject-not-recategorize
       mechanism this arc leaned on since 216 (and 217's "submit
       UTILITY with allow_category_change=FALSE so Meta rejects rather
       than recategorizes") does not exist. What stands: Meta decides
       the category from the words; a Utility-worded template stays
       Utility if Meta agrees, and gets moved to Marketing if it does
       not — and a Marketing result is the 63049 wall again. The
       wording (217) is the whole bet; the flag was never a safety
       net. The field stays in the payload (harmless) but the
       docstrings that promise it forces a reject must stop saying so.
     * Ruling: CC fixes the script in three places — (a) submit path
       `/ApprovalRequests/whatsapp`, fetch path unchanged; (b) reuse
       an existing content SID when `KETTLE_CONTENT_SID` is set in the
       env, skipping creation, so the founder submits
       HX8be9f36a7206df4a6fd9b389ccabf912 rather than minting a
       duplicate; (c) the module docstring and submit_for_approval
       comment state the changelog truth above. No product code
       touched. Then the founder reruns with the SID exported. Meta's
       verdict, with its category as approved, is entry 221.
     * The dark-stage precondition from 210 sharpens: before secrets
       are set, PM confirms in the console that the approved template's
       category reads Utility, not just that its status reads Approved.
       Approved-as-Marketing = do not deploy; back to wording.
     * Build note (CC, 21c6a2c, filed here by PM because 220 had not
       reached origin when CC ran): (a) (b) (c) done as ruled; both
       paths of (b) exercised offline with the network stubbed; body,
       name, category, language, variables byte-identical; the
       sentence-pins-registry test still passes; product suite 570
       passed, ruff clean. CC also changed the terminal line from
       "Submitting for WhatsApp approval as UTILITY,
       allow_category_change=false…" to "Submitting for WhatsApp
       approval, requesting UTILITY…" — a fourth edit outside the
       ruling, ratified: the retired promise must not appear on the
       founder's screen at the moment it matters. CC's offer of a
       one-line test that APPROVAL_API ends in "/whatsapp" and
       APPROVAL_FETCH does not is accepted as a follow-on, bundled
       with the next CC touch of the tools/ directory, not a
       round-trip of its own.
     * Next number: 221.

221. **(2026-09-01, v5 submitted) REJECTED before review: Meta forbids a
     variable at the start or end of a template body. A new hard rule;
     the founder picks the opening word.**
     * Second run of the script (KETTLE_CONTENT_SID exported, path fix
       in 21c6a2c): `submitted: received` → within one poll
       `rejected`. Reason, verbatim: `Problem: Failed to create
       template, Reason: type=OAuthException, code=100,
       subCode=2388299, userMessage=Variables can’t be at the start
       or end of the template., message=Invalid parameter`. Record
       shows category UTILITY, allow_category_change false, status
       rejected, name kettle_ask_parent_v5.
     * This is a validation reject, not a review verdict — same class
       as 205's emoji-in-button (code 100). It says nothing yet about
       whether Meta reads the words as Utility. The 217 body begins
       `{{1}} asked Kettle…`, so the rule bites on the first
       character. Hard rule for every future template: the body must
       open and close with fixed text; a variable never sits first
       or last. 217's body is otherwise unchanged and still the
       founder's words.
     * Fix is one opening word before the name; the founder chooses
       (217 law: his register). Candidates offered, each the 217 body
       with only the opening changed; the fallback for a missing
       owner name stays sentence-initial so it needs no case change:
       (a) `Hi. {{1}} asked Kettle to check in with you when a
       morning looks different. Is everything okay? Reply with a 👍
       when you're free.` (b) `Hello. {{1}} asked Kettle…` (same
       tail). (c) `This is Kettle. {{1}} asked us to check in with
       you when a morning looks different. Is everything okay? Reply
       with a 👍 when you're free.` — rejected by PM before offering
       wider: it moves Kettle from the one asked to the one talking,
       which 217 deliberately avoided. PM leans (a): shortest, and
       "Hi." is how a person opens a text. Fallback under (a)/(b):
       `Hi. Your family asked Kettle…` — OWNER_FALLBACK stays exactly
       "Your family".
     * Founder chose (a). v6 body, VERBATIM, this is the ask sentence
       from here on, both paths: `Hi. {{1}} asked Kettle to check in
       with you when a morning looks different. Is everything okay?
       Reply with a 👍 when you're free.` Fallback unchanged: "Your
       family".
     * Route: the founder creates and submits v6 in the Twilio console
       (Content Template Builder, name kettle_ask_parent_v6, English,
       text, one variable sampled "Priya", category Utility). Since
       220 the script's only edge over the console (the flag) is gone,
       so no CC trip gates the submission. Code catches up in one CC
       commit before any deploy: registry sentence and script BODY /
       TEMPLATE_NAME to v6, sentence-pins test, plus the URL assertion
       accepted in 220. Meta's verdict is the next entry. HX8be9…
       stays as the rejected record; delete with v1–v4 later.
     * Submitted 2026-09-01 13:42 EDT from the console: v6 is
       HX61758012edba26686ec7ee361a0f493f; WhatsApp business-initiated
       shows pending (grey), not the instant red of v5 — so the body
       passed validation and is in review.
     * Next number: 222.

222. **(2026-09-01, 13:57 EDT) v6 APPROVED, category UTILITY. The US
     wall is cleared on paper; pass 2 of the dark stage is on.**
     * Read on the template page by PM (console, Hema's session):
       kettle_ask_parent_v6, HX61758012edba26686ec7ee361a0f493f,
       "WhatsApp approval status: Approved", "WhatsApp category:
       Utility", date updated 2026-09-01 13:45:49 EDT — three minutes
       after submission; body on the page is the 221 sentence exactly.
       No recategorization email is expected because none happened;
       if one arrives, it outranks this reading and we stop.
     * What this proves: Meta accepts the 221 words as Utility. What
       it does not prove yet: delivery to a US phone — that is pass 2,
       and the 63049 wall is judged by the message log, not the
       template page.
     * Ruling: dark stage restarts. Runbook gains a "Pass 2 setup"
       block: one `fly secrets set` with both values (FROM real, SID
       v6) from product/, run AFTER the deploy train (a `fly deploy`
       would restart the app anyway; secrets last). TestMom's number
       is already on file; no address SQL. Next ask fires 11:00
       parent-local on the next quiet Rehearsal morning; expected
       screen: "Hi. Hema asked Kettle to check in with you when a
       morning looks different. Is everything okay? Reply with a 👍
       when you're free." from HeyKettle (the owner of Rehearsal is
       Hema; if the first word is not his first name, that is the
       finding).
     * Code catch-up owed before the FLIP, not before pass 2 (the
       template path sends the SID + variables and never reads the
       registry sentence): registry `{owner_name}` sentence and the
       script BODY/TEMPLATE_NAME to v6 words, the sentence-pins test,
       the URL assertion from 220. One CC commit; bundled with the
       next CC task.
     * Next number: 223.

223. **(2026-09-01, ~14:10 EDT) Deploy train shipped; site counter live;
     dark stage pass 2 armed.**
     * Founder: 0022 applied in Studio (whole file, one run); secrets
       set (SITE_METRICS_TOKEN both apps, SITE_METRICS_EMAIL on
       kettle-api, SITE_METRICS_ENDPOINT on kettle-site); product,
       site, webapp deployed in that order. Then, last, the pass 2
       secrets from 222 on kettle-api — one rolling update, succeeded.
     * PM verified live: site_daily_counts and site_weekly_sends exist
       with RLS on, no policies, no anon/authenticated grants; the four
       guide thumbnails render on /resources from /img/guides/ at
       1440×810 and the old path is 404; POST /site-metrics/daily is
       401 without a token and 401 with a wrong one; first counter
       rows landed within ten minutes of the site deploy (day
       2026-09-01: 'other' 23, /blog/ 4, /resources/ 2, / 2, three
       article paths) — option C works end to end, floors as ruled in
       213. First weekly email: Monday 2026-09-07, 9am ET. Founder
       eyeballed Memory v1.1 (filters, scroll, "Who to call") on
       kettle-app.fly.dev and is happy; PM could not reach the webapp
       host from its browser. Note for the record: the webapp is
       served at kettle-app.fly.dev; app.heykettle.com was never set
       up (founder). PM's "/health returns 404" remark was a PM error:
       the route is /healthz and fly.toml checks it.
     * State now: real number + v6 Utility template live for EVERY
       family (210's isolation caveat stands; keep it short). Next
       Rehearsal ask: 11:00 parent-local 2026-09-02, to Hema's phone.
       Expected screen in 222. Verification list = runbook, v6 copy.
     * Next number: 224.

224. **(2026-09-01, ~14:26 EDT) Direct test send: v6 DELIVERED to a US
     number. The 63049 wall is down in practice, not just on paper.**
     * Founder curl'd the Messages API himself (his creds): From the
       real number, To his phone, ContentSid v6, ContentVariables
       {"1":"Hema"}. Twilio accepted (MMe6b76c21c01ce1b975b80e9f4757e8b4,
       18:25:49Z) and the message ARRIVED — screenshots show the exact
       221 body rendered on WhatsApp at 2:25 PM, bubble from
       +1 (984) 370-4452, "Business account", Meta's "secure service"
       banner, no button. First business-initiated WhatsApp ever
       delivered to a US phone in this product's history.
     * Founder replied with a typed 👍. The ledger shows NOTHING for
       it — and that is the DESIGNED behavior, not a failure: a known
       number with no pending ask is recorded as a masked log line
       only (outbound.py record_parent_reply; "un-answering is not a
       thing a late reply can do"). The test send was outside the app,
       so no pending ask existed. Consequence: this test CANNOT prove
       the webhook path; only tomorrow's real ask can (reply → ask row
       marked answered → follow-on cancelled). To rule the webhook in
       or out today, check Twilio Debugger for 11200-class alerts on
       the inbound; no alert + inbound logged = webhook answered.
     * Finding, new: the chat header shows the NUMBER, not
       "HeyKettle". Expectation corrected: recipients who have not
       saved the contact see the number; the display name (and photo,
       once set) lives behind Profile, and name-instead-of-number in
       the header is largely an Official Business Account privilege.
       Runbook step 1 amended in spirit: verify via Profile that the
       name reads heykettle, don't demand it in the header. Work item
       before flip: set the sender's profile (photo, about, website)
       in Twilio's sender page / WhatsApp Manager, and confirm the
       display-name review (In review as of Aug 23) actually approved.
       RESOLVED same hour, from the phone: the profile card reads
       **HeyKettle** (approved, capitalized form — the Aug 23 record
       said "heykettle"), with the description ("HeyKettle sends adult
       children a short daily note about a parent's day. It asks
       nothing of the parent.") and https://heykettle.com already on
       it. Only the photo was missing; founder added one via the
       Twilio sender page (about line "Kettle passes along how the
       morning started.", 44 chars). Rulings: Vertical = Other (never
       Medical/Health, same reasoning as 10DLC); email and address
       stay empty; the photo should eventually be the site's kettle
       mark so the chat avatar matches the site — swap any time, no
       review. Work item closed.
     * Founder judgment on the words, after seeing them on a real
       phone: "when a morning looks different" is writer-speak; wants
       a v7 in plainer speech. His draft: "Hi. Hema asked Kettle to
       check in with you when your morning is not as usual and check
       that you're okay. Reply with a 👍 when you can." PM counter
       (keeps his phrasing, restores the direct question, drops the
       doubled "check"): `Hi. {{1}} asked Kettle to check in with you
       when your morning is not as usual. Is everything okay? Reply
       with a 👍 when you can.` Founder locks the final words; then
       console submit as kettle_ask_parent_v7 (Utility), keep v6 in
       the secret until v7 shows Approved+Utility, then swap the SID.
       The locked words and Meta's verdict are the next entry.
     * Next number: 225.

225. **(2026-09-01, ~15:00 EDT) v7 submitted by the founder and APPROVED
     as Utility in minutes. The ask sentence is final in his register;
     the secret swaps to v7 tonight.**
     * The founder locked the PM counter-wording from 224 by
       submitting it himself. kettle_ask_parent_v7 =
       HX1ebee977bfd531bf7fdee2bf0d1484ad, updated 14:52:47 EDT,
       WhatsApp approval status Approved, category Utility (PM read
       both fields on the template page). Body VERBATIM, now the ask
       sentence on BOTH paths, superseding 221's:
       `Hi. {{1}} asked Kettle to check in with you when your morning
       is not as usual. Is everything okay? Reply with a 👍 when you
       can.` {{1}} = owner first name, fallback exactly "Your family".
     * Ruling: TWILIO_ASK_CONTENT_SID moves from v6 to v7 before
       tomorrow's 11:00 pass (one fly secrets set; founder). v6 stays
       Approved/Utility in Twilio as the proven-delivered fallback —
       it is the template that actually landed on a US phone (224) —
       and is not deleted until v7 has done the same in pass 2.
       Code catch-up (registry sentence, script BODY/TEMPLATE_NAME,
       sentence-pins test, URL assertion) now targets the v7 words.
     * Founder's profile work verified on the phone: the avatar is
       the site's kettle mark (founder had his image agent resize it
       to 640px; PM's "stock teapot" read in 224 was wrong), name
       HeyKettle, description and site link on the card. Meta's Phone
       Profile panel still says display name "In review" even though
       the phone already renders HeyKettle — no action, Meta-side lag;
       watch, don't chase. Same kettle image goes into the Meta
       panel's own Profile picture slot (founder asked; yes — same
       640px file, keeps the two stores consistent; no review cycle).
     * Twilio Alerts read (founder curl): the last three alerts are
       63046 template-APPROVED notices (v6 today; v3 and v4 on Aug
       30 — so v3 cleared review, noted for the delete-later list).
       NO 11200-class webhook failure exists for the 👍 reply window,
       so nothing recorded the webhook failing; full proof of the
       reply path stays with tomorrow's real ask, as 224 said.
     * Next number: 226.

226. **(2026-09-01, ~15:45 EDT) 10DLC root cause found: the Trust Hub
     primary profile is an INDIVIDUAL profile, so the wizard was
     silently registering a Sole Proprietor brand. Submission paused.**
     * PM read the profile page (console, founder's session):
       "projectkettle", Primary profile, type **Individual**, status
       Approved — the founder personally (personal contact details,
       home address), no business section, no EIN field anywhere.
       This explains both symptoms: the morning's "unexpected error"
       (a Standard-brand attempt over a personal profile) and the
       afternoon wizard's missing EIN prompt (it had dropped onto the
       sole-prop track, where none is asked). The review screen's
       "Brand name: LINKABIT AI LABS LLC" was a label the wizard
       never intended to verify against an EIN.
     * Founder decision framed, PM recommends path 1: (1) STANDARD —
       via Twilio support (the support chat already offered an
       agent): convert/replace the primary customer profile with a
       Business profile (LINKABIT AI LABS LLC, type LLC, EIN,
       business address), then rerun the wizard, which will then ask
       for the EIN; brand belongs to the company. (2) SOLE PROP —
       submit as-is: fast, caps sufficient for beta, but registers
       the founder personally, wrong type for an existing LLC, and
       redoing it properly later means re-registration and fees.
       SMS is not on Wave D's critical path (WhatsApp delivers as of
       224), so days of support latency cost nothing.
     * docs/a2p-10dlc-campaign.md status updated across the day
       (blocked → unblocked-but-wrong-track → paused on this
       decision); its campaign samples were also reworded to the v7
       sentence + STOP line so the eventual campaign matches the live
       template.
     * Next number: 227.

227. **(2026-09-01, ~4:45pm EDT) 10DLC brand SUBMITTED, the right way:
     Low Volume Standard for the LLC, off the converted Business
     profile. In review at TCR.**
     * The path out of 226, all founder-executed the same hour: Trust
       Hub's self-serve "Convert to a business profile" (no support
       ticket needed — PM's ticket route was the slower answer);
       conversion approved within the hour; A2P wizard rerun from
       Start then followed the Standard track and inherited the
       Business profile.
     * Two matching lessons that will matter every time a form asks
       for the company: the IRS CP 575 letter carries the legal name
       as **LINKABIT AI LABS** — no "LLC" — and the business address
       zip as **27523**; carrier vetting matches the CP 575, not the
       NC filing, so the brand went in as LINKABIT AI LABS. The
       compliance profile's inherited "…LLC" spelling and an
       inherited linkabitai.com website URL were both corrected on
       the review screen (website → https://heykettle.com, the live
       site that shows what the campaign claims).
     * Submitted as: Low Volume Standard (under 6,000 msgs/day —
       Kettle's volume is a rounding error against that; if we ever
       outgrow it, a new brand then is a good problem), brand
       friendly name HeyKettle, industry Technology, EIN-verified,
       founder as authorized rep. Twilio's fee bills to the account
       balance silently; no checkout step.
     * State: brand IN REVIEW (hours to days; email will say).
       Approved → campaign step unlocks; paste-ready campaign text
       (Account Notifications use case, v7 samples + STOP line) in
       docs/a2p-10dlc-campaign.md. Rejected → verbatim reason to the
       ledger, fix the named field. SMS transport build (spec 011
       amendment) can proceed in parallel regardless.
     * Next number: 228.

228. **(2026-09-01, evening) 10DLC finished end to end: brand APPROVED
     (~3 hours), site grew the two pages carriers require, and the
     campaign is SUBMITTED. The verbal consent script is now canon.**
     * Brand: approved same evening (Low Volume Standard, LINKABIT AI
       LABS). Campaign wizard then demanded what our site lacked: a
       privacy policy containing a mobile-number non-sharing
       statement, message frequency, and "message and data rates may
       apply" — and a terms page. Founder approved PM drafts; shipped
       to the site (privacy.html gains a "Text messages" section,
       dated 2026-09-01; new standalone terms.html in the privacy
       page's fetch-nothing posture; both in sitemap; CI green,
       deployed, committed by founder).
     * Campaign filed as Account Notifications. First submission
       bounced on three automated checks, all wording: description
       didn't read as the use case, description said only "HeyKettle"
       (not the registered brand), and verbal opt-in lacked the
       exact script. Fixes: description now opens "HeyKettle, a
       service operated by LINKABIT AI LABS, sends notifications to
       enrolled members of a HeyKettle family account…"; the consent
       field carries the full script. Resubmit passed initial
       verification; now in TCR review (1–7 business days; monthly
       campaign fee applies).
     * **The setup consent script, VERBATIM (carriers have this
       exact text; the setup flow must say the same):** "Kettle is a
       service from HeyKettle. It sends you a short text when your
       morning is not as usual, to ask if everything is okay. You
       would get at most one question a day, and one reminder if you
       do not reply. Message and data rates may apply. You can reply
       HELP for help, or STOP to end the texts at any time. The
       terms are at heykettle.com/terms.html and the privacy policy
       at heykettle.com/privacy.html. Do you want these texts?
       Please say yes or no." After yes → one enrollment-confirming
       welcome text (option (c) from the campaign doc, now
       ratified by the filing): "HeyKettle: [name] set you up to get
       a short text from Kettle when your morning is not as usual.
       At most one question a day, and one reminder. Message and
       data rates may apply. Reply HELP for help or STOP to end
       these texts. heykettle.com"
     * Other filed values: samples 1–2 = the v7 ask (+ STOP line) in
       named and "Your family" forms; sample 4 = the HELP reply
       ("HeyKettle: a family service. Questions:
       hello@heykettle.com. Reply STOP to end these texts."); opt-in
       keywords blank (defaults START/YES/UNSTOP stand — a STOPped
       parent can text START to resume); embedded links yes, sample
       https://heykettle.com, no shorteners; no phone numbers, no
       lending, no age-gating; opt-in Verbal only.
     * Consequences owed: (a) hello@heykettle.com is now in a
       carrier filing, the HELP reply, and the terms page — the
       forward MUST exist before any SMS sends (founder). (b) Spec
       011 amendment (SMS transport build) now has its consent
       script, welcome text, and STOP semantics fixed by this filing
       — CC builds to THESE strings. (c) The setup flow must present
       the script above at enrollment. Campaign verdict = next
       10DLC entry.
     * Next number: 229.

229. **(2026-09-02, midday) Wave D pass 2 CLEAN: v7 delivered on the real
     number at 11:00:57 ET, and the reply path is proven — after a
     config fix.**
     * Delivery: ask row 11:00:57 ET, transport twilio_whatsapp, body
       v7 verbatim on TestMom's phone at 11:01. No ops_alerts beyond
       the expected noon alert for a dark-stage parent.
     * `{{1}}` rendered as "Your family", NOT "Hema". Correct per 217:
       the Rehearsal owner's member display_name is an email address,
       which `owner_first_name` rejects. So pass 2 proves the FALLBACK
       path only. The runbook's "Hi. Hema asked…" expectation was a PM
       miss (assumed a name never on file). To prove the name path:
       founder sets that member's display_name to "Hema" (Studio DML)
       before the next quiet-morning pass.
     * Reply path: first 👍 (12:27 ET) recorded NOTHING. Cause: the
       real WhatsApp sender's Messaging Endpoint Configuration in the
       Twilio console was entirely empty — no incoming-message webhook.
       The reply path had only ever been wired on the sandbox. Founder
       set incoming webhook = https://kettle-api.fly.dev/outbound/reply
       (POST), fallback/status/messaging-service left empty. Second 👍
       matched: replied_utc 12:33:55 ET. Twilio signature verified
       against PUBLIC_BASE_URL, so that value is confirmed correct.
     * Standing rule (make structural): a sender swap is not done until
       its INBOUND webhook is set and a reply has round-tripped. The
       onboarding/ops runbook's sender-swap checklist gains that line;
       the DB silence on Sep 1's ask (never answered) was this bug,
       not a no-reply.
     * Still owed from this pass: confirm no follow_on row for
       2026-09-02 after the follow-on hour (cancellation proof), then
       reaction-👍 pass next quiet morning, then no-reply ladder pass,
       then flip order (item 4 code catch-up before flip).
     * Next number: 230.

230. **(2026-09-02, 1pm) 10DLC campaign APPROVED. SMS to +1 is now
     carrier-registered. Sending remains gated on spec 011.**
     * Read from the console by PM (Chrome, read-only): A2P Campaign
       CM267f6c7e5b77d9bb9d57c0bc13945c01, status Approved, use case
       Account Notification, brand HeyKettle
       BN17aaa4a756b388a218a9f8437ba6f1dd, last updated Sep 1. Review
       took under a day, not the 1–7 business days quoted.
     * The campaign is bound to Messaging Service
       MG0e9fbf94ad89764c8a6f121f2027675c ("Messaging Service created
       on August 11, 2026"), whose sender pool holds +19843704452
       (Local 10DLC, SMS+MMS). So SMS sends MUST go out via that
       Messaging Service SID (MessagingServiceSid), not a bare From —
       the registration attaches to the service. Spec 011 amendment
       carries this.
     * WhatsApp is unaffected: the WhatsApp sender's endpoint config
       has no Messaging Service selected (229), and must stay that
       way — the service's inbound handling is for SMS STOP/HELP.
     * Not yet verified: the number's SMS "Registration required"
       flag clearing, and the Messaging Service's inbound/opt-out
       settings (console pages 404'd on PM's paths; founder to open
       Messaging Services → the service → Integration and Opt-Out
       and report what they show). Both feed spec 011.
     * Next number: 231.

231. **(2026-09-02, afternoon) Spec 011 Amendment A (SMS transport for
     +1 parents) RATIFIED.** Three founder rulings, rest locked by
     228/230 evidence:
     * SMS ask body = the filed sample, always: v7 + "Reply STOP to
       end these texts." (option (a)). The daily SMS question is the
       only SMS the parent gets besides the one-time welcome.
     * Enrollment of a phone-only parent: setup shows the child the
       228 script verbatim; the control that enrols reads "They said
       yes" and stores `sms_consent_utc`. Ruled NOT a consent ceremony
       (no gate, no extra screen); the 10DLC filing's "consent recorded
       with the parent's record at setup" is this timestamp.
     * Family-facing copy when a parent texts STOP: DEFERRED. v1 =
       founder ops_alert only; opted-out parent gets no ask, hence no
       follow-on.
     * Locked design (see spec A.2–A.10): per-parent routing
       (whatsapp_e164 → WhatsApp; else +1 phone_e164 + consent + not
       opted out → twilio_sms; else recorded skip); payload
       MessagingServiceSid + To + Body, never a bare From; kind
       `sms_welcome` once per parent; inbound on the SAME
       /outbound/reply using Twilio's OptOutType (STOP/START/HELP are
       never replies; body still never read; lookup by phone_e164 when
       From has no whatsapp: prefix); 21610 = opted out; migration
       0023 (parents.sms_consent_utc, sms_opted_out_utc); secret
       TWILIO_MESSAGING_SERVICE_SID; "one reminder" in the script is a
       ceiling, v1 sends the parent none; Phase 4 dark stage on
       TestMom with whatsapp_e164 nulled.
     * Order: Phase 3 flip first, then the item-4 catch-up commit,
       then Amendment A build. Founder console tasks A.8 can run any
       time (service inbound webhook, HELP text, registration flag).
     * Next number: 232.

232. **(2026-09-02, evening) v7 catch-up commit REVIEWED and APPROVED
     (5174f02). Registry, submission script, pins, site copy, runbook
     all on v7 words; nothing touched outside the brief.**
     * Registry body diffed against 225: identical, straight
       characters, "Hi." present. Codepoint pins now 127 (named) /
       133 (fallback). The apostrophe pin lost its positive half
       because v7 has no apostrophe; the negative half (no curly
       apostrophe) stays. Accepted.
     * Site: eight "ordinary"→"normal" swaps, all rendered strings
       including HOW_STRIP_ALT (alt text is read aloud, so it is
       copy). RULED: "An ordinary day." → "A normal day." is the
       correct edit; the article follows the word. Meta description
       and HERO_BODY now say "normal routine". rhythmField's internal
       `mode = "ordinary"` and code comments are not copy; left alone.
     * tools/submit_ask_template.py is a record of what was filed,
       not a submitter: TEMPLATE_NAME v7, BODY v7. New tests pin
       APPROVAL_API ends /ApprovalRequests/whatsapp and APPROVAL_FETCH
       does not.
     * Runbook gained "Sender-swap checklist" (four conditions; step 3
       = one typed reply round-tripped). Structural fix for 229.
     * Process note from CC, on record: plant drills were run without
       a WIP commit and a checkout revert took two finished items with
       it; caught, reapplied, suite re-run on the restored tree.
       The law stands: commit WIP before destructive experiments.
     * Deploy owed (founder): `cd site && npm run ci && fly deploy`;
       `cd product && fly deploy` (registry body only renders when no
       ContentSid is set; deploying keeps prod = HEAD). No secret
       changes.
     * Next number: 233.

233. **(2026-09-02, evening) Twilio SMS console tasks DONE (spec 011
     A.8 items 1–3). Number is registered and the SMS inbound path is
     wired; nothing sends until Amendment A ships.**
     * Messaging Service MG0e9fbf94ad89764c8a6f121f2027675c → Settings
       → Inbound messages: "Send a webhook", request URL
       https://kettle-api.fly.dev/outbound/reply, POST; fallback empty;
       delivery status callback empty. (Was "Defer to sender's webhook"
       with the number's own webhook empty, i.e. inbound SMS went
       nowhere.) PM filled, founder saved.
     * Same service → Opt-out: HELP confirmation message set to the
       filed string verbatim: "HeyKettle: a family service. Questions:
       hello@heykettle.com. Reply STOP to end these texts." STOP and
       START confirmations left at Twilio defaults (not in the filing).
     * Number +1 984 370 4452: Traffic Status "Messaging enabled";
       Messaging configuration = the Aug 11 Messaging Service (service
       settings override the number-level webhook, which is empty and
       may stay so). No "Registration required" flag.
     * Console still shows one "Onboarding task" for the number (A2P,
       last modified Sep 1). With the campaign Approved and traffic
       enabled this reads as a lagging checklist record, like the Meta
       panel's "In review" on the display name. Watch, don't chase; if
       the first SMS dark-stage send fails with a registration error,
       this is the first place to look.
     * Twilio balance $20.00 at time of writing. Top up before real +1
       parents go on SMS (about 3 segments per ask at UCS-2).
     * Next number: 234.

234. **(2026-09-02, evening) Supabase auth custom SMTP was ALREADY
     APPLIED (Resend). PM miss: the plan doc and this ledger said
     "not yet applied"; the dashboard said otherwise.**
     * Seen in the dashboard (founder screenshot): Enable custom SMTP
       ON; sender `Kettle <hello@send.heykettle.com>` (plan said
       sign-in@; hello@ stands, it is verified and friendlier); host
       smtp.resend.com; port 465; username resend; password saved;
       minimum interval per user 60 s. docs/auth-smtp-plan.md status
       line corrected.
     * Test, same evening (founder): signed out of the app, requested
       a sign-in link; arrived 5:41 PM ET from `Kettle
       <hello@send.heykettle.com>` in an Outlook inbox, not spam.
       Custom SMTP is live and delivering. Founder had applied this
       earlier without a ledger entry; this entry is the record.
     * Still open, one screen: Authentication → Rate Limits → email
       sends, raise to 30/hour if still at the default 2 (the August
       429 was the rate limit, not the mailer). Resend tracking on
       send.heykettle.com assumed OFF (digest links have worked);
       confirm at leisure.
     * Lesson for the record: before calling anything a blocker,
       check the live surface, not the plan doc. Same class as the
       checklist-"Complete" miss (228) and the "Hema in {{1}}" miss
       (229).
     * Next number: 235.

235. **(2026-09-02, evening) Spec 013 RATIFIED: sign in with a 6-digit
     email code; the magic link stays in the same email as the second
     path. Pre-beta; starts now.**
     * Why now: it is the one pre-beta item on the board that touches
       nothing the flip depends on, and the phone failure it fixes
       (link opens in the mail app's browser, not the installed app)
       is exactly what a beta family hits on day one.
     * Ruling: BOTH code and link in the email, code first and larger.
       Phones use the code; laptops use the link. No platform
       detection in the app.
     * Strings VERBATIM in spec 013 §3. Button "Email me a code";
       LOGIN_SENT rewritten; new LOGIN_CODE_WRONG; email subject "Your
       Kettle sign-in code". Parents never sign in; unchanged.
     * Founder dashboard: both Supabase email templates (Magic Link
       and Confirm signup) gain {{ .Token }}; text per §3.
     * Order on the board: this ships before the beta invites; Memory
       tab v1.1 (1218017356495916) stays after the flip.
     * Next number: 236.

236. **(2026-09-02, late) Spec 013 built at 2dad423; two build-report
     calls accepted; deploy gated on the founder's template edit.**
     * Webapp 188 tests (8 new), ci green, nothing deployed.
     * Accepted: step 2 stays visible after the first successful send;
       a rate-limited resend shows LOGIN_RATE_LIMITED beside the resend
       link instead of collapsing to step 1. Spec 013 §2 amended.
     * Accepted: sessionRestore.test.tsx mock keys renamed to match the
       data.ts surface; assertions untouched. §5 wording amended so
       "unchanged" means what it asserts, not byte-identical.
     * Bad-code detection is loose on purpose (otp_expired code, or
       "token" + "expired"/"invalid" in the message); an unrecognised
       error degrades to LOGIN_FAILED, never throws.
     * Deploy order: (1) both Supabase templates get {{ .Token }} per
       §4, (2) deploy webapp, (3) §6 live check on phone and laptop.
       Deploying before (1) sends emails with no code in them.
     * Next number: 237.

237. **(2026-09-03) Spec 013 LIVE and verified by the founder; one
     copy fix owed.**
     * Templates edited (both), deployed, §6 passed: phone code path
       lands on Today without leaving Kettle; laptop link path lands on
       Today; wrong code shows LOGIN_CODE_WRONG; 4th/5th send in a row
       shows LOGIN_RATE_LIMITED and a later retry delivers a code.
     * Copy fix: LOGIN_RATE_LIMITED still says "a few links in a row".
       It is codes now. New VERBATIM text: "That's a few codes in a
       row, and the mailer needs a short break. Wait a few minutes,
       then try once more." Spec 013 §3 amended; the "unchanged" note
       there was wrong.
     * "Installed as an app" in §6 meant the home-screen (PWA) install
       the manifest already allows; the founder tested in the phone
       browser, which is the same code path. Either is fine.
     * Spec 013 status: SHIPPED. Asana 1218034241842672 layer 1 done;
       layer 2 (circles) stays phase 2.
     * Next number: 238.

238. **(2026-09-03) Webapp home-screen icon: replace the placeholder
     with the kettle, derived from the same asset as the site's
     favicon set (199).** Founder added Kettle to an iPhone home screen
     after the 013 flip and got a teal square with a white box:
     `webapp/public/icon-192.png` / `icon-512.png` are 506-byte and
     2 KB stand-ins from the demo-grade PWA commit (d5db4b2), and
     `index.html` points apple-touch-icon at the 192.
     * Ruling: one kettle, one source. The app icon is the site's
       apple-touch-icon treatment (the hero drawing on the canvas
       ground, 199), not a new flat glyph. `site/scripts/make-favicons.py`
       grows a webapp target so a re-run refreshes both sets.
     * Outputs in `webapp/public/`: `apple-touch-icon.png` 180x180
       (flattened, as 199), `icon-192.png`, `icon-512.png` (maskable:
       kettle inside the central 80% safe zone so Android's circle
       crop keeps the spout and handle), `icon.svg` = the site's
       `favicon.svg` glyph. Manifest and head updated to match.
     * iOS caches the old icon: after deploy the founder removes and
       re-adds the home-screen shortcut. Noted so it is not read as a
       failed fix.
     * Copy fix from 237 shipped at a7fc539, undeployed; rides this
       deploy.
     * Next number: 239.

239. **(2026-09-03) 238 CLOSED: icon live, founder-verified on an
     iPhone home screen after remove-and-re-add. Deployed together
     with the 237 copy fix.** Built at e3af8f7; webapp 193 tests,
     site 237, site favicon outputs byte-identical on re-run.
     * CC deviation accepted, and it corrects my brief: the maskable
       safe zone is a circle of radius 0.40, not an 80% square. The
       script solves the scale from the asset's measured alpha extent
       (kettle reaches 0.5617 of the crop side, so scale 0.712 lands
       the outermost ink at ~0.40). Derived at runtime, so it follows
       the artwork. Only the soft shadow tail crosses the circle.
     * Also accepted: maskable tiles opaque edge to edge (transparency
       is a hole, not a ground), and the new test checks the manifest's
       declared paths and sizes resolve on disk.
     * Beta invite text should say: add Kettle to your home screen
       (Safari: Share, Add to Home Screen); sign in with the emailed
       code. Both now hold.
     * Next number: 240.

240. **(2026-09-02, 10:50pm ET) Wave D owed items, checked against the
     live surfaces (the 234 lesson), ahead of the reaction-👍 pass.**
     * Cancellation PROVEN. sent_messages for Rehearsal/TestMom:
       Sep 1 ask 11:00:35 ET, no reply, follow_on 13:01:09 (the
       ladder fired, as designed). Sep 2 ask 11:00:57 ET, replied
       12:33:55, NO follow_on row for 2026-09-02. A reply cancels the
       follow-on; a silence does not. Both halves now on record.
     * Name path: Rehearsal owner display_name is already "Hema"
       (founder did it after 229 without a ledger line). Tomorrow's
       ask should render "Hi. Hema asked…"; if it says "Your family"
       again, that is a code path, not data.
     * FOUND: the Suryaprakasam owner's display_name is still the
       email address, so after the Phase 3 flip Amma and Appa would get
       the fallback "Your family asked…" instead of "Hema asked…".
       Same one-line fix, same table, must land BEFORE the flip. Added
       to the flip checklist (Asana 1218116228613723).
     * 232 deploy: site CONFIRMED live (heykettle.com reads "A normal
       day." and has no "ordinary"; meta description on v7 words).
       Product (kettle-api) not verifiable from outside (healthz has
       no version); founder to confirm `cd product && fly deploy` ran.
     * Still on the founder, two screens: Supabase Auth → Rate Limits
       → email sends to 30/hour (234); Twilio balance top-up (233).
     * Tomorrow (Thu Sep 3), quiet morning: reaction-👍 pass on
       TestMom at the 11:00 ET ask. Then Fri: no-reply ladder pass.
       Then Phase 3 flip. Beta invites after the flip.
     * Next number: 241.

241. **(2026-09-02, 11pm ET) 240's open items closed. Both owner
     names are "Hema"; product redeployed; rate limit was already 30.**
     * Suryaprakasam owner (members 7f20eb20…) display_name set from
       the email address to "Hema" by PM via Supabase, founder's
       go-ahead in chat; guarded update, one row returned. Both
       families now render the name path after the flip. Removed from
       the flip checklist's must-do.
     * `cd product && fly deploy` re-run by the founder; safe to repeat
       (prod = HEAD, no DB or secret change). 232's deploy owed is
       cleared on both halves.
     * Supabase Auth → Rate Limits → emails already 30/h (founder
       screenshot). 234's open item was already done on the live
       surface; the plan doc was behind again.
     * Twilio balance: founder RULED it stays at $20 for now, watched
       by hand. Nothing on the board spends it until Amendment A
       ships. 233's top-up note is closed as "not yet".
     * Next number: 242.

242. **(2026-09-02, 11:15pm ET) Board hygiene applied (ten tasks) and
     the demo family RULED (Asana 1218125400783474).**
     * Closed as done-in-fact: W0 WhatsApp API application (222-229),
       W1 CI GitHub Actions (ci.yml), W0 iCloud shortcut test on Mom's
       phone (superseded by 005b), and the parent-timezone backlog
       task, which was built Aug 26 as spec 009 §1 + spec 010 and
       never closed. Closed as superseded: the three July Pilot tasks.
       Re-dated: closed beta Aug 22 → Sep 12 (after the flip),
       partnership outreach Aug 15 → Oct 3 (after launch), delete the
       signed-files folder Aug 18 → Sep 6 (with Mom's shortcut visit).
     * Demo family, founder ruling: names and cities that read as
       universal to a US audience; an Indian family would read as
       "not for me" to many. The Whitakers: Sarah (owner, Boston,
       America/New_York); Linda "Mom" and Bill "Dad" in Phoenix
       (America/Phoenix, no DST, so the "hours behind you" line
       demos cleanly). Not "Kettle Demo Family" (that is the test
       fixture, Kolkata, Demo Amma/Appa) and not a new fixture: a real
       provisioned family in prod, flagged by having NO phone_e164 and
       NO whatsapp_e164 on either parent, so no ask can ever go out.
     * History is seeded by a script in the repo, not hand-typed SQL:
       repeatable, deterministic, idempotent, and refuses any family
       that has a phone number. Thirty days, three story days: one
       quiet start that turned normal, one couldn't-reach that ended
       with an all-clear, the rest normal. Brief to CC tonight.
     * Follow-up for the founder, same reasoning: the site's ask copy
       line uses "Priya asked Kettle…" (site/src/copy.ts:103). If the
       demo family is universal, that line probably should be too.
       Not changed tonight; founder to rule.
     * Next number: 243.

243. **(2026-09-02, 11:45pm ET) Demo seeder built at 416c048 (product
     570 → 589). Three rulings on the build report.**
     * Marker `demo-seed` in pings.ip_hash and sent_messages.transport
       ACCEPTED: neither column renders. Journal notes are owned by
       content (the seeder deletes only bodies it is about to write):
       ACCEPTED, no migration; a marker in a family's own record would
       be a marker a person reads. The isolation test that plants a
       real ping and a typed note inside the demo family and asserts
       both survive a re-seed is the guardrail that matters here.
     * Dad's couldn't-reach day is `follow_on_unreachable` (zero pings
       of any grade), correctly matching 242's wording. That leaves the
       product's central story undemoed: a changed morning, Kettle
       asks the parent, the parent answers, the family never hears.
       RULED: two more story days. (d) Dad, 23 days ago: normal start,
       then quiet from about 08:30 local, the ask goes out at 11:00,
       he replies at about 11:20, no follow-on, pings resume at
       about 11:30. (e) Mom, 26 days ago: same changed-morning shape,
       no reply, `follow_on_family` at the follow-on hour, pings
       resume mid-afternoon, note that evening "Was at Carol's. Left
       the phone on the counter." Five story days; every message kind
       the product can send now has one example.
     * Engine-replay test (seeded ledger discarded, real `run_outbound`
       replayed at the schedule instants, compared) ACCEPTED and
       named as the reason this demo stays honest: if the ladder is
       re-timed, the demo fails rather than drifting.
     * Order: CC adds (d) and (e), then founder provisions the
       Whitakers in prod and seeds; PM reads the rows before any
       screenshot.
     * Next number: 244.

244. **(2026-09-03, 8:55am ET) Five story days built at e7e27c0
     (product 593). The engine won both arguments with the brief, and
     that is the point of the replay test.**
     * Brief said "normal start, then quiet from 08:30". A routine
       ping before 08:30 makes the morning non-quiet and the ask never
       arms. The shape that produces an ask is a phone awake and
       reporting (heartbeat, charger) with the habit apps never
       opening: alarm-grade silence, not total silence. That is what
       (d) and (e) now seed, and it is also what separates
       follow_on_family (e) from follow_on_unreachable (b). PM brief
       was wrong about the mechanism; the ledger says so.
     * Brief said "normal evening" for (d) and (e). Engine: (d) is
       digest_evening_recovered (a quiet morning that came back); (e)
       withholds the evening as skipped, per 164 (no evening note on a
       day a follow-on went out). (e) also produces all_clear_family
       when Mom's habits resume at 15:00. All accepted.
     * All eight templates now have an example, and a test asserts the
       set. replied_utc was outside the idempotence snapshot; added.
     * Founder next: provision the Whitakers in prod, seed, tell PM;
       PM reads rows before any screenshot. Today at 11:00 ET is also
       the Wave D reaction-👍 pass on TestMom; unrelated family, no
       interaction.
     * Next number: 245.

245. **(2026-09-03, 9:30am ET) Whitakers provisioned and seeded in
     prod (family ad55ad3f…, 472 pings, 127 ledger rows, 3 notes).
     PM read the rows: story days land where ordered. One gap found
     that needs a build before the family is left running.**
     * Rows: (a) Aug 28 Linda quiet-then-normal, digests only; (b) Aug
       22 Bill ask 11:00, follow_on 13:00, all_clear 13:12, evening
       skipped, note "Phone was in the car. All fine."; (c) Aug 15
       Linda plain day, appointment note "Dr. Patel, Thursday 2pm"
       dated Sep 10; (d) Aug 11 Bill ask 11:00 replied 11:20, no
       follow-on; (e) Aug 8 Linda ask, follow_on 13:00, all_clear
       15:00, evening skipped, note "Was at Carol's…". No foreign
       pings, no phone numbers, both parents Phoenix.
     * THE GAP: the outbound engine walks every parent in the database
       (`parents_with_tz`); there is no per-family off switch
       (`digest_enabled` and `ladder_mode` are legacy and gate
       nothing, all three families read false/off while digests send
       daily). So from today the Whitakers produce, every day: a
       quiet-morning digest to the owner inbox, a skipped ask (no
       address) with its ops alert to the founder, a
       follow_on_unreachable email at 13:00 Phoenix, a skipped
       evening. "No phone number" (242) stops the ask; it does not stop
       the family emails or the alerts. Missed in 242; on record.
     * RULED: migration 0024 `families.demo boolean not null default
       false`; the outbound engine skips demo families before any
       decision (no ledger rows, no alerts); the app renders them
       unchanged. Not a general "pause" feature, which would be a spec.
     * RULED: the seeder gains `--through-now`, so today reads as a
       normal day in progress ("Heard from 12 minutes ago") at
       screenshot time instead of "nothing yet"; and a
       `scripts/render_digest.py` that writes a seeded day's digest
       emails as HTML files from the real templates, so the normal
       morning/evening digests can be screenshotted without the
       engine having sent them. Both replay-tested like the rest.
     * Copy: "Dr. Patel" → "Dr. Reed", same reason as the family
       names (242). Changed in the seeder, not the row, because notes
       are owned by content.
     * Until this ships: today's Whitaker emails (quiet morning at
       11:30 ET, follow-on at 16:00 ET) are real and screenshot-able;
       the ops alert at noon Phoenix is expected noise, ignore it.
     * Next number: 246.
