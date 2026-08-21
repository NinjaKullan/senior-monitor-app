"""The hosted per-parent setup page (spec 005b §4.3).

Served by this API on purpose: the page's one live behaviour — the verify
check — asks "did the server just see a ping", and the server that saw it is
this one. Same origin, no CORS surface, no coupling to the child app's build.

What this page is: consent in plain language, the visual steps, the
pre-empted permission warning, and the live verify-by-prediction check.
What it never is: a file. Delivery is WhatsApp document attachments
(DECISIONS 117); no route here serves or links a `.shortcut`.

The URL is the credential (DECISIONS 102), so every response is
`Cache-Control: no-store`, the document carries no-referrer and noindex, and
the slug appears nowhere in the HTML — the script derives its state URL from
`location.pathname`, so the secret lives in the address bar alone.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

import psycopg
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from kettle import db
from kettle import setup_copy as copy
from kettle.signals import SIGNAL_LABELS, shortcut_name
from kettle.timeutil import now_utc

router = APIRouter()

#: Header on every /s/* response. The page is a credential's escort; nothing
#: about it may outlive the link in a cache (the DECISIONS 111 posture).
CACHE_CONTROL = "no-store"

#: The page runs its own inline script and styles and talks only to us.
CSP = (
    "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
    "connect-src 'self'; base-uri 'none'; form-action 'none'"
)

#: Per-app triggers that read "App → Is Opened". `routine` renders its own
#: multi-app sentence. A vocabulary key outside every trigger family refuses
#: to render rather than inheriting a default — an invented instruction on
#: this page would send a parent building the wrong automation.
APP_OPEN_SIGNALS = frozenset({"whatsapp", "youtube", "news"})

TILE_GLYPHS = {
    "routine": "◎",
    "charger": "⚡︎",
    "charge_on": "⚡︎",
    "charge_off": "⚡︎",
    "device_alive": "☀︎",
}
TILE_GLYPH_DEFAULT = "◎"


def automation_row(signal: str, parent_name: str) -> str:
    """The one-line automation instruction for a signal, or a loud refusal."""
    shortcut = shortcut_name(signal)
    if signal == "routine":
        return copy.AUTO_ROW_ROUTINE.format(parent=parent_name, shortcut=shortcut)
    if signal in APP_OPEN_SIGNALS:
        return copy.AUTO_ROW_APP.format(label=SIGNAL_LABELS[signal], shortcut=shortcut)
    if signal == "charger":
        return copy.AUTO_ROW_CHARGER_BOTH.format(shortcut=shortcut)
    if signal == "charge_on":
        return copy.AUTO_ROW_CHARGE_ON.format(shortcut=shortcut)
    if signal == "charge_off":
        return copy.AUTO_ROW_CHARGE_OFF.format(shortcut=shortcut)
    if signal == "device_alive":
        return copy.AUTO_ROW_TIME_OF_DAY.format(shortcut=shortcut)
    raise ValueError(f"no automation instruction for signal {signal!r}")


def browser_consent_applies(keys: list[str]) -> bool:
    """Does this set need the browser consent sentence (spec §4.5)?

    Empty until DECISIONS 100 lands a browser key, but wired now: people hear
    "browsing" even though we only see that an app opened, so the sentence
    must appear the day such a signal exists — not be rediscovered then.
    """
    return any(k in copy.BROWSER_SIGNALS for k in keys)


def verify_app_label(signals: list[dict[str, Any]]) -> str | None:
    """What the verify step asks the parent to open.

    Alarm-grade only, per product law #6: the green check anchors a person's
    card, so a charger edge or a timer must never be what turns it on. None
    means the set has nothing a card may be promised for.
    """
    for row in signals:
        if row["alarm_grade"]:
            if row["signal"] == "routine":
                return copy.VERIFY_APP_ROUTINE
            return SIGNAL_LABELS.get(row["signal"], row["signal"])
    return None


@dataclass(frozen=True)
class SetupState:
    """A slug resolved to what the page may say."""

    status: str  # "live" | "expired" | "revoked" | "unknown"
    parent_id: Any | None = None
    parent_name: str | None = None
    child_name: str | None = None
    signals: tuple[dict[str, Any], ...] = ()


def resolve_setup(conn: psycopg.Connection, slug: str, now: datetime) -> SetupState:
    """Decide what a slug is entitled to.

    Order matters: a revoked device outranks everything (revoking the token
    kills the URL, spec §4.2), a rotated link is gone even if unexpired, and
    expiry is checked last. The dead ends still name the family's owner —
    that is the child contact path acceptance 3 requires — but never a signal,
    a step, or a file.
    """
    row = db.setup_link_by_slug(conn, slug)
    if row is None:
        return SetupState(status="unknown")

    child = db.family_owner_name(conn, row["family_id"])
    if not row["device_active"] or row["device_revoked_utc"] or row["revoked_utc"]:
        return SetupState(status="revoked", child_name=child)
    if row["expires_utc"] <= now:
        return SetupState(status="expired", child_name=child)

    signals = tuple(db.parent_active_signals(conn, row["parent_id"]))
    return SetupState(
        status="live",
        parent_id=row["parent_id"],
        parent_name=row["parent_name"],
        child_name=child,
        signals=signals,
    )


# --- rendering ---------------------------------------------------------------

_CSS = """
:root {
  --kettle: #FD6631; --kettle-soft: #FFF0EA; --ink: #2B2320; --ink-soft: #6B5F58;
  --paper: #FAF7F4; --card: #FFFFFF; --green: #2E9E5B; --green-soft: #E8F6EE;
  --line: #EAE2DC;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--paper); color: var(--ink);
  max-width: 430px; margin: 0 auto; min-height: 100vh;
  display: flex; flex-direction: column;
}
header {
  padding: 18px 20px 14px; background: var(--card);
  border-bottom: 1px solid var(--line); display: flex; align-items: center; gap: 10px;
}
.mark {
  width: 34px; height: 34px; border-radius: 9px; background: var(--kettle); flex: none;
  display: grid; place-items: center; color: #fff; font-size: 18px; font-weight: 700;
}
header .who { font-size: 15px; font-weight: 650; }
header .sub { font-size: 12px; color: var(--ink-soft); }
.helper {
  margin-left: auto; font-size: 11px; color: var(--ink-soft);
  display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none;
}
.helper .pill {
  width: 34px; height: 20px; border-radius: 10px; background: #D8CFC8;
  position: relative; transition: background .15s;
}
.helper .pill::after {
  content: ""; position: absolute; top: 2px; left: 2px; width: 16px; height: 16px;
  border-radius: 50%; background: #fff; transition: left .15s;
}
.helper.on .pill { background: var(--kettle); }
.helper.on .pill::after { left: 16px; }
.dots { display: flex; gap: 6px; justify-content: center; padding: 14px 0 4px; }
.dots span { width: 7px; height: 7px; border-radius: 50%; background: #D8CFC8; }
.dots span.done { background: var(--green); }
.dots span.now { background: var(--kettle); }
main { flex: 1; padding: 10px 22px 24px; display: flex; flex-direction: column; }
.screen { display: none; flex: 1; flex-direction: column; }
.screen.active { display: flex; }
h1 { font-size: 22px; line-height: 1.25; margin: 8px 0 6px; letter-spacing: -.2px; }
.say { font-size: 15px; line-height: 1.5; color: var(--ink-soft); margin-bottom: 14px; }
.say b { color: var(--ink); }
.bubble {
  position: relative; background: var(--kettle-soft); border: 1px solid #F8CDB9;
  border-radius: 14px; padding: 12px 14px; font-size: 14px; line-height: 1.45;
  margin: 10px 0 0 46px;
}
.bubble::before {
  content: ""; position: absolute; left: -8px; top: 16px;
  border: 8px solid transparent; border-right-color: var(--kettle-soft); border-left: 0;
}
.bubblerow { display: flex; align-items: flex-start; }
.avatar {
  width: 36px; height: 36px; border-radius: 50%; background: var(--kettle);
  color: #fff; display: grid; place-items: center; font-size: 16px; flex: none; margin-top: 10px;
}
.visual {
  background: var(--card); border: 1px solid var(--line); border-radius: 16px;
  padding: 16px; margin: 14px 0; text-align: center;
}
.visual .cap { font-size: 12px; color: var(--ink-soft); margin-top: 10px; }
.appicon {
  width: 64px; height: 64px; border-radius: 15px; margin: 0 auto;
  display: grid; place-items: center; font-size: 30px; color: #fff;
  background: linear-gradient(135deg, #4DA8F7, #E85AA0);
}
.tiles { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
.tile {
  flex: 1; min-width: 120px; max-width: 150px; background: var(--kettle); border-radius: 14px;
  color: #fff; padding: 14px 10px; font-size: 13px; font-weight: 600; text-align: left;
}
.tile .g { font-size: 20px; display: block; margin-bottom: 14px; }
.applewarn {
  text-align: left; background: #F4F4F6; border-radius: 12px; padding: 14px;
  font-size: 13px; color: #333; border: 1px solid #E2E2E6;
}
.applewarn .t { font-weight: 650; margin-bottom: 6px; }
.applewarn .btns { display: flex; gap: 8px; margin-top: 12px; }
.applewarn .b {
  flex: 1; text-align: center; padding: 8px; border-radius: 8px; background: #fff;
  color: #0A84FF; font-weight: 600; border: 1px solid #E2E2E6;
}
.applewarn .b.primary { background: #0A84FF; color: #fff; }
.checklist { list-style: none; margin: 6px 0; }
.checklist li {
  display: flex; gap: 10px; align-items: flex-start; padding: 8px 0;
  font-size: 14px; line-height: 1.4;
}
.checklist .n {
  flex: none; width: 22px; height: 22px; border-radius: 50%; background: var(--kettle-soft);
  color: var(--kettle); font-size: 12px; font-weight: 700; display: grid;
  place-items: center; margin-top: 1px;
}
.verify {
  border-radius: 16px; padding: 18px; text-align: center; margin: 14px 0;
  background: var(--card); border: 1px solid var(--line); transition: all .3s;
}
.verify.green { background: var(--green-soft); border-color: #BBE3CB; }
.verify .big { font-size: 40px; }
.verify .msg { font-size: 14px; margin-top: 8px; color: var(--ink-soft); }
.verify.green .msg { color: var(--green); font-weight: 650; }
.spacer { flex: 1; }
.cta {
  display: block; width: 100%; padding: 15px; border: 0; border-radius: 14px;
  background: var(--kettle); color: #fff; font-size: 16px; font-weight: 650;
  cursor: pointer; margin-top: 10px; font-family: inherit; text-align: center;
  text-decoration: none;
}
.cta.ghost {
  background: none; color: var(--ink-soft); font-weight: 500; font-size: 13px; padding: 8px;
}
.cta:disabled { background: #D8CFC8; cursor: default; }
.stop {
  font-size: 12px; color: var(--ink-soft); text-align: center; margin-top: 8px; line-height: 1.4;
}
.kill {
  margin-top: 10px; padding: 10px 12px; border-radius: 12px; background: var(--card);
  border: 1px dashed #D8CFC8; font-size: 12.5px; color: var(--ink-soft); line-height: 1.45;
}
.consent-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 12px 0; }
.consent-card { border-radius: 12px; padding: 12px; font-size: 12.5px; line-height: 1.4; }
.consent-card.yes { background: var(--green-soft); }
.consent-card.no { background: #FBEBEB; }
.consent-card .h { font-weight: 700; font-size: 11px; letter-spacing: .4px; margin-bottom: 6px; }
.consent-card.yes .h { color: var(--green); }
.consent-card.no .h { color: #C0392B; }
.helper-note {
  display: none; background: #FFF8E8; border: 1px solid #F2E2B3; border-radius: 10px;
  padding: 10px 12px; font-size: 12.5px; color: #7A6420; margin-bottom: 10px; line-height: 1.4;
}
body.helping .helper-note { display: block; }
.dead { padding: 40px 22px; }
.dead p { color: var(--ink-soft); font-size: 15px; line-height: 1.5; margin-top: 10px; }
"""

# The page's behaviour. No secrets here: the state URL comes from
# location.pathname, so this script is identical for every parent.
_JS = """
var C = __COPY__;
var screens = Array.prototype.slice.call(document.querySelectorAll('.screen'));
var dots = document.getElementById('dots');
screens.forEach(function () {
  dots.appendChild(document.createElement('span'));
});
var at = 0;
function render() {
  screens.forEach(function (s, i) { s.classList.toggle('active', i === at); });
  Array.prototype.forEach.call(dots.children, function (d, i) {
    d.className = i < at ? 'done' : i === at ? 'now' : '';
  });
}
function next() {
  if (at < screens.length - 1) at++;
  render();
  if (screens[at].id === 'verify' && C.hasVerify) enterVerify();
  window.scrollTo(0, 0);
}
document.getElementById('helperToggle').onclick = function () {
  this.classList.toggle('on');
  document.body.classList.toggle('helping');
};
Array.prototype.forEach.call(document.querySelectorAll('[data-next]'), function (b) {
  b.onclick = next;
});

var statePath = location.pathname.replace(/\\/$/, '') + '/state';
var since = null;
var pollTimer = null;
var startedAt = null;

function enterVerify() {
  // Capture the server clock *before* the parent leaves for the other app:
  // they open it first and tap "I opened it" after, so a tap-time baseline
  // would postdate the very ping it waits for.
  fetch(statePath).then(function (r) { return r.json(); }).then(function (d) {
    if (d && d.now) since = d.now;
  }).catch(function () {});
}
function setVerify(icon, msg, green) {
  var box = document.getElementById('verifyBox');
  box.classList.toggle('green', !!green);
  document.getElementById('verifyIcon').textContent = icon;
  document.getElementById('verifyMsg').textContent = msg;
}
function startVerify() {
  document.getElementById('verifyBtn').disabled = true;
  setVerify('⏳', C.checking, false);
  startedAt = Date.now();
  var go = function () {
    poll();
    pollTimer = setInterval(poll, 3000);
  };
  if (since) go();
  else {
    fetch(statePath).then(function (r) { return r.json(); }).then(function (d) {
      if (d && d.now) since = d.now;
      go();
    }).catch(go);
  }
}
function poll() {
  if (!since) return;
  fetch(statePath + '?since=' + encodeURIComponent(since))
    .then(function (r) {
      if (!r.ok) throw new Error('gone');
      return r.json();
    })
    .then(function (d) {
      if (d.status !== 'live') throw new Error('gone');
      if (d.seen) {
        clearInterval(pollTimer);
        setVerify('✅', C.green, true);
        document.getElementById('verifyBtn').style.display = 'none';
        document.getElementById('verifyNext').style.display = 'block';
        return;
      }
      var waited = (Date.now() - startedAt) / 1000;
      if (waited > 75) setVerify('🕰', C.crossed, false);
      else if (waited > 30) setVerify('⏳', C.retry, false);
    })
    .catch(function () {
      clearInterval(pollTimer);
      setVerify('🕰', C.died, false);
    });
}
if (C.hasVerify) {
  document.getElementById('verifyBtn').onclick = startVerify;
}
render();
"""


def _e(value: str | None) -> str:
    """Escape one user-sourced string for HTML."""
    return html.escape(value or "", quote=True)


def _screen(body: str, screen_id: str = "") -> str:
    id_attr = f' id="{screen_id}"' if screen_id else ""
    return f'<section class="screen"{id_attr}>{body}</section>'


def _cta(label: str, extra: str = "") -> str:
    return f'<button class="cta" data-next{(" " + extra) if extra else ""}>{label}</button>'


def _bubble(text: str) -> str:
    return (
        '<div class="bubblerow"><div class="avatar">◎</div>'
        f'<div class="bubble">{text}</div></div>'
    )


def render_setup_page(state: SetupState, public_base_url: str) -> str:
    """The whole live page, one document, nothing external but the App Store."""
    parent = _e(state.parent_name)
    child = _e(state.child_name)
    host = _e(urlsplit(public_base_url).netloc or public_base_url)
    signals = list(state.signals)
    keys = [row["signal"] for row in signals]

    sub = (
        copy.HEADER_SUB.format(child=child)
        if state.child_name
        else copy.HEADER_SUB_NO_CHILD
    )

    sent = (
        copy.CONSENT_SENT_MERGED
        if "routine" in keys
        else copy.CONSENT_SENT_PER_APP
    )
    browser_note = (
        f'<p class="say">{copy.CONSENT_BROWSER}</p>' if browser_consent_applies(keys) else ""
    )
    consent = _screen(
        f'<div class="helper-note">{copy.HELPER_NOTE_CONSENT}</div>'
        f"<h1>{copy.CONSENT_TITLE}</h1>"
        f'<p class="say">{copy.CONSENT_SAY}</p>'
        f'<div class="consent-grid">'
        f'<div class="consent-card yes"><div class="h">{copy.CONSENT_SENT_HEADING}</div>'
        f"{sent}</div>"
        f'<div class="consent-card no"><div class="h">{copy.CONSENT_NEVER_HEADING}</div>'
        f"{copy.CONSENT_NEVER}</div></div>"
        f"{browser_note}"
        f'<div class="kill">🔴 <b>{copy.KILL_SWITCH}</b></div>'
        f'<div class="spacer"></div>{_cta(copy.CONSENT_CTA)}'
        f'<p class="stop">{copy.CONSENT_STOP}</p>'
    )

    step_zero = _screen(
        f'<div class="helper-note">{copy.HELPER_NOTE_GENERAL}</div>'
        f"<h1>{copy.STEP_ZERO_TITLE}</h1>"
        f'<div class="visual"><div class="appicon">⧉</div>'
        f'<div class="cap">{copy.STEP_ZERO_CAP}</div></div>'
        f"{_bubble(copy.STEP_ZERO_BUBBLE)}"
        f'<div class="spacer"></div>'
        f'<a class="cta ghost" href="{copy.APP_STORE_SHORTCUTS_URL}">{copy.STEP_ZERO_STORE_CTA}</a>'
        f"{_cta(copy.STEP_ZERO_CTA)}"
    )

    tiles = "".join(
        f'<div class="tile"><span class="g">'
        f"{TILE_GLYPHS.get(row['signal'], TILE_GLYPH_DEFAULT)}</span>"
        f"{_e(shortcut_name(row['signal']))}</div>"
        for row in signals
    )
    add_title = (
        copy.ADD_TITLE_TWO
        if len(signals) == 2
        else copy.ADD_TITLE_MANY.format(count=len(signals))
    )
    add_say = (
        copy.ADD_SAY.format(child=child) if state.child_name else copy.ADD_SAY_NO_CHILD
    )
    add = _screen(
        f"<h1>{add_title}</h1>"
        f'<p class="say">{add_say}</p>'
        f'<div class="visual"><div class="tiles">{tiles}</div>'
        f'<div class="cap">{copy.ADD_CAP}</div></div>'
        f'<div class="spacer"></div>{_cta(copy.ADD_CTA)}'
    )

    warn_shortcut = _e(shortcut_name(keys[0])) if keys else "Kettle"
    first_run = _screen(
        f'<div class="helper-note">{copy.HELPER_NOTE_FIRSTRUN}</div>'
        f"<h1>{copy.FIRSTRUN_TITLE}</h1>"
        f'<p class="say">{copy.FIRSTRUN_SAY}</p>'
        f'<div class="visual"><div class="applewarn">'
        f'<div class="t">{copy.APPLEWARN_TITLE.format(shortcut=warn_shortcut, host=host)}</div>'
        f"{copy.APPLEWARN_BODY}"
        f'<div class="btns"><div class="b">{copy.APPLEWARN_DENY}</div>'
        f'<div class="b primary">{copy.APPLEWARN_ALLOW}</div></div></div>'
        f'<div class="cap">{copy.FIRSTRUN_CAP}</div></div>'
        f'<div class="spacer"></div>{_cta(copy.FIRSTRUN_CTA)}'
    )

    rows = "".join(
        f'<li><span class="n">{i}</span><span>{automation_row(row["signal"], parent)}</span></li>'
        for i, row in enumerate(signals, start=1)
    )
    automations = _screen(
        f"<h1>{copy.AUTO_TITLE}</h1>"
        f'<p class="say">{copy.AUTO_SAY}</p>'
        f'<ol class="checklist">{rows}</ol>'
        f"{_bubble(copy.AUTO_HONESTY.format(count=len(signals)))}"
        f'<div class="spacer"></div>{_cta(copy.AUTO_CTA)}'
    )

    app_label = verify_app_label(signals)
    if app_label is None:
        no_routine = (
            copy.VERIFY_NO_ROUTINE.format(child=child)
            if state.child_name
            else copy.VERIFY_NO_ROUTINE.format(child=copy.DEAD_NO_CHILD)
        )
        verify = _screen(
            f"<h1>{copy.VERIFY_TITLE}</h1>"
            f'<p class="say">{no_routine}</p>'
            f'<div class="spacer"></div>{_cta(copy.VERIFY_FINISH)}',
            screen_id="verify",
        )
    else:
        app = _e(app_label)
        verify = _screen(
            f"<h1>{copy.VERIFY_TITLE}</h1>"
            f'<p class="say">{copy.VERIFY_SAY.format(app=app)}</p>'
            f'<div class="verify" id="verifyBox">'
            f'<div class="big" id="verifyIcon">⏳</div>'
            f'<div class="msg" id="verifyMsg">{copy.VERIFY_WAITING}</div></div>'
            f'<div class="spacer"></div>'
            f'<button class="cta" id="verifyBtn">{copy.VERIFY_BUTTON.format(app=app)}</button>'
            f'<button class="cta" id="verifyNext" data-next style="display:none">'
            f"{copy.VERIFY_FINISH}</button>",
            screen_id="verify",
        )

    done = _screen(
        f"<h1>{copy.DONE_TITLE.format(parent=parent)}</h1>"
        f'<p class="say">{copy.DONE_SAY}</p>'
        f'<div class="consent-grid">'
        f'<div class="consent-card yes"><div class="h">{copy.DONE_SEES_HEADING}</div>'
        f"{copy.DONE_SEES}</div>"
        f'<div class="consent-card no"><div class="h">{copy.DONE_NOT_HEADING}</div>'
        f"{copy.DONE_NOT}</div></div>"
        f'<div class="kill">🔴 {copy.DONE_KILL}</div>'
        f'<div class="spacer"></div>'
    )

    verify_copy = {
        "hasVerify": app_label is not None,
        "checking": copy.VERIFY_CHECKING,
        "green": copy.VERIFY_GREEN.format(parent=state.parent_name or ""),
        "retry": copy.VERIFY_RETRY.format(app=app_label or ""),
        "crossed": (
            copy.VERIFY_CROSSED.format(parent=state.parent_name or "", child=state.child_name)
            if state.child_name
            else copy.VERIFY_CROSSED_NO_CHILD.format(parent=state.parent_name or "")
        ),
        "died": copy.VERIFY_LINK_DIED.format(
            child=state.child_name or copy.DEAD_NO_CHILD
        ),
    }
    script = _JS.replace(
        "__COPY__", json.dumps(verify_copy, ensure_ascii=True).replace("</", "<\\/")
    )

    return (
        "<!doctype html>\n"
        '<html lang="en"><head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="referrer" content="no-referrer">\n'
        '<meta name="robots" content="noindex">\n'
        f"<title>{copy.PAGE_TITLE.format(parent=parent)}</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head><body>\n"
        '<header><div class="mark">◎</div><div>'
        f'<div class="who">{parent}’s setup</div><div class="sub">{sub}</div></div>'
        f'<div class="helper" id="helperToggle"><span>{copy.HELPER_TOGGLE}</span>'
        '<span class="pill"></span></div></header>\n'
        '<div class="dots" id="dots"></div>\n'
        "<main>\n"
        + consent
        + step_zero
        + add
        + first_run
        + automations
        + verify
        + done
        + "\n</main>\n"
        f"<script>{script}</script>\n"
        "</body></html>"
    )


def render_dead_end(state: SetupState) -> str:
    """Expired, replaced, or unknown: a sentence and a person to ask.

    Never steps, never signals, and by construction never a file — the child's
    name is the only fact a dead link is still entitled to (acceptance 3).
    """
    child = _e(state.child_name) if state.child_name else copy.DEAD_NO_CHILD
    if state.status == "expired":
        title, body = copy.DEAD_EXPIRED_TITLE, copy.DEAD_EXPIRED_BODY.format(child=child)
    elif state.status == "revoked":
        title, body = copy.DEAD_REVOKED_TITLE, copy.DEAD_REVOKED_BODY.format(child=child)
    else:
        title, body = copy.DEAD_UNKNOWN_TITLE, copy.DEAD_UNKNOWN_BODY
    return (
        "<!doctype html>\n"
        '<html lang="en"><head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="referrer" content="no-referrer">\n'
        '<meta name="robots" content="noindex">\n'
        f"<title>Kettle</title>\n<style>{_CSS}</style>\n"
        "</head><body>\n"
        '<header><div class="mark">◎</div><div>'
        '<div class="who">Kettle</div></div></header>\n'
        f'<main><div class="dead"><h1>{title}</h1><p>{body}</p></div></main>\n'
        "</body></html>"
    )


# --- routes ------------------------------------------------------------------


def _headers() -> dict[str, str]:
    return {
        "Cache-Control": CACHE_CONTROL,
        "X-Robots-Tag": "noindex",
        "Content-Security-Policy": CSP,
    }


@router.get("/s/{slug}", response_class=HTMLResponse)
async def setup_page(request: Request, slug: str) -> HTMLResponse:
    """One parent's setup page, or the plain-language dead end."""
    with request.app.state.pool.connection() as conn:
        state = resolve_setup(conn, slug, now_utc())
    if state.status == "unknown":
        return HTMLResponse(render_dead_end(state), status_code=404, headers=_headers())
    if state.status in ("expired", "revoked"):
        return HTMLResponse(render_dead_end(state), status_code=410, headers=_headers())
    return HTMLResponse(
        render_setup_page(state, request.app.state.settings.public_base_url),
        headers=_headers(),
    )


@router.get("/s/{slug}/state")
async def setup_state(request: Request, slug: str, since: str | None = None) -> JSONResponse:
    """The page's one live read: is the link alive, and has the server heard.

    `seen` is true only for an **alarm-grade** ping at or after `since` —
    law #6 applied to the verify check: a charger edge or a daily timer must
    never be what turns the named card green. `since` values come from this
    endpoint's own `now`, so no client clock is ever consulted.
    """
    now = now_utc()
    with request.app.state.pool.connection() as conn:
        state = resolve_setup(conn, slug, now)
        if state.status == "unknown":
            raise StarletteHTTPException(status_code=404, detail="not found")
        if state.status in ("expired", "revoked"):
            return JSONResponse(
                {"status": state.status}, status_code=410, headers=_headers()
            )

        seen: bool | None = None
        if since is not None:
            try:
                cutoff = datetime.fromisoformat(since)
            except ValueError:
                raise StarletteHTTPException(
                    status_code=400, detail="malformed since"
                ) from None
            if cutoff.tzinfo is None:
                raise StarletteHTTPException(status_code=400, detail="malformed since")
            last = db.last_alarm_ping(conn, state.parent_id)
            # Strictly after: timestamps are second-resolution, so a ping in
            # the same second as the baseline is treated as before the screen.
            # The check is a crossed-pair detector — a stale first-run ping
            # greening it is the failure it exists to catch, and the page's
            # retry copy absorbs the sub-second miss on the honest side.
            seen = last is not None and last > cutoff

    return JSONResponse(
        {
            "status": "live",
            "parent_name": state.parent_name,
            "now": now.isoformat(),
            "seen": seen,
        },
        headers=_headers(),
    )
