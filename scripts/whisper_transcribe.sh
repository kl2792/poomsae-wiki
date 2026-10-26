#!/usr/bin/env bash
# Wrapper: run whisper_transcribe.py with OpenMP conflict workaround.
# See whisper_transcribe.py for details.
set -euo pipefail
export KMP_DUPLICATE_LIB_OK=TRUE
exec python3 "$(dirname "$0")/whisper_transcribe.py" "$@"
