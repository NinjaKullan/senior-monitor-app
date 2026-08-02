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

---

## PM rulings — Fable, 2026-07-30 (review of 36fcc4a: four approvals, four changes)

24. **No pronoun inference** — approved, and adopted as policy: nothing ever infers pronouns from names. Neutral is the product default until spec 005's wizard collects an explicit optional field. Gendered variants stay behind the argument.
25. **Time format** — ⬅ **CHANGE.** Render `8:12 am`, lowercase. These are family messages; warmth beats locale-purity and both target markets read 12-hour comfortably.
26. **Cutoff gates the send moment too** — approved; a restart must never deliver a stale "good morning".
27. **Evening aggregation** — ⬅ **CHANGE** to the recording, not the index: record evening sends per included parent (one row per parent per member, `parent_id` always set) while the delivered message stays aggregated per timezone group. `parent_id` becomes NOT NULL for both kinds, the coalesce sentinel goes, the two-group collision dies, and the audit gets richer.
28. **Three-name evening copy** — approved; keep the pattern.
29. **WhatsApp members** — ⬅ **CHANGE.** Skip silently while the channel is a stub: no attempt, no failed row (a failed row would hold the day's slot and eat the first real WhatsApp digest when the channel goes live). One deduped ops row, kind `digest_channel_unavailable`, once per member per local day.
30. **Send-then-record window** — approved as built, no `pending`. The trade is right for this message class: a rare duplicate "good morning" is a harmless oddity, a silent loss is a missing reassurance. Document the window as a revisit-at-scale item; reopen when digests carry anything heavier.
31. **Unroutable family** — ⬅ **CHANGE.** An enabled family with no reachable recipient is a misconfiguration the founder must see: deduped ops row, kind `digest_unroutable`, once per family per local day, then skip as before.

### Implementation of the four changes (2026-07-30)

**25.** `format_time` builds the string by hand rather than with `%-I`/`%p` —
those are platform-dependent and upper-case respectively. Covered across the
awkward hours: midnight reads `12:05 am`, noon `12:00 pm`.

**27.** New migration `0006_digest_sends_per_parent.sql` rather than an edit to
0005, so it converges the schema whether or not 0005 has been applied anywhere —
the item-22 lesson. It refuses to run rather than deleting: if any aggregated
(null-parent) rows exist it raises with an explanation, because which parents
such a row covered was never recorded and cannot be back-filled, and silently
destroying send history would be the wrong default. Expected to be a no-op given
digests have never been enabled.

`test_two_timezone_groups_both_get_their_evening` is the regression the change
exists for: four monitored people, two timezone groups, two active parents in
each, four distinct rows on one local_date. Under the 0005 shape the second
group's message was silently blocked.

One behaviour worth knowing, a consequence of per-parent rows: a parent whose
first alarm-grade ping lands *after* their group's evening message has gone out
gets a follow-up summary naming both parents, because their row is missing. The
family gets two texts that evening, the second one accurate. Say the word if
you'd rather the day's summary be final once sent.

**29.** `DigestChannel` gained an `available` flag; the WhatsApp stub sets it
False and the scheduler skips those recipients before any send or record. Ops row
dedupe is per member per local day, keyed on the detail text since `ops_alerts`
has no member column — `db.ops_alert_exists_with_detail` does that, and a test
asserts two WhatsApp members produce two distinct rows rather than one.

**30.** Window documented in `_fan_out` where the trade is made, and in the
README, both flagged as revisit-at-scale.

**31.** `digest_unroutable` written once per family per local day before the
skip, with a test that a properly routable family produces none.

---

## PM ruling — Fable, 2026-07-30 (evening finality) + CI

**Ruling.** Evening is final per timezone group per local date. A parent whose
first alarm-grade ping lands after their group's evening send is omitted from
that day's digest entirely — no follow-up text. Rationale for the record: the
digest's contract is predictable cadence (one morning, one evening); a surprise
late text is an anomaly even with positive content, and a parent silent until 9pm
is heartbeat/ladder information, not digest information. The existing
`digest_skipped` ops row already tells the founder.

32. **Finality mechanism: the group-send fact, derived — no new state.** Of the
    three options offered (evaluated-marker, group-send fact, activity-before-
    send-moment) I took the middle one, because the fact is already in the
    database and the other two add something that can drift from it.

    `_fan_out` now takes two parent lists. `group_parent_ids` is everyone the
    message *could* have covered — the whole timezone group for an evening, the
    single parent for a morning — and a recipient holding a row for any of them
    has had that message today, so nothing further goes out.
    `covered_parent_ids` is who it actually vouched for and gets the rows. No new
    column, no marker table, and no second source of truth about whether a
    message went out: the rows that record the send are the same rows that
    prevent the next one.

    Rejected, for the record: an evaluated-marker needs its own write and can
    disagree with `digest_sends` after a partial failure; gating eligibility on
    "activity before the send moment" would change what the message *means*
    (it would silently redefine an active day as an active-by-20:30 day) and
    would still need a send fact to stop the 21:20 pass re-sending.

    Morning behaviour is unchanged by construction — its group is one parent, so
    the gate is the same test it always was, and there is a test asserting one
    parent's morning never gates another's.

33. **CI added: `.github/workflows/ci.yml`.** One file, both suites, ruff, no
    deployment steps. Postgres 16 service container so the product suite genuinely
    runs, and `KETTLE_REQUIRE_POSTGRES=1` in the job env, which turns the local
    "no database → skip" fallback into a hard failure. That is item 18's
    "revisit as a hard failure when CI exists", now due: a missing database on a
    laptop is a machine without Postgres, but in CI it is a broken pipeline.

    Verified as far as is possible without running Actions: the workflow YAML
    parses, the combined `pip install -r requirements-dev.txt -r
    product/requirements-dev.txt` resolves cleanly in a fresh 3.12 venv (the two
    files pin the overlapping packages identically), and the full suite plus ruff
    were run from that venv with CI's exact env — 159 passed. The hard-failure
    path was also exercised directly: with `KETTLE_REQUIRE_POSTGRES=1` and no
    database the product suite fails with "product suite FAILED — no Postgres
    reachable", and without the variable it still skips. What I cannot verify
    from here is the service-container wiring itself; the first run on main will
    say.

---

## Spec 004 — escalation ladder v1 (2026-07-31)

Built as specified; all nine acceptance criteria have tests. The two you called
out are the two I spent the most care on: `test_shadow_never_touches_a_channel`
asserts zero invocations against the channel object itself, and
`test_the_reply_body_is_dropped_everywhere` posts a distinctive body then greps
every column of every table plus every log record for it.

34. **The FAMILY copy says "she"; I render "they" unless a pronoun is recorded.**
    §4's binding copy is `...and she hasn't answered a gentle check-in`. That
    conflicts with the policy you adopted at item 24 — nothing infers pronouns
    from names — so I applied your ruling rather than the literal string: the
    default is `they haven't answered`, with `she`/`he` variants behind an
    explicit pronoun argument, ready for the wizard's optional field.

    Worth flagging beyond the policy: the substitution needs verb agreement, so
    the template takes a clause (`she hasn't` / `they haven't`) rather than a
    bare pronoun. A naive `{pronoun} hasn't` would have shipped "they hasn't
    answered" to a family. Tested in all four cases.

35. **Ladder copy lives in its own module.** `messages.py` carries a test that no
    template in it describes absence — which is the digest's whole law. Ladder
    copy exists to describe absence. Rather than weaken that test I put the
    ladder templates in `ladder_messages.py`, and there is now a test in each
    direction: no digest template mentions absence, no ladder template claims to
    be a digest.

36. **The contact line is the one place digits are allowed.** §3 says the
    FAMILY-ALL message includes the named contact's "name/number"; §4 says no
    digits anywhere. A phone number is the entire point of the suggestion, so I
    included it and scoped the copy-law test to exempt exactly that substring —
    everything else in the message still must contain no digit. If you would
    rather the copy name the contact without their number, that is a one-line
    change and the test tightens with it.

37. **Timing decisions the spec left open.**
    * The daytime window (05:00–21:00) gates *opening* a candidate. Once open, a
      ladder keeps walking outside those hours — a 20:30 ask whose grace expires
      at 22:00 still reaches the family. Stopping mid-ladder at 21:00 seemed
      clearly wrong; say if you meant otherwise.
    * `ask_skipped` goes to FAMILY-1 immediately in the same pass. There is no
      ask to wait for, so waiting the grace period would only delay the message.
    * The contact line appears at FAMILY-ALL only, per §3, not at FAMILY-1.
    * `mechanism_ok` = any ping of any signal since 05:00 local. Simple and
      defensible; a tighter "in the last N minutes" would be more sensitive to a
      phone that died at lunchtime.

38. **Founder ntfy fires in `live` too, prefixed `[LIVE ...]`.** §5 specifies it
    for shadow. Telling the founder less on the mode where real messages go out
    seemed like the wrong asymmetry, and it is not a privilege escalation — it
    goes to the same ops topic either way. Easy to restrict to shadow if you
    disagree.

39. **Live mode also requires digests at the database level, not just the CLI.**
    §1 says "requires `digest_enabled` as a precondition" and AC4 offers
    "constraint or check at flip time". Both columns live on `families`, so a
    table CHECK does it structurally: there is no order of operations, and no
    direct SQL, that leaves a family live without digests. The CLI reports the
    refusal rather than enforcing it.

40. **`ladder_candidates` is my design.** §3 names `ladder_events` and its
    columns, and references a `candidate_id`, but no candidates table is
    specified. Mine holds the stage, the trigger branch, `mechanism_ok`, one
    timestamp per stage, and the resolution — enough for the shadow ledger to be
    the labelled data the threshold analysis needs. Unique on (parent, local
    date), which is where "one candidate per parent per day" is enforced.

41. **A resolved candidate blocks re-arming for the rest of the day**, per §2 —
    including the case where the parent goes quiet again for eight hours after
    resolving at 12:30. That is v1 as specified and I have not built around it,
    but it is the behaviour I would expect to revisit first once shadow data
    exists.

---

## PM rulings — Fable, 2026-07-31 (review of dec9b2f: ALL APPROVED AS BUILT)

No code changes. Notes recorded against each item.

34. **Policy over literal — right call.** The clause-template grammar catch is
    appreciated. **Spec 004 §4's "she" is hereby amended to the neutral form.**
    (Note: `specs/004-ladder-v1.md` line 39 still carries the original string;
    the amendment is recorded here. A regression to "she" would fail
    `test_family_unanswered_copy_is_neutral_by_default`, which asserts the exact
    neutral wording, so the stale line cannot quietly become code.)
35. **The bidirectional absence-law tests are adopted as permanent structure.**
    Future message modules must join one side or the other explicitly: a module
    that describes absence, or one that must never describe it. Neither test may
    be weakened to accommodate a new module — add the module to the right side
    instead.
36. **The digits exemption for the contact number stands.** The number is the
    point of the suggestion.
37. **All four timing decisions approved**, with two revisit-notes carried
    forward to the threshold-analysis spec:
    * *Family-send quiet hours* — decide once shadow data shows how often
      post-21:00 escalations actually occur.
    * *`mechanism_ok` window* — likely to tighten from "since 05:00 local" to a
      recent-minutes window. A phone dead since lunchtime currently reads as
      mechanism-ok off a single morning timer ping, which flatters the handset.
      (Flagged by the implementer at item 37; the PM agrees it is right.)
38. **`[LIVE]` founder ntfy stands.** More visibility on the higher-stakes mode
    is the correct asymmetry.
39. **The CHECK constraint is the preferred mechanism**, and is noted as the
    pattern for future mode preconditions: where both sides of a precondition
    live on one table, make the wrong state unrepresentable rather than merely
    discouraged.
40. **`ladder_candidates` approved as designed**, including the unique-per-day
    index placement.
41. **Same-day re-arming stays as specified**, and is the first candidate for
    revision once shadow data exists.

---

## Spec 005a — child PWA, demo-grade (2026-07-31)

All nine acceptance criteria have tests. The stack decisions §1 left implicit
are recorded here too, since this is the first frontend in the repo and these
choices will be inherited by 005b.

42. **Refresh: 45-second polling, not Supabase realtime.** §3.1 left this open.
    Polling wins on three counts for this app specifically. The underlying
    events happen at human pace — a handful of pings a day, and the state only
    ever moves one way — so a socket buys latency nobody is waiting on. It has
    no channel-level RLS to reason about separately from the table policies,
    which matters because realtime authorisation is a second place isolation can
    be got wrong. And it has no reconnect path to get wrong on a phone that has
    been in a pocket for six hours, which is the actual usage pattern. Realtime
    becomes worth it when the ladder gets a surface (005b/004 UI) and seconds
    start to matter; today it would be complexity in the highest-trust screen.

43. **Stack setup decisions** (RosterPro-style, but the details were mine):
    * **TypeScript**, strict, with `tsc --noEmit` in both `build` and `lint`.
      The row shapes coming back from RLS-filtered queries are exactly the kind
      of thing worth typing.
    * **shadcn/ui components vendored by hand**, not via `npx shadcn init`. The
      CLI is interactive and network-dependent; what it does is copy source into
      your tree, so `components/ui/{card,button,input}.tsx` are those files,
      written directly, in the same shape the CLI produces. Adding more later is
      the same operation.
    * **Tailwind v3, not v4.** v4's engine is fine but shadcn's ecosystem and
      every example still assume v3's config file. No reason to spend the
      novelty budget here.
    * **Vitest + Testing Library**, jsdom environment. Vitest shares Vite's
      transform pipeline, so there is no second build config to keep in sync.
    * **Vite pinned to 5.4** rather than 6. Vitest 2.1 depends on Vite 5, and
      with both installed TypeScript sees two copies of Vite's types and refuses
      to typecheck the config. Pinning to one Vite is simpler than either a
      `vitest.config.ts` split or type-suppression, and Vite 6 buys this app
      nothing.
    * **eslint 9 flat config** with typescript-eslint and react-hooks. `npm run
      lint` is eslint; `npm run ci` is lint → test → build → verify:build, which
      is exactly what the CI job runs.

44. **The service-key guard decodes JWTs rather than pattern-matching them.**
    AC7 asks CI to grep the build output. A literal grep would miss the case
    that actually matters: a service key and a publishable key are both
    `eyJ…`-shaped JWTs, and the only difference is the `role` claim inside. So
    `check-build-secrets.mjs` extracts every JWT-looking string, base64-decodes
    the payload, and fails on any role that is not `anon` — plus literal patterns
    for `sb_secret_`, `service_role`, connection strings, and the Twilio/ntfy env
    names. Verified by planting both a fake service-role JWT and an
    `sb_secret_…` string in `dist/` and watching it exit 1.

45. **The morning digest's clock time is recomputed, not stored.** §3.2 says
    recompose from templates and store no message text. But the morning template
    contains a time that `digest_sends` does not record. Rather than add a
    column — which would be storing message content by another name — the app
    finds the first alarm-grade ping of that local date and re-derives the time
    from it, exactly as the backend did. If no such ping survives, that entry is
    omitted rather than rendered with a guess.

46. **AC1 is proved from the Python side, not through PostgREST.** "Re-use the
    two-family RLS fixtures through the real app's queries" cannot literally run
    the JS client here — that needs a live Supabase, and this container has
    Postgres only. So the app's entire read surface is declared in one file
    (`webapp/src/lib/queries.ts`), and `product/tests/test_webapp_contract.py`
    parses it, asserts every table it names is RLS-protected with a policy,
    asserts every column exists, and then runs those same selects as the
    `authenticated` role over the two-family fixtures. The selects carry no
    WHERE clause, which is the point: the app never filters by family, so if a
    policy were wrong the test would return the neighbour's rows. What is *not*
    covered is the supabase-js/PostgREST layer between the browser and those
    policies; the first real login against the deployed app is what confirms it.

47. **Copy now lives in two languages, with a guard against drift.** The digest
    templates exist in `kettle/messages.py` and `webapp/src/lib/copy.ts`, because
    the app recomposes messages rather than storing them.
    `test_webapp_copy_matches_the_backend_templates` parses the TS file and
    compares the strings, so drift fails the backend suite rather than shipping a
    digest list that quietly disagrees with the SMS a family received.

48. **`ops_alerts` and the ladder tables are absent from the read surface by
    assertion, not by omission.** A test checks `queries.ts` names neither. The
    founder's plumbing log has no privilege granted to `authenticated` anyway
    (0004), but the ladder tables *do* have family select policies, so nothing
    but this test stops a future screen quietly surfacing candidate history in
    the app whose floor is meant to be `Quiet so far`.

---

## PM rulings — Fable, 2026-07-31 (review of 4903112: ALL APPROVED AS BUILT)

No code changes. Notes recorded against each item.

42. **Polling at 45s approved**, with the reasoning adopted: realtime's
    channel-level authorisation is a *second* isolation surface, and buying one
    for events that happen at human pace is a bad trade. Revisit when the ladder
    gets a UI and seconds start to matter.

44. **Decode-don't-grep is adopted as the permanent pattern for secret checks.**
    Pattern-matching a credential that differs from a safe one only by an
    interior claim is exactly the vacuous-test failure mode this project keeps
    killing: it passes, it looks like coverage, and it would not have caught the
    thing it was written for. Any future secret scan decodes and inspects.

46. **The honest limit is acknowledged.** The PostgREST hop between the browser
    and the policies is verified by the founder's first real login against the
    deployed app; his membership is pre-seeded in the demo family for exactly
    that purpose.

48. **The read-surface assertion joins items 35 and 39 as permanent structure.**
    Any future screen widens `webapp/src/lib/queries.ts` deliberately and
    consciously, or not at all. Three standing structures now:
    * **35** — message modules join one side of the absence law explicitly.
    * **39** — mode preconditions become CHECK constraints where both columns
      share a table.
    * **48** — the app's read surface is declared in one file, and widening it is
      a visible act.

43, 45, 47. Recorded as-is.

### Production note (PM, via connector)

Migrations **0005–0008 are applied to `kettle-prod`**. Advisor-clean afterwards,
and 0004's default-privilege protection demonstrably covered the new function:
`app_claim_membership` arrived with no `anon` EXECUTE to revoke, because the
bootstrap defaults were already gone. The migration's explicit
`revoke ... from anon` was a no-op in production — which is the outcome 0004 was
written to produce, and worth having on the record as evidence it works rather
than as an assumption.

---

## Spec 005c — Glance warmth pass (implementer notes, 2026-08-01)

Nothing here blocks review; these are the judgement calls the spec left open,
recorded so the PM can overrule any of them cheaply.

49. **Pronoun default is the parent's own name, not `their`.** §1 says "her/his
    only if a recorded pronoun exists — else `their time` / `{Name}'s time`" and
    leaves the choice between those two. `renderClock` supports both, but with
    no pronoun recorded it returns `Amma's time`. Two reasons: it obeys items
    24/34 (never infer a pronoun from a name) without sounding like it is
    working around a missing field, and it reads warmer than the grammatically
    neutral form in a line the child sees every day. There is no pronoun column
    on `parents` yet, so today every subline takes this branch; the pronoun
    parameter exists so adding the column later is a data change, not a copy
    change.

50. **The subline collapses to one clock when both zones agree.** A child
    visiting Chennai would otherwise read `8:12 am Amma's time · 8:12 am yours`,
    which is the interface admitting it does not know where you are. Same-string
    comparison, not same-offset: two zones that happen to render the same clock
    for this instant read the same to the person holding the phone, which is the
    only thing the line is for.

51. **The current segment reads `ahead`, not `quiet`.** §2 says a past segment
    with no routine renders soft/dim. That leaves the *in-progress* segment
    ambiguous, and I gave it the neutral future state. Dimming the segment you
    are standing in would turn "it is 10am and Amma is not up yet" into a
    verdict rendered at 10am — the exact thing the floor copy is written to
    avoid. A segment only ever dims once it is genuinely over.

52. **Day parts cover the whole clock; the small hours are `morning`.** §2 names
    05–12/12–17/17–21 for the arc, which leaves 21–05 unassigned for the
    *headline*. `dayPartFor` sends anything before noon to morning, so a card
    opened at 01:30 local reads `Quiet so far this morning`. It is the gentlest
    true thing at that hour, and inventing a fourth "night" state would add a
    copy line that only ever appears when nobody is looking. The arc still shows
    three segments — an overnight ping simply lights none of them, which is
    correct: it was not routine in any part of the day being described.

53. **The arc's accessible name is `Routine seen: morning, afternoon`.** The arc
    is `role="img"` with the segments `aria-hidden`, because three separately
    announced bars are noise. That label is the no-numbers law's real test
    surface: a screen-reader user must get the same coarse fact, not a richer
    one, so the guardrail test scans element *attributes* as well as text.
    Nothing has been seen yet reads `No routine seen yet today`.

54. **Beacon freshness is 26 hours**, per §3's "~26h". The `device_alive` timer
    fires daily, so the threshold is one cadence plus two hours of slack for a
    phone that charged late or a network that took its time. It is deliberately
    long: a beacon that goes still on an ordinary late morning teaches the
    family to ignore it. Boundary is inclusive (`<= 26h` breathes) and tested,
    so the state cannot flap on the tick.

55. **Reduced motion is handled by `motion-safe:`, not by JS.** The breathing
    class is `motion-safe:animate-breathe`, so a viewer with
    `prefers-reduced-motion` gets the still dot's appearance while the data
    state stays `breathing` in the DOM. That keeps the accessibility choice out
    of the honesty test: `data-state` always reports what the data says, and the
    animation is a presentation of it.

56. **The no-numeric-activity assertion compares markup, not text.** §1 asks
    that no rendered element encode a ping count. Scanning text would miss a
    count in an attribute or a class, so the test renders the same card from one
    ping and from five and requires byte-identical markup once clock times are
    masked. I verified it by planting both regressions: a `data-hits` attribute
    on the arc (caught by the attribute scan) and a genuine ping count threaded
    into an empty `<span>` (caught by the markup comparison, which text scanning
    could not have seen). The unconditional-animation regression was planted
    too, and the still-variant test caught it.

57. **`GLANCE_*` constants are now classified as headline or subline** in
    `test_webapp_contract.py`. The old floor test scanned every constant with
    that prefix for words like `no `, which the new subline placeholder
    `No routine seen yet` would trip — a plain absence caption is not a verdict,
    but a *headline* saying it would be. Rather than exempt the constant, the
    test requires every `GLANCE_*` name to be classified and fails on an
    unclassified one, so the floor cannot rot by someone adding a constant the
    scan silently skips.

---

## PM rulings — Fable, 2026-08-01 (review of 5072721: items 49–57)

Two ruled explicitly, the rest approved as recorded. Nothing in 49–57 is
believed to contradict product law, so nothing is reopened.

51. **APPROVED, and graduated to principle: the UI renders no verdicts on
    unfinished time.** In the PM's words — "the segment you're standing in reads
    `ahead`, never `quiet`. A 10am dim segment is an accusation against someone
    who slept in; `ahead` is patience." Recorded alongside the floor rule rather
    than as an implementation note, because it governs anything future that
    displays a stretch of time: the arc today, and any per-day or per-week shape
    that ever follows it. A segment dims only once it is genuinely over.

    Made load-bearing in the same commit: `webapp/README.md` now states the two
    rules together, `buildArc` cites the principle where the decision is made,
    and the test asserts it for **all three** segments plus the dims-when-over
    case — the old version only checked the morning, which would have let a
    future refactor render a verdict on an unfinished afternoon.

49. **APPROVED: `Amma's time` beats `their time`** — warmer, clearer, and it is
    the name the family themselves chose at provisioning. The pronoun field,
    when 005b's wizard collects it, *upgrades* the copy; the name stays the right
    default forever. Worth noting what this makes of the `pronoun` parameter on
    `renderClock`/`renderSubline`: not a fallback path awaiting a real answer,
    but an optional refinement over a default that is already correct.

50, 52–57. Approved as recorded.

### Standing structures (updated)

Four now, three of them shapes a future change has to work through and one a
rule about what may be shown:

* **35** — message modules join one side of the absence law explicitly.
* **39** — mode preconditions become CHECK constraints where both columns share
  a table.
* **48** — the app's read surface is declared in one file, and widening it is a
  visible act.
* **51** — no verdicts on unfinished time, and `Quiet so far …` remains the
  floor beneath everything that is finished.

---

## Spec 005d — tripwire health panel (implementer notes, 2026-08-01)

Nothing here blocked the build. Items 58 and 59 are the two the PM will most
want to overrule cheaply if I have read the spec wrong.

58. **The read surface did not widen — the *consequence* of reading it did.**
    §2 anticipates "this view widens `queries.ts` deliberately (parent_signals +
    per-signal last ping)", and standing structure 48 says that widening is a
    visible act. It turned out there was nothing to widen: 005a already reads
    `parent_signals` and `pings` whole, columns and all, so the detail view
    needed no new column and no new table. Rather than treat that as nothing to
    do, I asked what actually changed and made *that* the conscious act.

    What changed is stakes. `parent_signals.signal` used to pick a beacon's
    shade — an RLS leak there would have mis-tinted a dot. It now prints a named
    list of one parent's apps, so the same leak would print a neighbour's
    tripwire inventory. `pings.signal` likewise now decides what that list says
    about each row. So both tables are asserted row-by-row for isolation in
    `test_the_apps_own_queries_return_one_family_only` (they previously rode on
    the loop's `families`/`parents` spot-checks; `parent_signals` had no
    assertion at all), `queries.ts`'s header records why, and I verified the new
    assertion by dropping *only* the `parent_signals` policy and watching it
    catch the other family's rows. `ladder_candidates` joined the absent-tables
    assertion while I was there — 004 added it after item 48 was written, and it
    has a family select policy.

    If the PM would rather structure 48 be satisfied by a literal diff to
    `READ_SURFACE`, say so and I will narrow the two selects to the columns each
    screen genuinely uses — but that would be a *narrowing* dressed as a
    widening, and I do not think it is what the rule is for.

