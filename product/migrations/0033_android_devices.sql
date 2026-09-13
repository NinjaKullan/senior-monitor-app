-- 0033 — the Android device's claim record (spec 014 §6.5, DECISIONS 329).
--
-- Two columns on the device row, written once at POST /s/{slug}/claim and
-- read by nothing in the product: the OEM and the app version exist for the
-- soak-test record (which phones, which build). No new ping fields — a ping
-- is three fields forever (014 §7).

alter table devices add column oem text
    check (oem is null or char_length(oem) <= 120);
alter table devices add column app_version text
    check (app_version is null or char_length(app_version) <= 120);
