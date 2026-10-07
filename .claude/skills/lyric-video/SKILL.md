---
name: lyric-video
description: Turn a song clip (TikTok download, screen recording, MP3) into finished TikTok "speed song" lyric videos with word-by-word lyrics, night b-roll and a caption. Use when the user sends a song/clip and wants a lyric video, edit, "speed song" or paroles video.
---

# lyric-video

Goal: the user sends raw material, you hand back videos ready to post. Do everything yourself; only ask when something is truly missing.

## 1. Inputs
- The clip: an uploaded file (look in the uploads dir the user @-mentions) or a path. The clip's sound is kept in the output.
- Artist + title: take them from the message. If missing, ask once in a single short question.
- Optional: style (`damso` = blue words, `bello` = white words + purple last word + line subtitle, `cream` = huge cream type), b-roll searches ("dubai night"…), start/end seconds.

## 2. Run
```bash
scripts/setup.sh   # no-op if already installed (the SessionStart hook runs it too)
.venv/bin/python lyricgen.py make "<clip>" --artist "<Artist>" --title "<Title>" [--style damso bello] [--broll-query "dubai night" "night drive"] [--start S --end E]
```
It separates the vocals, transcribes with word timestamps, swaps in official lyrics from LRCLIB when reachable, downloads Pixabay/Pexels b-roll when `PIXABAY_API_KEY`/`PEXELS_API_KEY` is set (else uses `broll/` or the source video), renders each style and writes `caption.txt`.

## 3. Check before sending
- Contact sheet: `ffmpeg -v error -y -i OUT.mp4 -vf "fps=1/2,scale=270:-1,tile=6x3" -frames:v 1 sheet.jpg` then Read it. Words must be readable and centred.
- Read `projects/<name>/lyrics.txt`. If the log says official lyrics were NOT used, look for mis-heard words (nonsense, wrong names, the song title misspelled). Fix what you are sure of, then:
  `.venv/bin/python lyricgen.py align projects/<name> && .venv/bin/python lyricgen.py render projects/<name> --style <styles> [--broll-dir broll]`
- Never invent lyrics. List the words you are unsure of so the user can correct them.

## 4. Deliver
Send every MP4 + the caption with SendUserFile, in one message. Tell the user in 2-3 lines: styles made, lyrics source (official / transcription), words to double-check.
