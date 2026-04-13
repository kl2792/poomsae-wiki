#!/usr/bin/env bash
# Run extraction script in hardened Docker container
# Usage: ./run_extract.sh <form-slug> <script.py>
#
# Mounts:
#   /input/transcript.txt  (ro) — OCR transcript
#   /input/captions.json   (ro) — parsed captions
#   /output/               (rw) — extraction script output
#
# Security:
#   --network none          — no network
#   --cap-drop ALL          — no capabilities
#   --read-only             — immutable root
#   --security-opt no-new-privileges
#   --tmpfs /tmp            — writable tmp, no exec

set -euo pipefail

SLUG="$1"
SCRIPT="$2"

DAT_DIR="$(cd "$(dirname "$0")/../dat" && pwd)"
TRANSCRIPT="$DAT_DIR/transcripts/${SLUG}.txt"
CAPTIONS="$DAT_DIR/captions/${SLUG}.json"
OUTPUT_DIR="$DAT_DIR/sandbox-out/${SLUG}"

mkdir -p "$OUTPUT_DIR"

# Build image if needed
IMAGE="poom-extract"
docker build -q -t "$IMAGE" -f "$(dirname "$0")/Dockerfile.extract" "$(dirname "$0")" >/dev/null

# Run extraction in sandbox
docker run --rm \
  --network none \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  --read-only \
  --tmpfs /tmp:noexec,nosuid,size=256m \
  -v "$TRANSCRIPT:/input/transcript.txt:ro" \
  -v "${CAPTIONS}:/input/captions.json:ro" \
  -v "$SCRIPT:/work/extract.py:ro" \
  -v "$OUTPUT_DIR:/output" \
  "$IMAGE" /work/extract.py

echo "Output in $OUTPUT_DIR"
ls -la "$OUTPUT_DIR"
