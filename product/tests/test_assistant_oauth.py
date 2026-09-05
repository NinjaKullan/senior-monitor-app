"""Spec 019 §9 — the authorization server, end to end with a scripted client."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import psycopg
import pytest
from fastapi.testclient import TestClient
from testsupport_assistant import (
    JWKS,
    Assistant,
    jwks_client,
    mcp_call,
    pkce_pair,
    session_token,
)

from kettle.assistant_auth import redirect_allowed, www_authenticate
from kettle.main import create_app
from kettle.provisioning import provision_family
from testsupport import BASE_URL, add_member, as_user

USER = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def api(settings, notifier, conn, clock):
    with TestClient(create_app(settings, notifier, clock, jwks_client=jwks_client())) as c:
        yield c


@pytest.fixture
def family(conn):
    family = provision_family(
        conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")], base_url=BASE_URL
    )
    add_member(conn, family.family_id, USER, role="admin")
    return family


def _grants(conn):
    return conn.execute("select * from assistant_grants order by created_utc").fetchall()


# --- discovery and the 401 ------------------------------------------------------


def test_discovery_documents_carry_the_fields_in_section_4(api, settings):
    base = settings.public_base_url
    resource = api.get("/.well-known/oauth-protected-resource").json()
    assert resource["resource"] == f"{base}/mcp"
    assert resource["authorization_servers"] == [base]
    assert resource["scopes_supported"] == ["kettle:read"]
    server = api.get("/.well-known/oauth-authorization-server").json()
    assert server["issuer"] == base
    assert server["code_challenge_methods_supported"] == ["S256"]
    assert server["registration_endpoint"] == f"{base}/oauth/register"
    assert set(server["grant_types_supported"]) == {"authorization_code", "refresh_token"}
    assert "none" in server["token_endpoint_auth_methods_supported"]
    assert server["authorization_endpoint"] == f"{base}/oauth/authorize"
    assert server["token_endpoint"] == f"{base}/oauth/token"


def test_mcp_without_a_token_is_a_401_with_the_header_verbatim(api, settings):
    response = mcp_call(api, None, "tools/list")
    assert response.status_code == 401
    base = settings.public_base_url
    assert response.headers["www-authenticate"] == (
        f'Bearer resource_metadata="{base}/.well-known/oauth-protected-resource"'
    )
    assert (
        www_authenticate("https://x")
        == 'Bearer resource_metadata="https://x/.well-known/oauth-protected-resource"'
    )
    # A wrong token is the same 401, never a tool error.
    assert mcp_call(api, "not-a-token", "tools/list").status_code == 401


# --- the flow -------------------------------------------------------------------


def test_register_authorize_approve_exchange_call(api, conn, family):
    assistant = Assistant(api)
    registered = assistant.register("Claude")
    assert registered["token_endpoint_auth_method"] == "none"
    assert registered["client_id"].startswith("kc_")

    verifier, challenge = pkce_pair()
    sent = assistant.authorize(challenge, state="s1")
    assert sent.status_code == 302
    location = urlsplit(sent.headers["location"])
    assert (
        f"{location.scheme}://{location.netloc}{location.path}" == "https://kettle-app.test/connect"
    )
    request_id = parse_qs(location.query)["request"][0]

    # The consent screen learns the client's name without a session.
    assert api.get("/oauth/pending", params={"request": request_id}).json() == {
        "client_name": "Claude"
    }

    approved = assistant.approve(request_id, session_token(USER))
    back = urlsplit(approved.json()["redirect"])
    assert f"{back.scheme}://{back.netloc}{back.path}" == assistant.redirect_uri
    query = parse_qs(back.query)
    assert query["state"] == ["s1"]
    code = query["code"][0]

    exchanged = assistant.token(
        grant_type="authorization_code",
        code=code,
        code_verifier=verifier,
        redirect_uri=assistant.redirect_uri,
    )
    body = exchanged.json()
    assert exchanged.status_code == 200
    assert (
        body["token_type"] == "bearer"
        and body["expires_in"] == 3600
        and body["scope"] == "kettle:read"
    )
    assistant.access_token, assistant.refresh_token = body["access_token"], body["refresh_token"]

    # Stored hashed, never plain.
    [grant] = _grants(conn)
    assert (
        grant["access_token_hash"] != body["access_token"] and len(grant["access_token_hash"]) == 64
    )
    assert str(grant["auth_user_id"]) == USER and grant["client_name"] == "Claude"
    assert "family_id" not in grant

    listed = mcp_call(api, body["access_token"], "tools/list").json()
    assert {t["name"] for t in listed["result"]["tools"]} == {
        "today",
        "parent_day",
        "memory",
        "who_to_call",
        "circles",
    }
    assert "Amma" in assistant.text("today")

    # The code is single use.
    again = assistant.token(
        grant_type="authorization_code",
        code=code,
        code_verifier=verifier,
        redirect_uri=assistant.redirect_uri,
    )
    assert again.status_code == 400 and again.json()["error"] == "invalid_grant"


def test_refresh_rotates_and_the_old_one_dies(api, conn, family):
    assistant = Assistant(api)
    assistant.connect(USER)
    old_refresh, old_access = assistant.refresh_token, assistant.access_token
    rotated = assistant.token(grant_type="refresh_token", refresh_token=old_refresh)
    assert rotated.status_code == 200
    body = rotated.json()
    assert body["refresh_token"] != old_refresh and body["access_token"] != old_access
    dead = assistant.token(grant_type="refresh_token", refresh_token=old_refresh)
    assert dead.status_code == 400 and dead.json()["error"] == "invalid_grant"
    # One grant row, rotated in place; the old access token is gone with it.
    assert len(_grants(conn)) == 1
    assert mcp_call(api, old_access, "tools/list").status_code == 401
    assert mcp_call(api, body["access_token"], "tools/list").status_code == 200


def test_access_tokens_last_an_hour_and_grants_ninety_days(api, conn, family, clock):
    assistant = Assistant(api)
    assistant.connect(USER)
    clock.now += timedelta(hours=1, seconds=1)
    assert mcp_call(api, assistant.access_token, "tools/list").status_code == 401
    refreshed = assistant.token(grant_type="refresh_token", refresh_token=assistant.refresh_token)
    assert refreshed.status_code == 200
    # Ninety days of silence: the grant is expired, refresh says invalid_grant.
    clock.now += timedelta(days=90, seconds=1)
    expired = assistant.token(
        grant_type="refresh_token", refresh_token=refreshed.json()["refresh_token"]
    )
    assert expired.status_code == 400 and expired.json()["error"] == "invalid_grant"


def test_revoke_from_kettles_side_ends_both_tokens(api, conn, family, authed):
    assistant = Assistant(api)
    assistant.connect(USER)
    [grant] = _grants(conn)
    as_user(authed, USER)
    authed.execute("select public.app_revoke_assistant(%s)", (grant["id"],))
    assert mcp_call(api, assistant.access_token, "tools/list").status_code == 401
    refreshed = assistant.token(grant_type="refresh_token", refresh_token=assistant.refresh_token)
    assert refreshed.json()["error"] == "invalid_grant"
    # Only the caller's own grant: a stranger revoking it is refused.
    as_user(authed, OTHER)
    with pytest.raises(psycopg.errors.InsufficientPrivilege, match="not_allowed"):
        authed.execute("select public.app_revoke_assistant(%s)", (grant["id"],))


# --- what is refused -----------------------------------------------------------


def test_missing_pkce_and_wrong_method_are_refused(api, family):
    assistant = Assistant(api)
    assistant.register()
    for response in (assistant.authorize(None), assistant.authorize("abc", method="plain")):
        assert response.status_code == 302
        query = parse_qs(urlsplit(response.headers["location"]).query)
        assert query["error"] == ["invalid_request"] and query["state"] == ["xyz"]


def test_wrong_verifier_is_refused(api, family):
    assistant = Assistant(api)
    assistant.register()
    _, challenge = pkce_pair()
    sent = assistant.authorize(challenge)
    request_id = parse_qs(urlsplit(sent.headers["location"]).query)["request"][0]
    code = parse_qs(
        urlsplit(assistant.approve(request_id, session_token(USER)).json()["redirect"]).query
    )["code"][0]
    wrong = assistant.token(
        grant_type="authorization_code",
        code=code,
        code_verifier="not-the-verifier",
        redirect_uri=assistant.redirect_uri,
    )
    assert wrong.status_code == 400 and wrong.json()["error"] == "invalid_grant"


def test_redirect_mismatch_is_refused_and_loopback_ignores_the_port(api, family):
    assistant = Assistant(api, redirect_uri="http://localhost:8765/callback")
    assistant.register(redirect_uris=["http://localhost:8765/callback"])
    _, challenge = pkce_pair()
    assert assistant.authorize(challenge, redirect_uri="https://evil.test/cb").status_code == 400
    assert (
        assistant.authorize(challenge, redirect_uri="http://localhost:9999/callback").status_code
        == 302
    )
    assert redirect_allowed(["http://127.0.0.1:1234/cb"], "http://127.0.0.1:65000/cb")
    assert not redirect_allowed(
        ["https://claude.ai/api/mcp/auth_callback"], "https://claude.ai/api/mcp/other"
    )
    assert not redirect_allowed(["http://localhost:1/cb"], "http://localhost:1/other")
    # And the whole flow works on the loopback with a different port.
    assistant.connect(USER, redirect_uri="http://localhost:4321/callback")
    assert mcp_call(api, assistant.access_token, "tools/list").status_code == 200


def test_a_code_expires_after_ten_minutes_and_a_request_after_its_life(api, family, clock):
    assistant = Assistant(api)
    assistant.register()
    verifier, challenge = pkce_pair()
    request_id = parse_qs(urlsplit(assistant.authorize(challenge).headers["location"]).query)[
        "request"
    ][0]
    code = parse_qs(
        urlsplit(assistant.approve(request_id, session_token(USER)).json()["redirect"]).query
    )["code"][0]
    clock.now += timedelta(minutes=10, seconds=1)
    late = assistant.token(
        grant_type="authorization_code",
        code=code,
        code_verifier=verifier,
        redirect_uri=assistant.redirect_uri,
    )
    assert late.json()["error"] == "invalid_grant"
    # A request nobody approved in time is gone for the consent screen.
    stale = parse_qs(urlsplit(assistant.authorize(challenge).headers["location"]).query)["request"][
        0
    ]
    clock.now += timedelta(minutes=11)
    assert api.get("/oauth/pending", params={"request": stale}).status_code == 410
    assert assistant.approve(stale, session_token(USER)).status_code == 410


def test_approve_needs_a_session_signed_by_the_projects_key(
    settings, notifier, conn, family, clock
):
    calls: list[str] = []
    with TestClient(
        create_app(settings, notifier, clock, jwks_client=jwks_client(calls=calls))
    ) as api:
        assistant = Assistant(api)
        assistant.register()
        _, challenge = pkce_pair()
        request_id = parse_qs(urlsplit(assistant.authorize(challenge).headers["location"]).query)[
            "request"
        ][0]
        assert assistant.approve(request_id, "garbage").status_code == 401
        assert assistant.approve(request_id, session_token(USER, expired=True)).status_code == 401
        from cryptography.hazmat.primitives.asymmetric import ec

        stranger = ec.generate_private_key(ec.SECP256R1())
        assert assistant.approve(request_id, session_token(USER, key=stranger)).status_code == 401
        assert assistant.approve(request_id, session_token(USER)).status_code == 200
        # JWKS fetched once for the first unknown kid, cached for the rest;
        # the unknown-kid token forced one refetch and was still refused.
        assert calls.count(calls[0]) <= 3
        assert api.post("/oauth/approve", json={"request_id": request_id}).status_code == 401


def test_deny_sends_access_denied_back(api, family):
    assistant = Assistant(api)
    assistant.register()
    _, challenge = pkce_pair()
    request_id = parse_qs(urlsplit(assistant.authorize(challenge).headers["location"]).query)[
        "request"
    ][0]
    denied = assistant.approve(request_id, session_token(USER), decision="deny")
    query = parse_qs(urlsplit(denied.json()["redirect"]).query)
    assert query["error"] == ["access_denied"] and query["state"] == ["xyz"]
    assert assistant.approve(request_id, session_token(USER)).status_code == 410


def test_a_nameless_client_gets_the_fallback_on_the_consent_screen(api, family):
    assistant = Assistant(api)
    assistant.register(name=None)
    _, challenge = pkce_pair()
    request_id = parse_qs(urlsplit(assistant.authorize(challenge).headers["location"]).query)[
        "request"
    ][0]
    assert (
        api.get("/oauth/pending", params={"request": request_id}).json()["client_name"]
        == "An assistant"
    )


def test_register_is_json_and_token_is_form_only(api):
    assert (
        api.post(
            "/oauth/register", content="not json", headers={"content-type": "application/json"}
        ).status_code
        == 400
    )
    assert api.post("/oauth/register", json={"redirect_uris": []}).status_code == 400
    assert api.post("/oauth/token", json={"grant_type": "authorization_code"}).status_code in (
        400,
        401,
    )


# --- the grants table as the app sees it ------------------------------------------


def test_a_person_reads_their_own_grants_on_the_rendered_columns_and_never_a_hash(
    api, conn, family, authed
):
    assistant = Assistant(api)
    assistant.connect(USER)
    as_user(authed, USER)
    rows = authed.execute(
        "select id, client_name, created_utc, last_used_utc, revoked_utc from assistant_grants"
    ).fetchall()
    assert [r["client_name"] for r in rows] == ["Claude"]
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute("select access_token_hash from assistant_grants")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute("select * from assistant_grants")
    as_user(authed, OTHER)
    assert authed.execute("select id from assistant_grants").fetchall() == []
    for statement in (
        "update assistant_grants set revoked_utc = now()",
        "delete from assistant_grants",
        "select client_id from assistant_clients",
        "select id from assistant_requests",
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            authed.execute(statement)
    for fn in ("app_revoke_assistant",):
        row = conn.execute(
            "select has_function_privilege('anon', p.oid, 'execute') as anon, "
            "has_function_privilege('authenticated', p.oid, 'execute') as authed "
            "from pg_proc p where p.proname = %s",
            (fn,),
        ).fetchone()
        assert (row["anon"], row["authed"]) == (False, True)


def test_the_jwks_is_the_shape_supabase_publishes():
    assert JWKS["keys"][0]["kty"] == "EC" and JWKS["keys"][0]["crv"] == "P-256"
