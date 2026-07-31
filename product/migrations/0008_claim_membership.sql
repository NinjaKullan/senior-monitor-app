-- 0008 — link a Supabase Auth user to the member rows invited by their email
-- (spec 005a §2).
--
-- `members.auth_user_id` is null until the invited person actually signs up, so
-- something has to make the connection at first login. That something cannot be
-- an ordinary UPDATE from the client: the row is invisible to them until it is
-- claimed, and granting a write to close that loop would hand every logged-in
-- user a way to attach themselves to rows.
--
-- So: SECURITY DEFINER, and narrow. It matches on the *verified* email from the
-- JWT, never a parameter, so a caller cannot ask to be linked to someone else's
-- invitation. It only ever fills nulls, so an already-claimed row is untouched
-- by anyone. And it links every matching membership, because one auth user
-- genuinely can belong to two families — the in-laws case that item 13 kept
-- `auth_user_id` non-unique for.
--
-- Grants follow 0002's helper pattern and 0004's doctrine: revoke from PUBLIC,
-- grant to `authenticated` only, and never to `anon` (item 23's lesson — the
-- bootstrap's default privileges hand EXECUTE to anon at creation time, and
-- revoking from PUBLIC does not remove a direct grant).

create or replace function public.app_claim_membership()
returns integer
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    claimed_email text;
    claimed_count integer;
begin
    if auth.uid() is null then
        return 0;
    end if;

    -- The email comes from the verified JWT, not from the caller's argument
    -- list. There is no argument list.
    claimed_email := lower(nullif(
        current_setting('request.jwt.claims', true)::jsonb ->> 'email', ''
    ));
    if claimed_email is null then
        return 0;
    end if;

    update members
    set auth_user_id = auth.uid()
    where auth_user_id is null
      and email is not null
      and lower(email) = claimed_email;

    get diagnostics claimed_count = row_count;
    return claimed_count;
end;
$$;

revoke all on function public.app_claim_membership() from public;
revoke all on function public.app_claim_membership() from anon;
grant execute on function public.app_claim_membership() to authenticated;
