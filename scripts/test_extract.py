#!/usr/bin/env python3
"""Tests for extract.py validation logic."""

import json
import os
import tempfile
from pathlib import Path

from extract import validate_form, FORMS_DIR, PRE_DIR, FORM_META


def test_all_existing_forms_pass_validation():
    """Every JSON in dat/forms/ should pass validation with zero errors."""
    assert FORMS_DIR.exists(), f"Forms directory not found: {FORMS_DIR}"
    json_files = sorted(FORMS_DIR.glob("*.json"))
    assert len(json_files) > 0, "No JSON files in forms directory"

    for path in json_files:
        warnings = []
        errors = validate_form(str(path), warnings=warnings)
        assert errors == [], f"{path.name}: {errors}"


def test_validate_form_catches_missing_fields():
    """A JSON missing required fields should produce errors."""
    bad = {"name": {"en": "Test", "ko": "test"}, "techniques": [], "sequence": []}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", dir=str(FORMS_DIR.parent), delete=False
    ) as f:
        json.dump(bad, f)
        tmp_path = f.name

    try:
        errors = validate_form(tmp_path)
        assert len(errors) > 0, "Expected errors for missing fields"
        missing = [e for e in errors if "Missing field" in e]
        assert len(missing) > 0
    finally:
        os.unlink(tmp_path)


def test_validate_form_catches_unresolved_technique_ref():
    """A sequence step referencing a nonexistent technique should error."""
    bad = {
        "id": "test",
        "name": {"en": "Test", "ko": "test"},
        "total_moves": 1,
        "video_id": "xxx",
        "techniques": [
            {
                "key": "real-technique",
                "name": {"en": "Real", "ko": "진짜", "romanized": "Jinjja"},
                "category": "block",
            }
        ],
        "sequence": [
            {
                "step": 0,
                "technique": "nonexistent",
                "side": None,
                "direction": "forward",
                "kihap": False,
                "timestamp": 0,
                "timestamp_end": 1,
            }
        ],
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", dir=str(FORMS_DIR.parent), delete=False
    ) as f:
        json.dump(bad, f)
        tmp_path = f.name

    try:
        errors = validate_form(tmp_path)
        assert any("nonexistent" in e for e in errors)
    finally:
        os.unlink(tmp_path)


def test_validate_form_catches_unordered_steps():
    """Out-of-order sequence steps should produce an error."""
    bad = {
        "id": "test",
        "name": {"en": "Test", "ko": "test"},
        "total_moves": 2,
        "video_id": "xxx",
        "techniques": [
            {
                "key": "a",
                "name": {"en": "A", "ko": "아", "romanized": "A"},
                "category": "block",
            }
        ],
        "sequence": [
            {"step": 2, "technique": "a", "side": None, "direction": "forward", "kihap": False, "timestamp": 0, "timestamp_end": 1},
            {"step": 1, "technique": "a", "side": None, "direction": "forward", "kihap": False, "timestamp": 1, "timestamp_end": 2},
        ],
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", dir=str(FORMS_DIR.parent), delete=False
    ) as f:
        json.dump(bad, f)
        tmp_path = f.name

    try:
        errors = validate_form(tmp_path)
        assert any("not in order" in e for e in errors)
    finally:
        os.unlink(tmp_path)


