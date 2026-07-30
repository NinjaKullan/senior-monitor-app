# Implementer questions

Claude Code: when a spec is ambiguous or looks wrong, add a dated question here (don't guess, don't build around it). Fable reviews this file on every pull.

---

## Spec 001 — pilot backend (2026-07-25)

None of these blocked the build. Each records the reading I implemented so it can be
corrected cheaply; the code change is one-liner sized in every case.

1. **`ip_hash` has no salt env var.** §3 says "salted SHA-256 truncated" but the §2
   env table has no salt. I added `IP_HASH_SALT` (documented in `.env.example`), and
   when it is unset the app generates a fresh random salt per boot — hashes then stop
   correlating across restarts, which makes them useless for the "is this the same
   device?" ops question. Should `IP_HASH_SALT` be a required Fly secret instead?

2. **Interstitial gate: both parents, or either?** §4 reads "if today (IST) has no
   label row for each parent". I implemented **both** — `/status` shows data only once
   mom *and* dad each have a label row for today. If the intent was "show data as soon
   as any label exists", that is one line.

3. **Evening check window.** §5 says the 20:00 check applies the "same rule over the
   full day". I read "same rule" literally: zero alarm-grade pings since **05:00 IST**
   (the same window start as the noon check, just later). The alternative reading is
   since IST midnight, which would additionally forgive a 02:00 IST ping. Confirm?

4. **Infra alert on an empty database.** §5's infra rule ("no device at all has pinged
   in 24h") is literally true on a fresh deploy with zero pings, so a brand-new server
   sends one `🔧 Pipeline silent 24h` alert per IST day until the phones are
   instrumented. I implemented it literally. Want it suppressed until the first ping
   ever arrives?

5. **`who` on infra alerts.** The `alerts` table has a NOT NULL-ish `who` column but
   the infra alert is about the pipeline, not a person. Stored as `""`. Fine, or would
   you rather see `all`?

6. **"Last heartbeat check" has nowhere durable to live.** §4 asks `/status` to show
   the last check time; the §3 schema has no table for it. I kept it in process memory
   (resets on deploy, shows "not yet since restart"). Adding a one-row `meta` table
   would fix that but changes the schema you specified — say the word.

7. **Blinding scope.** Only `/status` is gated behind labels. `/pings/{who}`,
   `/export.csv` and `/labels.csv` are not — `/pings/{who}` is the promise made to Dad
   ("you can see every ping it has ever sent"), so gating it seemed clearly wrong, and
   gating the CSVs would let a curious `curl` bypass the discipline anyway. Confirm
   that's the intent, or say which ones should also be gated.

8. **Acceptance criterion 8 cannot be verified from here.** "Fresh deploy on Fly with
   empty volume boots, creates schema, passes `/healthz`" needs a Fly account and a
   deploy. I covered the code half —
   `tests/test_labels_and_views.py::test_fresh_empty_volume_boots_and_creates_schema`
   points the app at a non-existent directory, boots it, and asserts the schema is
   created and `/healthz` returns `{"db": true}`. The deploy itself is Hema's Saturday
   step; `README.md` has the exact commands.

9. **Empty note on "Save note".** Pressing "Save note" with an empty text box records
   `"nothing unusual"` rather than erroring, so a mistyped tap still leaves the day
   labelled (an unlabelled day is a hole in the Phase-1 dataset). If you'd rather it
   reject empty notes, that's a two-line change.

---

## PM answers — Fable, 2026-07-25 (review of fcc8a83: APPROVED, one change requested)

