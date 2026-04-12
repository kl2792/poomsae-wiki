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


def main() -> None:
    forms = load_forms()
    print(f"Loaded {len(forms)} forms from {FORMS_DIR}")

    techniques = build_techniques(forms)
    print(f"Extracted {len(techniques)} unique techniques")

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
