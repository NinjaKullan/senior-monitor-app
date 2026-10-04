"""Spec 019 §9 — the authorization server, end to end with a scripted client."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import httpx
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

from kettle import assistant_auth
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
    # Amendment A: the write scope is offered beside read.
    assert resource["scopes_supported"] == ["kettle:read", "kettle:write"]
    server = api.get("/.well-known/oauth-authorization-server").json()
    assert server["issuer"] == base
    assert server["code_challenge_methods_supported"] == ["S256"]
    assert server["registration_endpoint"] == f"{base}/oauth/register"
    assert set(server["grant_types_supported"]) == {"authorization_code", "refresh_token"}
    assert "none" in server["token_endpoint_auth_methods_supported"]
    assert server["authorization_endpoint"] == f"{base}/oauth/authorize"
    assert server["token_endpoint"] == f"{base}/oauth/token"
    # CIMD alongside DCR: a client_id that is an https URL names its own document.
    assert server["client_id_metadata_document_supported"] is True


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


LEGACY_HOST = "kettle-api.fly.dev"


def _code_for(assistant: Assistant, challenge: str, resource: str | None = None) -> str:
    sent = assistant.authorize(challenge, resource=resource)
    assert sent.status_code == 302, sent.text
    request_id = parse_qs(urlsplit(sent.headers["location"]).query)["request"][0]
    approved = assistant.approve(request_id, session_token(USER))
    assert approved.status_code == 200, approved.text
    return parse_qs(urlsplit(approved.json()["redirect"]).query)["code"][0]


@pytest.mark.parametrize("host", ["kettle-api.test", LEGACY_HOST])
def test_protected_resource_names_the_host_it_was_asked_on(api, settings, host):
    """Brief 358 §2: `resource` equals the MCP URL exactly on whichever of the
    two live hosts (357) the request arrived at, and the 401's pointer leads
    to that host's document. The authorization server is the one issuer."""
    base = settings.public_base_url
    assert base == "https://kettle-api.test"
    document = api.get(
        "/.well-known/oauth-protected-resource", headers={"host": f"{host}:443"}
    ).json()
    assert document["resource"] == f"https://{host}/mcp"
    assert document["authorization_servers"] == [base]
    assert document["scopes_supported"] == ["kettle:read", "kettle:write"]
    assert document["bearer_methods_supported"] == ["header"]
    headers = {
        "host": host,
        "accept": "application/json, text/event-stream",
        "content-type": "application/json",
    }
    refused = api.post("/mcp", content="{}", headers=headers, follow_redirects=False)
    assert refused.status_code == 401
    assert refused.headers["www-authenticate"] == (
        f'Bearer resource_metadata="https://{host}/.well-known/oauth-protected-resource"'
    )


def test_a_host_that_is_not_ours_gets_the_issuers_document(api, settings):
    """A request with some other Host (a proxy, a probe) is answered as the
    issuer: discovery never names a host the API does not answer on."""
    base = settings.public_base_url
    for host in ("evil.test", "kettle-api.test.evil.test", ""):
        document = api.get("/.well-known/oauth-protected-resource", headers={"host": host}).json()
        assert document["resource"] == f"{base}/mcp", host
    assert assistant_auth.base_for(base, "KETTLE-API.FLY.DEV:8443") == "https://kettle-api.fly.dev"
    assert assistant_auth.base_for(base, None) == base
    assert assistant_auth.mcp_resources(base) == {
        f"{base}/mcp",
        f"https://{LEGACY_HOST}/mcp",
    }


# --- RFC 8707: the resource parameter (brief 358 §3) ----------------------------


