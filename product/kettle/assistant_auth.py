"""The authorization server behind /mcp (spec 019 §4).

kettle-api issues its own tokens to assistants on top of the family's
existing sign-in: an assistant registers itself (RFC 7591), sends the person
to /oauth/authorize with a PKCE S256 challenge, Kettle parks that request
and hands the person to the webapp's /connect page, the webapp posts Allow
to /oauth/approve with the person's Supabase session, and the assistant
swaps the resulting one-time code for tokens at /oauth/token.

Fixed points, none of them choices: PKCE S256 on every authorize; redirect
URIs matched exactly except loopback, where the port is ignored; codes
single use and ten minutes; access tokens one hour; refresh tokens rotated
on every use, a grant unused ninety days expiring with invalid_grant; every
token stored as a sha256 hash and never plain; discovery, register and
token make no upstream call. The one upstream call in this module is the
JWKS fetch inside /oauth/approve, cached and refetched on an unknown kid.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import httpx
import jwt
import psycopg
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from kettle.assistant_copy import ASSISTANT_FALLBACK
from kettle.timeutil import now_utc

log = logging.getLogger("kettle.assistant")

SCOPE = "kettle:read"
#: Spec 019 Amendment A: notes and replies through the door. Implies read.
SCOPE_WRITE = "kettle:write"
SCOPES = (SCOPE, SCOPE_WRITE)


def normalise_scope(requested: str | None) -> str | None:
    """The scope a request gets: read by default; write implies read; any
    part outside the two offered is refused (None)."""
    parts = (requested or SCOPE).split()
    if any(part not in SCOPES for part in parts):
        return None
    return SCOPE_WRITE if SCOPE_WRITE in parts else SCOPE


def can_write(scope: str | None) -> bool:
    return SCOPE_WRITE in (scope or "").split()


CODE_LIFE = timedelta(minutes=10)
ACCESS_LIFE = timedelta(hours=1)
REFRESH_LIFE = timedelta(days=90)
REQUEST_SWEEP = timedelta(hours=1)
CLAUDE_CALLBACK = "https://claude.ai/api/mcp/auth_callback"
#: Client ID Metadata Documents (CIMD): a client_id that is an https URL
#: names a JSON document the client hosts; its redirect_uris and client_name
#: are the registration, so no row is created per connect.
CIMD_TIMEOUT = 5.0
CIMD_CACHE_LIFE = timedelta(hours=1)
#: A failed fetch is remembered this long (DECISIONS 319): a burst of
#: connects must not hammer the client's edge, and the shipped copy stands
#: for the duration.
CIMD_FAILURE_LIFE = timedelta(minutes=10)
#: Where a client document may live (brief 358 §7, ruled by the PM). Trust
#: is per host prefix, not per exact URL: ChatGPT mints one document per app
#: under chatgpt.com/oauth/, so an exact-key allowlist refused the real
#: connect. A client_id under one of these prefixes is fetched live; anything
#: else is never fetched, which is the F1 guarantee (`is_cimd_client_id`).
#: A module constant, not a setting: the list is two names and a change to
#: it is a ruling.
TRUSTED_CLIENT_DOCUMENT_PREFIXES: tuple[str, ...] = (
    "https://claude.ai/oauth/",
    "https://chatgpt.com/oauth/",
)

#: Pinned client documents, keyed by client_id URL, in the shape _parse_cimd
#: returns (DECISIONS 319). claude.ai's edge answers Kettle's fetch of
#: Claude's document with a Cloudflare challenge from the Fly machine; the
#: redirect address is the one thing a document decides, and it is public.
#: The live fetch still wins when it works; the pinned copy stands when it
#: does not. Every key is under a trusted prefix above (a test holds it): a
#: pin is a fallback for a document already trusted, never a way in.
#: Claude's, as fetched Sep 8 2026.
KNOWN_CLIENT_DOCUMENTS: dict[str, dict[str, Any]] = {
    "https://claude.ai/oauth/mcp-oauth-client-metadata": {
        "client_id": "https://claude.ai/oauth/mcp-oauth-client-metadata",
        "client_name": "Claude",
        "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
    },
    #: ChatGPT's, as fetched Oct 3 2026 (DECISIONS 359 follow-up 1). The
    #: document names private_key_jwt as its preferred token auth and lists
    #: `none` as supported; Kettle advertises `none`, so ChatGPT uses PKCE.
    "https://chatgpt.com/oauth/client.json": {
        "client_id": "https://chatgpt.com/oauth/client.json",
        "client_name": "ChatGPT",
        "redirect_uris": ["https://chatgpt.com/connector_platform_oauth_redirect"],
    },
    #: ChatGPT's per-app document for Kettle (brief 358 §7), the one its
    #: Connect step actually sends; as fetched Oct 4 2026 by the founder in
    #: Safari. It lists token_endpoint_auth_methods_supported `none` and
    #: `private_key_jwt`; Kettle advertises `none`, unchanged.
    "https://chatgpt.com/oauth/A1YFUC1zmNdF/client.json": {
        "client_id": "https://chatgpt.com/oauth/A1YFUC1zmNdF/client.json",
        "client_name": "ChatGPT",
        "redirect_uris": ["https://chatgpt.com/connector/oauth/A1YFUC1zmNdF"],
    },
}


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def new_token() -> str:
    return secrets.token_urlsafe(32)


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def pkce_matches(verifier: str, challenge: str) -> bool:
    return secrets.compare_digest(
        _b64url(hashlib.sha256(verifier.encode("ascii")).digest()), challenge
    )


def redirect_allowed(registered: list[str], requested: str) -> bool:
    """Exact match, except loopback where the port is ignored (Claude Code)."""
    if requested in registered:
        return True
    parts = urlsplit(requested)
    if parts.scheme != "http" or parts.hostname not in ("localhost", "127.0.0.1"):
        return False
    for uri in registered:
        reg = urlsplit(uri)
        if (
            reg.scheme == "http"
            and reg.hostname == parts.hostname
            and reg.path == parts.path
            and reg.query == parts.query
        ):
            return True
    return False


def with_query(url: str, params: dict[str, str]) -> str:
    parts = urlsplit(url)
    existing = parse_qs(parts.query, keep_blank_values=True)
    merged = {k: v[0] for k, v in existing.items()}
    merged.update({k: v for k, v in params.items() if v is not None})
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(merged), parts.fragment))


# --- discovery (§4) ------------------------------------------------------------

#: The API answers on both hosts indefinitely (DECISIONS 357): every forged
#: shortcut and every connector added before the move names the old one.
#: Discovery is built from the host a request arrived on, so the protected
#: resource's `resource` equals the MCP URL the person typed, whichever host
#: that was (brief 358 §2). Any other Host falls back to `public_base_url`.
LEGACY_API_HOSTS: frozenset[str] = frozenset({"kettle-api.fly.dev"})


def api_hosts(public_base_url: str) -> frozenset[str]:
    """The hosts this API is reachable on: the issuer's plus the legacy ones."""
    own = urlsplit(public_base_url).hostname or ""
    return LEGACY_API_HOSTS | ({own} if own else frozenset())


