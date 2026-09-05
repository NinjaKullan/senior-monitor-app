-- 0029 — ask Kettle from an assistant (spec 019, DECISIONS 284).
--
-- kettle-api becomes an OAuth authorization server and an MCP server. Three
-- tables carry the plumbing and nothing about a family:
--
--   assistant_clients   what an assistant registered (RFC 7591): a name and
--                       the redirect URIs it may be sent back to.
--   assistant_requests  one pending authorization, from /oauth/authorize to
--                       the code being swapped: ten-minute life, single use.
--   assistant_grants    one row per connection a person made. Tokens are
--                       stored HASHED (sha256), never plain; a grant unused
--                       for ninety days expires; revoking sets revoked_utc
--                       and both tokens fail from the next call.
--
-- A grant stores an auth_user_id and NEVER a family: which circles the
-- assistant may see is looked up at call time from `members`, the same set
-- app_current_family_ids() yields, so removing someone from a circle (015)
-- removes it from their assistant in the same instant.
--
-- 0004 doctrine on all three: RLS on, no client write of any kind, and the
-- only client read is a person's OWN grants on the columns the Family screen
-- renders — the hash columns are not granted to `authenticated` at all, so a
-- select naming them is refused by privilege, not merely by policy.

create table assistant_clients (
    client_id     text primary key,
    client_name   text,
    redirect_uris text[] not null,
    created_utc   timestamptz not null default now()
);

create table assistant_requests (
    id             uuid primary key default gen_random_uuid(),
    client_id      text not null references assistant_clients(client_id) on delete cascade,
    client_name    text,
    redirect_uri   text not null,
    code_challenge text not null,
    state          text,
    scope          text not null default 'kettle:read',
    created_utc    timestamptz not null default now(),
    expires_utc    timestamptz not null,
    auth_user_id   uuid,
    code_hash      text,
    used_utc       timestamptz
);
create index assistant_requests_code_idx on assistant_requests (code_hash) where code_hash is not null;

create table assistant_grants (
    id                  uuid primary key default gen_random_uuid(),
    auth_user_id        uuid not null,
    client_id           text not null references assistant_clients(client_id) on delete cascade,
    client_name         text,
    created_utc         timestamptz not null default now(),
    last_used_utc       timestamptz not null default now(),
    revoked_utc         timestamptz,
    access_token_hash   text not null,
    access_expires_utc  timestamptz not null,
    refresh_token_hash  text not null,
    refresh_expires_utc timestamptz not null
);
create index assistant_grants_access_idx on assistant_grants (access_token_hash);
create index assistant_grants_refresh_idx on assistant_grants (refresh_token_hash);
create index assistant_grants_user_idx on assistant_grants (auth_user_id);

alter table assistant_clients  enable row level security;
alter table assistant_requests enable row level security;
alter table assistant_grants   enable row level security;

-- The one client read: a person's own connections, on the rendered columns.
create policy assistant_grants_own on assistant_grants
    for select to authenticated
    using (auth_user_id = auth.uid());

revoke all on assistant_clients, assistant_requests, assistant_grants from anon, authenticated;
grant select (id, client_name, created_utc, last_used_utc, revoked_utc)
    on assistant_grants to authenticated;

-- Disconnect from Kettle's side (spec 019 §5): the caller's own grant only.
create or replace function public.app_revoke_assistant(p_grant_id uuid)
returns void
language plpgsql
security definer
set search_path = public, auth
as $$
declare
    n integer;
begin
    update assistant_grants
    set revoked_utc = coalesce(revoked_utc, now())
    where id = p_grant_id and auth_user_id = auth.uid();
    get diagnostics n = row_count;
    if n = 0 then
        raise exception 'not_allowed' using errcode = '42501';
    end if;
end;
$$;

revoke all on function public.app_revoke_assistant(uuid) from public, anon;
grant execute on function public.app_revoke_assistant(uuid) to authenticated;
