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
