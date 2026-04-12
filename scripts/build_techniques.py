#!/usr/bin/env python3
"""Build dat/techniques.json from per-form JSONs.

Reads all form JSONs in dat/forms/, deduplicates techniques by English name
(case-insensitive), picks the best source (video_timestamp > 0, most tips),
merges tips from all forms, and writes a single techniques.json.
"""

import json
import os
import re
import sys
from pathlib import Path

FORMS_DIR = Path(__file__).resolve().parent.parent / "dat" / "forms"
OUTPUT = Path(__file__).resolve().parent.parent / "dat" / "techniques.json"


def _slugify_single(name: str) -> str:
    """Slugify a single (non-combo) technique name."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def slugify(name: str) -> str:
    """Convert English technique name to a URL-safe slug key.

    Preserves '+' for combo techniques: "Front Kick + Low Block"
    becomes "front-kick+low-block".
    """
    if " + " in name:
        parts = name.split(" + ")
        return "+".join(_slugify_single(p) for p in parts)
    return _slugify_single(name)


def load_forms() -> list[dict]:
    """Load all form JSONs sorted in curriculum order."""
    forms = []
    for f in sorted(FORMS_DIR.glob("*.json")):
        with open(f) as fh:
            forms.append(json.load(fh))

    # SYNC: this sort order must match app/src/lib/data.ts getAllForms()
    def sort_key(form: dict) -> tuple:
        m = re.match(r"taegeuk-(\d+)", form["id"])
        if m:
            return (0, int(m.group(1)))
        dan = form.get("dan") or 99
        return (1, dan)

    forms.sort(key=sort_key)
    return forms


def tip_key(tip: dict | str) -> str:
    """Dedup key for a tip (by text content)."""
    text = tip if isinstance(tip, str) else tip.get("text", "")
    return text.strip().lower()


def build_techniques(forms: list[dict]) -> dict:
    """Build the merged technique database.

    Groups techniques by normalized English name. For each group:
    - Picks the source with video_timestamp > 0 and the most tips
    - Merges tips from all forms (deduped by text)
    - Tracks which forms use each technique
    """
    # name_lower -> list of (form, technique)
    groups: dict[str, list[tuple[dict, dict]]] = {}

    for form in forms:
        for tech in form.get("techniques", []):
            name_lower = tech["name"]["en"].strip().lower()
            groups.setdefault(name_lower, []).append((form, tech))

    result = {}

    for name_lower, entries in sorted(groups.items()):
        # Pick best source: prefer video_timestamp > 0, then most tips
        best_form, best_tech = max(
            entries,
            key=lambda ft: (
                1 if (ft[1].get("video_timestamp") or 0) > 0 else 0,
                len(ft[1].get("tips", [])),
            ),
        )

        # Generate a stable slug key from the English name
        key = slugify(best_tech["name"]["en"])

        # Merge tips from all forms, deduped by text
        seen_tips: set[str] = set()
        merged_tips = []
        for form, tech in entries:
            for tip in tech.get("tips", []):
                tk = tip_key(tip)
                if tk and tk not in seen_tips:
                    seen_tips.add(tk)
                    if isinstance(tip, str):
                        merged_tips.append({"text": tip})
                    else:
                        tip_entry: dict = {"text": tip["text"]}
                        if tip.get("timestamp"):
                            tip_entry["timestamp"] = tip["timestamp"]
                            tip_entry["video_id"] = form["video_id"]
                        merged_tips.append(tip_entry)

        # Track which forms use this technique
        used_in = sorted(set(form["id"] for form, _ in entries))

        # Build source info from the best entry
        source: dict = {
            "form_id": best_form["id"],
            "form_name": best_form["name"]["en"],
            "video_id": best_form["video_id"],
            "timestamp": best_tech.get("video_timestamp") or 0,
        }
        if best_tech.get("video_timestamp_end"):
            source["timestamp_end"] = best_tech["video_timestamp_end"]

        entry = {
            "key": key,
            "name": best_tech["name"],
            "category": best_tech.get("category", "technique"),
            "source": source,
            "tips": merged_tips,
            "used_in": used_in,
        }

        result[key] = entry

    return result


def normalize_hyphenation(s: str) -> str:
    """Normalize compound words: knife-hand→knifehand, back-fist→backfist, spear-hand→spearhand.

    Case-aware: 'Knife-hand' → 'Knifehand', 'knife-hand' → 'knifehand'.
    """
    replacements = {
        "knife-hand": "knifehand",
        "back-fist": "backfist",
        "spear-hand": "spearhand",
    }
    result = s
    for old, new in replacements.items():
        def _replace(m: re.Match) -> str:
            matched = m.group(0)
            if matched[0].isupper():
                return new.capitalize()
            return new
        result = re.sub(re.escape(old), _replace, result, flags=re.IGNORECASE)
    return result


def normalize_key(key: str) -> str:
    """Normalize a technique key: apply hyphenation rules."""
    return normalize_hyphenation(key)


def normalize_en_name(name: str) -> str:
    """Normalize English name for dedup comparison."""
    return normalize_hyphenation(name.strip().lower())


def normalize_romanized(name: str) -> str:
    """Normalize romanized name for dedup: lowercase, no spaces/hyphens."""
    return re.sub(r"[\s\-]+", "", name.strip().lower())


def word_set_key(name: str) -> str:
    """Create a word-set key for matching reordered English names.

    'outward middle block' and 'middle outward block' both produce the same key.
    """
    normalized = normalize_en_name(name)
    return " ".join(sorted(normalized.split()))


def post_process(techniques: dict) -> tuple[dict, dict[str, str]]:
    """Post-process technique dict: normalize categories, keys, and dedup.

    Returns:
        (cleaned_techniques, rename_map) where rename_map maps old_key -> new_key
        for all keys that were renamed or merged.
    """
    rename_map: dict[str, str] = {}

    # --- 1. Category normalization ---
    for key, tech in techniques.items():
        cat = tech["category"]
        if cat == "ready":
            tech["category"] = "stance"
        elif cat == "technique":
            # Infer from name if possible
            name_lower = tech["name"]["en"].lower()
            if any(w in name_lower for w in ["block", "makgi"]):
                tech["category"] = "block"
            elif any(w in name_lower for w in ["kick", "chagi"]):
                tech["category"] = "kick"
            elif any(w in name_lower for w in ["stance", "seogi", "jase"]):
                tech["category"] = "stance"
            else:
                tech["category"] = "strike"

    # --- 2. Key normalization (hyphenation) ---
    new_techniques: dict = {}
    for old_key, tech in techniques.items():
        new_key = normalize_key(old_key)
        # Also normalize the English name in the entry
        tech["name"]["en"] = normalize_hyphenation(tech["name"]["en"])
        tech["key"] = new_key
        if new_key != old_key:
            rename_map[old_key] = new_key
        if new_key in new_techniques:
            # Merge: keep the one with more tips, merge used_in
            existing = new_techniques[new_key]
            if len(tech.get("tips", [])) > len(existing.get("tips", [])):
                tech["used_in"] = sorted(set(tech["used_in"]) | set(existing["used_in"]))
                # Merge tips
                seen = {tip_key(t) for t in tech["tips"]}
                for t in existing["tips"]:
                    if tip_key(t) not in seen:
                        tech["tips"].append(t)
                        seen.add(tip_key(t))
                new_techniques[new_key] = tech
            else:
                existing["used_in"] = sorted(set(existing["used_in"]) | set(tech["used_in"]))
                seen = {tip_key(t) for t in existing["tips"]}
                for t in tech["tips"]:
                    if tip_key(t) not in seen:
                        existing["tips"].append(t)
                        seen.add(tip_key(t))
            rename_map[old_key] = new_key
        else:
            new_techniques[new_key] = tech
    techniques = new_techniques

    # --- 3. Dedup by romanized name ---
    rom_groups: dict[str, list[str]] = {}
    for key, tech in techniques.items():
        rom = normalize_romanized(tech["name"].get("romanized", ""))
        if rom:
            rom_groups.setdefault(rom, []).append(key)

    for rom, keys in rom_groups.items():
        if len(keys) <= 1:
            continue
        # Pick the one with more tips
        best_key = max(keys, key=lambda k: len(techniques[k].get("tips", [])))
        for k in keys:
            if k == best_key:
                continue
            # Merge into best
            victim = techniques[k]
            winner = techniques[best_key]
            winner["used_in"] = sorted(set(winner["used_in"]) | set(victim["used_in"]))
            seen = {tip_key(t) for t in winner["tips"]}
            for t in victim["tips"]:
                if tip_key(t) not in seen:
                    winner["tips"].append(t)
                    seen.add(tip_key(t))
            rename_map[k] = best_key
            del techniques[k]

    # --- 3b. Fuzzy dedup by romanized prefix (stance modifiers only) ---
    # If one romanized name is a prefix of another (same category, neither is
    # a combination indicated by '+'), and the suffix is a known stance/posture
    # modifier, merge them. Keep the longer/more specific name.
    # Known stance suffixes: "jase" (posture/stance), "seogi" (standing stance)
    STANCE_SUFFIXES = {"jase", "seogi"}
    rom_keys = [
        (k, normalize_romanized(tech["name"].get("romanized", "")), tech)
        for k, tech in techniques.items()
    ]
    merged_fuzzy: set[str] = set()
    for i, (k1, r1, t1) in enumerate(rom_keys):
        if not r1 or k1 in merged_fuzzy:
            continue
        for j, (k2, r2, t2) in enumerate(rom_keys):
            if i >= j or not r2 or k2 in merged_fuzzy:
                continue
            if t1["category"] != t2["category"]:
                continue
            if r1 == r2:
                continue
            # Determine shorter/longer
            if len(r1) < len(r2):
                shorter_k, shorter_r, shorter_t = k1, r1, t1
                longer_k, longer_r, longer_t = k2, r2, t2
            else:
                shorter_k, shorter_r, shorter_t = k2, r2, t2
                longer_k, longer_r, longer_t = k1, r1, t1
            if not longer_r.startswith(shorter_r):
                continue
            # Skip if either name is a combination (contains '+')
            longer_rom_raw = longer_t["name"].get("romanized", "")
            shorter_rom_raw = shorter_t["name"].get("romanized", "")
            if "+" in longer_rom_raw or "+" in shorter_rom_raw:
                continue
            # Only merge if suffix is a known stance modifier
            suffix = longer_r[len(shorter_r):]
            if suffix not in STANCE_SUFFIXES:
                continue
            # Merge: keep the longer/more specific name
            winner = techniques[longer_k]
            victim = techniques[shorter_k]
            winner["used_in"] = sorted(set(winner["used_in"]) | set(victim["used_in"]))
            seen = {tip_key(t) for t in winner["tips"]}
            for t in victim["tips"]:
                if tip_key(t) not in seen:
                    winner["tips"].append(t)
                    seen.add(tip_key(t))
            # Prefer source with video timestamp
            if (victim["source"]["timestamp"] > 0
                    and winner["source"]["timestamp"] == 0):
                winner["source"] = victim["source"]
            rename_map[shorter_k] = longer_k
            merged_fuzzy.add(shorter_k)
            del techniques[shorter_k]

    # --- 3c. Fuzzy dedup by English "Stance" suffix ---
    # "X" and "X Stance" are the same technique — keep "X Stance".
    en_stance_map: dict[str, str] = {}  # en_lower_without_stance -> key
    for key, tech in list(techniques.items()):
        en = tech["name"]["en"].strip().lower()
        if en.endswith(" stance"):
            base = en[: -len(" stance")]
            en_stance_map[base] = key

    for key, tech in list(techniques.items()):
        if key not in techniques:
            continue
        en = tech["name"]["en"].strip().lower()
        if en in en_stance_map and en_stance_map[en] != key:
            stance_key = en_stance_map[en]
            if stance_key not in techniques:
                continue
            winner = techniques[stance_key]
            victim = techniques[key]
            winner["used_in"] = sorted(set(winner["used_in"]) | set(victim["used_in"]))
            seen_t = {tip_key(t) for t in winner["tips"]}
            for t in victim["tips"]:
                if tip_key(t) not in seen_t:
                    winner["tips"].append(t)
                    seen_t.add(tip_key(t))
            if (victim["source"]["timestamp"] > 0
                    and winner["source"]["timestamp"] == 0):
                winner["source"] = victim["source"]
            rename_map[key] = stance_key
            del techniques[key]

    # --- 4. Dedup by similar English name (word-order normalization) ---
    en_groups: dict[str, list[str]] = {}
    for key, tech in techniques.items():
        ws = word_set_key(tech["name"]["en"])
        en_groups.setdefault(ws, []).append(key)

    for ws, keys in en_groups.items():
        if len(keys) <= 1:
            continue
        best_key = max(keys, key=lambda k: len(techniques[k].get("tips", [])))
        for k in keys:
            if k == best_key:
                continue
            victim = techniques[k]
            winner = techniques[best_key]
            winner["used_in"] = sorted(set(winner["used_in"]) | set(victim["used_in"]))
            seen = {tip_key(t) for t in winner["tips"]}
            for t in victim["tips"]:
                if tip_key(t) not in seen:
                    winner["tips"].append(t)
                    seen.add(tip_key(t))
            rename_map[k] = best_key
            del techniques[k]

    return techniques, rename_map


CURRICULUM_ORDER = [
    "taegeuk-1", "taegeuk-2", "taegeuk-3", "taegeuk-4",
    "taegeuk-5", "taegeuk-6", "taegeuk-7", "taegeuk-8",
    "koryo", "keumgang", "taebaek", "pyeongwon",
    "sipjin", "jitae", "chonkwon", "hansu", "ilyeo",
]


def _en_word_set(name: str) -> set[str]:
    """Normalized word set for English name matching."""
    return set(normalize_en_name(name).split())


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein edit distance between two strings."""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


