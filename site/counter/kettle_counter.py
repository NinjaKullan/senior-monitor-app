"""Count what the site served, ship only the counts (DECISIONS 201/211).

The design is docs/log-summary-job-design.md, option C: count at the edge,
persist nothing raw. This process is the edge. It runs nginx as its child,
reads nginx's access log off that child's stdout, keeps a tally in memory, and
POSTs the tally to kettle-api. What it never does is write a request line
anywhere, hold one for longer than the microseconds it takes to bucket it, or
send anything but {day, path, count} triples over the wire.

Three properties are load-bearing, in this order:

1. **Serving outranks counting, always.** Every counting operation runs inside
   a try/except, and the outermost loop's only guaranteed job is to keep
   draining nginx's stdout. If the tally logic fails permanently the process
   degrades to a pure pass-through pipe and nginx keeps serving; it does not
   exit and take the webserver with it. A metrics hiccup must never touch
   serving is not a slogan here, it is the exception structure.
2. **Nothing identifying is ever in scope.** The log format nginx is given
   (site/nginx.conf, `kettle_counts`) carries a timestamp, a status and a
   path — no address, no user agent, no referer, no query string. So there is
   no IP in this process to leak even by accident; the privacy guarantee is
   made upstream by the format, not downstream by discipline here.
3. **Off-allowlist paths are anonymised before they are counted.** A path that
   is not in the shipped sitemap becomes the single literal bucket `other`
   before it reaches the tally, so a URL someone probed us with is never
   written down, never shipped, and never stored.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import signal
import subprocess
import sys
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

log = logging.getLogger("kettle.counter")

#: Everything not on the allowlist collapses to this one bucket.
OTHER = "other"

#: Where the shipped sitemap lives inside the image. The allowlist is DERIVED
#: from it rather than written out again here, so a page added to the site is
#: counted without a second edit, and the two lists cannot drift apart. The
#: sitemap already carries the PDFs, which is why "sitemap paths + PDFs" needs
#: no separate PDF rule.
SITEMAP_PATH = "/usr/share/nginx/html/sitemap.xml"

#: nginx writes: ISO8601 time, status, path. Anchored, and anything that does
#: not match is dropped rather than guessed at.
LINE_RE = re.compile(r"^(\S+) (\d{3}) (\S*)$")


def allowlist_from_sitemap(text: str) -> frozenset[str]:
    """Path set from a sitemap document, or an empty set if it will not parse.

    An unparseable sitemap must not take the site down, so this returns empty
    and the counter simply buckets everything as `other` — degraded, honest,
    and serving is untouched.
    """
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        log.warning("sitemap did not parse; counting everything as %s", OTHER)
        return frozenset()
    paths = set()
    for loc in root.iter():
        if not loc.tag.endswith("loc") or not (loc.text or "").strip():
            continue
        url = loc.text.strip()
        # Keep only the path. Deliberately string surgery rather than urlparse:
        # the only thing wanted is what follows the host, and a sitemap entry
        # that is already a bare path works unchanged.
        after_scheme = url.split("://", 1)[-1]
        slash = after_scheme.find("/")
        paths.add(normalise_path(after_scheme[slash:] if slash != -1 else "/"))
    return frozenset(paths)


def normalise_path(path: str) -> str:
    """Fold a served path to the form the sitemap uses.

    nginx logs the post-rewrite `$uri`, so a request for `/blog/` is logged as
    `/blog/index.html` once the index module has resolved it. Folding that back
    is what makes a sitemap-derived allowlist match real traffic at all.
    """
    # Defensive: the log format carries no query string, but a `?` arriving by
    # any route must not become part of a bucket name.
    path = path.split("?", 1)[0].split("#", 1)[0]
    if not path.startswith("/"):
        return path
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    return path or "/"


def counted(status: int) -> bool:
    """Was this response a page or a file actually served?

    2xx is a served body; 304 is a returning reader whose browser already had
    it, which is a read either way. Everything else — redirects, 404s, errors —
    is not a view of the thing and is not counted. The design doc tracked a
    status CLASS in memory while giving the table no column to put one in
    (three fields, and they are literally three); folding the class away at the
    counter is how that squares, and it is recorded in DECISIONS 212.
    """
    return 200 <= status < 300 or status == 304


class Tally:
    """Per-day counts, guarded by a lock, cleared only when the day rolls.

    Cumulative for the day rather than since-last-flush: each flush ships the
    running total and the endpoint keeps the high-water mark, which is what
    makes a flush idempotent and a lost flush harmless.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._days: dict[str, dict[str, int]] = {}

    def add(self, day: str, path: str) -> None:
        with self._lock:
            counts = self._days.setdefault(day, {})
            counts[path] = counts.get(path, 0) + 1

    def snapshot(self) -> dict[str, dict[str, int]]:
        with self._lock:
            return {day: dict(counts) for day, counts in self._days.items()}

    def forget_before(self, day: str) -> None:
        """Drop days older than `day` once they have been shipped."""
        with self._lock:
            for stale in [d for d in self._days if d < day]:
                del self._days[stale]


