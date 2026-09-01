#!/usr/bin/env python3
"""Create and submit the v5 ask template through Twilio's Content API.

DECISIONS 217. The founder runs this; it is not wired into the app and nothing
imports it.

**Why a script rather than the console.** Meta approved v4 but recategorized it
Marketing on the way in, and Meta refuses to deliver marketing templates to US
numbers — so the ask never reached a US parent (DECISIONS 216, error 63049).
The fix is to submit as UTILITY with `allow_category_change=false`, so Meta
either approves it as Utility or REJECTS it, instead of quietly downgrading it
into a category that cannot be delivered. The console cannot set that flag.
The Content API can, which is the whole reason this file exists.

Credentials come from the environment and are never written down here:

    export TWILIO_ACCOUNT_SID=AC...
    export TWILIO_AUTH_TOKEN=...
    python3 tools/submit_ask_template.py

It prints the new Content SID, submits it for WhatsApp approval, then polls
until Meta says Approved or Rejected — printing Meta's own rejection words
verbatim, because a paraphrased rejection reason is a rejection reason nobody
can act on.

Nothing here touches the running system: no Fly secret is set, no family is
moved, and the sandbox stays the production path until a dark-stage pass shows
a template actually delivering to a US number.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from base64 import b64encode

CONTENT_API = "https://content.twilio.com/v1/Content"
APPROVAL_API = "https://content.twilio.com/v1/Content/{sid}/ApprovalRequests"
APPROVAL_FETCH = "https://content.twilio.com/v1/Content/{sid}/ApprovalRequests"

TEMPLATE_NAME = "kettle_ask_parent_v5"
LANGUAGE = "en"
CATEGORY = "UTILITY"

#: The ruled body, VERBATIM (DECISIONS 217). Bare U+1F44D with no variation
#: selector, straight apostrophe. `{{1}}` is Meta's placeholder syntax; the
#: same sentence lives in kettle/outbound_templates.py as `{owner_name}` for
#: the sandbox path, and a test pins the two to the same words.
BODY = (
    "{{1}} asked Kettle to check in with you when a morning looks different. "
    "Is everything okay? Reply with a \U0001f44d when you're free."
)

#: Meta wants a sample for each variable so a reviewer can read the message as
#: a person would receive it.
VARIABLES = {"1": "Priya"}

POLL_SECONDS = 15
POLL_ATTEMPTS = 80  # ~20 minutes; approvals are usually minutes


def _auth_header() -> str:
    sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    if not sid or not token:
        sys.exit(
            "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in the "
            "environment. They are never stored in this repository."
        )
    return "Basic " + b64encode(f"{sid}:{token}".encode()).decode()


def _request(url: str, payload: dict | None = None, method: str = "GET") -> dict:
    """One API call. Errors print Twilio's own body and stop.

    Deliberately urllib: this is a founder-run script in a repo that pins its
    dependencies, and it should not need an install to be runnable.
    """
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", _auth_header())
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read() or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        sys.exit(f"Twilio said HTTP {exc.code}: {body}")
    except urllib.error.URLError as exc:
        sys.exit(f"could not reach Twilio: {exc.reason}")


def create_content() -> str:
    """Create the twilio/text content resource. Returns its SID."""
    payload = {
        "friendly_name": TEMPLATE_NAME,
        "language": LANGUAGE,
        "variables": VARIABLES,
        # twilio/text and nothing else: no buttons, no quick replies, no media.
        # DECISIONS 205 — Meta forbids emoji in template buttons, so the body
        # does the inviting and the 👍 is typed by the parent.
        "types": {"twilio/text": {"body": BODY}},
    }
    created = _request(CONTENT_API, payload, method="POST")
    sid = created.get("sid", "")
    if not sid:
        sys.exit(f"no SID in Twilio's response: {created}")
    return sid


def submit_for_approval(sid: str) -> dict:
    """Submit for WhatsApp approval as Utility, category change DISALLOWED."""
    payload = {
        "name": TEMPLATE_NAME,
        "category": CATEGORY,
        # THE point of this script. False means Meta must either approve this
        # as Utility or reject it — it may not recategorize it to Marketing,
        # which is what silently happened to v4 and made it undeliverable to
        # every US number (DECISIONS 216).
        "allow_category_change": False,
    }
    return _request(APPROVAL_API.format(sid=sid), payload, method="POST")


def _status_of(record: dict) -> tuple[str, str]:
    """(status, rejection reason) out of an approval record, shape-tolerant."""
    whatsapp = record.get("whatsapp") or record
    status = str(whatsapp.get("status", "") or record.get("status", "")).lower()
    reason = str(
        whatsapp.get("rejection_reason", "") or record.get("rejection_reason", "") or ""
    )
    return status, reason


def poll(sid: str) -> int:
    """Poll until Approved or Rejected. Returns a process exit code."""
    for attempt in range(1, POLL_ATTEMPTS + 1):
        record = _request(APPROVAL_FETCH.format(sid=sid))
        status, reason = _status_of(record)
        print(f"[{attempt:>3}] status: {status or 'unknown'}")
        if status == "approved":
            print("\nAPPROVED as", CATEGORY)
            print("Content SID:", sid)
            print(
                "\nNothing is live yet. Setting TWILIO_ASK_CONTENT_SID is a "
                "separate, deliberate step, and the dark stage restarts from "
                "step 1 (DECISIONS 216/217)."
            )
            return 0
        if status == "rejected":
            # Meta's words, unedited. A paraphrase here would cost the founder
            # the one piece of information the whole attempt was for.
            print("\nREJECTED. Meta's reason, verbatim:")
            print(reason or "(Twilio returned no rejection reason)")
            print("\nFull record:")
            print(json.dumps(record, indent=2, sort_keys=True))
            return 1
        time.sleep(POLL_SECONDS)
    print("\nStill pending after the polling window; check the Twilio console.")
    print("Content SID:", sid)
    return 2


def main() -> int:
    print(f"Creating {TEMPLATE_NAME} ({LANGUAGE}, one variable, no buttons)…")
    print("Body:")
    print(BODY)
    sid = create_content()
    print("\nContent SID:", sid)

    print(f"\nSubmitting for WhatsApp approval as {CATEGORY}, "
          "allow_category_change=false…")
    submitted = submit_for_approval(sid)
    status, _ = _status_of(submitted)
    print("submitted:", status or "pending")

    return poll(sid)


if __name__ == "__main__":
    sys.exit(main())
