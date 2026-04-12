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

VALID_CATEGORIES = {"block", "kick", "strike", "stance", "ready", "technique", "combination"}


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
