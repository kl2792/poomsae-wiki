#!/usr/bin/env python3
"""
Deterministic pre-extraction of technique names, tips, and sections from OCR transcripts.

No LLM involved -- regex only. Produces a ground-truth anchor file that the LLM
extraction stage must respect (preventing hallucinated technique names).

Usage:
    python3 pre_extract.py taegeuk-7jang       # Pre-extract one form
    python3 pre_extract.py --all               # Pre-extract all forms
"""

import json
import re
import sys
from pathlib import Path

DAT_DIR = Path(__file__).parent.parent / "dat"
TRANSCRIPTS_DIR = DAT_DIR / "transcripts"
CAPTIONS_DIR = DAT_DIR / "captions"
PRE_DIR = DAT_DIR / "pre"

# Import FORM_META from extract.py (same directory)
sys.path.insert(0, str(Path(__file__).parent))
from extract import FORM_META

# Words that should never be a complete technique name
NOISE_NAMES = frozenset({
    "KEY", "MOVES", "EXPLANATION", "PART", "REPEAT", "POOMSAE",
    "TAEGEUK", "KUKKIWON", "KUKIIWON", "KUEKIWON", "KEUKKWON",
    "TAEKWONDO", "ACADEMY", "JANG", "OF", "OOOO", "OOOOO",
    "OEN", "OREN", "OREUN", "LEFT", "RIGHT",
    # Trigram / section labels that OCR picks up with numbers
    "MOUNTAIN", "HEAVEN", "LAKE", "FIRE", "THUNDER", "WIND", "WATER", "EARTH",
    "EIGHT", "TRIGRAMS", "TRIGRAM",
    "GAN", "KEON", "TAE", "RI", "JIN", "SON", "GAM", "GON",
})

# OCR garbage suffixes that get appended to technique names
OCR_GARBAGE = re.compile(
    r"\s+(?:"
    r"[VWMF]+E[VYO]+\s*(?:A+[NMC]+|M).*"     # VEV MANV/EO, WEV AANM/EO, etc.
    r"|XX\s+OREN.*"                             # XX OREN = right/left markers
    r"|[WYM]\s+XX\s+.*"                         # W XX OREN...
    r"|[=<>:;,.\-]+\s*$"                         # trailing punctuation
    r"|[a-z]{1,3}\s*$"                           # trailing lowercase fragments
    r"|\d+\s*$"                                  # trailing numbers
    r"|[A-Z]{1,2}\s*$"                           # one or two letter fragments
    r")"
)


def parse_timestamp(line: str) -> int | None:
    """Extract timestamp in seconds from a transcript line like '[123s] ...'."""
    m = re.match(r"\[(\d+)s\]", line)
    return int(m.group(1)) if m else None


def clean_technique_name(name: str) -> str:
    """Remove OCR garbage from the end of a technique name."""
    name = re.sub(r"\s+", " ", name).strip()
    # Remove trailing OCR artifacts
    name = OCR_GARBAGE.sub("", name).strip()
    # Remove trailing non-alpha characters
    name = re.sub(r"[^A-Z()]+$", "", name).strip()
    return name


def is_noise(name: str) -> bool:
    """Check if a name consists entirely of noise words."""
    words = set(re.sub(r"[^A-Z\s]", "", name).split())
    return words <= NOISE_NAMES or len(name) < 4


