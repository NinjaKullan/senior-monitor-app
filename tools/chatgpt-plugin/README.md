# tools/chatgpt-plugin

The ChatGPT plugin package for Kettle (DECISIONS 358; `docs/chatgpt-plugin-brief.md`).
It describes the MCP server the product already runs; nothing here is served, and
nothing here changes a tool, its copy, or the OAuth server.

- `kettle/plugin.json`: the manifest, with the ChatGPT interface block under
  `extensions."com.openai.interface"`. Every string a person reads is the PM's copy
  (brief §3, verbatim) and is scanned against the site's copy-law ban lists by
  `product/tests/test_chatgpt_plugin.py`.
- `kettle/mcp.json`: one server, `kettle`, streamable HTTP at
  `https://api.heykettle.com/mcp`. No auth fields: OAuth is discovered from the
  server's own `/.well-known` documents.
- `kettle/assets/logo.png`: a copy of `webapp/public/icon-512.png`.
- `make-zip.sh`: builds `dist/kettle-plugin-<version>.zip` containing the `kettle/`
  folder and nothing beside it. `dist/` is gitignored.

The domain challenge the directory asks for is served by the product:
`GET /.well-known/openai-apps-challenge` returns the `OPENAI_APPS_CHALLENGE` Fly
secret as bare text, or 404 while the secret is unset.
