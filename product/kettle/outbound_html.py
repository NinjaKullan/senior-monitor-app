"""The HTML wrapper every outbound email wears (the email-polish pass).

The words come from the registry and ONLY from the registry: this module
lays them out and adds no copy of its own beyond the footer, which reuses
`EMAIL_SUBJECT` verbatim, and the site's own domain as the link text. The
laws, each held by a test:

* **Table-based layout, every style inline.** No external CSS, no remote
  fonts — the serif stack is Georgia, 'Times New Roman', serif.
* **Exactly one image**: the 44px hearth glyph, hosted at a stable unhashed
  URL on heykettle.com (the site serves it with revalidate caching, the
  DECISIONS 112 contract). width/height set, alt="Kettle".
* **No text lives only inside an image.** With images blocked the email
  still reads complete: chip, sentence, sub-line, footer. A test strips the
  <img> and asserts every word survives.
* **Multipart always**: the caller sends this HTML beside a plain-text part
  carrying the same words. Blocked HTML degrades to the same message, not a
  different one.
* **The v5 palette, inline**: paper #F7F2E9, card #FDFBF6, ink #2E2822,
  chip #E7EFD6 / #D5E3B8 / #7A4A26, rule #D5E3B8, link #96552D. No em
  dashes anywhere.
"""

from __future__ import annotations

import html
from collections.abc import Mapping

from kettle.outbound_templates import EMAIL_SUBJECT, render

#: One hosted image, one stable URL. The asset lives in site/public (served
#: unhashed under the DECISIONS 112 revalidate rule), so the SITE deploy must
#: carry it before the first polished email goes out.
GLYPH_URL = "https://heykettle.com/email-glyph.png"

SITE_URL = "https://heykettle.com"
SITE_LINK_TEXT = "heykettle.com"

SERIF = "Georgia, 'Times New Roman', serif"

#: The v5 palette, by name, so the tests and the markup agree by reference.
PAPER = "#F7F2E9"
CARD = "#FDFBF6"
INK = "#2E2822"
CHIP_FILL = "#E7EFD6"
CHIP_BORDER = "#D5E3B8"
CHIP_TEXT = "#7A4A26"
RULE = "#D5E3B8"
LINK = "#96552D"


def split_body(body: str) -> tuple[str, str]:
    """The day's sentence, then everything after it as the sub-line.

    Registry bodies are one to three plain sentences; the first carries the
    day and renders large, the rest render small. A one-sentence body has an
    empty sub-line.
    """
    cut = body.find(". ")
    if cut == -1:
        return body, ""
    return body[: cut + 1], body[cut + 2 :]


def render_email_html(
    template_id: str,
    variables: Mapping[str, str],
    relationship: str | None,
) -> str:
    """The full HTML part for one message. Words from the registry, verbatim."""
    body = render(template_id, variables)
    sentence, subline = split_body(body)

    chip_row = ""
    if relationship:
        chip_row = (
            '<tr><td align="center" style="padding:14px 32px 0;">'
            f'<span style="display:inline-block;background-color:{CHIP_FILL};'
            f"border:1px solid {CHIP_BORDER};border-radius:999px;"
            f"padding:4px 14px;font-family:{SERIF};font-size:13px;"
            f'color:{CHIP_TEXT};">{html.escape(relationship)}</span>'
            "</td></tr>"
        )

    subline_row = ""
    if subline:
        subline_row = (
            '<tr><td align="center" style="padding:10px 40px 0;'
            f'font-family:{SERIF};font-size:15px;line-height:1.5;color:{INK};">'
            f"{html.escape(subline)}</td></tr>"
        )

    return (
        "<!doctype html>"
        '<html><body style="margin:0;padding:0;background-color:' + PAPER + ';">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="background-color:{PAPER};">'
        '<tr><td align="center" style="padding:32px 16px;">'
        '<table role="presentation" width="440" cellpadding="0" cellspacing="0" '
        f'border="0" style="max-width:440px;background-color:{CARD};'
        'border-radius:18px;">'
        '<tr><td align="center" style="padding:36px 32px 0;">'
        f'<img src="{GLYPH_URL}" width="44" height="44" alt="Kettle" '
        'style="display:block;border:0;" />'
        "</td></tr>"
        f"{chip_row}"
        '<tr><td align="center" style="padding:18px 40px 0;'
        f'font-family:{SERIF};font-size:24px;line-height:1.3;color:{INK};">'
        f"{html.escape(sentence)}</td></tr>"
        f"{subline_row}"
        '<tr><td align="center" style="padding:24px 32px 0;">'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0">'
        f'<tr><td width="56" height="3" style="background-color:{RULE};'
        'border-radius:2px;font-size:0;line-height:0;">&nbsp;</td></tr>'
        "</table></td></tr>"
        '<tr><td align="center" style="padding:20px 32px 36px;'
        f'font-family:{SERIF};font-size:13px;line-height:1.6;color:{INK};">'
        f"{html.escape(EMAIL_SUBJECT)}<br />"
        f'<a href="{SITE_URL}" style="color:{LINK};">{SITE_LINK_TEXT}</a>'
        "</td></tr>"
        "</table></td></tr></table></body></html>"
    )
