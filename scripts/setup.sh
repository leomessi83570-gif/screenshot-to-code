#!/usr/bin/env bash
# Idempotent install: ffmpeg, Python venv, models (~740 MB), fonts. Safe to run at every session start.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "installing ffmpeg…"
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo -n"
  ($SUDO apt-get update -qq && $SUDO apt-get install -y -qq ffmpeg) >/dev/null 2>&1 \
    || echo "WARN: could not install ffmpeg automatically — install it manually"
fi

[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/pip install -q --disable-pip-version-check -r requirements.txt
.venv/bin/python lyricgen.py setup
echo "lyricgen ready: .venv/bin/python lyricgen.py make <clip> --artist X --title Y"
