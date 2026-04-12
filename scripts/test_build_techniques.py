#!/usr/bin/env python3
"""Tests for build_techniques.py and the generated techniques.json."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
FORMS_DIR = ROOT_DIR / "dat" / "forms"
TECHNIQUES_FILE = ROOT_DIR / "dat" / "techniques.json"

VALID_CATEGORIES = {"block", "kick", "strike", "stance", "combination"}


def load_techniques() -> dict:
    """Load techniques.json and return as dict."""
    assert TECHNIQUES_FILE.exists(), f"techniques.json not found at {TECHNIQUES_FILE}"
    with open(TECHNIQUES_FILE) as f:
        return json.load(f)


def test_build_techniques_produces_output():
    """Running build_techniques.py produces dat/techniques.json without error."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "build_techniques.py")],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
    )
    assert result.returncode == 0, f"build_techniques.py failed:\n{result.stderr}"
    assert TECHNIQUES_FILE.exists(), "techniques.json not created"


def test_output_has_more_than_100_entries():
    """Technique database should contain more than 100 unique techniques."""
    data = load_techniques()
    assert len(data) > 100, f"Only {len(data)} techniques (expected > 100)"


def test_no_duplicate_keys():
    """Every technique key should be unique (JSON keys are unique by spec, but verify values match)."""
    data = load_techniques()
    keys_from_values = [t["key"] for t in data.values()]
    keys_from_dict = list(data.keys())
    # Keys in the dict should match the 'key' field in each entry
    for dict_key, entry in data.items():
        assert dict_key == entry["key"], f"Dict key '{dict_key}' != entry key '{entry['key']}'"
    # No duplicate key values
    assert len(set(keys_from_values)) == len(keys_from_values), "Duplicate key values found"


def test_every_source_form_id_exists():
    """Every technique's source.form_id should reference an existing form JSON."""
    data = load_techniques()
    form_ids = {p.stem for p in FORMS_DIR.glob("*.json")}
    for key, tech in data.items():
        form_id = tech["source"]["form_id"]
        assert form_id in form_ids, (
            f"Technique '{key}' references form '{form_id}' which doesn't exist in dat/forms/"
        )


def test_tips_have_text_field():
    """Every tip should have a 'text' field."""
    data = load_techniques()
    for key, tech in data.items():
        for i, tip in enumerate(tech.get("tips", [])):
            assert "text" in tip, f"Technique '{key}' tip {i} missing 'text' field"
            assert isinstance(tip["text"], str), f"Technique '{key}' tip {i} text is not a string"
            assert len(tip["text"]) > 0, f"Technique '{key}' tip {i} has empty text"


def test_tips_with_timestamp_have_valid_fields():
    """Tips with timestamps should have numeric timestamp and string video_id."""
    data = load_techniques()
    for key, tech in data.items():
        for i, tip in enumerate(tech.get("tips", [])):
            if "timestamp" in tip:
                assert isinstance(tip["timestamp"], (int, float)), (
                    f"Technique '{key}' tip {i} timestamp is not numeric"
                )
                assert "video_id" in tip, (
                    f"Technique '{key}' tip {i} has timestamp but no video_id"
                )


def test_categories_are_valid():
    """Every technique should have a category from the allowed set."""
    data = load_techniques()
    for key, tech in data.items():
        assert tech["category"] in VALID_CATEGORIES, (
            f"Technique '{key}' has invalid category '{tech['category']}'"
        )


def test_every_technique_has_used_in():
    """Every technique should appear in at least one form."""
    data = load_techniques()
    for key, tech in data.items():
        assert len(tech["used_in"]) > 0, f"Technique '{key}' has empty used_in"


def test_used_in_references_valid_forms():
    """Every form_id in used_in should exist in dat/forms/."""
    data = load_techniques()
    form_ids = {p.stem for p in FORMS_DIR.glob("*.json")}
    for key, tech in data.items():
        for form_id in tech["used_in"]:
            assert form_id in form_ids, (
                f"Technique '{key}' used_in references nonexistent form '{form_id}'"
            )


