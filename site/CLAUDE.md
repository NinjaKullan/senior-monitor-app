# site/ — the marketing page, and the laws it is held to

Loaded when you are working under `site/`. Root `CLAUDE.md` carries the product law
that binds every surface; this file carries what only applies here.

`docs/design-language.md` is the law of this surface and `site/README.md` says what
the build enforces. Both are worth reading before a first change; what follows is the
short form and the things that are not written down anywhere else.

## Running anything

- `cd site && npm ci` on a fresh container, then `npm run ci` — lint, vitest,
  tsc + build + prerender, then the secret / foreign-origin / prerender checks in the
  order CI runs them. `npx vitest run src/tests/<file>` for one file while iterating.
- The build removes `dist/` before it starts. A build that fails must leave nothing
  behind: verification that reads a stale `dist/` passes against the *previous* build
  (`docs/failure-families.md` §1).

## The laws

- **The copy law** reaches every string a person can read, including alt text and
  `aria-` attributes, and it is scanned over `copy.ts` *and* the rendered DOM: no
  urgency, no diagnosis, no medical, alarm, surveillance or person-verdict wording, no
  romanized kinship or culture-coded vocabulary, and only three digits on the whole
  page. `src/tests/copyLaw.test.tsx`.
- **What, never how.** Public surfaces describe what is collected and never the
  mechanism — no tooling names, no automation vocabulary, no named infrastructure.
  Mechanism transparency belongs on the setup surface, behind an expiring link.
- **The motion law.** Entry fade and rise, once, gated `motion-safe:`; hovers are
  colour-only. Three scripted exceptions exist and all are written into
  `docs/design-language.md` §6 rather than into a component: the Rhythm Field, the
  three-fields dust answering a desktop pointer, and the kettle mark's steam. A fourth
  animated element is a new argument, to be made there first.
- **One typeface, five type roles, three real weights.** A sixth size is an amendment
  to `docs/design-language.md` §3, not a decision to be made inside a `className`.
  Emphasis is a whole sentence carried by weight, never an italic fragment.
- **One image set.** Every image the page renders comes from the six illustrations in
  `site/public/`, at unhashed stable names the cache contract depends on — plus the
  kettle mark, which is the brand's own object rather than an illustration and is the
  one decorative image on the page (DECISIONS 187). A decorative image carries an
  empty alt AND `aria-hidden`; anything else on this page carries written alt text.
- **The kettle mark's steam scales with the kettle, never with the page.** Every
  length in `src/kettle-mark.css` is a multiple of one container-relative unit, and a
  bare `px` there is the founder-reported drift returning. `scripts/probe-kettle.mjs`
  measures it in a real browser at three widths; the suite refuses the pixel.
- **The kettle mark reaches the page by being transparent, not by blending.** A
  `mix-blend-mode` here is a browser-specific bug written back in: iOS Safari will not
  blend across the GPU-composited rhythm canvas, so the multiply version showed the
  white ground on every iPhone (DECISIONS 190). The asset carries real alpha; nothing
  has to composite cleverly.
- **Nothing between the kettle mark and the hero section may create a stacking
  context** — no z-index, opacity, transform, filter, isolation or animation on an
  ancestor (DECISIONS 189, kept in 190). It was the blend that first exposed this, but
  the layering it protects outlived the blend: steam over drawing, drawing over the
  hero's wash and canvas. The hero's copy wrapper is `relative` with no z-index for
  exactly this reason, and the canvas stays behind it on DOM order.

## Mobile verification

- **Check the site on a phone before the founder does.** Any pass that touches
  layout or adds a component checks the affected sections at **360, 390 and
  768** and treats a wrap, overlap or horizontal overflow there as a blocking
  finding. jsdom lays nothing out, so the suite is structurally blind to this:
  twice the founder has found on a real handset what the whole suite called
  green (the field's orbits on the section's words; the scenario tabs folding
  into two ragged lines). `site/scripts/probe-responsive.mjs` and
  `probe-field.mjs` measure it in a real browser — neither is in `npm run ci`,
  because Playwright is not a dependency; run them against a preview server.
  What they cannot reach, pin as classes **with the arithmetic beside them**.

The two probes:

```bash
npm run build && npx vite preview --port 5288 &
node scripts/probe-responsive.mjs http://127.0.0.1:5288/   # wrap, overflow, tap targets, the floating CTA
node scripts/probe-field.mjs      http://127.0.0.1:5288/   # canvas pixels against text boxes
```
