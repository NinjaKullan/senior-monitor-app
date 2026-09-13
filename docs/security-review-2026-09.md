# Security review — 2026-09 (the assistant door, the two token routes, migrations 0029–0033)

Read-only adversarial review, requested by the PM. The threat model is an
attacker with the public docs (spec 019, the discovery documents, the OAuth
flow) and a free Claude account — someone who can register a client, connect
their own circle, and send crafted requests to the public routes.

**Scope reviewed.** `product/kettle/assistant_auth.py`,
`product/kettle/assistant_tools.py` (the write tools especially), the `/d/{token}`
and `/s/{slug}/claim` routes in `product/kettle/main.py` and
`product/kettle/setup_page.py`, migrations 0029–0033 (RLS, grants, SECURITY
DEFINER functions, the view), and the 0032 reply trigger.

**Method.** Sixteen reproductions in `docs/security-review-2026-09-tests.py`, run
against a real Postgres (RLS and the definer functions actually apply — the
`authed` connection does `set role authenticated` and presents a Supabase-shaped
JWT). Fifteen `safe_*` tests pass by showing an attack fails; one `finding_*`
test passes by demonstrating the one vulnerable behaviour. Run: copy the file
into `product/tests/` and `KETTLE_REQUIRE_POSTGRES=1 pytest` it (it lives under
`docs/` so CI does not collect it). All sixteen pass on `668f44e`.

**Verdict.** One finding worth fixing: an **unauthenticated blind SSRF** through
the CIMD `client_id` on `/oauth/authorize` and `/oauth/token` (F1, Medium).
Everything else the PM asked about holds: a read-only grant cannot write, one
person's token cannot reach another circle, a removed member cannot write, the
CIMD shipped copy cannot redirect a code, PKCE and the loopback rule cannot be
bypassed, the claim route cannot hand out another parent's token, `authenticated`
cannot read or write `household_pings` or `journal_entries` past RLS, the flood
counters degrade sanely, and nothing logs a token, a hash, a body, or a raw IP.

---

## Findings

| # | Severity | What | Where |
|---|---|---|---|
| F1 | Medium | Unauthenticated blind SSRF: the server fetches any `https://` host named as a `client_id` | `assistant_auth.py:269`, `:307`, `:548`; `main.py:451–452` |
| O1 | Low (accepted) | `X-Forwarded-For` fallback lets a caller pick the rate-limit / ping-hash key if the Fly proxy is ever bypassed | `main.py:59` |
| O2 | Low | `memory`'s `since` is passed unvalidated to a `::date` cast; a bad value returns a DB-error tool result instead of a sentence | `assistant_tools.py` `memory_for` |

---

## F1 — Unauthenticated blind SSRF via a CIMD `client_id` (Medium)

**What.** Client ID Metadata Documents let a client identify itself by an
`https://` URL that Kettle fetches (spec 019 §4, DECISIONS 319). `is_cimd_client_id`
accepts any string that starts with `https://` (`assistant_auth.py:269`), and
`ClientDocuments._live` fetches it directly with no host allowlist and no
private-address check (`assistant_auth.py:307`, the `self._client.get(client_id)`
at `:312`). Both `/oauth/authorize` (`main.py:451`) and `/oauth/token`
(`main.py:452`) reach it through `client_for` (`assistant_auth.py:548`, called at
`:577` and `:675`), and both are **unauthenticated** — no session, no bearer, no
rate limit on any `/oauth/*` route. So an attacker sends:

```
GET /oauth/authorize?client_id=https://[fdaa:0:1::3]:4280/x&redirect_uri=https://claude.ai/cb
      &response_type=code&code_challenge=c&code_challenge_method=S256
```

and the server issues a GET to that internal address. The response is not
reflected (the caller gets a generic `invalid_client`), so it is a **blind**
SSRF, and httpx 0.28 does not follow redirects by default, so there is no
redirect pivot. What remains is real: an unauthenticated party can make the Fly
machine open connections to arbitrary hosts — link-local metadata addresses, the
6PN internal network — and distinguish reachable from filtered by timing and
error class. There is no per-host cap, so it doubles as an outbound-request
amplifier (only a *failed* fetch is remembered, for ten minutes; a novel host is
always fetched).