59. **Cadence defaults, and what would tune them.** Built as specified: 26h for
    `device_alive`, 7 days for everything else. Three notes for when there is
    pilot data to tune against.

    * **The 7-day window is a guess about *people*, not about equipment.** It has
      to cover the slowest real user of the least-used app, and today nobody
      knows what that is. A parent who opens the news app fortnightly will read
      `Not heard in a while` forever, and the repair nudge will sit on her card
      permanently until someone deactivates the signal — which is arguably the
      correct outcome (a tripwire nobody trips is not a tripwire) but arrives as
      a false alarm rather than as a decision. **The tuning data already exists:
      per-signal ping history is exactly what would give each signal its own
      cadence from that parent's own median gap.** That is the version I would
      build once the pilot has a month of data — per-parent, per-signal, learned
      rather than declared.
    * **A learned cadence is close to the line drawn by product law #1**, and
      I have not built it for that reason. "This signal usually arrives every
      2 days and hasn't in 5" is trend inference about equipment; the same
      sentence about a person is decline detection. If the PM wants the learned
      version, I would want the ruling to say explicitly that a per-signal
      cadence may never be shown, compared across time, or used for anything but
      choosing between the two chips.
    * **26h and the beacon's 26h are the same number for the same reason** but
      are two constants (`BEACON_FRESH_HOURS`, `CADENCE_HOURS.device_alive`). I
      left them separate deliberately: they answer different questions (is the
      handset alive? / is this tripwire reporting?) and will tune apart. If they
      are meant to move together, say so and I will make one reference the other.