def extract_key_moves(lines: list[str]) -> list[dict]:
    """Extract numbered KEY MOVES technique names.

    Strategy:
    1. Find summary list lines (3+ numbered entries in one line) for authoritative names
    2. Find individual breakdown headers (NN. TECHNIQUE) for per-technique timestamps
    3. Merge: names from summary, timestamps from individual breakdowns
    """
    # Phase 1: Extract from KEY MOVES summary list lines.
    # Summary lines have 3+ numbered technique entries separated by pipes.
    # Distinguish from EXPLANATION sequence lists by: summary uses 2-digit numbers
    # (01., 02., ...) and names do NOT start with OEN/OREUN side indicators.
    summary_moves = {}  # number -> name
    for line in lines:
        # Quick check: does this line have 3+ zero-padded numbered entries (01., 02., ...)?
        if len(re.findall(r"0\d[.,]\s+[A-Z]", line)) < 2:
            continue

        segments = line.split("|")
        for seg in segments:
            seg = seg.strip()
            m = re.match(r".*?(\d{1,2})[.,]\s+([A-Z][A-Z\s()\+]+)", seg)
            if not m:
                continue
            num = int(m.group(1))
            name = clean_technique_name(m.group(2))
            if is_noise(name):
                continue
            # Skip if name starts with OEN/OREUN (that's a sequence step, not summary)
            if re.match(r"^(OEN|OREUN)\s+", name):
                continue
            # Keep longest name across all summary appearances
            if num not in summary_moves or len(name) > len(summary_moves[num]):
                summary_moves[num] = name

    # Phase 2: Extract individual breakdown headers for timestamps.
    # These are NN. TECHNIQUE lines that appear solo in the KEY MOVES section
    # (before EXPLANATION OF PART). We stop when we see "EXPLANATION" + "OF PART"
    # or "OEN = left" (sequence legend) to avoid picking up sequence steps.
    # Note: bare "EXPLANATION" can appear as a label for the KEY MOVES section itself.
    breakdown_ts = {}  # number -> timestamp (first occurrence)
    breakdown_names = {}  # number -> name
    for line in lines:
        ts = parse_timestamp(line)
        if ts is None:
            continue

        # Stop at EXPLANATION OF PART section (where sequence steps begin)
        if "EXPLANATION" in line and "PART" in line:
            break
        # Also stop if we see the OEN/OREN legend (marks sequence area)
        if re.search(r"OEN\s*=\s*left", line) or re.search(r"OREN\s*=\s*right", line):
            break

        # Skip summary list lines
        entries = re.findall(r"\d{1,2}[.,]\s+[A-Z]", line)
        if len(entries) >= 3:
            continue

        segments = line.split("|")
        for i, seg in enumerate(segments):
            seg = seg.strip()
            m = re.match(r"(\d{1,2})[.,]\s+([A-Z][A-Z\s()\+]+)", seg)
            if not m:
                continue
            num = int(m.group(1))
            name = m.group(2).strip()

            # Try to extend with next segment (multi-line OCR technique names)
            if i + 1 < len(segments):
                next_seg = segments[i + 1].strip()
                next_m = re.match(r"([A-Z(][A-Z\s()]+)", next_seg)
                if next_m:
                    extended = name + " " + next_m.group(1).strip()
                    extended = clean_technique_name(extended)
                    if not is_noise(extended):
                        name = extended

            name = clean_technique_name(name)
            if is_noise(name):
                continue

            # Record first timestamp for each technique number
            if num not in breakdown_ts:
                breakdown_ts[num] = ts

            # Track breakdown names separately (don't override summary names)
            if num not in breakdown_names or len(name) > len(breakdown_names[num]):
                breakdown_names[num] = name

    # Only use breakdown names for techniques NOT in summary
    for num, name in breakdown_names.items():
        if num not in summary_moves:
            summary_moves[num] = name

    # Phase 3: Merge
    result = []
    for num in sorted(summary_moves):
        result.append({
            "number": f"{num:02d}",
            "name": summary_moves[num],
            "timestamp": breakdown_ts.get(num, 0),
        })
    return result


