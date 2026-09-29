"""The locked cut: every shot's id, length, picture and exact on-screen words. SCRIPT.md is the
human copy; mockup.py and render.py both read this list, so the words live in one place.

picture:
  "blender|<set shot>[|<frame>]"     frames from out/frames/<set shot>/, from <frame> (default 1;
                                     consecutive rows share a set shot and play on through it)
  "screen|<rec>|<label>[|<under>]"   recordings/<rec>.mp4 on the plate, or a grey card saying
                                     <label> until it exists; <under>: small type below the screen
  "card|<layout>"                    a still paper card laying out its own words (render.card_png)
words: "\n" is a line break the caption keeps. Screen captions sit in the left column. Rows with
the same words are one beat: the caption stays up across them.

The v6 cut (founder, 2026-09-28): v5 with its three A/B extras in (the push-in into the note, the
zoom onto Mom's card, the push-in to the real text message), a 0.75 s hold on the note at the end
of the push-in, two soft sounds in the kitchen, and the stillness after the thumbs up trimmed.
The v7 cut (founder, 2026-09-28): v6 with shot 4's zoom taken out (the full screen again, as in
v5) and the new music (audio/music-v2.mp3, from 28 s).
"""

import os

SHOTS = [
    ("01", 2.5, "blender|01", "Mom and Dad live far away."),
    # The two phones turn slowly under the app icon and the line for the "Meet Kettle" line, then
    # the camera pushes into the green phone's screen (frames 204 to 234), which shows the note,
    # and holds on it for 0.75 s (to 8.55 s) before it becomes shot 3 (render: "brand").
    ("02", 8.55, "blender|03", "Kettle\nKnow Mom's okay, between the calls."),
    ("04", 3.7, "screen|R1|Morning note email", "Twice a day,\nthe family gets\na short note."),
    ("05", 3.7, "screen|R2|Today card", "The app shows when\nKettle last heard\nfrom her."),
    # Clip C's animation, unchanged: the push in to the text message (frames 20 to 50), the hold,
    # the pull back (140 to 172) as her reply lands and the thumbs up folds up (150 to 174). The
    # shot ends 0.1 s after the thumbs up is fully up.
    ("07", 5.9, "blender|07c", "Morning looks different?\nKettle asks her first."),
    ("08", 3.35, "screen|R3|Memory", "Notes and replies,\nin the family's\nown words."),
    ("09", 3.1, "screen|R4|Who to call", "Who to call,\nif you can't\nreach her."),
    ("10", 2.8, "screen|R5|Family circle", "Brothers and sisters\nsee the same notes."),
    ("16", 7.5, "card|more",
     "More ways to use Kettle\nConnect Mom's smart plug or Alexa routine\n"
     "Ask about Mom in Claude or ChatGPT."),
    ("15", 6.6, "card|end",
     "Kettle\nheykettle.com\nFor checking in, not checking up.\nNow open to founding families."),
]  # fmt: skip

# Captions laid out another way than the shot's kind implies, and captions that leave early.
CAPTION_LAYOUT = {"02": "brand"}  # the app icon and "Kettle" in a row, the line beneath
CAPTION_OUT_EARLY = {"02": 1.75}  # gone as the push-in starts (6.8 s), before the note hold

# Soft cross-dissolves at every join (founder: 0.3 s, 0.5 s going into shot 2). The outgoing shot
# runs on under the incoming one for that long, so a join adds no time.
DISSOLVE, DISSOLVE_INTO_2 = 0.3, 0.5
DISSOLVES = {(a[0], b[0]): DISSOLVE for a, b in zip(SHOTS, SHOTS[1:])}  # noqa: B905
DISSOLVES[("01", "02")] = DISSOLVE_INTO_2

# Slow zooms on a screen shot: shot -> {format: (start s, from scale, to scale, focus x, focus y,
# to x, to y)}. The focus point (in that format's frame) grows from one scale to the other and
# glides to (to x, to y) as it does. v6 zoomed shot 4 onto Mom's card: "05": {"16x9": (1.0, 1.0,
# 2.0, 1410, 737, 1420, 560)}; v7 took it out. The Care Compare video zooms onto the ZIP.
ZOOM: dict[str, dict[str, tuple[float, float, float, int, int, int, int]]] = {}

# Sound effects (founder, v6): shot -> (file, seconds into the shot, gain in dB). Synthesized by
# sfx.py, so no licence applies. Shot 7: a soft text tick as Mom's reply lands on the phone
# (frame 150) and a light paper pop as the thumbs up rises (frame 158), both under the voice.
# Gains set so each sits about 11 dB under the voice's average level (measured in the mix).
SFX = {"07": [("assets/sfx/tick.wav", 149 / 30, -6.0), ("assets/sfx/pop.wav", 157 / 30, -4.0)]}