def test_a_resource_named_at_authorize_is_bound_and_must_be_named_again(api, conn, family):
    """ChatGPT appends `resource=<MCP URL>` to authorize and token: the
    authorize request accepts it, the token request that names it again is
    minted, and the grant carries it. A token request naming a different
    one is `invalid_target` and the code is spent on it."""
    assistant = Assistant(api)
    assistant.register()
    mcp = "https://kettle-api.test/mcp"
    verifier, challenge = pkce_pair()
    code = _code_for(assistant, challenge, resource=mcp)
    minted = assistant.token(
        grant_type="authorization_code",
        code=code,
        code_verifier=verifier,
        redirect_uri=assistant.redirect_uri,
        resource=mcp,
    )
    assert minted.status_code == 200, minted.text
    assert [g["resource"] for g in _grants(conn)] == [mcp]
    # Refresh: the same resource is fine; the other host's MCP URL is not.
    refresh = minted.json()["refresh_token"]
    other = f"https://{LEGACY_HOST}/mcp"
    wrong = assistant.token(grant_type="refresh_token", refresh_token=refresh, resource=other)
    assert wrong.status_code == 400 and wrong.json()["error"] == "invalid_target"
    same = assistant.token(grant_type="refresh_token", refresh_token=refresh, resource=mcp)
    assert same.status_code == 200, same.text

    # A second authorization, exchanged for a different resource: refused,
    # and a retry with the right one finds the code already spent.
    verifier, challenge = pkce_pair()
    code = _code_for(assistant, challenge, resource=mcp)
    differs = assistant.token(
        grant_type="authorization_code",
        code=code,
        code_verifier=verifier,
        redirect_uri=assistant.redirect_uri,
        resource=other,
    )
    assert differs.status_code == 400 and differs.json()["error"] == "invalid_target"
    retry = assistant.token(
        grant_type="authorization_code",
        code=code,
        code_verifier=verifier,
        redirect_uri=assistant.redirect_uri,
        resource=mcp,
    )
    assert retry.status_code == 400 and retry.json()["error"] == "invalid_grant"
    assert len(_grants(conn)) == 1


def test_a_resource_that_is_not_this_server_is_invalid_target_and_absent_is_fine(api, conn, family):
    """Present but foreign is refused at both endpoints with the RFC's own
    error; a client that sends none (Claude) is unchanged, and the other
    live host's MCP URL is accepted. Never a 400 for mere presence."""
    assistant = Assistant(api)
    assistant.register()
    _, challenge = pkce_pair()
    sent = assistant.authorize(challenge, resource="https://evil.test/mcp")
    assert sent.status_code == 302
    query = parse_qs(urlsplit(sent.headers["location"]).query)
    assert query["error"] == ["invalid_target"] and query["state"] == ["xyz"]
    assert assistant.authorize(challenge, resource=f"https://{LEGACY_HOST}/mcp/").status_code == 302
    assistant.connect(USER)
    foreign = assistant.token(
        grant_type="refresh_token",
        refresh_token=assistant.refresh_token,
        resource="https://evil.test/mcp",
    )
    assert foreign.status_code == 400 and foreign.json()["error"] == "invalid_target"
    # The grant was bound to nothing, so it accepts a refresh with or
    # without one of our own resources named.
    named = assistant.token(
        grant_type="refresh_token",
        refresh_token=assistant.refresh_token,
        resource="https://kettle-api.test/mcp",
    )
    assert named.status_code == 200, named.text
    assert [g["resource"] for g in _grants(conn)] == [None]


# --- the ChatGPT redirect URIs (brief 358 §4) ------------------------------------


def test_chatgpts_redirect_uris_register_and_match_exactly(api, family):
    """Dynamic registration takes both shapes ChatGPT sends, per
    registration and matched exactly; a sibling path under the same host is
    not the registered one."""
    platform = "https://chatgpt.com/connector_platform_oauth_redirect"
    callback = "https://chatgpt.com/connector/oauth/cb_6f1d2a0e9b"
    assistant = Assistant(api, redirect_uri=platform)
    registered = assistant.register("ChatGPT", redirect_uris=[platform, callback])
    assert registered["redirect_uris"] == [platform, callback]
    _, challenge = pkce_pair()
    assert assistant.authorize(challenge, redirect_uri=callback).status_code == 302
    assert (
        assistant.authorize(
            challenge, redirect_uri="https://chatgpt.com/connector/oauth/cb_other"
        ).status_code
        == 400
    )
    assert assistant.authorize(challenge, redirect_uri=f"{platform}/").status_code == 400
    assistant.connect(USER, redirect_uri=callback)
    assert mcp_call(api, assistant.access_token, "tools/list").status_code == 200


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
        "client_name": "Claude",
        "scope": "kettle:read",
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
        "add_note",
        "reply",
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