def _parse_step_from_segment(seg: str) -> dict | None:
    """Parse a single numbered step from a pipe-separated segment.

    Returns dict with keys {num, name, side} or None if no match.
    """
    seg = seg.strip()

    # Match: N. (OEN|OREUN) TECHNIQUE
    m = re.match(
        r"(\d{1,2})[.,]\s+(OEN|OREUN)\s+([A-Z][A-Z\s()\+]{3,})",
        seg,
    )
    if m:
        name = clean_technique_name(m.group(3))
        if is_noise(name):
            return None
        return {
            "num": int(m.group(1)),
            "name": name,
            "side": "left" if m.group(2) == "OEN" else "right",
        }

    # Match: N. TECHNIQUE (no side prefix -- less common)
    m2 = re.match(r"(\d{1,2})[.,]\s+([A-Z][A-Z\s()\+]{3,})", seg)
    if m2:
        name = m2.group(2).strip()

        side = None
        if name.startswith("OEN "):
            side = "left"
            name = name[4:]
        elif name.startswith("OREUN "):
            side = "right"
            name = name[6:]

        name = clean_technique_name(name)
        if is_noise(name):
            return None
        return {"num": int(m2.group(1)), "name": name, "side": side}

    return None


def _find_explanation_sections(lines: list[str]) -> list[tuple[int, int]]:
    """Find timestamp ranges for each EXPLANATION OF PART section.

    Returns list of (start_ts, end_ts) tuples. End timestamp is the start
    of the next section, or the REPEAT section, or the last line timestamp.
    """
    section_starts = []  # timestamps where EXPLANATION sections begin
    repeat_ts = None
    last_ts = 0

    for line in lines:
        ts = parse_timestamp(line)
        if ts is None:
            continue
        last_ts = ts

        # Detect "EXPLANATION ... PART" or "OF PART N" headers
        if ("EXPLANATION" in line and "PART" in line) or re.search(r"OF\s*PART\s*\d", line):
            if not section_starts or ts > section_starts[-1] + 30:
                section_starts.append(ts)

        if "REPEAT" in line and section_starts:
            if repeat_ts is None:
                repeat_ts = ts

    if not section_starts:
        return []

    end_ts = repeat_ts if repeat_ts else last_ts + 1

    ranges = []
    for i, start in enumerate(section_starts):
        if i + 1 < len(section_starts):
            ranges.append((start, section_starts[i + 1]))
        else:
            ranges.append((start, end_ts))
    return ranges


def _extract_steps_for_section(
    lines: list[str], start_ts: int, end_ts: int,
) -> list[dict]:
    """Extract step list from one EXPLANATION section by finding the best line.

    The best line is the one with the most numbered step items, since each
    frame adds one step incrementally and the last frame has the full list.

    Returns list of {name, side, timestamp} dicts in step order.
    """
    best_steps: dict[int, dict] = {}  # num -> {name, side, timestamp}
    best_count = 0

    for line in lines:
        ts = parse_timestamp(line)
        if ts is None:
            continue
        if ts < start_ts or ts >= end_ts:
            continue

        # Parse all step items from this line
        line_steps: dict[int, dict] = {}
        segments = line.split("|")
        for seg in segments:
            parsed = _parse_step_from_segment(seg)
            if parsed is None:
                continue
            num = parsed["num"]
            # Keep longest name for each step number within this line
            if num not in line_steps or len(parsed["name"]) > len(line_steps[num]["name"]):
                line_steps[num] = {
                    "name": parsed["name"],
                    "side": parsed["side"],
                    "timestamp": ts,
                }

        if len(line_steps) > best_count:
            best_count = len(line_steps)
            best_steps = line_steps

    # Also do a second pass: accumulate across all lines in the section,
    # keeping the longest name per step number. This handles cases where the
    # step list is split across two screen regions (e.g., steps 1-5 on one
    # screen, then 6-10 on the next, never all on one line together).
    accumulated: dict[int, dict] = {}
    for line in lines:
        ts = parse_timestamp(line)
        if ts is None:
            continue
        if ts < start_ts or ts >= end_ts:
            continue

        segments = line.split("|")
        for seg in segments:
            parsed = _parse_step_from_segment(seg)
            if parsed is None:
                continue
            num = parsed["num"]
            if num not in accumulated or len(parsed["name"]) > len(accumulated[num]["name"]):
                accumulated[num] = {
                    "name": parsed["name"],
                    "side": parsed["side"],
                    "timestamp": ts,
                }

    # Use accumulated if it found more steps than the best single line
    if len(accumulated) > len(best_steps):
        best_steps = accumulated

    result = []
    for num in sorted(best_steps):
        result.append(best_steps[num])
    return result