60. **`never` reads as `Not heard in a while`, so a fresh family sees the repair
    nudge immediately.** A signal with no pings at all is beyond any cadence, so
    it is stale, so the nudge appears the first time the child opens the detail
    view for a parent whose shortcuts are not installed yet. That is the
    opposite of the 001 item-4 ruling (suppress the infra alert until the first
    ping ever arrives), so it is worth flagging — but I think the difference is
    real. That was an unsolicited ntfy push at a fixed hour, and nagging before
    setup teaches the founder to ignore it. This is a screen someone deliberately
    opened to ask "is my equipment working?", and the honest answer for an
    uninstalled shortcut is no. The nudge — "a two-minute FaceTime" — is also
    exactly the right instruction for a half-finished setup. A third chip
    (`Not set up yet`) would say it more precisely and would add a state the spec
    did not ask for; happy to add it if you want the precision.

61. **Signal names follow the backend's `SIGNAL_LABELS`, so `Charger On` and
    `Charger Off` are two rows, not one `Charger`.** §1's list of humanised names
    reads `Charger`, but §1 also says one row per active `parent_signals` entry,
    and the standard set has two charger signals. I resolved it toward the
    backend's existing labels because of what this screen is *for*: those strings
    are the names of the shortcuts on the parent's phone (`Kettle — Amma Charger
    On`), and a repair surface that calls a shortcut something other than its
    name sends the family hunting. `Daily Check` keeps the backend's casing for
    the same reason. A Python test now fails if the two ever drift. If you would
    rather see a single collapsed `Charger` row whose health is the newest of
    either signal, that is a small change to `computeTripwires` plus one line in
    the exemption list.

62. **The exemption is an allowlist passed by one caller; the ban is derived.**
    AC5 asks for a scoped exemption rather than a weakened global test, so
    `assertCopyLaw(text, allow)` masks an explicit list before the ban scan and
    every other surface calls it with no allowlist at all. Two asymmetries are
    deliberate: the **allowlist** is pinned as literals (deriving it from
    `SIGNAL_DISPLAY_NAMES` would let a newly added signal exempt itself), while
    the **ban** *is* derived from that map (so a new signal joins the ban for
    free). Deriving the ban immediately paid for itself: the law banned the raw
    keys but not the humanised names, and `Daily Check` — ordinary English —
    could have appeared on a digest or a glance headline with nothing objecting.
    That gap is now closed globally, which makes this commit a net *tightening*
    of the copy law rather than its first loosening.

63. **Day-granularity is enforced against the DOM, not against the copy.** The
    AC3 walk scans text *and* attributes for digits and allows exactly one shape,
    `N days ago`. Two things I got wrong first and fixed: the mask needs no
    leading `\b` (element text concatenates to `Connected3 days ago`, and the
    boundary silently stopped it matching — a mask that never matches is a test
    that proves nothing), and the mask must not become a blanket digit
    allowance, so the plant test asserts `opened 4 times` and a `data-days="3"`
    attribute both still throw. Verified the whole guardrail set by planting five
    regressions in the real components — a clock time on the recency line, an
    always-on repair nudge, a red chip, another parent's signals in the list, and
    a signal name on the Glance subline — and confirming each was caught by the
    test written for it before reverting.

64. **Rows are in configured order, not stale-first.** A maintenance list whose
    rows rearrange themselves between 45-second polls is harder to read than one
    that stays put, and the amber chip already carries the attention. Trivial to
    flip if you would rather the broken one always be at the top.

---

## PM rulings — Fable, 2026-08-01 (review of 1dc1f57: items 58–64)

One change requested (60), one deferral recorded (59), the rest approved.

58. **APPROVED as built.** Structure 48's spirit is that widening the read
    surface is a *conscious act*; the consciousness moved into row-by-row
    isolation assertions and added coverage `parent_signals` never had, which
    satisfies it. A literal `READ_SURFACE` diff would be a narrowing dressed as a
    widening and is **not** required.

59. **Do not build learned cadences.** v1's fixed windows stand until the
    pilot's threshold-analysis spec exists. The deferral is recorded rather than
    the design: *if* learned cadences are ever built they will be
    mechanism-health only, never displayed, and never compared across time — but
    that ruling belongs to that spec and is not made here. Cited at
    `CADENCE_HOURS`, where someone would go to change them.

60. ⬅ **CHANGE REQUESTED, and made.** `never` is `Not set up yet`, not stale.
    Same principle as the 001 item-4 ruling: absence of *ever* means
    not-yet-configured, not broken. Neutral chip, not amber; excluded from the
    repair-nudge trigger. **A fresh family's first minutes must not open with
    "something needs fixing."**

    Built as a third `TripwireHealth` state rather than a rendering special-case,
    so the distinction survives anything downstream that asks a row how it is
    doing. `needsRepair` is `some(health === "stale")` and deliberately not
    `some(health !== "connected")` — the comment says why, because that is the
    exact line a future refactor would smooth over. Both cases the PM named are
    tests, at the logic layer and again at the DOM: all-`never` parent → zero
    amber, zero nudge; one real ping then eight stale days → amber and nudge as
    normal. The unconfigured chip is also quieter than `Connected`, which at
    least earns its colour — an uninstalled shortcut should read like an empty
    field, not like a state.

61. **APPROVED** — the repair surface names what the phone names. The spec's
    humanised list in §1 is synced to the implementation (`Charger On`,
    `Charger Off`, `Daily Check`), not the other way round.

62–64. **Approved as recorded.** Standing instruction reaffirmed: flag anything
    believed to touch product law and it reopens.

### Process (founder, same day)

Builds land on `main` — merge the working branch and push there, now and for
future specs. `main` is the PM's review surface; a branch nobody has merged is
not reviewable by a `git pull`.

---

## UI polish round — founder, on-device (implementer notes, 2026-08-01)

Four changes from holding the app on a phone, no spec. Recorded because two of
them made judgement calls the founder's brief left to me, and one narrowed a
guardrail.

65. **The card's tap affordance is a chevron plus a colour-only pressed state.**
    `active:bg-muted/60` and a `focus-visible` ring, and deliberately no
    transform. A scale or translate on press would be the app's first animation
    outside `motion-safe:`, which item 55 put there on purpose — a viewer who
    asked for no motion should not get a card that jumps under the thumb. The
    test asserts the absence, not just the presence, so the cheap version of this
    (`active:scale-95`) cannot arrive later without failing.

    The chevron is `aria-hidden`: the tap target already carries
    `Tripwire health for {name}` as its accessible name, and a second announced
    element would only make the card noisier to a screen reader.

66. **The row height is `min-h-11`, the same 11 the Button uses.** Reusing the
    app's existing touch-target unit rather than inventing a padding value —
    it's the one number in this codebase that already means "comfortable to hit
    on a phone".

67. **The DOM walk narrows for SVG, and this is the one thing here I would flag
    as guardrail-adjacent.** The chevrons put `viewBox="0 0 24 24"` and
    `stroke-width="2"` in the detail view, which the AC3 digit walk correctly
    objected to. Rather than exempt the icons or drop the attribute scan, the
    walk now skips *geometry* attributes on SVG-namespaced elements only, and
    still scans `aria-*`, `data-*`, `role`, `title` and `alt` everywhere. Two
    plants prove the narrowing is that narrow: an icon carrying
    `aria-label="opened 4 times"` and one carrying `data-days="3"` both still
    fail, while a decorative chevron passes.

    The principle I applied: the walk exists to catch what a reader or a screen
    reader could reach, and it already skipped `class` for exactly that reason
    (Tailwind's scale is full of digits). Path geometry is in the same category.
    If the PM reads this as a weakening rather than a sharpening, the fallback is
    CSS-drawn chevrons and no SVG in the tree at all — a little uglier, and it
    would keep the scan absolute.

68. **`never` is deleted, not merely unrendered.** The founder's call was that a
    tripwire with no pings shows its chip and no recency text; the choice between
    an em dash and nothing was left to me, and I chose **nothing**. An em dash
    is a glyph a screen reader announces for a row that has nothing to say, and
    the row needs no filler to hold its shape — the chip is right-aligned either
    way. (The Family screen's `—` for a missing name is the other precedent, but
    that one is holding a column in a two-column list.)

    The word came out of `copy.ts` entirely and `renderRecency` no longer accepts
    the `never` kind, so a future caller reaching for it fails to compile. That
    follows the same reasoning the recency vocabulary already used against clock
    times: the constraint is safest when the string does not exist. The model
    still knows `recency.kind === "never"` — that is the fact — it simply has no
    words for it.

---

## Spec 005e — shortcut forge (implementer notes, 2026-08-02)

69. **The plist format, and what I could not verify.** The brief said to build a
    shortcut by hand in the Shortcuts app, export it, inspect it, and match the
    output. **I could not do that step.** This container is Linux; there is no
    macOS, no Shortcuts app, and no way to obtain a genuine export. Rather than
    write up an inspection I did not perform, here is the format as implemented,
    split honestly by how much each part is actually known — and a command that
    lets the founder close the gap in about two minutes on a Mac.

    *Known by construction (the code would not work otherwise):*
    * A `.shortcut` is a property list with a dictionary at the top. `plistlib`
      reads and writes it; XML and binary are both plists, and real exports are
      often binary, so `--verify` and `--inspect` accept either while the forge
      writes XML (diffable, and deterministic under `sort_keys=True`).
    * `WFWorkflowActions` is an array of action dictionaries, each with
      `WFWorkflowActionIdentifier` (a reverse-DNS string) and
      `WFWorkflowActionParameters` (a dictionary).
    * `Get Contents of URL` is `is.workflow.actions.downloadurl`, and its URL
      parameter is `WFURL`. A plain GET is the default, so no method, body, or
      header keys are needed — and every one of those omitted is a key an
      importing Shortcuts build cannot disagree with us about.

    *Inference — plausible, unconfirmed, and the reason this item exists:*
    * **The nine top-level keys.** Exports carry client-version, icon,
      import-questions, input-classes, types and minimum-version keys. I believe
      most are optional with sensible defaults, but I assert an exact set for
      *our* files anyway. That exactness is a self-imposed contract, not Apple's
      schema: it is what makes "an extra key fails" a meaningful test.
    * **`WFWorkflowClientVersion` / `MinimumClientVersion` = 900.** Chosen to
      claim as little as possible, on the theory that a low minimum asks less of
      a parent's phone. If Shortcuts rejects the file, this is the first thing I
      would change, and the value it wants will be in a real export.
    * **No `WFWorkflowIcon`.** A glyph number and a colour integer guessed wrong
      are a visible oddity on someone's home screen; omitted on the assumption
      Shortcuts supplies its default. Unverified.
    * **No `UUID` in the action parameters.** Believed necessary only when a
      later action references an earlier one's output, and there is no later
      action. If a real export has one on a lone action, note that it must be
      *deterministic* here (uuid5 over token+signal) or the diffable-bytes
      requirement in AC3 dies.
    * **`WFWorkflowTypes: []`.** Assumed to mean "no surface restriction".
    * **The signed output may not be a plist at all.** Recent macOS signs into an
      encrypted container rather than a plist, which is why `--verify` runs
      against the *unsigned* directory, before `forge-sign.sh`. If signing
      produces something `plistlib` still reads, that is a bonus, not the plan.

    *How to close it:* build one tripwire by hand on the Mac, export it, and run
    `python -m scripts.forge --inspect ~/Downloads/Whatever.shortcut`. It prints
    that file's keys, its action identifiers and parameter names, and the two
    key-set differences against what the forge generates. Anything surprising
    belongs back in this item — and the fix is almost always one constant in
    `scripts/forge.py`, because everything above lives in exactly one place.

70. **What `--mode anyone` asks of the receiving phone is documented but not
    proven.** Apple's material says signing sends the shortcut to Apple for
    validation and that "anyone" (versus "people-who-know-me") controls who may
    import it, and iOS 15 removed the standalone *Allow Untrusted Shortcuts*
    toggle. From that, a signed file should import with nothing turned on. I
    could not confirm it — no Mac to sign with, no handset to import to — so
    `product/README.md` states it as expected behaviour with the fallback
    (Settings → Shortcuts → Allow Untrusted Shortcuts, which only appears after
    the app has been opened once) and asks for the real answer after the first
    send. It decides whether 005b's wizard needs a "turn this on first" step,
    which is why it is worth writing down rather than discovering twice.

71. **Validation is exact rather than permissive, and that is a product
    decision.** `validate()` rejects an unexpected top-level key, an extra
    action parameter, or a second action, instead of checking only that the
    fetch is present. A permissive validator would pass every file the forge
    currently emits and would also pass the file where someone pasted in a
    second action — and these files get *signed and sent to a parent*, where
    nobody will ever read the plist again. Exactness costs a failed build the
    day Apple adds a key; permissiveness costs a shortcut that quietly does
    something extra on someone's mother's phone. The plants make the choice
    load-bearing: a second action, an extra key, a missing key, an extra
    parameter, a swapped action, four wrong URL shapes, and the name/URL
    mismatch each have a test, and I verified the set by making the validator
    permissive and watching five of them fail.

72. **Two judgement calls on the secrets discipline.** (a) The scan is stricter
    than the webapp's: `check-build-secrets.mjs` asks whether a JWT is the
    *safe* one, because a publishable key legitimately ships in a bundle. No JWT
    of any role belongs in a shortcut, so any that decodes is a finding — the
    test plants the `anon` key specifically, since that is the one a
    shape-matcher would most happily wave through. (b) `.gitignore` covers
    `*.shortcut` tree-wide as well as `out/`, because the founder will one day
    pass `--out ~/Desktop` or run from the repo root, and the directory rule
    alone would not catch it. The test asks `git check-ignore` rather than
    re-implementing gitignore matching, and also asserts that a tracked path is
    *not* ignored — otherwise it would be a test that passes on a broken repo.

73. **The forge is one file in `scripts/`, not a `kettle/` module with a CLI.**
    The repo's convention is logic in `kettle/`, thin entry point in `scripts/`,
    and I departed from it deliberately: this is a founder tool, `kettle/` ships
    in the deployed API image, and shortcut generation has no business running
    on the server. Tests import `scripts.forge` directly, which the pytest path
    config already supports. If the 005b CI-runner path pulls generation into a
    service, that is the moment to promote it to `kettle/`.

---

## Oura design analysis — research, no spec (2026-08-02)

Three calls raised by `docs/oura-design-analysis.md`. None blocked the research;
all three block the landing-page spec, and 75 touches product law.

74. **Both Oura typefaces are commercial, and the substitution is a design
    decision, not a swap.** The sans is Akkurat LL (Lineto), the serif is PP
    Editorial New (Pangram Pangram) — self-hosted `.woff2`, read from their
    `@font-face` block, so this is certain rather than guessed. Neither can be
    used by Kettle without a licence. Two things follow. (a) **Budget or open
    substitutes?** A licence pair is real money for a pre-revenue product; open
    alternatives exist for both roles but none is a drop-in for the serif's
    ultralight italic, which is precisely the face doing the emotional work in
    their system (§1). (b) **Whatever we pick must ship a real semibold.** Oura
    does not: they declare only 300 and 400 of the sans and then apply
    `font-bold` to every CTA, so every button on their site renders faux-bold.
    That is a bug we would be copying by accident. I have not chosen a pair —
    the analysis names the requirements per role (§11) and stops there.

75. **The "status eyebrow" is the one pattern I could not resolve against
    product law #1, and I want a ruling before the landing-page spec uses it.**
    Their data cards open with a small-caps, wide-tracked status word in a warm
    clay (`#D89078`) or pink (`#F06898`) — `PAY ATTENTION`, `STRESSFUL DAY` —
    followed by a serif sentence that interprets the number underneath it. The
    *typographic* device is the best thing on the site for our purposes: it
    states a condition without shouting, and the colour vocabulary deliberately
    excludes red. But the device exists to deliver a **judgement about a
    person's state**, which is exactly what law #1 forbids and law #6 constrains.
    My reading, which I have written into the doc as form-carries /
    semantics-refused: Kettle may use the eyebrow slot for a statement about
    **the routine or the setup** ("Not set up yet" already lives in this
    register, per the 005d ruling on item 60), and never for a statement about
    the person. If the PM wants the slot banned outright rather than
    re-purposed, say so before the spec — it changes the card grammar, not one
    string.

