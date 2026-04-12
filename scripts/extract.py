#!/usr/bin/env python3
"""
Extract structured poomsae data from pre-extracted JSON via LLM.

Reproducible pipeline: pre-extraction JSON → prompt → claude CLI → JSON → validate

Requires pre_extract.py to run first (extracts key_moves, sequence_steps,
tips from raw OCR transcript). This script never reads the transcript directly.

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


def _format_key_moves(pre_data: dict) -> str:
    """Format key_moves list for prompt inclusion."""
    lines = []
    for m in pre_data.get("key_moves", []):
        ts = f"@{m['timestamp']}s" if m["timestamp"] > 0 else ""
        lines.append(f"  {m['number']}. {m['name']} {ts}")
    return "\n".join(lines)


def _format_tips(pre_data: dict) -> str:
    """Format tips list for prompt inclusion (capped at 50)."""
    tips = pre_data.get("tips", [])
    lines = []
    for t in tips[:50]:
        lines.append(f"  [{t['timestamp']}s] {t['text']}")
    if len(tips) > 50:
        lines.append(f"  ... and {len(tips) - 50} more")
    return "\n".join(lines)


def _format_sequence_steps(pre_data: dict) -> str:
    """Format sequence_steps list for prompt inclusion."""
    lines = []
    for s in pre_data.get("sequence_steps", []):
        side = f"({s['side']})" if s["side"] else ""
        lines.append(f"  {s['number']}. {s['name']} {side} @{s['timestamp']}s")
    return "\n".join(lines)


def _format_sections(pre_data: dict) -> str:
    """Format sections timestamps for prompt inclusion."""
    lines = []
    for name, ts in pre_data.get("sections", {}).items():
        lines.append(f"  {name}: {ts}s")
    return "\n".join(lines)


def _form_header(meta: dict) -> str:
    """Common header for both pass prompts."""
    return f"""FORM: {meta['name_en']} ({meta['name_ko']})
VIDEO ID: {meta['video_id']}
DURATION: {meta['duration']}s
EXPECTED MOVES: ~{meta['expected_moves']}

Source: Official KKW instructional video. Data below was pre-extracted from timestamped OCR transcript.
Video structure: Intro → KEY MOVES (numbered technique breakdowns with tips) → EXPLANATION OF PART (full sequence with OEN=left, OREUN=right) → REPEAT (full-speed run)."""


def build_techniques_prompt(meta: dict, pre_data: dict) -> str:
    """Pass 1: Translate and structure techniques from pre-extracted data.

    Uses ONLY key_moves + tips from pre-extraction. No transcript needed.
    """
    key_moves = _format_key_moves(pre_data)
    tips = _format_tips(pre_data)
    sections = _format_sections(pre_data)

    return f"""Translate and structure these taekwondo techniques from an official KKW instructional video.

{_form_header(meta)}

KEY MOVES from video (romanized names with timestamps):
{key_moves}

TIPS extracted from video:
{tips}

SECTIONS detected (timestamps):
{sections}

For each technique in KEY MOVES, output:
- key: URL-safe slug (lowercase, hyphens)
- name.en: English translation ONLY (e.g., "Low Block", "Middle Punch"). No romanized text.
- name.ko: Korean hangul (e.g., "아래막기", "몸통지르기")
- name.romanized: cleaned KKW romanization (e.g., "Arae Makgi", "Momtong Jireugi")
- category: block / kick / strike / stance / combination
- video_timestamp: from the KEY MOVES list above (or 0 if not featured)
- video_timestamp_end: estimated end of that technique's segment (next technique's timestamp)
- tips: match tips to techniques by timestamp proximity (MAX 3 per technique, pick most instructive)

Also identify any additional basic techniques used in this form's sequence that are NOT in KEY MOVES (e.g., momtong jireugi, arae makgi, ap chagi). Include those with video_timestamp: 0 and empty tips.

RULES:
- Ready positions (junbi, tongmilgi junbijase, etc.) use category 'stance'
- Normalize hyphenation: 'knifehand' not 'knife-hand', 'backfist' not 'back-fist'
- For combinations: join with " + " in all three name fields
- Do NOT invent techniques that don't appear in KEY MOVES or standard TKD vocabulary

SECTIONS: Build from the detected timestamps above.
- intro: {{start: 0, end: breakdown_start}}
- breakdown: KEY MOVES technique explanations
- explanation: EXPLANATION OF PART sections
- repeat: full-speed run

{{
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
  "sections": {{
    "intro": {{ "start": N, "end": N }},
    "breakdown": {{ "start": N, "end": N }},
    "explanation": {{ "start": N, "end": N }},
    "repeat": {{ "start": N, "end": N }}
  }}
}}

