#!/usr/bin/env python3
"""
Parse YouTube auto-caption VTT files into structured JSON.

Auto-captions contain narrated instructional tips with timestamps that OCR misses.
VTT format has overlapping segments with duplicate text; this parser merges them
into deduplicated caption entries.

Usage:
    python3 parse_captions.py taegeuk-1jang    # Parse one form
    python3 parse_captions.py --all            # Parse all forms
"""

import json
import re
import sys
from pathlib import Path

DAT_DIR = Path(__file__).parent.parent / "dat"
RAW_DIR = DAT_DIR / "raw"
CAPTIONS_DIR = DAT_DIR / "captions"

# Import FORM_META from extract.py (same directory)
sys.path.insert(0, str(Path(__file__).parent))
from extract import FORM_META


def parse_vtt_timestamp(ts: str) -> float:
    """Convert VTT timestamp 'HH:MM:SS.mmm' to seconds.

    Args:
        ts: Timestamp string like '00:01:23.456'.

    Returns:
        Time in seconds as a float.
    """
    parts = ts.split(":")
    h, m = int(parts[0]), int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s


def strip_vtt_tags(text: str) -> str:
    """Remove VTT inline timing tags like <00:00:26.800><c> word</c>.

    Args:
        text: Raw VTT caption line with possible inline tags.

    Returns:
        Clean text with tags removed.
    """
    # Remove <c> and </c> tags
    text = re.sub(r"</?c>", "", text)
    # Remove timestamp tags like <00:00:26.800>
    text = re.sub(r"<[\d:.]+>", "", text)
    # Collapse whitespace
    return re.sub(r"\s+", " ", text).strip()


def parse_vtt(vtt_text: str) -> list[dict]:
    """Parse VTT content into raw caption segments.

    Each segment has start, end (seconds) and text. Segments with only
    whitespace, [Music], or empty text are skipped.

    Args:
        vtt_text: Full contents of a .vtt file.

    Returns:
        List of dicts with 'start', 'end', 'text' keys.
    """
    segments = []
    lines = vtt_text.splitlines()
    i = 0

    while i < len(lines):
        # Look for timestamp line: HH:MM:SS.mmm --> HH:MM:SS.mmm
        m = re.match(
            r"(\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2}\.\d{3})",
            lines[i],
        )
        if not m:
            i += 1
            continue

        start = parse_vtt_timestamp(m.group(1))
        end = parse_vtt_timestamp(m.group(2))
        i += 1

        # Collect text lines until blank line or next timestamp
        text_lines = []
        while i < len(lines) and lines[i].strip():
            line = lines[i].strip()
            # Skip [Music] and similar annotations
            if not re.match(r"^\[.*\]$", line):
                text_lines.append(strip_vtt_tags(line))
            i += 1

        text = " ".join(text_lines).strip()
        if text and not re.match(r"^\[.*\]$", text):
            segments.append({"start": start, "end": end, "text": text})

        i += 1

    return segments


def merge_segments(segments: list[dict]) -> list[dict]:
    """Merge overlapping VTT segments into deduplicated captions.

    VTT auto-captions repeat text across overlapping time windows. This
    function merges consecutive segments that share text (one is a prefix
    of the other or they share significant overlap) into single entries
    spanning the full time range.

    Args:
        segments: Raw parsed VTT segments with start, end, text.

    Returns:
        Merged caption entries with deduplicated text.
    """
    if not segments:
        return []

    merged = []
    current = {
        "start": segments[0]["start"],
        "end": segments[0]["end"],
        "text": segments[0]["text"],
    }

    for seg in segments[1:]:
        # Normalize for comparison
        cur_norm = current["text"].lower().strip()
        seg_norm = seg["text"].lower().strip()

        # Check if segments share text (prefix/suffix overlap)
        # VTT duplicates: seg text starts with or contains the current text,
        # or current text ends with the beginning of seg text
        is_continuation = False

        if seg_norm.startswith(cur_norm) or cur_norm.startswith(seg_norm):
            # One is prefix of the other — same content window
            is_continuation = True
        elif cur_norm in seg_norm or seg_norm in cur_norm:
            is_continuation = True
        else:
            # Check if there's word-level overlap at the boundary
            cur_words = cur_norm.split()
            seg_words = seg_norm.split()
            if len(cur_words) >= 2 and len(seg_words) >= 2:
                # Last N words of current match first N words of segment
                for overlap_len in range(min(len(cur_words), len(seg_words)), 0, -1):
                    if cur_words[-overlap_len:] == seg_words[:overlap_len]:
                        is_continuation = True
                        break

        if is_continuation:
            # Extend current segment: keep the longer text, expand time range
            current["end"] = seg["end"]
            if len(seg["text"]) > len(current["text"]):
                current["text"] = seg["text"]
        else:
            # New distinct segment
            merged.append(current)
            current = {
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
            }

    merged.append(current)
    return merged