76. **The trade-dress line needs a number, not an adjective.** The brief said
    patterns yes, cloning no, and for structure that is easy to honour: type
    ratios, a 4px spacing unit, a 22-column named-line grid and a corner-anchored
    radial wash are techniques, and §11 carries them across without hesitation.
    Colour is where it gets uncomfortable. "Warm neutrals" is a look half the
    wellness market shares, but `#F7F1E8` ground with `#4A4741` ink *as a pair*
    is recognisably Oura's, and a landing page in that exact pair alongside an
    editorial serif and scenario tabs would read as an imitation to anyone who
    knows the reference. I proposed shifted values (`#F6F2EC` / `#403C36`) as
    candidates rather than picking, because how far to move is a brand call, not
    an implementation one. The question for the PM: is "same family, different
    values, and never their exact pair" the standing rule, or does Kettle want a
    deliberately different warmth — greener, greyer, or lighter — so the
    reference is invisible? The second is more work and a stronger position.

---

## Field results — founder on-device, recorded by PM (Fable, 2026-08-02): items 69–70

70. **CLOSED by field test.** A forge-generated, `--mode anyone` signed
    shortcut sent to a family member's iPhone imported with a single tap — the
    Add Shortcut sheet opened directly, no Settings toggle, no "Allow Untrusted
    Shortcuts" prompt at any point. **005b's wizard needs no "turn this on
    first" step.** The `product/README.md` expected-behaviour note can be
    promoted from expectation to fact. *Addendum (founder, next day): the
    shortcut also ran end-to-end on her handset and returned the server's OK —
    import and ping are both field-proven.*

