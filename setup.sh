#!/usr/bin/env bash
# One-time setup per workspace. Run from the repo root. ~3 min.
set -e
cd "$(dirname "$0")"
mkdir -p raw work sheets stills
pip install -q --break-system-packages faster-whisper pillow-heif numpy pillow
(cd kvf-video && npm i --no-audit --no-fund)
chmod +x proxy.sh setup_enhance.sh
command -v ffmpeg >/dev/null || { echo "ffmpeg missing"; exit 1; }
echo "setup ok"