def find_vtt_file(slug: str) -> Path | None:
    """Find the VTT file for a given form slug.

    Searches dat/ and dat/raw/ for VTT files matching the video title or
    video ID from FORM_META.

    Args:
        slug: Form slug like 'taegeuk-1jang'.

    Returns:
        Path to the VTT file, or None if not found.
    """
    meta = FORM_META.get(slug)
    if not meta:
        return None

    video_id = meta["video_id"]

    # Search patterns: dat/ and dat/raw/ for files containing the video ID
    search_dirs = [DAT_DIR, RAW_DIR]
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for vtt_path in search_dir.glob("*.vtt"):
            if video_id in vtt_path.name:
                return vtt_path

    # Also try matching by title pattern from the info.json files
    # Video titles in raw/ match patterns like "TAEGEUK 1JANG.mp4"
    title_patterns = _slug_to_title_patterns(slug)
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for vtt_path in search_dir.glob("*.vtt"):
            name_lower = vtt_path.stem.lower()
            for pattern in title_patterns:
                if pattern in name_lower:
                    return vtt_path

    return None


def _slug_to_title_patterns(slug: str) -> list[str]:
    """Generate possible video title patterns from a form slug.

    Args:
        slug: Form slug like 'taegeuk-1jang' or 'koryo'.

    Returns:
        List of lowercase patterns to match against filenames.
    """
    patterns = [slug.replace("-", " ")]

    # taegeuk-1jang -> "taegeuk 1jang"
    m = re.match(r"taegeuk-(\d)jang", slug)
    if m:
        patterns.append(f"taegeuk {m.group(1)}jang")

    # Single-word forms: koryo, keumgang, etc.
    if "-" not in slug:
        patterns.append(slug)

    return patterns


def parse_captions(slug: str) -> dict | None:
    """Parse VTT captions for a single form.

    Args:
        slug: Form slug like 'taegeuk-1jang'.

    Returns:
        Dict with form_slug and captions list, or None if no VTT found.
    """
    vtt_path = find_vtt_file(slug)
    if vtt_path is None:
        print(f"  {slug}: no VTT file found, skipping")
        return None

    vtt_text = vtt_path.read_text(encoding="utf-8")
    segments = parse_vtt(vtt_text)
    merged = merge_segments(segments)

    # Round timestamps to 1 decimal
    captions = []
    for seg in merged:
        captions.append({
            "start": round(seg["start"], 1),
            "end": round(seg["end"], 1),
            "text": seg["text"],
        })

    result = {
        "form_slug": slug,
        "source_file": vtt_path.name,
        "captions": captions,
    }

    CAPTIONS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CAPTIONS_DIR / f"{slug}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  {slug}: {len(captions)} captions from {vtt_path.name}")
    print(f"  Wrote {out_path}")
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 parse_captions.py <slug>    Parse one form")
        print("  python3 parse_captions.py --all     Parse all forms")
        print(f"\nSlugs: {', '.join(sorted(FORM_META.keys()))}")
        sys.exit(1)

    if "--all" in sys.argv:
        found = 0
        for slug in sorted(FORM_META.keys()):
            result = parse_captions(slug)
            if result:
                found += 1
        print(f"\nParsed captions for {found}/{len(FORM_META)} forms")
    else:
        slug = [a for a in sys.argv[1:] if not a.startswith("--")][0]
        parse_captions(slug)


if __name__ == "__main__":
    main()
