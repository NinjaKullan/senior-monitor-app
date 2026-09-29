# Feature videos

Three short videos in the launch film's style, from its sets and recordings, each on its own voice
take. The shots, words and voice spans live in `features.py`; this is the human copy.

```sh
KETTLE_CUT=family python3 render.py        # out/kettle-family-16x9.mp4 and -9x16.mp4
KETTLE_CUT=smarthome python3 render.py
KETTLE_CUT=carecompare python3 render.py
```

Voice lines are the spans between each take's silences (ffmpeg silencedetect, -40 dB, 0.3 s),
padded 0.05 s. Pacing as the launch film: 0.3 s dissolves, each line 0.2 s after its cut, at least
0.5 s between lines, and the v7 end card on the last line ("Kettle. For checking in, not checking
up."), held through its 0.8 s fade. Music: `music-v2.mp3` from 28.0 s at one steady level, 18 dB
under the voice. Both formats are mastered to -16 LUFS, true peak -1 dBTP or lower.

## Family: 24.2 s

| # | Voice (s in take) | Picture | Caption | Length (s) |
|---|---|---|---|---|
| 1 | 0.00–3.64 | The houses (launch shot 1, map.py; 9 frames longer) | Mom and Dad live on their own, / and the whole family wants to help. | 4.2 |
| 2 | 3.94–7.08 | New: a phone face up, message bubbles and missed-call chips landing around it (phones.py sc) | But the updates end up scattered / across texts and calls. | 3.7 |
| 3 | 7.39–10.20 | Screen R3: Memory, notes and replies | Kettle keeps it in one place, / for everyone. | 3.4 |
| 4 | 10.52–12.83 | Screen R5: the family circle | Brothers and sisters / see the same notes. | 2.9 |
| 5 | 13.09–15.90 | Screen R6: Claude, who to call (old 11a/11b) | And you can reach it / from Claude or ChatGPT. | 3.4 |
| 6 | 16.18–18.13 | The founder's replacement Claude clip (recordings/claude-note.MP4): the note "Mom's doctor appointment is Thursday at 2." and Claude's proposed note, held; never R7 | Ask who to call, / or leave a note. | 2.5 |
| 7 | 18.45–21.39 | The v7 end card | Kettle / heykettle.com / For checking in, not checking up. / Now open to founding families. | 4.1 |

## Smart home: 11.3 s

Short (founder): minimum pacing, no long silent holds. In these three shots the kettle stands
further right, wholly out of the close-up (and out of every 9:16 frame, which has no room for it
whole), and the window hangs further left, behind the plant, so the captions sit on plain wall.
Dad's folded newspaper darkens a little as the lamp comes on, which otherwise blows it out white.

| # | Voice (s in take) | Picture | Caption | Length (s) |
|---|---|---|---|---|
| 1 | 0.00–2.69 | New: Dad's kitchen, close on the smart plug (its green light), the speaker and his folded newspaper; lamp off (kitchen.py 10a) | Already have a smart plug / or Alexa at Dad's? | 3.2 |
| 2 | 2.95–3.79 | 10b from frame 30: the lamp on the smart plug comes on | Add it to Kettle. | 1.4 |
| 3 | 4.08–6.35 | 10c: from 10b's framing, a slow pull-back to the whole kitchen, lamp on | One more way Kettle / hears from his day. | 2.8 |
| 4 | 6.67–9.40 | The v7 end card | (as above) | 3.9 |

## Care Compare: 17.2 s

No jump back (founder): every shot is later in the recording than the one before.

| # | Voice (s in take) | Picture | Caption | Length (s) |
|---|---|---|---|---|
| 1 | 0.00–2.24 | R9 from its start: the question being typed (complete only at 3.2 s) | Looking for home health care / for Mom? | 2.8 |
| 2 | 3.07–7.72 | R9 12.0–16.0 s, slowed to 0.75x: the five agencies arriving | Care Compare by HeyKettle / reads Medicare's own ratings, / in plain words. | 5.2 |
| 3 | 7.94–9.88 | R9 at 16.0 s held, as a detail of the whole question bubble pushing in slowly and drifting toward the ZIP (43215); the bubble is never cropped | Free. / Just enter a ZIP code. | 2.5 |
| 4 | 10.15–12.22 | R9 at 25.8 s: Medicare's source line and "When you call, ask whether they serve your address..." | Then call and ask / your own questions. | 2.6 |
| 5 | 12.46–15.49 | The v7 end card | (as above) | 4.1 |
