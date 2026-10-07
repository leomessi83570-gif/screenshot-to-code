# lyricgen

Automatic TikTok lyric-video ("speed song") generator. Main entry: `lyricgen.py make`. See README.md (French) for the user-facing guide and `.claude/skills/lyric-video/SKILL.md` for the agent workflow.

- Python: always `.venv/bin/python` (created by `scripts/setup.sh`, which the SessionStart hook runs).
- Heavy assets (models/, fonts/, broll/, projects/) are git-ignored and re-downloaded by setup.
- Models come from GitHub releases of k2-fsa/sherpa-onnx (Hugging Face is not needed).
- Optional network: lrclib.net (official lyrics), pixabay.com + cdn.pixabay.com (b-roll, needs PIXABAY_API_KEY) or api.pexels.com + videos.pexels.com (PEXELS_API_KEY). Every online step degrades gracefully when blocked.
- Talk to the user in French.
