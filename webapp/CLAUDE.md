# webapp/ — the family app, and the laws it is held to

Loaded when you are working under `webapp/`. Root `CLAUDE.md` carries the product law
that binds every surface; this file carries what only applies here.

`webapp/README.md` is the fuller account — the security model, the screens, the one
tripwire-health exemption and why it is safe.

## Running anything

- `cd webapp && npm ci` on a fresh container, then `npm run ci` — lint, vitest,
  tsc + build, secret scan. `npx vitest run src/tests/<file>` for one file.
- The build removes `dist/` before it starts, for the reason in
  `docs/failure-families.md` §1: a failed build must not leave a previous artifact for
  a checker to pass against.
- **A bare `fly deploy` ships a deaf app.** The Dockerfile takes the API base URL as a
  build arg; `fly.toml` has to carry it. DECISIONS 114.

## The laws

- **This app never says which family you are looking at — with ONE exception.** An
  account in two or more circles gets the switcher, "Looking at" and the stored
  family names, and that is the only place a name may appear (spec 015 §8,
  DECISIONS 269). A single-circle account sees no switcher and no name; DECISIONS
  124 stands for them. A test holds both sides.
- **Membership is written only through the 0025 functions.** Add, remove, set role,
  set mail, leave — never a direct write to `members`. The functions decide who
  may; the app only renders the refusal in §9's words.
- **`Quiet so far` is as dark as this app ever gets.** The escalation ladder owns
  everything darker and does not live here. No counts, no signal names, no trend
  anything, no person-verdict — the copy law lands the same way it does on the site,
  and `src/tests/copyLaw.test.tsx` holds it.
- **App and channel names are banned except where a ruling pins them.** There are two
  such pins, each tied to one copy key rather than to a vocabulary: the SMS wording,
  and the setup card's share CTA, which may say "Send on WhatsApp" (DECISIONS 122). A
  pin is a single key, and adding one is a ruling, not an edit.
- **The setup link's slug never appears as text.** It travels inside an href and
  nothing else; a slug printed on screen is a token printed on screen.
- **Phone numbers ride in hrefs, never as text — with ONE spec-012 exemption:** the
  contacts sheet shows `phone_display` inside its `tel:` anchor (E.164 in the href),
  scoped to `data-testid="contact-phone"` and removed as a NODE before the copy
  scan's digit walk. The exemption is the element, never the digits; a number
  rendered anywhere else still fails the scan, and a plant proves it.
- **Journal dates render on the VIEWER's clock, parents' clocks on the family's.**
  DECISIONS 279/spec 018: a note is dated the way a messaging app dates it. The
  family zone still drives every parent-facing time. A test holds 03:30Z as two
  different days for New York and Kolkata viewers.
- **Notes are edited and deleted only through the 0028 functions.** The author
  edits their own; the author or an admin deletes; Kettle's lines never. The
  panel renders links only where the functions would say yes.
- **`/connect` is the one route, and `assistant_grants` the one per-person read.**
  Spec 019: the consent screen is reached from kettle-api with a request id in
  the URL and posts Allow with the Supabase session; the grants read is keyed on
  the viewer by RLS, never on a circle, and the token hashes are not granted at
  all. The address the family copies is the API host's `/mcp` and nothing else.
- **The journal is insert-only from the client's own SQL; contacts are editable.** A note is record and a
  correction is a new entry; a contact is reference data the family owns and may
  change or remove. Kettle's own lines (spec 012 §3) are written by the backend,
  never this app — the one auto note the app writes is the city change, and it now
  names its kind.
- **The cache contract** (DECISIONS 112): the shell always revalidates, hashed assets
  are immutable for a year, and no rule may reintroduce a lifetime on an unhashed
  file — otherwise a deploy white-screens returning browsers.
  `product/tests/test_webapp_caching.py` asserts it against `nginx.conf`.
