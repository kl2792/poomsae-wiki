#!/usr/bin/env python3
"""Cross-reference form sequence data against Whisper caption transcripts.

Approach: For each form, extracts ALL technique name mentions from the
explanation/breakdown captions, builds a technique vocabulary, then checks
each sequence step's technique against that vocabulary. Reports techniques
in the sequence that are never mentioned in the captions.

Also does per-part analysis where caption part lists align with sequence
chunks (only for taegeuk-1 where counts match perfectly).

Usage:
    python3 scripts/auto_review.py             # Report only
    python3 scripts/auto_review.py --fix       # Apply clear fixes
    python3 scripts/auto_review.py --verbose   # Show all parsed data
    python3 scripts/auto_review.py --form taegeuk-1  # Single form
"""

import json
import re
import sys
from pathlib import Path

FORMS_DIR = Path(__file__).resolve().parent.parent / "dat" / "forms"
CAPTIONS_DIR = Path(__file__).resolve().parent.parent / "dat" / "captions"

# --- Romanization mappings ---
# Maps Whisper romanization variants to canonical technique keys.
TECHNIQUE_MAP: dict[str, str] = {
    # Knifehand blocks
    "sonnal pakatmaki": "knifehand-outward-block",
    "sonnal pakkatmaki": "knifehand-outward-block",
    "sonnal pakkatmakki": "knifehand-outward-block",
    "sonnal pakatmakki": "knifehand-outward-block",
    "solnal pakkatmaki": "knifehand-outward-block",
    "solnal pakkatmakki": "knifehand-outward-block",
    "sonal pakkatmaki": "knifehand-outward-block",
    "sonal pakkatmakki": "knifehand-outward-block",
    "sonnal bakkatmaki": "knifehand-outward-block",
    "sonnal bakkatmakki": "knifehand-outward-block",
    # Sonnal geoduro
    "seonal geodureo maki": "sonal-geodeureo-makki",
    "sonnal geodureo maki": "sonal-geodeureo-makki",
    "sonnal geodureo makki": "sonal-geodeureo-makki",
    "sonnal godeura makki": "sonal-geodeureo-makki",
    "sonnal godeura maki": "sonal-geodeureo-makki",
    "sonnal godoro maki": "sonal-geodeureo-makki",
    "sonnal godoro makki": "sonal-geodeureo-makki",
    "sonar godoro makki": "sonal-geodeureo-makki",
    "sonar godoro maki": "sonal-geodeureo-makki",
    "sonar goduro makki": "sonal-geodeureo-makki",
    "sonnal godoromaki": "sonal-geodeureo-makki",
    "sonnal godoromakki": "sonal-geodeureo-makki",
    "sonar godora makki": "sonal-geodeureo-makki",
    "sonar godura makki": "sonal-geodeureo-makki",
    "solnal godoromakki": "sonal-geodeureo-makki",
    "solnal godoromaki": "sonal-geodeureo-makki",
    "sonnal geoduro maki": "sonal-geodeureo-makki",
    "sonnal geoduro makki": "sonal-geodeureo-makki",
    # Sonnal geoduro arae
    "sonar godoro aremakki": "sonal-geodeureo-arae-makki",
    "sonar godoro are makki": "sonal-geodeureo-arae-makki",
    "sonar goduro aremakki": "sonal-geodeureo-arae-makki",
    "sonar godura aremakki": "sonal-geodeureo-arae-makki",
    "sonar godoro aremaki": "sonal-geodeureo-arae-makki",
    "sonnal geoduro aremakki": "sonal-geodeureo-arae-makki",
    "sonnal geoduro are makki": "sonal-geodeureo-arae-makki",
    "solnal goduro aremaki": "sonal-geodeureo-arae-makki",
    "solnal goduro aremakki": "sonal-geodeureo-arae-makki",
    "seonnal godureo aremakki": "sonal-geodeureo-arae-makki",
    "sonnal godureo aremakki": "sonal-geodeureo-arae-makki",
    # Sonal anchigi
    "sonnal anchigi": "sonal-anchigi",
    "solnal anchigi": "sonal-anchigi",
    "sonal anchigi": "sonal-anchigi",
    # Blocks
    "are maki": "low-block",
    "are makki": "low-block",
    "aremaki": "low-block",
    "aremakki": "low-block",
    "arae maki": "low-block",
    "arae makki": "low-block",
    "araemaki": "low-block",
    "araemakki": "low-block",
    "an maki": "momtong-an-makki",
    "an makki": "momtong-an-makki",
    "anmaki": "momtong-an-makki",
    "anmakki": "momtong-an-makki",
    "olgul maki": "ollyeo-makki",
    "olgul makki": "ollyeo-makki",
    "olgulmaki": "ollyeo-makki",
    "olgulmakki": "ollyeo-makki",
    "ollyeo maki": "ollyeo-makki",
    "ollyeo makki": "ollyeo-makki",
    "orgul maki": "ollyeo-makki",
    "orgul makki": "ollyeo-makki",
    "uryomaki": "ollyeo-makki",
    "pakkat maki": "momtong-bakkat-makki",
    "pakkat makki": "momtong-bakkat-makki",
    "pakkatmaki": "momtong-bakkat-makki",
    "pakkatmakki": "momtong-bakkat-makki",
    "pakatmaki": "momtong-bakkat-makki",
    "pakatmakki": "momtong-bakkat-makki",
    "bakkat maki": "momtong-bakkat-makki",
    "bakkat makki": "momtong-bakkat-makki",
    "bakkatmaki": "momtong-bakkat-makki",
    "bakkatmakki": "momtong-bakkat-makki",
    "bakkadmaki": "momtong-bakkat-makki",
    "bakkadmakki": "momtong-bakkat-makki",
    "bakkadmakgi": "momtong-bakkat-makki",
    "momtong pakkatmaki": "momtong-bakkat-makki",
    "momtong pakkatmakki": "momtong-bakkat-makki",
    "momtong bakkatmaki": "momtong-bakkat-makki",
    "momtong bakkatmakki": "momtong-bakkat-makki",
    "bituro maki": "bituro-makki",
    "bituro makki": "bituro-makki",
    "bituromaki": "bituro-makki",
    "bituromakki": "bituro-makki",
    # Strikes
    "jirugi": "middle-punch",
    "jireugi": "middle-punch",
    "jirigi": "middle-punch",
    "jiriki": "middle-punch",
    "olgul jirugi": "ulgul-jireugi",
    "olgul jireugi": "ulgul-jireugi",
    "double jirugi": "du-bon-jireugi",
    "double jireugi": "du-bon-jireugi",
    "mejumok neryeochigi": "mejumeok-naeryeochigi",
    "mejumok neryochigi": "mejumeok-naeryeochigi",
    "doongjungmok apchigi": "deungjumeok-ap-chigi",
    "ddeungjumok apchigi": "deungjumeok-ap-chigi",
    "deungjumok apchigi": "deungjumeok-ap-chigi",
    "ddeungjungmok apchigi": "deungjumeok-ap-chigi",
    "dung jumeok apchigi": "deungjumeok-ap-chigi",
    "dung jumok apchigi": "deungjumeok-ap-chigi",
    "palkumchi doryochigi": "palggumchi-dollyeochigi",
    "palkumchi pyojokchigi": "palggumchi-pyojeokchigi",
    "chaebipoom anchigi": "jebipum-anchigi",
    "jebipoom anchigi": "jebipum-anchigi",
    "jebipum anchigi": "jebipum-anchigi",
    # More strikes
    "dung jumeok apchigi": "deungjumeok-ap-chigi",
    "ddeungjumeok abchigi": "deungjumeok-ap-chigi",
    "pyeon seon geut saewo jireugi": "pyeonsonkeut-sewo-jireugi",
    "pyeonsongkut saewo jireugi": "pyeonsonkeut-sewo-jireugi",
    "seonal geoduro maki": "sonal-geodeureo-makki",
    "double jirigi": "du-bon-jireugi",
    "patangseon anmakki": "batangson-momtong-an-makki",
    "patangson anmakki": "batangson-momtong-an-makki",
    "battangson anmakgi": "batangson-momtong-an-makki",
    "patang son anmakki": "batangson-momtong-an-makki",
    "sonar bakat makki": "sonal-bakkat-makki",
    "palkumchi doryeochigi": "palggumchi-dollyeochigi",
    "godura are makki": "geodeureo-arae-makki",
    "goduro are makki": "geodeureo-arae-makki",
    "gawimakki": "gawimakki",
    "haecheomakki": "momtong-hecheomakgi",
    "bojumok": "bojumeok",
    # Kicks
    "apchagi": "ap-chagi",
    "ap chagi": "ap-chagi",
    "aptagi": "ap-chagi",
    "abjagi": "ap-chagi",
    "abchagi": "ap-chagi",
    "yeopchagi": "yeop-chagi",
    "yeop chagi": "yeop-chagi",
    "doryo chagi": "dollyo-chagi",
    "doryochagi": "dollyo-chagi",
    "dollyo chagi": "dollyo-chagi",
    "dollyochagi": "dollyo-chagi",
}