69. **Downgraded to optional.** The same field test is stronger evidence than
    the inspect diff was designed to produce: Apple's signer accepted the
    forge's file and Shortcuts imported it on a real handset, so the inferred
    parts of the plist format (client version, omitted icon, omitted UUID,
    empty `WFWorkflowTypes`) are empirically fine. The inspect comparison
    against a hand-built export remains welcome — it would show what keys real
    exports carry and sharpen `validate()`'s exactness contract — but nothing
    is blocked on it. (For the record: the founder's command was correct; the
    only failure was pointing `--inspect` at a placeholder filename. Also for
    the record: inspecting a *forge-generated* file answers nothing — the diff
    is only informative against a shortcut built by hand in the Shortcuts app
    and exported. Paths with spaces need quotes.)

77. **forge.py must lazy-import psycopg** (PM, from the founder's field
    session). `--device-token` mode failed on a bare Mac with
    `ModuleNotFoundError: No module named 'psycopg'` — the forge imports its
    database driver even when the token is supplied directly and no database
    is ever touched. The founder tool should run dependency-free on a laptop
    that has never seen the backend: move the DB import inside the code path
    that needs it, and add a test that `--device-token` mode works with
    psycopg absent. Small fix, fold into the next build.

---

## Spec 006 — landing page (implementer notes, 2026-08-02)