def base_for(public_base_url: str, host: str | None) -> str:
    """The base URL to build discovery from: the request's own host when it
    is one of ours (always https; Fly terminates TLS), else the issuer."""
    name = (host or "").split(":", 1)[0].strip().lower()
    if name and name in api_hosts(public_base_url):
        return f"https://{name}"
    return public_base_url


def mcp_resources(public_base_url: str) -> frozenset[str]:
    """Every MCP URL a `resource` parameter may name (RFC 8707): one per host."""
    return frozenset(f"https://{host}/mcp" for host in api_hosts(public_base_url))


def normalise_resource(value: str | None) -> str | None:
    """A `resource` parameter as compared: trimmed, no trailing slash; absent is None."""
    cleaned = (value or "").strip().rstrip("/")
    return cleaned or None


def protected_resource_metadata(base: str, issuer: str | None = None) -> dict[str, Any]:
    """RFC 9728, per host: `resource` is this host's MCP URL, and the
    authorization server is the one issuer whichever host answered."""
    return {
        "resource": f"{base}/mcp",
        "authorization_servers": [issuer or base],
        "scopes_supported": list(SCOPES),
        "bearer_methods_supported": ["header"],
    }


def authorization_server_metadata(base: str) -> dict[str, Any]:
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "registration_endpoint": f"{base}/oauth/register",
        "scopes_supported": list(SCOPES),
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "client_id_metadata_document_supported": True,
    }