SIDE_MAP: dict[str, str] = {
    "wen": "left",
    "oen": "left",
    "oren": "right",
    "orun": "right",
    "orin": "right",
    "oriun": "right",
}

# Alias sets: technique keys that refer to the same technique.
ALIASES: list[set[str]] = [
    {"momtong-an-makki", "inward-middle-block", "middle-inward-block"},
    {"ollyeo-makki", "upper-block", "high-block", "high-rising-block"},
    {"momtong-bakkat-makki", "outward-block", "middle-outward-block"},
    {"knifehand-outward-block", "sonal-bakkat-makki",
     "knifehand-outward-middle-block", "knifehand-block"},
    {"sonal-geodeureo-makki", "sonnal-geoduro-makki",
     "knifehand-assisted-block", "knifehand-assisted-middle-block"},
    {"sonal-geodeureo-arae-makki", "sonnal-geoduro-arae-makki",
     "knifehand-assisted-low-block", "knifehand-assisted-low-downward-block"},
    {"ap-chagi", "front-kick"},
    {"du-bon-jireugi", "double-punch", "front-kick-double-punch",
     "middle-double-punch"},
    {"ulgul-jireugi", "high-punch"},
    {"mejumeok-naeryeochigi", "mejumok-naeryeo-chigi"},
    {"deungjumeok-ap-chigi", "backfist-front-strike", "deungjumeok-apchigi"},
    {"palggumchi-dollyeochigi", "palkumchi-dollyo-chigi",
     "elbow-turning-strike"},
    {"palggumchi-pyojeokchigi", "palkumchi-pyojok-chigi",
     "elbow-target-strike", "palggumchi-pyojeokchigi"},
    {"jebipum-anchigi", "jebipoom-anchigi"},
    {"yeop-chagi", "yeopchagi", "side-kick"},
    {"dollyo-chagi", "roundhouse-kick", "high-roundhouse-kick"},
    {"bituro-makki", "twisting-block"},
    {"low-block", "low-downward-block"},
    {"sonal-anchigi", "knifehand-inward-strike"},
    {"batangson-momtong-an-makki", "palm-middle-inward-block",
     "palm-inward-block"},
    {"geodeureo-arae-makki", "knifehand-assisted-low-block"},
    {"gawimakki", "scissors-block"},
    {"momtong-hecheomakgi", "middle-spreading-block"},
    {"bojumeok", "bojumok", "covered-fist"},
    {"deungjumeok-ap-chigi", "deungjumeok-apchigi"},
]

