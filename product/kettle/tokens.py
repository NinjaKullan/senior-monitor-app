"""Device tokens.

Per device, never per family and never guessable: the pilot's `who=mom` URL was
fine for two phones the founder owned and is not fine for strangers. The token
is the whole identity of a ping, so it is generated server-side, url-safe (it
sits in a path segment), and long enough that enumeration is pointless.

Humans never type these. Delivery is a pre-built shortcut behind a tapped iCloud
link or a QR scan.
"""

from __future__ import annotations

import secrets

# 18 random bytes -> 24 url-safe characters, comfortably over the 20 the schema
# enforces with a CHECK constraint.
TOKEN_BYTES = 18


def new_device_token() -> str:
    """Generate a fresh url-safe device token."""
    return secrets.token_urlsafe(TOKEN_BYTES)