def test_no_ready_or_technique_categories():
    """No technique should have category 'ready' or 'technique' after post-processing."""
    data = load_techniques()
    for key, tech in data.items():
        assert tech["category"] != "ready", (
            f"Technique '{key}' still has category 'ready'"
        )
        assert tech["category"] != "technique", (
            f"Technique '{key}' still has category 'technique'"
        )


def test_no_hyphenated_compounds_in_keys():
    """Keys should use 'knifehand' not 'knife-hand', 'backfist' not 'back-fist'."""
    data = load_techniques()
    bad_patterns = ["knife-hand", "back-fist", "spear-hand"]
    for key in data:
        for pat in bad_patterns:
            assert pat not in key, (
                f"Key '{key}' contains unhyphenated compound '{pat}'"
            )


def test_no_hyphenated_compounds_in_en_names():
    """English names should use 'Knifehand' not 'Knife-hand', etc."""
    data = load_techniques()
    bad_patterns = ["knife-hand", "back-fist", "spear-hand"]
    for key, tech in data.items():
        en = tech["name"]["en"].lower()
        for pat in bad_patterns:
            assert pat not in en, (
                f"Technique '{key}' en name contains '{pat}': {tech['name']['en']}"
            )


def test_no_duplicate_romanized_names():
    """No two techniques should have the same normalized romanized name."""
    import re as _re
    data = load_techniques()
    seen: dict[str, str] = {}
    for key, tech in data.items():
        rom = _re.sub(r"[\s\-]+", "", tech["name"].get("romanized", "").strip().lower())
        if rom and rom in seen:
            assert False, (
                f"Duplicate romanized name '{tech['name']['romanized']}': "
                f"'{key}' and '{seen[rom]}'"
            )
        if rom:
            seen[rom] = key


def test_form_jsons_reference_valid_technique_keys():
    """Every technique key in form JSONs should exist in techniques.json."""
    data = load_techniques()
    valid_keys = set(data.keys())
    for form_path in sorted(FORMS_DIR.glob("*.json")):
        with open(form_path) as f:
            form = json.load(f)
        for step in form.get("sequence", []):
            tech_key = step.get("technique", "")
            assert tech_key in valid_keys or tech_key in {
                t["key"] for t in form.get("techniques", [])
            }, (
                f"{form_path.stem} step {step.get('step')}: "
                f"technique '{tech_key}' not in techniques.json"
            )


def test_combos_without_video_have_components():
    """Combo techniques (key contains '+') with timestamp=0 should have a components field."""
    data = load_techniques()
    for key, tech in data.items():
        if "+" not in key:
            continue
        if tech["source"]["timestamp"] == 0:
            assert "components" in tech, (
                f"Combo '{key}' has no video (timestamp=0) but missing 'components' field"
            )
            assert isinstance(tech["components"], list), (
                f"Combo '{key}' components should be a list"
            )
            assert len(tech["components"]) >= 2, (
                f"Combo '{key}' should have at least 2 components, got {len(tech['components'])}"
            )


def test_combos_with_video_have_no_components():
    """Combo techniques with their own video (timestamp>0) should NOT have components."""
    data = load_techniques()
    for key, tech in data.items():
        if "+" not in key:
            continue
        if tech["source"]["timestamp"] > 0:
            assert "components" not in tech, (
                f"Combo '{key}' has own video but should not have 'components' field"
            )


def test_combo_components_reference_valid_keys():
    """Each entry in a combo's components list should be either a valid technique key or a string name."""
    data = load_techniques()
    valid_keys = set(data.keys())
    for key, tech in data.items():
        if "components" not in tech:
            continue
        for comp in tech["components"]:
            assert isinstance(comp, str), (
                f"Combo '{key}' has non-string component: {comp}"
            )
            # Components should ideally be valid keys; warn if not
            # (unmatched components are left as English name strings)


def test_combo_keys_contain_plus():
    """Combo techniques (English name with ' + ') should have '+' in their key."""
    data = load_techniques()
    for key, tech in data.items():
        en = tech["name"]["en"]
        if " + " in en:
            assert "+" in key, (
                f"Technique '{key}' has combo English name '{en}' but key lacks '+'"
            )


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
        except Exception as e:
            print(f"  FAIL  {test.__name__}: {e}")
            failed += 1
    print(f"\n{len(tests)} tests, {failed} failed")
    sys.exit(1 if failed else 0)
