#!/usr/bin/env python3
"""
Extract structured poomsae data from OCR transcripts via LLM.

Reproducible pipeline: transcript → prompt → claude CLI → JSON → validate

Usage:
    python3 extract.py taegeuk-1jang       # Extract one form
    python3 extract.py --all               # Extract all forms
    python3 extract.py --prompt-only koryo  # Print prompt without calling LLM
    python3 extract.py --validate          # Validate all existing JSONs
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

DAT_DIR = Path(__file__).parent.parent / "dat"
TRANSCRIPTS_DIR = DAT_DIR / "transcripts"
FORMS_DIR = DAT_DIR / "forms"
PRE_DIR = DAT_DIR / "pre"

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


def format_pre_extracted(pre_data: dict | None) -> str:
    """Format pre-extracted data as a prompt section."""
    if not pre_data:
        return ""

    parts = []
    parts.append("""
PRE-EXTRACTED DATA (from video transcript -- use ONLY these technique names):

CRITICAL: Do NOT add any technique that is not in the lists below.
If you think a technique is missing, leave a note but do NOT invent it.
The sequence may use basic techniques (momtong jireugi, arae makgi, ap chagi, etc.)
that are not in KEY MOVES -- those are fine to include since they are standard TKD techniques.
But do NOT invent named techniques that appear nowhere in the transcript.
""")

    if pre_data.get("key_moves"):
        parts.append("KEY MOVES found in video:")
        for m in pre_data["key_moves"]:
            ts = f"@{m['timestamp']}s" if m["timestamp"] > 0 else ""
            parts.append(f"  {m['number']}. {m['name']} {ts}")
        parts.append("")

    if pre_data.get("sequence_steps"):
        parts.append("SEQUENCE STEPS found in EXPLANATION sections:")
        for s in pre_data["sequence_steps"]:
            side = f"({s['side']})" if s["side"] else ""
            parts.append(f"  {s['number']}. {s['name']} {side} @{s['timestamp']}s")
        parts.append("")

    if pre_data.get("tips"):
        parts.append("TIPS found:")
        for t in pre_data["tips"][:50]:  # Cap at 50 to avoid prompt bloat
            parts.append(f"  [{t['timestamp']}s] {t['text']}")
        if len(pre_data.get("tips", [])) > 50:
            parts.append(f"  ... and {len(pre_data['tips']) - 50} more")
        parts.append("")

    if pre_data.get("sections"):
        parts.append("SECTIONS detected:")
        for name, ts in pre_data["sections"].items():
            parts.append(f"  {name}: {ts}s")
        parts.append("")

    return "\n".join(parts)


def build_prompt(transcript: str, meta: dict, pre_data: dict | None = None) -> str:
    pre_section = format_pre_extracted(pre_data)
    return f"""Extract structured poomsae data from this OCR transcript of an official KKW instructional video.

FORM: {meta['name_en']} ({meta['name_ko']})
VIDEO ID: {meta['video_id']}
DURATION: {meta['duration']}s
EXPECTED MOVES: ~{meta['expected_moves']}

The transcript is timestamped OCR text: [Ns] text from that video frame.
The video structure: Intro → KEY MOVES (numbered technique breakdowns with tips) → EXPLANATION OF PART (full sequence with OEN=left, OREUN=right) → REPEAT (full-speed run).

OUTPUT: A single JSON object. Every field is REQUIRED.

CRITICAL RULES:

