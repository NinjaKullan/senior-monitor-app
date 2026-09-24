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
    ("11a", 3.7, "screen|R6|Claude: the question", "Kettle works\ninside Claude, too."),
    ("11b", 3.7, "screen|R6|Claude: Kettle's answer", "Ask how Mom's\nmorning went."),
    ("12", 5.0, "screen|R7|Claude: add a note", "Or tell it something\nfor the family."),
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
    assert 75 <= total <= 90, total
    print(f"{len(SHOTS)} shots, {total:.1f} s, words clean")
