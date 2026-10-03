# Assistant directories: conformance audit of `/mcp` (DECISIONS 358)

Scope: make Kettle's MCP server and its OAuth server pass the published
requirements of the Claude connector directory, the ChatGPT apps directory
and Meta AI Connectors, without changing what the tools do or say. Audit
first, then fix only the gaps listed below. Report each gap as found/fixed
or already-conformant. Anything outside this list is a follow-up note in
the report, not a change.

Sources (read before touching code):
- Claude: https://claude.com/docs/connectors/building/authentication and
  https://claude.com/docs/connectors/building/review-criteria
- ChatGPT: https://developers.openai.com/apps-sdk/build/auth and
  https://developers.openai.com/apps-sdk/app-submission-guidelines
- Meta: https://dev.meta.ai/products/connectors (early access; no
  published auth spec yet, so the ChatGPT and Claude rules are the bar)

## 1. Authorization server metadata (`/.well-known/oauth-authorization-server`)
- `code_challenge_methods_supported` lists `S256` (ChatGPT refuses the
  server without it).
- `token_endpoint_auth_methods_supported` includes `none`.
- `grant_types_supported`: `authorization_code`, `refresh_token`.
- `response_types_supported`: `code`.
- `registration_endpoint` present (it is).

## 2. Protected resource metadata (`/.well-known/oauth-protected-resource`)
- `resource` equals the MCP URL exactly, per host: `https://api.heykettle.com/mcp`
  on the new host, `https://kettle-api.fly.dev/mcp` on the old one (both
  hosts stay live, DECISIONS 357). Confirm the metadata is built from the
  request host, not a single default.
- `scopes_supported` present (an empty list is acceptable; absent is not).
- Unauthenticated `/mcp` answers 401 with
  `WWW-Authenticate: Bearer resource_metadata="..."` (it does; confirm the
  URL matches the host).

## 3. `resource` parameter (RFC 8707)
- ChatGPT appends `resource=<MCP URL>` to authorize and token requests.
  Accept it, bind it to the grant, and reject a token request whose
  `resource` differs from the authorize request's. Never 400 on its
  presence.

## 4. Client registration
- DCR (`/oauth/register`) accepts ChatGPT's redirect URIs:
  `https://chatgpt.com/connector_platform_oauth_redirect` and
  `https://chatgpt.com/connector/oauth/{callback_id}`. Exact match, no
  wildcard; each registration carries its own list.
- CIMD: add `https://chatgpt.com/oauth/client.json` to
  `KNOWN_CLIENT_DOCUMENTS` as the fallback copy, fetched live first the
  same way Claude's is (DECISIONS 319). Record the fetch date in the
  comment.
- Token endpoint accepts `application/x-www-form-urlencoded` (Claude
  requires it) and JSON bodies.

## 5. Tool metadata (`assistant_tools.py`)
- Every tool has `title` plus annotations: read tools
  `readOnlyHint: true`; `add_note` and `reply` `readOnlyHint: false`,
  `destructiveHint: false`; all tools `openWorldHint: false`. Wrong
  annotations are a stated rejection cause at both directories.
- Tool names stay as they are (all under 64 characters; read and write
  already separate).
- Descriptions unchanged: copy is the PM's, not this brief's.

## 6. Tests
- One test per item above, including both hosts for §2 and a `resource`
  mismatch for §3.

## 7. Report
- Table: item, found, changed (file:line), test. Then follow-ups found but
  not touched. No deploy; the PM and founder deploy after review.