_ALIAS_LOOKUP: dict[str, frozenset[str]] = {}


def _build_alias_lookup() -> None:
    """Merge overlapping alias sets and build the lookup."""
    merged: list[set[str]] = []
    for alias_set in ALIASES:
        overlapping: list[int] = []
        for i, m in enumerate(merged):
            if m & alias_set:
                overlapping.append(i)
        if overlapping:
            combined = set(alias_set)
            for i in reversed(overlapping):
                combined |= merged.pop(i)
            merged.append(combined)
        else:
            merged.append(set(alias_set))
    for alias_set in merged:
        fs = frozenset(alias_set)
        for key in alias_set:
            _ALIAS_LOOKUP[key] = fs


_build_alias_lookup()


def keys_equivalent(a: str, b: str) -> bool:
    """Check if two technique keys are equivalent."""
    if a == b:
        return True
    alias_a = _ALIAS_LOOKUP.get(a)
    if alias_a and b in alias_a:
        return True
    return False


def form_id_to_caption_slug(form_id: str) -> str:
    """Convert form ID to caption file slug."""
    m = re.match(r"taegeuk-(\d+)", form_id)
    if m:
        return f"taegeuk-{m.group(1)}jang"
    return form_id


def load_form(form_id: str) -> dict:
    path = FORMS_DIR / f"{form_id}.json"
    with open(path) as f:
        return json.load(f)