def test_validate_form_catches_invalid_json():
    """A file with invalid JSON should return an error."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", dir=str(FORMS_DIR.parent), delete=False
    ) as f:
        f.write("not valid json {{{")
        tmp_path = f.name

    try:
        errors = validate_form(tmp_path)
        assert len(errors) == 1
        assert "Invalid JSON" in errors[0]
    finally:
        os.unlink(tmp_path)


def test_validate_form_catches_romanized_leak_in_en_name():
    """English name containing parentheses (romanized leak) should error."""
    bad = {
        "id": "test",
        "name": {"en": "Test", "ko": "test"},
        "total_moves": 1,
        "video_id": "xxx",
        "techniques": [
            {
                "key": "a",
                "name": {"en": "Low Block (Arae Makgi)", "ko": "아래막기", "romanized": "Arae Makgi"},
                "category": "block",
            }
        ],
        "sequence": [],
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", dir=str(FORMS_DIR.parent), delete=False
    ) as f:
        json.dump(bad, f)
        tmp_path = f.name

    try:
        errors = validate_form(tmp_path)
        assert any("parentheses" in e for e in errors)
    finally:
        os.unlink(tmp_path)


def test_form_meta_covers_all_json_files():
    """Every JSON file should have a corresponding FORM_META entry."""
    json_files = sorted(FORMS_DIR.glob("*.json"))
    meta_ids = {m["id"] for m in FORM_META.values()}
    for path in json_files:
        form_id = path.stem
        assert form_id in meta_ids, f"{path.name} has no FORM_META entry"


def test_every_form_technique_appears_in_wiki():
    """Every technique from every form JSON should have an entry in techniques.json."""
    import json as _json
    techniques_file = FORMS_DIR.parent / "techniques.json"
    assert techniques_file.exists(), f"techniques.json not found at {techniques_file}"
    with open(techniques_file) as f:
        wiki = _json.load(f)
    wiki_names = {t["name"]["en"].strip().lower() for t in wiki.values()}

    json_files = sorted(FORMS_DIR.glob("*.json"))
    missing = []
    for path in json_files:
        with open(path) as f:
            form = _json.load(f)
        for tech in form.get("techniques", []):
            name_lower = tech["name"]["en"].strip().lower()
            if name_lower not in wiki_names:
                missing.append(f"{path.stem}: {tech['name']['en']}")
    assert missing == [], f"Form techniques missing from wiki:\n" + "\n".join(missing)


def test_validate_warns_on_technique_not_in_pre_extraction():
    """Validation should warn when a technique's romanized name doesn't match pre-extraction data."""
    # Create a form JSON with a technique that won't match any pre-extracted name
    form_data = {
        "id": "taegeuk-1",  # Must match a FORM_META entry that has a pre-extraction file
        "name": {"en": "Taegeuk Il Jang", "ko": "태극 1장"},
        "total_moves": 1,
        "video_id": "xxx",
        "techniques": [
            {
                "key": "fake-technique",
                "name": {
                    "en": "Fake Technique",
                    "ko": "가짜",
                    "romanized": "Zzzzfake Zzzznotreal",
                },
                "category": "strike",
            }
        ],
        "sequence": [
            {
                "step": 0,
                "technique": "fake-technique",
                "side": None,
                "direction": "forward",
                "kihap": False,
                "timestamp": 0,
                "timestamp_end": 1,
            }
        ],
    }
    # Only run this test if pre-extraction file exists for taegeuk-1jang
    pre_path = PRE_DIR / "taegeuk-1jang.json"
    if not pre_path.exists():
        return  # Skip if no pre-extraction data available

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", dir=str(FORMS_DIR.parent), delete=False
    ) as f:
        json.dump(form_data, f)
        tmp_path = f.name

    try:
        warnings: list[str] = []
        errors = validate_form(tmp_path, warnings=warnings)
        hallucination_warnings = [w for w in warnings if "possible hallucination" in w]
        assert len(hallucination_warnings) > 0, (
            f"Expected hallucination warning for 'Zzzzfake Zzzznotreal', "
            f"got errors: {errors}, warnings: {warnings}"
        )
    finally:
        os.unlink(tmp_path)


def test_validate_no_warning_for_real_technique():
    """Validation should NOT warn for techniques that match pre-extraction data."""
    pre_path = PRE_DIR / "taegeuk-1jang.json"
    if not pre_path.exists():
        return  # Skip if no pre-extraction data

    with open(pre_path) as f:
        pre_data = json.load(f)

    # Use a real technique name from the pre-extraction
    if not pre_data.get("key_moves"):
        return
    real_name = pre_data["key_moves"][0]["name"]

    form_data = {
        "id": "taegeuk-1",
        "name": {"en": "Taegeuk Il Jang", "ko": "태극 1장"},
        "total_moves": 1,
        "video_id": "xxx",
        "techniques": [
            {
                "key": "real-tech",
                "name": {
                    "en": "Real Tech",
                    "ko": "진짜",
                    "romanized": real_name,
                },
                "category": "block",
            }
        ],
        "sequence": [
            {
                "step": 0,
                "technique": "real-tech",
                "side": None,
                "direction": "forward",
                "kihap": False,
                "timestamp": 0,
                "timestamp_end": 1,
            }
        ],
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", dir=str(FORMS_DIR.parent), delete=False
    ) as f:
        json.dump(form_data, f)
        tmp_path = f.name

    try:
        warnings: list[str] = []
        errors = validate_form(tmp_path, warnings=warnings)
        hallucination_warnings = [w for w in warnings if "possible hallucination" in w]
        assert len(hallucination_warnings) == 0, (
            f"Unexpected hallucination warning for '{real_name}': {hallucination_warnings}"
        )
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    import sys
    # Simple runner if pytest not available
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