Output ONLY valid JSON, no other text."""


def build_sequence_prompt(meta: dict, pre_data: dict, technique_keys: list[str]) -> str:
    """Pass 2: Build move sequence from pre-extracted steps + technique keys.

    Uses ONLY sequence_steps from pre-extraction + technique keys from Pass 1.
    No transcript needed.
    """
    keys_str = ", ".join(technique_keys)
    steps = _format_sequence_steps(pre_data)

    return f"""Build the move sequence for this taekwondo form using the technique keys from Pass 1.

{_form_header(meta)}

TECHNIQUE KEYS (copy VERBATIM — do not modify, abbreviate, or re-slugify):
{keys_str}

SEQUENCE STEPS from video (with sides and timestamps):
{steps}

Map each step to a technique key. Add direction from your knowledge of this form's floor pattern.

RULES:
- Every step.technique MUST be copied EXACTLY from TECHNIQUE KEYS. Character-for-character match.
- Do NOT invent new keys. Do NOT add hyphens, remove hyphens, or change spelling.
- For combinations not in the list: join two existing keys with "+" (e.g., "ap-chagi+momtong-jireugi")
- If a step doesn't match any key, use the CLOSEST key from the list.
- OEN = left, OREUN = right
- Include step 0 for ready stance (use the first key if it's a stance/junbi)
- Kihap on the correct moves (usually last move, sometimes mid-form)
- Timestamps come from the SEQUENCE STEPS above

{{
  "total_moves": N,
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

Output ONLY valid JSON, no other text."""


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


def extract_form(slug: str, prompt_only: bool = False):
    meta = FORM_META.get(slug)
    if not meta:
        print(f"ERROR: No metadata for {slug}")
        return False

    # Require pre-extracted data (produced by pre_extract.py from transcript)
    pre_path = PRE_DIR / f"{slug}.json"
    if not pre_path.exists():
        print(f"ERROR: No pre-extraction at {pre_path}")
        print(f"  Run pre_extract.py first: python3 scripts/pre_extract.py {slug}")
        return False

    with open(pre_path) as f:
        pre_data = json.load(f)
    print(f"  Loaded pre-extraction: {len(pre_data.get('key_moves', []))} key moves, "
          f"{len(pre_data.get('sequence_steps', []))} steps, "
          f"{len(pre_data.get('tips', []))} tips")

    techniques_prompt = build_techniques_prompt(meta, pre_data)
    sequence_prompt_fn = lambda tech_keys: build_sequence_prompt(meta, pre_data, tech_keys)

    if prompt_only:
        print("=== PASS 1: TECHNIQUES PROMPT ===")
        print(techniques_prompt)
        print("\n=== PASS 2: SEQUENCE PROMPT (with placeholder keys) ===")
        print(sequence_prompt_fn(["<technique-key-1>", "<technique-key-2>", "..."]))
        return True

    # Pass 1: techniques + sections
    print(f"  Extracting {slug} — Pass 1: techniques + sections...")
    pass1 = _call_claude(techniques_prompt, "Pass 1")
    if pass1 is None:
        return False

    techniques = pass1.get("techniques", [])
    sections = pass1.get("sections", {})
    if not techniques:
        print("  ERROR: Pass 1 returned no techniques")
        return False
    technique_keys = [t["key"] for t in techniques if "key" in t]
    print(f"  Pass 1: {len(techniques)} techniques, {len(technique_keys)} keys")

    # Pass 2: sequence
    print(f"  Extracting {slug} — Pass 2: sequence...")
    pass2 = _call_claude(sequence_prompt_fn(technique_keys), "Pass 2")
    if pass2 is None:
        return False

    sequence = pass2.get("sequence", [])
    total_moves = pass2.get("total_moves", len(sequence) - 1)  # -1 for step 0
    if not sequence:
        print("  ERROR: Pass 2 returned no sequence")
        return False

    # Repair: fix any sequence technique keys that don't match Pass 1 keys
    key_set = set(technique_keys)
    repaired = 0
    for step in sequence:
        tk = step.get("technique", "")
        if tk not in key_set and "+" not in tk:
            # Fuzzy match: find closest key by normalized form
            norm = tk.lower().replace("-", "").replace(" ", "")
            best = None
            best_score = 0
            for k in technique_keys:
                knorm = k.lower().replace("-", "").replace(" ", "")
                # Check substring containment
                if norm in knorm or knorm in norm:
                    score = min(len(norm), len(knorm)) / max(len(norm), len(knorm))
                    if score > best_score:
                        best_score = score
                        best = k
            if best and best_score > 0.5:
                step["technique"] = best
                repaired += 1
    if repaired:
        print(f"  Repaired {repaired} mismatched technique keys in sequence")

    print(f"  Pass 2: {len(sequence)} steps, total_moves={total_moves}")

    # Merge into final form JSON
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
        "techniques": techniques,
        "sequence": sequence,
    }

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
