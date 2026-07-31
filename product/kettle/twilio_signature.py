"""Twilio request signature validation (stdlib only, no SDK).

Twilio signs an inbound webhook by concatenating the full request URL with every
POST parameter in sorted key order, HMAC-SHA1'ing that with the account's auth
token, and base64-encoding the result into `X-Twilio-Signature`.

Reimplemented here rather than pulled in as a dependency: it is twelve lines of
hmac, and the ladder's inbound path is one place where "what exactly is being
verified" should be readable in this repo rather than in someone else's.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from collections.abc import Mapping


def expected_signature(auth_token: str, url: str, params: Mapping[str, str]) -> str:
    """The signature Twilio would send for this URL and these POST params."""
    payload = url
    for key in sorted(params):
        payload += key + params[key]
    digest = hmac.new(
        auth_token.encode("utf-8"), payload.encode("utf-8"), hashlib.sha1
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


def is_valid(
    auth_token: str, url: str, params: Mapping[str, str], signature: str | None
) -> bool:
    """Constant-time check of an inbound webhook's signature.

    An empty auth token never validates: an unconfigured deployment must reject
    inbound requests, not accept every one of them.
    """
    if not auth_token or not signature:
        return False
    return hmac.compare_digest(expected_signature(auth_token, url, params), signature)
