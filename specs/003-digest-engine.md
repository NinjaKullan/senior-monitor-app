# Spec 003 — Digest engine (the two daily messages)

*PM: Fable. Builds on spec 002's `product/` backend. This is the first family-facing feature of the product; the design decisions in PLAN.md ("Digest design decision", Jul 26) are binding.*

## 0. Product-law note (read first)

CLAUDE.md law #3 restricts family-facing sends "until a spec says otherwise." **This spec says otherwise — for digests only.** Digests are reassurance messages sent when routine IS observed. Absence-of-routine messaging to families (alerts, "quiet day" worry-inducers, the senior-first ask, the ladder) remains prohibited and belongs to spec 004. Nothing in this spec may message anyone about the *absence* of activity, and nothing here messages the senior at all. The pilot (`app/`) remains untouched and founder-only.

## 1. The two messages

**Morning ("day started"):** sent to the family circle when a parent's FIRST alarm-grade ping of their local day is observed.
- Trigger: first alarm-grade ping since 00:00 parent-local. Sent once per parent per local day (idempotent, survives restarts).
- Not sent before the ping exists — a "day started" without evidence is manufactured reassurance and violates the attribution rule.
- Cutoff: not sent if the first ping arrives after 14:00 parent-local (a "day started" message at dinnertime is noise; the evening message covers the day). Cutoff hour env-configurable.
- Copy (binding template): `Good morning — {parent}'s day started normally ({time} her time).` / neutral variant `({time} local time)` when pronoun unknown. Time is the first-ping time rounded to the minute. NO counts, NO app names, NO signal names.

**Evening (daily summary):** sent at a fixed parent-local hour, default 20:30 (env-configurable).
- Includes only parents who had ≥1 alarm-grade ping that local day: `{parent} had a normal, active day.` Multiple qualifying parents in one family aggregate into one message: `Amma and Appa both had normal, active days.`
- A parent with ZERO alarm-grade pings that day is silently omitted, and an `ops_alerts` row (kind `digest_skipped`) is written so the founder sees it. If no parent qualifies, no family message is sent at all. The family-facing absence path is spec 004's job; during beta the founder handles it humanly.
- Same copy law: no counts, no app names, no trends, no comparisons to other days.

## 2. Delivery

- Channel abstraction (`DigestChannel` protocol): implement **Twilio SMS** now; **WhatsApp template** as a stub implementing the same interface (wired when Meta verification lands). Per-member channel via new column (see §3); env: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM` (all optional → log-only channel, same pattern as ntfy).
- Recipients: family members with `digest_channel != 'none'` and a `phone_e164`. Send failures: log + `ops_alerts` (kind `digest_delivery_failed`), never retry-storm (one retry, then give up until next message).

## 3. Schema (migration 0005)

```sql
alter table families add column digest_enabled boolean not null default false;
alter table members  add column digest_channel text not null default 'sms'
    check (digest_channel in ('sms','whatsapp','none'));
create table digest_sends (
    id bigint generated always as identity primary key,
    family_id uuid not null references families(id) on delete cascade,
    parent_id uuid references parents(id) on delete cascade,  -- null for aggregated evening rows
    kind text not null check (kind in ('morning','evening')),
    local_date date not null,
    member_id uuid not null references members(id) on delete cascade,
    channel text not null,
    status text not null check (status in ('sent','failed')),
    ts_utc timestamptz not null default now()
);
create unique index digest_once_idx on digest_sends (family_id, coalesce(parent_id, '00000000-0000-0000-0000-000000000000'::uuid), kind, local_date, member_id);
```
- RLS: `digest_sends` select-policy for the family's members (same pattern as pings); no write grants (service writes). Follow 0004 doctrine: explicit grants only, and confirm the advisor stays clean after 0005.
- **`families.digest_enabled` defaults FALSE.** Nothing sends to any family until the founder flips it — per-family explicit enablement is the beta safety, on top of a global `DIGEST_ENABLED` env kill-switch (default off in `.env.example`).

## 4. Scheduler

Extend the existing in-process loop (or a sibling loop): each pass, per enabled family, per parent in the parent's effective tz — (a) morning: first alarm-grade ping today ∧ before cutoff ∧ no `morning` row for (parent, local_date) → send to each recipient, record rows; (b) evening: local time ≥ evening hour ∧ no `evening` row for (family, local_date, member) → compose, send, record. Idempotency comes from `digest_sends`, not from in-memory state, so restarts never double-send (test this explicitly).

## 5. Non-goals

Absence/quiet-day messaging to families (004). Senior-facing anything (004). WhatsApp Business verification flow. Per-family custom copy or send-times UI (005). Digest content beyond the binding templates. Photos, trends, scores, streaks — never.

## 6. Acceptance criteria

1. Morning: parent pings whatsapp at 08:12 local → each recipient gets exactly one morning message containing the parent's name and "day started normally"; a second ping, a scheduler re-pass, and a process restart produce no second send (DB-backed idempotency).
2. No ping → no morning message ever (assert zero sends on a silent day); first ping at 15:00 local → no morning message (cutoff), evening still counts the day as active.
3. Evening at 20:30 parent-local: active parents aggregate into one message per recipient; zero-activity parent omitted + `digest_skipped` ops row; all-parents-quiet → zero family sends.
4. Copy law enforced by test: rendered messages match the binding templates and contain no digits other than the time, no signal names, no counts.
5. Timezone: parent override (Chicago) gets morning/evening on Chicago clock while family (IST) parents use IST — two-parent test, injectable clock.
6. `digest_enabled=false` family with full activity → zero sends. Global `DIGEST_ENABLED=0` → zero sends regardless.
7. Twilio channel: mocked HTTP asserts one POST per recipient with correct E.164; failure path writes `digest_delivery_failed` ops row and does not crash the loop. Unset creds → log-only.
8. RLS: family member's JWT can select their own family's `digest_sends` rows and not another family's (extend the RLS suite); advisor-clean after 0005.
9. `pytest` green (pilot + product), `ruff` clean, pilot untouched, no secrets in diff.
