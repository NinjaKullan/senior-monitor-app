"""Twilio request-signature verification for the reply webhook (spec 007 §2.6).

Rebuilt for Wave C rather than resurrected: the retired spec-004 module did
this job for `/twilio/inbound`, and the shape was worth keeping while the code
was not. Twilio signs every webhook it sends: it concatenates the full public
URL with every POST parameter, sorted by name, as name + value with no
separators, HMAC-SHA1s that under the account's auth token, and base64-encodes
the digest into the `X-Twilio-Signature` header.

Two details are load-bearing:

* **The URL is the one Twilio was configured with**, not the one the app sees
  behind Fly's proxy (which arrives as plain HTTP on an internal port). The
  caller builds it from PUBLIC_BASE_URL + the route path, so verification is
  against the address that was actually signed.
* **The comparison is constant-time** (`hmac.compare_digest`). A signature
  check that leaks its prefix by timing is a signature check that can be
  forged byte by byte.

The parameters include the message body. That is the ONLY thing the body is
used for — the caller verifies, extracts the sender, and discards everything
else, per §2.6's content-blind rule.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from collections.abc import Mapping


def expected_signature(auth_token: str, url: str, params: Mapping[str, str]) -> str:
    """The signature Twilio would produce for this request."""
    payload = url + "".join(name + params[name] for name in sorted(params))
    digest = hmac.new(
        auth_token.encode("utf-8"), payload.encode("utf-8"), hashlib.sha1
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def verify_signature(
    auth_token: str, url: str, params: Mapping[str, str], signature: str
) -> bool:
    """True only for a request signed with this auth token for this URL.

    An empty token or an empty signature is False, never a pass-through: the
    absence of a credential must fail closed on a route that can cancel an
    escalation.
    """
    if not auth_token or not signature:
        return False
    return hmac.compare_digest(expected_signature(auth_token, url, params), signature)