def test_register_is_json_and_token_reads_form_or_json(api, family):
    """Brief 358 §4: the token endpoint reads the form body Claude posts and
    the JSON body ChatGPT may post; a body that is neither is an empty
    request (invalid_client), never a 500."""
    assert (
        api.post(
            "/oauth/register", content="not json", headers={"content-type": "application/json"}
        ).status_code
        == 400
    )
    assert api.post("/oauth/register", json={"redirect_uris": []}).status_code == 400
    assert api.post("/oauth/token", json={"grant_type": "authorization_code"}).status_code == 401
    assert api.post("/oauth/token", json=["not", "an", "object"]).status_code == 401
    assert (
        api.post(
            "/oauth/token", content="{not json", headers={"content-type": "application/json"}
        ).status_code
        == 401
    )
    # The same exchange, once as a form and once as JSON, both mint tokens.
    assistant = Assistant(api)
    assistant.connect(USER)
    as_form = assistant.token(grant_type="refresh_token", refresh_token=assistant.refresh_token)
    assert as_form.status_code == 200, as_form.text
    as_json = assistant.token(
        as_json=True, grant_type="refresh_token", refresh_token=as_form.json()["refresh_token"]
    )
    assert as_json.status_code == 200, as_json.text
    assert as_json.json()["refresh_token"] != as_form.json()["refresh_token"]


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


# --- Client ID Metadata Documents (CIMD), beside dynamic registration ----------------

#: A per-app document under a trusted prefix (brief 358 §7), the shape
#: ChatGPT's Connect step sends; not pinned unless a test pins it.
CIMD_ID = "https://chatgpt.com/oauth/TESTAPP0001/client.json"
CIMD_REDIRECT = "https://chatgpt.com/connector/oauth/TESTAPP0001"
#: An https URL under neither prefix: never a client, never fetched.
UNKNOWN_ID = "https://assistant.test/.well-known/oauth-client"


def cimd_document(**over):
    return {
        "client_id": CIMD_ID,
        "client_name": "Documented",
        "redirect_uris": [CIMD_REDIRECT],
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        **over,
    }


def cimd_client(
    document=None, status: int = 200, calls: list[str] | None = None, url: str = CIMD_ID
) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(str(request.url))
        if str(request.url) == url:
            return httpx.Response(
                status, json=document if document is not None else cimd_document()
            )
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture
def cimd_api_factory(settings, notifier, conn, clock):
    def make(client: httpx.Client):
        return TestClient(
            create_app(settings, notifier, clock, jwks_client=jwks_client(), cimd_client=client)
        )

    return make


@pytest.fixture
def known_cimd(monkeypatch):
    """Pin CIMD_ID's document for the duration, the way Claude's and ChatGPT's
    are pinned (DECISIONS 319/336): the pinned copy names CIMD_REDIRECT, so a
    live fetch that fails falls back to a redirect the test can still use.
    Being a client at all needs no pin since brief 358 §7; the prefix does."""
    monkeypatch.setitem(
        assistant_auth.KNOWN_CLIENT_DOCUMENTS,
        CIMD_ID,
        {"client_id": CIMD_ID, "client_name": "Documented", "redirect_uris": [CIMD_REDIRECT]},
    )


def test_a_cimd_client_connects_without_registering(cimd_api_factory, conn, family, known_cimd):
    calls: list[str] = []
    with cimd_api_factory(cimd_client(calls=calls)) as api:
        assistant = Assistant(api, redirect_uri=CIMD_REDIRECT)
        assistant.client_id = CIMD_ID  # never POSTs /oauth/register
        _, challenge = pkce_pair()
        sent = assistant.authorize(challenge)
        assert sent.status_code == 302, sent.text
        request_id = parse_qs(urlsplit(sent.headers["location"]).query)["request"][0]
        # The consent screen learns the name from the document.
        assert api.get("/oauth/pending", params={"request": request_id}).json() == {
            "client_name": "Documented",
            "scope": "kettle:read",
        }
        assistant.connect(USER)
        assert mcp_call(api, assistant.access_token, "tools/list").status_code == 200
        # Connect twice more: one row for the client, keyed by its URL, never a
        # kc_ row per connect; the document was fetched once (cached).
        assistant.connect(USER)
        assistant.connect(USER)
    rows = conn.execute("select client_id, client_name from assistant_clients").fetchall()
    assert [(r["client_id"], r["client_name"]) for r in rows] == [(CIMD_ID, "Documented")]
    assert calls == [CIMD_ID]
    assert {g["client_id"] for g in _grants(conn)} == {CIMD_ID}


