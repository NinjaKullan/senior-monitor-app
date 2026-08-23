-- 0014 — the relationship label outbound copy renders (DECISIONS 149).
--
-- Templates never use a parent's given name or a family's own pet name:
-- Kettle cannot know what a family calls their elders, and guessing pretends
-- an intimacy the product does not have. The child picks a label from a
-- standard set instead, and that label is the only thing `{relationship}`
-- ever renders.
--
-- The set is closed here on purpose. Free text in this column would be a
-- family's private vocabulary stored server-side and rendered into messages —
-- exactly what 149 rules out — so "extendable" means widening this constraint
-- in a later migration, never removing it. The Python mirror of this list is
-- `kettle.provisioning.RELATIONSHIP_LABELS`; a test holds the two identical.
--
-- Nullable because both live parents predate it. A parent without a label is
-- never rendered into a relationship-bearing template — the send is skipped
-- and the day's slot stays free (kettle/outbound.py), because a message that
-- reaches a family with a blank in it is worse than one that waits.
alter table parents add column relationship text
    constraint parents_relationship_known check (
        relationship in ('Mom', 'Dad', 'Grandma', 'Grandpa', 'Aunt', 'Uncle')
    );
