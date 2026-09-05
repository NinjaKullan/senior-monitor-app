"""Shared helpers for the spec 019 tests: a signed Supabase-shaped session, a
JWKS the verifier can fetch, an OAuth client that walks the whole flow, and
one JSON-RPC call into /mcp."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from kettle.assistant_auth import jwks_document_for


def _outbound_copy_lists():
    """The outbound scan's banned lists, loaded by path: product/tests is not
    a package, so a test cannot import its neighbour by name."""
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parent / "tests" / "test_outbound_copy.py"
    spec = importlib.util.spec_from_file_location("outbound_copy_scan", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.BANNED, module.BANNED_PHRASES, module.GENDERED_PRONOUNS, module.VERDICT_PHRASES


REL_TIME = re.compile(r"\b\d+ (?:minutes|hours|days) ago\b|\b1 (?:minute|hour|day) ago\b")
CLOCK = re.compile(r"\b\d{1,2}:\d{2} [ap]m\b")
MONTH_DAY = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2}\b")
#: ALL_CLEAR_SENT is the one §8 label the outbound scan's verdict list would
#: catch ("all clear"); ruled verbatim, so it is named here rather than the
#: list widened (filed in the 019 build notes).
ALLOWED_PHRASES = ("all clear",)
NAMES = ("Kettle", "Linda", "Bill", "Amma", "Appa", "Sarah", "Tom", "Carol", "Whitaker", "Sharma")


def assert_assistant_copy_law(text: str, *, digits_ok: bool = False) -> None:
    """Spec 019's laws over one rendered answer or description: straight
    apostrophes, no dashes, no quote marks, the outbound word and phrase bans,
    no gendered pronoun, and no count outside the heard, clock and date
    shapes (who_to_call carries numbers by design)."""
    banned, banned_phrases, pronouns, verdicts = _outbound_copy_lists()
    scanned = text
    for name in NAMES:
        scanned = scanned.replace(name, "«name»")
    assert "—" not in text and "–" not in text, f"a dash in: {text}"
    assert "‘" not in text and "’" not in text, f"a curly apostrophe in: {text}"
    assert '"' not in text and "“" not in text and "”" not in text, f"a quote mark in: {text}"
    lowered = scanned.lower()
    for phrase in ALLOWED_PHRASES:
        lowered = lowered.replace(phrase, "«allowed»")
    for word in banned + pronouns:
        assert not re.search(rf"\b{re.escape(word)}\b", lowered), f"banned word {word!r} in: {text}"
    for phrase in banned_phrases + verdicts:
        assert phrase not in lowered, f"banned phrase {phrase!r} in: {text}"
    if not digits_ok:
        stripped = MONTH_DAY.sub("", CLOCK.sub("", REL_TIME.sub("", scanned)))
        assert not re.search(r"\d", stripped), f"a count in: {text}"


KID = "kettle-test-key"
_PRIVATE = ec.generate_private_key(ec.SECP256R1())
JWKS = jwks_document_for(_PRIVATE.public_key(), KID)
JWKS_URL = "https://supabase.test/auth/v1/.well-known/jwks.json"


def jwks_client(
    document: dict[str, Any] | None = None, calls: list[str] | None = None
) -> httpx.Client:
    """An httpx client that answers the JWKS URL and nothing else."""

    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(str(request.url))
        if str(request.url) == JWKS_URL:
            return httpx.Response(200, json=document or JWKS)
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler))


def session_token(auth_user_id: str, *, kid: str = KID, expired: bool = False, key=None) -> str:
    """A Supabase-shaped access token: ES256, kid in the header, sub + exp."""
    now = datetime.now(UTC)
    claims = {
        "sub": auth_user_id,
        "aud": "authenticated",
        "role": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + (timedelta(hours=-1) if expired else timedelta(hours=1))).timestamp()),
    }
    return jwt.encode(claims, key or _PRIVATE, algorithm="ES256", headers={"kid": kid})


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


class Assistant:
    """A scripted OAuth client, the way Claude's connector behaves."""

    def __init__(
        self, client: TestClient, redirect_uri: str = "https://claude.ai/api/mcp/auth_callback"
    ):
        self.client = client
        self.redirect_uri = redirect_uri
        self.client_id = ""
        self.access_token = ""
        self.refresh_token = ""

    def register(
        self, name: str | None = "Claude", redirect_uris: list[str] | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"redirect_uris": redirect_uris or [self.redirect_uri]}
        if name is not None:
            payload["client_name"] = name
        response = self.client.post("/oauth/register", json=payload)
        assert response.status_code == 201, response.text
        self.client_id = response.json()["client_id"]
        return response.json()

    def authorize(
        self,
        challenge: str | None,
        *,
        method: str = "S256",
        state: str = "xyz",
        redirect_uri: str | None = None,
        scope: str | None = "kettle:read",
    ) -> httpx.Response:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri or self.redirect_uri,
            "response_type": "code",
            "state": state,
        }
        if challenge is not None:
            params["code_challenge"] = challenge
            params["code_challenge_method"] = method
        if scope is not None:
            params["scope"] = scope
        return self.client.get("/oauth/authorize", params=params, follow_redirects=False)

    def approve(self, request_id: str, session: str, decision: str = "allow") -> httpx.Response:
        return self.client.post(
            "/oauth/approve",
            json={"request_id": request_id, "decision": decision},
            headers={"authorization": f"Bearer {session}"},
        )

    def token(self, **form: str) -> httpx.Response:
        form.setdefault("client_id", self.client_id)
        return self.client.post(
            "/oauth/token", data=form, headers={"content-type": "application/x-www-form-urlencoded"}
        )

    def connect(self, auth_user_id: str, redirect_uri: str | None = None) -> None:
        """Register, authorize, approve, exchange: the whole flow, kept tokens."""
        if not self.client_id:
            self.register()
        verifier, challenge = pkce_pair()
        sent = self.authorize(challenge, redirect_uri=redirect_uri)
        assert sent.status_code == 302, sent.text
        request_id = parse_qs(urlsplit(sent.headers["location"]).query)["request"][0]
        approved = self.approve(request_id, session_token(auth_user_id))
        assert approved.status_code == 200, approved.text
        back = urlsplit(approved.json()["redirect"])
        code = parse_qs(back.query)["code"][0]
        exchanged = self.token(
            grant_type="authorization_code",
            code=code,
            code_verifier=verifier,
            redirect_uri=redirect_uri or self.redirect_uri,
        )
        assert exchanged.status_code == 200, exchanged.text
        body = exchanged.json()
        self.access_token = body["access_token"]
        self.refresh_token = body["refresh_token"]

    def call(
        self, tool: str, arguments: dict[str, Any] | None = None, token: str | None = None
    ) -> httpx.Response:
        return mcp_call(
            self.client,
            token or self.access_token,
            "tools/call",
            {"name": tool, "arguments": arguments or {}},
        )

    def text(self, tool: str, **arguments: Any) -> str:
        response = self.call(tool, arguments)
        assert response.status_code == 200, response.text
        body = response.json()
        assert "error" not in body, body
        result = body["result"]
        assert not result.get("isError"), result
        return "\n".join(c["text"] for c in result["content"] if c.get("type") == "text")


def mcp_call(
    client: TestClient, token: str | None, method: str, params: dict[str, Any] | None = None
) -> httpx.Response:
    headers = {"accept": "application/json, text/event-stream", "content-type": "application/json"}
    if token:
        headers["authorization"] = f"Bearer {token}"
    return client.post(
        "/mcp",
        content=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}),
        headers=headers,
    )
