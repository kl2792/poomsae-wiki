#!/usr/bin/env bash
# Extract frames at 1fps from all downloaded videos
set -euo pipefail

DAT_DIR="$(cd "$(dirname "$0")/../dat" && pwd)"
RAW_DIR="$DAT_DIR/raw"
FRAMES_DIR="$DAT_DIR/frames"

for video in "$RAW_DIR"/*.mp4; do
  name=$(basename "$video" .mp4)
  # Convert to slug: lowercase, spaces to hyphens
  slug=$(echo "$name" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g' | sed 's/[^a-z0-9-]//g')
  outdir="$FRAMES_DIR/$slug"

  if [ -d "$outdir" ] && [ "$(ls "$outdir"/*.jpg 2>/dev/null | wc -l)" -gt 0 ]; then
    echo "SKIP $name (frames exist)"
    continue
  fi

  mkdir -p "$outdir"
  echo "Extracting frames: $name -> $slug"
  ffmpeg -i "$video" -vf fps=1 -q:v 2 "$outdir/frame_%04d.jpg" -loglevel warning
  count=$(ls "$outdir"/*.jpg | wc -l)
  echo "  -> $count frames"
done

echo "Done."
