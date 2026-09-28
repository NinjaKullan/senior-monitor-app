#!/usr/bin/env python3
"""Mom's phone screen for shot 07: a plain text-message thread (SMS style, not WhatsApp), drawn by
headless Chrome so every word is exact. Kitchen.py maps these onto the phone's screen.

python3 sms_screens.py -> assets/sms/thread-0.png (empty), -1.png (Kettle's message),
                          -2.png (the message and Mom's thumbs-up reply)
The message is the ask exactly as the product sends it (the writers' brief, rule 9), with the
name of whoever set the parent up: here "Anna", a made-up family member.
"""

from __future__ import annotations

import html
import subprocess
from pathlib import Path

from shots import check

HERE = Path(__file__).resolve().parent
OUT = HERE / "assets" / "sms"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1000, 2060  # the phone screen's aspect (0.9 x 0.94 of an 11 x 22.5 cm phone)
SENDER = "Kettle"
MESSAGE = (
    "Hi. Anna asked Kettle to check in with you when your morning is not as usual. "
    "Is everything okay? Reply with a 👍 when you can."
)
REPLY = "👍"


def page(stage: int) -> str:
    incoming = f'<div class="in">{html.escape(MESSAGE)}</div>' if stage >= 1 else ""
    reply = f'<div class="out">{REPLY}</div>' if stage >= 2 else ""
    return f"""<!doctype html><meta charset="utf-8"><style>
html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; }}
body {{ background: #FBF8F2; font-family: -apple-system, "Helvetica Neue", sans-serif;
        color: #2B2824; }}
.bar {{ height: 300px; background: #F1ECE3; border-bottom: 2px solid #E2DBCF;
        display: flex; flex-direction: column; align-items: center; justify-content: flex-end;
        padding-bottom: 26px; box-sizing: border-box; }}
.avatar {{ width: 118px; height: 118px; border-radius: 50%; background: #8A847B; color: #FBF8F2;
           font-size: 62px; display: flex; align-items: center; justify-content: center; }}
.name {{ font-size: 44px; margin-top: 12px; }}
.label {{ text-align: center; color: #8A847B; font-size: 34px; margin: 46px 0 26px; }}
.in {{ margin: 0 150px 0 44px; background: #DCD5C9; border-radius: 52px; padding: 40px 48px;
       font-size: 60px; line-height: 1.28; }}
.out {{ margin: 46px 44px 0 auto; width: max-content; background: #297A5C; border-radius: 52px;
        padding: 26px 46px; font-size: 96px; line-height: 1.1; }}
</style>
<div class="bar"><div class="avatar">K</div><div class="name">{SENDER}</div></div>
<div class="label">Text Message · Today 9:41 AM</div>
{incoming}{reply}"""


def main() -> None:
    check(MESSAGE)  # the same copy check as every caption
    OUT.mkdir(parents=True, exist_ok=True)
    for stage in (0, 1, 2):
        src = OUT / f"thread-{stage}.html"
        src.write_text(page(stage), encoding="utf-8")
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                        f"--window-size={W},{H}", "--virtual-time-budget=2000",
                        f"--screenshot={OUT / f'thread-{stage}.png'}", f"file://{src}"],
                       check=True, capture_output=True)  # fmt: skip
        src.unlink()
        print(f"wrote assets/sms/thread-{stage}.png")


if __name__ == "__main__":
    main()
