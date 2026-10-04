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

## 5a. Title must also be an annotation (found at submission, Oct 3)
- The Claude directory form reads `annotations.title`, not the tool-level
  `title`, and flags all seven tools "Missing title annotation". Keep the
  tool-level `title` and set the same string on `ToolAnnotations.title` for
  each tool (one `ToolAnnotations` per tool, built from `READ_ONLY` or
  `WRITES` with the title added). Extend the §5 test to assert both fields
  carry the same title. Nothing else changes.

## 6. Tests
- One test per item above, including both hosts for §2 and a `resource`
  mismatch for §3.

## 7. Report
- Table: item, found, changed (file:line), test. Then follow-ups found but
  not touched. No deploy; the PM and founder deploy after review.

## 7. ChatGPT mints a client document per app (found Oct 4 at the OpenAI
## portal's Connect step; ruling by the PM, DECISIONS 358)
- OpenAI's dashboard did not use `https://chatgpt.com/oauth/client.json`.
  It sent `client_id=https://chatgpt.com/oauth/A1YFUC1zmNdF/client.json`
  with `redirect_uri=https://chatgpt.com/connector/oauth/A1YFUC1zmNdF`,
  and Kettle answered `invalid_client` because, since F1, only the exact
  keys of `KNOWN_CLIENT_DOCUMENTS` count as client documents.
- Ruling: trust is per host prefix, not per exact URL. A client_id is a
  client document when it starts with one of `TRUSTED_CLIENT_DOCUMENT_PREFIXES`
  = `https://claude.ai/oauth/`, `https://chatgpt.com/oauth/` (a module
  constant, no setting). Such a document is fetched live as today (same
  timeout, cache and failure memory); when the fetch fails, the shipped
  copy in `KNOWN_CLIENT_DOCUMENTS` stands if there is one, otherwise the
  client is unknown. Nothing outside the prefixes is ever fetched, so F1's
  guarantee holds: no arbitrary URL reaches the fetcher.
- Pin this document in `KNOWN_CLIENT_DOCUMENTS`, as fetched Oct 4 2026 by
  the founder in Safari:
  client_id `https://chatgpt.com/oauth/A1YFUC1zmNdF/client.json`,
  client_name `ChatGPT`, redirect_uris
  `["https://chatgpt.com/connector/oauth/A1YFUC1zmNdF"]`. The document
  also lists token_endpoint_auth_methods_supported `none` and
  `private_key_jwt`; Kettle advertises `none`, unchanged.
- Tests: a chatgpt.com document under the prefix is a client even when
  not pinned (live fetch mocked); a URL outside both prefixes is unknown
  with no fetch (the F1 test stays green); the pinned copy stands when the
  live fetch fails. Update the F1 docstring in `is_cimd_client_id`.
- The `resource` parameter in the same request matched §3 and is fine.
