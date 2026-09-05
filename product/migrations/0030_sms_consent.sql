-- 0030 — SMS for +1 parents (spec 011 Amendment A, DECISIONS 231/290).
--
-- A parent in the US who does not use WhatsApp can receive the same ask by
-- SMS. The carrier filing says consent is verbal at setup and recorded with
-- the parent's record: `sms_consent_utc` is that record, set by the one
-- enrollment control ("They said yes") through a SECURITY DEFINER function,
-- admin only, the 017 pause pattern. With no consent the number is stored
-- and nothing is ever sent. `sms_opted_out_utc` is STOP arriving (or Twilio
-- error 21610), cleared by START; while set the ask is a quiet recorded skip.
--
-- The ledger admits one new kind, `sms_welcome`: the enrollment-confirming
-- text, once per parent ever (the engine keys it on (parent_id, kind), not
-- the day). No other RLS change: the columns ride the parents read the app
-- already has, and no client UPDATE touches them.

alter table parents add column sms_consent_utc timestamptz;
alter table parents add column sms_opted_out_utc timestamptz;

alter table sent_messages drop constraint sent_messages_kind_check;
alter table sent_messages add constraint sent_messages_kind_check check (
    kind in ('digest_morning', 'digest_evening', 'ask', 'follow_on', 'all_clear', 'sms_welcome')
);

create or replace function public.app_sms_consent(p_parent_id uuid)
returns void
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    target parents%rowtype;
begin
    select * into target from parents where id = p_parent_id;
    if not found then
        raise exception 'not_admin' using errcode = '42501';
    end if;
    if not exists (
        select 1 from members
        where family_id = target.family_id and auth_user_id = auth.uid() and role = 'admin'
    ) then
        raise exception 'not_admin' using errcode = '42501';
    end if;
    -- The button exists only for a +1 phone with no WhatsApp number (A.6);
    -- the function holds the same line so a stale screen cannot enrol a
    -- parent the routing would never text.
    if target.whatsapp_e164 is not null and target.whatsapp_e164 <> '' then
        raise exception 'has_whatsapp' using errcode = '23514';
    end if;
    if target.phone_e164 is null or target.phone_e164 not like '+1%' then
        raise exception 'not_a_us_number' using errcode = '23514';
    end if;
    update parents
    set sms_consent_utc = coalesce(sms_consent_utc, now())
    where id = p_parent_id;
end;
$$;

revoke all on function public.app_sms_consent(uuid) from public, anon;
grant execute on function public.app_sms_consent(uuid) to authenticated;
