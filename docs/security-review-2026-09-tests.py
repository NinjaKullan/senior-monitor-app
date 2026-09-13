"""Adversarial security review, 2026-09 — the reproductions behind the report.

Evidence, not part of the suite. It lives under docs/ so CI does not collect it
(pytest testpaths are `tests` and `product/tests`); run it by hand:

    cp docs/security-review-2026-09-tests.py product/tests/
    KETTLE_REQUIRE_POSTGRES=1 .venv/bin/python -m pytest \
        product/tests/security-review-2026-09-tests.py -q

One file, grouped by the reviewer's ten questions. Every test runs against the
real Postgres so RLS and the SECURITY DEFINER functions are exercised, not faked.
Tests named `safe_*` PASS by proving the attack does not work; the one named
`finding_*` PASSES by demonstrating the vulnerable behaviour so the report has a
reproduction. When F1 is fixed, invert `test_finding_*` (assert the fetch is
refused) and move the file into product/tests.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import psycopg
import pytest
from fastapi.testclient import TestClient
from testsupport import BASE_URL, add_member, as_user
from testsupport_assistant import Assistant, jwks_client, mcp_call, session_token

from kettle import assistant_auth
from kettle.main import create_app
from kettle.provisioning import provision_family

USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 13, 6, 30, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def api(settings, notifier, conn, clock):
    with TestClient(create_app(settings, notifier, clock, jwks_client=jwks_client())) as c:
        yield c


def family_with_user(conn, name, user, parent="Amma"):
    fam = provision_family(
        conn, name, "Asia/Kolkata", [(parent, None, "Mom")], base_url=BASE_URL,
        owner_email=f"{name.lower()}@example.test", owner_name="Owner",
    )
    add_member(conn, fam.family_id, user, role="admin")
    return fam


# ── Q1: can a read-only grant write? ───────────────────────────────────────────


def test_safe_read_only_grant_cannot_write(api, conn):
    family_with_user(conn, "Sharma", USER_A)
    a = Assistant(api)
    a.connect(USER_A, scope="kettle:read")
    note = a.text("add_note", text="slip this in")
    reply = a.text("reply", text="and this")
    assert note == __import__("kettle.assistant_copy", fromlist=["NEED_WRITE"]).NEED_WRITE
    assert reply == note
    landed = conn.execute("select count(*) as n from journal_entries").fetchone()["n"]
    assert landed == 0


# ── Q2: can one person's token reach another circle's data? ─────────────────────


def test_safe_token_sees_only_its_own_circle(api, conn):
    family_with_user(conn, "Sharma", USER_A, parent="Amma")
    family_with_user(conn, "Whitaker", USER_B, parent="Linda")
    a = Assistant(api)
    a.connect(USER_A, scope="kettle:write")
    # today with no name lists only A's circle; B's parent is unknown to A.
    everyone = a.text("today")
    assert "Amma" in everyone and "Linda" not in everyone
    unknown = a.text("today", parent="Linda")
    assert "Linda" not in unknown or "does not" in unknown.lower() or "isn't" in unknown.lower()
    # A write aimed at B's parent by name never lands in B's family.
    a.text("add_note", text="reach across", parent="Linda")
    b_rows = conn.execute(
        "select count(*) as n from journal_entries j join parents p on p.id = j.parent_id "
        "where p.display_name = 'Linda'"
    ).fetchone()["n"]
    assert b_rows == 0


# ── Q3: can a removed member still write? ───────────────────────────────────────


def test_safe_removed_member_cannot_write(api, conn):
    fam = family_with_user(conn, "Sharma", USER_A)
    a = Assistant(api)
    a.connect(USER_A, scope="kettle:write")
    # The grant is real and unrevoked, but the seat is gone.
    conn.execute("delete from members where family_id = %s and auth_user_id = %s",
                 (fam.family_id, USER_A))
    out = a.text("add_note", text="I was removed a moment ago")
    assert conn.execute("select count(*) as n from journal_entries").fetchone()["n"] == 0
    # The token still resolves (removal does not revoke it) — it simply has no circle.
    assert out  # a sentence, not a crash


# ── Q4: can the CIMD shipped copy be abused to redirect a code? ─────────────────


def test_safe_cimd_shipped_copy_pins_the_redirect(api):
    # Claude's client_id with an attacker redirect: the shipped copy fixes the
    # redirect_uris, so authorize refuses rather than sending a code anywhere else.
    r = api.get("/oauth/authorize", params={
        "client_id": "https://claude.ai/oauth/mcp-oauth-client-metadata",
        "redirect_uri": "https://evil.example/steal",
        "response_type": "code", "state": "x",
        "code_challenge": "abc", "code_challenge_method": "S256",
    })
    assert r.status_code == 400
    assert r.json()["error"] == "invalid_client" or "redirect" in r.text.lower()


# ── Q5: can PKCE or the loopback rule be bypassed? ──────────────────────────────


def test_safe_pkce_is_required_and_verifier_is_checked(api, conn):
    family_with_user(conn, "Sharma", USER_A)
    a = Assistant(api)
    a.register()
    # No challenge at all: refused before a request is parked.
    none = a.authorize(None)
    assert none.status_code == 302 and "invalid_request" in none.headers["location"]
    # A challenge, then the wrong verifier at exchange: no tokens.
    verifier, challenge = __import__("testsupport_assistant", fromlist=["pkce_pair"]).pkce_pair()
    sent = a.authorize(challenge)
    request_id = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(
        __import__("urllib.parse", fromlist=["urlsplit"]).urlsplit(sent.headers["location"]).query
    )["request"][0]
    approved = a.approve(request_id, session_token(USER_A))
    code = __import__("urllib.parse", fromlist=["parse_qs"]).parse_qs(
        __import__("urllib.parse", fromlist=["urlsplit"]).urlsplit(approved.json()["redirect"]).query
    )["code"][0]
    bad = a.token(grant_type="authorization_code", code=code,
                  code_verifier="not-the-verifier", redirect_uri=a.redirect_uri)
    assert bad.status_code == 400 and bad.json()["error"] == "invalid_grant"


def test_safe_loopback_exemption_only_helps_loopback_registrations(api, conn):
    # A client registered with an https callback cannot pivot to a loopback URI.
    a = Assistant(api)
    a.register(redirect_uris=["https://claude.ai/api/mcp/auth_callback"])
    r = a.authorize("chal", redirect_uri="http://127.0.0.1:9999/api/mcp/auth_callback")
    assert r.status_code == 400 and "redirect" in r.text.lower()
    # And redirect_allowed itself: loopback port ignored only for a loopback registration.
    assert assistant_auth.redirect_allowed(["http://localhost/cb"], "http://localhost:55/cb")
    assert not assistant_auth.redirect_allowed(["https://claude.ai/cb"], "http://127.0.0.1:55/cb")
    assert not assistant_auth.redirect_allowed(["http://localhost/cb"], "http://localhost/OTHER")


# ── Q6: can the claim route hand out a token for someone else's parent? ─────────


def test_safe_claim_needs_the_secret_slug_and_returns_only_that_parents_token(api, conn):
    fam = provision_family(conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")],
                           base_url=BASE_URL, platform="android")
    [amma] = fam.parents
    # A random/guessed slug is a 404 — the slug is the only identity in the URL.
    assert api.post("/s/notarealslug000000000000/claim",
                    json={"platform": "android"}).status_code == 404
    # The real slug hands back the link's OWN parent's token, nobody else's.
    slug = amma.setup_url.rsplit("/", 1)[-1]
    body = api.post(f"/s/{slug}/claim", json={"platform": "android"}).json()
    assert body["device_token"] == amma.device_token


# ── Q7: household_pings / journal_entries past RLS by `authenticated`? ──────────


def test_safe_authenticated_cannot_write_household_pings(authed, conn):
    fam = family_with_user(conn, "Sharma", USER_A)
    dev = conn.execute(
        "insert into household_devices (parent_id, kind, token) values "
        "(%s, 'plug', %s) returning id",
        (fam.parents[0].parent_id, "a" * 40),
    ).fetchone()["id"]
    as_user(authed, USER_A)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute("insert into household_pings (device_id, ts_utc) values (%s, now())", (dev,))


def test_safe_authenticated_cannot_read_another_circles_devices_or_pings(authed, conn):
    a = family_with_user(conn, "Sharma", USER_A)
    b = family_with_user(conn, "Whitaker", USER_B, parent="Linda")
    devs = {}
    for fam in (a, b):
        devs[fam.family_id] = conn.execute(
            "insert into household_devices (parent_id, kind, token) values (%s, 'plug', %s) "
            "returning id",
            (fam.parents[0].parent_id, fam.family_id.hex[:8] + "z" * 32),
        ).fetchone()["id"]
        conn.execute("insert into household_pings (device_id, ts_utc) values (%s, now())",
                     (devs[fam.family_id],))
    as_user(authed, USER_A)
    # The device table carries no grant at all.
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        authed.execute("select * from household_devices")
    # The view and the pings show only A's circle.
    view = authed.execute("select id from household_devices_view").fetchall()
    assert {r["id"] for r in view} == {devs[a.family_id]}
    seen = authed.execute("select device_id from household_pings").fetchall()
    assert {r["device_id"] for r in seen} == {devs[a.family_id]}


def test_safe_authenticated_cannot_touch_another_familys_journal(authed, conn):
    a = family_with_user(conn, "Sharma", USER_A)
    b = family_with_user(conn, "Whitaker", USER_B, parent="Linda")
    conn.execute("insert into journal_entries (family_id, author_label, body, kind, created_utc) "
                 "values (%s, 'Owner', 'B private note', 'note', now())", (b.family_id,))
    as_user(authed, USER_A)
    # Cannot read B's note.
    assert authed.execute("select count(*) as n from journal_entries").fetchone()["n"] == 0
    # Cannot insert into B's family.
    with pytest.raises(psycopg.errors.Error):
        authed.execute("insert into journal_entries (family_id, author_label, body, kind, "
                       "created_utc) values (%s, 'x', 'forged', 'note', now())", (b.family_id,))


def test_safe_a_browser_client_cannot_forge_journal_authorship(authed, conn):
    a = family_with_user(conn, "Sharma", USER_A)
    b = family_with_user(conn, "Whitaker", USER_B, parent="Linda")
    b_seat = conn.execute("select id from members where family_id = %s and role = 'admin' "
                          "order by created_utc limit 1", (b.family_id,)).fetchone()["id"]
    as_user(authed, USER_A)
    # Insert into A's own family but claim B's member as the author.
    authed.execute("insert into journal_entries (family_id, author_member_id, author_label, body, "
                   "kind, created_utc) values (%s, %s, 'spoof', 'mine', 'note', now())",
                   (a.family_id, b_seat))
    got = conn.execute("select author_member_id from journal_entries where family_id = %s",
                       (a.family_id,)).fetchone()["author_member_id"]
    a_seat = conn.execute("select id from members where family_id = %s and auth_user_id = %s",
                          (a.family_id, USER_A)).fetchone()["id"]
    # The trigger overrode the forged author with A's own seat from the JWT.
    assert got == a_seat


# ── Q8: can the flood counters be starved? ──────────────────────────────────────


def test_flood_counter_keying_and_eviction(clock):
    from kettle.waitlist import FloodCounter
    fc = FloodCounter(limit=5, window=timedelta(hours=1), max_keys=3)
    now = clock()
    # One key is blocked after five hits.
    for _ in range(5):
        assert fc.allow("victim", now)
    assert not fc.allow("victim", now)
    # Rotating three OTHER keys evicts the victim's counter (oldest-out), which
    # RESETS the victim — it never lets the blocked key send more from its own key.
    for k in ("k1", "k2", "k3"):
        fc.allow(k, now)
    assert fc.allow("victim", now)  # readmitted only because its history was dropped
    # A distinct key per request is never throttled: the guard is per-key, so a
    # caller who can vary the key (a spoofable X-Forwarded-For with no Fly-Client-IP)
    # bypasses it — the table cap is the backstop (DECISIONS 307/308).
    assert all(fc.allow(f"spoof-{i}", now) for i in range(50))


# ── Q9: does anything log a token, a hash, a body, or an IP? ────────────────────


def test_safe_ping_and_claim_do_not_log_the_token_or_slug(api, conn, caplog):
    """The product's own loggers (`kettle.*`) must carry no token or full slug.

    caplog also sees the TestClient's httpx logger, which prints the request URL
    (token and all) — that line is the test harness, not kettle, and in prod
    uvicorn runs with --no-access-log so no equivalent is emitted. We assert
    against kettle's records only, then confirm the leaking line was httpx's."""
    import logging
    fam = provision_family(conn, "Sharma", "Asia/Kolkata", [("Amma", None, "Mom")],
                           base_url=BASE_URL, platform="android")
    [amma] = fam.parents
    slug = amma.setup_url.rsplit("/", 1)[-1]
    with caplog.at_level(logging.DEBUG):
        api.get(f"/p/{amma.device_token}/unlock")
        body = api.post(f"/s/{slug}/claim", json={"platform": "android"}).json()
    kettle_text = "\n".join(
        r.getMessage() for r in caplog.records if r.name.startswith("kettle")
    )
    assert amma.device_token not in kettle_text
    assert body["device_token"] not in kettle_text
    assert slug not in kettle_text  # only the last 6 chars appear, the masked ops form
    assert slug[-6:] in kettle_text
    # The only records carrying the full token are the test client's httpx lines.
    leaking = [r.name for r in caplog.records if amma.device_token in r.getMessage()]
    assert leaking and all(not n.startswith("kettle") for n in leaking), leaking


def test_safe_oauth_token_exchange_logs_no_token(api, conn, caplog):
    import logging
    family_with_user(conn, "Sharma", USER_A)
    with caplog.at_level(logging.DEBUG):
        a = Assistant(api)
        a.connect(USER_A, scope="kettle:write")
    assert a.access_token not in caplog.text
    assert a.refresh_token not in caplog.text
    assert assistant_auth.sha256(a.access_token) not in caplog.text


# ── FINDING: unauthenticated blind SSRF via a CIMD client_id ────────────────────


def test_finding_cimd_client_id_makes_the_server_fetch_any_https_host(settings, notifier, conn):
    """UNAUTHENTICATED: /oauth/authorize and /oauth/token fetch whatever https
    URL the client_id names, with no host allowlist and no private-range block.
    A recording transport stands in for the real httpx client the app builds in
    production; the request it records is the request prod would put on the wire."""
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json={})  # a non-CIMD body: still fetched first

    rec = httpx.Client(transport=httpx.MockTransport(handler))
    with TestClient(create_app(settings, notifier, jwks_client=jwks_client(),
                               cimd_client=rec)) as api:
        internal = "https://[fdaa:0:1::3]:4280/internal/secrets"
        r = api.get("/oauth/authorize", params={
            "client_id": internal, "redirect_uri": "https://claude.ai/cb",
            "response_type": "code", "code_challenge": "c", "code_challenge_method": "S256",
        })
        # The response is a harmless invalid_client (blind: nothing reflected)…
        assert r.status_code == 400
        # …but the server already reached out to the attacker-chosen internal host.
        assert internal in seen, seen
        # /oauth/token is the same unauthenticated entry point.
        seen.clear()
        api.post("/oauth/token", data={"grant_type": "authorization_code",
                                       "client_id": "https://169.254.169.254/latest/",
                                       "code": "x", "code_verifier": "y",
                                       "redirect_uri": "z"},
                 headers={"content-type": "application/x-www-form-urlencoded"})
        assert "https://169.254.169.254/latest/" in seen, seen


# ── low: memory's `since` is unvalidated (robustness, not exposure) ─────────────


def test_low_memory_since_is_unvalidated(api, conn):
    family_with_user(conn, "Sharma", USER_A)
    a = Assistant(api)
    a.connect(USER_A, scope="kettle:read")
    r = a.call("memory", {"since": "not-a-date"})
    body = r.json()
    # It does not 500 the process, but unlike parent_day it surfaces a DB error
    # result rather than a sentence; contrast parent_day's floor check.
    assert r.status_code == 200
    assert body.get("result", {}).get("isError") or "error" in body