def test_a_known_url_with_a_broken_live_document_falls_back_to_its_shipped_copy(
    cimd_api_factory, family, known_cimd
):
    """DECISIONS 336: for a PINNED url, an unreachable or self-contradicting
    live document is not "no client" — the shipped copy stands (319/320), the
    same way Claude's does when its edge challenges the fetch. (For a url
    outside the prefixes there is no fetch at all; that is the test below.)"""
    for client in (
        cimd_client(status=404),
        cimd_client(status=500),
        cimd_client(document={"not": "json shaped"}),
        cimd_client(document=cimd_document(client_id="https://other.test/doc")),
        cimd_client(document=cimd_document(redirect_uris=[])),
    ):
        with cimd_api_factory(client) as api:
            assistant = Assistant(api, redirect_uri=CIMD_REDIRECT)
            assistant.client_id = CIMD_ID
            _, challenge = pkce_pair()
            # The shipped copy names CIMD_REDIRECT, so authorize proceeds.
            sent = assistant.authorize(challenge)
            assert sent.status_code == 302, sent.text
            assert "request=" in sent.headers["location"]


def test_a_cimd_redirect_outside_the_document_is_refused(cimd_api_factory, family, known_cimd):
    with cimd_api_factory(cimd_client()) as api:
        assistant = Assistant(api, redirect_uri=CIMD_REDIRECT)
        assistant.client_id = CIMD_ID
        _, challenge = pkce_pair()
        refused = assistant.authorize(challenge, redirect_uri="https://evil.test/cb")
        assert refused.status_code == 400
        assert refused.json()["error"] == "invalid_request"
        # And the document's own redirect still works in the same app.
        assert assistant.authorize(challenge).status_code == 302


def test_dynamic_registration_still_works_beside_cimd(cimd_api_factory, conn, family):
    with cimd_api_factory(cimd_client()) as api:
        assistant = Assistant(api)
        assistant.connect(USER)
        assert assistant.client_id.startswith("kc_")
        assert mcp_call(api, assistant.access_token, "tools/list").status_code == 200


# --- the shipped copy of a known client's document (DECISIONS 319) ------------------

CLAUDE_ID = "https://claude.ai/oauth/mcp-oauth-client-metadata"
CLAUDE_REDIRECT = "https://claude.ai/api/mcp/auth_callback"


def challenged(calls: list[str] | None = None, url: str = CLAUDE_ID) -> httpx.Client:
    """claude.ai's edge as seen from Fly: a Cloudflare challenge, text/html."""

    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(str(request.url))
        if str(request.url) == url:
            return httpx.Response(
                403, text="<html>Just a moment...</html>", headers={"content-type": "text/html"}
            )
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_a_challenged_fetch_of_claudes_document_falls_back_to_the_shipped_copy(
    cimd_api_factory, conn, family, caplog
):
    import logging

    with (
        caplog.at_level(logging.WARNING, logger="kettle.assistant"),
        cimd_api_factory(challenged()) as api,
    ):
        assistant = Assistant(api, redirect_uri=CLAUDE_REDIRECT)
        assistant.client_id = CLAUDE_ID
        _, challenge = pkce_pair()
        sent = assistant.authorize(challenge, scope="kettle:read kettle:write")
        assert sent.status_code == 302, sent.text
        request_id = parse_qs(urlsplit(sent.headers["location"]).query)["request"][0]
        assert api.get("/oauth/pending", params={"request": request_id}).json() == {
            "client_name": "Claude",
            "scope": "kettle:write",
        }
        assistant.connect(USER, scope="kettle:write")
        assert mcp_call(api, assistant.access_token, "tools/list").status_code == 200
    rows = conn.execute(
        "select client_id, client_name, redirect_uris from assistant_clients"
    ).fetchall()
    assert [(r["client_id"], r["client_name"], list(r["redirect_uris"])) for r in rows] == [
        (CLAUDE_ID, "Claude", [CLAUDE_REDIRECT])
    ]
    assert (
        f"client document at {CLAUDE_ID} refused: 403 text/html; using the shipped copy"
        in caplog.text
    )