def _is_fuzzy_match(
    en_a: str, rom_a: str, en_b: str, rom_b: str
) -> bool:
    """Check if two techniques are a fuzzy match for video inheritance.

    For non-combination techniques: matches when the word set of one English
    name is a strict subset of the other, OR when one romanized name is a
    substring of the other (bidirectional).

    For combination techniques (containing '+'): matches only when one
    romanized name is a substring of the other (original behavior).
    """
    is_combo = "+" in en_a or "+" in en_b
    # Romanized substring (bidirectional)
    rom_match = False
    if rom_a and rom_b and rom_a != rom_b:
        rom_match = rom_a in rom_b or rom_b in rom_a
    if is_combo:
        return rom_match
    # Word-set containment on English names (bidirectional)
    ws_a = _en_word_set(en_a)
    ws_b = _en_word_set(en_b)
    en_match = ws_a < ws_b or ws_b < ws_a  # strict subset either direction
    return en_match or rom_match


# Romanized modifier words that can be added/removed without changing the
# base technique.  Used by level-aware video inheritance.
_ROMANIZED_MODIFIERS: set[str] = {
    # Level
    "ulgul", "momtong", "arae",
    # Stance
    "hakdari", "seogi", "dwit", "gubi", "ap", "beom", "jase",
    # Position
    "yeop", "an", "bakkat",
}


