-- 0034 — the OAuth `resource` parameter, RFC 8707 (DECISIONS 358, brief §3).
--
-- ChatGPT appends `resource=<MCP URL>` to its authorize and token requests.
-- The authorize request records the value it was asked for; the token
-- exchange refuses a request whose `resource` differs from it, and the grant
-- carries the value for the audit trail. Nullable: Claude sends none, and a
-- request without one is bound to no resource. Never granted to a client
-- role: the 0029/0032 column grant on assistant_grants lists its columns by
-- name and this one is not among them.

alter table assistant_requests add column resource text
    check (resource is null or char_length(resource) <= 2048);
alter table assistant_grants add column resource text
    check (resource is null or char_length(resource) <= 2048);