#: Near misses of the trusted prefixes: a lookalike host, the prefix inside
#: another URL, plain http, a path that only shares a stem, other casing.
#: None is a client, none is fetched.
OUTSIDE_THE_PREFIXES = (
    UNKNOWN_ID,
    "https://chatgpt.com.evil.test/oauth/x/client.json",
    "https://evil.test/https://chatgpt.com/oauth/x/client.json",
    "http://chatgpt.com/oauth/x/client.json",
    "https://chatgpt.com/oauthx/client.json",
    "https://chatgpt.com/oauth",
    "HTTPS://CHATGPT.COM/oauth/x/client.json",
    "https://claude.ai/api/mcp/auth_callback",
)


def test_a_url_outside_both_prefixes_is_invalid_client_with_no_fetch_and_no_log(
    cimd_api_factory, family, caplog
):
    """DECISIONS 336, kept by brief 358 §7: an `https://` client_id under
    neither trusted prefix is not a CIMD client at all. It gets
    `invalid_client` — the same silence an unknown `kc_` id gets — with no
    fetch and no log line. The recording transport would answer 200 for any
    of these URLs if reached, so a request arriving would prove the fetch
    happened; none does."""
    import logging

    for url in OUTSIDE_THE_PREFIXES:
        assert not assistant_auth.is_cimd_client_id(url), url
    calls: list[str] = []
    with (
        caplog.at_level(logging.WARNING, logger="kettle.assistant"),
        cimd_api_factory(cimd_client(calls=calls, url=UNKNOWN_ID)) as api,
    ):
        for url in OUTSIDE_THE_PREFIXES:
            assistant = Assistant(api, redirect_uri=CIMD_REDIRECT)
            assistant.client_id = url
            _, challenge = pkce_pair()
            refused = assistant.authorize(challenge)
            assert refused.status_code == 400, url
            assert refused.json()["error"] == "invalid_client", url
    assert calls == []  # no fetch of any attacker-named URL
    assert "assistant.test" not in caplog.text and "evil.test" not in caplog.text


def test_a_chatgpt_document_under_the_prefix_is_a_client_even_when_not_pinned(
    cimd_api_factory, conn, family
):
    """Brief 358 §7: ChatGPT mints one document per app, so the Connect step
    sends a client_id nobody pinned. Under the prefix it is fetched live and
    the whole flow works; the mirrored row and the grant carry its URL."""
    assert assistant_auth.is_cimd_client_id(CIMD_ID)
    assert CIMD_ID not in assistant_auth.KNOWN_CLIENT_DOCUMENTS
    calls: list[str] = []
    with cimd_api_factory(cimd_client(calls=calls)) as api:
        assistant = Assistant(api, redirect_uri=CIMD_REDIRECT)
        assistant.client_id = CIMD_ID
        _, challenge = pkce_pair()
        sent = assistant.authorize(challenge, resource="https://kettle-api.test/mcp")
        assert sent.status_code == 302, sent.text
        request_id = parse_qs(urlsplit(sent.headers["location"]).query)["request"][0]
        assert api.get("/oauth/pending", params={"request": request_id}).json() == {
            "client_name": "Documented",
            "scope": "kettle:read",
        }
        assistant.connect(USER)
        assert mcp_call(api, assistant.access_token, "tools/list").status_code == 200
    assert calls == [CIMD_ID]  # fetched once; the cache serves the rest
    rows = conn.execute("select client_id, client_name from assistant_clients").fetchall()
    assert [(r["client_id"], r["client_name"]) for r in rows] == [(CIMD_ID, "Documented")]
    assert {g["client_id"] for g in _grants(conn)} == {CIMD_ID}


CHATGPT_APP_ID = "https://chatgpt.com/oauth/A1YFUC1zmNdF/client.json"
CHATGPT_APP_REDIRECT = "https://chatgpt.com/connector/oauth/A1YFUC1zmNdF"