def www_authenticate(base: str) -> str:
    """The 401 header on /mcp, verbatim (§4)."""
    return f'Bearer resource_metadata="{base}/.well-known/oauth-protected-resource"'


# --- the Supabase session check (§4, PM update: ES256 via JWKS only) -----------


class JwksVerifier:
    """Verify a Supabase access token against the project's JWKS.

    Fetched once and cached; refetched when a token names a kid the cache
    does not hold, and never more than once per verification. ES256 (the
    project's ECC P-256 key) is what kettle-prod signs with; the algorithm
    list is what the JWKS advertises, so a key rotation is a refetch, not a
    deploy.
    """

    def __init__(self, jwks_url: str, client: httpx.Client | None = None) -> None:
        self._url = jwks_url
        self._client = client or httpx.Client(timeout=5.0)
        self._keys: dict[str, jwt.PyJWK] = {}

    def _refetch(self) -> None:
        response = self._client.get(self._url)
        response.raise_for_status()
        keys: dict[str, jwt.PyJWK] = {}
        for entry in response.json().get("keys", []):
            try:
                keys[entry.get("kid", "")] = jwt.PyJWK(entry)
            except jwt.PyJWKError:  # pragma: no cover - a malformed entry is skipped
                continue
        self._keys = keys

    def subject(self, token: str) -> str | None:
        """The verified `sub`, or None for anything that does not check out."""
        if not self._url:
            return None
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError:
            return None
        kid = header.get("kid", "")
        if kid not in self._keys:
            try:
                self._refetch()
            except (httpx.HTTPError, ValueError):
                log.warning("assistant: JWKS fetch failed")
                return None
        key = self._keys.get(kid)
        if key is None:
            return None
        try:
            # ES256 and nothing else (PM, Sep 5): the algorithm list is
            # fixed here, never read from the token, so a token claiming
            # another algorithm against this key is refused rather than
            # confused.
            claims = jwt.decode(token, key.key, algorithms=["ES256"], options={"verify_aud": False})
        except jwt.PyJWTError:
            return None
        sub = claims.get("sub")
        return str(sub) if sub else None


# --- storage -------------------------------------------------------------------


@dataclass(frozen=True)
class Tokens:
    access_token: str
    refresh_token: str
    expires_in: int
    scope: str = SCOPE