def extract_sequence_steps(lines: list[str]) -> list[dict]:
    """Extract numbered sequence steps from all EXPLANATION OF PART sections.

    These lines show the full form sequence with side indicators:
        1. OREUN BATANGSON (MOMTONG)ANMAKGI
        2. OREUN APCHAGI + OEN (MOMTONG)ANMAKGI

    Strategy:
    1. Detect EXPLANATION OF PART section boundaries by timestamp.
    2. For each section, find the line with the most step items (the final
       build-up frame has the complete list for that part).
    3. Concatenate parts, renumbering sequentially across all parts.
    """
    sections = _find_explanation_sections(lines)

    if not sections:
        # Fallback: no EXPLANATION sections found, try old approach
        # with all lines after first EXPLANATION mention
        return _extract_steps_for_section(lines, 0, 999999)

    all_steps = []
    for start_ts, end_ts in sections:
        part_steps = _extract_steps_for_section(lines, start_ts, end_ts)
        all_steps.extend(part_steps)

    # Renumber sequentially across all parts
    result = []
    for i, step in enumerate(all_steps, 1):
        result.append({
            "number": str(i),
            "name": step["name"],
            "side": step["side"],
            "timestamp": step["timestamp"],
        })
    return result


def extract_tips(lines: list[str]) -> list[dict]:
    """Extract instructional tips from the transcript.

    Tips are English sentences with instructional content (>30 chars).
    Deduplication uses normalized lowercase prefix matching since OCR
    produces slight variations of the same tip across frames.
    """
    # Patterns that indicate instructional content
    tip_patterns = re.compile(
        r"(?:the\s+(?:blocking|assisting|thrusting)\s+(?:hand|arm|fist|elbow|wrist))"
        r"|(?:[Bb]e\s+careful)"
        r"|(?:[Ss]hould\s+(?:be|not|align|point|cross|touch))"
        r"|(?:[Ss]traighten)"
        r"|(?:[Pp]lace\s+the)"
        r"|(?:[Bb]lock\s+by)"
        r"|(?:[Ss]trike\s+a\s+target)"
        r"|(?:[Ww]hen\s+initiating)"
        r"|(?:[Bb]oth\s+elbows)"
        r"|(?:[Ff]or\s+(?:Oen|Oreun))"
        r"|(?:cross\s+your\s+(?:right|left)\s+arm)"
        r"|(?:[Yy]our\s+(?:fist|elbow)\s+should)"
        r"|(?:not\s+to\s+(?:kick|let))"
        r"|(?:the\s+(?:back|palm|wrist|space|arm)\s+of)"
        r"|(?:starts?\s+with\s+(?:the|your))",
        re.IGNORECASE,
    )

    raw_tips = []  # (timestamp, text)

    for line in lines:
        ts = parse_timestamp(line)
        if ts is None:
            continue

        segments = line.split("|")
        for seg in segments:
            seg = seg.strip()
            # Remove leading OCR checkmark indicators
            cleaned = re.sub(r"^[WYMw]\s+", "", seg)

            if len(cleaned) < 30:
                continue
            if not tip_patterns.search(cleaned):
                continue

            # Skip if mostly non-alpha
            alpha_ratio = sum(c.isalpha() or c.isspace() for c in cleaned) / max(len(cleaned), 1)
            if alpha_ratio < 0.7:
                continue

            text = re.sub(r"\s+", " ", cleaned).strip()
            raw_tips.append((ts, text))

    # Dedup: normalize text (strip OCR leader noise, lowercase) and group by
    # a content-based key. OCR produces many near-duplicates across frames.
    def normalize_for_dedup(text: str) -> str:
        """Strip OCR noise and normalize for dedup comparison."""
        # Remove leading timestamps, OCR markers, noise chars
        t = re.sub(r"^\[\d+s\]\s*", "", text)
        t = re.sub(r"^[WYMw/\s\*\"]+", "", t)
        t = re.sub(r"^[^a-zA-Z]+", "", t)
        # Keep only alpha and spaces
        t = re.sub(r"[^a-zA-Z\s]", "", t)
        # Lowercase, collapse whitespace
        t = re.sub(r"\s+", " ", t.lower().strip())
        # Take first 35 chars as the dedup key
        return t[:35]

    seen = {}  # dedup_key -> (timestamp, text)
    for ts, text in raw_tips:
        key = normalize_for_dedup(text)
        if len(key) < 15:
            continue
        if key in seen:
            prev_ts, prev_text = seen[key]
            seen[key] = (min(prev_ts, ts), text if len(text) > len(prev_text) else prev_text)
        else:
            seen[key] = (ts, text)

    result = []
    for key in sorted(seen, key=lambda k: seen[k][0]):
        ts, text = seen[key]
        # Final cleanup: remove leading OCR artifacts from the stored text
        text = re.sub(r"^\[\d+s\]\s*", "", text)
        text = re.sub(r"^[WYMw]\s+", "", text)
        text = re.sub(r"^[^a-zA-Z]+", "", text).strip()
        if len(text) >= 20:
            result.append({"text": text, "timestamp": ts})
    return result


