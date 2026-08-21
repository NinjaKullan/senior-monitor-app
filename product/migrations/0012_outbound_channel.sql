-- 0012 — the outbound channel's ledger and the one contact field it needs
-- (spec 007 §2.3 and §4, Wave A).
--
-- The table records **that Kettle spoke**, never what anyone did and never what
-- was said. No message body is stored: templates are code, and the ledger keeps
-- the template's id. The three-fields law is untouched because this is not a
-- signal table — nothing here describes a person's behaviour.
--
-- Posture, identical to `waitlist` (0009): there is no policy on it, so RLS
-- denies every anon and authenticated statement by default, 0004's revoked
-- default privileges mean neither role holds a privilege to exercise anyway,
-- and the direct revokes below say it a third time about this table
-- specifically. The API's service role is the only writer, and no client ever
-- reads it.
--
-- **The uniqueness key includes the parent, and that is a deliberate departure
-- from the spec's `(family, date, kind)`.** Migration 0006 exists because 0005
-- keyed a send at family granularity, and a family with two parents silently
-- lost the second row. Every message this channel sends is about or to one
-- person — the digest names a parent, the ask goes to a parent, the follow-on
-- is about a parent — so `parent_id` is NOT NULL and part of the key. Both of
-- the founder's parents are live in production; the spec's literal key would
-- have let exactly one of them be asked about per day. Cheap to overrule, and
-- recorded in DECISIONS.

create table sent_messages (
    id          bigint generated always as identity primary key,
    family_id   uuid not null references families(id) on delete cascade,
    -- Not nullable, and not a sentinel: see 0006 for the migration that had to
    -- undo exactly that shape.
    parent_id   uuid not null references parents(id) on delete cascade,
    -- The parent's local calendar day, so "one ask per day" means her day.
    local_date  date not null,
    kind        text not null check (
        kind in ('digest_morning', 'digest_evening', 'ask', 'follow_on')
    ),
    -- Which template said it. The body lives in code and is never copied here.
    template_id text not null,
    transport   text not null,
    sent_utc    timestamptz not null default now(),
    -- Set by the reply intake (§2.6): the parent answered, timestamp only. It
    -- lives on the ask's own row because that is what it answers, and because a
    -- follow-on's precondition is then a single row's state rather than a join
    -- across two tables that could disagree.
    replied_utc timestamptz
);

-- The sent-once guarantee. A crashed-and-restarted scheduler re-deciding the
-- same day cannot double-send: the second insert violates this index.
create unique index sent_messages_once_idx
    on sent_messages (family_id, parent_id, local_date, kind);
create index sent_messages_family_idx on sent_messages (family_id, local_date);

-- The parent's WhatsApp number (§4). Deliberately a second column rather than a
-- reuse of `parents.phone_e164`, which 0007 defined as the SMS number the spec
-- 004 ladder's ASK stage uses: the two ladders are separate code paths in this
-- pass, and one column serving two senders would make "which channel did we
-- reach her on" unanswerable. A family with one number sets both.
--
-- The child's digest address is NOT added here. `members.email` has existed
-- since 0001 and spec 007 §3 says the digest goes to the child's account email,
-- so there is nothing to add; a second address column would be a second source
-- of truth for the same fact.
alter table parents add column whatsapp_e164 text;

alter table sent_messages enable row level security;

revoke all on sent_messages from anon, authenticated;
revoke all on sequence sent_messages_id_seq from anon, authenticated;
