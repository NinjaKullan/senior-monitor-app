-- 0018 — the display-only city label (spec 009 §5).
--
-- Kid-entered free text ("Chennai"), rendered on the Today card and the
-- parent detail as orientation, never as data: the timezone itself is NOT
-- editable here (separate backlog task), and nothing computes from this
-- column. Nullable on purpose — where absent the app falls back to
-- "{Name}'s time".
--
-- The update grant is COLUMN-scoped: authenticated may update city_label and
-- nothing else on parents, so the standing read-only contract on every other
-- column holds (product/tests/test_webapp_contract.py's "update parents set
-- display_name" must still be refused). RLS bounds the rows to the caller's
-- own family in both directions of the update.

alter table parents add column city_label text
    constraint parents_city_label_length check (char_length(city_label) <= 40);

create policy parents_update_own_family on parents
    for update to authenticated
    using (family_id in (select public.app_current_family_ids()))
    with check (family_id in (select public.app_current_family_ids()));

grant update (city_label) on parents to authenticated;