def extract_sections(lines: list[str], slug: str) -> dict:
    """Extract section timestamps: poomsae, key_moves, explanation, repeat."""
    sections = {
        "poomsae": None,
        "key_moves": None,
        "explanation": None,
        "repeat": None,
    }

    explanation_found = False

    for line in lines:
        ts = parse_timestamp(line)
        if ts is None:
            continue

        # POOMSAE section
        if sections["poomsae"] is None and "POOMSAE" in line:
            sections["poomsae"] = ts

        # KEY MOVES: first summary list
        if sections["key_moves"] is None:
            numbered_count = len(re.findall(r"\d{2}[.,]\s+[A-Z]", line))
            if numbered_count >= 3:
                sections["key_moves"] = ts

        # EXPLANATION OF PART
        if sections["explanation"] is None and "EXPLANATION" in line:
            sections["explanation"] = ts
            explanation_found = True

        # REPEAT section (must come after explanation)
        if sections["repeat"] is None and "REPEAT" in line and explanation_found:
            sections["repeat"] = ts

    return {k: v for k, v in sections.items() if v is not None}


def load_caption_tips(slug: str) -> list[dict]:
    """Load instructional tips from parsed auto-captions.

    Reads dat/captions/{slug}.json if it exists, and returns caption entries
    as tip dicts with 'text' and 'timestamp' keys.

    Args:
        slug: Form slug like 'taegeuk-1jang'.

    Returns:
        List of tip dicts from captions, or empty list if no captions file.
    """
    caption_path = CAPTIONS_DIR / f"{slug}.json"
    if not caption_path.exists():
        return []

    with open(caption_path) as f:
        data = json.load(f)

    tips = []
    for cap in data.get("captions", []):
        text = cap.get("text", "").strip()
        # Only keep substantive caption lines (instructional content)
        if len(text) < 20:
            continue
        # Skip music/noise markers
        if re.match(r"^\[.*\]$", text):
            continue
        tips.append({
            "text": text,
            "timestamp": int(cap.get("start", 0)),
            "source": "caption",
        })
    return tips


