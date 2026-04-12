#!/usr/bin/env python3
"""
Extract structured poomsae data from pre-extracted JSON.

Mostly programmatic pipeline: matches techniques from dat/techniques.json,
assigns tips by timestamp proximity, builds sequence from pre-extracted steps.
Kihap positions are static lookups from KKW standard. Uses LLM only for
directions and translating new techniques.

Requires pre_extract.py to run first (extracts key_moves, sequence_steps,
tips from raw OCR transcript). This script never reads the transcript directly.

Usage:
    python3 extract.py taegeuk-1jang       # Extract one form
    python3 extract.py --all               # Extract all forms
    python3 extract.py --prompt-only koryo  # Print LLM prompt without calling
    python3 extract.py --no-llm koryo      # Skip LLM (placeholder directions)
    python3 extract.py --validate          # Validate all existing JSONs
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

DAT_DIR = Path(__file__).parent.parent / "dat"
FORMS_DIR = DAT_DIR / "forms"
PRE_DIR = DAT_DIR / "pre"
TECHNIQUES_PATH = DAT_DIR / "techniques.json"

FORM_META = {
    "taegeuk-1jang": {"id": "taegeuk-1", "name_en": "Taegeuk Il Jang", "name_ko": "태극 1장", "meaning": "Heaven (Keon ☰)", "belt": "8th Geup", "dan": None, "video_id": "WhkjRruCBTo", "duration": 970, "expected_moves": 18},
    "taegeuk-2jang": {"id": "taegeuk-2", "name_en": "Taegeuk I Jang", "name_ko": "태극 2장", "meaning": "Lake (Tae ☱)", "belt": "7th Geup", "dan": None, "video_id": "tGlrUplKHh8", "duration": 556, "expected_moves": 18},
    "taegeuk-3jang": {"id": "taegeuk-3", "name_en": "Taegeuk Sam Jang", "name_ko": "태극 3장", "meaning": "Fire (Ri ☲)", "belt": "6th Geup", "dan": None, "video_id": "ksSqKt0UkWo", "duration": 836, "expected_moves": 20},
    "taegeuk-4jang": {"id": "taegeuk-4", "name_en": "Taegeuk Sa Jang", "name_ko": "태극 4장", "meaning": "Thunder (Jin ☳)", "belt": "5th Geup", "dan": None, "video_id": "Lt917gacJho", "duration": 810, "expected_moves": 20},
    "taegeuk-5jang": {"id": "taegeuk-5", "name_en": "Taegeuk Oh Jang", "name_ko": "태극 5장", "meaning": "Wind (Son ☴)", "belt": "4th Geup", "dan": None, "video_id": "VdqNEAHWCBM", "duration": 811, "expected_moves": 20},
    "taegeuk-6jang": {"id": "taegeuk-6", "name_en": "Taegeuk Yuk Jang", "name_ko": "태극 6장", "meaning": "Water (Gam ☵)", "belt": "3rd Geup", "dan": None, "video_id": "jcBwWo4wN7c", "duration": 835, "expected_moves": 23},
    "taegeuk-7jang": {"id": "taegeuk-7", "name_en": "Taegeuk Chil Jang", "name_ko": "태극 7장", "meaning": "Mountain (Gan ☶)", "belt": "2nd Geup", "dan": None, "video_id": "6FUM1p6qqhQ", "duration": 1362, "expected_moves": 25},
    "taegeuk-8jang": {"id": "taegeuk-8", "name_en": "Taegeuk Pal Jang", "name_ko": "태극 8장", "meaning": "Earth (Gon ☷)", "belt": "1st Geup", "dan": None, "video_id": "Gr_Je2ZkgkI", "duration": 1025, "expected_moves": 24},
    "koryo": {"id": "koryo", "name_en": "Koryo", "name_ko": "고려", "meaning": "Koryo dynasty spirit", "belt": None, "dan": 1, "video_id": "mGa60JDtWmg", "duration": 1325, "expected_moves": 30},
    "keumgang": {"id": "keumgang", "name_en": "Keumgang", "name_ko": "금강", "meaning": "Diamond / unbreakable", "belt": None, "dan": 2, "video_id": "CRGVSOmaQaY", "duration": 1179, "expected_moves": 27},
    "taebaek": {"id": "taebaek", "name_en": "Taebaek", "name_ko": "태백", "meaning": "Sacred mountain / light", "belt": None, "dan": 3, "video_id": "Q4dYdFRbE4U", "duration": 899, "expected_moves": 26},
    "pyeongwon": {"id": "pyeongwon", "name_en": "Pyeongwon", "name_ko": "평원", "meaning": "Vast plain", "belt": None, "dan": 4, "video_id": "RB-7mBtvtZw", "duration": 1505, "expected_moves": 25},
    "sipjin": {"id": "sipjin", "name_en": "Sipjin", "name_ko": "십진", "meaning": "Decimal / 10 symbols of longevity", "belt": None, "dan": 5, "video_id": "hOZB0IESJ38", "duration": 1786, "expected_moves": 28},
    "jitae": {"id": "jitae", "name_en": "Jitae", "name_ko": "지태", "meaning": "Earth / all living things", "belt": None, "dan": 6, "video_id": "nur2WsN7dQw", "duration": 1106, "expected_moves": 28},
    "chonkwon": {"id": "chonkwon", "name_en": "Cheonkwon", "name_ko": "천권", "meaning": "Sky / heaven", "belt": None, "dan": 7, "video_id": "FBxCzK5c4bE", "duration": 1343, "expected_moves": 33},
    "hansu": {"id": "hansu", "name_en": "Hansu", "name_ko": "한수", "meaning": "Water / fluidity", "belt": None, "dan": 8, "video_id": "lRp1JE7f-a8", "duration": 966, "expected_moves": 27},
    "ilyeo": {"id": "ilyeo", "name_en": "Ilyeo", "name_ko": "일여", "meaning": "Oneness / unity of mind and body", "belt": None, "dan": 9, "video_id": "jWClKVOrqJ8", "duration": 1020, "expected_moves": 24},
}

# Kihap (yell) positions per form from KKW standard.
# -1 means last step in the sequence (excluding step 0 junbi).
KIHAP_POSITIONS: dict[str, list[int]] = {
    "taegeuk-1": [-1],
    "taegeuk-2": [-1],
    "taegeuk-3": [-1],
    "taegeuk-4": [-1],
    "taegeuk-5": [-1],
    "taegeuk-6": [-1],
    "taegeuk-7": [-1],
    "taegeuk-8": [-1],
    "koryo": [22, -1],
    "keumgang": [-1],
    "taebaek": [-1],
    "pyeongwon": [-1],
    "sipjin": [11, -1],
    "jitae": [-1],
    "chonkwon": [9, 25, -1],
    "hansu": [16, -1],
    "ilyeo": [17, -1],
}


# --- Normalization / matching (shared logic with build_techniques.py) ---

def normalize_romanized(name: str) -> str:
    """Normalize romanized name: lowercase, strip non-alpha, collapse spaces.

    Strips parenthetical alternatives like (NAERYEO), (MOMTONG).
    """
    s = name.upper()
    # Remove parenthetical alternatives: ARAE(NAERYEO) -> ARAE
    s = re.sub(r"\([^)]*\)", "", s)
    # Remove trailing noise from OCR: trailing parens, symbols
    s = re.sub(r"[^A-Za-z\s+]", "", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


# Side indicators to strip from combo parts before matching
_SIDE_INDICATORS = {"oen", "oreun"}


def _strip_side_indicators(name: str) -> str:
    """Strip side indicators (OEN, OREUN) from a technique name."""
    words = name.split()
    return " ".join(w for w in words if w.lower() not in _SIDE_INDICATORS)


def _romanized_to_title(name: str) -> str:
    """Convert a normalized romanized name to title case for display.

    Capitalizes each word. Used as fallback for English and Korean names
    when a technique is unmatched.
    """
    return " ".join(w.capitalize() for w in name.split())


def _normalize_for_match(name: str) -> str:
    """Normalize for matching: lowercase, no spaces/hyphens."""
    return re.sub(r"[\s\-]+", "", normalize_romanized(name))


def categorize_by_suffix(romanized: str) -> str:
    """Categorize a technique by its romanized name suffix."""
    rom = romanized.lower().replace(" ", "")
    if rom.endswith("makgi") or rom.endswith("makki"):
        return "block"
    if rom.endswith("chagi"):
        return "kick"
    if rom.endswith("jireugi") or rom.endswith("chigi") or rom.endswith("jireuki"):
        return "strike"
    if rom.endswith("seogi") or rom.endswith("jase"):
        return "stance"
    return "strike"  # default


def _slugify(name: str) -> str:
    """Convert a name to URL-safe slug.

    Strips '+' signs — combo keys should be built explicitly from
    matched parts, not from slugifying raw combo names.
    """
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s\-]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def match_technique(name: str, tech_db: dict) -> dict | None:
    """Match a romanized technique name against techniques.json.

    Returns the matching technique entry or None.
    Tries: exact normalized match, then with side indicators stripped,
    then fuzzy substring match.
    """
    norm = _normalize_for_match(name)
    if not norm:
        return None

    # Also try with side indicators stripped
    stripped = _strip_side_indicators(normalize_romanized(name))
    norm_stripped = re.sub(r"[\s\-]+", "", stripped) if stripped != normalize_romanized(name) else None

    # Exact match on normalized romanized
    for tech in tech_db.values():
        if not tech.get("key"):
            continue  # Skip entries with empty key
        tech_norm = _normalize_for_match(tech["name"]["romanized"])
        if tech_norm == norm:
            return tech
        if norm_stripped and tech_norm == norm_stripped:
            return tech

    # Fuzzy: substring containment (bidirectional)
    best = None
    best_score = 0
    for tech in tech_db.values():
        if not tech.get("key"):
            continue  # Skip entries with empty key
        tech_norm = _normalize_for_match(tech["name"]["romanized"])
        if not tech_norm:
            continue
        # Try both original and side-stripped
        for candidate in ([norm, norm_stripped] if norm_stripped else [norm]):
            if candidate in tech_norm or tech_norm in candidate:
                score = min(len(candidate), len(tech_norm)) / max(len(candidate), len(tech_norm))
                if score > best_score:
                    best_score = score
                    best = tech
    if best and best_score > 0.5:
        return best
    return None


def match_combo_technique(name: str, tech_db: dict) -> list[dict] | None:
    """Match a combo technique name (contains '+') against techniques.json.

    Strips parenthetical annotations and side indicators (OEN, OREUN) from
    each part before matching. Returns list of matched technique entries,
    or None if any part fails to match.
    """
    parts = re.split(r"\s*\+\s*", name)
    if len(parts) < 2:
        return None
    matched = []
    for part in parts:
        part = part.strip()
        m = match_technique(part, tech_db)
        if not m:
            # Strip side indicators and retry
            stripped = _strip_side_indicators(normalize_romanized(part))
            if stripped != normalize_romanized(part):
                m = match_technique(stripped, tech_db)
        if m:
            matched.append(m)
        else:
            return None
    return matched


# --- Tip matching ---

def match_tips_to_techniques(tips: list[dict], techniques: list[dict]) -> dict[str, list[dict]]:
    """Match tips to techniques by video segment containment.

    A tip is assigned to a technique if:
        technique.video_timestamp <= tip.timestamp < technique.video_timestamp_end

    Tips that don't fall within any technique's segment are dropped.
    Max 5 tips per technique.

    Returns: {technique_key: [tip, ...]}
    """
    # Build segments: (start, end, key)
    segments = []
    for t in techniques:
        start = t.get("video_timestamp", 0)
        end = t.get("video_timestamp_end", 0)
        if start > 0 and end > start:
            segments.append((start, end, t["key"]))
    # Sort by start timestamp
    segments.sort()

    if not segments:
        return {}

    result: dict[str, list[dict]] = {}
    for tip in tips:
        ts = tip.get("timestamp", 0)
        if ts <= 0:
            continue
        # Find the segment containing this tip's timestamp
        for seg_start, seg_end, seg_key in segments:
            if seg_start <= ts < seg_end:
                if seg_key not in result:
                    result[seg_key] = []
                if len(result[seg_key]) < 5:
                    result[seg_key].append(tip)
                break
    return result


# --- Sections builder ---

def build_sections(pre_data: dict, meta: dict) -> dict:
    """Build sections from pre-extracted section timestamps."""
    raw = pre_data.get("sections", {})
    duration = meta["duration"]

    # Pre-extraction sections have: key_moves, explanation, repeat (timestamps)
    km_ts = raw.get("key_moves", 0)
    exp_ts = raw.get("explanation", 0)
    rep_ts = raw.get("repeat", 0)

    sections = {}
    if km_ts > 0:
        sections["intro"] = {"start": 0, "end": km_ts}
        sections["breakdown"] = {"start": km_ts, "end": exp_ts if exp_ts > 0 else rep_ts if rep_ts > 0 else duration}
    if exp_ts > 0:
        sections["explanation"] = {"start": exp_ts, "end": rep_ts if rep_ts > 0 else duration}
    if rep_ts > 0:
        sections["repeat"] = {"start": rep_ts, "end": duration}
    return sections


# --- Kihap inference ---

def apply_kihap(sequence: list[dict], form_id: str, tips: list[dict]) -> int:
    """Apply kihap markers to sequence steps.

    Uses static KIHAP_POSITIONS lookup, then scans tips for "kihap"/"yell"
    mentions and marks the nearest step by timestamp.

    Args:
        sequence: List of sequence step dicts (mutated in place).
        form_id: Form identifier (e.g. "taegeuk-1", "koryo").
        tips: Pre-extracted tips list.

    Returns:
        Number of steps marked with kihap.
    """
    if not sequence:
        return 0

    # Static lookup
    positions = KIHAP_POSITIONS.get(form_id, [])
    max_step = max(s["step"] for s in sequence)
    step_set: set[int] = set()
    for pos in positions:
        if pos == -1:
            step_set.add(max_step)
        else:
            step_set.add(pos)

    # Transcript evidence: scan tips for kihap/yell keywords
    kihap_timestamps: list[int] = []
    for tip in tips:
        text = tip.get("text", "").lower()
        if "kihap" in text or "yell" in text or "shout" in text:
            ts = tip.get("timestamp", 0)
            if ts > 0:
                kihap_timestamps.append(ts)

    # For each kihap timestamp, find the nearest sequence step (within 30s)
    max_tip_dist = 30
    for ts in kihap_timestamps:
        best_step = None
        best_dist = float("inf")
        for s in sequence:
            s_ts = s.get("timestamp", 0)
            if s_ts <= 0:
                continue
            dist = abs(s_ts - ts)
            if dist < best_dist:
                best_dist = dist
                best_step = s["step"]
        if best_step is not None and best_dist <= max_tip_dist:
            step_set.add(best_step)

    # Apply to sequence
    count = 0
    for s in sequence:
        if s["step"] in step_set:
            s["kihap"] = True
            count += 1
    return count


# --- LLM prompt for directions + new translations ---

def build_translation_prompt(new_techniques: list[dict]) -> str:
    """Build a compact LLM prompt to translate unmatched technique names.

    Given romanized OCR text (possibly with typos), asks for:
    - Corrected romanized name
    - English translation
    - Korean hangul
    - Category (block/kick/strike/stance)
    """
    lines = [
        "Translate these taekwondo technique names from romanized Korean to "
        "English and Korean hangul. The romanized names come from OCR and may "
        "contain typos (e.g. BARRANMAKGI should be BAKKANMAKGI, "
        "JEOCHEQOJIREUGI should be JEOCHEOJIREUGI). Fix OCR errors.",
        "",
    ]
    for i, t in enumerate(new_techniques, 1):
        lines.append(f"{i}. {t['name']['romanized']}")
    lines.append("")
    lines.append("Output JSON array only:")
    lines.append('[{"romanized": "corrected romanized", "en": "English Name", '
                  '"ko": "한글이름", "category": "block|kick|strike|stance"}, ...]')
    return "\n".join(lines)


def build_llm_prompt(
    meta: dict,
    sequence_steps: list[dict],
) -> str:
    """Build a compact LLM prompt for directions only.

    Kihap is handled programmatically via KIHAP_POSITIONS, so the LLM
    only needs to provide direction for each step.
    """
    form_name = meta["name_en"]
    expected = meta["expected_moves"]

    lines = [f"Form: {form_name} ({expected} moves)\n"]

    lines.append("Sequence (provide direction for each step):")
    for s in sequence_steps:
        side_str = f" ({s.get('side', '')})" if s.get("side") else ""
        lines.append(f"{s['step']}. {s['technique_romanized']}{side_str} @{s.get('timestamp', 0)}s")

    lines.append("")
    lines.append("For each step: direction (forward/backward/left-90/right-90/left-180/right-180).")
    lines.append("")
    lines.append('Output JSON only:')
    lines.append('{"directions": [{"step": 0, "direction": "forward"}, ...]}')

    return "\n".join(lines)


def _parse_llm_json(output: str) -> dict | None:
    """Parse JSON from LLM output, stripping markdown fences and preamble."""
    output = output.strip()
    # Strip markdown fences
    if "```json" in output:
        output = output.split("```json", 1)[1]
    elif "```" in output:
        output = output.split("```", 1)[1]
    if output.endswith("```"):
        output = output.rsplit("```", 1)[0]
    # Strip any text before first { or [
    for i, c in enumerate(output):
        if c in '{[':
            output = output[i:]
            break
    output = output.strip()
    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        print(f"  ERROR: Invalid JSON: {e}")
        print(f"  Output (first 500 chars): {output[:500]}")
        return None


def _call_claude(prompt: str, label: str) -> dict | None:
    """Call claude CLI with a prompt and parse JSON output."""
    print(f"  [{label}] Calling claude CLI...")
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "text"],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        print(f"  [{label}] ERROR: claude CLI failed: {result.stderr[:200]}")
        return None
    data = _parse_llm_json(result.stdout)
    if data is None:
        print(f"  [{label}] Failed to parse JSON output")
    return data


# --- Validation (unchanged) ---

def validate_form(path: str, warnings: list[str] | None = None) -> list[str]:
    """Validate a form JSON. Returns list of errors.

    If `warnings` list is provided, appends non-blocking warnings (e.g.
    possible hallucinations) to it instead of to errors.
    """
    errors = []
    try:
        with open(path) as f:
            d = json.load(f)
    except Exception as e:
        return [f"Invalid JSON: {e}"]

    # Required top-level fields
    for field in ['id', 'name', 'total_moves', 'video_id', 'techniques', 'sequence']:
        if field not in d:
            errors.append(f"Missing field: {field}")

    if 'techniques' not in d or 'sequence' not in d:
        return errors

    # Check all techniques have required fields
    tech_keys = set()
    for i, t in enumerate(d['techniques']):
        for field in ['key', 'name', 'category']:
            if field not in t:
                errors.append(f"Technique {i}: missing {field}")
        if 'key' in t:
            tech_keys.add(t['key'])
        if 'name' in t:
            for nf in ['en', 'ko', 'romanized']:
                if nf not in t['name']:
                    errors.append(f"Technique {t.get('key','?')}: missing name.{nf}")
            # Check no romanized in English name
            if 'en' in t['name'] and '(' in t['name']['en']:
                errors.append(f"Technique {t.get('key','?')}: name.en contains parentheses (romanized leak?): {t['name']['en']}")

    # Check for deprecated categories
    for i, t in enumerate(d['techniques']):
        cat = t.get('category', '')
        if cat == 'ready':
            errors.append(f"Technique {t.get('key','?')}: category 'ready' should be 'stance'")
        if cat == 'technique':
            errors.append(f"Technique {t.get('key','?')}: category 'technique' is invalid (use strike/block/stance)")

    # Check all sequence references resolve
    for s in d['sequence']:
        if s['technique'] not in tech_keys:
            errors.append(f"Step {s.get('step','?')}: technique '{s['technique']}' not in techniques array")

    # Check sequence is ordered by step
    steps = [s['step'] for s in d['sequence']]
    if steps != sorted(steps):
        errors.append("Sequence steps not in order")

    # Cross-check techniques against pre-extraction data
    form_id = d.get('id', '')
    slug_for_pre = None
    for slug_candidate, meta in FORM_META.items():
        if meta['id'] == form_id:
            slug_for_pre = slug_candidate
            break
    if slug_for_pre:
        pre_path = PRE_DIR / f"{slug_for_pre}.json"
        if pre_path.exists():
            with open(pre_path) as f:
                pre_data = json.load(f)
            pre_names = _collect_pre_names(pre_data)
            for t in d['techniques']:
                rom = t.get('name', {}).get('romanized', '')
                if rom and not _matches_pre_names(rom, pre_names):
                    msg = (
                        f"WARNING: Technique '{rom}' not found in "
                        f"transcript -- possible hallucination"
                    )
                    if warnings is not None:
                        warnings.append(msg)
                    else:
                        errors.append(msg)

    return errors


# --- Pre-extraction cross-check helpers ---

_STANDARD_TECHNIQUES = {
    "momtong jireugi", "arae makgi", "ap chagi", "olgul jireugi",
    "junbi", "junbijase", "gibon junbijase",
}


def _normalize_pre_name(name: str) -> str:
    """Normalize a pre-extracted name for fuzzy comparison."""
    s = re.sub(r"[^a-z\s]", "", name.lower())
    return re.sub(r"\s+", " ", s).strip()


def _collect_pre_names(pre_data: dict) -> set[str]:
    """Collect all normalized technique names from pre-extraction data."""
    names: set[str] = set()
    for m in pre_data.get("key_moves", []):
        names.add(_normalize_pre_name(m["name"]))
    for s in pre_data.get("sequence_steps", []):
        names.add(_normalize_pre_name(s["name"]))
    return names


def _matches_pre_names(romanized: str, pre_names: set[str]) -> bool:
    """Check if a romanized technique name matches any pre-extracted name."""
    norm = _normalize_pre_name(romanized)
    if not norm:
        return True
    if norm in _STANDARD_TECHNIQUES:
        return True
    parts = norm.split("+") if "+" in romanized else [norm]
    for part in parts:
        part = part.strip()
        if part in _STANDARD_TECHNIQUES:
            continue
        matched = False
        for pre in pre_names:
            if not pre:
                continue
            if part in pre or pre in part:
                matched = True
                break
        if not matched:
            return False
    return True


# --- Main extraction pipeline ---

def extract_form(slug: str, prompt_only: bool = False, no_llm: bool = False):
    meta = FORM_META.get(slug)
    if not meta:
        print(f"ERROR: No metadata for {slug}")
        return False

    # --- Step 1: Load pre-extraction + existing techniques ---
    pre_path = PRE_DIR / f"{slug}.json"
    if not pre_path.exists():
        print(f"ERROR: No pre-extraction at {pre_path}")
        print(f"  Run pre_extract.py first: python3 scripts/pre_extract.py {slug}")
        return False

    with open(pre_path) as f:
        pre_data = json.load(f)

    tech_db = {}
    if TECHNIQUES_PATH.exists():
        with open(TECHNIQUES_PATH) as f:
            tech_db = json.load(f)

    key_moves = pre_data.get("key_moves", [])
    sequence_steps = pre_data.get("sequence_steps", [])
    tips = pre_data.get("tips", [])
    print(f"  Loaded pre-extraction: {len(key_moves)} key moves, "
          f"{len(sequence_steps)} steps, {len(tips)} tips")
    print(f"  Loaded {len(tech_db)} techniques from techniques.json")

    # --- Step 2: Match key_moves to techniques.json ---
    matched_techniques: dict[str, dict] = {}  # key -> technique entry
    new_techniques: list[dict] = []  # unmatched, need LLM translation

    for move in key_moves:
        raw_name = move["name"]
        norm_name = normalize_romanized(raw_name)
        ts = move.get("timestamp", 0)

        # Handle combos
        if "+" in raw_name:
            combo_parts = match_combo_technique(raw_name, tech_db)
            if combo_parts:
                combo_key = "+".join(p["key"] for p in combo_parts)
                combo_en = " + ".join(p["name"]["en"] for p in combo_parts)
                combo_ko = " + ".join(p["name"]["ko"] for p in combo_parts)
                combo_rom = " + ".join(p["name"]["romanized"] for p in combo_parts)
                matched_techniques[combo_key] = {
                    "key": combo_key,
                    "name": {"en": combo_en, "ko": combo_ko, "romanized": combo_rom},
                    "category": "combination",
                    "video_timestamp": ts,
                    "video_timestamp_end": 0,
                    "tips": [],
                }
                continue

        match = match_technique(raw_name, tech_db)
        if match:
            key = match["key"]
            if key not in matched_techniques:
                matched_techniques[key] = {
                    "key": key,
                    "name": dict(match["name"]),
                    "category": match["category"],
                    "video_timestamp": ts,
                    "video_timestamp_end": 0,
                    "tips": [],
                }
            elif ts > 0 and matched_techniques[key]["video_timestamp"] == 0:
                matched_techniques[key]["video_timestamp"] = ts
        else:
            # New technique: need LLM translation
            # Build a temporary entry with what we know
            category = categorize_by_suffix(norm_name)
            temp_key = _slugify(norm_name)
            # Title-case the romanized name
            rom_title = _romanized_to_title(norm_name)
            # Use romanized as fallback for en/ko until LLM provides translations
            new_techniques.append({
                "key": temp_key,
                "name": {"en": rom_title, "ko": rom_title, "romanized": rom_title},
                "category": category,
                "video_timestamp": ts,
                "video_timestamp_end": 0,
                "tips": [],
            })

    # Compute video_timestamp_end for each technique (next technique's timestamp)
    all_techs_ordered = sorted(
        list(matched_techniques.values()) + new_techniques,
        key=lambda t: t["video_timestamp"]
    )
    for i, tech in enumerate(all_techs_ordered):
        if i + 1 < len(all_techs_ordered):
            tech["video_timestamp_end"] = all_techs_ordered[i + 1]["video_timestamp"]
        else:
            # Last technique: end at explanation section start or duration
            sections_raw = pre_data.get("sections", {})
            tech["video_timestamp_end"] = sections_raw.get("explanation", meta["duration"])

    print(f"  Matched {len(matched_techniques)} techniques, {len(new_techniques)} new")

    # --- Step 3: Match tips to techniques by timestamp ---
    all_form_techniques = list(matched_techniques.values()) + new_techniques
    tip_map = match_tips_to_techniques(tips, all_form_techniques)
    for tech in all_form_techniques:
        tech["tips"] = tip_map.get(tech["key"], [])
    total_assigned = sum(len(v) for v in tip_map.values())
    print(f"  Assigned {total_assigned} tips to techniques")

    # --- Step 4: Build sequence from pre-extracted steps ---
    sequence = []
    for i, step in enumerate(sequence_steps):
        raw_name = step["name"]
        side = step.get("side")
        # Normalize side
        if side:
            side = side.lower()
            if side in ("oen", "left"):
                side = "left"
            elif side in ("oreun", "right"):
                side = "right"

        ts = step.get("timestamp", 0)
        ts_end = sequence_steps[i + 1]["timestamp"] if i + 1 < len(sequence_steps) else 0

        # Match technique
        tech_key = None
        matched_entry = None
        if "+" in raw_name:
            combo_parts = match_combo_technique(raw_name, tech_db)
            if combo_parts:
                tech_key = "+".join(p["key"] for p in combo_parts)
        if tech_key is None and "+" not in raw_name:
            matched_entry = match_technique(raw_name, tech_db)
            if matched_entry:
                tech_key = matched_entry["key"]
        if tech_key is None:
            # Try matching against new_techniques (strip side for comparison)
            norm = _normalize_for_match(raw_name)
            norm_stripped = _normalize_for_match(_strip_side_indicators(normalize_romanized(raw_name)))
            for nt in new_techniques:
                nt_norm = _normalize_for_match(nt["name"]["romanized"])
                if nt_norm == norm or nt_norm == norm_stripped:
                    tech_key = nt["key"]
                    break
        if tech_key is None:
            # Fallback for combos: try matching each part individually
            # with side indicators stripped
            if "+" in raw_name:
                parts = re.split(r"\s*\+\s*", raw_name)
                part_keys = []
                all_matched = True
                for part in parts:
                    part = part.strip()
                    stripped = _strip_side_indicators(normalize_romanized(part))
                    m = match_technique(stripped, tech_db) or match_technique(part, tech_db)
                    if m:
                        part_keys.append(m["key"])
                    else:
                        # Try new_techniques
                        pn = _normalize_for_match(stripped)
                        found = False
                        for nt in new_techniques:
                            if _normalize_for_match(nt["name"]["romanized"]) == pn:
                                part_keys.append(nt["key"])
                                found = True
                                break
                        if not found:
                            all_matched = False
                            break
                if all_matched and len(part_keys) >= 2:
                    tech_key = "+".join(part_keys)
            if tech_key is None:
                tech_key = _slugify(normalize_romanized(raw_name))
                print(f"  WARNING: Step {step['number']} unmatched: {raw_name} -> {tech_key}")

        # Ensure the technique exists in our technique list
        if tech_key not in matched_techniques:
            found_new = any(nt["key"] == tech_key for nt in new_techniques)
            if not found_new:
                if matched_entry and "+" not in tech_key:
                    # Technique matched from tech_db but wasn't in key_moves
                    matched_techniques[tech_key] = {
                        "key": tech_key,
                        "name": dict(matched_entry["name"]),
                        "category": matched_entry["category"],
                        "video_timestamp": 0,
                        "video_timestamp_end": 0,
                        "tips": [],
                    }
                elif "+" in tech_key:
                    # Combo: build from parts if we can find them
                    parts = tech_key.split("+")
                    combo_en = " + ".join(tech_db[p]["name"]["en"] if p in tech_db else p for p in parts)
                    combo_ko = " + ".join(tech_db[p]["name"]["ko"] if p in tech_db else "" for p in parts)
                    combo_rom = " + ".join(tech_db[p]["name"]["romanized"] if p in tech_db else p for p in parts)
                    matched_techniques[tech_key] = {
                        "key": tech_key,
                        "name": {"en": combo_en, "ko": combo_ko, "romanized": combo_rom},
                        "category": "combination",
                        "video_timestamp": 0,
                        "video_timestamp_end": 0,
                        "tips": [],
                    }
                else:
                    # Truly unmatched: add as new technique
                    norm_name = normalize_romanized(raw_name)
                    rom_title = _romanized_to_title(norm_name)
                    new_entry = {
                        "key": tech_key,
                        "name": {"en": rom_title, "ko": rom_title, "romanized": rom_title},
                        "category": categorize_by_suffix(norm_name),
                        "video_timestamp": 0,
                        "video_timestamp_end": 0,
                        "tips": [],
                    }
                    new_techniques.append(new_entry)

        step_num = int(step["number"]) if step["number"].isdigit() else i + 1
        seq_entry = {
            "step": step_num,
            "technique": tech_key,
            "side": side,
            "direction": "forward",  # placeholder, filled by LLM
            "kihap": False,  # placeholder, filled by LLM
            "timestamp": ts,
            "timestamp_end": ts_end,
        }
        sequence.append(seq_entry)

    # Build sequence step info for LLM prompt
    # Rebuild all_form_techniques since Step 4 may have added to matched_techniques
    all_form_techniques = list(matched_techniques.values()) + new_techniques
    llm_sequence_steps = []
    for s in sequence:
        # Find the romanized name for display
        rom = s["technique"]
        for tech in all_form_techniques:
            if tech["key"] == s["technique"]:
                rom = tech["name"]["romanized"]
                break
        llm_sequence_steps.append({
            "step": s["step"],
            "technique_romanized": rom,
            "side": s.get("side"),
            "timestamp": s.get("timestamp", 0),
        })

    print(f"  Built sequence: {len(sequence)} steps")

    # --- Step 5: Apply kihap markers (static lookup + transcript evidence) ---
    kihap_count = apply_kihap(sequence, meta["id"], tips)
    print(f"  Kihap: {kihap_count} steps marked")

    _new_key_renames_early: dict[str, str] = {}  # old_key -> new_key from LLM translations

    # --- Step 6a: LLM call for unmatched technique translations ---
    if new_techniques and not no_llm:
        translation_prompt = build_translation_prompt(new_techniques)
        if prompt_only:
            print("=== TRANSLATION PROMPT ===")
            print(translation_prompt)
            print()
        else:
            llm_translations = _call_claude(translation_prompt, "translations")
            if llm_translations:
                # LLM returns a JSON array
                if isinstance(llm_translations, dict):
                    llm_list = llm_translations.get("translations", [])
                else:
                    llm_list = llm_translations  # direct array

                # Match by position (prompt lists techniques in order).
                # Also try romanized key matching as fallback for reordered output.
                llm_by_rom: dict[str, dict] = {}
                for nt in llm_list:
                    rom_key = _normalize_for_match(nt.get("romanized", ""))
                    llm_by_rom[rom_key] = nt

                translated_count = 0
                for i, tech in enumerate(new_techniques):
                    # Try positional match first, then romanized key
                    translation = None
                    if i < len(llm_list):
                        translation = llm_list[i]
                    if not translation:
                        rom_key = _normalize_for_match(tech["name"]["romanized"])
                        translation = llm_by_rom.get(rom_key)
                    if translation:
                        tech["name"]["en"] = translation.get("en", tech["name"]["en"])
                        tech["name"]["ko"] = translation.get("ko", tech["name"]["ko"])
                        # Update romanized with corrected version from LLM
                        if translation.get("romanized"):
                            tech["name"]["romanized"] = translation["romanized"]
                        if translation.get("category"):
                            tech["category"] = translation["category"]
                        # Update key from English name
                        if tech["name"]["en"]:
                            old_key = tech["key"]
                            tech["key"] = _slugify(tech["name"]["en"])
                            if old_key != tech["key"]:
                                _new_key_renames_early[old_key] = tech["key"]
                        translated_count += 1
                print(f"  LLM translations: {translated_count}/{len(new_techniques)} techniques")
            else:
                print("  WARNING: Translation LLM call failed, using raw OCR names")
    elif new_techniques and no_llm:
        print(f"  WARNING: {len(new_techniques)} techniques have raw OCR names "
              f"(no hangul Korean, romanized English). Run without --no-llm to fix.")

    # --- Step 6b: LLM call for directions ---
    prompt = build_llm_prompt(meta, llm_sequence_steps)

    if prompt_only:
        print("=== DIRECTIONS PROMPT ===")
        print(prompt)
        return True

    if no_llm:
        print("  Skipping LLM call (--no-llm mode)")
    else:
        llm_result = _call_claude(prompt, "directions")
        if llm_result:
            directions = llm_result.get("directions", [])
            dir_by_step = {d["step"]: d for d in directions}
            for s in sequence:
                d = dir_by_step.get(s["step"])
                if d:
                    s["direction"] = d.get("direction", "forward")
            print(f"  LLM directions: {len(directions)} steps")
        else:
            print("  WARNING: Directions LLM call failed, using placeholder directions")

    # --- Step 7: Build sections ---
    sections = build_sections(pre_data, meta)

    # --- Step 8: Merge into final form JSON ---
    # Combine matched + new techniques, dedup by key
    final_techniques = []
    seen_keys: set[str] = set()
    for tech in list(matched_techniques.values()) + new_techniques:
        if tech["key"] not in seen_keys:
            seen_keys.add(tech["key"])
            final_techniques.append(tech)

    # Update sequence technique keys for any renamed new techniques
    # Merge early renames (from LLM translation) with romanized-based renames
    new_key_renames = dict(_new_key_renames_early)
    for tech in new_techniques:
        old_key = _slugify(normalize_romanized(tech["name"]["romanized"]))
        if old_key != tech["key"]:
            new_key_renames[old_key] = tech["key"]
    for s in sequence:
        if s["technique"] in new_key_renames:
            s["technique"] = new_key_renames[s["technique"]]

    total_moves = len(sequence)
    data = {
        "id": meta["id"],
        "name": {"en": meta["name_en"], "ko": meta["name_ko"]},
        "meaning": {"en": meta["meaning"]},
        "belt": meta["belt"],
        "dan": meta["dan"],
        "total_moves": total_moves,
        "video_id": meta["video_id"],
        "video_duration_seconds": meta["duration"],
        "sections": sections,
        "techniques": final_techniques,
        "sequence": sequence,
    }

    # Write + validate
    FORMS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FORMS_DIR / f"{meta['id']}.json"
    with open(out_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    warnings: list[str] = []
    errors = validate_form(str(out_path), warnings=warnings)
    techs = len(data.get('techniques', []))
    steps = len(data.get('sequence', []))
    tips_count = sum(len(t.get('tips', [])) for t in data.get('techniques', []))

    if errors:
        print(f"  ERRORS ({len(errors)}):")
        for e in errors[:10]:
            print(f"    - {e}")
        if len(errors) > 10:
            print(f"    ... and {len(errors) - 10} more")
    if warnings:
        print(f"  WARNINGS ({len(warnings)}):")
        for w in warnings[:10]:
            print(f"    - {w}")
        if len(warnings) > 10:
            print(f"    ... and {len(warnings) - 10} more")
    print(f"  Wrote {out_path}: {techs} techniques, {steps} steps, {tips_count} tips, "
          f"{len(errors)} errors, {len(warnings)} warnings")
    return len(errors) == 0


def validate_all():
    """Validate all existing form JSONs."""
    total_errors = 0
    total_warnings = 0
    for fname in sorted(os.listdir(FORMS_DIR)):
        if not fname.endswith('.json'):
            continue
        path = str(FORMS_DIR / fname)
        warnings: list[str] = []
        errors = validate_form(path, warnings=warnings)
        with open(path) as f:
            d = json.load(f)
        techs = len(d.get('techniques', []))
        steps = len(d.get('sequence', []))
        tips_count = sum(len(t.get('tips', [])) for t in d.get('techniques', []))
        status = "OK" if not errors else f"{len(errors)} errors"
        if warnings:
            status += f", {len(warnings)} warnings"
        print(f"{fname:25s} {techs:3d} tech  {steps:3d} steps  {tips_count:4d} tips  {status}")
        for e in errors:
            print(f"  - {e}")
        for w in warnings:
            print(f"  - {w}")
        total_errors += len(errors)
        total_warnings += len(warnings)
    print(f"\nTotal: {total_errors} errors, {total_warnings} warnings")
    return total_errors == 0


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 extract.py <slug>           Extract one form")
        print("  python3 extract.py --all             Extract all forms")
        print("  python3 extract.py --validate        Validate existing JSONs")
        print("  python3 extract.py --prompt-only <slug>  Print LLM prompt only")
        print("  python3 extract.py --no-llm <slug>       Skip LLM call")
        print(f"\nSlugs: {', '.join(sorted(FORM_META.keys()))}")
        sys.exit(1)

    if "--validate" in sys.argv:
        ok = validate_all()
        sys.exit(0 if ok else 1)

    prompt_only = "--prompt-only" in sys.argv
    no_llm = "--no-llm" in sys.argv
    do_all = "--all" in sys.argv

    if do_all:
        for slug in sorted(FORM_META.keys()):
            print(f"\n{'=' * 50}\n{slug}\n{'=' * 50}")
            extract_form(slug, prompt_only=prompt_only, no_llm=no_llm)
    else:
        slug = [a for a in sys.argv[1:] if not a.startswith("--")][0]
        extract_form(slug, prompt_only=prompt_only, no_llm=no_llm)


if __name__ == "__main__":
    main()
