"""The locked cut: every shot's id, length, picture and exact on-screen words. SCRIPT.md is the
human copy; mockup.py and render.py both read this list, so the words live in one place.

picture:
  "blender|<set shot>"               frames from out/frames/<set shot>/ (consecutive rows share
                                     a set shot and play on through its frames)
  "screen|<rec>|<label>[|<under>]"   recordings/<rec>.mp4 on the plate, or a grey card saying
                                     <label> until it exists; <under>: small type below the screen
  "close|15"                         the close set, with the name and address laid over it
words: "\n" is a line break the caption keeps. Screen captions sit in the left column.
"""

SHOTS = [
    ("01", 4.2, "blender|01", "Mom and Dad live far away."),
    ("02", 4.7, "blender|02", "Mom's phone does what it always does."),
    ("03", 5.2, "blender|03", "iPhone or Android. The phone she already owns."),
    ("04", 5.7, "screen|R1|Morning note email", "Twice a day,\nthe family gets\na short note."),
    ("05", 5.7, "screen|R2|Today card", "The app shows when\nKettle last heard\nfrom her."),
    ("06", 4.7, "blender|06", "If a morning doesn't look like hers,"),
    ("07a", 3.7, "blender|07", "Kettle asks her first, quietly."),
    ("07b", 5.2, "blender|07", "The family hears only if she doesn't answer."),
    ("08", 5.2, "screen|R3|Memory", "Notes and replies,\nin the family's\nown words."),
    ("09", 5.2, "screen|R4|Who to call", "Who to call,\nif you can't\nreach her."),
    ("10", 5.0, "screen|R5|Family circle", "Brothers and sisters\nsee the same notes."),
    ("10b", 4.7, "blender|10b", "Add Mom's smart plug or Alexa routine."),
    ("11a", 3.7, "screen|R6|Claude: the question", "Kettle works\ninside Claude, too."),
    ("11b", 4.7, "screen|R6|Claude: Kettle's answer", "Ask who to call,\nright from Claude."),
    ("12", 5.8, "screen|R7|Claude: add a note", "Or tell it something\nfor the family."),
    ("13", 4.2, "screen|R8|Memory: the new note", "It lands in the\nfamily's notes."),
    (
        "14a",
        3.8,
        "screen|R9|Claude: Care Compare|Care Compare by HeyKettle",
        "Looking for\nhome health care?",
    ),
    (
        "14b",
        4.2,
        "screen|R9|Claude: Care Compare|Care Compare by HeyKettle",
        "Medicare's ratings,\nin plain words. Free.",
    ),
    ("15a", 1.0, "close|15", ""),
    ("15b", 4.7, "close|15", "For checking in, not checking up."),
    ("15c", 3.7, "close|15", "Now open to founding families."),
]

# How each recording is cut before it goes on screen (source is 1206x2622, 60 fps).
#   crop:  (top, bottom) rows kept; bottom None = to the end. App screens lose the status bar and
#          the circle switcher (410); Claude loses the status bar and, in R7, the faded tail of
#          R6's last line above the chat (300).
#   cuts:  (start, end, speed[, {"mask": (top, bottom, hex)}]) pieces played in order; end None =
#          to the end. Gaps are cut out. A mask covers source rows top..bottom with blank page
#          stretched from 50 rows starting at `sample` in the same frame, so the colour matches
#          exactly (a painted colour came out grey against the iPhone's encoding).
#   hold:  one frame, at this second, for the whole shot.
# A recording with no entry plays from its first frame, uncropped.
RECORDINGS = {
    # R1: one static frame of the Outlook email; keep the message, drop the status bar, Outlook's
    # back arrow, and its reply bar and tab bar (a coloured assistant icon sits there).
    "R1": {"crop": (300, 1790), "cuts": [(0.3, None, 1)]},
    "R2": {"crop": (410, None), "cuts": [(1.5, None, 1)]},  # founder: trim the first 1.5 s
    # R3, R4: the first 0.9 s is the home screen and the app opening (founder: no personal apps).
    "R3": {"crop": (410, None), "cuts": [(1.0, None, 1)]},
    "R4": {"crop": (410, None), "cuts": [(1.0, None, 1)]},
    # The circle only, before "Add someone" opens a form that pushes the connector address
    # (".../mcp") and the list of connected assistants into view.
    "R5": {"crop": (190, 1180), "cuts": [(0.0, 3.9, 1)]},
    # Typing x5, Claude's lookup x4, the answer streaming in, then a hold on 24.0 s, when the list
    # is fully drawn, with Claude's closing "call 911" line (rows 1725 to 1910) covered by blank
    # page from the same frame, rows 1905 to 1955 (founder: end on the list of people to call; the
    # full list reads better than a faint last entry).
    "R6": {
        "crop": (300, None),
        "cuts": [
            (2.7, 13.5, 5),
            (13.5, 22.0, 4),
            (22.0, 22.36, 1),
            (24.0, 24.05, 1, {"mask": (1725, 1910, 1905)}),
        ],
    },  # fmt: skip
    # Skips 5.8 to 7.3 s (sending scrolls R6's 911 line back into view) and 10.6 to 17.6 s (idle).
    "R7": {
        "crop": (300, None),
        "cuts": [
            (2.6, 5.8, 4),
            (7.3, 10.0, 3),
            (10.0, 10.6, 1),
            (17.6, 22.3, 5),
            (22.3, 27.8, 5),
            (27.8, 29.6, 1),
        ],
    },  # fmt: skip
    "R8": {"crop": (410, None), "hold": 2.0},  # founder: hold the frame
    # Typing x5, the lookup x4 (as R6), the five agencies streaming in x2, then the slow scroll to
    # Medicare's source line x2.4, which holds.
    "R9": {
        "crop": (300, None),
        "cuts": [(0.0, 3.3, 5), (3.3, 12.0, 4), (12.0, 16.0, 2), (16.0, 23.2, 2.4)],
    },
}

BANNED = [
    "monitor",
    "track",
    "alert",
    "alarm",
    "surveil",
    "elderly",
    "senior",
    "sensor",
    "detect",
    "dashboard",
    "score",
    "safe",
    "fine",
    "okay",
    "checked in",
    "ordinary",
    "signal",
    "ping",
    "shortcut",
    "automat",
    "api",
    "mcp",
    "loved one",
]


def check(words: str) -> None:
    """The brief's section 5, on every word that reaches the screen. A breach stops the build."""
    low = words.lower()
    bad = [b for b in BANNED if b in low] + [c for c in "—!’“”" if c in words]
    if bad:
        raise SystemExit(f"copy law: {bad} in {words!r}")


if __name__ == "__main__":  # self-check: the words pass, and a planted breach is caught
    for s in SHOTS:
        check(s[3])
    for planted in ("Kettle keeps Mom safe.", "Heard from — today"):
        try:
            check(planted)
        except SystemExit:
            continue
        raise AssertionError(f"copy law missed {planted!r}")
    total = sum(s[1] for s in SHOTS)
    # The founder raised the cap from 90 to 95 s for shot 10b (2026-09-26).
    assert 75 <= round(total, 3) <= 95, total
    print(f"{len(SHOTS)} shots, {total:.1f} s, words clean")