def register_client(conn: psycopg.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    uris = payload.get("redirect_uris")
    if not isinstance(uris, list) or not uris or not all(isinstance(u, str) and u for u in uris):
        raise ValueError("invalid_redirect_uri")
    name = payload.get("client_name")
    client_name = name.strip()[:120] if isinstance(name, str) and name.strip() else None
    client_id = "kc_" + secrets.token_urlsafe(16)
    now = now_utc()
    conn.execute(
        "insert into assistant_clients (client_id, client_name, redirect_uris, created_utc) "
        "values (%s, %s, %s, %s)",
        (client_id, client_name, uris, now),
    )
    return {
        "client_id": client_id,
        "client_id_issued_at": int(now.timestamp()),
        "client_name": client_name,
        "redirect_uris": uris,
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "scope": " ".join(SCOPES),
    }


def client_row(conn: psycopg.Connection, client_id: str) -> dict[str, Any] | None:
    return conn.execute(
        "select client_id, client_name, redirect_uris from assistant_clients where client_id = %s",
        (client_id,),
    ).fetchone()


def is_cimd_client_id(client_id: str) -> bool:
    """A CIMD client is one whose document lives under a trusted prefix
    (brief 358 §7, widening DECISIONS 336).

    CIMD is closed to unknown hosts, not to unknown URLs: a `client_id` that
    starts with one of TRUSTED_CLIENT_DOCUMENT_PREFIXES is a CIMD client and
    its document is fetched live (`ClientDocuments`), with the pinned copy in
    KNOWN_CLIENT_DOCUMENTS standing when the fetch fails and one exists. 336
    keyed this on the exact pinned URLs; ChatGPT mints a document per app
    under chatgpt.com/oauth/, so the real connect was refused. Every other
    `https://` id is an unknown client — `client_for` returns None and
    fetches nothing, the same silence an unknown `kc_` id gets — so an
    attacker still cannot make kettle-api fetch an arbitrary URL from the
    unauthenticated `/oauth/authorize` and `/oauth/token` routes (the F1
    SSRF, `docs/security-review-2026-09.md`): nothing outside the two hosts
    is ever reached. DCR stays open to everyone."""
    return client_id.startswith(TRUSTED_CLIENT_DOCUMENT_PREFIXES)


class ClientDocuments:
    """CIMD documents, fetched once an hour per client_id and never on the
    token path's hot loop. Order (DECISIONS 319): a cached good copy, then
    the live fetch, then the shipped copy for that URL, then None
    (invalid_client). A failed fetch is remembered for CIMD_FAILURE_LIFE and
    the shipped copy stands for that time."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=CIMD_TIMEOUT)
        self._cache: dict[str, tuple[datetime, dict[str, Any]]] = {}
        self._failed: dict[str, datetime] = {}

    def fetch(self, client_id: str, now: datetime) -> dict[str, Any] | None:
        cached = self._cache.get(client_id)
        if cached is not None and now - cached[0] < CIMD_CACHE_LIFE:
            return cached[1]
        failed = self._failed.get(client_id)
        if failed is not None and now - failed < CIMD_FAILURE_LIFE:
            return KNOWN_CLIENT_DOCUMENTS.get(client_id)
        parsed, why = self._live(client_id)
        if parsed is not None:
            self._cache[client_id] = (now, parsed)
            self._failed.pop(client_id, None)
            return parsed
        self._failed[client_id] = now
        shipped = KNOWN_CLIENT_DOCUMENTS.get(client_id)
        log.warning(
            "assistant: client document at %s refused: %s; %s",
            client_id,
            why,
            "using the shipped copy" if shipped else "no shipped copy",
        )
        return shipped

    def _live(self, client_id: str) -> tuple[dict[str, Any] | None, str]:
        """The parsed live document, or None and the reason in words: the
        status and content type when there was a response, the exception
        class when there was not."""
        try:
            response = self._client.get(
                client_id, headers={"accept": "application/json"}, timeout=CIMD_TIMEOUT
            )
        except httpx.HTTPError as exc:
            return None, type(exc).__name__
        why = f"{response.status_code} {response.headers.get('content-type', '')}".strip()
        if response.status_code != 200:
            return None, why
        try:
            document = response.json()
        except ValueError:
            return None, f"{why} (not JSON)"
        parsed = _parse_cimd(client_id, document)
        if parsed is None:
            return None, f"{why} (does not describe {client_id})"
        return parsed, why


def _parse_cimd(client_id: str, document: Any) -> dict[str, Any] | None:
    if not isinstance(document, dict) or document.get("client_id") != client_id:
        return None
    uris = document.get("redirect_uris")
    if not isinstance(uris, list) or not uris or not all(isinstance(u, str) and u for u in uris):
        return None
    name = document.get("client_name")
    client_name = name.strip()[:120] if isinstance(name, str) and name.strip() else None
    return {"client_id": client_id, "client_name": client_name, "redirect_uris": uris}


def mirror_client(conn: psycopg.Connection, client: dict[str, Any], now: datetime) -> None:
    """One assistant_clients row per CIMD client_id, keyed by the URL and
    refreshed from the document — never a row per connect. The requests and
    grants tables reference assistant_clients, and a revoke cascades the way
    it does for a registered client."""
    conn.execute(
        """
        insert into assistant_clients (client_id, client_name, redirect_uris, created_utc)
        values (%s, %s, %s, %s)
        on conflict (client_id) do update
            set client_name = excluded.client_name, redirect_uris = excluded.redirect_uris
        """,
        (client["client_id"], client["client_name"], client["redirect_uris"], now),
    )


def sweep_requests(conn: psycopg.Connection, now: datetime) -> None:
    conn.execute("delete from assistant_requests where created_utc < %s", (now - REQUEST_SWEEP,))


def create_request(
    conn: psycopg.Connection,
    client: dict[str, Any],
    redirect_uri: str,
    code_challenge: str,
    state: str | None,
    now: datetime,
    scope: str = SCOPE,
    resource: str | None = None,
) -> str:
    row = conn.execute(
        """
        insert into assistant_requests
            (client_id, client_name, redirect_uri, code_challenge, state, scope,
             created_utc, expires_utc, resource)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s) returning id
        """,
        (
            client["client_id"],
            client["client_name"],
            redirect_uri,
            code_challenge,
            state,
            scope,
            now,
            now + CODE_LIFE,
            resource,
        ),
    ).fetchone()
    return str(row["id"])


def request_row(conn: psycopg.Connection, request_id: str) -> dict[str, Any] | None:
    try:
        return conn.execute(
            "select * from assistant_requests where id = %s", (request_id,)
        ).fetchone()
    except psycopg.DataError:
        return None


def approve_request(
    conn: psycopg.Connection, request_id: str, auth_user_id: str, now: datetime
) -> str | None:
    """Mint the one-time code for a pending, unexpired request. None if it
    is gone, expired or already answered."""
    code = new_token()
    row = conn.execute(
        """
        update assistant_requests
        set auth_user_id = %s, code_hash = %s, expires_utc = %s
        where id = %s and auth_user_id is null and used_utc is null and expires_utc > %s
        returning id
        """,
        (auth_user_id, sha256(code), now + CODE_LIFE, request_id, now),
    ).fetchone()
    return code if row else None


def _issue(conn: psycopg.Connection, grant_id: Any, now: datetime) -> Tokens:
    access, refresh = new_token(), new_token()
    conn.execute(
        """
        update assistant_grants
        set access_token_hash = %s, access_expires_utc = %s,
            refresh_token_hash = %s, refresh_expires_utc = %s, last_used_utc = %s
        where id = %s
        """,
        (sha256(access), now + ACCESS_LIFE, sha256(refresh), now + REFRESH_LIFE, now, grant_id),
    )
    scope = conn.execute(
        "select scope from assistant_grants where id = %s", (grant_id,)
    ).fetchone()["scope"]
    return Tokens(access, refresh, int(ACCESS_LIFE.total_seconds()), scope)


class ResourceMismatch(Exception):
    """RFC 8707: the token request names a `resource` other than the one the
    authorize request (or the grant) was bound to. Its own class so the
    token endpoint can answer `invalid_target` rather than `invalid_grant`."""


def _resource_matches(bound: str | None, asked: str | None) -> bool:
    """A request bound to no resource accepts any; a bound one must be
    named again exactly (compared normalised)."""
    return normalise_resource(bound) is None or normalise_resource(bound) == normalise_resource(
        asked
    )


def exchange_code(
    conn: psycopg.Connection,
    code: str,
    verifier: str,
    client_id: str,
    redirect_uri: str,
    now: datetime,
    resource: str | None = None,
) -> Tokens | None:
    row = conn.execute(
        """
        update assistant_requests set used_utc = %s
        where code_hash = %s and used_utc is null and auth_user_id is not null
          and expires_utc > %s and client_id = %s and redirect_uri = %s
        returning *
        """,
        (now, sha256(code), now, client_id, redirect_uri),
    ).fetchone()
    if row is None or not pkce_matches(verifier, row["code_challenge"]):
        return None
    # The code is spent either way (fail closed, the wrong-verifier posture):
    # a mismatch here is a different client's exchange, not a retry.
    if not _resource_matches(row["resource"], resource):
        raise ResourceMismatch
    grant = conn.execute(
        """
        insert into assistant_grants
            (auth_user_id, client_id, client_name, created_utc, last_used_utc,
             access_token_hash, access_expires_utc, refresh_token_hash, refresh_expires_utc,
             scope, resource)
        values (%s, %s, %s, %s, %s, 'pending', %s, 'pending', %s, %s, %s) returning id
        """,
        (
            row["auth_user_id"],
            row["client_id"],
            row["client_name"],
            now,
            now,
            now,
            now,
            row["scope"],
            normalise_resource(row["resource"]),
        ),
    ).fetchone()
    return _issue(conn, grant["id"], now)


def refresh_grant(
    conn: psycopg.Connection,
    refresh_token: str,
    client_id: str,
    now: datetime,
    resource: str | None = None,
) -> Tokens | None:
    """Rotate: the old refresh token dies in the same statement the new one
    is issued. Unused ninety days, revoked, or unknown: None. A grant bound
    to a resource (RFC 8707) refuses a refresh that names a different one."""
    row = conn.execute(
        """
        select id, resource from assistant_grants
        where refresh_token_hash = %s and client_id = %s and revoked_utc is null
          and refresh_expires_utc > %s
        """,
        (sha256(refresh_token), client_id, now),
    ).fetchone()
    if row is None:
        return None
    if not _resource_matches(row["resource"], resource):
        raise ResourceMismatch
    return _issue(conn, row["id"], now)


def resolve_grant(conn: psycopg.Connection, token: str, now: datetime) -> dict[str, Any] | None:
    """The grant an access token stands for — who, what scope, which client
    (Amendment A) — or None."""
    row = conn.execute(
        """
        update assistant_grants set last_used_utc = %s
        where access_token_hash = %s and revoked_utc is null and access_expires_utc > %s
        returning id, auth_user_id, scope, client_name
        """,
        (now, sha256(token), now),
    ).fetchone()
    if row is None:
        return None
    return {
        "id": str(row["id"]),
        "auth_user_id": str(row["auth_user_id"]),
        "scope": row["scope"],
        "client_name": row["client_name"],
    }


def resolve_bearer(conn: psycopg.Connection, token: str, now: datetime) -> str | None:
    """The auth_user_id an access token stands for, or None."""
    grant = resolve_grant(conn, token, now)
    return grant["auth_user_id"] if grant else None


# --- the routes ------------------------------------------------------------------


def _oauth_error(error: str, description: str = "", status: int = 400) -> JSONResponse:
    body: dict[str, str] = {"error": error}
    if description:
        body["error_description"] = description
    return JSONResponse(body, status_code=status, headers={"cache-control": "no-store"})


async def _token_body(request: Request) -> dict[str, str]:
    """The token request's parameters. Claude posts
    `application/x-www-form-urlencoded` (RFC 6749 §4.1.3) and ChatGPT may
    post JSON (brief 358 §4); both are read, and anything that is not a flat
    object of strings is an empty request rather than an exception."""
    raw = (await request.body()).decode("utf-8", errors="replace")
    if request.headers.get("content-type", "").split(";", 1)[0].strip() == "application/json":
        try:
            payload = json.loads(raw)
        except ValueError:
            return {}
        if not isinstance(payload, dict):
            return {}
        return {k: v for k, v in payload.items() if isinstance(k, str) and isinstance(v, str)}
    return {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}


class OAuthRoutes:
    """The handlers, bound to a pool factory, the public base and the app origin."""

    def __init__(
        self,
        base: str,
        app_origin: str,
        verifier: JwksVerifier,
        clock: Callable[[], datetime] = now_utc,
        documents: ClientDocuments | None = None,
    ) -> None:
        self.base = base
        self.app_origin = app_origin
        self.verifier = verifier
        self.clock = clock
        self.documents = documents or ClientDocuments()
        #: RFC 8707: the MCP URLs a `resource` parameter may name, one per
        #: host the API answers on (DECISIONS 357). Anything else is
        #: `invalid_target`, the error the RFC names for it.
        self.resources = mcp_resources(base)

    def client_for(self, conn: psycopg.Connection, client_id: str) -> dict[str, Any] | None:
        """A registered client by its kc_ id, or a CIMD client by its URL."""
        if not is_cimd_client_id(client_id):
            return client_row(conn, client_id)
        client = self.documents.fetch(client_id, self.clock())
        if client is not None:
            mirror_client(conn, client, self.clock())
        return client

    async def register(self, request: Request) -> JSONResponse:
        try:
            payload = await request.json()
        except ValueError:
            return _oauth_error("invalid_client_metadata")
        if not isinstance(payload, dict):
            return _oauth_error("invalid_client_metadata")
        with request.app.state.pool.connection() as conn:
            try:
                registered = register_client(conn, payload)
            except ValueError as exc:
                return _oauth_error(str(exc))
        return JSONResponse(registered, status_code=201, headers={"cache-control": "no-store"})

    async def authorize(self, request: Request):
        q = request.query_params
        client_id = q.get("client_id", "")
        redirect_uri = q.get("redirect_uri", "")
        state = q.get("state")
        with request.app.state.pool.connection() as conn:
            client = self.client_for(conn, client_id)
            if client is None:
                return _oauth_error("invalid_client")
            if not redirect_uri or not redirect_allowed(
                list(client["redirect_uris"]), redirect_uri
            ):
                # A redirect we do not trust is never redirected to.
                return _oauth_error("invalid_request", "redirect_uri does not match")

            def refuse(error: str, description: str) -> RedirectResponse:
                return RedirectResponse(
                    with_query(
                        redirect_uri,
                        {"error": error, "error_description": description, "state": state},
                    ),
                    status_code=302,
                )

            if q.get("response_type") != "code":
                return refuse("unsupported_response_type", "response_type must be code")
            challenge = q.get("code_challenge", "")
            if not challenge or q.get("code_challenge_method") != "S256":
                return refuse("invalid_request", "PKCE S256 is required")
            scope = normalise_scope(q.get("scope"))
            if scope is None:
                return refuse("invalid_scope", f"only {' and '.join(SCOPES)} are offered")
            # RFC 8707 (brief 358 §3): ChatGPT names the MCP URL it is
            # connecting to. Absent is fine (Claude sends none); present, it
            # must be one of this API's MCP URLs and is bound to the request,
            # so the token exchange can refuse a different one.
            resource = normalise_resource(q.get("resource"))
            if resource is not None and resource not in self.resources:
                return refuse("invalid_target", "resource is not this server's MCP URL")
            now = self.clock()
            sweep_requests(conn, now)
            request_id = create_request(
                conn, client, redirect_uri, challenge, state, now, scope, resource
            )
        return RedirectResponse(f"{self.app_origin}/connect?request={request_id}", status_code=302)

    async def approve(self, request: Request) -> JSONResponse:
        """Called by the webapp with the person's Supabase session (§4)."""
        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return _oauth_error("invalid_token", status=401)
        subject = self.verifier.subject(auth[7:].strip())
        if subject is None:
            return _oauth_error("invalid_token", status=401)
        try:
            payload = await request.json()
        except ValueError:
            return _oauth_error("invalid_request")
        request_id = str(payload.get("request_id", "")) if isinstance(payload, dict) else ""
        decision = payload.get("decision", "allow") if isinstance(payload, dict) else "allow"
        now = self.clock()
        with request.app.state.pool.connection() as conn:
            row = request_row(conn, request_id)
            if (
                row is None
                or row["used_utc"] is not None
                or row["expires_utc"] <= now
                or row["auth_user_id"]
            ):
                return JSONResponse({"error": "expired"}, status_code=410)
            if decision != "allow":
                conn.execute(
                    "update assistant_requests set used_utc = %s where id = %s", (now, row["id"])
                )
                return JSONResponse(
                    {
                        "redirect": with_query(
                            row["redirect_uri"], {"error": "access_denied", "state": row["state"]}
                        ),
                    }
                )
            code = approve_request(conn, request_id, subject, now)
        if code is None:
            return JSONResponse({"error": "expired"}, status_code=410)
        return JSONResponse(
            {"redirect": with_query(row["redirect_uri"], {"code": code, "state": row["state"]})}
        )

    async def pending(self, request: Request) -> JSONResponse:
        """What the consent screen shows: the client's name, or the fallback.
        No session needed — the request id is the capability, ten minutes long."""
        request_id = request.query_params.get("request", "")
        now = self.clock()
        with request.app.state.pool.connection() as conn:
            row = request_row(conn, request_id)
        if (
            row is None
            or row["used_utc"] is not None
            or row["expires_utc"] <= now
            or row["auth_user_id"]
        ):
            return JSONResponse({"error": "expired"}, status_code=410)
        return JSONResponse(
            {"client_name": row["client_name"] or ASSISTANT_FALLBACK, "scope": row["scope"]}
        )

    async def token(self, request: Request) -> JSONResponse:
        form = await _token_body(request)
        grant_type = form.get("grant_type", "")
        client_id = form.get("client_id", "")
        resource = normalise_resource(form.get("resource"))
        now = self.clock()
        with request.app.state.pool.connection() as conn:
            if self.client_for(conn, client_id) is None:
                return _oauth_error("invalid_client", status=401)
            # RFC 8707 at the token endpoint too: a `resource` that is not
            # one of this API's MCP URLs is `invalid_target` before any code
            # or refresh token is spent on it.
            if resource is not None and resource not in self.resources:
                return _oauth_error("invalid_target", "resource is not this server's MCP URL")
            try:
                if grant_type == "authorization_code":
                    tokens = exchange_code(
                        conn,
                        form.get("code", ""),
                        form.get("code_verifier", ""),
                        client_id,
                        form.get("redirect_uri", ""),
                        now,
                        resource,
                    )
                elif grant_type == "refresh_token":
                    tokens = refresh_grant(
                        conn, form.get("refresh_token", ""), client_id, now, resource
                    )
                else:
                    return _oauth_error("unsupported_grant_type")
            except ResourceMismatch:
                return _oauth_error("invalid_target", "resource differs from the authorization")
        if tokens is None:
            return _oauth_error("invalid_grant")
        return JSONResponse(
            {
                "access_token": tokens.access_token,
                "token_type": "bearer",
                "expires_in": tokens.expires_in,
                "refresh_token": tokens.refresh_token,
                "scope": tokens.scope,
            },
            headers={"cache-control": "no-store", "pragma": "no-cache"},
        )


def jwks_document_for(public_numbers_key: Any, kid: str) -> dict[str, Any]:
    """A JWKS carrying one ES256 public key — the test double for the project's
    document. Lives here so the tests build exactly what the verifier reads."""
    numbers = public_numbers_key.public_numbers()
    size = 32
    return {
        "keys": [
            {
                "kty": "EC",
                "crv": "P-256",
                "kid": kid,
                "alg": "ES256",
                "use": "sig",
                "x": _b64url(numbers.x.to_bytes(size, "big")),
                "y": _b64url(numbers.y.to_bytes(size, "big")),
            }
        ]
    }