Six calls, one of them a real ambiguity between two clauses of the spec.

78. **`--device-token` did not mean what item 77 said it meant, and fixing it
    took more than a lazy import.** Item 77 describes the mode as one where "no
    database is ever touched", but the code as built queried for two things the
    token alone does not carry: the parent's display name (which *is* the
    filename) and their active signal list. So a lazy import would have moved
    the failure rather than removed it — `psycopg` unimported, then imported one
    line later.

    Built instead as an explicit offline mode: `--device-token TOKEN --name
    "Amma"` takes both facts from the command line, exactly as they appear on a
    provisioning printout, and touches nothing. Signals default to the standard
    set with `--signals` to override, and the list is printed back before the
    files are written so an unexpected sixth shortcut is noticed at the terminal
    rather than on a parent's phone. With `DATABASE_URL` set, nothing changes:
    the database stays authoritative about what is active. If the PM would rather
    offline mode refuse to guess the signal list and require `--signals`, that is
    one line — but the founder had six shortcuts on a printout, and defaulting to
    the set that printout describes is the behaviour that matches the field.

79. **The drafted scenario sentences are intact word for word; the element
    boundary falls inside them.** §3.2 asks for "a serif emphasis phrase inside a
    sans sentence", which the drafts do not arrive pre-split into. Rather than
    set a whole sentence in the serif — which would break design-language §3's
    only permitted serif shape and the scarcity that makes it work — each
    scenario is a `_LEAD` (sans) and a `_SERIF` (its closing phrase). Nothing was
    reworded. Two of the four moved a clause between the lead and the following
    paragraph so the emphasis lands on the phrase carrying the feeling rather
    than the fact; the founder swaps strings freely at review either way.

