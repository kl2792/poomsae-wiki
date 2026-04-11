#!/usr/bin/env python3
"""
Generate timestamped text transcripts from video frames.
Full-frame OCR → timestamped lines → feed to LLM for structured extraction.

Usage:
    python3 transcript.py                  # All forms
    python3 transcript.py koryo            # One form
"""

import os
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pytesseract
from PIL import Image, ImageEnhance, ImageOps

DAT_DIR = Path(__file__).parent.parent / "dat"
FRAMES_DIR = DAT_DIR / "frames"
TRANSCRIPTS_DIR = DAT_DIR / "transcripts"

# Noise patterns to filter
NOISE_RE = re.compile(
    r'KUKKIWON|WORLD TAEKWONDO|POOMSAE\s*$|KEY MOVES|EXPLANATION OF PART|'
    r'ACADEMY|HEADQUARTERS|^\s*[=\-_~<>|{}\[\]]+\s*$|'
    r'^[^a-zA-Z0-9]*$',
    re.IGNORECASE | re.MULTILINE
)


def ocr_frame(frame_path: str) -> str:
    """Full-frame OCR, returns cleaned text."""
    img = Image.open(frame_path)
    w, h = img.size
    # Crop out top/bottom bars (logos + nav)
    cropped = img.crop((0, int(h * 0.06), w, int(h * 0.88)))
    scaled = cropped.resize((cropped.width * 2, cropped.height * 2), Image.LANCZOS)
    gray = ImageOps.grayscale(scaled)
    enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
    text = pytesseract.image_to_string(enhanced, lang='eng', config='--psm 6')
    # Clean: remove noise lines, collapse whitespace
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line or len(line) < 3:
            continue
        if NOISE_RE.search(line):
            continue
        lines.append(line)
    return ' | '.join(lines)


def worker(args: tuple) -> tuple:
    frame_path, timestamp = args
    text = ocr_frame(frame_path)
    return (timestamp, text)


def extract_frames(video_path: str, out_dir: str, fps: float = 1.0) -> list:
    os.makedirs(out_dir, exist_ok=True)
    existing = sorted(Path(out_dir).glob("frame_*.jpg"))
    if existing:
        return [str(f) for f in existing]
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={fps}", "-q:v", "2",
        os.path.join(out_dir, "frame_%05d.jpg"),
        "-loglevel", "warning"
    ], check=True)
    return [str(f) for f in sorted(Path(out_dir).glob("frame_*.jpg"))]


def process_form(slug: str, video_path: str = None, fps: float = 1.0,
                 max_workers: int = 4):
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    frame_dir = str(FRAMES_DIR / slug)

    if video_path:
        frames = extract_frames(video_path, frame_dir, fps=fps)
    else:
        frames = sorted(str(f) for f in Path(frame_dir).glob("frame_*.jpg"))

    if not frames:
        print(f"  No frames for {slug}")
        return

    print(f"  {len(frames)} frames, {max_workers} workers...")

    work = [(f, i) for i, f in enumerate(frames)]
    results = {}
    done = 0

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(worker, w) for w in work]
        for future in as_completed(futures):
            done += 1
            if done % 100 == 0:
                print(f"    {done}/{len(frames)}...")
            ts, text = future.result()
            if text:
                results[ts] = text

    # Write transcript
    out_path = TRANSCRIPTS_DIR / f"{slug}.txt"
    with open(out_path, 'w') as f:
        for ts in sorted(results.keys()):
            f.write(f"[{ts}s] {results[ts]}\n")

    print(f"  Saved: {out_path} ({len(results)} lines)")
    return out_path


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    raw_dir = DAT_DIR / "raw"
    videos = sorted(raw_dir.glob("*.mp4")) if raw_dir.exists() else []

    for video in videos:
        if 'sample' in video.stem.lower():
            continue
        slug = re.sub(r'[^a-z0-9]+', '-', video.stem.lower()).strip('-')
        if target and target not in slug:
            continue
        print(f"\n{'=' * 50}\n{video.stem} -> {slug}\n{'=' * 50}")
        process_form(slug, video_path=str(video))


if __name__ == "__main__":
    main()
