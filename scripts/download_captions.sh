#!/usr/bin/env bash
# Download auto-captions (VTT) for all KKW poomsae videos, without re-downloading video files.
set -euo pipefail

DAT_DIR="$(cd "$(dirname "$0")/../dat" && pwd)"
RAW_DIR="$DAT_DIR/raw"

PLAYLIST="https://www.youtube.com/playlist?list=PLSFr5pEwo7gSwvfg4bjxoF3liyfJkCLAj"

echo "Downloading auto-captions to $RAW_DIR ..."
yt-dlp \
  --write-auto-sub --sub-lang en --sub-format vtt \
  --skip-download \
  -o "$RAW_DIR/%(title)s [%(id)s].%(ext)s" \
  "$PLAYLIST"

echo "Done. VTT files:"
ls -lh "$RAW_DIR"/*.vtt 2>/dev/null || echo "(no VTT files found)"
