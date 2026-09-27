"""The locked cut: every shot's id, length, picture and exact on-screen words. SCRIPT.md is the
human copy; mockup.py and render.py both read this list, so the words live in one place.

picture:
  "blender|<set shot>[|<frame>]"     frames from out/frames/<set shot>/, from <frame> (default 1;
                                     consecutive rows share a set shot and play on through it)
  "screen|<rec>|<label>[|<under>]"   recordings/<rec>.mp4 on the plate, or a grey card saying
                                     <label> until it exists; <under>: small type below the screen
  "close|15"                         the close set, with the name and address laid over it
words: "\n" is a line break the caption keeps. Screen captions sit in the left column.
"""

SHOTS = [
    ("01", 2.3, "blender|01", "Mom and Dad live far away."),
    ("03", 2.9, "blender|03", "The phone she already owns.\niPhone or Android."),
    ("04", 3.7, "screen|R1|Morning note email", "Twice a day,\nthe family gets\na short note."),
    ("05", 3.7, "screen|R2|Today card", "The app shows when\nKettle last heard\nfrom her."),
    # From frame 8, so the bubble (12 to 30) and the thumbs up (66 to 90) both land in 2.9 s.
    ("07", 2.9, "blender|07|8", "Kettle asks her first,\nbefore anyone else hears."),
    ("08", 3.4, "screen|R3|Memory", "Notes and replies,\nin the family's\nown words."),
    ("09", 3.4, "screen|R4|Who to call", "Who to call,\nif you can't\nreach her."),
    ("10", 3.1, "screen|R5|Family circle", "Brothers and sisters\nsee the same notes."),
    ("10b", 2.6, "blender|10b", "Add Mom's smart plug or Alexa routine."),
    ("11a", 2.0, "screen|R6|Claude: the question", "Kettle works\ninside Claude, too."),
    ("11b", 2.6, "screen|R6|Claude: Kettle's answer", "Ask who to call,\nright from Claude."),
    ("12", 2.6, "screen|R7|Claude: add a note", "Or tell it something\nfor the family."),
    ("13", 2.8, "screen|R8|Memory: the new note", "It lands in the\nfamily's notes."),
    ("14a", 2.0, "screen|R9|Claude: Care Compare|Care Compare by HeyKettle",
     "Looking for\nhome health care?"),
    ("14b", 2.3, "screen|R9|Claude: Care Compare|Care Compare by HeyKettle",
     "Medicare's ratings,\nin plain words. Free."),
    ("15b", 2.3, "close|15", "For checking in, not checking up."),
    ("15c", 2.0, "close|15", "Now open to founding families."),
]  # fmt: skip

# Hold rule (founder, 2026-09-26, after a test viewer drifted): read once at 0.3 s a word, plus
# 0.5 s; app screens, which carry the most reading, plus 1.0 s instead. Painted shots at most 3 s.
APP_SCREENS = {"04", "05", "08", "09", "10", "13"}
PAINTED_MAX = 3.0


def hold(sid: str, words: str) -> float:
    return (1.0 if sid in APP_SCREENS else 0.5) + 0.3 * len(words.split())


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
    # Typing x10, Claude's lookup x8 (founder's re-time), the answer streaming in, then a hold on
    # 24.0 s, when the list is fully drawn, with Claude's closing "call 911" line (rows 1725 to
    # 1910) covered by blank page from the same frame, rows 1905 to 1955 (founder: end on the list
    # of people to call; the full list reads better than a faint last entry).
    "R6": {
        "crop": (300, None),
        "cuts": [
            (2.7, 13.5, 10),
            (13.5, 22.0, 8),
            (22.0, 22.36, 1),
            (24.0, 24.05, 1, {"mask": (1725, 1910, 1905)}),
        ],
    },  # fmt: skip
    # The note pasted in x8, Claude reading it back x4, then a hold on its proposed note. It skips
    # 5.8 to 7.3 s (sending scrolls R6's 911 line back into view); the confirm and Claude's reply
    # no longer fit the 2.6 s shot, and shot 13 shows the note landing in the app instead.
    "R7": {"crop": (300, None), "cuts": [(2.6, 5.8, 8), (7.3, 10.0, 4), (10.0, 12.0, 1)]},
    "R8": {"crop": (410, None), "hold": 2.0},  # founder: hold the frame
    # Typing x10, the lookup x8 (as R6), the five agencies streaming in x3, then a quick scroll to
    # Medicare's source line x6, which holds.
    "R9": {
        "crop": (300, None),
        "cuts": [(0.0, 3.3, 10), (3.3, 12.0, 8), (12.0, 16.0, 3), (16.0, 23.2, 6)],
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
    for sid, sec, pic, words in SHOTS:
        assert sec >= round(hold(sid, words), 2) - 0.05, f"{sid}: {sec} s is under its hold"
        if pic.startswith("blender"):
            assert sec <= PAINTED_MAX, f"{sid}: painted shots run at most {PAINTED_MAX} s"
    total = sum(s[1] for s in SHOTS)
    # The founder re-timed the cut to 45 to 50 s (2026-09-26).
    assert 45 <= round(total, 3) <= 50, total
    print(f"{len(SHOTS)} shots, {total:.1f} s, words clean")
