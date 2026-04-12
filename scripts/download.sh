#!/usr/bin/env bash
# Download all KKW poomsae videos at 720p
set -euo pipefail

DAT_DIR="$(cd "$(dirname "$0")/../dat" && pwd)"
RAW_DIR="$DAT_DIR/raw"
mkdir -p "$RAW_DIR"

PLAYLIST="https://www.youtube.com/playlist?list=PLSFr5pEwo7gSwvfg4bjxoF3liyfJkCLAj"

echo "Downloading all videos to $RAW_DIR ..."
yt-dlp \
  -f "bestvideo[height<=720]+bestaudio/best[height<=720]" \
  --merge-output-format mp4 \
  -o "$RAW_DIR/%(title)s.%(ext)s" \
  --write-info-json \
  --write-auto-sub --sub-lang en --sub-format vtt \
  "$PLAYLIST"

echo "Done. Videos:"
ls -lh "$RAW_DIR"/*.mp4
