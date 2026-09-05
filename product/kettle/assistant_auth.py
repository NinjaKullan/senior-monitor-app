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
CODE_LIFE = timedelta(minutes=10)
ACCESS_LIFE = timedelta(hours=1)
REFRESH_LIFE = timedelta(days=90)
REQUEST_SWEEP = timedelta(hours=1)
CLAUDE_CALLBACK = "https://claude.ai/api/mcp/auth_callback"


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


def protected_resource_metadata(base: str) -> dict[str, Any]:
    return {
        "resource": f"{base}/mcp",
        "authorization_servers": [base],
        "scopes_supported": [SCOPE],
        "bearer_methods_supported": ["header"],
    }


def authorization_server_metadata(base: str) -> dict[str, Any]:
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "registration_endpoint": f"{base}/oauth/register",
        "scopes_supported": [SCOPE],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
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
        "scope": SCOPE,
    }


def client_row(conn: psycopg.Connection, client_id: str) -> dict[str, Any] | None:
    return conn.execute(
        "select client_id, client_name, redirect_uris from assistant_clients where client_id = %s",
        (client_id,),
    ).fetchone()


def sweep_requests(conn: psycopg.Connection, now: datetime) -> None:
    conn.execute("delete from assistant_requests where created_utc < %s", (now - REQUEST_SWEEP,))


def create_request(
    conn: psycopg.Connection,
    client: dict[str, Any],
    redirect_uri: str,
    code_challenge: str,
    state: str | None,
    now: datetime,
) -> str:
    row = conn.execute(
        """
        insert into assistant_requests
            (client_id, client_name, redirect_uri, code_challenge, state, scope,
             created_utc, expires_utc)
        values (%s, %s, %s, %s, %s, %s, %s, %s) returning id
        """,
        (
            client["client_id"],
            client["client_name"],
            redirect_uri,
            code_challenge,
            state,
            SCOPE,
            now,
            now + CODE_LIFE,
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
    return Tokens(access, refresh, int(ACCESS_LIFE.total_seconds()))


def exchange_code(
    conn: psycopg.Connection,
    code: str,
    verifier: str,
    client_id: str,
    redirect_uri: str,
    now: datetime,
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
    grant = conn.execute(
        """
        insert into assistant_grants
            (auth_user_id, client_id, client_name, created_utc, last_used_utc,
             access_token_hash, access_expires_utc, refresh_token_hash, refresh_expires_utc)
        values (%s, %s, %s, %s, %s, 'pending', %s, 'pending', %s) returning id
        """,
        (row["auth_user_id"], row["client_id"], row["client_name"], now, now, now, now),
    ).fetchone()
    return _issue(conn, grant["id"], now)


def refresh_grant(
    conn: psycopg.Connection, refresh_token: str, client_id: str, now: datetime
) -> Tokens | None:
    """Rotate: the old refresh token dies in the same statement the new one
    is issued. Unused ninety days, revoked, or unknown: None."""
    row = conn.execute(
        """
        select id from assistant_grants
        where refresh_token_hash = %s and client_id = %s and revoked_utc is null
          and refresh_expires_utc > %s
        """,
        (sha256(refresh_token), client_id, now),
    ).fetchone()
    if row is None:
        return None
    return _issue(conn, row["id"], now)


def resolve_bearer(conn: psycopg.Connection, token: str, now: datetime) -> str | None:
    """The auth_user_id an access token stands for, or None."""
    row = conn.execute(
        """
        update assistant_grants set last_used_utc = %s
        where access_token_hash = %s and revoked_utc is null and access_expires_utc > %s
        returning auth_user_id
        """,
        (now, sha256(token), now),
    ).fetchone()
    return str(row["auth_user_id"]) if row else None


# --- the routes ------------------------------------------------------------------


def _oauth_error(error: str, description: str = "", status: int = 400) -> JSONResponse:
    body: dict[str, str] = {"error": error}
    if description:
        body["error_description"] = description
    return JSONResponse(body, status_code=status, headers={"cache-control": "no-store"})


class OAuthRoutes:
    """The handlers, bound to a pool factory, the public base and the app origin."""

    def __init__(
        self,
        base: str,
        app_origin: str,
        verifier: JwksVerifier,
        clock: Callable[[], datetime] = now_utc,
    ) -> None:
        self.base = base
        self.app_origin = app_origin
        self.verifier = verifier
        self.clock = clock

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
            client = client_row(conn, client_id)
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
            scope = q.get("scope") or SCOPE
            if any(part not in (SCOPE,) for part in scope.split()):
                return refuse("invalid_scope", f"only {SCOPE} is offered")
            now = self.clock()
            sweep_requests(conn, now)
            request_id = create_request(conn, client, redirect_uri, challenge, state, now)
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
        return JSONResponse({"client_name": row["client_name"] or ASSISTANT_FALLBACK})

    async def token(self, request: Request) -> JSONResponse:
        raw = (await request.body()).decode("utf-8", errors="replace")
        form = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
        grant_type = form.get("grant_type", "")
        client_id = form.get("client_id", "")
        now = self.clock()
        with request.app.state.pool.connection() as conn:
            if client_row(conn, client_id) is None:
                return _oauth_error("invalid_client", status=401)
            if grant_type == "authorization_code":
                tokens = exchange_code(
                    conn,
                    form.get("code", ""),
                    form.get("code_verifier", ""),
                    client_id,
                    form.get("redirect_uri", ""),
                    now,
                )
            elif grant_type == "refresh_token":
                tokens = refresh_grant(conn, form.get("refresh_token", ""), client_id, now)
            else:
                return _oauth_error("unsupported_grant_type")
        if tokens is None:
            return _oauth_error("invalid_grant")
        return JSONResponse(
            {
                "access_token": tokens.access_token,
                "token_type": "bearer",
                "expires_in": tokens.expires_in,
                "refresh_token": tokens.refresh_token,
                "scope": SCOPE,
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