80. **AC5 and §3.2 disagree about the notification, and I read AC5 as the
    narrower claim.** §3.2 gives the notification component to two panels ("where
    noted"); AC5 asks the four panels to "render identical DOM structure". Taken
    literally together they cannot both hold. I read AC5's purpose as *the `off`
    panel must not be escalated* — no extra border, no heavier weight, no badge —
    and tested it that way: the four panels share one component, one class list
    is asserted across all four, morning matches afternoon and off matches seen
    exactly, and `off`'s first six structural lines are compared against
    `morning`'s. If the PM wants the stricter literal reading, the fix is an
    always-rendered notification slot that is empty on two panels; I did not do
    that because an empty flex child changes the spacing and would be markup
    added to satisfy a test rather than a reader.

81. **The foreign-origin scan needed two named exemptions, and both are
    inert strings rather than requests.** `www.w3.org` is the SVG namespace
    identifier. `reactjs.org` is baked into React's production build as the
    minified-error link, inside a `throw`. Neither is ever fetched. They are
    listed by name with the reason beside them — the same visible-exemption
    shape item 67 used for the SVG geometry narrowing — and `foreignOrigins.test.ts`
    plants a font CDN, four analytics beacons, and two lookalike hosts
    (`cdn.reactjs.org.evil.test`, `w3.org.evil.test`) to prove the allowlist is
    exact-host and not a substring match.

82. **The motion scan reads the rendered DOM, not the source, and that change
    came out of a plant.** The first version scanned class literals in the
    source; planting an ungated `animate-rise` on `Section` did **not** fail it,
    because that component builds its class string from a template literal the
    regex could not see. A guard that reports green over the exact regression it
    exists to catch is worse than no guard, so the scan now walks every rendered
    element's `classList`, with the source scan kept as a second net. Worth
    recording because the lesson generalises: any source-text scan of Tailwind
    classes in this repo is one refactor away from silently covering nothing.

83. **Marketing's ban list is longer than the product's, on purpose.** Beyond the
    spec's six categories I added a medical group (`unwell`, `ill`, `hospital`,
    `fallen`, `injured`, `collapse`, `frail`, `at risk`) and `condition` /
    `cognitive` to the diagnosis group. §4 lists categories rather than closed
    vocabularies, and these are the words a well-meaning marketing edit reaches
    for first. None appears in any drafted string, so this costs nothing today
    and refuses a sentence nobody has written yet — which is the only time a ban
    is cheap. `SCENARIOS_H2` is mine, not the spec's ("An ordinary day."), since
    §3.2 names the tabs but not the heading above them.