TECHNIQUES:
- Include ALL techniques used in the sequence, not just the KEY MOVES from the video
- The KEY MOVES section shows ~5-14 featured techniques. But the sequence uses many more basic techniques (momtong jireugi, arae makgi, ap chagi, etc.) that are NOT in KEY MOVES. You MUST include these too.
- Every technique referenced by ANY sequence step MUST exist in the techniques array
- Every technique MUST have: key (slug), name.en (English ONLY, no romanized), name.ko (hangul), name.romanized (KKW standard), category (block/kick/strike/stance/combination), video_timestamp (from KEY MOVES section, or 0 if not featured), video_timestamp_end (optional, when the technique segment ends), tips (array of {{text, timestamp}} from OCR'd ✓ tips, or empty [])
- Ready positions (junbi, tongmilgi junbijase, etc.) use category 'stance'
- Normalize hyphenation: use 'knifehand' not 'knife-hand', 'backfist' not 'back-fist'

SEQUENCE:
- The full ordered sequence from EXPLANATION OF PART sections
- OEN = left, OREUN = right
- Every step.technique MUST match a key in the techniques array
- Combination moves (A + B) use a single technique key like "ap-chagi+momtong-jireugi"
- Include step 0 for ready stance
- Directions from your knowledge of this form's floor pattern
- Kihap on the correct moves (usually last move, sometimes mid-form)
- Timestamps from when each step appears in the EXPLANATION section

NAMING CONSISTENCY:
- name.en: English translation ONLY (e.g., "Low Block", "Middle Punch", "Front Kick + Middle Punch")
- name.romanized: KKW romanization (e.g., "Arae Makgi", "Momtong Jireugi", "Ap Chagi + Momtong Jireugi")
- name.ko: Hangul (e.g., "아래막기", "몸통지르기")
- For combinations: join with " + " in all three fields

SECTIONS:
- intro: before KEY MOVES
- breakdown: KEY MOVES technique explanations
- explanation: EXPLANATION OF PART sections
- repeat: full-speed run (the REPEAT section)
- Timestamps from when section headers appear in transcript

{{
  "id": "{meta['id']}",
  "name": {{ "en": "{meta['name_en']}", "ko": "{meta['name_ko']}" }},
  "meaning": {{ "en": "{meta['meaning']}" }},
  "belt": {json.dumps(meta['belt'])},
  "dan": {json.dumps(meta['dan'])},
  "total_moves": N,
  "video_id": "{meta['video_id']}",
  "video_duration_seconds": {meta['duration']},
  "sections": {{
    "intro": {{ "start": N, "end": N }},
    "breakdown": {{ "start": N, "end": N }},
    "explanation": {{ "start": N, "end": N }},
    "repeat": {{ "start": N, "end": N }}
  }},
  "techniques": [
    {{
      "key": "technique-slug",
      "name": {{ "en": "English Name", "ko": "한국어", "romanized": "Romanized Korean" }},
      "category": "block",
      "video_timestamp": 186,
      "video_timestamp_end": 210,
      "tips": [{{ "text": "tip from video", "timestamp": 209 }}]
    }}
  ],
  "sequence": [
    {{
      "step": 0,
      "technique": "junbi",
      "side": null,
      "direction": "forward",
      "kihap": false,
      "timestamp": 490,
      "timestamp_end": 495
    }}
  ]
}}

Output ONLY valid JSON, no other text.
{pre_section}
TRANSCRIPT:
{transcript}"""


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
    # Map form_id back to slug for pre-extraction file lookup
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
                        f"transcript — possible hallucination"
                    )
                    if warnings is not None:
                        warnings.append(msg)
                    else:
                        errors.append(msg)

    return errors


# --- Pre-extraction cross-check helpers ---

# Standard techniques that appear in almost every form and don't need
# transcript anchoring.
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
    """Check if a romanized technique name matches any pre-extracted name.

    Uses substring matching in both directions: the romanized name is
    contained in a pre-name, or a pre-name is contained in the romanized.
    Also allows standard techniques that don't need anchoring.
    """
    norm = _normalize_pre_name(romanized)
    if not norm:
        return True  # No romanized name to check
    # Standard techniques are always OK
    if norm in _STANDARD_TECHNIQUES:
        return True
    # Check for combo parts individually
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


def extract_form(slug: str, prompt_only: bool = False):
    transcript_path = TRANSCRIPTS_DIR / f"{slug}.txt"
    if not transcript_path.exists():
        print(f"ERROR: No transcript at {transcript_path}")
        return False

    meta = FORM_META.get(slug)
    if not meta:
        print(f"ERROR: No metadata for {slug}")
        return False

    transcript = transcript_path.read_text()

    # Load pre-extracted data if available
    pre_path = PRE_DIR / f"{slug}.json"
    pre_data = None
    if pre_path.exists():
        with open(pre_path) as f:
            pre_data = json.load(f)
        print(f"  Loaded pre-extraction: {len(pre_data.get('key_moves', []))} key moves, "
              f"{len(pre_data.get('sequence_steps', []))} steps")
    else:
        print(f"  WARNING: No pre-extraction at {pre_path} — running without anchoring")

    prompt = build_prompt(transcript, meta, pre_data)

    if prompt_only:
        print(prompt)
        return True

    print(f"  Extracting {slug} via claude CLI...")
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "text"],
        capture_output=True, text=True, timeout=600
    )

    if result.returncode != 0:
        print(f"  ERROR: claude CLI failed: {result.stderr[:200]}")
        return False

    # Parse JSON from output
    output = result.stdout.strip()
    if output.startswith("```"):
        output = output.split("\n", 1)[1]
    if output.endswith("```"):
        output = output.rsplit("```", 1)[0]
    output = output.strip()

    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        print(f"  ERROR: Invalid JSON: {e}")
        print(f"  Output (first 500 chars): {output[:500]}")
        return False

    # Validate
    FORMS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FORMS_DIR / f"{meta['id']}.json"
    with open(out_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    warnings: list[str] = []
    errors = validate_form(str(out_path), warnings=warnings)
    techs = len(data.get('techniques', []))
    steps = len(data.get('sequence', []))
    tips = sum(len(t.get('tips', [])) for t in data.get('techniques', []))

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
    print(f"  Wrote {out_path}: {techs} techniques, {steps} steps, {tips} tips, "
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
        tips = sum(len(t.get('tips', [])) for t in d.get('techniques', []))
        status = "OK" if not errors else f"{len(errors)} errors"
        if warnings:
            status += f", {len(warnings)} warnings"
        print(f"{fname:25s} {techs:3d} tech  {steps:3d} steps  {tips:4d} tips  {status}")
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
        print("  python3 extract.py --prompt-only <slug>  Print prompt only")
        print(f"\nSlugs: {', '.join(sorted(FORM_META.keys()))}")
        sys.exit(1)

    if "--validate" in sys.argv:
        ok = validate_all()
        sys.exit(0 if ok else 1)

    prompt_only = "--prompt-only" in sys.argv
    do_all = "--all" in sys.argv

    if do_all:
        for slug in sorted(FORM_META.keys()):
            print(f"\n{'=' * 50}\n{slug}\n{'=' * 50}")
            extract_form(slug, prompt_only=prompt_only)
    else:
        slug = [a for a in sys.argv[1:] if not a.startswith("--")][0]
        extract_form(slug, prompt_only=prompt_only)


if __name__ == "__main__":
    main()