def test_the_pinned_chatgpt_copy_stands_when_the_live_fetch_fails(cimd_api_factory, family):
    """Brief 358 §7: the per-app document is pinned as fetched Oct 4 2026, so
    a failed live fetch (here a challenge, as claude.ai's edge does) still
    lets ChatGPT's real redirect through and names it on the consent screen."""
    pinned = assistant_auth.KNOWN_CLIENT_DOCUMENTS[CHATGPT_APP_ID]
    assert pinned == {
        "client_id": CHATGPT_APP_ID,
        "client_name": "ChatGPT",
        "redirect_uris": [CHATGPT_APP_REDIRECT],
    }
    calls: list[str] = []
    with cimd_api_factory(challenged(calls, url=CHATGPT_APP_ID)) as api:
        assistant = Assistant(api, redirect_uri=CHATGPT_APP_REDIRECT)
        assistant.client_id = CHATGPT_APP_ID
        _, challenge = pkce_pair()
        sent = assistant.authorize(challenge)
        assert sent.status_code == 302, sent.text
        request_id = parse_qs(urlsplit(sent.headers["location"]).query)["request"][0]
        assert api.get("/oauth/pending", params={"request": request_id}).json() == {
            "client_name": "ChatGPT",
            "scope": "kettle:read",
        }
        # The pinned copy names one redirect; a sibling app's is refused.
        other = "https://chatgpt.com/connector/oauth/B2ZZZZZZZZZZ"
        assert assistant.authorize(challenge, redirect_uri=other).status_code == 400
    assert calls == [CHATGPT_APP_ID]


def test_every_pinned_document_is_under_a_trusted_prefix():
    """A pin is a fallback for a document already trusted, never a way in: a
    key outside the prefixes would be dead (is_cimd_client_id never reaches
    it) and would read as if it granted something."""
    prefixes = assistant_auth.TRUSTED_CLIENT_DOCUMENT_PREFIXES
    assert prefixes == ("https://claude.ai/oauth/", "https://chatgpt.com/oauth/")
    assert all(p.startswith("https://") and p.endswith("/") for p in prefixes)
    for key, document in assistant_auth.KNOWN_CLIENT_DOCUMENTS.items():
        assert assistant_auth.is_cimd_client_id(key), key
        assert document["client_id"] == key
        assert document["redirect_uris"]


def test_a_live_document_that_differs_wins_over_the_shipped_copy(cimd_api_factory, conn, family):
    second = "https://claude.ai/api/mcp/other_callback"
    live = {
        "client_id": CLAUDE_ID,
        "client_name": "Claude",
        "redirect_uris": [CLAUDE_REDIRECT, second],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return (
            httpx.Response(200, json=live) if str(request.url) == CLAUDE_ID else httpx.Response(404)
        )

    with cimd_api_factory(httpx.Client(transport=httpx.MockTransport(handler))) as api:
        assistant = Assistant(api, redirect_uri=second)
        assistant.client_id = CLAUDE_ID
        _, challenge = pkce_pair()
        assert assistant.authorize(challenge).status_code == 302
    row = conn.execute("select redirect_uris from assistant_clients").fetchone()
    assert list(row["redirect_uris"]) == [CLAUDE_REDIRECT, second]


def test_a_failed_fetch_is_remembered_for_ten_minutes(cimd_api_factory, family, clock):
    from datetime import timedelta

    calls: list[str] = []
    with cimd_api_factory(challenged(calls)) as api:
        assistant = Assistant(api, redirect_uri=CLAUDE_REDIRECT)
        assistant.client_id = CLAUDE_ID
        for _ in range(3):
            _, challenge = pkce_pair()
            assert assistant.authorize(challenge).status_code == 302
        assert calls == [CLAUDE_ID]
        clock.now = clock.now + timedelta(minutes=10, seconds=1)
        _, challenge = pkce_pair()
        assert assistant.authorize(challenge).status_code == 302
        assert calls == [CLAUDE_ID, CLAUDE_ID]


def test_a_network_failure_logs_the_exception_class_and_uses_the_shipped_copy(
    cimd_api_factory, family, caplog
):
    import logging

    def explode(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("slow", request=request)

    with (
        caplog.at_level(logging.WARNING, logger="kettle.assistant"),
        cimd_api_factory(httpx.Client(transport=httpx.MockTransport(explode))) as api,
    ):
        assistant = Assistant(api, redirect_uri=CLAUDE_REDIRECT)
        assistant.client_id = CLAUDE_ID
        _, challenge = pkce_pair()
        assert assistant.authorize(challenge).status_code == 302
    assert f"client document at {CLAUDE_ID} refused: ConnectTimeout; using the shipped copy" in (
        caplog.text
    )
