#!/usr/bin/env python3
"""
OCR pipeline for KKW poomsae videos.

Two-pass approach:
  Pass 1: OCR title region on every frame (1fps) → move boundaries
  Pass 2: OCR tip regions only on frames within move segments

Usage:
    python3 ocr.py                    # Process all forms
    python3 ocr.py taegeuk-1jang      # Process one form
"""

import json
import os
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageOps
except ImportError:
    print("Install: pip3 install pytesseract Pillow")
    sys.exit(1)

DAT_DIR = Path(__file__).parent.parent / "dat"
FRAMES_DIR = DAT_DIR / "frames"
OCR_DIR = DAT_DIR / "ocr"

MOVE_TITLE_RE = re.compile(r'(\d{1,2})\.\s*([A-Z][A-Z\s()]+)')
TIP_RE = re.compile(r'[✓✔☑]\s*(.+)', re.DOTALL)
SECTION_RE = re.compile(r'\b(REPEAT)\b', re.IGNORECASE)
NAV_BAR_RE = re.compile(r'POOMSAE|KEY MOVES|EXPLANATION OF PART', re.IGNORECASE)


def preprocess(img, scale=2):
    w, h = img.size
    scaled = img.resize((w * scale, h * scale), Image.LANCZOS)
    gray = ImageOps.grayscale(scaled)
    return ImageEnhance.Contrast(gray).enhance(2.0)


# --- Pass 1: Title detection ---

def ocr_title(frame_path: str) -> dict | None:
    """OCR the title region of a frame. Returns move info or None."""
    img = Image.open(frame_path)
    w, h = img.size

    # Title region: left 55%, y 25-70% (wide enough for long names)
    region = img.crop((int(w * 0.05), int(h * 0.25), int(w * 0.55), int(h * 0.70)))
    processed = preprocess(region, scale=3)
    text = pytesseract.image_to_string(processed, lang='eng', config='--psm 7').strip()

    match = MOVE_TITLE_RE.search(text)
    if match:
        return {
            "number": int(match.group(1)),
            "technique": match.group(2).strip()
        }

    # Check for REPEAT section header (full frame, skip nav bar)
    # Only check the center band (not bottom nav)
    center = img.crop((int(w * 0.2), int(h * 0.3), int(w * 0.8), int(h * 0.7)))
    center_processed = preprocess(center, scale=2)
    center_text = pytesseract.image_to_string(center_processed, lang='eng', config='--psm 6').strip()
    if SECTION_RE.search(center_text) and not NAV_BAR_RE.search(center_text):
        return {"section": "REPEAT"}

    return None


def pass1_worker(args: tuple) -> tuple:
    """Worker for parallel title detection. Returns (timestamp, result)."""
    frame_path, timestamp = args
    result = ocr_title(frame_path)
    return (timestamp, frame_path, result)


# --- Pass 2: Tip extraction ---

def ocr_tips(frame_path: str) -> str | None:
    """OCR tip text from a frame. Tips can appear on either side."""
    img = Image.open(frame_path)
    w, h = img.size

    # Try right side first (more common)
    right = img.crop((int(w * 0.45), int(h * 0.20), int(w * 0.95), int(h * 0.80)))
    right_processed = preprocess(right, scale=2)
    right_text = pytesseract.image_to_string(right_processed, lang='eng', config='--psm 6').strip()

    tip_match = TIP_RE.search(right_text)
    if tip_match:
        return tip_match.group(1).strip()

    # Try left side
    left = img.crop((int(w * 0.05), int(h * 0.20), int(w * 0.55), int(h * 0.80)))
    left_processed = preprocess(left, scale=2)
    left_text = pytesseract.image_to_string(left_processed, lang='eng', config='--psm 6').strip()

    tip_match = TIP_RE.search(left_text)
    if tip_match:
        return tip_match.group(1).strip()

    # Substantial text without checkmark (OCR may miss the ✓)
    for text in [right_text, left_text]:
        # Filter out nav bar text and short garbage
        if len(text) > 40 and not NAV_BAR_RE.search(text):
            return text

    return None


def pass2_worker(args: tuple) -> tuple:
    """Worker for parallel tip extraction."""
    frame_path, timestamp = args
    tip = ocr_tips(frame_path)
    return (timestamp, tip)


# --- Pipeline ---

def extract_frames(video_path: str, out_dir: str, fps: float = 1.0) -> list:
    """Extract frames from video at given fps."""
    os.makedirs(out_dir, exist_ok=True)
    existing = sorted(Path(out_dir).glob("frame_*.jpg"))
    if existing:
        print(f"  Frames exist ({len(existing)}), reusing")
        return [str(f) for f in existing]

    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={fps}", "-q:v", "2",
        os.path.join(out_dir, "frame_%05d.jpg"),
        "-loglevel", "warning"
    ], check=True)

    frames = sorted(Path(out_dir).glob("frame_*.jpg"))
    print(f"  Extracted {len(frames)} frames")
    return [str(f) for f in frames]