def ship(
    endpoint: str,
    token: str,
    day: str,
    counts: dict[str, int],
    timeout: float = 10.0,
) -> bool:
    """POST one day's counts. Returns True on 2xx; never raises.

    Fail silent-but-logged, per the design: a metrics endpoint that is down, a
    token that is wrong, DNS that is having a moment — each is a log line and a
    retry on the next flush, and none of them is allowed to become an exception
    that unwinds into the drain loop.
    """
    body = json.dumps({"day": day, "counts": counts}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-kettle-metrics-token": token,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 300
    except urllib.error.HTTPError as exc:
        # The status is worth a log line; the token never is.
        log.warning("metrics POST refused: HTTP %s", exc.code)
    except Exception as exc:  # noqa: BLE001 - counting never breaks serving
        log.warning("metrics POST failed: %s", type(exc).__name__)
    return False


def flush(tally: Tally, endpoint: str, token: str, today: str) -> None:
    """Ship every day held, then forget the ones that are finished.

    Today's row is shipped too, and re-shipped on the next flush with a larger
    number — which is exactly why the endpoint keeps a high-water mark instead
    of adding. Under the site app's `auto_stop_machines` this is the difference
    between a working counter and one that reports whatever happened in the
    last few idle minutes before midnight.
    """
    for day, counts in sorted(tally.snapshot().items()):
        if counts and ship(endpoint, token, day, counts):
            log.info("shipped %d paths for %s", len(counts), day)
    tally.forget_before(today)


def utc_day(now: datetime | None = None) -> str:
    return (now or datetime.now(UTC)).strftime("%Y-%m-%d")


def consume(line: str, tally: Tally, allowlist: frozenset[str]) -> None:
    """Bucket one access-log line. Anything unrecognised is dropped."""
    match = LINE_RE.match(line.strip())
    if not match:
        return
    stamp, status, raw_path = match.groups()
    if not counted(int(status)):
        return
    path = normalise_path(raw_path)
    # The day comes from the log line's own timestamp, so a line written just
    # before midnight lands in the day it belongs to even if it is read after.
    day = stamp[:10] if len(stamp) >= 10 and stamp[4] == "-" else utc_day()
    tally.add(day, path if path in allowlist else OTHER)


def read_sitemap(path: str = SITEMAP_PATH) -> frozenset[str]:
    try:
        with open(path, encoding="utf-8") as handle:
            return allowlist_from_sitemap(handle.read())
    except OSError:
        log.warning("no sitemap at %s; counting everything as %s", path, OTHER)
        return frozenset()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    endpoint = os.environ.get("SITE_METRICS_ENDPOINT", "").strip()
    token = os.environ.get("SITE_METRICS_TOKEN", "").strip()
    interval = int(os.environ.get("SITE_METRICS_INTERVAL_S", "300"))
    counting = bool(endpoint and token)
    if not counting:
        # Unconfigured is a supported state, not an error: the image serves the
        # site with no metrics at all until the founder sets the secret, and
        # that path has to be the boring one.
        log.info("metrics not configured; serving only")

    allowlist = read_sitemap() if counting else frozenset()
    tally = Tally()

    nginx = subprocess.Popen(
        ["nginx", "-g", "daemon off;"],
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        bufsize=1,
    )

    def forward(signum: int, _frame: object) -> None:
        """Hand signals to nginx; Fly's stop is a TERM and it must reach it."""
        with contextlib.suppress(Exception):
            nginx.send_signal(signum)

    signal.signal(signal.SIGTERM, forward)
    signal.signal(signal.SIGINT, forward)

    stop = threading.Event()

    def flusher() -> None:
        while not stop.wait(interval):
            try:
                flush(tally, endpoint, token, utc_day())
            except Exception:  # noqa: BLE001 - never unwind into serving
                log.warning("flush failed", exc_info=False)

    if counting:
        threading.Thread(target=flusher, daemon=True, name="flusher").start()

    # THE drain loop. Its contract is that nginx's stdout is always read, so
    # the pipe cannot fill and block a worker mid-response. Counting is a
    # best-effort side effect inside it, and a permanently failing tally
    # degrades this to a plain pipe rather than stopping it.
    assert nginx.stdout is not None
    for line in nginx.stdout:
        sys.stdout.write(line)
        if counting:
            # Serving outranks counting: a bad line is dropped, never raised.
            with contextlib.suppress(Exception):
                consume(line, tally, allowlist)
    sys.stdout.flush()

    stop.set()
    code = nginx.wait()
    if counting:
        # A clean stop ships what the day has so far. Fly's auto-stop is a
        # TERM, so this is the common path, not the rare one.
        try:
            flush(tally, endpoint, token, utc_day())
        except Exception:  # noqa: BLE001
            log.warning("final flush failed")
    return code


if __name__ == "__main__":
    sys.exit(main())