1. **IP_HASH_SALT** — keep as built. Hema sets it as a Fly secret at deploy; random-per-boot is the correct *fallback*, not the config. No code change.
2. **Interstitial gates both parents** — your reading is correct. Blinding means both labels exist before any data is seen. No change.
3. **Evening window from 05:00 IST** — correct. The waking window is the day; a 02:00 ping should not silence the evening check. No change.
4. **Infra alert on empty DB** — ⬅ **CHANGE REQUESTED.** Suppress the infra rule until at least one ping has ever been received (`last_ping_any() is None` → skip, don't fire). A fresh server nagging daily before the phones are set up trains the founder to ignore the 🔧 alert — exactly the alarm-fatigue failure this product exists to avoid. Include a test: empty DB at any hour → no infra alert; one ping then 24h silence → fires.
5. **`who=""` on infra alerts** — fine as stored. No change.
6. **Heartbeat last-check in memory** — accepted; `alerts` is the durable record. Do not add a meta table. No change.
7. **Blinding scope** — correct on all three counts. `/pings/{who}` is a transparency promise and must never be gated. CSVs ungated is accepted for the pilot; the discipline for Phase 1 is procedural: Hema, don't open `/export.csv` before labelling. No change.
8. **AC8** — acknowledged; that's Hema's deploy step, tracked in PLAN.md.
9. **Empty note → "nothing unusual"** — good judgment; an unlabelled day is worse than a default label. Keep.

Review notes, no action needed: HTML escaping verified throughout views.py; token compare is constant-time; no path from any alert to family (product law #3 holds); fly.toml `auto_stop_machines=false` rationale is right. Independent test run: 40/41 pass under a Python-3.10 shim in the review sandbox (the 1 failure is a sandbox SOCKS-proxy artifact in `test_log_only_when_no_topic_configured`, not a code issue; 41/41 claimed on 3.12 is credible). Known accepted risk: if the server is down for the entire 12:00–12:59 IST hour, that day's noon check is skipped — acceptable for pilot.

---

## Spec 001a — device_alive timer signal (2026-07-26)

Built exactly as specified: `device_alive` added to `SIGNALS`, deliberately not to
`ALARM_GRADE`, no other functional change. One thing I did **not** change, because
the spec says the config line is the only functional change, but which touches
product law #6:

10. **`/status` "Today: N pings" now counts `device_alive`.** The per-person headline
    count is unfiltered, so from tomorrow it silently includes ~1 timer ping per
    person per day. The per-signal table underneath breaks it out, so nothing is
    hidden, but the headline number is the one that reads as "how active was Mom
    today" — and a plumbing event is now a small part of it. Want that count
    restricted to alarm-grade signals (or to everything except `device_alive`)? It is
    a one-line change in `_render_status`, and I would rather you decided than have
    me quietly redefine a number you already read every day.

    **PM ruling — Fable, 2026-07-26: fix it.** Headline restricted to alarm-grade
    signals and relabelled "Today: N routine pings" so the number says what it
    counts. The per-signal table below is unchanged and still lists every signal,
    `device_alive` included. Implemented: `_render_status` passes `ALARM_GRADE` to
    `count_pings_between`; covered by
    `tests/test_status.py::test_today_count_headline_is_alarm_grade_only`
    (2 whatsapp + 1 device_alive → headline reads 2). Resolved.

---

## Spec 002 — multi-tenant core (2026-07-29)

Built as specified. None of these blocked the build; each records the reading I
implemented so it can be corrected cheaply.

11. **"Connects with the service-role key" → I used a Postgres connection string.**
    §1 says the service connects with the service-role key. Reading it against
    "plain SQL migrations, no ORM", I took that to mean the service-role *Postgres*
    URI (`DATABASE_URL`, Settings → Database → Connection string), driven by
    psycopg — not the service-role JWT against PostgREST via supabase-py. The
    isolation story is identical either way (that role bypasses RLS by design), but
    if you meant the REST client, the data layer changes shape.

12. **Provisioning creates an owner member only when `--owner-email` is given.**
    §5 lists family + parents + devices + seeded signals, not members. But a family
    with no member row is one no JWT can ever read, so the CLI takes an optional
    `--owner-email` and writes an `owner` row with `auth_user_id` left null — that
    column gets filled at Supabase Auth signup, not at provisioning. Confirm.

13. **`auth_user_id` is deliberately not unique.** A child monitoring their own
    parents *and* their in-laws is two memberships for one auth user, and the
    roadmap's "any elder, not just parents" points the same way. The RLS helper
    returns a set of family ids, so this works; there is a test for it
    (`test_policies_survive_a_second_membership`). A unique index would forbid it —
    say so if that is what you want.

14. **One device per parent at provisioning.** The schema is one-to-many; the CLI
    creates a single device per person because that is the iPhone case. No
    `--device` flag. Fine for beta?

15. **No revoke command.** §5 does not list one. `db.revoke_device()` exists and
    AC3 tests it, but the operator path today is a SQL update. The roadmap calls a
    lost phone "a one-tap revoke" — want `--revoke <token>` added to the CLI (or its
    own script) in this spec, or does that wait for the PWA?

16. **Infra check cadence.** §4 carries the pilot's infra rule over but does not
    restate "hourly". I evaluate it on every pass with once-per-family-per-local-day
    dedupe — same net behaviour as the pilot, no clock-hour condition. The evening
    window likewise starts at 05:00 local, per your ruling on the pilot.

17. **Local Postgres, not the supabase CLI, for tests.** `supabase start` needs
    Docker, and this container has the client but no daemon. So the suite runs on a
    plain Postgres plus `migrations/local/0000_supabase_shim.sql`, which creates
    only what hosted Supabase already provides (`auth` schema, `auth.uid()`, the
    three roles) — the policies under test are byte-for-byte the ones that ship.
    Both paths are documented in `product/README.md`. Writing the shim caught a real
    bug, incidentally: `''::jsonb` raises, so `auth.uid()` has to nullif the setting
    *before* casting, which is exactly how Supabase defines it.

18. **Product tests skip when no Postgres is reachable.** On a bare machine
    `pytest` reports "52 passed, 52 skipped" and exits green. That is deliberate —
    the pilot suite should not need a database — but a green run that skipped them
    is not a green run of this spec, and the README says so. If you would rather it
    fail loudly, that is a one-line change.

19. **One file outside `product/` changed: root `pyproject.toml`.** `testpaths` now
    includes `product/tests` so a bare `pytest` runs both suites, and isort is told
    that `kettle`/`scripts`/`testsupport` are first-party. `app/` and `tests/` are
    byte-identical — `git status -- app/ tests/` is empty. Flagging it because
    "pilot untouched" was a hard requirement and this is the one shared file.

20. **AC7 is half-verifiable here.** No Fly or Supabase account, and no Docker
    daemon, so neither the image build nor a real deploy ran. The code half is a
    genuine test: `test_empty_database_boots_and_passes_healthz` creates a brand-new
    Postgres database, applies the real migrations, asserts the table and policy
    sets, boots the app against it and checks `/healthz`. The deploy itself is
    Hema's step; `product/README.md` has the exact commands.

---

## PM rulings — Fable, 2026-07-29 (review of 3ba6ebb: APPROVED, one change requested)

11. **Service-role Postgres URI via psycopg** — correct reading, intended architecture. PostgREST adds nothing for a server-side service. No change.
12. **Owner member on `--owner-email`, `auth_user_id` null until signup** — right. Real member creation belongs to the PWA (spec 005). No change.
13. **`auth_user_id` non-unique** — approved and deliberate: one auth user in multiple families (own parents + in-laws) is a real customer shape. Keep it non-unique, keep the test.
14. **One device per parent** — fine for beta. Multi-device waits for a real need. No change.
15. **Revoke command** — ⬅ **CHANGE REQUESTED.** Add `--revoke <token>` to the provisioning CLI; print what was revoked (family, parent, platform); refuse with a clear message on an unknown token. A lost phone is an operational emergency and the operator path must not be hand-written SQL at midnight. Extend AC3's coverage through the CLI path.
16. **Infra evaluated every pass with per-local-day dedupe** — approved; equivalent to and simpler than a clock-hour condition. No change.
17. **Local Postgres + shim** — approved; sound, and the bug it caught proves it earns its keep. No change.
18. **Skip behaviour** — keep it, but make the reason explicit: "product suite SKIPPED — no Postgres reachable; this is NOT a green run of spec 002." Revisit as a hard failure when CI exists.
19. **Root `pyproject.toml`** — approved; shared tooling, not pilot behaviour. No change.
20. **AC7** — acknowledged; the deploy is Hema's step.

### Implementation of items 15 and 18 (2026-07-29)

**15 — `--revoke <device_token>`.** `provisioning.revoke_by_token()` resolves the
token, revokes that one device and returns what it killed;
`render_revocation()` prints family / parent / platform with the token masked to
its last six characters (the operator already has it; terminal history and
screen-shares do not need it in full). Unknown token → a message naming where to
find the token, and exit 1, never a silent success. Idempotent: a second run
reports "Already revoked" and preserves the original `revoked_utc`, because
emergency commands get run twice. `--revoke` refuses to be combined with
provisioning arguments.

AC3 now covers the operator path end to end
(`test_revoke_via_the_cli_kills_only_that_device`): two phones ping fine, the CLI
revokes one, that token gets a `403`, the *other* phone still gets a `200`, and
the DB shows exactly one device deactivated with a timestamp. Plus an
unknown-token test, an idempotency test, and one for the mutually-exclusive
arguments.

**18 — Skip reason.** Now reads exactly as ruled, with the URL and error type
appended. `-rs` added to the root pytest `addopts` so the reason always shows in
the summary — without it a fully-skipped product suite prints only "56 skipped",
which is the misreading the ruling is about.

---

## Migration 0003 — revoke anon EXECUTE (2026-07-29)

Added as directed, one line, matching what you already applied in production. The
shim needed two lines to make it testable rather than vacuous — Supabase grants
USAGE on `public` to all three roles and sets default privileges granting EXECUTE
on new public functions to them, and neither happens on a bare Postgres. With
both reproduced, the sequence now demonstrably behaves as production did:
after 0002 `anon` holds a direct EXECUTE grant that survived
`revoke all ... from public`, and 0003 is what removes it
(`test_anon_grant_exists_before_0003_and_is_gone_after`).

21. **The same Supabase bootstrap probably grants table privileges to `anon` and
    `authenticated` too — worth one query before we assume otherwise.** The
    default-privileges statement that produced the function grant you found is,
    in Supabase's standard project setup, one of a set covering tables and
    sequences as well:

    ```sql
    alter default privileges in schema public grant all on tables    to anon, authenticated, service_role;
    alter default privileges in schema public grant all on functions to anon, authenticated, service_role;
    alter default privileges in schema public grant all on sequences to anon, authenticated, service_role;
    ```

    If the tables line is present in our project, then in production every table
    created by 0001 carries `ALL` for `anon` and `authenticated`, and two of my
    test's claims are locally true but production-false:

    - `ops_alerts` — my test asserts an end user gets `InsufficientPrivilege`. In
      production they would more likely get **zero rows**, blocked by RLS having
      no policy rather than by privilege. Same data outcome, weaker mechanism.
    - `0002`'s `revoke insert, update, delete ... from authenticated` names only
      `authenticated`, so `anon` would retain write privileges — again gated only
      by RLS-with-no-policy.

    No data is exposed either way: RLS with no matching policy denies both reads
    and writes. But "protected by two independent things" and "protected by one"
    are different postures, and I would rather you know which one we have.

    I have **not** modelled this in the shim or changed those tests, because I
    cannot see production and I would be rewriting passing security tests on an
    assumption. One query from the Supabase connector settles it:

    ```sql
    select grantee, table_name, string_agg(privilege_type, ',' order by privilege_type) as privs
    from information_schema.role_table_grants
    where table_schema = 'public' and grantee in ('anon', 'authenticated')
    group by grantee, table_name order by grantee, table_name;
    ```

    If `anon` or `authenticated` appears against any table, say the word and I
    will add `0004` to revoke the residual privileges, teach the shim the table
    default-privileges line, and adjust those two tests to assert the real
    mechanism. If the output is empty, the current tests are already accurate and
    nothing needs doing.

    **PM answer — Fable, 2026-07-29: confirmed, and worse than suspected.** The
    bootstrap had granted `anon` the *full* privilege set on all seven tables —
    including TRUNCATE, which is not row-level and which RLS does not govern at
    all — and `authenticated` retained TRUNCATE/REFERENCES/TRIGGER plus SELECT on
    `ops_alerts`. `0004_revoke_residual_table_privileges` applied to production
    via the Supabase connector. Resolved.

    **Implementation (2026-07-29).** Shim now reproduces the tables and sequences
    default-privileges lines alongside the functions one, so the local
    pre-migration state matches the audit exactly: anon with
    SELECT/INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER on every table plus
    the identity sequences, authenticated with TRUNCATE/REFERENCES/TRIGGER
    everywhere and SELECT on `ops_alerts`. After 0004 the catalog holds exactly
    six rows: `authenticated` → SELECT on the six family tables. anon holds
    nothing anywhere, `ops_alerts` is granted to nobody, and the remaining
    default privileges name only `service_role`.

    The two tests I flagged now assert the mechanism rather than a locally-true
    accident: `test_ops_alerts_are_service_only` checks both gates separately (no
    privilege *and* no policy), and `test_authenticated_role_cannot_write_or_truncate`
    adds the TRUNCATE attempt — the operation RLS would never have caught. Two
    new catalog tests pin the end state exactly
    (`test_anon_holds_no_privileges_on_anything`,
    `test_authenticated_holds_exactly_select_on_the_family_tables`), and
    `test_residual_privileges_exist_before_0004_and_are_gone_after` proves 0004 is
    load-bearing by asserting the full pre-state, applying it, and asserting the
    post-state including that no default privilege still names anon or
    authenticated.

22. **`0004`'s SQL is my reconstruction, not your verbatim statements — please
    diff it.** Your message pasted the placeholder rather than the SQL you ran, so
    I wrote the file to reach the end state you specified and verified that end
    state against the catalog. It is functionally correct by test, but I cannot
    claim it is textually identical to what production received, and "the repo is
    canonical" is a claim about text. Paste the real thing and I will swap it in;
    if it produces the same end state the tests will stay green either way. The
    one place a difference could actually bite is the three ALTER DEFAULT
    PRIVILEGES statements — I revoke tables, sequences and functions from both
    `anon` and `authenticated`, which means any future object needs an explicit
    grant for authenticated too. If yours revoked from `anon` only, future tables
    would silently re-acquire the full set for `authenticated`, and that is worth
    catching now rather than at the next migration.

    **PM resolution — Fable, 2026-07-29: repo file is canonical; production
    converged to it.** Production's migration ledger does *not* match this repo
    statement-for-statement, and that is now a recorded fact rather than a
    discrepancy:

    - **Step 1**, applied via the Supabase connector as
      `0004_revoke_residual_table_privileges` before the repo file existed:
      revoked all table and sequence privileges from `anon`; revoked
      insert/update/delete/truncate/references/trigger on all tables and
      `select on ops_alerts` from `authenticated`; revoked all sequence
      privileges from `authenticated`; and three
      `alter default privileges for role postgres ... revoke all on
      {tables,sequences,functions} from anon` — **`anon` only**.
    - **Step 2**, applied today after reviewing this repo's file: the three
      `revoke all on {tables,sequences,functions} from anon, authenticated`
      statements, adopting the stronger both-roles doctrine from item 22.

    End state in production verified to match this repo's test assertions. The
    file stays as written; the ledger reads as two steps to the same place.

23. **`pg_default_acl` assertions must be scoped to the migrating role.** Noted
    by the PM: a hosted Supabase project carries default-ACL rows owned by
    `supabase_admin` that still name `anon`/`authenticated`. Those govern objects
    the platform creates, not ours, and cannot be altered from the `postgres`
    role — so the unscoped assertion in
    `test_residual_privileges_exist_before_0004_and_are_gone_after` was true in
    the shim (everything postgres-owned) and would have failed against
    production, reading as "0004 didn't work" when the app-owned defaults are
    clean.

    Fixed: the query now filters `pg_get_userbyid(d.defaclrole) = current_user`,
    with the reasoning in the test body and in the migration's own comment so the
    next person auditing production hits the explanation before the confusion.
    Verified rather than assumed — creating a default ACL owned by a second role
    and naming `anon` is seen by the unscoped query (1 row) and correctly ignored
    by the scoped one (0 rows). The assertion also now requires the scoped set to
    be non-empty, so a future mis-scoping that matches nothing fails loudly
    instead of passing vacuously.

---

## Spec 003 — digest engine (2026-07-30)

Built as specified; all 9 acceptance criteria have tests. None of these blocked
the build.

24. **There is no pronoun column, so the gendered copy never renders.** §1 gives
    `({time} her time)` with a neutral `({time} local time)` "when pronoun
    unknown", but neither spec 002's schema nor this one stores a pronoun. So the
    neutral form is what every message uses today. `render_morning()` takes an
    optional `pronoun` argument and the gendered variants are implemented and
    tested, so adding a `parents.pronoun` column later is a one-line wiring
    change.

    Worth stating explicitly because it is a product decision, not just a schema
    gap: nothing infers a pronoun from a name. "Amma" means mother in Tamil and
    the guess would usually be right, which is exactly what makes it a bad habit
    to build in — the one time it is wrong, it is wrong in a message to that
    person's family. If you want gendered copy, it should come from a field
    someone filled in during onboarding.

25. **Time renders 24-hour (`08:12`).** Unambiguous for both Chennai and Texas
    recipients and locale-free. `8:12 am` reads warmer if you prefer it — one
    line in `messages.format_time`, and the copy-law test does not care which.

26. **The morning cutoff also applies to the moment of sending.** §1 words it as
    "not sent if the first ping arrives after 14:00", but the stated reason — a
    "day started" at dinnertime is noise — applies just as much when the ping was
    at 08:12 and the server was down until 18:00. I gate on both, so a restart in
    the evening cannot deliver a stale "good morning". Say the word if you want
    the literal ping-time-only reading.

27. **Evening groups parents by timezone, and there is an index edge case.**
    §1 says a family's active parents aggregate into one message; AC5 says a
    Chicago parent gets their evening on Chicago's clock. Both hold only if the
    aggregation is per timezone group within the family, which is what I built:
    Appa (IST) gets his summary at 20:30 IST, Amma (Chicago) hers ~10.5 hours
    later. Single-parent messages record `parent_id`; aggregated ones record
    null, matching the unique index's `coalesce`.

    The edge case: a family with **two or more timezone groups that each have two
    or more active parents** would produce two aggregated rows, both with
    `parent_id` null and the same `local_date`, and the unique index would block
    the second group's message. Needs 4+ monitored people split across timezones,
    so it cannot bite the beta — but it is silent when it does. Fix is a
    discriminator in the index (the tz string, or a group id). I did not change
    your DDL to add one; say if you want it.

28. **Three-or-more-parent evening copy is mine.** §1 gives the one- and
    two-parent forms only. I extended the pattern: `Amma, Appa and Patti all had
    normal, active days.` The roadmap's "any elder, not just parents" makes three
    reachable. Confirm the wording.

29. **A `whatsapp` member before Meta verification produces one failure per
    message.** The stub reports "not sent" rather than pretending, so those
    recipients get a `failed` row and a `digest_delivery_failed` ops alert each
    time. That is honest and self-limiting (the failed row holds the slot for the
    day), and no beta family will be on `whatsapp` since the column defaults to
    `sms` — but if you would rather those members be skipped silently until the
    channel is live, that is a small change.

30. **The send-then-record window is real, and the schema hints at why.** True
    "never double-send" would claim the `digest_sends` row *before* dialling, but
    the `status` CHECK allows only `sent`/`failed` — there is no `pending` to
    claim with. So I send, then insert with `on conflict do nothing`. Restarts
    between passes are safe (tested); a crash in the narrow window between the
    provider accepting the message and the row landing would re-send on the next
    pass. The alternative trades a possible duplicate for a possible silent
    loss, which for a reassurance message seems the worse failure — but if you
    want the stronger guarantee, add `'pending'` to the CHECK and I will claim
    first and update after.

31. **A family with no reachable recipients is skipped entirely.** If an opted-in
    family has no member with a channel and a phone, the pass moves on without
    writing `digest_skipped` rows for its quiet parents — there is nobody the
    digest concerns. It also means that family generates no ops signal at all.
    Fine, or would you rather the founder be told that an enabled family has
    nowhere to send?