def load_captions(form_id: str) -> list[dict] | None:
    slug = form_id_to_caption_slug(form_id)
    path = CAPTIONS_DIR / f"{slug}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)["captions"]


def resolve_technique(name: str) -> str | None:
    """Resolve a romanized technique name to a technique key."""
    lower = name.lower().strip()
    if lower in TECHNIQUE_MAP:
        return TECHNIQUE_MAP[lower]
    no_space = lower.replace(" ", "")
    for mapped_name, key in TECHNIQUE_MAP.items():
        if mapped_name.replace(" ", "") == no_space:
            return key
    return None


def extract_all_caption_techniques(captions: list[dict]) -> set[str]:
    """Extract all recognizable technique keys mentioned anywhere in captions."""
    full_text = " ".join(c["text"] for c in captions).lower()
    found: set[str] = set()

    # Try to find each mapped name in the full text
    for romanized, key in sorted(
        TECHNIQUE_MAP.items(), key=lambda x: -len(x[0])
    ):
        if romanized.lower() in full_text:
            found.add(key)

    return found


def extract_part_techniques(
    captions: list[dict],
) -> list[tuple[int, list[tuple[str | None, str, str | None]]]]:
    """Extract technique lists per part from 'consist of' patterns.

    Returns list of (part_num, [(side, raw_name, resolved_key), ...]).
    """
    joined = " ".join(c["text"] for c in captions)
    parts: list[tuple[int, list[tuple[str | None, str, str | None]]]] = []

    pattern = re.compile(
        r"(?:first|second|third|fourth|1st|2nd|3rd|4th)\s+part[,]?\s+"
        r"consist[s]?\s+of\s+",
        re.IGNORECASE,
    )

    for match in pattern.finditer(joined):
        prefix = match.group(0).lower()
        if "first" in prefix or "1st" in prefix:
            part_num = 1
        elif "second" in prefix or "2nd" in prefix:
            part_num = 2
        elif "third" in prefix or "3rd" in prefix:
            part_num = 3
        elif "fourth" in prefix or "4th" in prefix:
            part_num = 4
        else:
            continue

        rest = joined[match.end():]
        # Cut at next non-technique sentence
        end_pattern = re.compile(
            r"(?:When\s+(?:connecting|moving|performing|setting|transitioning)|"
            r"Caution|We will|Push on|The (?:connection|three|moment|first|target)|"
            r"Pay close|Shift|From the|Your |Be careful|This |That |It is|"
            r"Always|Move the|Remove|control|Set |Place |Spin |"
            r"The key|A closer|Slowly|In succession|then perform|"
            r"After performing|take one step|the hand blade|"
            r"Before performing|spread the two|Because you|There are no|"
            r"Some of the|Ilyo \d|you can attack|block downward|"
            r"but it can also|but also apply)",
            re.IGNORECASE,
        )
        end_match = end_pattern.search(rest)
        if end_match:
            text = rest[: end_match.start()].strip()
        else:
            text = rest[:300].strip()

        text = re.sub(r"\.\s*$", "", text)
        text = re.sub(r",?\s*and\s*$", "", text)

        # Parse individual techniques
        techniques = _parse_technique_list(text)
        parts.append((part_num, techniques))

    return parts


