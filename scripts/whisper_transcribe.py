#!/usr/bin/env python3
"""Transcribe KKW poomsae videos using faster-whisper (CTranslate2).

RAM budget: ~5GB peak (medium model, int8 quantized). Well under 32GB.
Speed: ~4-6x faster than vanilla openai-whisper on CPU.

Usage:
    python3 scripts/whisper_transcribe.py                     # all videos
    python3 scripts/whisper_transcribe.py "KORYO.mp4"         # single video
"""

import os
import sys
from pathlib import Path

# Avoid OpenMP duplicate-library abort (torch + ctranslate2 both link libiomp5)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from faster_whisper import WhisperModel

DAT_DIR = Path(__file__).parent.parent / "dat"
RAW_DIR = DAT_DIR / "raw"
OUT_DIR = DAT_DIR / "whisper"

MODEL = "medium"
THREADS = 4


def format_vtt_ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def transcribe(mp4_path: Path, out_dir: Path, model: WhisperModel) -> Path:
    """Transcribe a single video to VTT."""
    out_path = out_dir / f"{mp4_path.stem}.vtt"

    segments, info = model.transcribe(
        str(mp4_path), language="en", vad_filter=True
    )

    with open(out_path, "w") as f:
        f.write("WEBVTT\n\n")
        count = 0
        for seg in segments:
            f.write(f"{format_vtt_ts(seg.start)} --> {format_vtt_ts(seg.end)}\n")
            f.write(f"{seg.text.strip()}\n\n")
            count += 1
        if count == 0:
            f.write("NOTE No speech detected\n\n")

    print(f"  lang={info.language} (p={info.language_probability:.2f}), "
          f"duration={info.duration:.0f}s, segments={count}")
    return out_path


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 1:
        files = [RAW_DIR / sys.argv[1]]
    else:
        files = sorted(
            f for f in RAW_DIR.glob("*.mp4")
            if not f.name.startswith("sample_")
        )

    total = len(files)
    if total == 0:
        print("No .mp4 files found in", RAW_DIR)
        sys.exit(1)

    # Load model once (downloads on first run, ~1.5GB for medium)
    print(f"Loading {MODEL} model (int8, {THREADS} threads)...")
    model = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=THREADS)
    print("Model loaded.\n")

    done = 0
    skipped = 0
    for i, mp4 in enumerate(files, 1):
        if not mp4.exists():
            print(f"[{i}/{total}] {mp4.name} — NOT FOUND, skipping")
            continue

        vtt_path = OUT_DIR / f"{mp4.stem}.vtt"
        if vtt_path.exists() and vtt_path.stat().st_size > 10:
            print(f"[{i}/{total}] {mp4.stem} — already done, skipping")
            skipped += 1
            continue

        print(f"[{i}/{total}] {mp4.stem} — transcribing...")
        transcribe(mp4, OUT_DIR, model)
        done += 1

    vtts = list(OUT_DIR.glob("*.vtt"))
    print(f"\nDone. {done} transcribed, {skipped} skipped. {len(vtts)} VTT files total.")


if __name__ == "__main__":
    main()
