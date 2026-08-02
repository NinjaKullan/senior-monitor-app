-- 0009 — the landing page's waitlist (spec 006 §7).
--
-- The first table in this schema that has nothing to do with a family, and the
-- first whose rows are typed by strangers. Both facts drive its shape.
--
-- **Nothing reads this from a client, ever.** There is no policy on it — not a
-- restrictive one, an absent one — so RLS denies every anon and authenticated
-- statement by default, and 0004's revoked default privileges mean neither role
-- holds a privilege to exercise anyway. Two locks, and the API's service role
-- (which bypasses RLS) is the only thing that writes. The webapp's declared read
-- surface does not learn this table's name; a test asserts it stays out.
--
-- The `parent_phone` answer is the whole analytical point of the page — it is
-- what decides Wave 2 platform priority with data instead of instinct — so it is
-- a CHECK constraint rather than free text (standing structure 39: where a
-- precondition lives on the table, make the wrong state unrepresentable).
--
-- Email is stored lowercased and unique, and the API upserts. That is a privacy
-- decision as much as a hygiene one: a duplicate signup has to be
-- indistinguishable from a first one, or POST /waitlist becomes an oracle for
-- "is this person on the list".

create table waitlist (
    id           bigint generated always as identity primary key,
    email        text not null unique check (email = lower(email) and email like '%_@_%.__%'),
    parent_phone text not null check (parent_phone in ('iphone', 'android', 'unsure')),
    created_at   timestamptz not null default now()
);

alter table waitlist enable row level security;

-- Belt and braces over 0004's default-privilege revocation. That migration
-- stopped the bootstrap granting on *future* tables owned by the migrating role;
-- this says the same thing directly about this one, so the guarantee does not
-- depend on which role ran which file in which order.
revoke all on waitlist from anon, authenticated;
revoke all on sequence waitlist_id_seq from anon, authenticated;