def _parse_technique_list(
    text: str,
) -> list[tuple[str | None, str, str | None]]:
    """Parse technique list text into (side, raw_name, resolved_key) tuples."""
    # Normalize separators
    side_prefix_pattern = "|".join(
        re.escape(s) for s in sorted(SIDE_MAP.keys(), key=len, reverse=True)
    )
    # Period + side prefix = separator
    text = re.sub(
        rf"\.\s+(?=(?:{side_prefix_pattern})\s)",
        ", ",
        text,
        flags=re.IGNORECASE,
    )

    items = re.split(r",\s*(?:and\s+)?|(?:^|\s)and\s+", text)
    results: list[tuple[str | None, str, str | None]] = []

    for item in items:
        item = item.strip().rstrip(".")
        if not item:
            continue

        # Split by side prefix boundaries
        sub_items = _split_by_side_prefix(item)
        for sub in sub_items:
            sub = sub.strip()
            if not sub:
                continue
            side = None
            lower = sub.lower()
            for prefix, side_val in sorted(
                SIDE_MAP.items(), key=lambda x: len(x[0]), reverse=True
            ):
                if lower.startswith(prefix + " "):
                    side = side_val
                    sub = sub[len(prefix) + 1:].strip()
                    break

            # Skip stance-only mentions
            sub_lower = sub.lower()
            if sub_lower in ("apsugi", "apsogi", "apgubi"):
                continue

            key = resolve_technique(sub)
            results.append((side, sub, key))

    return results


def _split_by_side_prefix(text: str) -> list[str]:
    """Split text at side-prefix boundaries after technique endings."""
    side_prefix_pattern = "|".join(
        re.escape(s) for s in sorted(SIDE_MAP.keys(), key=len, reverse=True)
    )
    tech_ending = r"(?:maki|makki|makgi|jirugi|jireugi|jirigi|chagi|chigi)"
    pattern = re.compile(
        rf"({tech_ending})\s+({side_prefix_pattern})\s+",
        re.IGNORECASE,
    )
    segments: list[str] = []
    last = 0
    for m in pattern.finditer(text):
        split_pos = m.start() + len(m.group(1))
        segments.append(text[last:split_pos])
        last = split_pos
    segments.append(text[last:])
    return [s.strip() for s in segments if s.strip()]


def review_form(form_id: str, verbose: bool = False) -> list[dict]:
    """Review a single form against its captions.

    Returns list of findings. Each finding is a dict with 'type' and details.
    """
    form = load_form(form_id)
    captions = load_captions(form_id)
    if captions is None:
        return [{"type": "info", "form_id": form_id, "msg": "no captions file"}]

    findings: list[dict] = []

    # 1. Extract all techniques mentioned in captions
    caption_vocab = extract_all_caption_techniques(captions)

    # 2. Extract per-part technique lists
    parts = extract_part_techniques(captions)

    if verbose:
        print(f"\n{'='*60}")
        print(f"Form: {form_id}")
        print(f"  Caption vocabulary ({len(caption_vocab)}): "
              f"{sorted(caption_vocab)}")
        print(f"  Found {len(parts)} parts in captions")
        for pnum, techs in parts:
            tech_strs = [
                f"{'L' if s == 'left' else 'R' if s == 'right' else '?'} "
                f"{r} -> {k or '?'}"
                for s, r, k in techs
            ]
            print(f"    Part {pnum}: {tech_strs}")

    # 3. Check each sequence step's technique against caption vocabulary
    for step in form["sequence"]:
        if step["step"] == 0:
            continue
        tech = step["technique"]
        # Split combos
        components = tech.split("+")
        for comp in components:
            # Check if this component (or an alias) appears in caption vocab
            found = comp in caption_vocab
            if not found:
                for cv in caption_vocab:
                    if keys_equivalent(comp, cv):
                        found = True
                        break
            if not found:
                findings.append({
                    "type": "not_in_captions",
                    "form_id": form_id,
                    "step": step["step"],
                    "technique": comp,
                    "full_technique": tech,
                })

    # 4. Per-part analysis: check that part technique lists are consistent
    #    with the sequence
    sequence_techs_flat: set[str] = set()
    # Also collect full technique keys for substring matching
    sequence_techs_full: set[str] = set()
    for step in form["sequence"]:
        if step["step"] == 0:
            continue
        sequence_techs_full.add(step["technique"])
        for comp in step["technique"].split("+"):
            sequence_techs_flat.add(comp)

    for pnum, techs in parts:
        for side, raw, key in techs:
            if key is None:
                findings.append({
                    "type": "unrecognized",
                    "form_id": form_id,
                    "part": pnum,
                    "raw": raw,
                    "side": side,
                })
                continue

            # Check if this technique (or alias) appears in sequence
            # Also check compound technique keys (e.g., "front-kick" in
            # "front-kick-first-leg-punch")
            found = key in sequence_techs_flat
            if not found:
                for st in sequence_techs_flat:
                    if keys_equivalent(key, st):
                        found = True
                        break
            if not found:
                # Check if any alias of key appears as substring in full keys
                key_aliases = _ALIAS_LOOKUP.get(key, frozenset({key}))
                for full_key in sequence_techs_full:
                    for alias in key_aliases:
                        if alias in full_key:
                            found = True
                            break
                    if found:
                        break
            if not found:
                findings.append({
                    "type": "in_captions_not_sequence",
                    "form_id": form_id,
                    "part": pnum,
                    "caption_key": key,
                    "caption_raw": raw,
                    "caption_side": side,
                    "sequence_techs": sorted(sequence_techs_flat),
                })

    return findings