def _romanized_base(romanized: str) -> str:
    """Extract the base technique from a romanized name by removing modifier words.

    Returns a space-joined, sorted, lowercased string of non-modifier words.
    Sorting makes the comparison order-independent.
    """
    words = re.sub(r"[\s\-]+", " ", romanized.strip().lower()).split()
    base_words = [w for w in words if w not in _ROMANIZED_MODIFIERS]
    return " ".join(sorted(base_words))


def inherit_video_sources(techniques: dict, forms: list[dict]) -> int:
    """Inherit video source from earlier forms for techniques with no video.

    For each technique with source.timestamp == 0, search forms in curriculum
    order for the first form that has a technique with a fuzzy-matching name
    AND video_timestamp > 0. Matching uses word-set containment on English
    names or romanized substring matching, both bidirectional. Among matches,
    picks the closest by edit distance on English name.

    After inheritance, fixes techniques where tips have timestamps and video_id
    but source.timestamp == 0 by setting source.timestamp from the first tip.

    Returns count of techniques that inherited a video source.
    """
    # Build form lookup indexed by curriculum order
    form_by_id: dict[str, dict] = {f["id"]: f for f in forms}
    ordered_forms = [form_by_id[fid] for fid in CURRICULUM_ORDER if fid in form_by_id]

    # Build index: normalized romanized -> (form, tech_entry) for first
    # occurrence with video_timestamp > 0
    rom_video_index: dict[str, tuple[dict, dict]] = {}
    for form in ordered_forms:
        for tech in form.get("techniques", []):
            rom = normalize_romanized(tech["name"].get("romanized", ""))
            ts = tech.get("video_timestamp") or 0
            if rom and ts > 0 and rom not in rom_video_index:
                rom_video_index[rom] = (form, tech)

    # Map form_id to curriculum position for ordering constraint
    form_position = {fid: i for i, fid in enumerate(CURRICULUM_ORDER)}

    inherited = 0
    for key, tech in techniques.items():
        if tech["source"]["timestamp"] > 0:
            continue
        # Skip combo techniques — they get decomposed into components instead
        if "+" in key:
            continue
        rom = normalize_romanized(tech["name"].get("romanized", ""))
        en = tech["name"]["en"]
        if not rom:
            continue

        # Determine the earliest form this technique appears in
        earliest_pos = min(
            (form_position.get(fid, 999) for fid in tech.get("used_in", [])),
            default=999,
        )

        # Try exact romanized match first — but only from same or earlier form
        match = rom_video_index.get(rom)
        if match:
            src_pos = form_position.get(match[0]["id"], 999)
            if src_pos > earliest_pos:
                match = None  # Video from a later form — skip

        if not match:
            # Bidirectional fuzzy matching — only from same or earlier forms
            best_match = None
            best_dist = float("inf")
            for vid_rom, entry in rom_video_index.items():
                src_pos = form_position.get(entry[0]["id"], 999)
                if src_pos > earliest_pos:
                    continue  # Skip videos from later forms
                vid_en = entry[1]["name"]["en"]
                if _is_fuzzy_match(en, rom, vid_en, vid_rom):
                    dist = _edit_distance(
                        normalize_en_name(en), normalize_en_name(vid_en)
                    )
                    if dist < best_dist:
                        best_dist = dist
                        best_match = entry
            match = best_match
        if not match:
            continue
        src_form, src_tech = match
        tech["source"] = {
            "form_id": src_form["id"],
            "form_name": src_form["name"]["en"],
            "video_id": src_form["video_id"],
            "timestamp": src_tech.get("video_timestamp") or 0,
        }
        if src_tech.get("video_timestamp_end"):
            tech["source"]["timestamp_end"] = src_tech["video_timestamp_end"]
        # Merge tips from the source form technique
        seen = {tip_key(t) for t in tech["tips"]}
        for tip in src_tech.get("tips", []):
            tk = tip_key(tip)
            if tk and tk not in seen:
                seen.add(tk)
                if isinstance(tip, str):
                    tech["tips"].append({"text": tip})
                else:
                    tip_entry: dict = {"text": tip["text"]}
                    if tip.get("timestamp"):
                        tip_entry["timestamp"] = tip["timestamp"]
                        tip_entry["video_id"] = src_form["video_id"]
                    tech["tips"].append(tip_entry)
        inherited += 1

    # --- Level-aware pass ---
    # For techniques still without video, match against techniques (not forms)
    # that already have video by comparing romanized base words (ignoring
    # level/stance/position modifiers).  Pick the closest by edit distance.
    level_inherited = 0
    # Build base -> list of (key, tech) for techniques WITH video
    base_video_index: dict[str, list[tuple[str, dict]]] = {}
    for k, t in techniques.items():
        if t["source"]["timestamp"] <= 0:
            continue
        rom = t["name"].get("romanized", "")
        if not rom:
            continue
        base = _romanized_base(rom)
        if base:
            base_video_index.setdefault(base, []).append((k, t))

    for key, tech in techniques.items():
        if tech["source"]["timestamp"] > 0:
            continue
        rom_raw = tech["name"].get("romanized", "")
        if not rom_raw:
            continue
        base = _romanized_base(rom_raw)
        if not base or base not in base_video_index:
            continue
        # Pick the candidate with shortest edit distance on romanized name
        rom_norm = normalize_romanized(rom_raw)
        best_entry = None
        best_dist = float("inf")
        for cand_key, cand_tech in base_video_index[base]:
            cand_rom = normalize_romanized(cand_tech["name"].get("romanized", ""))
            dist = _edit_distance(rom_norm, cand_rom)
            if dist < best_dist:
                best_dist = dist
                best_entry = cand_tech
        if best_entry is None:
            continue
        tech["source"] = dict(best_entry["source"])
        level_inherited += 1
        inherited += 1

    if level_inherited:
        print(f"  Level-aware inheritance: {level_inherited} techniques")

    # Fix techniques where tips have timestamps but source.timestamp == 0.
    # Set source.timestamp from the first tip with a timestamp.
    tip_fixed = 0
    for key, tech in techniques.items():
        if tech["source"]["timestamp"] != 0:
            continue
        for tip in tech["tips"]:
            if isinstance(tip, dict) and tip.get("timestamp") and tip.get("video_id"):
                tech["source"]["timestamp"] = tip["timestamp"]
                # Ensure source video_id matches the tip's video_id
                tech["source"]["video_id"] = tip["video_id"]
                tip_fixed += 1
                break
    if tip_fixed:
        print(f"  Fixed {tip_fixed} techniques with timestamp from tips")

    return inherited