def merge_tips(ocr_tips: list[dict], caption_tips: list[dict]) -> list[dict]:
    """Merge OCR tips with caption tips, deduplicating by text similarity.

    Caption tips supplement OCR tips. Dedup uses normalized prefix matching
    (first 35 chars, lowercased, alpha-only) — same approach as OCR dedup.

    Args:
        ocr_tips: Tips extracted from OCR transcripts.
        caption_tips: Tips extracted from auto-captions.

    Returns:
        Merged, deduplicated list of tips sorted by timestamp.
    """
    def normalize_key(text: str) -> str:
        t = re.sub(r"[^a-zA-Z\s]", "", text)
        t = re.sub(r"\s+", " ", t.lower().strip())
        return t[:35]

    # Index OCR tips by normalized key
    seen_keys: set[str] = set()
    for tip in ocr_tips:
        key = normalize_key(tip["text"])
        if len(key) >= 10:
            seen_keys.add(key)

    def words_overlap(a: str, b: str) -> float:
        """Fraction of shared words between two texts."""
        wa = set(a.lower().split())
        wb = set(b.lower().split())
        if not wa or not wb:
            return 0.0
        return len(wa & wb) / min(len(wa), len(wb))

    # Add caption tips that don't duplicate OCR tips
    merged = list(ocr_tips)
    added = 0
    for tip in caption_tips:
        key = normalize_key(tip["text"])
        if len(key) < 10:
            continue
        if key not in seen_keys:
            seen_keys.add(key)
            merged.append(tip)
            added += 1

    if added > 0:
        print(f"    +{added} caption tips (after dedup)")

    # Sort by timestamp
    merged.sort(key=lambda t: t.get("timestamp", 0))

    # Second pass: remove near-timestamp duplicates with high word overlap
    deduped = []
    for tip in merged:
        is_dup = False
        for existing in deduped:
            ts_diff = abs(tip.get("timestamp", 0) - existing.get("timestamp", 0))
            if ts_diff <= 3 and words_overlap(tip["text"], existing["text"]) > 0.5:
                is_dup = True
                # Keep the longer version
                if len(tip["text"]) > len(existing["text"]):
                    existing["text"] = tip["text"]
                break
        if not is_dup:
            deduped.append(tip)

    if len(merged) > len(deduped):
        print(f"    Deduped {len(merged) - len(deduped)} near-timestamp duplicates")

    return deduped


def pre_extract(slug: str) -> dict | None:
    """Run deterministic pre-extraction for a single form.

    Returns the extracted data dict, or None on error.
    """
    transcript_path = TRANSCRIPTS_DIR / f"{slug}.txt"
    if not transcript_path.exists():
        print(f"ERROR: No transcript at {transcript_path}")
        return None

    lines = transcript_path.read_text().splitlines()

    key_moves = extract_key_moves(lines)
    sequence_steps = extract_sequence_steps(lines)
    tips = extract_tips(lines)
    sections = extract_sections(lines, slug)

    # Merge caption tips if available
    caption_tips = load_caption_tips(slug)
    if caption_tips:
        tips = merge_tips(tips, caption_tips)

    result = {
        "form_slug": slug,
        "key_moves": key_moves,
        "sequence_steps": sequence_steps,
        "tips": tips,
        "sections": sections,
    }

    PRE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PRE_DIR / f"{slug}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  {slug}: {len(key_moves)} key moves, {len(sequence_steps)} steps, {len(tips)} tips")
    print(f"  Wrote {out_path}")
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 pre_extract.py <slug>    Pre-extract one form")
        print("  python3 pre_extract.py --all     Pre-extract all forms")
        print(f"\nSlugs: {', '.join(sorted(FORM_META.keys()))}")
        sys.exit(1)

    if "--all" in sys.argv:
        for slug in sorted(FORM_META.keys()):
            print(f"\n{'=' * 50}\n{slug}\n{'=' * 50}")
            pre_extract(slug)
    else:
        slug = [a for a in sys.argv[1:] if not a.startswith("--")][0]
        pre_extract(slug)


if __name__ == "__main__":
    main()
