# Kettle launch video

A 47.7 s launch film for heykettle.com, LinkedIn and YouTube, plus a 9:16 cut for TikTok, Reels
and Shorts made from the same edit. An AI voice-over reads one line per shot over captions, with
quiet music and two soft sounds in the kitchen (the founder's override, brief section 8). The
brief is `docs/launch-video-brief.md`, the approved words and timings are in `SCRIPT.md`, the shots
are in `STORYBOARD.md`, and progress is in `TASKS.md`.

## Render

```sh
cd marketing/launch-video
python3 render.py
```

That produces:

- `out/kettle-launch-16x9.mp4`: 1920x1080, 30 fps, H.264 yuv420p, AAC
- `out/kettle-launch-9x16.mp4`: 1080x1920, same encoding
- `out/shots/<id>.png`: one still per shot, in both formats

`python3 render.py --vertical` builds only the 9:16 cut. The audio is `audio/voiceover-v3.mp3`
(`shots.VOICE_TAKE`), `audio/music-v2.mp3` from 28.0 s at one steady level under the voice
(`shots.MUSIC_*`) and the two sounds `python3 sfx.py` writes to `assets/sfx/` (`shots.SFX`). Both
cuts are mastered to -16 LUFS with the true peak at -1 dBTP or lower.

The first run renders every painted frame in Blender, about 1,100 frames at 6 to 10 s each on an
M5 GPU, so it takes a few hours. After that, runs reuse `out/frames/` and take a few minutes. To
re-render one set, delete its folder under `out/frames/`. `out/` is gitignored.

Needs: Blender at `/Applications/Blender.app` (5.2, Cycles on Metal), Google Chrome, ffmpeg and
Python 3. There are no Python packages to install: Blender's own numpy does the image work.

## Screen recordings

Every app screen and Claude conversation is a real recording of the Rehearsal family. Until a
recording exists, a grey card labelled with its name stands in, and the build lists what is still
a placeholder. To add one, save it as `recordings/R1.mp4` to `recordings/R9.mp4` (steps are in
`STORYBOARD.md`) and run `python3 render.py` again. Recordings are gitignored and never committed.

## How it is made

- **Words.** `shots.py` holds every shot's length, picture and exact words. `render.py` and
  `mockup.py` both read it and refuse to build if a word breaks the brief's section 5. Run
  `python3 shots.py` for the self-check.
- **Paintings.** `node paint.mjs <name> style-tests/look-reference.png` asks Gemini (key from
  `GEMINI_API_KEY`, the same daily cap as `tools/social/make_strip.py`) for one flat paper layer on
  magenta. The prompts are in `assets/PROMPTS.md`. `blender -b -P blender/cutout.py -- in.png out.png`
  cuts the layer out to `assets/layers/`. The render never calls Gemini.
- **Sets.** `blender/paper.py` is the paper-diorama kit: table, wall, cards, the phone and the
  light. There is one script per set: `map.py` (shot 1), `kitchen.py` (shots 2, 6, 7), `phones.py`
  (shot 3) and `close.py` (shot 15 and the plate under the screen shots). To render one frame of a
  set: `blender -b -P blender/kitchen.py -- 07 still 200`.
- **Composite.** Headless Chrome draws the captions and cards as transparent PNGs, because this
  ffmpeg has no drawtext. ffmpeg lays them over the frames and joins the shots. The 9:16 cut takes
  a moving window from each painted frame that follows the subject (`render.REFRAME_9X16`), puts
  the words above it and keeps all text clear of the top and bottom 12% of the frame.
- **Mockups.** `python3 mockup.py` rebuilds the phase 3 stills, contact sheet and rough cut.
