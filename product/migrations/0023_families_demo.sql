-- 0023 — a family the engine walks past (DECISIONS 245).
--
-- The demo family (242) is flagged by having no phone numbers on either
-- parent, and that stops the ASK. It stops nothing else. The engine walks
-- every parent in the database, so from the day the Whitakers were seeded
-- they would produce, daily and forever: a quiet-morning digest into the
-- owner's inbox, a skipped ask with its ops alert to the founder, a
-- follow_on_unreachable email at 13:00 Phoenix, and a skipped evening. A
-- family that exists to be photographed does not get to send anybody mail.
--
-- Deliberately NOT a general pause switch. "Stop this family for a while" is
-- a product question with a spec attached (who may set it, what the app says
-- while it is set, what happens to the day it was set on). This is one bit
-- meaning "this household is scenery", read in exactly one place, and the
-- app renders a demo family exactly as it renders any other.
--
-- Default false, so every existing family keeps behaving as it does today
-- and the flag has to be set on purpose.

alter table families add column demo boolean not null default false;

comment on column families.demo is
    'Scenery: the outbound engine skips this family entirely (DECISIONS 245). '
    'Not a pause switch; the app renders it unchanged.';
