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


def slugify(name: str) -> str:
    """Convert English technique name to a URL-safe slug key."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


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


def update_form_jsons(rename_map: dict[str, str], techniques: dict) -> int:
    """Update technique references in form JSONs after dedup.

    Updates keys, categories, and English names to match the canonical
    technique entries.

    Returns count of updated forms.
    """
    # Build lookup from normalized romanized name to canonical technique
    rom_to_canonical: dict[str, dict] = {}
    for tech in techniques.values():
        rom = normalize_romanized(tech["name"].get("romanized", ""))
        if rom:
            rom_to_canonical[rom] = tech

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

            # Sync name/key with canonical techniques.json entry via romanized name
            rom = normalize_romanized(tech["name"].get("romanized", ""))
            if rom and rom in rom_to_canonical:
                canonical = rom_to_canonical[rom]
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

    # Update form JSONs with renamed keys
    updated = update_form_jsons(rename_map, techniques)
    if updated:
        print(f"  Updated {updated} form JSONs")

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
