# Kettle launch video: script (v6, 2026-09-28)

The v6 cut: 47.7 s, 16:9 first. It is v5 (the committed cut's shots and animations on the third
voice take (`audio/voiceover-v3.mp3`, VOICEOVER.md), with the founder's changes: the app icon and
the line over the two phones, a push into one phone's screen that becomes the note, the fixed
kettle in the kitchen, and new "more ways" and end cards) with v5's three A/B extras in, a 0.75 s
hold on the note at the end of the push-in, two soft sounds in the kitchen, and the stillness after
the thumbs up trimmed. Cut: the smart
plug (10b), the Claude shots (11a to 13) and Medicare (14a, 14b), which become their own short
videos (TASKS.md).

- **Words:** Patrick Hand, ink, on paper, never over a screen's text. Screen captions sit in the
  left column; the two cards lay out their own words.
- **Transitions:** a soft 0.3 s cross-dissolve at every join, 0.5 s going into shot 2. The
  outgoing shot runs on underneath, so no time is added. Shot 2's words leave 1 s early so the
  push-in lands on the phone's screen alone.
- **Hold rule:** read once, at 0.3 s a word, plus 0.5 s; app screens 04 and 05 plus 1.0 s; shots 6
  to 8, tightened for v5, plus 0.7 s. Painted shots at most 3 s, except shot 2 (its voice line,
  the push-in and the note hold) and shot 5 (the push to the text message and back). The end card holds long enough to read everything before its 0.8 s fade.
  `shots.py` asserts all of it, and a 42 to 48 s total.
- **Voice:** each line starts 0.2 s into its shot, with at least 0.5 s of quiet between lines.
- **Screens:** real recordings of the Rehearsal family, parents shown as "Mom" and "Dad".

| Line | Voice (exact) |
|---|---|
| 1 | Mom and Dad live far away. |
| 2 | Meet Kettle. It checks in with Mom through the phone she already has, so you know she's okay between the calls. |
| 3 | Twice a day, you get a short note. |
| 4 | See when Kettle last heard from her. |
| 5 | Different morning? Kettle asks her first. |
| 6 | Notes and replies, in your own words. |
| 7 | Who to call, in one place. |
| 8 | Everyone sees the same notes. |
| 9 | There's more. Connect Mom's smart plug or Alexa routine, or ask about her in Claude or ChatGPT. |
| 10 | Kettle. For checking in, not checking up. Join us at heykettle.com. |

| # | Time (s) | Picture | On-screen words (exact) | Voice line | Length (s) | Hold (s) |
|---|---|---|---|---|---|---|
| 1 (01) | 0.0 to 2.5 | Painted: the paper map, the city and Mom and Dad's house both in frame, a slight drift | Mom and Dad live far away. | 1 | 2.50 | 2.3 |
| 2 (02) | 2.5 to 11.1 | Painted: the two phones, the camera turning slowly over them; the app icon, "Kettle" and the line above; then a push into the green phone's screen, which shows the morning note, held 0.75 s | Kettle / Know Mom's okay, between the calls. | 2 | 8.55 | 2.6 |
| 3 (04) | 11.1 to 14.8 | Screen R1: the morning note email (the push-in dissolves into it) | Twice a day, / the family gets / a short note. | 3 | 3.70 | 3.7 |
| 4 (05) | 14.8 to 18.4 | Screen R2: the Today card, full screen (v7: the zoom is out) | The app shows when / Kettle last heard / from her. | 4 | 3.70 | 3.7 |
| 5 (07) | 18.4 to 24.4 | Painted: the kitchen; the camera pushes in to Mom's phone and the real text message, holds, then pulls back as her 👍 reply lands (a soft tick) and the paper thumbs up rises (a light pop); the fixed kettle on its burner | Morning looks different? / Kettle asks her first. | 5 | 5.90 | 2.6 |
| 6 (08) | 24.4 to 27.7 | Screen R3: Memory, notes and a reply | Notes and replies, / in the family's / own words. | 6 | 3.35 | 3.1 |
| 7 (09) | 27.7 to 30.8 | Screen R4: Who to call | Who to call, / if you can't / reach her. | 7 | 3.10 | 3.1 |
| 8 (10) | 30.8 to 33.6 | Screen R5: the family circle | Brothers and sisters / see the same notes. | 8 | 2.80 | 2.8 |
| 9 (16) | 33.6 to 41.1 | Card: "More ways to use Kettle" and two lines; still | More ways to use Kettle / Connect Mom's smart plug or Alexa routine / Ask about Mom in Claude or ChatGPT. | 9 | 7.50 | 6.2 |
| 10 (15) | 41.1 to 47.7 | Card: the app icon, "Kettle", heykettle.com and both lines, one steady hold | Kettle / heykettle.com / For checking in, not checking up. / Now open to founding families. | 10 | 6.60 | 4.4 |

## Self-check against brief §5

Every caption and card line runs through `shots.check` on every build. All pass. Two founder
overrides are recorded in the brief (section 8) and no longer flag: "Know Mom's okay, between the
calls." and "Ask about Mom in Claude or ChatGPT.". The voice lines carry the same words.

## Sounds (v6)

Two soft sounds in shot 5, synthesized by `sfx.py` with ffmpeg (no licence applies): a warm text
tick as Mom's 👍 reply lands on her phone (frame 150), and a light paper pop as the thumbs up rises
(frame 158). In the voice-only mix they sit about 11 and 15 dB under the voice's average level.

## From the v5 A/B clips

A and C are in v6 and v7: A, the push into the phone's screen. B, the zoom onto Mom's card, was in v6 and is out in v7.
C is the push in to the real text message, with its moves and speed unchanged.

## Music (v7)

`audio/music-v2.mp3` from 28.0 s to 75.7 s: the calm middle, after the sparse piano intro (0 to 27 s)
and before the low end comes in at 83 s (drums from 107 s). It fades in over 0.5 s and out over 2 s,
at one steady level 18 dB under the voice.
