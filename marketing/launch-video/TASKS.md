# Launch video checklist

- [x] Phase 0: four questions answered (landscape 75 to 90 s first; no voice-over; Android in; close "Founding families, now")
- [x] look-reference.png = style-tests/01-flat.png; assets/kettle.png copied from origin/video-explainer
- [x] Phase 1: script approved (shot 14 now home health)
- [x] Phase 2: storyboard approved (second Rehearsal seat; parents renamed Mom/Dad for the session; recordings after lock)
- [x] Phase 3: locked (6 of 25 Gemini images), with "Care Compare by HeyKettle" at 44 px
- [x] Phase 4: kitchen look approved; fixes applied (phone on a stand, cream steam, sage oven door, kettle on a trivet, every card seated)
- [x] Phase 4: kitchen animates for shots 2, 6, 7 (blender/kitchen.py)
- [x] Phase 4: map set, shot 1 (blender/map.py)
- [x] Phase 4: phones set, shot 3 (blender/phones.py)
- [x] Phase 4: close, shot 15, and the plate under the screen shots (blender/close.py)
- [x] Phase 4: compositor (render.py): captions, placeholders, recordings path, 16:9 and 9:16
- [x] Phase 4: README with the one render command
- [x] Phase 4: all frames rendered; 16:9 and 9:16 cuts built, 88.5 s, H.264 yuv420p 30 fps, stills in out/shots/
- [x] Recordings R2 to R8 in, cut per shots.RECORDINGS (crops, trims, typing sped up, R6 ends before the 911 line, R8 held)
- [x] R9 in (typing x5, lookup x4, agencies and the scroll to the source line); R6 holds the full list with the 911 line covered
- [x] R1 in (Dad's morning note, Outlook, cropped to the message); render.py run 2026-09-26, no placeholders left
- [x] Shot 10b (her own smart plug) built in Blender; 11b held to 4.7 s; total 95.0 s (founder's cap)
- [x] 10b's words: "Add Mom's smart plug or Alexa routine." (founder, 2026-09-26); 10b 4.7 s, shot 12 5.8 s
- [x] Re-timed to 46.6 s (founder, 2026-09-26): read once + 0.5 s, app screens + 1.0 s, painted shots at most 3 s; shots 2+3 and 6+7a+7b merged
- [x] Founder renamed Rehearsal's parents back to TestMom / TestDad (2026-09-26)
Gemini images, phase 4: 17 of 60
- [x] Phase 4: remaining scenes, compositing, 16:9 + 9:16 renders, README, PROMPTS.md (<= 60 Gemini images)
- [x] Commit and push on branch launch-video (kept current)
- [x] v4 re-cut (founder, 2026-09-27): 39.2 s on voiceover-v2; built and reviewed, then replaced by v5
- [x] v5 (founder, 2026-09-28): the committed cut's shots on voiceover-v3, app icon over the phones, push-in into the note, fixed kettle in 07, new more-ways and end cards; A/B clips A, B, C
- [x] v6 (founder, 2026-09-28): v5 with the A/B extras in, a 0.75 s note hold, two soft sounds in the kitchen, the stillness after the thumbs up trimmed; 47.7 s
- [x] v7 (founder, 2026-09-28): v6 without the zoom onto Mom's card, new music (music-v2 from 28.0 s); approved as the final 16:9 cut
- [x] Finals: out/kettle-launch-16x9.mp4 (v7) and out/kettle-launch-9x16.mp4 (the same edit reframed for vertical, captions and cards clear of the top and bottom 12%); 47.7 s, -16.0 LUFS, -1.6 dBTP
- [x] Commit and push the final build on launch-video (not merged to main)
- [x] Founder overrides recorded in the brief, section 8: "Know Mom's okay" and the ChatGPT claim (2026-09-28)

## Future short videos (cut from the launch video, 2026-09-27)

- [ ] Medicare ratings: Care Compare by HeyKettle, home health near a ZIP (recording R9 and its old shots 14a/14b)
- [ ] Kettle in Claude and ChatGPT: ask who to call, add a note, it lands in Memory (recordings R6, R7, R8; check ChatGPT is live first)
- [ ] Smart plug and Alexa: add Mom's own plug or routine (Blender shot 10b)