def process_form(form_slug: str, video_path: str = None, fps: float = 1.0,
                 max_workers: int = 4):
    """Full pipeline: extract → title pass → segment → tip pass."""
    OCR_DIR.mkdir(parents=True, exist_ok=True)
    frame_dir = str(FRAMES_DIR / form_slug)

    # Extract frames
    if video_path:
        frames = extract_frames(video_path, frame_dir, fps=fps)
    else:
        frames = sorted(str(f) for f in Path(frame_dir).glob("frame_*.jpg"))
    if not frames:
        print(f"  ERROR: no frames for {form_slug}")
        return

    # --- Pass 1: Title detection (every frame, parallel) ---
    print(f"  Pass 1: Title detection on {len(frames)} frames ({max_workers} workers)...")
    work = [(f, round(i / fps, 1)) for i, f in enumerate(frames)]
    title_results = []
    done = 0

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(pass1_worker, w) for w in work]
        for future in as_completed(futures):
            done += 1
            if done % 100 == 0:
                print(f"    {done}/{len(frames)}...")
            ts, path, result = future.result()
            if result:
                title_results.append((ts, path, result))

    title_results.sort(key=lambda x: x[0])
    print(f"  Pass 1: {len(title_results)} detections")

    # --- Segment moves ---
    moves = []
    current = None
    repeat_ts = None

    for ts, path, result in title_results:
        if "section" in result:
            if result["section"] == "REPEAT":
                repeat_ts = ts
                if current:
                    current["timestamp_end"] = ts
                    moves.append(current)
                    current = None
            continue

        num = result["number"]
        # Same move on consecutive frame — skip
        if current and current["number"] == num:
            continue
        # Close previous
        if current:
            current["timestamp_end"] = ts
            moves.append(current)
        # Start new
        current = {
            "number": num,
            "technique": result["technique"],
            "timestamp_start": ts,
            "timestamp_end": None,
            "tips": []
        }

    if current:
        current["timestamp_end"] = repeat_ts or (len(frames) / fps)
        moves.append(current)

    print(f"  Segmented: {len(moves)} moves" +
          (f", REPEAT at {repeat_ts}s" if repeat_ts else ""))

    # --- Pass 2: Tip extraction (only frames within move segments) ---
    tip_work = []
    for move in moves:
        start_frame = int(move["timestamp_start"] * fps)
        end_frame = int(move["timestamp_end"] * fps) if move["timestamp_end"] else len(frames)
        for i in range(start_frame, min(end_frame, len(frames))):
            tip_work.append((frames[i], round(i / fps, 1)))

    if tip_work:
        print(f"  Pass 2: Tip extraction on {len(tip_work)} frames...")
        tip_results = {}
        done = 0

        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(pass2_worker, w) for w in tip_work]
            for future in as_completed(futures):
                done += 1
                if done % 100 == 0:
                    print(f"    {done}/{len(tip_work)}...")
                ts, tip = future.result()
                if tip:
                    tip_results[ts] = tip

        # Assign tips to moves
        for move in moves:
            start = move["timestamp_start"]
            end = move["timestamp_end"] or 9999
            for ts in sorted(tip_results.keys()):
                if start <= ts < end:
                    tip = tip_results[ts]
                    # Deduplicate
                    if not move["tips"] or move["tips"][-1] != tip:
                        move["tips"].append(tip)

    # --- Save results ---
    seg_path = OCR_DIR / f"{form_slug}.json"
    output = {
        "form": form_slug,
        "total_moves": len(moves),
        "repeat_timestamp": repeat_ts,
        "moves": moves,
    }
    with open(seg_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"  Saved: {seg_path}")

    # Summary
    for m in moves:
        tips_str = f" ({len(m['tips'])} tips)" if m['tips'] else ""
        end = m['timestamp_end'] or '?'
        print(f"    {m['number']:2d}. {m['technique']:<30s} "
              f"[{m['timestamp_start']}s - {end}s]{tips_str}")
    if repeat_ts:
        print(f"    [REPEAT] at {repeat_ts}s")

    return output


def main():
    FPS = 1.0  # 1 frame per second — reliable, fast enough with parallelism

    target = sys.argv[1] if len(sys.argv) > 1 else None
    raw_dir = DAT_DIR / "raw"
    videos = sorted(raw_dir.glob("*.mp4")) if raw_dir.exists() else []

    if not videos:
        if not FRAMES_DIR.exists():
            print("No videos or frames. Run download.sh first.")
            sys.exit(1)
        form_dirs = sorted(d.name for d in FRAMES_DIR.iterdir()
                           if d.is_dir() and not d.name.startswith('.'))
        if target:
            form_dirs = [d for d in form_dirs if target in d]
        for slug in form_dirs:
            print(f"\n{'=' * 60}\n{slug}\n{'=' * 60}")
            process_form(slug, fps=FPS)
        return

    for video in videos:
        name = video.stem
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        if target and target not in slug:
            continue
        print(f"\n{'=' * 60}\n{name} -> {slug}\n{'=' * 60}")
        process_form(slug, video_path=str(video), fps=FPS)


if __name__ == "__main__":
    main()