**Reproduction.** `test_finding_cimd_client_id_makes_the_server_fetch_any_https_host`.
A recording transport stands in for the httpx client the app builds in
production (`assistant_auth.py:281`, `client or httpx.Client(...)` — with nothing
injected, prod uses the real client and the request goes on the wire). The test
drives `/oauth/authorize` with `client_id=https://[fdaa:0:1::3]:4280/internal/secrets`
and `/oauth/token` with `client_id=https://169.254.169.254/latest/`, and asserts
the server reached out to each while returning only a harmless `invalid_client`.

**Severity: Medium.** Unauthenticated and needs nothing but a public URL, which
argues up; blind, `https`-only (many internal services are plain HTTP), and
no redirect-following, which argue down. It exposes internal-network reachability
and an unmetered outbound-fetch primitive, not data directly.

**Smallest fix.** Guard the fetch, not the feature. Before `_live` fetches,
resolve the host and refuse any address that is loopback, link-local, private, or
unique-local; keep `https`-only. About ten lines in `ClientDocuments._live`:

```python
import ipaddress, socket
from urllib.parse import urlsplit

def _fetchable(url: str) -> bool:
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        return False
    try:
        infos = socket.getaddrinfo(parts.hostname, parts.port or 443)
    except socket.gaierror:
        return False
    for *_, sockaddr in infos:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False
    return True
```

Call it at the top of `_live`; a refused host returns `(None, "host not allowed")`
so the shipped copy still stands for known clients and DCR still covers everyone
else. (There is a TOCTOU gap between resolve and connect that a determined
attacker with DNS control can still exploit; a stricter alternative the PM may
prefer is an **allowlist of CIMD hosts** — in practice only `claude.ai` connects
by CIMD today, and Codex connects by DCR with a loopback redirect, so an allowlist
costs nothing operationally.) Either way, add the guard before the deploy that
turns CIMD on for a stranger; today only the founder has connected.

This is a fix for the PM to rule on, not applied here.

---

## The questions, each answered with its test

**Can a read-only grant write?** No. `add_note_for` and `reply_for` both begin
`if not can_write(grant.get("scope")): return NEED_WRITE`, and the grant's scope
is fixed at authorize time by `normalise_scope` (write must be asked for; an
unknown scope is refused outright) and echoed unchanged through refresh.
`test_safe_read_only_grant_cannot_write`: a read grant gets `NEED_WRITE` from both
tools and zero rows land.

**Can one person's token reach another circle's data?** No. Every tool derives the
caller's circles from `members` at call time keyed on the resolved
`auth_user_id` (`circles_for`), never from the grant, and every read is scoped to
that set. `test_safe_token_sees_only_its_own_circle`: user A's token lists only
A's parent, cannot name B's parent, and a write A aims at B's parent by name lands
nothing in B's family.

**Can a removed member still write?** No. Removal does not revoke the token (by
design, 013/015), but `member_for` reads the seat at call time; with no seat the
write returns a sentence and nothing lands.
`test_safe_removed_member_cannot_write`.

**Can the CIMD shipped copy be abused to redirect a code?** No. The shipped copy
pins Claude's `redirect_uris` to the one public callback, and `authorize` refuses
a `redirect_uri` that is not an exact (or loopback-port) match before any code is
minted. `test_safe_cimd_shipped_copy_pins_the_redirect`. (A live document that
*differs* from the shipped copy wins, per DECISIONS 320 — but only `claude.ai`
answers for `claude.ai`'s URL, so this is not attacker-reachable.)

**Can PKCE or the loopback rule be bypassed?** No. `authorize` requires
`code_challenge` with `S256` or it refuses; `exchange_code` fails unless
`pkce_matches(verifier, challenge)`. The loopback port-ignore in `redirect_allowed`
applies only when both the request and a registered URI are `http` loopback, so a
client registered with an `https` callback cannot pivot to `http://127.0.0.1`.
`test_safe_pkce_is_required_and_verifier_is_checked`,
`test_safe_loopback_exemption_only_helps_loopback_registrations`.

**Can the claim route hand out a token for someone else's parent?** No. The 144-bit
slug is the only identity in the URL; a guessed slug is a 404, and the real slug
returns the link's own parent's token and no other. Non-Android links are refused
(DECISIONS 331). `test_safe_claim_needs_the_secret_slug_and_returns_only_that_parents_token`.
Reinstalls minting fresh tokens for the same parent are within the trust model —
whoever holds the slug already holds that parent's setup link (330: a claim never
revokes; the founder revokes).