# Voice-over (VOICEOVER.md): one take, ten lines in the founder's order, each cut at the silences
# around it and kept whole, natural pauses included. A line starts VOICE_LEAD s after its shot
# appears, with at least VOICE_BREATH s of quiet between lines.
VOICE_TAKE = "audio/voiceover-v3.mp3"
VOICE_LEAD, VOICE_BREATH, VOICE_BEFORE_INTRO = 0.2, 0.5, 0.5
VOICE = {
    "01": [(0.00, 1.74)],  # Mom and Dad live far away.
    "02": [(2.29, 8.85)],  # Meet Kettle. It checks in with Mom ... between the calls.
    "04": [(9.35, 11.68)],  # Twice a day, you get a short note.
    "05": [(12.06, 13.82)],  # See when Kettle last heard from her.
    "07": [(14.40, 16.81)],  # Different morning? Kettle asks her first.
    "08": [(17.17, 19.99)],  # Notes and replies, in your own words.
    "09": [(20.40, 22.16)],  # Who to call, in one place.
    "10": [(22.56, 24.22)],  # Everyone sees the same notes.
    "16": [(24.40, 31.33)],  # There's more. Connect Mom's smart plug ... Claude or ChatGPT.
    "15": [(31.81, 37.22)],  # Kettle. For checking in, not checking up. Join us at heykettle.com.
}

# Music (founder): MUSIC_TRACK from MUSIC_START s at one steady level, MUSIC_UNDER dB below the
# voice's speaking level, with no swells in the gaps; in over 0.5 s, out over 2 s. v7: the calm
# middle of music-v2, 28.0 to 75.7 s, after the sparse piano intro and before the low end comes in
# at 83 s (drums from 107 s). It has one soft breath at 53 to 56 s (film 25 to 28 s).
MUSIC_TRACK = "audio/music-v2.mp3"
MUSIC_START, MUSIC_UNDER = 28.0, 18.0


def voice_length(sid: str) -> float:
    return sum(p[1] - p[0] for p in VOICE.get(sid, []))


def beats() -> list[tuple[list[str], float, str]]:
    """Consecutive rows with the same words, as (shot ids, seconds, words)."""
    out: list[tuple[list[str], float, str]] = []
    for sid, sec, _pic, words in SHOTS:
        if out and out[-1][2] == words:
            out[-1][0].append(sid)
            out[-1] = (out[-1][0], out[-1][1] + sec, words)
        else:
            out.append(([sid], sec, words))
    return out


# Hold rule (founder, 2026-09-26): read once at 0.3 s a word, plus 0.5 s; app screens, which carry
# the most reading, plus 1.0 s instead; shots 6 to 8 (08, 09, 10), tightened for v5, plus 0.7 s.
# Painted shots at most 3 s, except those the founder set longer (PAINTED_LONG: seconds at
# least). The end card also holds through the 0.8 s fade.
APP_SCREENS = {"04", "05"}
TIGHT = {"08", "09", "10"}
PAINTED_MAX = 3.0
PAINTED_LONG = {"02": 6.0, "07": 5.5}
FINAL_FADE = 0.8


def hold(sid: str, words: str) -> float:
    base = 1.0 if sid in APP_SCREENS else 0.7 if sid in TIGHT else 0.5
    return base + 0.3 * len(words.split())


# How each recording is cut before it goes on screen (source is 1206x2622, 60 fps).
#   crop:  (top, bottom) rows kept; bottom None = to the end. App screens lose the status bar and
#          the circle switcher (410); Claude loses the status bar and, in R7, the faded tail of
#          R6's last line above the chat (300).
#   cuts:  (start, end, speed[, {"mask": (top, bottom, hex)}]) pieces played in order; end None =
#          to the end. Gaps are cut out. A mask covers source rows top..bottom with blank page
#          stretched from 50 rows starting at `sample` in the same frame, so the colour matches
#          exactly (a painted colour came out grey against the iPhone's encoding).
#   hold:  one frame, at this second, for the whole shot.
#   src:   the recording this entry cuts, when it is not its own name (a zoomed copy).
#   xcrop: (left, right) columns kept.
#   box:   (x, y, w, h) where the 16:9 cut fits it, in place of the phone-sized card.
# A recording with no entry plays from its first frame, uncropped.
RECORDINGS = {
    # The v4 zooms (founder: readable on a phone): the note card itself, Mom's card with its
    # "Heard from" line, the family circle, and the list of people to call.
    "R1z": {"src": "R1", "crop": (780, 1800), "xcrop": (60, 1146), "cuts": [(0.3, None, 1)],
            "box": (970, 90, 900, 900)},
    "R2z": {"src": "R2", "crop": (1630, 2040), "xcrop": (60, 1146), "cuts": [(1.5, None, 1)],
            "box": (970, 90, 900, 900)},
    "R5z": {"src": "R5", "crop": (200, 1090), "xcrop": (40, 1166), "cuts": [(0.0, 3.9, 1)],
            "box": (970, 90, 900, 900)},
    "R4z": {"src": "R4", "crop": (960, 2150), "xcrop": (40, 1166), "cuts": [(1.0, None, 1)],
            "box": (970, 90, 900, 900)},
    # R1: one static frame of the Outlook email; keep the message, drop the status bar, Outlook's
    # back arrow, and its reply bar and tab bar (a coloured assistant icon sits there). Since v7
    # (founder, 2026-09-28) it plays Mom's morning note (recordings/mom-note.mp4, recorded the
    # same way), not Dad's (R1.MP4); same crop, start and timing.
    "R1": {"src": "mom-note", "crop": (300, 1790), "cuts": [(0.3, None, 1)]},
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
}  # fmt: skip

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