def update_form_jsons(rename_map: dict[str, str], techniques: dict) -> int:
    """Update technique references in form JSONs after dedup.

    Updates keys, categories, and English names to match the canonical
    technique entries.

    Returns count of updated forms.
    """
    # Build lookups for canonical technique matching
    rom_to_canonical: dict[str, dict] = {}
    key_to_canonical: dict[str, dict] = {}
    for tech in techniques.values():
        rom = normalize_romanized(tech["name"].get("romanized", ""))
        if rom:
            rom_to_canonical[rom] = tech
        key_to_canonical[tech["key"]] = tech

    updated_count = 0
    for form_path in sorted(FORMS_DIR.glob("*.json")):
        with open(form_path) as f:
            data = json.load(f)

        changed = False
        for step in data.get("sequence", []):
            old_tech = step.get("technique", "")
            if old_tech in rename_map:
                step["technique"] = rename_map[old_tech]
                changed = True

        # Dedup technique entries within the form (after rename, two entries
        # may have the same key)
        seen_keys: set[str] = set()
        deduped_techniques = []
        for tech in data.get("techniques", []):
            old_key = tech.get("key", "")
            if old_key in rename_map:
                new_key = rename_map[old_key]
                tech["key"] = new_key
                changed = True

            # Sync name/key with canonical techniques.json entry
            # Try romanized match first, then key match (for renamed entries)
            canonical = None
            rom = normalize_romanized(tech["name"].get("romanized", ""))
            if rom and rom in rom_to_canonical:
                canonical = rom_to_canonical[rom]
            elif tech["key"] in key_to_canonical:
                canonical = key_to_canonical[tech["key"]]
            if canonical:
                if tech["name"] != canonical["name"]:
                    tech["name"] = dict(canonical["name"])
                    changed = True
                if tech["key"] != canonical["key"]:
                    # Also update sequence references
                    old_form_key = tech["key"]
                    for step in data.get("sequence", []):
                        if step.get("technique") == old_form_key:
                            step["technique"] = canonical["key"]
                    tech["key"] = canonical["key"]
                    changed = True
            # Normalize category in source forms too
            if tech.get("category") == "ready":
                tech["category"] = "stance"
                changed = True
            if tech.get("category") == "technique":
                name_lower = tech["name"]["en"].lower()
                if any(w in name_lower for w in ["block", "makgi"]):
                    tech["category"] = "block"
                elif any(w in name_lower for w in ["kick", "chagi"]):
                    tech["category"] = "kick"
                elif any(w in name_lower for w in ["stance", "seogi", "jase"]):
                    tech["category"] = "stance"
                else:
                    tech["category"] = "strike"
                changed = True
            # Normalize English name hyphenation in source forms
            old_en = tech["name"].get("en", "")
            new_en = normalize_hyphenation(old_en)
            if old_en != new_en:
                tech["name"]["en"] = new_en
                changed = True

            # Skip duplicate technique entries within the same form
            current_key = tech.get("key", "")
            if current_key in seen_keys:
                changed = True
                continue
            seen_keys.add(current_key)
            deduped_techniques.append(tech)

        if len(deduped_techniques) != len(data.get("techniques", [])):
            changed = True
        data["techniques"] = deduped_techniques

        if changed:
            with open(form_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            updated_count += 1

    return updated_count


def decompose_combos(techniques: dict) -> int:
    """Add 'components' field to combo techniques that lack their own video.

    A combo is any technique whose key contains '+'. If it has
    source.timestamp > 0 it has its own KEY MOVES video segment and is kept
    as-is. Otherwise, split the English name by ' + ', match each part to an
    existing technique (case-insensitive), and record the list of component keys.

    Returns count of combos that received a components field.
    """
    # Build lookup: lowercase English name -> technique key
    en_to_key: dict[str, str] = {}
    for key, tech in techniques.items():
        en_to_key[tech["name"]["en"].strip().lower()] = key

    count = 0
    for key, tech in techniques.items():
        if "+" not in key:
            continue
        if tech["source"]["timestamp"] > 0:
            continue  # Has own video — standalone combo
        en = tech["name"]["en"]
        parts = en.split(" + ")
        components: list[str] = []
        for part in parts:
            matched_key = en_to_key.get(part.strip().lower())
            if matched_key:
                components.append(matched_key)
            else:
                components.append(part.strip())  # Unmatched: leave as string
        tech["components"] = components
        count += 1
    return count


def sort_by_curriculum(techniques: dict, forms: list[dict]) -> dict:
    """Sort techniques by first appearance in curriculum order.

    Ordering:
    1. First form the technique appears in (taegeuk-1 first, ilyeo last)
    2. Within the same form, order of first appearance in that form's sequence
    """
    form_position = {fid: i for i, fid in enumerate(CURRICULUM_ORDER)}

    # Build index: technique key -> (form_position, sequence_position)
    # from form JSONs (sequence steps reference technique keys)
    tech_first_appearance: dict[str, tuple[int, int]] = {}
    for form in forms:
        fid = form["id"]
        fpos = form_position.get(fid, 999)
        for step_idx, step in enumerate(form.get("sequence", [])):
            tkey = step.get("technique", "")
            if tkey and tkey not in tech_first_appearance:
                tech_first_appearance[tkey] = (fpos, step_idx)

    def sort_key(item: tuple[str, dict]) -> tuple:
        key, tech = item
        appearance = tech_first_appearance.get(key)
        if appearance:
            return appearance
        # Fallback: use used_in forms
        earliest = min(
            (form_position.get(fid, 999) for fid in tech.get("used_in", [])),
            default=999,
        )
        return (earliest, 999)

    sorted_items = sorted(techniques.items(), key=sort_key)
    return dict(sorted_items)


def main() -> None:
    forms = load_forms()
    print(f"Loaded {len(forms)} forms from {FORMS_DIR}")

    techniques = build_techniques(forms)
    raw_count = len(techniques)
    print(f"Extracted {raw_count} techniques (before dedup)")

    techniques, rename_map = post_process(techniques)
    print(f"After dedup: {len(techniques)} techniques ({raw_count - len(techniques)} merged)")
    if rename_map:
        print(f"  Renames: {len(rename_map)}")
        for old, new in sorted(rename_map.items()):
            if old != new:
                print(f"    {old} -> {new}")

    # Inherit video sources for techniques with no video breakdown
    zero_before = sum(1 for t in techniques.values() if t["source"]["timestamp"] == 0)
    inherited = inherit_video_sources(techniques, forms)
    zero_after = sum(1 for t in techniques.values() if t["source"]["timestamp"] == 0)
    print(f"Video inheritance: {inherited} techniques inherited sources "
          f"({zero_before} -> {zero_after} with timestamp=0)")
    if zero_after > 0:
        no_video = [
            (k, t["name"]["en"], t["name"].get("romanized", ""))
            for k, t in sorted(techniques.items())
            if t["source"]["timestamp"] == 0
        ]
        print(f"  Remaining no-video ({len(no_video)}):")
        for k, en, rom in no_video:
            print(f"    {k}: {en} ({rom})")

    # Update form JSONs with renamed keys
    updated = update_form_jsons(rename_map, techniques)
    if updated:
        print(f"  Updated {updated} form JSONs")

    # Decompose combo techniques without own video
    combo_count = decompose_combos(techniques)
    combo_total = sum(1 for k in techniques if "+" in k)
    print(f"Combos: {combo_total} total, {combo_count} decomposed (no own video)")

    # Sort by curriculum order
    techniques = sort_by_curriculum(techniques, forms)

    # Category breakdown
    cats: dict[str, int] = {}
    for t in techniques.values():
        c = t["category"]
        cats[c] = cats.get(c, 0) + 1
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(techniques, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