---

## PM rulings — Fable, 2026-08-02 (review of 1effca4..0bbf9cc: items 78–83, plus the 74–76 record)

Review verdict: **approved, no changes requested.** One spec amendment made by
the PM (AC5, per the ruling on 80) so the spec and the suite agree in writing.

74–76. Formally recorded here for the numbering trail: ruled into
    `docs/design-language.md` §3/§7/§4 before spec 006 was written — Fraunces +
    Instrument Sans, self-hosted, with a true semibold (74); the eyebrow's
    typographic form travels for sections and scenarios only, person-status
    semantics refused under law #1 (75); Oura's palette strategy adopted with
    every value re-chosen around Kettle green, never their exact pair (76).
    Spec 006 §2 locked the resulting values.

78. **APPROVED.** The right fix — an offline mode taking its facts from the
    provisioning printout, rather than a lazy import that would have moved the
    failure one line. The blocker-with-companion test (prove the block blocks)
    is the plant-and-revert norm applied to an import, noted approvingly.

79. **APPROVED, with one norm restated.** The serif carrying a phrase rather
    than a whole sentence is not a deviation at all — it is design-language §3
    verbatim ("the emotional phrase inside an otherwise plain sans sentence").
    Review also found two wording changes item 79 did *not* disclose: step 1's
    body reworded ("Pre-built shortcuts note her phone's ordinary moments") and
    "at all" appended to step 2. Both are accepted on merit — they read better
    and pass the law — but the norm stands: copy edits are disclosed, not
    discovered in review.

80. **RULED: the purpose reading stands.** AC5 existed so the `off` panel can
    never be escalated. Morning≡afternoon, off≡seen, one class list across all
    four, and off's structural head equal to morning's proves that better than
    an always-rendered empty notification slot, which would be markup written
    for a test rather than a reader. Spec 006 AC5 is amended to say what is
    tested; no build change requested.

81. **APPROVED.** Two named inert strings with lookalike-host plants proving
    exact-host matching is a scoped exemption in the item-62 mould.

82. **APPROVED, and graduated to a working norm:** any source-text scan of
    Tailwind classes in this repo is assumed blind until proved otherwise;
    guards walk the rendered DOM, with source scans as a second net at most.
    Already recorded in CLAUDE.md's state-of-build; the plant discipline
    finding this hole is exactly why the discipline exists.

83. **APPROVED.** The medical group tightens in law #1's direction, and banning
    words no drafted sentence uses is the only time a ban is cheap.
    `An ordinary day.` stands. One nuance so item 62 is not over-read: this ban
    list is hand-written categories rather than data-derived — correct here,
    because marketing has no live vocabulary source to derive from. "Derived
    where possible" never meant inventing a source to derive from.

Owed by the founder before the page is live: migration 0009 applied to
`kettle-prod`, DNS, and a static host pointed at `site/dist/`
(`site/README.md`, three steps).

---

## Spec 006 Amendment A — universal English, both parents (implementer notes, 2026-08-02)

84. **The culture ban is scanned against the unmasked text, which makes it the
    first ban here that cannot be exempted.** Amendment A says "no allowlist
    entries", and there are two ways to build that: an empty allowlist, or an
    unreachable one. Every other ban in `copyLaw.test.tsx` runs over
    `mask(text, allow)`, so a future entry on the pinned allowlist would carry a
    kinship term through with it — the senior-first question is already exempt
    from the verdict ban that way, and it is the right mechanism *there*. For
    this group the exemption is simply not offered: the scan reads the raw
    string. A test passes an offending sentence as its own allowlist entry and
    requires it to fail anyway, and I verified the whole thing by moving the scan
    onto the masked text and watching that test go red.

    Worth a ruling only if the PM disagrees: it means a legitimate future use —
    quoting a family, say, in a testimonial — would need this file edited rather
    than an allowlist entry added. That felt like the right amount of friction
    for a rule that came from the founder looking at the built page.

85. **Two strings outside `copy.ts` carried the old words, and one of them is
    real copy.** `index.html`'s meta description repeated the hero sentence
    verbatim; it is the line a search result shows, so it moved with the string
    it mirrors rather than staying behind as the one place the old words
    survived. The other was a comment in `NotificationCard.tsx` ("a mother's
    name"), updated for consistency with the both-parents ruling rather than
    because any test looks at it. The privacy page was clean.

    Neither is covered by the ban test, which only reads `copy.ts` and the
    rendered DOM. If the PM wants the meta description structurally tied to
    `HERO_BODY` — it is the kind of duplication that drifts — that is a small
    change to the prerender check, and I did not make it unasked because it is
    a mechanism change rather than a string change and this amendment is
    explicitly strings and tests only.

86. **The morning sentence keeps QUESTIONS 79's split.** Amendment A gives the
    line whole (`By the time her coffee went cold …`); it lands as `MORNING_LEAD`
    plus `MORNING_SERIF` exactly as before, because design-language §3 permits
    the serif only as a phrase inside a sans sentence. The words are the
    amendment's, unaltered; only the element boundary sits inside them.

87. **`Her morning` / `Her afternoon` stay singular, and `OFF_SERIF` still says
    "asks her first".** Amendment A balances the *page*, and says the scenarios
    may follow one vivid parent — so the tab labels and the scenario copy were
    left alone deliberately rather than overlooked. What changed is the hero
    (plural) and the sample digest (Dad). The asymmetry is now asserted in two
    tests and explained in `copy.ts`'s header, because it reads like a mismatch
    to anyone meeting it cold and the obvious "fix" is the thing the amendment
    forbids.

---

## PM rulings — Fable, 2026-08-02 (review of 369f33e..66457ee: items 84–87)

Review verdict: **approved, no changes requested.** Amendment A built as
specified — strings and tests only, all three suites green.

84. **RULED: the unreachable exemption stands.** A rule that came from the
    founder looking at the built page must not be bypassable by an allowlist
    entry; the offending-sentence-as-its-own-allowlist test makes the
    unreachability load-bearing. If a real testimonial ever needs a kinship
    term, the right act is editing the ban's own file with the founder decision
    cited — widening as a conscious, visible act, the structure-48 philosophy
    applied to vocabulary. That friction is the feature.

85. **APPROVED as left, with one note for the next build that touches
    `site/`:** tie the meta description structurally to `HERO_BODY` in the
    prerender check — it is exactly the duplication that drifts. Declining to
    make a mechanism change inside a strings-only amendment was the right
    instinct; the find itself (a search result is copy, and the copy most
    people will ever see) is noted approvingly.

86. **APPROVED** — the 79 split applied to the new words is design-language §3
    working as intended.

87. **APPROVED.** The kept asymmetry — her scenarios, plural hero, Dad's
    digest — is Amendment A exactly as intended, and pinning it with two tests
    plus the `copy.ts` header paragraph is the house pattern: the deliberate
    choice defended against the obvious future "fix".