**Can `household_pings` or `journal_entries` be written or read past RLS by
`authenticated`?** No. `household_devices` carries no grant at all (the table
raises `InsufficientPrivilege` for `authenticated`); `household_pings` grants
`SELECT` only, scoped by `app_household_device_ids()` to the caller's circles, and
the read surface is the token-free view. `journal_entries` grants `SELECT, INSERT`
bounded by per-family policies, and the 0032 trigger overrides `author_member_id`
from the JWT so a browser client cannot forge authorship.
`test_safe_authenticated_cannot_write_household_pings`,
`test_safe_authenticated_cannot_read_another_circles_devices_or_pings`,
`test_safe_authenticated_cannot_touch_another_familys_journal`,
`test_safe_a_browser_client_cannot_forge_journal_authorship`.

**Can the flood counters be starved?** Not in the attacker's favour. Evicting a
key by rotating others only *resets* the evicted key; it never lets a blocked key
send more from its own key. The real limit is the key itself — see O1.
`test_flood_counter_keying_and_eviction`.

**Does anything log a token, a hash, a body, or an IP?** No. The Dockerfile runs
uvicorn with `--no-access-log`, so request URLs (which carry slugs and tokens) are
never logged in production. Kettle's own loggers log the slug only as its masked
last six characters (`setup_page.py:735`), never the full slug or a device token,
and the OAuth flow logs no access or refresh token and no hash. The ping path
hashes the IP (salted, truncated) before storage and the household route reads no
IP at all. `test_safe_ping_and_claim_do_not_log_the_token_or_slug`,
`test_safe_oauth_token_exchange_logs_no_token`. (In the test harness the full
token appears once — in the *TestClient's own* httpx request line, which uvicorn's
`--no-access-log` suppresses in production; the test asserts the leaking record is
never one of kettle's own.)

---

## Observations (not exploitable as shipped)

**O1 — the client-IP source (Low, accepted).** `_client_ip` (`main.py:59`) reads
`Fly-Client-IP` first, then falls back to `X-Forwarded-For`, then the socket. In
production kettle-api sits behind Fly, which sets `Fly-Client-IP`, so the
fallback never runs and the key is trustworthy. If the app were ever exposed
without that proxy, both the flood-counter key and the hashed ping IP would become
caller-controllable, letting a caller mint a fresh rate-limit bucket per request.
This is the trust assumption DECISIONS 307/308 took knowingly, with the 50,000-row
table cap as the backstop. Worth a comment naming the dependency; no change needed
while Fly fronts the app. `test_flood_counter_keying_and_eviction` shows the
per-key bypass a spoofable key would give.

**O2 — `memory`'s `since` is unvalidated (Low).** `parent_day` floors and bounds
its date argument, but `memory` passes `since` straight into a `%s::date` cast. A
value like `"not-a-date"` raises inside the tool and comes back as a DB-error tool
result rather than one of Kettle's sentences (§7 says expected cases are
sentences). No injection (the value is parameterised) and no data crosses a circle
boundary (the query is still scoped by the caller's circles); the connection is
autocommit so no transaction is poisoned. Purely a robustness and copy-law nit:
validate `since` the way `parent_day` validates its date, or catch the cast and
return `DAY_NOTHING`-style text. `test_low_memory_since_is_unvalidated`.

---

## Notes for the PM

- F1 is the only item that changes behaviour to fix, and it is a rule for the PM:
  the SSRF guard (or the host allowlist) is not applied here. It should land
  before CIMD is relied on for any stranger family; today only the founder has
  connected, and Claude connects by CIMD while Codex connects by DCR.
- The reproductions are in `docs/security-review-2026-09-tests.py`. They are
  evidence, not a suite addition — CI does not collect `docs/`. When F1 is fixed,
  invert `test_finding_*` to assert the fetch is refused and move the file into
  `product/tests/`.
- Nothing in scope was changed on `main`. This report and its test file are the
  only additions.
