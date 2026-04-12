#!/usr/bin/env python3
"""Tests for extract.py validation logic."""

import json
import os
import tempfile
from pathlib import Path

from extract import validate_form, FORMS_DIR, FORM_META


def test_all_existing_forms_pass_validation():
    """Every JSON in dat/forms/ should pass validation with zero errors."""
    assert FORMS_DIR.exists(), f"Forms directory not found: {FORMS_DIR}"
    json_files = sorted(FORMS_DIR.glob("*.json"))
    assert len(json_files) > 0, "No JSON files in forms directory"

    for path in json_files:
        errors = validate_form(str(path))
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