FORM_IDS = [
    "taegeuk-1", "taegeuk-2", "taegeuk-3", "taegeuk-4",
    "taegeuk-5", "taegeuk-6", "taegeuk-7", "taegeuk-8",
    "koryo", "keumgang", "taebaek", "pyeongwon",
    "sipjin", "jitae", "chonkwon", "hansu", "ilyeo",
]


def main() -> None:
    verbose = "--verbose" in sys.argv
    form_filter = None
    if "--form" in sys.argv:
        idx = sys.argv.index("--form")
        if idx + 1 < len(sys.argv):
            form_filter = sys.argv[idx + 1]

    forms_to_review = [form_filter] if form_filter else FORM_IDS
    all_findings: list[dict] = []

    for form_id in forms_to_review:
        findings = review_form(form_id, verbose)
        all_findings.extend(findings)

    # Print report
    print(f"\n{'='*60}")
    print("CROSS-REFERENCE REPORT")
    print(f"{'='*60}")

    by_type: dict[str, list[dict]] = {}
    for f in all_findings:
        by_type.setdefault(f["type"], []).append(f)

    # Most interesting: techniques in captions but not in sequence (possible data errors)
    if "in_captions_not_sequence" in by_type:
        items = by_type["in_captions_not_sequence"]
        print(f"\n--- CAPTION TECHNIQUE NOT IN SEQUENCE ({len(items)}) ---")
        print("  (Caption mentions a technique that the form sequence doesn't use)")
        for item in items:
            print(
                f"  {item['form_id']} part {item['part']}: "
                f"caption says '{item['caption_raw']}' -> {item['caption_key']}  "
                f"side={item.get('caption_side', '?')}"
            )

    # Techniques in sequence but never mentioned in captions
    if "not_in_captions" in by_type:
        items = by_type["not_in_captions"]
        # Group by form
        by_form: dict[str, list[dict]] = {}
        for item in items:
            by_form.setdefault(item["form_id"], []).append(item)
        print(f"\n--- SEQUENCE TECHNIQUE NOT IN CAPTIONS ({len(items)}) ---")
        print("  (Technique in form sequence but never mentioned in captions)")
        for fid, fitems in sorted(by_form.items()):
            techs = sorted(set(item["technique"] for item in fitems))
            print(f"  {fid}: {techs}")

    # Unrecognized caption technique names
    if "unrecognized" in by_type:
        items = by_type["unrecognized"]
        print(f"\n--- UNRECOGNIZED CAPTION TECHNIQUES ({len(items)}) ---")
        for item in items:
            print(
                f"  {item['form_id']} part {item['part']}: "
                f"'{item['raw']}' (side={item.get('side', '?')})"
            )

    if "info" in by_type:
        for item in by_type["info"]:
            print(f"\n  INFO: {item['form_id']}: {item['msg']}")

    total = len(all_findings)
    print(f"\nTotal: {total} findings across {len(forms_to_review)} forms")


if __name__ == "__main__":
    main()