# Words the founder approved although the scan would flag them. The overrides are recorded in the
# brief (docs/launch-video-brief.md, section 8), so they pass silently; anything else still stops
# the build.
OUT_NAME = "kettle-launch"  # out/<OUT_NAME>-16x9.mp4 and -9x16.mp4
TOTAL_RANGE = (42, 48)  # the v5 cut (founder, 2026-09-28)

FOUNDER_APPROVED = {
    # Brief section 8: approved although section 5 bans "okay" as a verdict about a person.
    "Kettle\nKnow Mom's okay, between the calls.",
    # The ask on Mom's phone (A/B clip C), exactly as the product sends it: the writers' brief,
    # rule 9, pins it verbatim, and "check in with" is the pinned Kettle-as-actor phrase.
    "Hi. Anna asked Kettle to check in with you when your morning is not as usual. "
    "Is everything okay? Reply with a 👍 when you can.",
}


def check(words: str) -> None:
    """The brief's section 5, on every word that reaches the screen. A breach stops the build,
    unless the founder approved those exact words (FOUNDER_APPROVED, brief section 8)."""
    if words in FOUNDER_APPROVED:
        return
    low = words.lower()
    bad = [b for b in BANNED if b in low] + [c for c in "—!’“”" if c in words]
    if bad:
        raise SystemExit(f"copy law: {bad} in {words!r}")


# The feature videos (features.py): KETTLE_CUT=<name> swaps in that video's shots, voice, dissolves
# and zooms, adds its recording cuts, and names its files; everything else is shared.
CUT = os.environ.get("KETTLE_CUT")
if CUT:
    from features import cut

    _feature = cut(CUT)
    RECORDINGS = {**RECORDINGS, **_feature.pop("EXTRA_RECORDINGS")}
    globals().update(_feature)

if __name__ == "__main__":  # self-check: the words pass, and a planted breach is caught
    for s in SHOTS:
        check(s[3])
    for planted in ("Kettle keeps Mom safe.", "Heard from — today"):
        try:
            check(planted)
        except SystemExit:
            continue
        raise AssertionError(f"copy law missed {planted!r}")
    # The launch film's hold rules; the feature videos are paced by their voice lines instead.
    for ids, sec, words in beats() if not CUT else []:
        assert sec >= round(hold(ids[0], words), 2) - 0.05, f"{ids}: {sec} s is under its hold"
    for sid, sec, pic, _words in SHOTS if not CUT else []:
        if pic.startswith("blender"):
            if sid in PAINTED_LONG:
                assert sec >= PAINTED_LONG[sid], (
                    f"{sid}: the founder asked for {PAINTED_LONG[sid]} s"
                )
            else:
                assert sec <= PAINTED_MAX, f"{sid}: painted shots run at most {PAINTED_MAX} s"
    last_id, last_sec, _p, last_words = SHOTS[-1]
    end_hold = VOICE_LEAD + voice_length(last_id) if CUT else hold(last_id, last_words)
    assert last_sec >= end_hold + FINAL_FADE - 0.05, "end card fades too soon"
    # Voice: each line inside its beat, and quiet between lines.
    clock, starts = 0.0, {}
    for sid, sec, *_ in SHOTS:
        starts[sid], clock = clock, clock + sec
    ends = {}
    for ids, sec, _w in beats():
        for sid in ids:
            if sid in VOICE:
                end = starts[sid] + VOICE_LEAD + voice_length(sid)
                assert end <= starts[ids[0]] + sec + 0.01, f"{sid}: its line runs past its beat"
                ends[sid] = end
    lines = sorted((starts[s] + VOICE_LEAD, s) for s in VOICE)
    for (_a0, s0), (a1, s1) in zip(lines, lines[1:]):  # noqa: B905
        need = VOICE_BEFORE_INTRO if s1 == "02" else VOICE_BREATH
        assert a1 - ends[s0] >= need - 0.05, f"{s0} to {s1}: {a1 - ends[s0]:.2f} s of quiet"
    total = sum(s[1] for s in SHOTS)
    assert TOTAL_RANGE[0] <= round(total, 3) <= TOTAL_RANGE[1], total
    print(f"{CUT or 'launch'}: {len(SHOTS)} shots, {total:.1f} s, words checked")
