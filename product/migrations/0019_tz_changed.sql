-- 0019 — the city is the timezone (spec 010 §2).
--
-- The city picker is the ONE surface that moves a parent's clock: picking a
-- city writes city_label, tz and (when the zone actually changed)
-- tz_changed_utc in a single update. The timestamp is what the engine's
-- changeover conservatism reads (spec 010 §3): from this instant until the
-- first local midnight in the NEW zone, the ask ladder is suppressed and the
-- morning-quiet body is not used, because a shifted clock can fabricate a
-- quiet morning.
--
-- The grant model continues from 0018: column-scoped, so authenticated may
-- now update exactly city_label (0018), tz and tz_changed_utc — and nothing
-- else on parents. display_name and every other column stay refused, and the
-- contract test re-pins that. Rows stay bounded to the caller's family by
-- 0018's parents_update_own_family policy.

alter table parents add column tz_changed_utc timestamptz;

grant update (tz, tz_changed_utc) on parents to authenticated;
