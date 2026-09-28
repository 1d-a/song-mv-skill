#!/usr/bin/env bash
# one-time setup: python venv + deps + ffmpeg check + whisper model download
set -euo pipefail
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo "ffmpeg missing: sudo apt-get install -y ffmpeg"; exit 1; }
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
.venv/bin/python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"
echo "ready: use .venv/bin/python -m mvkit.<cmd>"
